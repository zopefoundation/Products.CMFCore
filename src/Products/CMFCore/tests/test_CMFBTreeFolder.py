##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for CMFBTreeFolder module.
"""

import unittest

from ..testing import ConformsToFolder


class CMFBTreeFolderTests(ConformsToFolder, unittest.TestCase):

    def _getTargetClass(self):
        from ..CMFBTreeFolder import CMFBTreeFolder

        return CMFBTreeFolder

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_empty(self):
        empty = self._makeOne('test')
        self.assertEqual(len(empty.objectIds()), 0)


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(CMFBTreeFolderTests),
        ))
