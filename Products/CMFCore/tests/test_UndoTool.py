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
""" Unit tests for UndoTool module.

$Id$
"""

import unittest
import Testing


class DummyFolder(object):

    def undoable_transactions(self, first_transaction=None,
                              last_transaction=None,
                              PrincipiaUndoBatchSize=None):
        return ()


class UndoToolTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.CMFCore.UndoTool import UndoTool

        return UndoTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_z2interfaces(self):
        from Interface.Verify import verifyClass
        from Products.CMFCore.interfaces.portal_undo \
                import portal_undo as IUndoTool

        verifyClass(IUndoTool, self._getTargetClass())

    def test_z3interfaces(self):
        from zope.interface.verify import verifyClass
        from Products.CMFCore.interfaces import IUndoTool

        verifyClass(IUndoTool, self._getTargetClass())

    def test_listUndoableTransactionsFor(self):
        udtool = self._makeOne()
        obj = DummyFolder()
        transactions = udtool.listUndoableTransactionsFor(obj)
        self.assertEqual(transactions, ())


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UndoToolTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
