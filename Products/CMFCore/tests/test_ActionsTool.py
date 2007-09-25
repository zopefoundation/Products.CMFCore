##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for ActionsTool module.

$Id$
"""

import unittest
import Testing

from zope.component import getSiteManager
from zope.testing.cleanup import cleanUp

from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.ActionInformation import ActionCategory
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.Expression import Expression
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.MembershipTool import MembershipTool
from Products.CMFCore.tests.base.testcase import SecurityRequestTest
from Products.CMFCore.URLTool import URLTool


class ActionsToolTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.CMFCore.ActionsTool import ActionsTool

        return ActionsTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_z2interfaces(self):
        from Interface.Verify import verifyClass
        from Products.CMFCore.interfaces.portal_actions \
                import ActionProvider as IActionProvider
        from Products.CMFCore.interfaces.portal_actions \
                import portal_actions as IActionsTool

        verifyClass(IActionProvider, self._getTargetClass())
        verifyClass(IActionsTool, self._getTargetClass())

    def test_z3interfaces(self):
        from zope.interface.verify import verifyClass
        from Products.CMFCore.interfaces import IActionProvider
        from Products.CMFCore.interfaces import IActionsTool

        verifyClass(IActionProvider, self._getTargetClass())
        verifyClass(IActionsTool, self._getTargetClass())

    def test_listActionProviders(self):
        tool = self._makeOne()
        tool.action_providers = ('portal_actions',)
        self.assertEqual(tool.listActionProviders(), ('portal_actions',))

    def test_addActionProvider(self):
        tool = self._makeOne()
        tool.foo = 'acquirable attribute'
        tool.portal_url = 'acquirable attribute'
        tool.action_providers = ('portal_actions',)
        tool.addActionProvider('foo')
        self.assertEqual(tool.listActionProviders(),
                          ('portal_actions', 'foo'))
        tool.addActionProvider('portal_url')
        tool.addActionProvider('foo')
        self.assertEqual(tool.listActionProviders(),
                          ('portal_actions', 'foo', 'portal_url'))

    def test_deleteActionProvider(self):
        tool = self._makeOne()
        tool.action_providers = ('portal_actions', 'foo')
        tool.deleteActionProvider('foo')
        self.assertEqual(tool.listActionProviders(), ('portal_actions',))

    def test_getActionObject(self):
        tool = self._makeOne()
        tool._setObject('object', ActionCategory('object'))
        tool.object._setObject('newstyle_id', Action('newstyle_id'))
        tool.addAction('an_id', 'name', '', '', '', 'object')
        rval = tool.getActionObject('object/an_id')
        self.assertEqual(rval, tool._actions[0])
        rval = tool.getActionObject('object/newstyle_id')
        self.assertEqual(rval, None)
        rval = tool.getActionObject('object/not_existing_id')
        self.assertEqual(rval, None)
        self.assertRaises(ValueError, tool.getActionObject, 'wrong_format')


class ActionsToolSecurityRequestTests(SecurityRequestTest):

    def _getTargetClass(self):
        from Products.CMFCore.ActionsTool import ActionsTool

        return ActionsTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def setUp(self):
        SecurityRequestTest.setUp(self)

        root = self.root
        sm = getSiteManager()
        sm.registerUtility(root, ISiteRoot)
        root._setObject( 'portal_actions', self._makeOne() )
        root._setObject( 'portal_url', URLTool() )
        root._setObject( 'foo', URLTool() )
        root._setObject('portal_membership', MembershipTool())
        self.tool = root.portal_actions
        self.tool.action_providers = ('portal_actions',)

    def test_listActionInformationActions(self):
        # Check that listFilteredActionsFor works for objects that return
        # ActionInformation objects
        root = self.root
        tool = self.tool
        tool._actions = (
              ActionInformation(id='folderContents',
                                title='Folder contents',
                                action=Expression(text='string:'
                                             '${folder_url}/folder_contents'),
                                condition=Expression(text='python: '
                                                      'folder is not object'),
                                permissions=('List folder contents',),
                                category='folder',
                                visible=1)
            ,
            )
        self.assertEqual(tool.listFilteredActionsFor(root.foo),
                         {'workflow': [],
                          'user': [],
                          'object': [],
                          'folder': [{'id': 'folderContents',
                                      'url': 'http://nohost/folder_contents',
                                      'title': 'Folder contents',
                                      'description': '',
                                      'visible': True,
                                      'available': True,
                                      'allowed': True,
                                      'category': 'folder'}],
                          'global': []})

    def tearDown(self):
        cleanUp()
        SecurityRequestTest.tearDown(self)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ActionsToolTests),
        unittest.makeSuite(ActionsToolSecurityRequestTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
