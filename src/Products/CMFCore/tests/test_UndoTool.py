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
""" Unit tests for UndoTool module.
"""

import unittest

from zope.interface.verify import verifyClass


class DummyFolder:

    def undoable_transactions(self, first_transaction=None,
                              last_transaction=None,
                              PrincipiaUndoBatchSize=None):
        return ()


class UndoToolTests(unittest.TestCase):

    def _getTargetClass(self):
        from ..UndoTool import UndoTool

        return UndoTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_interfaces(self):
        from ..interfaces import IUndoTool

        verifyClass(IUndoTool, self._getTargetClass())

    def test_listUndoableTransactionsFor(self):
        udtool = self._makeOne()
        obj = DummyFolder()
        transactions = udtool.listUndoableTransactionsFor(obj)
        self.assertEqual(transactions, ())


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(UndoToolTests),
        ))
