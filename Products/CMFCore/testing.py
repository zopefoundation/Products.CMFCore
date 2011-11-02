##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit test mixin classes and layers. """

from OFS.SimpleItem import SimpleItem
from Testing.ZopeTestCase import installPackage
from Testing.ZopeTestCase.layer import ZopeLite
from zope.component import adapts
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.interface import implements
from zope.interface.verify import verifyClass
from zope.publisher.interfaces.http import IHTTPRequest
from zope.site.hooks import setHooks
from zope.testing import testrunner
from zope.testing.cleanup import cleanUp

from Products.CMFCore.interfaces import IWorkflowDefinition
from Products.GenericSetup.utils import BodyAdapterBase

# BBB for Zope 2.12
try:
    from Zope2.App import zcml
except ImportError:
    from Products.Five import zcml


class ConformsToFolder:

    def test_folder_interfaces(self):
        from webdav.interfaces import IWriteLock
        from Products.CMFCore.interfaces import IDynamicType
        from Products.CMFCore.interfaces import IFolderish
        from Products.CMFCore.interfaces import IMutableMinimalDublinCore

        verifyClass(IDynamicType, self._getTargetClass())
        verifyClass(IFolderish, self._getTargetClass())
        verifyClass(IMutableMinimalDublinCore, self._getTargetClass())
        verifyClass(IWriteLock, self._getTargetClass())

    def test_folder_extra_interfaces(self):
        # in the long run this interface will become deprecated
        from Products.CMFCore.interfaces import IOpaqueItemManager

        verifyClass(IOpaqueItemManager, self._getTargetClass())


class ConformsToContent:

    def test_content_interfaces(self):
        from Products.CMFCore.interfaces import ICatalogableDublinCore
        from Products.CMFCore.interfaces import IContentish
        from Products.CMFCore.interfaces import IDublinCore
        from Products.CMFCore.interfaces import IDynamicType
        from Products.CMFCore.interfaces import IMutableDublinCore
        from Products.GenericSetup.interfaces import IDAVAware

        verifyClass(ICatalogableDublinCore, self._getTargetClass())
        verifyClass(IContentish, self._getTargetClass())
        verifyClass(IDAVAware, self._getTargetClass())
        verifyClass(IDublinCore, self._getTargetClass())
        verifyClass(IDynamicType, self._getTargetClass())
        verifyClass(IMutableDublinCore, self._getTargetClass())

    def test_content_extra_interfaces(self):
        # in the long run these interfaces will become deprecated
        from Products.CMFCore.interfaces import ICatalogAware
        from Products.CMFCore.interfaces import IOpaqueItemManager
        from Products.CMFCore.interfaces import IWorkflowAware

        verifyClass(ICatalogAware, self._getTargetClass())
        verifyClass(IOpaqueItemManager, self._getTargetClass())
        verifyClass(IWorkflowAware, self._getTargetClass())


class BrowserLanguages(object):

    implements(IUserPreferredLanguages)
    adapts(IHTTPRequest)

    def __init__(self, context):
        self.context = context

    def getPreferredLanguages(self):
        return ('test',)


class OFSZCMLLayer(ZopeLite):

    @classmethod
    def setUp(cls):
        import zope.component
        import OFS
        import Products.Five
        zcml.load_config('meta.zcml', zope.component)
        try:
            zcml.load_config('meta.zcml', OFS)
            zcml.load_config('configure.zcml', OFS)
        except IOError:  # Zope <= 2.13.0a2
            zcml.load_config('meta.zcml', Products.Five)
        # In Zope 2.12 this does an implicit commit
        installPackage('OFS')
        setHooks()

    @classmethod
    def tearDown(cls):
        cleanUp()


class EventZCMLLayer(ZopeLite):

    @classmethod
    def testSetUp(cls):
        import OFS
        import Products

        zcml.load_config('meta.zcml', Products.Five)
        try:
            zcml.load_config('event.zcml', OFS)
        except IOError:  # Zope <= 2.12.x
            zcml.load_config('event.zcml', Products.Five)
        zcml.load_config('event.zcml', Products.CMFCore)
        setHooks()

    @classmethod
    def testTearDown(cls):
        cleanUp()


class TraversingZCMLLayer(ZopeLite):

    @classmethod
    def testSetUp(cls):
        import Products.Five
        import zope.traversing

        zcml.load_config('meta.zcml', Products.Five)
        zcml.load_config('configure.zcml', zope.traversing)
        setHooks()

    @classmethod
    def testTearDown(cls):
        cleanUp()


class TraversingEventZCMLLayer(ZopeLite):

    @classmethod
    def testSetUp(cls):
        import Products.Five
        import zope.traversing

        zcml.load_config('meta.zcml', Products.Five)
        zcml.load_config('configure.zcml', zope.traversing)
        zcml.load_config('event.zcml', Products.Five)
        zcml.load_config('event.zcml', Products.CMFCore)
        setHooks()

    @classmethod
    def testTearDown(cls):
        cleanUp()


class FunctionalZCMLLayer(ZopeLite):

    @classmethod
    def setUp(cls):
        import Products

        zcml.load_config('testing.zcml', Products.CMFCore)
        setHooks()

    @classmethod
    def tearDown(cls):
        cleanUp()


_DUMMY_ZCML = """\
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:five="http://namespaces.zope.org/five"
    i18n_domain="dummy">
  <permission id="dummy.add" title="Add Dummy Workflow"/>
  <five:registerClass
      class="Products.CMFCore.testing.DummyWorkflow"
      meta_type="Dummy Workflow"
      permission="dummy.add"
      addview="addDummyWorkflow.html"
      global="false"
      />
  <adapter
      factory="Products.CMFCore.testing.DummyWorkflowBodyAdapter"
      provides="Products.GenericSetup.interfaces.IBody"
      for="Products.CMFCore.interfaces.IWorkflowDefinition
           Products.GenericSetup.interfaces.ISetupEnviron"
      />
</configure>
"""


class DummyWorkflow(SimpleItem):

    implements(IWorkflowDefinition)

    meta_type = 'Dummy Workflow'

    def __init__(self, id):
        self._id = id

    def getId(self):
        return self._id


class DummyWorkflowBodyAdapter(BodyAdapterBase):

    body = property(BodyAdapterBase._exportBody, BodyAdapterBase._importBody)


class ExportImportZCMLLayer(ZopeLite):

    @classmethod
    def testSetUp(cls):
        import Zope2.App
        import AccessControl
        import Products.Five
        import Products.GenericSetup
        import Products.CMFCore
        import Products.CMFCore.exportimport

        try:
            zcml.load_config('meta.zcml', Zope2.App)
        except IOError:  # Zope <= 2.12.x
            pass

        zcml.load_config('meta.zcml', Products.Five)

        try:
            zcml.load_config('permissions.zcml', AccessControl)
        except IOError:  # Zope <= 2.12.x
            pass

        zcml.load_config('permissions.zcml', Products.Five)

        zcml.load_config('meta.zcml', Products.GenericSetup)
        zcml.load_config('configure.zcml', Products.GenericSetup)
        zcml.load_config('permissions.zcml', Products.CMFCore)
        zcml.load_config('tool.zcml', Products.CMFCore)
        zcml.load_config('configure.zcml', Products.CMFCore.exportimport)
        zcml.load_string(_DUMMY_ZCML)
        setHooks()

    @classmethod
    def testTearDown(cls):
        cleanUp()


def run(test_suite):
    options = testrunner.get_options()
    options.resume_layer = None
    options.resume_number = 0
    testrunner.run_with_options(options, test_suite)
