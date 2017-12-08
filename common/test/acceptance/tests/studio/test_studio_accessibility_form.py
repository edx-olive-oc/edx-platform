"""
Bok-choy tests for the Studio Accessibility Feedback page.
"""
from common.test.acceptance.pages.studio.index import AccessibilityPage
from common.test.acceptance.tests.helpers import AcceptanceTest


class AccessibilityPageTest(AcceptanceTest):
    """
    Test that a user can access the page and submit studio accessibility feedback.
    """

    def setUp(self):
        """
        Load the helper for the accessibility page.
        """
        super(AccessibilityPageTest, self).setUp()
        self.accessibility_page = AccessibilityPage(self.browser)

    def test_page_loads(self):
        """
        Test if the page loads and that there is a header and input elements.
        """
        self.accessibility_page.visit()
        self.assertTrue(self.accessibility_page.header_text_on_page())

    def test_successful_submit(self):
        """
        Test filling out the accessibility feedback form out and submitting.
        """
        self.accessibility_page.visit()
        self.accessibility_page.fill_form(email='bokchoy@edx.org', name='Bok-choy', message='I\'m testing you.')
        self.accessibility_page.submit_form()
        self.accessibility_page.success_alert_shown()

    def test_error_submit_no_email(self):
        """
        Test filling out the accessibility feedback form out with missing email and submitting.
        """
        self.accessibility_page.visit()
        self.accessibility_page.fill_form(email='', name='Bok-choy', message='I\'m testing you.')
        self.accessibility_page.submit_form()
        self.accessibility_page.error_alert_shown()
        self.accessibility_page.alert_has_text('email')

    def test_error_submit_no_name(self):
        """
        Test filling out the accessibility feedback form out with missing name and submitting.
        """
        self.accessibility_page.visit()
        self.accessibility_page.fill_form(email='bokchoy@edx.org', name='', message='I\'m testing you.')
        self.accessibility_page.submit_form()
        self.accessibility_page.error_alert_shown()
        self.accessibility_page.alert_has_text('Full name')

    def test_error_submit_no_message(self):
        """
        Test filling out the accessibility feedback form out with missing message and submitting.
        """
        self.accessibility_page.visit()
        self.accessibility_page.fill_form(email='bokchoy@edx.org', name='Bok-choy', message='')
        self.accessibility_page.submit_form()
        self.accessibility_page.error_alert_shown()
        self.accessibility_page.alert_has_text('Message')

    def test_error_messages(self):
        self.accessibility_page.visit()

        self.accessibility_page.leave_field_blank('email')
        self.accessibility_page.error_message_is_shown_with_text('email', text='email')

        self.accessibility_page.leave_field_blank('fullName')
        self.accessibility_page.error_message_is_shown_with_text('fullName', text='Full name')

        self.accessibility_page.leave_field_blank('message', field_type='textarea')
        self.accessibility_page.error_message_is_shown_with_text('message', text='Message')
