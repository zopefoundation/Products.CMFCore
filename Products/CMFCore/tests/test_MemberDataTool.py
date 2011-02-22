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
import Testing

import Acquisition
from zope.component import provideUtility
from zope.component.interfaces import IFactory
from zope.interface.verify import verifyClass
from zope.testing.cleanup import cleanUp


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
        user.roles = tuple(roles)
        user.domains = tuple(domains)

    def getUsers(self):
        return self._users.values()


class DummyUser(Acquisition.Implicit):

    def __init__(self, name, password, roles, domains):
        self.name = name
        self.__ = password
        self.roles = tuple(roles)
        self.domains = tuple(domains)

    def getId(self):
        return self.name

    def getUserName(self):
        return 'name of %s' % self.getId()

    def getRoles(self):
        return self.roles + ('Authenticated',)

    def getDomains(self):
        return self.domains


class DummyMemberDataTool(Acquisition.Implicit):

    _members = {}


class MemberDataToolTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.CMFCore.MemberDataTool import MemberDataTool

        return MemberDataTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_interfaces(self):
        from Products.CMFCore.interfaces import IMemberDataTool

        verifyClass(IMemberDataTool, self._getTargetClass())

    def test_deleteMemberData(self):
        tool = self._makeOne()
        tool.registerMemberData('Dummy', 'user_foo')
        self.assertTrue(tool._members.has_key('user_foo'))
        self.assertTrue(tool.deleteMemberData('user_foo'))
        self.assertFalse(tool._members.has_key('user_foo'))
        self.assertFalse(tool.deleteMemberData('user_foo'))

    def test_pruneMemberData(self):
        # This needs a tad more setup
        from OFS.Folder import Folder
        from Products.CMFCore.MembershipTool import MembershipTool
        folder = Folder('test')
        folder._setObject('portal_memberdata', self._makeOne())
        folder._setObject('portal_membership', MembershipTool())
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
        from Products.CMFCore.MemberDataTool import MemberAdapter

        return MemberAdapter

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def setUp(self):
        self.mdtool = DummyMemberDataTool()
        self.aclu = DummyUserFolder()

    def tearDown(self):
        cleanUp()

    def test_interfaces(self):
        from AccessControl.interfaces import IUser
        from Products.CMFCore.interfaces import IMember
        from Products.CMFCore.interfaces import IMemberData

        verifyClass(IMember, self._getTargetClass())
        verifyClass(IMemberData, self._getTargetClass())
        verifyClass(IUser, self._getTargetClass())

    def test_setSecurityProfile(self):
        user = DummyUser('bob', 'pw', ['Role'], ['domain'])
        self.aclu._addUser(user)
        user = user.__of__(self.aclu)
        member = self._makeOne(user, self.mdtool)
        member.setSecurityProfile(password='newpw')
        self.assertEqual(user.__, 'newpw')
        self.assertEqual(list(user.roles), ['Role'])
        self.assertEqual(list(user.domains), ['domain'])
        member.setSecurityProfile(roles=['NewRole'])
        self.assertEqual(user.__, 'newpw')
        self.assertEqual(list(user.roles), ['NewRole'])
        self.assertEqual(list(user.domains), ['domain'])
        member.setSecurityProfile(domains=['newdomain'])
        self.assertEqual(user.__, 'newpw')
        self.assertEqual(list(user.roles), ['NewRole'])
        self.assertEqual(list(user.domains), ['newdomain'])

    def test_switching_memberdata_factory(self):
        from Products.CMFCore.MemberDataTool import MemberData

        user1 = DummyUser('dummy', '', [], []).__of__(self.aclu)
        member = self._makeOne(user1, self.mdtool)
        self.assertEqual(getattr(member._md, 'iamnew', None), None)

        class NewMemberData(MemberData):
            iamnew = 'yes'
        provideUtility(NewMemberData, IFactory, 'MemberData')

        user2 = DummyUser('dummy2', '', [], []).__of__(self.aclu)
        member = self._makeOne(user2, self.mdtool)
        self.assertEqual(getattr(member._md, 'iamnew', None), 'yes')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MemberDataToolTests),
        unittest.makeSuite(MemberAdapterTests),
        ))
