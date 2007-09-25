##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for five actions tool.

$Id$
"""

import unittest
from Testing import ZopeTestCase


def test_fiveactionstool():
    """
    Test the Five actions tool.

    Some basic setup:

      >>> import Products.Five
      >>> import Products.CMFCore
      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> zcml.load_config('permissions.zcml', Products.Five)
      >>> zcml.load_config('meta.zcml', Products.CMFCore)
      >>> folder = self.folder

    For menus to work, the request must have defaultSkin.
    
      >>> from zope.publisher.browser import setDefaultSkin
      >>> setDefaultSkin(self.folder.REQUEST)
      
    We need to make Zope 3 use Zope 2s security policy
    
      >>> from zope.security.management import thread_local
      >>> thread_local.interaction = None
      >>> from Products.Five.security import newInteraction
      >>> newInteraction()

    Log in as manager
   
      >>> uf = self.folder.acl_users
      >>> uf._doAddUser('manager', 'r00t', ['Manager'], [])
      >>> self.login('manager')

    Let's create a Five actions tool:

      >>> from Products.CMFCore.fiveactionstool import FiveActionsTool
      >>> folder.tool = FiveActionsTool()
      >>> tool = folder.tool # rewrap

    Let's create some simple content object providing ISimpleContent:

      >>> from Products.Five.tests.testing.simplecontent import SimpleContent
      >>> id = self.folder._setObject('foo', SimpleContent('foo', 'Foo'))
      >>> foo = self.folder.foo

    Now we'll load a configuration file specifying some menu and menu
    items for ISimpleContent.

      >>> import Products.CMFCore.tests
      >>> zcml.load_config('fiveactions.zcml', Products.CMFCore.tests)

    Let's look what the tool lists as actions for such an object. 

      >>> actions = tool.listActions(object=foo)
      >>> [(action.category, action.id) for action in actions]
      [('mymenu', 'action_foo_public.html'), ('mymenu', 'action_foo_protected.html')]

    But if we log in as a user who is not manager, we should not get the
    protected menu item, , as it was protected by a more restrictive permission:
    
      >>> uf = self.folder.acl_users
      >>> uf._doAddUser('user', 'user', [], [])
      >>> self.login('user')
      
      >>> actions = tool.listActions(object=foo)
      >>> [(action.category, action.id) for action in actions]
      [('mymenu', 'action_foo_public.html')]

    When looking at an object not implementing ISimpleContent, we see no
    actions:

      >>> tool.listActions(object=folder)
      ()

    The tool itself doesn't have any actions:

      >>> tool.listActions()
      ()

    Cleanup:

      >>> from zope.testing.cleanup import cleanUp
      >>> cleanUp()
    """


def test_suite():
    return unittest.TestSuite((
        ZopeTestCase.ZopeDocTestSuite(),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
