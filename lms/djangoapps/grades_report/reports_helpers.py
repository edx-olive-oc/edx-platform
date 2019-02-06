"""
Util functions and classes to build additional reports.
"""

from __future__ import division
from itertools import groupby

from django.utils.translation import ugettext as _

from xmodule.modulestore.django import modulestore


def order_by_section_block(graders_object, course_data):
    """
    Util function to order graders object against topological_traversal method output
    of the course structure, and return the same object but ordered by section.
    """
    SECTION_TYPE = u'chapter'
    grades_ordered_by_section = []
    for block in course_data.structure.topological_traversal():
        if block.block_type == SECTION_TYPE:
            matched_sections = filter(lambda x: x['section_block_id'] == block.block_id, graders_object)
            if matched_sections:
                grades_ordered_by_section.extend(matched_sections)

    sections_unreleased = [x for x in graders_object if 'Unreleased' in x['section_block_id']]
    grades_ordered_by_section.extend(sections_unreleased)
    return grades_ordered_by_section


def is_grade_component(section_info):
    """
    Function used to the filter dropped subsections.
    """
    component = False
    is_droppable = section_info.get("mark") and "dropped" in section_info["mark"].get("detail")
    if section_info.get("section_block_id") and not is_droppable:
        component = True

    return component


def generate_filtered_sections(data):
    """
    Util function to remove dropped subsections graders
    and return subsections with no-dropped grades.

    Returns:
        Same data object but, with a new section_filtered key with values filtered.
    """
    section_filtered = filter(is_grade_component, data["section_breakdown"])
    return section_filtered


def generate_by_assignment_type(data, course_policy):
    """
    Util function to group by section and then,
    generate the gradeset of that section and also generate
    by assignment types grades in that section.

    Returns:
        The same input data but, new section_grades key is added.
        1. section_grades: Object list by section, with assignment types grades info in that section.
    """
    MAX_PERCENTAGE_GRADE = 1.00
    section_filtered = data['section_filtered']
    section_by_assignment_type = []
    policy = assign_assignment_type_count(data, course_policy)
    for key, section in groupby(section_filtered, lambda x: x['section_block_id']):
        list_section = list(section)
        per_assignment_types_grades = []
        grades_per_section = {}
        for assignment_type in policy:
            filter_by_at = filter(lambda x: x['category'] == assignment_type['type'], list_section)
            # We only compute a total per assignment type if it belongs to the given section.
            if assignment_type['actual_count'] > 0 and len(filter_by_at) > 0:
                total_by_at = sum(item['percent'] for item in filter_by_at) / assignment_type['actual_count']
                max_possible_total_by_at = sum(MAX_PERCENTAGE_GRADE for item in filter_by_at) / assignment_type['actual_count']
                section_percent_by_at = total_by_at * assignment_type['weight']
                max_section_percent_by_at = max_possible_total_by_at * assignment_type['weight']
                per_assignment_types_grades.append({
                    'type': assignment_type['type'],
                    'grade': section_percent_by_at,
                    'max_possible_grade': max_section_percent_by_at
                })
        total_by_section = sum(item['grade'] for item in per_assignment_types_grades)
        max_total_by_section = sum(item['max_possible_grade'] for item in per_assignment_types_grades)
        grades_per_section = {
            'key': key,
            'assignment_types': per_assignment_types_grades,
            'percent': total_by_section,
            'max_possible_percent': max_total_by_section,
            'section_display_name': list_section[0]['section_display_name']
        }
        section_by_assignment_type.append(grades_per_section)
    return section_by_assignment_type


def assign_assignment_type_count(data, course_policy):
    """
    Util function to calculate the total of assign assignment types, in the course.

    Returns:
        Update course_policy object adding a new actual_count key with the calculated value.
    """
    policy = []
    for assignment_type in course_policy['GRADER']:
        at_list = filter(lambda x: x['category'] == assignment_type['type'], data['section_filtered'])
        total_count = len(at_list)
        policy.append({
            'weight': assignment_type['weight'],
            'type': assignment_type['type'],
            'actual_count': total_count
        })
    return policy


def calculate_up_to_data_grade(data, section_block_id=None):
    """
    Util function to calculate up-to-date-grade value,
    depending on the max possible points that each student can reach.

    Returns:
        Update data object put it in a new key with up-to-date-grade value.
    """
    up_to_date_grade = 0
    max_possible_total_percent = 0
    total_percent = 0
    ENTIRE_COURSE = _("All course sections")
    if section_block_id:
        for item in data['section_grades']:
            total_percent += item['percent']
            max_possible_total_percent += item['max_possible_percent']
            if section_block_id == item['key']:
                unreleased_section = data['section_grades'][-1]
                if unreleased_section['key'] == 'Unreleased' and section_block_id is None:
                    total_percent += unreleased_section['percent']
                    max_possible_total_percent += unreleased_section['max_possible_percent']
                break
        up_to_date_grade = total_percent / max_possible_total_percent
        return {
            'calculated_until_section': section_block_id,
            'percent': up_to_date_grade
        }
    else:
        return {
            'calculated_until_section': ENTIRE_COURSE,
            'percent': data['percent']
        }


def delete_unwanted_keys(data, keys_to_delete):
    """
    Util function to delete unwanted keys inside a dict object by
    a keys_to_delete list, with the name of the keys to remove.

    Returns:
        Same object input but no wanted keys in it.
    """
    for key in keys_to_delete:
        if data.get(key) or data.has_key(key):
            del data[key]
        else:
            # If the key doesn't exist at the top of data,
            # we search it inside a section_grades.
            for item in data['section_grades']:
                del item[key]
    return data


def get_course_subsections(sections):
    """
    Function used to get all problems by subsection in all the course tree.

    Returns:
        Object list ordered by all problem's tree, with his own name, id, possible points,
        and earned points by student.
    """
    problem_breakdown = []
    for key, element in sections.items():
        for subsection in element['sections']:
            for location, score in subsection.problem_scores.items():
                problem_locator = modulestore().get_item(location)
                summary_format = u"{section_name} - {subsection_name} - {problem_name}"
                summary = summary_format.format(
                    section_name=element['display_name'],
                    subsection_name=subsection.display_name,
                    problem_name=problem_locator.display_name,
                )
                problem_data = {
                    'problem_block_name': summary,
                    'problem_block_id': location.block_id,
                    'earned': score.earned,
                    'possible': score.possible,
                    'attempted': True if score.first_attempted else False,
                }
                problem_breakdown.append(problem_data)
    return problem_breakdown


def add_section_info_to_breakdown(grader_result, grader_by_format):
    """
    Util function to add section_block_id and section_display_name keys
    to each item in section_breakdown dict to identify the parent
    section to each item belogns to.
    """
    section_breakdown = filter(filter_average_sections, grader_result['section_breakdown'])
    for key, value in groupby(section_breakdown, lambda x: x['category']):
        subsection_grades = grader_by_format.get(key, {}).values()
        group_items = list(value)
        for index in range(max(len(subsection_grades), len(group_items))):
            if index < len(subsection_grades):
                parent_location = modulestore().get_parent_location(subsection_grades[index].location)
                parent_item = modulestore().get_item(parent_location)
                group_items[index]['section_block_id'] = parent_location.block_id
                group_items[index]['section_display_name'] = parent_item.display_name
            else:
                group_items[index]['section_block_id'] = 'Unreleased'
                group_items[index]['section_display_name'] = 'Unreleased'

    return grader_result


def filter_average_sections(item):
    """
    Function to filter only items that has Avergae in his detail key
    """
    if 'Average' in item['detail'] and 'prominent' in item:
        return False

    return True
