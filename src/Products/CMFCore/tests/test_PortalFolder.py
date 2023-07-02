##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for PortalFolder module.
"""

import unittest

import transaction
from AccessControl import SecurityManager
from AccessControl import Unauthorized
from AccessControl.SecurityManagement import newSecurityManager
from Acquisition import Implicit
from Acquisition import aq_base
from DateTime import DateTime
from OFS.Image import manage_addFile
from zope.component import getSiteManager
from zope.component.interfaces import IFactory
from zope.interface import implementer
from zope.interface.verify import verifyClass

from ..exceptions import BadRequest
from ..interfaces import ICatalogTool
from ..interfaces import ITypesTool
from ..interfaces import IWorkflowTool
from ..testing import ConformsToFolder
from ..testing import TraversingEventZCMLLayer
from ..TypesTool import FactoryTypeInformation as FTI
from ..TypesTool import TypesTool
from ..WorkflowTool import WorkflowTool
from .base.dummy import DummyContent
from .base.dummy import DummyFactoryDispatcher
from .base.dummy import DummySite
from .base.dummy import DummyUserFolder
from .base.testcase import SecurityTest
from .base.tidata import FTIDATA_CMF
from .base.tidata import FTIDATA_DUMMY


def extra_meta_types():
    return [{'name': 'Dummy', 'action': 'manage_addFolder',
             'permission': 'View'}]


@implementer(ICatalogTool)
class DummyCatalogTool:

    def __init__(self):
        self.paths = []
        self.ids = []

    def indexObject(self, object):
        self.paths.append('/'.join(object.getPhysicalPath()))
        self.ids.append(object.getId())

    def unindexObject(self, object):
        self.paths.remove('/'.join(object.getPhysicalPath()))
        self.ids.append(object.getId())

    def reindexObject(self, object):
        pass

    def __len__(self):
        return len(self.paths)


def has_path(catalog, path):
    if isinstance(path, tuple):
        path = '/'.join(path)
    return path in catalog.paths


def has_id(catalog, id):
    return id in catalog.ids


class PortalFolderFactoryTests(SecurityTest):

    layer = TraversingEventZCMLLayer
    _PORTAL_TYPE = 'Test Folder'

    def _getTargetObject(self):
        from ..PortalFolder import PortalFolderFactory

        return PortalFolderFactory

    def setUp(self):
        from ..PortalFolder import PortalFolder

        SecurityTest.setUp(self)
        self.site = DummySite('site').__of__(self.app)
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)

        self.ttool = ttool = TypesTool()
        ttool._setObject(self._PORTAL_TYPE,
                         FTI(id=self._PORTAL_TYPE,
                             title='Folder or Directory',
                             meta_type=PortalFolder.meta_type,
                             factory='cmf.folder',
                             filter_content_types=0))
        ttool._setObject('Dummy Content', FTI(**FTIDATA_DUMMY[0].copy()))
        sm = getSiteManager()
        sm.registerUtility(ttool, ITypesTool)
        sm.registerUtility(self._getTargetObject(), IFactory, 'cmf.folder')

        self.f = self.site._setObject('container', PortalFolder('container'))
        self.f._setPortalTypeName(self._PORTAL_TYPE)

    def test_invokeFactory(self):
        f = self.f
        self.assertFalse('foo' in f.objectIds())

        f.manage_addProduct = {'FooProduct': DummyFactoryDispatcher(f)}
        f.invokeFactory(type_name='Dummy Content', id='foo')

        self.assertTrue('foo' in f.objectIds())
        foo = f.foo
        self.assertEqual(foo.getId(), 'foo')
        self.assertEqual(foo.getPortalTypeName(), 'Dummy Content')
        self.assertEqual(foo.Type(), 'Dummy Content Title')

    def test_invokeFactory_disallowed_type(self):
        f = self.f
        ftype = getattr(self.ttool, self._PORTAL_TYPE)
        ftype.filter_content_types = 1
        self.assertRaises(ValueError,
                          f.invokeFactory, self._PORTAL_TYPE, 'sub')

        ftype.allowed_content_types = (self._PORTAL_TYPE,)
        f.invokeFactory(self._PORTAL_TYPE, id='sub')
        self.assertTrue('sub' in f.objectIds())
        self.assertRaises(ValueError, f.invokeFactory, 'Dummy Content', 'foo')


class PortalFolderTests(ConformsToFolder, unittest.TestCase):

    def _getTargetClass(self):
        from ..PortalFolder import PortalFolder

        return PortalFolder

    def test_interfaces(self):
        from OFS.interfaces import IOrderedContainer

        verifyClass(IOrderedContainer, self._getTargetClass())

    def test_FolderFilter(self):
        folder = self._getTargetClass()('test_id')

        # No filter
        request = {}
        encoded_filter = folder.encodeFolderFilter(request)
        self.assertEqual(folder.decodeFolderFilter(encoded_filter), {})

        # Simple filter
        request = {'filter_by_id': 'foobar'}
        encoded_filter = folder.encodeFolderFilter(request)
        self.assertEqual(folder.decodeFolderFilter(encoded_filter),
                         {'id': 'foobar'})

        # Multiple filters
        request = {'filter_by_id': 'foobar',
                   'filter_by_title': 'baz'}
        encoded_filter = folder.encodeFolderFilter(request)
        self.assertEqual(folder.decodeFolderFilter(encoded_filter),
                         {'id': 'foobar', 'title': 'baz'})

        # Non-filter request values are ignored
        request = {'filter_by_id': 'foobar', 'somekey': 'somevalue'}
        encoded_filter = folder.encodeFolderFilter(request)
        self.assertEqual(folder.decodeFolderFilter(encoded_filter),
                         {'id': 'foobar'})

        # Conspicuously large input values to the decode operation
        # are ignored to prevent a DOS
        encoded_filter = 'x' * 2000
        self.assertEqual(folder.decodeFolderFilter(encoded_filter), {})


class PortalFolderSecurityTests(SecurityTest):

    layer = TraversingEventZCMLLayer

    def _getTargetClass(self):
        from ..PortalFolder import PortalFolder

        return PortalFolder

    def _makeOne(self, id, *args, **kw):
        return self.site._setObject(id,
                                    self._getTargetClass()(id, *args, **kw))

    def setUp(self):
        SecurityTest.setUp(self)
        self.site = DummySite('site').__of__(self.app)

    def test_contents_methods(self):
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)

        ttool = TypesTool()
        getSiteManager().registerUtility(ttool, ITypesTool)

        f = self._makeOne('foo')
        self.assertEqual(f.objectValues(), [])
        self.assertEqual(f.contentIds(), [])
        self.assertEqual(f.contentItems(), [])
        self.assertEqual(f.contentValues(), [])
        self.assertEqual(f.listFolderContents(), [])
        self.assertEqual(f.listDAVObjects(), [])

        f._setObject('sub1', DummyContent('sub1'))
        self.assertEqual(f.objectValues(), [f.sub1])
        self.assertEqual(f.contentIds(), [])
        self.assertEqual(f.contentItems(), [])
        self.assertEqual(f.contentValues(), [])
        self.assertEqual(f.listFolderContents(), [])
        self.assertEqual(f.listDAVObjects(), [f.sub1])

        fti = FTIDATA_DUMMY[0].copy()
        ttool._setObject('Dummy Content', FTI(**fti))
        self.assertEqual(f.objectValues(), [f.sub1])
        self.assertEqual(f.contentIds(), ['sub1'])
        self.assertEqual(f.contentItems(), [('sub1', f.sub1)])
        self.assertEqual(f.contentValues(), [f.sub1])
        self.assertEqual(f.listFolderContents(), [f.sub1])
        self.assertEqual(f.listDAVObjects(), [f.sub1])

        f._setObject('hidden_sub2', DummyContent('hidden_sub2'))
        self.assertEqual(f.objectValues(), [f.sub1, f.hidden_sub2])
        self.assertEqual(f.contentIds(), ['sub1', 'hidden_sub2'])
        self.assertEqual(f.contentItems(), [('sub1', f.sub1),
                                            ('hidden_sub2', f.hidden_sub2)])
        self.assertEqual(f.contentValues(), [f.sub1, f.hidden_sub2])
        self.assertEqual(f.listFolderContents(), [f.sub1])
        self.assertEqual(f.listDAVObjects(), [f.sub1, f.hidden_sub2])

    def test_deletePropagation(self):
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        test = self._makeOne('test')
        foo = DummyContent('foo')
        foo.reset()
        self.assertFalse(foo.after_add_called)
        self.assertFalse(foo.before_delete_called)

        test._setObject('foo', foo)
        self.assertTrue(foo.after_add_called)
        self.assertFalse(foo.before_delete_called)

        foo.reset()
        test._delObject('foo')
        self.assertFalse(foo.after_add_called)
        self.assertTrue(foo.before_delete_called)

        foo.reset()
        test._setObject('foo', foo)
        test._delOb('foo')    # doesn't propagate
        self.assertTrue(foo.after_add_called)
        self.assertFalse(foo.before_delete_called)

    def test_manageDelObjects(self):
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        test = self._makeOne('test')
        foo = DummyContent('foo')

        test._setObject('foo', foo)
        foo.reset()
        test.manage_delObjects(ids=['foo'])
        self.assertFalse(foo.after_add_called)
        self.assertTrue(foo.before_delete_called)

    def test_catalogUnindexAndIndex(self):
        #
        # Test is a new object does get cataloged upon _setObject
        # and uncataloged upon manage_deleteObjects
        #
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        test = self._makeOne('test')
        ctool = DummyCatalogTool()
        self.assertEqual(len(ctool), 0)
        sm = getSiteManager()
        sm.registerUtility(ctool, ICatalogTool)
        sm.registerUtility(TypesTool(), ITypesTool)

        test._setObject('foo', DummyContent('foo', catalog=1))
        foo = test.foo
        self.assertTrue(foo.after_add_called)
        self.assertFalse(foo.before_delete_called)
        self.assertEqual(len(ctool), 1)

        foo.reset()
        test._delObject('foo')
        self.assertFalse(foo.after_add_called)
        self.assertTrue(foo.before_delete_called)
        self.assertEqual(len(ctool), 0)

    def test_portalfolder_cataloging(self):
        #
        # Test to ensure a portal folder itself is *not* cataloged upon
        # instantiation (Tracker issue 309)
        #
        ctool = DummyCatalogTool()
        wtool = WorkflowTool()
        sm = getSiteManager()
        sm.registerUtility(ctool, ICatalogTool)
        sm.registerUtility(wtool, IWorkflowTool)

        test = self._makeOne('test')
        wtool.notifyCreated(test)
        self.assertEqual(len(ctool), 0)

    def test_tracker261(self):
        #
        #   Tracker issue #261 says that content in a deleted folder
        #   is not being uncatalogued.  Try creating a subfolder with
        #   content object, and test.
        #
        from ..PortalFolder import PortalFolder

        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        test = self._makeOne('test')
        ctool = DummyCatalogTool()
        getSiteManager().registerUtility(ctool, ICatalogTool)
        self.assertEqual(len(ctool), 0)

        test._setObject('sub', PortalFolder('sub', ''))
        sub = test.sub

        sub._setObject('foo', DummyContent('foo', catalog=1))
        foo = sub.foo

        self.assertTrue(foo.after_add_called)
        self.assertFalse(foo.before_delete_called)
        self.assertEqual(len(ctool), 1)

        foo.reset()
        test._delObject('sub')
        self.assertFalse(foo.after_add_called)
        self.assertTrue(foo.before_delete_called)
        self.assertEqual(len(ctool), 0)

    def test_manageAddFolder(self):
        #
        #   Does MKDIR/MKCOL intercept work?
        #
        from ..PortalFolder import PortalFolder
        from ..PortalFolder import PortalFolderFactory

        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        test = self._makeOne('test')

        ttool = TypesTool()
        ttool._setObject('Folder',
                         FTI(id='Folder',
                             title='Folder or Directory',
                             meta_type=PortalFolder.meta_type,
                             factory='cmf.folder',
                             filter_content_types=0))
        ttool._setObject('Grabbed',
                         FTI('Grabbed',
                             title='Grabbed Content',
                             meta_type=PortalFolder.meta_type,
                             factory='cmf.folder'))
        sm = getSiteManager()
        sm.registerUtility(ttool, ITypesTool)
        sm.registerUtility(PortalFolderFactory, IFactory, 'cmf.folder')

        # First, test default behavior
        test.manage_addFolder(id='simple', title='Simple')
        self.assertEqual(test.simple.getPortalTypeName(), 'Folder')
        self.assertEqual(test.simple.Type(), 'Folder or Directory')
        self.assertEqual(test.simple.getId(), 'simple')
        self.assertEqual(test.simple.Title(), 'Simple')

        # Now, test overridden behavior
        ttool.Folder.setMethodAliases({'mkdir': 'grabbed'})

        class Grabbed:

            _grabbed_with = None

            def __init__(self, context):
                self._context = context

            def __call__(self, id):
                self._grabbed_with = id
                self._context._setOb(id, PortalFolder(id))
                self._context._getOb(id)._setPortalTypeName('Grabbed')

        self.app.grabbed = Grabbed(test)

        test.manage_addFolder(id='indirect', title='Indirect')
        self.assertEqual(test.indirect.getPortalTypeName(), 'Grabbed')
        self.assertEqual(test.indirect.Type(), 'Grabbed Content')
        self.assertEqual(test.indirect.getId(), 'indirect')
        self.assertEqual(test.indirect.Title(), 'Indirect')

    def test_contentPasteAllowedTypes(self):
        #
        #   _verifyObjectPaste() should honor allowed content types
        #
        ttool = TypesTool()
        getSiteManager().registerUtility(ttool, ITypesTool)
        fti = FTIDATA_DUMMY[0].copy()
        ttool._setObject('Dummy Content', FTI(**fti))
        ttool._setObject('Folder', FTI(**fti))
        sub1 = self._makeOne('sub1')
        sub1._setObject('dummy', DummyContent('dummy'))
        sub2 = self._makeOne('sub2')
        sub2.all_meta_types = extra_meta_types()

        # Allow adding of Dummy Content
        ttool.Folder.manage_changeProperties(filter_content_types=False)

        # Copy/paste should work fine
        cookie = sub1.manage_copyObjects(ids=['dummy'])
        sub2.manage_pasteObjects(cookie)

        # Disallow adding of Dummy Content
        ttool.Folder.manage_changeProperties(filter_content_types=True)

        # Now copy/paste should raise a ValueError
        cookie = sub1.manage_copyObjects(ids=('dummy',))
        self.assertRaises(ValueError, sub2.manage_pasteObjects, cookie)

    def test_contentPasteFollowsWorkflowGuards(self):
        #
        # Copy/Paste should obey workflow guards
        #
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        ttool = TypesTool()
        fti = FTIDATA_DUMMY[0].copy()
        ttool._setObject('Dummy Content', FTI(**fti))
        ttool._setObject('Folder', FTI(**fti))
        folder = self._makeOne('folder', 'Folder')
        content = self._makeOne('content')
        folder._setObject('content', content)
        sm = getSiteManager()
        sm.registerUtility(ttool, ITypesTool)

        # Allow adding of Dummy Content
        ttool.Folder.manage_changeProperties(filter_content_types=False)

        # Copy/paste verification should work fine
        folder._verifyObjectPaste(content)

        # Add a workflow with a blocking guard
        # Based on TypesTools tests
        class DummyWorkflow:

            _allow = False

            def allowCreate(self, container, type_id):
                return self._allow

        class DummyWorkflowTool:

            def __init__(self):
                self._workflows = [DummyWorkflow()]

            def getWorkflowsFor(self, type_id):
                return self._workflows

        # Now copy/paste verification should raise a ValueError
        sm.registerUtility(DummyWorkflowTool(), IWorkflowTool)
        self.assertRaises(ValueError, folder._verifyObjectPaste, content)

    def test_setObjectRaisesBadRequest(self):
        #
        #   _setObject() should raise BadRequest on duplicate id
        #
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        test = self._makeOne('test')
        test._setObject('foo', DummyContent('foo'))
        self.assertRaises(BadRequest, test._setObject, 'foo',
                          DummyContent('foo'))

    def test__checkId_Duplicate(self):
        #
        #   _checkId() should raise BadRequest on duplicate id
        #
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        test = self._makeOne('test')
        test._setObject('foo', DummyContent('foo'))
        self.assertRaises(BadRequest, test._checkId, 'foo')

    def test__checkId_PortalRoot(self):
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        test = self._makeOne('test')
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        test._checkId('acl_users')
        newSecurityManager(None, acl_users.user_foo)
        self.assertRaises(BadRequest, test._checkId, 'acl_users')

    def test__checkId_MethodAlias(self):
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        test = self._makeOne('test')
        test._setPortalTypeName('Dummy Content 15')
        ttool = TypesTool()
        ttool._setObject('Dummy Content 15', FTI(**FTIDATA_CMF[0]))
        getSiteManager().registerUtility(ttool, ITypesTool)
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        test._checkId('view')
        newSecurityManager(None, acl_users.user_foo)
        self.assertRaises(BadRequest, test._checkId, 'view')

    def test__checkId_starting_with_dot(self):
        #
        # doted prefixed names at the root of the portal can be overriden
        #

        # Create a .foo at the root
        self.site._setObject('.foo', DummyContent('.foo'))

        # Create a sub-folder
        sub = self._makeOne('sub')

        # It should be possible to create another .foo object in the
        # sub-folder
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.user_foo)

        self.assertTrue(sub.checkIdAvailable('.foo'))

    def test__checkId_Five(self):
        test = self._makeOne('test')
        self.assertRaises(BadRequest, test._checkId, '@@view')

    def test_checkIdAvailableCatchesBadRequest(self):
        #
        #   checkIdAvailable() should catch BadRequest
        #
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        test = self._makeOne('test')
        test._setObject('foo', DummyContent('foo'))
        self.assertFalse(test.checkIdAvailable('foo'))


class PortalFolderMoveTests(SecurityTest):

    layer = TraversingEventZCMLLayer

    def setUp(self):
        SecurityTest.setUp(self)
        self.app._setObject('site', DummySite('site'))
        self.site = self.app.site

    def _makeOne(self, id, *args, **kw):
        from ..PortalFolder import PortalFolder

        return self.site._setObject(id, PortalFolder(id, *args, **kw))

    def test_folderMove(self):
        #
        #   Does the catalog stay synched when folders are moved?
        #
        from ..PortalFolder import PortalFolder

        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        ctool = DummyCatalogTool()
        sm = getSiteManager()
        sm.registerUtility(TypesTool(), ITypesTool)
        sm.registerUtility(ctool, ICatalogTool)
        self.assertEqual(len(ctool), 0)

        folder = self._makeOne('folder')
        folder._setObject('sub', PortalFolder('sub', ''))
        folder.sub._setObject('foo', DummyContent('foo', catalog=1))
        self.assertEqual(len(ctool), 1)
        self.assertTrue(has_id(ctool, 'foo'))
        self.assertTrue(has_path(ctool, '/bar/site/folder/sub/foo'))

        transaction.savepoint(optimistic=True)
        folder.manage_renameObject(id='sub', new_id='new_sub')
        self.assertEqual(len(ctool), 1)
        self.assertTrue(has_id(ctool, 'foo'))
        self.assertTrue(has_path(ctool, '/bar/site/folder/new_sub/foo'))

        folder._setObject('bar', DummyContent('bar', catalog=1))
        self.assertEqual(len(ctool), 2)
        self.assertTrue(has_id(ctool, 'bar'))
        self.assertTrue(has_path(ctool, '/bar/site/folder/bar'))

        folder._setObject('sub2', PortalFolder('sub2', ''))
        sub2 = folder.sub2
        # Waaa! force sub2 to allow paste of Dummy object.
        sub2.all_meta_types = []
        sub2.all_meta_types.extend(sub2.all_meta_types)
        sub2.all_meta_types.extend(extra_meta_types())

        transaction.savepoint(optimistic=True)
        cookie = folder.manage_cutObjects(ids=['bar'])
        sub2.manage_pasteObjects(cookie)

        self.assertTrue(has_id(ctool, 'foo'))
        self.assertTrue(has_id(ctool, 'bar'))
        self.assertEqual(len(ctool), 2)
        self.assertTrue(has_path(ctool, '/bar/site/folder/sub2/bar'))

    def test_contentPaste(self):
        #
        #   Does copy / paste work?
        #
        acl_users = self.site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        ctool = DummyCatalogTool()
        ttool = TypesTool()
        fti = FTIDATA_DUMMY[0].copy()
        ttool._setObject('Dummy Content', FTI(**fti))
        sub1 = self._makeOne('sub1')
        sub2 = self._makeOne('sub2')
        sub3 = self._makeOne('sub3')
        self.assertEqual(len(ctool), 0)
        sm = getSiteManager()
        sm.registerUtility(ctool, ICatalogTool)
        sm.registerUtility(ttool, ITypesTool)

        sub1._setObject('dummy', DummyContent('dummy', catalog=1))
        self.assertTrue('dummy' in sub1.objectIds())
        self.assertTrue('dummy' in sub1.contentIds())
        self.assertFalse('dummy' in sub2.objectIds())
        self.assertFalse('dummy' in sub2.contentIds())
        self.assertFalse('dummy' in sub3.objectIds())
        self.assertFalse('dummy' in sub3.contentIds())
        self.assertTrue(has_path(ctool, '/bar/site/sub1/dummy'))
        self.assertFalse(has_path(ctool, '/bar/site/sub2/dummy'))
        self.assertFalse(has_path(ctool, '/bar/site/sub3/dummy'))

        cookie = sub1.manage_copyObjects(ids=('dummy',))
        # Waaa! force sub2 to allow paste of Dummy object.
        sub2.all_meta_types = []
        sub2.all_meta_types.extend(sub2.all_meta_types)
        sub2.all_meta_types.extend(extra_meta_types())
        sub2.manage_pasteObjects(cookie)
        self.assertTrue('dummy' in sub1.objectIds())
        self.assertTrue('dummy' in sub1.contentIds())
        self.assertTrue('dummy' in sub2.objectIds())
        self.assertTrue('dummy' in sub2.contentIds())
        self.assertFalse('dummy' in sub3.objectIds())
        self.assertFalse('dummy' in sub3.contentIds())
        self.assertTrue(has_path(ctool, '/bar/site/sub1/dummy'))
        self.assertTrue(has_path(ctool, '/bar/site/sub2/dummy'))
        self.assertFalse(has_path(ctool, '/bar/site/sub3/dummy'))

        transaction.savepoint(optimistic=True)
        cookie = sub1.manage_cutObjects(ids=('dummy',))
        # Waaa! force sub2 to allow paste of Dummy object.
        sub3.all_meta_types = []
        sub3.all_meta_types.extend(sub3.all_meta_types)
        sub3.all_meta_types.extend(extra_meta_types())
        sub3.manage_pasteObjects(cookie)
        self.assertFalse('dummy' in sub1.objectIds())
        self.assertFalse('dummy' in sub1.contentIds())
        self.assertTrue('dummy' in sub2.objectIds())
        self.assertTrue('dummy' in sub2.contentIds())
        self.assertTrue('dummy' in sub3.objectIds())
        self.assertTrue('dummy' in sub3.contentIds())
        self.assertFalse(has_path(ctool, '/bar/site/sub1/dummy'))
        self.assertTrue(has_path(ctool, '/bar/site/sub2/dummy'))
        self.assertTrue(has_path(ctool, '/bar/site/sub3/dummy'))


class ContentFilterTests(unittest.TestCase):

    def setUp(self):
        self.dummy = DummyContent('Dummy')

    def test_empty(self):
        from ..PortalFolder import ContentFilter

        cfilter = ContentFilter()
        dummy = self.dummy
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = [_f for _f in desc.split('; ') if _f]
        self.assertFalse(lines)

    def test_Type(self):
        from ..PortalFolder import ContentFilter

        cfilter = ContentFilter(Type='foo')
        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        cfilter = ContentFilter(Type='Dummy Content Title')
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'Type: Dummy Content Title')

        cfilter = ContentFilter(Type=('foo', 'bar'))
        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        cfilter = ContentFilter(Type=('Dummy Content Title', 'something else'))
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'Type: Dummy Content Title, something else')

    def test_portal_type(self):
        from ..PortalFolder import ContentFilter

        cfilter = ContentFilter(portal_type='some_pt')
        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        dummy.portal_type = 'asdf'
        self.assertFalse(cfilter(dummy))
        dummy.portal_type = 'some_ptyyy'
        self.assertFalse(cfilter(dummy))
        dummy.portal_type = 'xxxsome_ptyyy'
        self.assertFalse(cfilter(dummy))
        dummy.portal_type = 'some_pt'
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'Portal Type: some_pt')

    def test_Title(self):
        from ..PortalFolder import ContentFilter

        cfilter = ContentFilter(Title='foo')
        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        dummy.title = 'asdf'
        self.assertFalse(cfilter(dummy))
        dummy.title = 'foolish'
        self.assertTrue(cfilter(dummy))
        dummy.title = 'ohsofoolish'
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'Title: foo')

    def test_Creator(self):
        from ..PortalFolder import ContentFilter

        cfilter = ContentFilter(Creator='moe')
        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        dummy.creators = ('curly',)
        self.assertFalse(cfilter(dummy))
        dummy.creators = ('moe',)
        self.assertTrue(cfilter(dummy))
        dummy.creators = ('moe', 'curly')
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'Creator: moe')

    def test_Description(self):
        from ..PortalFolder import ContentFilter

        cfilter = ContentFilter(Description='funny')
        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        dummy.description = 'sad'
        self.assertFalse(cfilter(dummy))
        dummy.description = 'funny'
        self.assertTrue(cfilter(dummy))
        dummy.description = 'it is funny you should mention it...'
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'Description: funny')

    def test_Subject(self):
        from ..PortalFolder import ContentFilter

        cfilter = ContentFilter(Subject=('foo',))
        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        dummy.subject = ('bar',)
        self.assertFalse(cfilter(dummy))
        dummy.subject = ('foo',)
        self.assertTrue(cfilter(dummy))
        dummy.subject = ('foo', 'bar')
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'Subject: foo')

    def test_Subject2(self):
        # Now test with mutli-valued
        from ..PortalFolder import ContentFilter

        cfilter = ContentFilter(Subject=('foo', 'bar'))
        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        dummy.subject = ('baz',)
        self.assertFalse(cfilter(dummy))
        dummy.subject = ('bar',)
        self.assertTrue(cfilter(dummy))
        dummy.subject = ('foo',)
        self.assertTrue(cfilter(dummy))
        dummy.subject = ('foo', 'bar')
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'Subject: foo, bar')

    def test_created(self):
        from ..PortalFolder import ContentFilter

        creation_date = DateTime('2001/01/01')
        tz = creation_date.timezone()
        cfilter = ContentFilter(created=creation_date,
                                created_usage='range:min')
        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        dummy.created_date = DateTime('2000/12/31')
        self.assertFalse(cfilter(dummy))
        dummy.created_date = DateTime('2001/12/31')
        self.assertTrue(cfilter(dummy))
        dummy.created_date = DateTime('2001/01/01')
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0],
                         'Created since: 2001/01/01 00:00:00 %s' % tz)

    def test_created2(self):
        from ..PortalFolder import ContentFilter

        creation_date = DateTime('2001/01/01')
        tz = creation_date.timezone()
        cfilter = ContentFilter(created=creation_date,
                                created_usage='range:max')

        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        dummy.created_date = DateTime('2000/12/31')
        self.assertTrue(cfilter(dummy))
        dummy.created_date = DateTime('2001/12/31')
        self.assertFalse(cfilter(dummy))
        dummy.created_date = DateTime('2001/01/01')
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0],
                         'Created before: 2001/01/01 00:00:00 %s' % tz)

    def test_modified(self):
        from ..PortalFolder import ContentFilter

        creation_date = DateTime('2001/01/01')
        tz = creation_date.timezone()
        cfilter = ContentFilter(modified=DateTime('2001/01/01'),
                                modified_usage='range:min')
        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        dummy.modified_date = DateTime('2000/12/31')
        self.assertFalse(cfilter(dummy))
        dummy.modified_date = DateTime('2001/12/31')
        self.assertTrue(cfilter(dummy))
        dummy.modified_date = DateTime('2001/01/01')
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0],
                         'Modified since: 2001/01/01 00:00:00 %s' % tz)

    def test_modified2(self):
        from ..PortalFolder import ContentFilter

        creation_date = DateTime('2001/01/01')
        tz = creation_date.timezone()
        cfilter = ContentFilter(modified=DateTime('2001/01/01'),
                                modified_usage='range:max')
        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        dummy.modified_date = DateTime('2000/12/31')
        self.assertTrue(cfilter(dummy))
        dummy.modified_date = DateTime('2001/12/31')
        self.assertFalse(cfilter(dummy))
        dummy.modified_date = DateTime('2001/01/01')
        self.assertTrue(cfilter(dummy))
        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0],
                         'Modified before: 2001/01/01 00:00:00 %s' % tz)

    def test_mixed(self):
        from ..PortalFolder import ContentFilter

        creation_date = DateTime('2001/01/01')
        tz = creation_date.timezone()
        cfilter = ContentFilter(created=DateTime('2001/01/01'),
                                created_usage='range:max', Title='foo')

        dummy = self.dummy
        self.assertFalse(cfilter(dummy))
        dummy.created_date = DateTime('2000/12/31')
        self.assertFalse(cfilter(dummy))
        dummy.created_date = DateTime('2001/12/31')
        self.assertFalse(cfilter(dummy))
        dummy.created_date = DateTime('2001/01/01')
        self.assertFalse(cfilter(dummy))

        dummy.title = 'ohsofoolish'
        del dummy.created_date
        self.assertFalse(cfilter(dummy))
        dummy.created_date = DateTime('2000/12/31')
        self.assertTrue(cfilter(dummy))
        dummy.created_date = DateTime('2001/12/31')
        self.assertFalse(cfilter(dummy))
        dummy.created_date = DateTime('2001/01/01')
        self.assertTrue(cfilter(dummy))

        desc = str(cfilter)
        lines = desc.split('; ')
        self.assertEqual(len(lines), 2)
        self.assertTrue('Created before: 2001/01/01 00:00:00 %s' % tz in lines)
        self.assertTrue('Title: foo' in lines)


# -----------------------------------------------------------------------------
#   Tests for security-related CopySupport lifted from the Zope 2.7
#   / head OFS.tests.testCopySupport (see Collector #259).
# -----------------------------------------------------------------------------
ADD_IMAGES_AND_FILES = 'Add images and files'
FILE_META_TYPES = ({'name': 'File',
                    'action': 'manage_addFile',
                    'permission': ADD_IMAGES_AND_FILES},)


class _SensitiveSecurityPolicy:

    def __init__(self, validate_lambda, checkPermission_lambda):
        self._lambdas = (validate_lambda, checkPermission_lambda)

    def validate(self, *args, **kw):
        if self._lambdas[0](*args, **kw):
            return True
        raise Unauthorized

    def checkPermission(self, *args, **kw):
        return self._lambdas[1](*args, **kw)


class _AllowedUser(Implicit):

    def __init__(self, allowed_lambda):
        self._lambdas = (allowed_lambda,)

    def getId(self):
        return 'unit_tester'

    def getUserName(self):
        return 'Unit Tester'

    def allowed(self, object, object_roles=None):
        return self._lambdas[0](object, object_roles)


class PortalFolderCopySupportTests(SecurityTest):

    layer = TraversingEventZCMLLayer

    def _initFolders(self):
        from ..PortalFolder import PortalFolder

        self.app._setObject('folder1', PortalFolder('folder1'))
        self.app._setObject('folder2', PortalFolder('folder2'))
        folder1 = getattr(self.app, 'folder1')
        manage_addFile(folder1, 'file', file='', content_type='text/plain')

        # Hack, we need a _p_mtime for the file, so we make sure that it
        # has one. We use a subtransaction, which means we can rollback
        # later and pretend we didn't touch the ZODB.
        transaction.savepoint(optimistic=True)
        return self.app._getOb('folder1'), self.app._getOb('folder2')

    def _assertCopyErrorUnauth(self, callable, *args, **kw):
        import re

        from OFS.CopySupport import CopyError

        from ..exceptions import zExceptions_Unauthorized

        ce_regex = kw.get('ce_regex')
        if ce_regex is not None:
            del kw['ce_regex']

        try:
            callable(*args, **kw)
        except CopyError as e:
            if ce_regex is not None:
                pattern = re.compile(ce_regex, re.DOTALL)
                if pattern.search(str(e)) is None:
                    self.fail("Paste failed; didn't match pattern:\n%s" % e)
            else:
                self.fail('Paste failed; no pattern:\n%s' % e)

        except zExceptions_Unauthorized:
            pass
        else:
            self.fail('Paste allowed unexpectedly.')

    def _initPolicyAndUser(self, a_lambda=None, v_lambda=None, c_lambda=None):
        def _promiscuous(*args, **kw):
            return 1

        if a_lambda is None:
            a_lambda = _promiscuous

        if v_lambda is None:
            v_lambda = _promiscuous

        if c_lambda is None:
            c_lambda = _promiscuous

        scp = _SensitiveSecurityPolicy(v_lambda, c_lambda)
        SecurityManager.setSecurityPolicy(scp)

        newSecurityManager(None,
                           _AllowedUser(a_lambda).__of__(self.app.acl_users))

    def test_copy_baseline(self):

        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = FILE_META_TYPES

        self._initPolicyAndUser()

        self.assertTrue('file' in folder1.objectIds())
        self.assertFalse('file' in folder2.objectIds())

        cookie = folder1.manage_copyObjects(ids=('file',))
        folder2.manage_pasteObjects(cookie)

        self.assertTrue('file' in folder1.objectIds())
        self.assertTrue('file' in folder2.objectIds())

    def test_copy_cant_read_source(self):

        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = FILE_META_TYPES

        a_file = folder1._getOb('file')

        def _validate(a, c, n, v, *args, **kw):
            return aq_base(v) is not aq_base(a_file)

        self._initPolicyAndUser(v_lambda=_validate)

        cookie = folder1.manage_copyObjects(ids=('file',))
        self._assertCopyErrorUnauth(folder2.manage_pasteObjects,
                                    cookie,
                                    ce_regex='Insufficient privileges')

    def test_copy_cant_create_target_metatype_not_supported(self):
        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = ()

        self._initPolicyAndUser()

        cookie = folder1.manage_copyObjects(ids=('file',))
        self._assertCopyErrorUnauth(folder2.manage_pasteObjects, cookie,
                                    ce_regex='Not Supported')

    def test_move_baseline(self):

        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = FILE_META_TYPES

        self.assertTrue('file' in folder1.objectIds())
        self.assertFalse('file' in folder2.objectIds())

        self._initPolicyAndUser()

        cookie = folder1.manage_cutObjects(ids=('file',))
        folder2.manage_pasteObjects(cookie)

        self.assertFalse('file' in folder1.objectIds())
        self.assertTrue('file' in folder2.objectIds())

    def test_move_cant_read_source(self):
        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = FILE_META_TYPES

        a_file = folder1._getOb('file')

        def _validate(a, c, n, v, *args, **kw):
            return aq_base(v) is not aq_base(a_file)

        self._initPolicyAndUser(v_lambda=_validate)

        cookie = folder1.manage_cutObjects(ids=('file',))
        self._assertCopyErrorUnauth(folder2.manage_pasteObjects, cookie,
                                    ce_regex='Insufficient privileges')

    def test_move_cant_create_target_metatype_not_supported(self):
        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = ()

        self._initPolicyAndUser()

        cookie = folder1.manage_cutObjects(ids=('file',))
        self._assertCopyErrorUnauth(folder2.manage_pasteObjects, cookie,
                                    ce_regex='Not Supported')

    def test_move_cant_create_target_metatype_not_allowed(self):
        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = FILE_META_TYPES

        def _no_manage_addFile(a, c, n, v, *args, **kw):
            return n != 'manage_addFile'

        def _no_add_images_and_files(permission, object, context):
            return permission != ADD_IMAGES_AND_FILES

        self._initPolicyAndUser(v_lambda=_no_manage_addFile,
                                c_lambda=_no_add_images_and_files)

        cookie = folder1.manage_cutObjects(ids=('file',))
        self._assertCopyErrorUnauth(folder2.manage_pasteObjects, cookie,
                                    ce_regex='Insufficient privileges')

    def test_move_cant_delete_source(self):
        from AccessControl.Permissions import delete_objects as DeleteObjects

        from ..PortalFolder import PortalFolder

        folder1, folder2 = self._initFolders()
        folder1.manage_permission(DeleteObjects, roles=(), acquire=0)

        folder1._setObject('sub', PortalFolder('sub'))
        transaction.savepoint(optimistic=True)  # get a _p_jar for 'sub'

        def _no_delete_objects(permission, object, context):
            return permission != DeleteObjects

        self._initPolicyAndUser(c_lambda=_no_delete_objects)

        cookie = folder1.manage_cutObjects(ids=('sub',))
        self._assertCopyErrorUnauth(folder2.manage_pasteObjects, cookie,
                                    ce_regex='Insufficient Privileges'
                                    + '.*%s' % DeleteObjects)

    def test_paste_with_restricted_item_content_type_not_allowed(self):
        #   Test from CMF Collector #216 (Plone #2186), for the case
        #   in which the item being pasted does not allow adding such
        #   objects to containers which do not explicitly grant access.
        from ..PortalFolder import PortalFolder

        RESTRICTED_TYPE = 'Restricted Item'
        UNRESTRICTED_TYPE = 'Unrestricted Container'

        folder1, folder2 = self._initFolders()
        folder1.portal_type = UNRESTRICTED_TYPE
        folder2.portal_type = RESTRICTED_TYPE

        self._initPolicyAndUser()  # ensure that sec. machinery allows paste

        ttool = TypesTool()
        ttool._setObject(RESTRICTED_TYPE,
                         FTI(id=RESTRICTED_TYPE,
                             title=RESTRICTED_TYPE,
                             meta_type=PortalFolder.meta_type,
                             product='CMFCore',
                             factory='manage_addPortalFolder',
                             global_allow=0))
        ttool._setObject(UNRESTRICTED_TYPE,
                         FTI(id=UNRESTRICTED_TYPE,
                             title=UNRESTRICTED_TYPE,
                             meta_type=PortalFolder.meta_type,
                             product='CMFCore',
                             factory='manage_addPortalFolder',
                             filter_content_types=0))
        getSiteManager().registerUtility(ttool, ITypesTool)

        # copy and pasting the object into the folder should raise
        # an exception
        copy_cookie = self.app.manage_copyObjects(ids=['folder2'])
        self.assertRaises(ValueError, folder1.manage_pasteObjects, copy_cookie)

    def test_paste_with_restricted_item_content_type_allowed(self):
        #   Test from CMF Collector #216 (Plone #2186), for the case
        #   in which the item being pasted *does8 allow adding such
        #   objects to containers which *do* explicitly grant access.
        from ..PortalFolder import PortalFolder

        RESTRICTED_TYPE = 'Restricted Item'
        UNRESTRICTED_TYPE = 'Unrestricted Container'

        folder1, folder2 = self._initFolders()
        folder1.portal_type = UNRESTRICTED_TYPE
        folder2.portal_type = RESTRICTED_TYPE

        self._initPolicyAndUser()  # ensure that sec. machinery allows paste

        ttool = TypesTool()
        ttool._setObject(RESTRICTED_TYPE,
                         FTI(id=RESTRICTED_TYPE,
                             title=RESTRICTED_TYPE,
                             meta_type=PortalFolder.meta_type,
                             product='CMFCore',
                             factory='manage_addPortalFolder',
                             global_allow=0))
        ttool._setObject(UNRESTRICTED_TYPE,
                         FTI(id=UNRESTRICTED_TYPE,
                             title=UNRESTRICTED_TYPE,
                             meta_type=PortalFolder.meta_type,
                             product='CMFCore',
                             factory='manage_addPortalFolder',
                             filter_content_types=1,
                             allowed_content_types=[RESTRICTED_TYPE]))
        getSiteManager().registerUtility(ttool, ITypesTool)

        # copy and pasting the object into the folder should *not* raise
        # an exception, because the folder's type allows it.
        copy_cookie = self.app.manage_copyObjects(ids=['folder2'])
        folder1.manage_pasteObjects(copy_cookie)
        self.assertTrue('folder2' in folder1.objectIds())

    def test_paste_with_restricted_container_content_type(self):
        #   Test from CMF Collector #216 (Plone #2186), for the case
        #   in which the container does not allow adding items of the
        #   type being pasted.
        from ..PortalFolder import PortalFolder

        RESTRICTED_TYPE = 'Restricted Container'
        UNRESTRICTED_TYPE = 'Unrestricted Item'

        folder1, folder2 = self._initFolders()
        folder1.portal_type = RESTRICTED_TYPE
        folder2.portal_type = UNRESTRICTED_TYPE

        self._initPolicyAndUser()  # ensure that sec. machinery allows paste

        ttool = TypesTool()
        ttool._setObject(RESTRICTED_TYPE,
                         FTI(id=RESTRICTED_TYPE,
                             title=RESTRICTED_TYPE,
                             meta_type=PortalFolder.meta_type,
                             product='CMFCore',
                             factory='manage_addPortalFolder',
                             filter_content_types=1,
                             allowed_content_types=()))
        ttool._setObject(UNRESTRICTED_TYPE,
                         FTI(id=UNRESTRICTED_TYPE,
                             title=UNRESTRICTED_TYPE,
                             meta_type=PortalFolder.meta_type,
                             product='CMFCore',
                             factory='manage_addPortalFolder',
                             global_allow=1))
        getSiteManager().registerUtility(ttool, ITypesTool)

        # copy and pasting the object into the folder should raise
        # an exception
        copy_cookie = self.app.manage_copyObjects(ids=['folder2'])
        self.assertRaises(ValueError, folder1.manage_pasteObjects, copy_cookie)


def test_suite():
    loadTestsFromTestCase = unittest.defaultTestLoader.loadTestsFromTestCase
    return unittest.TestSuite((
        loadTestsFromTestCase(PortalFolderFactoryTests),
        loadTestsFromTestCase(PortalFolderTests),
        loadTestsFromTestCase(PortalFolderSecurityTests),
        loadTestsFromTestCase(PortalFolderMoveTests),
        loadTestsFromTestCase(ContentFilterTests),
        loadTestsFromTestCase(PortalFolderCopySupportTests)))
