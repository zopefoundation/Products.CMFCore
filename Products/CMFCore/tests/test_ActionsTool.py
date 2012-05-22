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
""" Unit tests for ActionsTool module. """

import unittest
import Testing

from zope.component import getSiteManager
from zope.interface.verify import verifyClass
from zope.testing.cleanup import cleanUp

from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.ActionInformation import ActionCategory
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.Expression import Expression
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.MembershipTool import MembershipTool
from Products.CMFCore.tests.base.testcase import SecurityRequestTest
from Products.CMFCore.tests.base.testcase import WarningInterceptor
from Products.CMFCore.URLTool import URLTool


class ActionsToolTests(unittest.TestCase, WarningInterceptor):

    def tearDown(self):
        self._free_warning_output()

    def _getTargetClass(self):
        from Products.CMFCore.ActionsTool import ActionsTool

        return ActionsTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_interfaces(self):
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

    def test_getActionObject_oldskool_action_deprecated(self):
        # We have to clear APB's __warningregistry__, or else we may not see
        # the warning we expect (i.e., if somebody else triggered it first).
        from Products.CMFCore import ActionProviderBase
        try:
            del ActionProviderBase.__warningregistry__
        except AttributeError:
            pass
        self._trap_warning_output()
        tool = self._makeOne()
        tool.addAction('an_id', 'name', '', '', '', 'object')
        rval = tool.getActionObject('object/an_id')
        self.assertEqual(rval, tool._actions[0])
        warning = self._our_stderr_stream.getvalue()
        self.assertTrue(
            'DeprecationWarning: '
            'Old-style actions are deprecated and will be removed in CMF '
            '2.4. Use Action and Action Category objects instead.' in warning)

    def test_getActionObject_skips_newstyle_actions(self):
        tool = self._makeOne()
        tool._setObject('object', ActionCategory('object'))
        tool.object._setObject('newstyle_id', Action('newstyle_id'))
        rval = tool.getActionObject('object/newstyle_id')
        self.assertEqual(rval, None)

    def test_getActionObject_nonesuch_returns_None(self):
        tool = self._makeOne()
        tool._setObject('object', ActionCategory('object'))
        rval = tool.getActionObject('object/not_existing_id')
        self.assertEqual(rval, None)

    def test_getActionObject_wrong_format_raises_ValueError(self):
        tool = self._makeOne()
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
                                icon_expr=Expression(text='string:'
                                             '${folder_url}/icon.gif'),
                                condition=Expression(text='python: '
                                                      'folder is not object'),
                                permissions=('List folder contents',),
                                category='folder',
                                link_target='_top',
                                visible=1)
            ,
            )
        self.assertEqual(tool.listFilteredActionsFor(root.foo),
                         {'workflow': [],
                          'user': [],
                          'object': [],
                          'folder': [{'id': 'folderContents',
                                      'url': 'http://nohost/folder_contents',
                                      'icon': 'http://nohost/icon.gif',
                                      'title': 'Folder contents',
                                      'description': '',
                                      'visible': True,
                                      'available': True,
                                      'allowed': True,
                                      'category': 'folder',
                                      'link_target': '_top'}],
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
