##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for MembershipTool module.
"""

import unittest

from AccessControl.SecurityManagement import newSecurityManager
from OFS.Folder import Folder
from zope.component import getSiteManager
from zope.component.interfaces import IFactory
from zope.interface.verify import verifyClass
from zope.testing.cleanup import cleanUp

from ..CMFBTreeFolder import CMFBTreeFolder
from ..interfaces import IMemberDataTool
from ..interfaces import ISiteRoot
from ..interfaces import IWorkflowTool
from ..MemberDataTool import MemberDataTool
from ..permissions import AccessContentsInformation
from ..permissions import View
from ..PortalFolder import PortalFolder
from .base.dummy import DummySite
from .base.dummy import DummyTool
from .base.dummy import DummyUserFolder
from .base.testcase import SecurityTest


class MembershipToolTests(unittest.TestCase):

    def _getTargetClass(self):
        from ..MembershipTool import MembershipTool

        return MembershipTool

    def test_interfaces(self):
        from ..interfaces import IMembershipTool

        verifyClass(IMembershipTool, self._getTargetClass())


class MembershipToolSecurityTests(SecurityTest):

    def _getTargetClass(self):
        from ..MembershipTool import MembershipTool

        return MembershipTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def _makeSite(self, parent=None):
        if parent is None:
            parent = self.app
        site = DummySite('site').__of__(parent)
        site._setObject('portal_membership', self._makeOne())
        return site

    def test_getCandidateLocalRoles(self):
        site = self._makeSite()
        mtool = site.portal_membership
        acl_users = site._setObject('acl_users', DummyUserFolder())

        newSecurityManager(None, acl_users.user_foo)
        rval = mtool.getCandidateLocalRoles(mtool)
        self.assertEqual(rval, ('Dummy',))
        newSecurityManager(None, acl_users.all_powerful_Oz)
        rval = mtool.getCandidateLocalRoles(mtool)
        self.assertEqual(rval, ('Manager', 'Member', 'Owner', 'Reviewer'))

    def test_isMemberAccessAllowed(self):
        site = self._makeSite()
        mtool = site.portal_membership
        acl_users = site._setObject('acl_users', DummyUserFolder())
        self.assertFalse(mtool.isMemberAccessAllowed('user_foo'))

        newSecurityManager(None, acl_users.user_bar)
        self.assertFalse(mtool.isMemberAccessAllowed('user_foo'))

        newSecurityManager(None, acl_users.user_foo)
        self.assertTrue(mtool.isMemberAccessAllowed('user_foo'))

        newSecurityManager(None, acl_users.all_powerful_Oz)
        self.assertTrue(mtool.isMemberAccessAllowed('user_foo'))

    def test_getMemberById_nonesuch(self):
        INVALID_USER_ID = 'nonesuch'

        self.app._setObject('folder', Folder('folder'))
        site = self._makeSite(self.app.folder)
        tool = site.portal_membership
        site.acl_users = DummyUserFolder()
        self.assertEqual(None, tool.getMemberById(INVALID_USER_ID))

    def test_getMemberById_local(self):
        LOCAL_USER_ID = 'user_foo'

        self.app._setObject('folder', Folder('folder'))
        site = self._makeSite(self.app.folder)
        site._setObject('acl_users', DummyUserFolder())
        tool = site.portal_membership
        member = tool.getMemberById(LOCAL_USER_ID)
        self.assertEqual(member.getId(), LOCAL_USER_ID)

    def test_getMemberById_nonlocal(self):
        NONLOCAL_USER_ID = 'user_bar'

        self.app._setObject('folder', Folder('folder'))
        site = self._makeSite(self.app.folder)
        self.app.folder._setObject('acl_users', DummyUserFolder())
        tool = site.portal_membership
        member = tool.getMemberById(NONLOCAL_USER_ID)
        self.assertEqual(member.getId(), NONLOCAL_USER_ID)

    def test_getMemberById_chained(self):
        LOCAL_USER_ID = 'user_foo'
        NONLOCAL_USER_ID = 'user_bar'

        self.app._setObject('folder', Folder('folder'))
        site = self._makeSite(self.app.folder)
        tool = site.portal_membership

        local_uf = DummyUserFolder()
        delattr(local_uf, NONLOCAL_USER_ID)
        site._setObject('acl_users', local_uf)

        nonlocal_uf = DummyUserFolder()
        delattr(nonlocal_uf, LOCAL_USER_ID)
        self.app.folder._setObject('acl_users', nonlocal_uf)

        local_member = tool.getMemberById(LOCAL_USER_ID)
        self.assertEqual(local_member.getId(), LOCAL_USER_ID)

        nonlocal_member = tool.getMemberById(NONLOCAL_USER_ID)
        self.assertEqual(nonlocal_member.getId(), NONLOCAL_USER_ID)


class MembershipToolMemberAreaTests(SecurityTest):

    def _getTargetClass(self):
        from ..MembershipTool import MembershipTool

        return MembershipTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def _makeSite(self, parent=None):
        if parent is None:
            parent = self.app
        site = DummySite('site').__of__(parent)
        site.__ac_roles__ = ('Reviewer',)
        site._setObject('portal_membership', self._makeOne())
        return site

    def setUp(self):
        from ..MembershipTool import BBBHomeFolderFactory

        SecurityTest.setUp(self)
        sm = getSiteManager()
        sm.registerUtility(DummyTool(), IWorkflowTool)
        sm.registerUtility(BBBHomeFolderFactory, IFactory,
                           'cmf.folder.home.bbb1')

    def tearDown(self):
        cleanUp()
        SecurityTest.tearDown(self)

    def test_createMemberArea(self):
        site = self._makeSite()
        mtool = site.portal_membership
        members = site._setObject('Members', PortalFolder('Members'))
        acl_users = site._setObject('acl_users', DummyUserFolder())

        # permission
        mtool.createMemberArea('user_foo')
        self.assertFalse(hasattr(members.aq_self, 'user_foo'))
        newSecurityManager(None, acl_users.user_bar)
        mtool.createMemberArea('user_foo')
        self.assertFalse(hasattr(members.aq_self, 'user_foo'))
        newSecurityManager(None, acl_users.user_foo)
        mtool.setMemberareaCreationFlag()
        mtool.createMemberArea('user_foo')
        self.assertFalse(hasattr(members.aq_self, 'user_foo'))
        newSecurityManager(None, acl_users.all_powerful_Oz)
        mtool.setMemberareaCreationFlag()
        mtool.createMemberArea('user_foo')
        self.assertTrue(hasattr(members.aq_self, 'user_foo'))

        # default content
        f = members.user_foo
        ownership = acl_users.user_foo
        localroles = (('user_foo', ('Owner',)),)
        self.assertEqual(f.Title(), "user_foo's Home")
        self.assertEqual(f.getPortalTypeName(), 'Folder')
        self.assertEqual(f.getOwner(), ownership)
        self.assertEqual(f.get_local_roles(), localroles,
                         'CMF Collector issue #162 (LocalRoles broken): %s'
                         % str(f.get_local_roles()))
        for p in (View, AccessContentsInformation):
            roles = [r['name'] for r in f.rolesOfPermission(p)
                     if r['selected']]
            self.assertEqual(roles, ['Manager', 'Owner', 'Reviewer'])
            self.assertEqual(bool(f.acquiredRolesAreUsedBy(p)), False)

    def test_createMemberAreaCMFBTreeFolder(self):
        # Test member area creation if the toplevel "Members" folder is
        # a CMFBTreeFolder (https://bugs.launchpad.net/zope-cmf/+bug/161668)
        site = self._makeSite()
        mtool = site.portal_membership
        members = site._setObject('Members', CMFBTreeFolder('Members'))
        acl_users = site._setObject('acl_users', DummyUserFolder())

        # permission
        mtool.createMemberArea('user_foo')
        self.assertFalse(hasattr(members.aq_self, 'user_foo'))
        newSecurityManager(None, acl_users.user_bar)
        mtool.createMemberArea('user_foo')
        self.assertFalse(hasattr(members.aq_self, 'user_foo'))
        newSecurityManager(None, acl_users.user_foo)
        mtool.setMemberareaCreationFlag()
        mtool.createMemberArea('user_foo')
        self.assertFalse(hasattr(members.aq_self, 'user_foo'))
        newSecurityManager(None, acl_users.all_powerful_Oz)
        mtool.setMemberareaCreationFlag()
        mtool.createMemberArea('user_foo')
        self.assertTrue(hasattr(members.aq_self, 'user_foo'))

        # default content
        f = members.user_foo
        ownership = acl_users.user_foo
        localroles = (('user_foo', ('Owner',)),)
        self.assertEqual(f.Title(), "user_foo's Home")
        self.assertEqual(f.getPortalTypeName(), 'Folder')
        self.assertEqual(f.getOwner(), ownership)
        self.assertEqual(f.get_local_roles(), localroles,
                         'CMF Collector issue #162 (LocalRoles broken): %s'
                         % str(f.get_local_roles()))
        for p in (View, AccessContentsInformation):
            roles = [r['name'] for r in f.rolesOfPermission(p)
                     if r['selected']]
            self.assertEqual(roles, ['Manager', 'Owner', 'Reviewer'])
            self.assertEqual(bool(f.acquiredRolesAreUsedBy(p)), False)

    def test_createMemberArea_chained(self):
        LOCAL_USER_ID = 'user_foo'
        NONLOCAL_USER_ID = 'user_bar'

        self.app._setObject('folder', Folder('folder'))
        site = self._makeSite(self.app.folder)
        mtool = site.portal_membership
        members = site._setObject('Members', PortalFolder('Members'))

        local_uf = DummyUserFolder()
        delattr(local_uf, NONLOCAL_USER_ID)
        acl_users = site._setObject('acl_users', local_uf)

        nonlocal_uf = DummyUserFolder()
        delattr(nonlocal_uf, LOCAL_USER_ID)
        self.app.folder._setObject('acl_users', nonlocal_uf)

        newSecurityManager(None, acl_users.all_powerful_Oz)
        mtool.createMemberArea(NONLOCAL_USER_ID)
        self.assertTrue(hasattr(members.aq_self, NONLOCAL_USER_ID))
        mtool.createMemberArea(LOCAL_USER_ID)
        self.assertTrue(hasattr(members.aq_self, LOCAL_USER_ID))

    def test_deleteMembers(self):
        site = self._makeSite()
        sm = getSiteManager()
        sm.registerUtility(site, ISiteRoot)
        mtool = site.portal_membership
        members = site._setObject('Members', PortalFolder('Members'))
        acl_users = site._setObject('acl_users', DummyUserFolder())
        mdtool = MemberDataTool()
        sm.registerUtility(mdtool, IMemberDataTool)
        newSecurityManager(None, acl_users.all_powerful_Oz)

        self.assertEqual(acl_users.getUserById('user_foo'), acl_users.user_foo)
        mtool.createMemberArea('user_foo')
        self.assertTrue(hasattr(members.aq_self, 'user_foo'))
        mdtool.registerMemberData('Dummy', 'user_foo')
        self.assertTrue('user_foo' in mdtool._members)

        rval = mtool.deleteMembers(('user_foo', 'user_baz'))
        self.assertEqual(rval, ('user_foo',))
        self.assertFalse(acl_users.getUserById('user_foo', None))
        self.assertFalse('user_foo' in mdtool._members)
        self.assertFalse(hasattr(members.aq_self, 'user_foo'))

    def test_deleteMembersUnsupported(self):
        # Quite a few user folders do not support the deletion API
        # http://www.zope.org/Collectors/CMF/481
        # Make sure we get the right exception
        site = self._makeSite()
        sm = getSiteManager()
        sm.registerUtility(site, ISiteRoot)
        mtool = site.portal_membership
        members = site._setObject('Members', PortalFolder('Members'))
        acl_users = site._setObject('acl_users', DummyUserFolder())
        mdtool = MemberDataTool()
        sm.registerUtility(mdtool, IMemberDataTool)
        newSecurityManager(None, acl_users.all_powerful_Oz)

        self.assertEqual(acl_users.getUserById('user_foo'), acl_users.user_foo)
        mtool.createMemberArea('user_foo')
        self.assertTrue(hasattr(members.aq_self, 'user_foo'))
        mdtool.registerMemberData('Dummy', 'user_foo')
        self.assertTrue('user_foo' in mdtool._members)

        # Fake an incompatible user folder by deleting the class method
        deletion_method = DummyUserFolder.userFolderDelUsers
        del DummyUserFolder.userFolderDelUsers
        self.assertRaises(NotImplementedError, mtool.deleteMembers,
                          ('user_foo',))
        self.assertTrue(acl_users.getUserById('user_foo', None))
        self.assertTrue('user_foo' in mdtool._members)
        self.assertTrue(hasattr(members.aq_self, 'user_foo'))

        # Cleanup
        DummyUserFolder.userFolderDelUsers = deletion_method


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(MembershipToolTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            MembershipToolSecurityTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            MembershipToolMemberAreaTests),
        ))
