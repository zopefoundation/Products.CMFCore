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
""" Unit tests for MemberDataTool module.
"""

import unittest

import Acquisition
from AccessControl.SecurityManagement import newSecurityManager
from DateTime.DateTime import DateTime
from zope.component import getSiteManager
from zope.interface.verify import verifyClass
from zope.testing.cleanup import cleanUp

from ..exceptions import BadRequest
from ..interfaces import IMembershipTool
from .base.security import DummyUser as BaseDummyUser


class DummyUserFolder(Acquisition.Implicit):

    def __init__(self):
        self._users = {}

    def _addUser(self, user):
        self._users[user.getId()] = user

    def userFolderEditUser(self, name, password, roles, domains):
        user = self._users[name]
        if password is not None:
            user.__ = password
        # Emulate AccessControl.User's stupid behavior (should test None)
        user._roles = tuple(roles)
        user._domains = tuple(domains)

    def getUsers(self):
        return self._users.values()


class DummyUser(BaseDummyUser):

    def __init__(self, name, password, roles, domains):
        self._id = self._name = name
        self.__ = password
        self._roles = tuple(roles)
        self._domains = tuple(domains)


class MemberDataToolTests(unittest.TestCase):

    def _getTargetClass(self):
        from ..MemberDataTool import MemberDataTool

        return MemberDataTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def tearDown(self):
        cleanUp()

    def test_interfaces(self):
        from ..interfaces import IMemberDataTool

        verifyClass(IMemberDataTool, self._getTargetClass())

    def test_new(self):
        tool = self._makeOne()
        self.assertEqual(tool.getProperty('email'), '')
        self.assertEqual(tool.getProperty('portal_skin'), '')
        self.assertEqual(tool.getProperty('listed'), False)
        self.assertEqual(tool.getProperty('login_time'),
                         DateTime('1970/01/01 00:00:00 UTC'))
        self.assertEqual(tool.getProperty('last_login_time'),
                         DateTime('1970/01/01 00:00:00 UTC'))

    def test_deleteMemberData(self):
        tool = self._makeOne()
        tool.registerMemberData('Dummy', 'user_foo')
        self.assertTrue('user_foo' in tool._members)
        self.assertTrue(tool.deleteMemberData('user_foo'))
        self.assertFalse('user_foo' in tool._members)
        self.assertFalse(tool.deleteMemberData('user_foo'))

    def test_pruneMemberData(self):
        # This needs a tad more setup
        from OFS.Folder import Folder

        from ..MembershipTool import MembershipTool
        folder = Folder('test')
        folder._setObject('portal_memberdata', self._makeOne())
        sm = getSiteManager()
        sm.registerUtility(MembershipTool().__of__(folder), IMembershipTool)
        folder._setObject('acl_users', DummyUserFolder())
        tool = folder.portal_memberdata

        # Create some members
        for i in range(20):
            tool.registerMemberData('Dummy_%i' % i, 'user_foo_%i' % i)

        # None of these fake members are in the user folder, which means
        # there are 20 members and 20 "orphans"
        contents = tool.getMemberDataContents()
        info_dict = contents[0]
        self.assertEqual(info_dict['member_count'], 20)
        self.assertEqual(info_dict['orphan_count'], 20)

        # Calling the prune method should delete all orphans, so we end
        # up with no members in the tool.
        tool.pruneMemberDataContents()
        contents = tool.getMemberDataContents()
        info_dict = contents[0]
        self.assertEqual(info_dict['member_count'], 0)
        self.assertEqual(info_dict['orphan_count'], 0)


class MemberAdapterTests(unittest.TestCase):

    def _getTargetClass(self):
        from ..MemberDataTool import MemberAdapter

        return MemberAdapter

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def setUp(self):
        from OFS.Folder import Folder

        from ..MemberDataTool import MemberDataTool
        from ..MembershipTool import MembershipTool

        self.site = Folder('test')
        self.site._setObject('portal_memberdata', MemberDataTool())
        sm = getSiteManager()
        sm.registerUtility(MembershipTool(), IMembershipTool)
        self.site._setObject('acl_users', DummyUserFolder())

    def tearDown(self):
        cleanUp()

    def test_interfaces(self):
        from AccessControl.interfaces import IUser

        from ..interfaces import IMember
        from ..interfaces import IMemberData

        verifyClass(IMember, self._getTargetClass())
        verifyClass(IMemberData, self._getTargetClass())
        verifyClass(IUser, self._getTargetClass())

    def test_init_does_not_persist_change(self):
        user = DummyUser('bob', 'pw', ['Role'], [])
        self._makeOne(user, self.site.portal_memberdata)
        self.assertNotIn(user.getId(), self.site.portal_memberdata._members)

    def test_notifyModified_persists_change(self):
        user = DummyUser('bob', 'pw', ['Role'], [])
        member = self._makeOne(user, self.site.portal_memberdata)
        member.notifyModified()
        self.assertIn(user.getId(), self.site.portal_memberdata._members)

    def test_setProperties(self):
        user = DummyUser('bob', 'pw', ['Role'], [])
        user = user.__of__(self.site.acl_users)
        member = self._makeOne(user, self.site.portal_memberdata)
        self.assertRaises(BadRequest, member.setProperties)

        newSecurityManager(None, DummyUser('john', 'pw', ['Role'], []))
        self.assertRaises(BadRequest, member.setProperties)

        newSecurityManager(None, user)
        member.setProperties()
        self.assertEqual(member.getProperty('email'), '')
        self.assertEqual(member.getProperty('login_time'),
                         DateTime('1970/01/01 00:00:00 UTC'))

        member.setProperties({'email': 'BOB@EXAMPLE.ORG',
                              'login_time': '2000/02/02'})
        self.assertEqual(member.getProperty('email'), 'BOB@EXAMPLE.ORG')
        self.assertEqual(member.getProperty('login_time'),
                         DateTime('2000/02/02 00:00:00'))

    def test_setSecurityProfile(self):
        user = DummyUser('bob', 'pw', ['Role'], ['domain'])
        self.site.acl_users._addUser(user)
        user = user.__of__(self.site.acl_users)
        member = self._makeOne(user, self.site.portal_memberdata)
        member.setSecurityProfile(password='newpw')
        self.assertEqual(user.__, 'newpw')
        self.assertEqual(list(user.getRoles()), ['Role'])
        self.assertEqual(list(user.getDomains()), ['domain'])
        member.setSecurityProfile(roles=['NewRole'])
        self.assertEqual(user.__, 'newpw')
        self.assertEqual(list(user.getRoles()), ['NewRole'])
        self.assertEqual(list(user.getDomains()), ['domain'])
        member.setSecurityProfile(domains=['newdomain'])
        self.assertEqual(user.__, 'newpw')
        self.assertEqual(list(user.getRoles()), ['NewRole'])
        self.assertEqual(list(user.getDomains()), ['newdomain'])


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(MemberDataToolTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(MemberAdapterTests),
        ))
