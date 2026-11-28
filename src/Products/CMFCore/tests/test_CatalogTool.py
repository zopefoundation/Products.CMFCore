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
""" Unit tests for CatalogTool module.
"""

import unittest

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from Acquisition import Implicit
from Testing.ZopeTestCase import installProduct
from zope.component import getSiteManager
from zope.globalrequest import clearRequest
from zope.globalrequest import setRequest
from zope.interface import implementer
from zope.testing.cleanup import cleanUp

from ..indexing import processQueue
from ..interfaces import ICatalogTool
from ..interfaces import IContentish
from ..interfaces import IIndexQueueProcessor
from ..interfaces import ITypesTool
from ..interfaces import IWorkflowTool
from ..testing import TraversingEventZCMLLayer
from .base.dummy import DummyContent
from .base.dummy import DummySite
from .base.dummy import DummyUserFolder
from .base.testcase import SecurityTest
from .test_PortalFolder import extra_meta_types


installProduct('PluginIndexes')


class FakeFolder(Implicit):
    id = 'portal'


class FakeWorkflowTool(Implicit):
    id = 'portal_workflow'

    def __init__(self, vars):
        self._vars = vars

    def getCatalogVariablesFor(self, ob):
        return self._vars


class IndexableObjectWrapperTests(unittest.TestCase):

    def _getTargetClass(self):
        from ..CatalogTool import IndexableObjectWrapper

        return IndexableObjectWrapper

    def _makeOne(self, vars, obj):
        from ..interfaces import ICatalogTool

        @implementer(ICatalogTool)
        class FakeCatalog(Implicit):
            id = 'portal_catalog'

        getSiteManager().registerUtility(FakeWorkflowTool(vars), IWorkflowTool)
        catalog = FakeCatalog().__of__(FakeFolder())
        return self._getTargetClass()(obj, catalog)

    def _makeContent(self, *args, **kw):
        return DummyContent(*args, **kw)

    def tearDown(self):
        cleanUp()

    def test_interfaces(self):
        from zope.interface.verify import verifyClass

        from ..interfaces import IIndexableObjectWrapper

        verifyClass(IIndexableObjectWrapper, self._getTargetClass())

    def test_allowedRolesAndUsers(self):
        # XXX This test fails when verbose security is enabled in zope.conf,
        # because the roles will then contain '_View_Permission' as well as
        # 'Manager'.
        obj = self._makeContent()
        w = self._makeOne({}, obj)
        self.assertEqual(w.allowedRolesAndUsers(), ['Manager'])

    def test___str__(self):
        obj = self._makeContent('foo')
        w = self._makeOne({}, obj)
        self.assertEqual(str(w), str(obj))

    def test_proxied_attributes(self):
        obj = self._makeContent('foo')
        obj.title = 'Foo'
        w = self._makeOne({}, obj)
        self.assertEqual(w.getId(), 'foo')
        self.assertEqual(w.Title(), 'Foo')

    def test_vars(self):
        obj = self._makeContent()
        w = self._makeOne({'bar': 1, 'baz': 2}, obj)
        self.assertEqual(w.bar, 1)
        self.assertEqual(w.baz, 2)

    def test_provided(self):
        from ..interfaces import IIndexableObject
        from ..interfaces import IIndexableObjectWrapper

        obj = self._makeContent()
        w = self._makeOne({}, obj)
        self.assertTrue(IContentish.providedBy(w))
        self.assertTrue(IIndexableObjectWrapper.providedBy(w))
        self.assertTrue(IIndexableObject.providedBy(w))

    def test_adapts(self):
        from zope.component import adaptedBy

        from ..interfaces import ICatalogTool

        w = self._getTargetClass()
        adapts = adaptedBy(w)
        self.assertEqual(adapts, (IContentish, ICatalogTool))

    def test_portal_type(self):
        obj = self._makeContent()
        w = self._makeOne({}, obj)
        self.assertEqual(w.portal_type, 'Dummy Content')
        obj.portal_type = None
        self.assertEqual(w.portal_type, '')


class CatalogToolTests(SecurityTest):

    def _getTargetClass(self):
        from ..CatalogTool import CatalogTool

        return CatalogTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def _makeContent(self, *args, **kw):
        from ..interfaces import IIndexableObject

        @implementer(IIndexableObject)
        class CatalogDummyContent(DummyContent):
            """ Dummy content that already provides IIndexableObject
                and therefore does not need a wrapper to be registered
            """
            allowedRolesAndUsers = ['Manager']  # default value

        return CatalogDummyContent(*args, **kw)

    def test_interfaces(self):
        from zope.interface.verify import verifyClass

        from Products.ZCatalog.interfaces import IZCatalog

        from ..interfaces import IActionProvider
        from ..interfaces import ICatalogTool

        verifyClass(IActionProvider, self._getTargetClass())
        verifyClass(ICatalogTool, self._getTargetClass())
        verifyClass(IZCatalog, self._getTargetClass())

    def loginWithRoles(self, *roles):
        from AccessControl.SecurityManagement import newSecurityManager

        from .base.security import UserWithRoles
        user = UserWithRoles(*roles).__of__(self.app)
        newSecurityManager(None, user)

    def loginManager(self):
        from AccessControl.SecurityManagement import newSecurityManager

        from .base.security import OmnipotentUser
        user = OmnipotentUser().__of__(self.app)
        newSecurityManager(None, user)

    def setupProxyRoles(self, *proxy_roles):
        from AccessControl import getSecurityManager

        class FauxExecutable:
            _proxy_roles = proxy_roles

        sm = getSecurityManager()
        sm.addContext(FauxExecutable())

    def test_processActions(self):
        """
            Tracker #405:  CatalogTool doesn't accept optional third
            argument, 'idxs', to 'catalog_object'.
        """
        tool = self._makeOne()
        tool.addIndex('SearchableText', 'KeywordIndex')
        dummy = self._makeContent(catalog=1)

        tool.catalog_object(dummy, '/dummy')
        tool.catalog_object(dummy, '/dummy', ['SearchableText'])

    def test_search_anonymous(self):
        catalog = self._makeOne()
        catalog.addIndex('allowedRolesAndUsers', 'KeywordIndex')
        catalog.addIndex('meta_type', 'FieldIndex')
        dummy = self._makeContent(catalog=1)
        catalog.catalog_object(dummy, '/dummy')

        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(catalog._catalog.searchResults(query)))
        self.assertEqual(0, len(catalog.searchResults(query)))

    def test_search_member_with_valid_roles(self):
        catalog = self._makeOne()
        catalog.addIndex('allowedRolesAndUsers', 'KeywordIndex')
        catalog.addIndex('meta_type', 'FieldIndex')
        dummy = self._makeContent(catalog=1)
        dummy.allowedRolesAndUsers = ('Blob',)
        catalog.catalog_object(dummy, '/dummy')

        self.loginWithRoles('Blob')

        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(catalog._catalog.searchResults(query)))
        self.assertEqual(1, len(catalog.searchResults(query)))

    def test_search_member_with_valid_roles_but_proxy_roles_limit(self):
        catalog = self._makeOne()
        catalog.addIndex('allowedRolesAndUsers', 'KeywordIndex')
        catalog.addIndex('meta_type', 'FieldIndex')
        dummy = self._makeContent(catalog=1)
        dummy.allowedRolesAndUsers = ('Blob',)
        catalog.catalog_object(dummy, '/dummy')

        self.loginWithRoles('Blob')
        self.setupProxyRoles('Waggle')

        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(catalog._catalog.searchResults(query)))
        self.assertEqual(0, len(catalog.searchResults(query)))

    def test_search_member_wo_valid_roles(self):
        catalog = self._makeOne()
        catalog.addIndex('allowedRolesAndUsers', 'KeywordIndex')
        catalog.addIndex('meta_type', 'FieldIndex')
        dummy = self._makeContent(catalog=1)
        dummy.allowedRoleAndUsers = ('Blob',)
        catalog.catalog_object(dummy, '/dummy')

        self.loginWithRoles('Waggle')

        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(catalog._catalog.searchResults(query)))
        self.assertEqual(0, len(catalog.searchResults(query)))

    def test_search_member_wo_valid_roles_but_proxy_roles_allow(self):
        catalog = self._makeOne()
        catalog.addIndex('allowedRolesAndUsers', 'KeywordIndex')
        catalog.addIndex('meta_type', 'FieldIndex')
        dummy = self._makeContent(catalog=1)
        dummy.allowedRolesAndUsers = ('Blob',)
        catalog.catalog_object(dummy, '/dummy')

        self.loginWithRoles('Waggle')
        self.setupProxyRoles('Blob')

        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(catalog._catalog.searchResults(query)))
        self.assertEqual(1, len(catalog.searchResults(query)))

    def test_search_inactive(self):
        from DateTime.DateTime import DateTime
        catalog = self._makeOne()
        catalog.addIndex('allowedRolesAndUsers', 'KeywordIndex')
        catalog.addIndex('effective', 'DateIndex')
        catalog.addIndex('expires', 'DateIndex')
        catalog.addIndex('meta_type', 'FieldIndex')
        now = DateTime()
        dummy = self._makeContent(catalog=1)
        dummy.allowedRolesAndUsers = ('Blob',)

        self.loginWithRoles('Blob')

        # not yet effective
        dummy.effective = now + 1
        dummy.expires = now + 2
        catalog.catalog_object(dummy, '/dummy')
        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(catalog._catalog.searchResults(query)))
        self.assertEqual(0, len(catalog.searchResults(query)))

        # already expired
        dummy.effective = now - 2
        dummy.expires = now - 1
        catalog.catalog_object(dummy, '/dummy')
        self.assertEqual(1, len(catalog._catalog.searchResults(query)))
        self.assertEqual(0, len(catalog.searchResults(query)))

    def test_search_restrict_manager(self):
        from DateTime.DateTime import DateTime
        catalog = self._makeOne()
        catalog.addIndex('allowedRolesAndUsers', 'KeywordIndex')
        catalog.addIndex('effective', 'DateIndex')
        catalog.addIndex('expires', 'DateIndex')
        catalog.addIndex('meta_type', 'FieldIndex')
        now = DateTime()
        dummy = self._makeContent(catalog=1)

        self.loginManager()

        # already expired
        dummy.effective = now - 4
        dummy.expires = now - 2
        catalog.catalog_object(dummy, '/dummy')
        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(catalog._catalog.searchResults(query)))
        self.assertEqual(1, len(catalog.searchResults(query)))

        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': now - 3, 'range': 'min'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': now - 1, 'range': 'min'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': now - 3, 'range': 'max'})))
        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': now - 1, 'range': 'max'})))
        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': (now - 3, now - 1), 'range': 'min:max'})))
        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': (now - 3, now - 1), 'range': 'minmax'})))
        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': now - 2})))
        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': now - 2, 'range': None})))

    def test_search_restrict_inactive(self):
        from DateTime.DateTime import DateTime
        catalog = self._makeOne()
        catalog.addIndex('allowedRolesAndUsers', 'KeywordIndex')
        catalog.addIndex('effective', 'DateIndex')
        catalog.addIndex('expires', 'DateIndex')
        catalog.addIndex('meta_type', 'FieldIndex')
        now = DateTime()
        dummy = self._makeContent(catalog=1)
        dummy.allowedRolesAndUsers = ('Blob',)

        self.loginWithRoles('Blob')

        # already expired
        dummy.effective = now - 4
        dummy.expires = now - 2
        catalog.catalog_object(dummy, '/dummy')
        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(catalog._catalog.searchResults(query)))
        self.assertEqual(0, len(catalog.searchResults(query)))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': now - 3, 'range': 'min'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': now - 3, 'range': 'max'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': now + 3, 'range': 'min'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': now + 3, 'range': 'max'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': (now - 3, now - 1), 'range': 'min:max'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': (now - 3, now - 1), 'range': 'minmax'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': now - 2, 'range': None})))

    def test_search_restrict_visible(self):
        from DateTime.DateTime import DateTime
        catalog = self._makeOne()
        catalog.addIndex('allowedRolesAndUsers', 'KeywordIndex')
        catalog.addIndex('effective', 'DateIndex')
        catalog.addIndex('expires', 'DateIndex')
        catalog.addIndex('meta_type', 'FieldIndex')

        now = DateTime()
        dummy = self._makeContent(catalog=1)
        dummy.allowedRolesAndUsers = ('Blob',)

        self.loginWithRoles('Blob')

        # visible
        dummy.effective = now - 2
        dummy.expires = now + 2
        catalog.catalog_object(dummy, '/dummy')
        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(catalog._catalog.searchResults(query)))
        self.assertEqual(1, len(catalog.searchResults(query)))

        self.assertEqual(0, len(catalog.searchResults(
            effective={'query': now - 1, 'range': 'min'})))
        self.assertEqual(1, len(catalog.searchResults(
            effective={'query': now - 1, 'range': 'max'})))
        self.assertEqual(0, len(catalog.searchResults(
            effective={'query': now + 1, 'range': 'min'})))
        self.assertEqual(1, len(catalog.searchResults(
            effective={'query': now + 1, 'range': 'max'})))
        self.assertEqual(0, len(catalog.searchResults(
            effective={'query': (now - 1, now + 1), 'range': 'min:max'})))
        self.assertEqual(0, len(catalog.searchResults(
            effective={'query': (now - 1, now + 1), 'range': 'minmax'})))
        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': now - 2, 'range': None})))

        self.assertEqual(1, len(catalog.searchResults(
            effective={'query': now - 3, 'range': 'min'})))
        self.assertEqual(0, len(catalog.searchResults(
            effective={'query': now - 3, 'range': 'max'})))
        self.assertEqual(0, len(catalog.searchResults(
            effective={'query': now + 3, 'range': 'min'})))
        self.assertEqual(1, len(catalog.searchResults(
            effective={'query': now + 3, 'range': 'max'})))
        self.assertEqual(1, len(catalog.searchResults(
            effective={'query': (now - 3, now + 3), 'range': 'min:max'})))
        self.assertEqual(1, len(catalog.searchResults(
            effective={'query': (now - 3, now + 3), 'range': 'minmax'})))

        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': now - 1, 'range': 'min'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': now - 1, 'range': 'max'})))
        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': now + 1, 'range': 'min'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': now + 1, 'range': 'max'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': (now - 1, now + 1), 'range': 'min:max'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': (now - 1, now + 1), 'range': 'minmax'})))

        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': now - 3, 'range': 'min'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': now - 3, 'range': 'max'})))
        self.assertEqual(0, len(catalog.searchResults(
            expires={'query': now + 3, 'range': 'min'})))
        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': now + 3, 'range': 'max'})))
        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': (now - 3, now + 3), 'range': 'min:max'})))
        self.assertEqual(1, len(catalog.searchResults(
            expires={'query': (now - 3, now + 3), 'range': 'minmax'})))

        self.assertEqual(1, len(catalog.searchResults(
            effective={'query': now - 1, 'range': 'max'},
            expires={'query': now + 1, 'range': 'min'})))

        self.assertEqual(0, len(catalog.searchResults(
            effective={'query': now + 1, 'range': 'max'},
            expires={'query': now + 3, 'range': 'min'})))

    def test_convertQuery(self):
        convert = self._makeOne()._convertQuery

        kw = {}
        convert(kw)
        self.assertEqual(kw, {})

        kw = {'expires': 5, 'expires_usage': 'brrr:min'}
        self.assertRaises(ValueError, convert, kw)

        kw = {'foo': 'bar'}
        convert(kw)
        self.assertEqual(kw, {'foo': 'bar'})

        kw = {'expires': 5, 'expires_usage': 'range:min'}
        convert(kw)
        self.assertEqual(kw, {'expires': {'query': 5, 'range': 'min'}})

        kw = {'expires': 5, 'expires_usage': 'range:max'}
        convert(kw)
        self.assertEqual(kw, {'expires': {'query': 5, 'range': 'max'}})

        kw = {'expires': (5, 7), 'expires_usage': 'range:min:max'}
        convert(kw)
        self.assertEqual(kw, {'expires':
                              {'query': (5, 7), 'range': 'min:max'}})

    def test_searchResults_brain(self):
        site = DummySite('site')
        site._setObject('dummy', self._makeContent(catalog=1))
        ctool = self._makeOne().__of__(site)
        ctool.addIndex('meta_type', 'FieldIndex')
        ctool.catalog_object(site.dummy, '/dummy')

        query = {'meta_type': 'Dummy'}
        brain = ctool.searchResults(query)[0]

        setRequest(self.REQUEST)
        self.assertEqual('/dummy', brain.getPath())
        self.assertEqual('http://nohost/dummy', brain.getURL())
        self.assertEqual(site.dummy, brain.getObject())
        self.assertTrue(hasattr(brain.getObject(), 'REQUEST'))
        clearRequest()

    def test_refreshCatalog(self):
        site = DummySite('site')
        site._setObject('dummy', self._makeContent(catalog=1))
        ctool = self._makeOne().__of__(site)
        ctool.addIndex('meta_type', 'FieldIndex')
        ctool.catalog_object(site.dummy, '/dummy')

        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(ctool._catalog.searchResults(query)))
        ctool.refreshCatalog(clear=1)
        length = len(ctool._catalog.searchResults(query))
        self.assertEqual(1, length,
                         "CMF Collector issue #379 ('Update Catalog' "
                         'fails): %s entries after refreshCatalog'
                         % length)

    def test_listAllowedRolesAndUsers_proxyroles(self):
        # https://bugs.launchpad.net/zope-cmf/+bug/161729
        from AccessControl import getSecurityManager
        catalog = self._makeOne()
        self.loginWithRoles('Blob')
        user = getSecurityManager().getUser()

        # First case, no proxy roles set at all
        arus = catalog._listAllowedRolesAndUsers(user)
        self.assertEqual(len(arus), 3)
        self.assertIn('Anonymous', arus)
        self.assertIn('Blob', arus)
        self.assertIn('user:%s' % user.getId(), arus)

        # Second case, a proxy role is set
        self.setupProxyRoles('Waggle')
        arus = catalog._listAllowedRolesAndUsers(user)
        self.assertEqual(len(arus), 3)
        self.assertIn('Anonymous', arus)
        self.assertIn('Waggle', arus)
        self.assertIn('user:%s' % user.getId(), arus)

        # Third case, proxy roles are an empty tuple. This happens if
        # proxy roles are unset using the ZMI. The behavior should
        # mirror the first case with no proxy role setting at all.
        self.setupProxyRoles()
        arus = catalog._listAllowedRolesAndUsers(user)
        self.assertEqual(len(arus), 3)
        self.assertIn('Anonymous', arus)
        self.assertIn('Blob', arus)
        self.assertIn('user:%s' % user.getId(), arus)

    def test_wrapping1(self):
        # DummyContent implements IIndexableObject
        # so should be indexed
        dummy = self._makeContent(catalog=1)
        ctool = self._makeOne()
        ctool.addIndex('meta_type', 'FieldIndex')
        ctool.catalog_object(dummy, '/dummy')
        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(ctool._catalog.searchResults(query)))

    def test_wrapping2(self):
        # DummyContent does not implement IIndexableObject
        # no wrapper registered - should fall back to using
        # wrapper class directly
        dummy = DummyContent(catalog=1)
        ctool = self._makeOne()
        ctool.addIndex('meta_type', 'FieldIndex')
        ctool.catalog_object(dummy, '/dummy')
        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(ctool._catalog.searchResults(query)))

    def test_wrapping3(self):
        # DummyContent does not implement IIndexableObject
        # wrapper registered - should look this up
        from ..interfaces import ICatalogTool
        from ..interfaces import IIndexableObject

        def FakeWrapper(object, catalog):
            return object

        sm = getSiteManager()
        sm.registerAdapter(FakeWrapper,
                           (IContentish, ICatalogTool),
                           IIndexableObject)

        dummy = DummyContent(catalog=1)
        ctool = self._makeOne()
        ctool.addIndex('meta_type', 'FieldIndex')
        ctool.catalog_object(dummy, '/dummy')
        query = {'meta_type': 'Dummy'}
        self.assertEqual(1, len(ctool._catalog.searchResults(query)))


class ModifiableDummyContent(DummyContent):

    notified = False

    def notifyModified(self):
        self.notified = True


class CatalogToolMoveTests(SecurityTest):

    layer = TraversingEventZCMLLayer

    def setUp(self):
        from ..CatalogTool import CatalogTool
        from ..indexing import PortalCatalogProcessor
        from ..PortalFolder import PortalFolder
        from ..TypesTool import TypesTool

        SecurityTest.setUp(self)
        self.app._setObject('site', DummySite('site'))
        site = self.app.site
        acl_users = site._setObject('acl_users', DummyUserFolder())
        newSecurityManager(None, acl_users.all_powerful_Oz)
        site._setObject('portal_catalog', CatalogTool())
        self.ctool = ctool = site.portal_catalog
        ctool.addIndex('path', 'PathIndex')
        ctool.addIndex('getId', 'FieldIndex')
        ctool.addIndex('Title', 'FieldIndex')
        sm = getSiteManager()
        sm.registerUtility(ctool, ICatalogTool)
        sm.registerUtility(TypesTool(), ITypesTool)
        sm.registerUtility(PortalCatalogProcessor(), IIndexQueueProcessor,
                           name='portal-catalog')
        self.folder = site._setObject('folder', PortalFolder('folder'))
        self.sub = self.folder._getOb(
            self.folder._setObject('sub', PortalFolder('sub')))
        # Waaa! force both folders to allow paste of Dummy object.
        self.folder.all_meta_types = extra_meta_types()
        self.sub.all_meta_types = extra_meta_types()

    def tearDown(self):
        sm = getSiteManager()
        sm.unregisterUtility(provided=ICatalogTool)
        sm.unregisterUtility(provided=ITypesTool)
        sm.unregisterUtility(provided=IIndexQueueProcessor,
                             name='portal-catalog')
        SecurityTest.tearDown(self)

    def _addContent(self, id='foo', title='Old'):
        ob = ModifiableDummyContent(id, catalog=1)
        ob.title = title
        self.folder._setObject(id, ob)
        return self.folder._getOb(id)

    def _catalogedPaths(self):
        # Every RID must be reachable through its path: no orphans.
        processQueue()
        cat = self.ctool._catalog
        self.assertEqual(len(cat.uids), len(cat.paths))
        self.assertEqual(len(cat), len(cat.paths))
        return sorted(cat.uids.keys())

    def _indexedValue(self, index, path):
        rid = self.ctool.getrid(path)
        return self.ctool._catalog.getIndex(index).getEntryForObject(rid)

    def test_moveObject_not_cataloged(self):
        ob = self._addContent()
        processQueue()

        self.assertFalse(self.ctool.moveObject(ob, '/bar/site/nowhere'))
        self.assertEqual(self._catalogedPaths(), ['/bar/site/folder/foo'])
        self.assertFalse(ob.notified)

    def test_moveObject_drops_stale_entry_at_new_path(self):
        ob = self._addContent()
        processQueue()
        self.ctool.catalog_object(ob, '/bar/site/folder/old')
        old_rid = self.ctool.getrid('/bar/site/folder/old')

        self.assertTrue(self.ctool.moveObject(ob, '/bar/site/folder/old'))

        self.assertEqual(self._catalogedPaths(), ['/bar/site/folder/foo'])
        self.assertEqual(self.ctool.getrid('/bar/site/folder/foo'), old_rid)

    def test_rename_preserves_rid(self):
        self._addContent()
        processQueue()
        rid = self.ctool.getrid('/bar/site/folder/foo')
        transaction.savepoint(optimistic=True)

        self.folder.manage_renameObject('foo', 'baz')

        self.assertEqual(self._catalogedPaths(), ['/bar/site/folder/baz'])
        self.assertEqual(self.ctool.getrid('/bar/site/folder/baz'), rid)
        self.assertEqual(self._indexedValue('getId', '/bar/site/folder/baz'),
                         'baz')
        self.assertEqual(
            self._indexedValue('path', '/bar/site/folder/baz'),
            '/bar/site/folder/baz')

    def test_cut_and_paste_preserves_rid(self):
        self._addContent()
        processQueue()
        rid = self.ctool.getrid('/bar/site/folder/foo')
        transaction.savepoint(optimistic=True)

        cookie = self.folder.manage_cutObjects(ids=['foo'])
        self.sub.manage_pasteObjects(cookie)

        self.assertEqual(self._catalogedPaths(), ['/bar/site/folder/sub/foo'])
        self.assertEqual(self.ctool.getrid('/bar/site/folder/sub/foo'), rid)

    def test_move_updates_modification_date(self):
        self._addContent()
        processQueue()
        transaction.savepoint(optimistic=True)

        self.folder.manage_renameObject('foo', 'baz')

        self.assertTrue(self.folder.baz.notified)

    def test_move_reindexes_all_indexes_by_default(self):
        ob = self._addContent(title='Old')
        processQueue()
        ob.title = 'New'  # changed without reindexing
        transaction.savepoint(optimistic=True)

        self.folder.manage_renameObject('foo', 'baz')

        self.assertEqual(self._catalogedPaths(), ['/bar/site/folder/baz'])
        self.assertEqual(self._indexedValue('Title', '/bar/site/folder/baz'),
                         'New')

    def test_move_skips_contextless_indexes(self):
        self.ctool._setProperty('contextless_indexes', ('Title',), 'lines')
        ob = self._addContent(title='Old')
        processQueue()
        ob.title = 'New'  # changed without reindexing
        transaction.savepoint(optimistic=True)

        self.folder.manage_renameObject('foo', 'baz')

        self.assertEqual(self._catalogedPaths(), ['/bar/site/folder/baz'])
        self.assertEqual(self._indexedValue('Title', '/bar/site/folder/baz'),
                         'Old')
        self.assertEqual(self._indexedValue('getId', '/bar/site/folder/baz'),
                         'baz')

    def test_rename_with_pending_reindex(self):
        # A reindex queued before the rename must not create a second
        # catalog entry next to the remapped one.
        ob = self._addContent(title='Old')
        processQueue()
        transaction.savepoint(optimistic=True)
        ob.title = 'New'
        ob.reindexObject()

        self.folder.manage_renameObject('foo', 'baz')

        self.assertEqual(self._catalogedPaths(), ['/bar/site/folder/baz'])
        self.assertEqual(self._indexedValue('Title', '/bar/site/folder/baz'),
                         'New')

    def test_cut_and_paste_with_pending_reindex(self):
        # A reindex queued before the move must not leave an entry behind
        # at the old path.
        ob = self._addContent(title='Old')
        processQueue()
        transaction.savepoint(optimistic=True)
        ob.title = 'New'
        ob.reindexObject()

        cookie = self.folder.manage_cutObjects(ids=['foo'])
        self.sub.manage_pasteObjects(cookie)

        self.assertEqual(self._catalogedPaths(), ['/bar/site/folder/sub/foo'])
        self.assertEqual(
            self._indexedValue('Title', '/bar/site/folder/sub/foo'), 'New')

    def test_add_and_rename_in_same_transaction(self):
        self._addContent(title='Old')  # index operation still queued
        transaction.savepoint(optimistic=True)

        self.folder.manage_renameObject('foo', 'baz')

        self.assertEqual(self._catalogedPaths(), ['/bar/site/folder/baz'])
        self.assertEqual(self._indexedValue('Title', '/bar/site/folder/baz'),
                         'Old')


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(
            IndexableObjectWrapperTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(CatalogToolTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            CatalogToolMoveTests),
    ))
