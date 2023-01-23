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
""" Unit tests for ActionsTool module.
"""

import unittest
import warnings

from AccessControl.SecurityManagement import newSecurityManager
from zope.component import getSiteManager
from zope.interface.verify import verifyClass
from zope.testing.cleanup import cleanUp

from ..ActionInformation import Action
from ..ActionInformation import ActionCategory
from ..ActionInformation import ActionInformation
from ..Expression import Expression
from ..interfaces import IMembershipTool
from ..interfaces import ISiteRoot
from ..interfaces import IURLTool
from ..MembershipTool import MembershipTool
from ..URLTool import URLTool
from .base.security import OmnipotentUser
from .base.testcase import SecurityTest


class ActionsToolTests(unittest.TestCase):

    def _getTargetClass(self):
        from ..ActionsTool import ActionsTool

        return ActionsTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_interfaces(self):
        from ..interfaces import IActionProvider
        from ..interfaces import IActionsTool

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
        from .. import ActionProviderBase
        try:
            del ActionProviderBase.__warningregistry__
        except AttributeError:
            pass
        tool = self._makeOne()
        tool.addAction('an_id', 'name', '', '', '', 'object')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            tool.getActionObject('object/an_id')
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertTrue(
                'Old-style actions are deprecated and will be removed in CMF '
                '2.4. Use Action and Action Category objects instead.'
                in str(w[-1].message))

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


class ActionsToolSecurityTests(SecurityTest):

    def _getTargetClass(self):
        from ..ActionsTool import ActionsTool

        return ActionsTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def setUp(self):
        from ..interfaces import IActionsTool

        SecurityTest.setUp(self)
        self.tool = self._makeOne()
        self.tool.action_providers = ('portal_actions',)
        self.app._setObject('foo', URLTool())
        sm = getSiteManager()
        sm.registerUtility(self.tool, IActionsTool)
        sm.registerUtility(MembershipTool(), IMembershipTool)
        sm.registerUtility(self.app, ISiteRoot)
        sm.registerUtility(URLTool(), IURLTool)

    def tearDown(self):
        cleanUp()
        SecurityTest.tearDown(self)

    def test_listActionInformationActions(self):
        # Check that listFilteredActionsFor works for objects that return
        # ActionInformation objects
        tool = self.tool
        act = 'string:${folder_url}/folder_contents'
        tool._actions = (
              ActionInformation(id='folderContents',
                                title='Folder contents',
                                action=Expression(text=act),
                                icon_expr=Expression(text='string:'
                                                     '${folder_url}/icon.gif'),
                                condition=Expression(text='python: '
                                                     'folder is not object'),
                                permissions=('List folder contents',),
                                category='folder',
                                link_target='_top',
                                visible=1),)

        newSecurityManager(None, OmnipotentUser().__of__(self.app.acl_users))
        expected = {'workflow': [],
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
                    'global': []}
        with warnings.catch_warnings():
            # Ignore the warning - anything that uses the attribute
            # ``_actions`` will raise it. The DeprecationWarning mentions the
            # goal of removing old-style actions, but this is too hard and may
            # never happen.
            warnings.simplefilter('ignore')
            self.assertEqual(tool.listFilteredActionsFor(self.app.foo),
                             expected)


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(ActionsToolTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            ActionsToolSecurityTests),
        ))
