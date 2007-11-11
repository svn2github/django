"""
Regression tests for the Test Client, especially the customized assertions.

"""
from django.test import Client, TestCase
from django.core import mail
import os

class AssertContainsTests(TestCase):
    def test_contains(self):
        "Responses can be inspected for content, including counting repeated substrings"
        response = self.client.get('/test_client_regress/no_template_view/')

        self.assertContains(response, 'never', 0)
        self.assertContains(response, 'once')
        self.assertContains(response, 'once', 1)
        self.assertContains(response, 'twice')
        self.assertContains(response, 'twice', 2)

        try:
            self.assertContains(response, 'never', 1)
        except AssertionError, e:
            self.assertEquals(str(e), "Found 0 instances of 'never' in response (expected 1)")

        try:
            self.assertContains(response, 'once', 0)
        except AssertionError, e:
            self.assertEquals(str(e), "Found 1 instances of 'once' in response (expected 0)")

        try:
            self.assertContains(response, 'once', 2)
        except AssertionError, e:
            self.assertEquals(str(e), "Found 1 instances of 'once' in response (expected 2)")

        try:
            self.assertContains(response, 'twice', 1)
        except AssertionError, e:
            self.assertEquals(str(e), "Found 2 instances of 'twice' in response (expected 1)")

        try:
            self.assertContains(response, 'thrice')
        except AssertionError, e:
            self.assertEquals(str(e), "Couldn't find 'thrice' in response")

        try:
            self.assertContains(response, 'thrice', 3)
        except AssertionError, e:
            self.assertEquals(str(e), "Found 0 instances of 'thrice' in response (expected 3)")

class AssertTemplateUsedTests(TestCase):
    fixtures = ['testdata.json']

    def test_no_context(self):
        "Template usage assertions work then templates aren't in use"
        response = self.client.get('/test_client_regress/no_template_view/')

        # Check that the no template case doesn't mess with the template assertions
        self.assertTemplateNotUsed(response, 'GET Template')

        try:
            self.assertTemplateUsed(response, 'GET Template')
        except AssertionError, e:
            self.assertEquals(str(e), "No templates used to render the response")

    def test_single_context(self):
        "Template assertions work when there is a single context"
        response = self.client.get('/test_client/post_view/', {})

        #
        try:
            self.assertTemplateNotUsed(response, 'Empty GET Template')
        except AssertionError, e:
            self.assertEquals(str(e), "Template 'Empty GET Template' was used unexpectedly in rendering the response")

        try:
            self.assertTemplateUsed(response, 'Empty POST Template')
        except AssertionError, e:
            self.assertEquals(str(e), "Template 'Empty POST Template' was not a template used to render the response. Actual template(s) used: Empty GET Template")

    def test_multiple_context(self):
        "Template assertions work when there are multiple contexts"
        post_data = {
            'text': 'Hello World',
            'email': 'foo@example.com',
            'value': 37,
            'single': 'b',
            'multi': ('b','c','e')
        }
        response = self.client.post('/test_client/form_view_with_template/', post_data)
        self.assertContains(response, 'POST data OK')
        try:
            self.assertTemplateNotUsed(response, "form_view.html")
        except AssertionError, e:
            self.assertEquals(str(e), "Template 'form_view.html' was used unexpectedly in rendering the response")

        try:
            self.assertTemplateNotUsed(response, 'base.html')
        except AssertionError, e:
            self.assertEquals(str(e), "Template 'base.html' was used unexpectedly in rendering the response")

        try:
            self.assertTemplateUsed(response, "Valid POST Template")
        except AssertionError, e:
            self.assertEquals(str(e), "Template 'Valid POST Template' was not a template used to render the response. Actual template(s) used: form_view.html, base.html")

class AssertRedirectsTests(TestCase):
    def test_redirect_page(self):
        "An assertion is raised if the original page couldn't be retrieved as expected"
        # This page will redirect with code 301, not 302
        response = self.client.get('/test_client/permanent_redirect_view/')
        try:
            self.assertRedirects(response, '/test_client/get_view/')
        except AssertionError, e:
            self.assertEquals(str(e), "Response didn't redirect as expected: Response code was 301 (expected 302)")

    def test_lost_query(self):
        "An assertion is raised if the redirect location doesn't preserve GET parameters"
        response = self.client.get('/test_client/redirect_view/', {'var': 'value'})
        try:
            self.assertRedirects(response, '/test_client/get_view/')
        except AssertionError, e:
            self.assertEquals(str(e), "Response redirected to 'http://testserver/test_client/get_view/?var=value', expected 'http://testserver/test_client/get_view/'")

    def test_incorrect_target(self):
        "An assertion is raised if the response redirects to another target"
        response = self.client.get('/test_client/permanent_redirect_view/')
        try:
            # Should redirect to get_view
            self.assertRedirects(response, '/test_client/some_view/')
        except AssertionError, e:
            self.assertEquals(str(e), "Response didn't redirect as expected: Response code was 301 (expected 302)")

    def test_target_page(self):
        "An assertion is raised if the response redirect target cannot be retrieved as expected"
        response = self.client.get('/test_client/double_redirect_view/')
        try:
            # The redirect target responds with a 301 code, not 200
            self.assertRedirects(response, 'http://testserver/test_client/permanent_redirect_view/')
        except AssertionError, e:
            self.assertEquals(str(e), "Couldn't retrieve redirection page '/test_client/permanent_redirect_view/': response code was 301 (expected 200)")

class AssertFormErrorTests(TestCase):
    def test_unknown_form(self):
        "An assertion is raised if the form name is unknown"
        post_data = {
            'text': 'Hello World',
            'email': 'not an email address',
            'value': 37,
            'single': 'b',
            'multi': ('b','c','e')
        }
        response = self.client.post('/test_client/form_view/', post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Invalid POST Template")

        try:
            self.assertFormError(response, 'wrong_form', 'some_field', 'Some error.')
        except AssertionError, e:
            self.assertEqual(str(e), "The form 'wrong_form' was not used to render the response")

    def test_unknown_field(self):
        "An assertion is raised if the field name is unknown"
        post_data = {
            'text': 'Hello World',
            'email': 'not an email address',
            'value': 37,
            'single': 'b',
            'multi': ('b','c','e')
        }
        response = self.client.post('/test_client/form_view/', post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Invalid POST Template")

        try:
            self.assertFormError(response, 'form', 'some_field', 'Some error.')
        except AssertionError, e:
            self.assertEqual(str(e), "The form 'form' in context 0 does not contain the field 'some_field'")

    def test_noerror_field(self):
        "An assertion is raised if the field doesn't have any errors"
        post_data = {
            'text': 'Hello World',
            'email': 'not an email address',
            'value': 37,
            'single': 'b',
            'multi': ('b','c','e')
        }
        response = self.client.post('/test_client/form_view/', post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Invalid POST Template")

        try:
            self.assertFormError(response, 'form', 'value', 'Some error.')
        except AssertionError, e:
            self.assertEqual(str(e), "The field 'value' on form 'form' in context 0 contains no errors")

    def test_unknown_error(self):
        "An assertion is raised if the field doesn't contain the provided error"
        post_data = {
            'text': 'Hello World',
            'email': 'not an email address',
            'value': 37,
            'single': 'b',
            'multi': ('b','c','e')
        }
        response = self.client.post('/test_client/form_view/', post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Invalid POST Template")

        try:
            self.assertFormError(response, 'form', 'email', 'Some error.')
        except AssertionError, e:
            self.assertEqual(str(e), "The field 'email' on form 'form' in context 0 does not contain the error 'Some error.' (actual errors: [u'Enter a valid e-mail address.'])")

    def test_unknown_nonfield_error(self):
        """
        Checks that an assertion is raised if the form's non field errors
        doesn't contain the provided error.
        """
        post_data = {
            'text': 'Hello World',
            'email': 'not an email address',
            'value': 37,
            'single': 'b',
            'multi': ('b','c','e')
        }
        response = self.client.post('/test_client/form_view/', post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Invalid POST Template")

        try:
            self.assertFormError(response, 'form', None, 'Some error.')
        except AssertionError, e:
            self.assertEqual(str(e), "The form 'form' in context 0 does not contain the non-field error 'Some error.' (actual errors: )")

class FileUploadTests(TestCase):
    def test_simple_upload(self):
        fd = open(os.path.join(os.path.dirname(__file__), "views.py"))
        post_data = {
            'name': 'Ringo',
            'file_field': fd,
        }
        response = self.client.post('/test_client_regress/file_upload/', post_data)
        self.assertEqual(response.status_code, 200)

class LoginTests(TestCase):
    fixtures = ['testdata']

    def test_login_different_client(self):
        "Check that using a different test client doesn't violate authentication"

        # Create a second client, and log in.
        c = Client()
        login = c.login(username='testclient', password='password')
        self.failUnless(login, 'Could not log in')

        # Get a redirection page with the second client.
        response = c.get("/test_client_regress/login_protected_redirect_view/")

        # At this points, the self.client isn't logged in.
        # Check that assertRedirects uses the original client, not the
        # default client.
        self.assertRedirects(response, "http://testserver/test_client_regress/get_view/")
