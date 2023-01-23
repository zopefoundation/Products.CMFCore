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
""" Unit tests for Expression module.
"""

import unittest

from zope.component import getSiteManager
from zope.testing.cleanup import cleanUp

from ..ActionInformation import ActionInformation
from ..Expression import Expression
from ..Expression import createExprContext
from ..interfaces import IMembershipTool
from .base.dummy import DummyContent
from .base.dummy import DummyTool as DummyMembershipTool
from .base.testcase import SecurityTest


class ExpressionTests(SecurityTest):

    def setUp(self):
        SecurityTest.setUp(self)
        app = self.app
        app._setObject('portal', DummyContent('portal', url='url_portal'))
        self.portal = app.portal
        self.folder = DummyContent('foo', url='url_foo')
        self.object = DummyContent('bar', url='url_bar')
        self.ai = ActionInformation(id='view',
                                    title='View',
                                    action=Expression(text='view'),
                                    condition=Expression(text='member'),
                                    category='global',
                                    visible=1)

    def tearDown(self):
        cleanUp()
        SecurityTest.tearDown(self)

    def test_anonymous_ec(self):
        sm = getSiteManager()
        sm.registerUtility(DummyMembershipTool(), IMembershipTool)
        ec = createExprContext(self.folder, self.portal, self.object)
        member = ec.contexts['member']
        self.assertFalse(member)

    def test_authenticatedUser_ec(self):
        sm = getSiteManager()
        sm.registerUtility(DummyMembershipTool(anon=0), IMembershipTool)
        ec = createExprContext(self.folder, self.portal, self.object)
        member = ec.contexts['member']
        self.assertEqual(member.getId(), 'dummy')

    def test_ec_context(self):
        sm = getSiteManager()
        sm.registerUtility(DummyMembershipTool(), IMembershipTool)
        ec = createExprContext(self.folder, self.portal, self.object)
        object = ec.contexts['object']
        portal = ec.contexts['portal']
        folder = ec.contexts['folder']
        self.assertTrue(object)
        self.assertEqual(object.id, 'bar')
        self.assertEqual(object.absolute_url(), 'url_bar')
        self.assertTrue(portal)
        self.assertEqual(portal.id, 'portal')
        self.assertEqual(portal.absolute_url(), 'url_portal')
        self.assertTrue(folder)
        self.assertEqual(folder.id, 'foo')
        self.assertEqual(folder.absolute_url(), 'url_foo')


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(ExpressionTests),
        ))
