# XXX This uses Plone testing stuff.
# from collective.explicitacquisition.testing import BASE_FUNCTIONAL_TESTING
# from plone.testing.z2 import Browser
# from six.moves.urllib.error import HTTPError
# from zope.interface import alsoProvides
# from plone.app.testing import setRoles
# from plone.app.testing import TEST_USER_ID
# from plone.app.testing import TEST_USER_NAME
# from plone.app.testing import TEST_USER_PASSWORD

# import unittest


# class TestBadAcquisition(unittest.TestCase):
#     layer = BASE_FUNCTIONAL_TESTING

#     def setUp(self):
#         self.portal = self.layer["portal"]
#         self.app = self.layer["app"]
#         setRoles(self.portal, TEST_USER_ID, ["Manager"])

#     def test_not_found_when_acquired_content(self):
#         "browsing to acquired content should trigger a 404"
#         self.portal.invokeFactory("Document", "a_page")
#         self.assertTrue("a_page" in self.portal.objectIds())
#         self.portal.invokeFactory("Folder", "a_folder")
#         self.assertTrue("a_folder" in self.portal.objectIds())
#         import transaction

#         transaction.commit()
#         browser = Browser(self.app)

#         # login
#         browser.open(self.portal.absolute_url() + "/login")
#         browser.getControl(name="__ac_name").value = TEST_USER_NAME
#         browser.getControl(name="__ac_password").value = TEST_USER_PASSWORD
#         browser.getControl(name="buttons.login").click()

#         browser.open(self.portal.a_page.absolute_url())
#         error = None
#         try:
#             url = self.portal.absolute_url() + "/a_folder/a_page"
#             browser.open(url)
#         except HTTPError as ex:
#             error = ex
#         self.assertIsNotNone(error, msg="Acquired content should not be published.")
#         self.assertEqual(404, error.code)

#     def test_not_found_when_template_on_acquired_content(self):
#         "browsing to template on acquired content should trigger a 404"
#         self.portal.invokeFactory("Document", "a_page")
#         self.assertIn("a_page", self.portal.objectIds())
#         self.portal.invokeFactory("Folder", "a_folder")
#         self.assertIn("a_folder", self.portal.objectIds())
#         import transaction

#         transaction.commit()
#         browser = Browser(self.app)

#         # login
#         browser.open(self.portal.absolute_url() + "/login")
#         browser.getControl(name="__ac_name").value = TEST_USER_NAME
#         browser.getControl(name="__ac_password").value = TEST_USER_PASSWORD
#         browser.getControl(name="buttons.login").click()

#         browser.open(self.portal.a_page.absolute_url())
#         error = None
#         try:
#             url = self.portal.absolute_url() + "/a_folder/a_page/document_view"
#             browser.open(url)
#         except HTTPError as ex:
#             error = ex
#         self.assertIsNotNone(error, msg="Acquired content should not be published.")
#         self.assertEqual(404, error.code)

#     def test_allow_publication_trough_acquisition_explicitely(self):
#         self.portal.invokeFactory("Document", "a_page")
#         self.assertIn("a_page", self.portal.objectIds())
#         a_page = self.portal["a_page"]
#         try:
#             from Products.CMFPlone.interfaces import IPublishableThroughAcquisition
#         except ImportError:
#             from collective.explicitacquisition.interfaces import (
#                 IPublishableThroughAcquisition,
#             )
#         alsoProvides(a_page, IPublishableThroughAcquisition)
#         self.portal.invokeFactory("Folder", "a_folder")
#         self.assertIn("a_folder", self.portal.objectIds())
#         import transaction

#         transaction.commit()
#         browser = Browser(self.app)
#         browser.open(self.portal.a_page.absolute_url())
#         error = None
#         try:
#             url = self.portal.absolute_url() + "/a_folder/a_page"
#             browser.open(url)
#         except HTTPError as ex:
#             error = ex
#         self.assertIsNone(error)
