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
""" Unit tests for DiscussionTool module.
"""

import unittest

from zope.interface.verify import verifyClass


class DiscussionToolTests(unittest.TestCase):

    def test_interfaces(self):
        from ..DiscussionTool import DiscussionTool
        from ..interfaces import IActionProvider
        from ..interfaces import IOldstyleDiscussionTool

        verifyClass(IActionProvider, DiscussionTool)
        verifyClass(IOldstyleDiscussionTool, DiscussionTool)


class OldDiscussableTests(unittest.TestCase):

    def test_interfaces(self):
        from ..DiscussionTool import OldDiscussable
        from ..interfaces import IOldstyleDiscussable

        verifyClass(IOldstyleDiscussable, OldDiscussable)


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(DiscussionToolTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(OldDiscussableTests),
        ))
