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
""" Unit tests for RegistrationTool module. """

import unittest
import Testing

from zope.interface.verify import verifyClass


class RegistrationToolTests(unittest.TestCase):

    def _makeOne(self):
        from Products.CMFCore.RegistrationTool import RegistrationTool

        return RegistrationTool()

    def test_interfaces(self):
        from Products.CMFCore.interfaces import IRegistrationTool
        from Products.CMFCore.RegistrationTool import RegistrationTool

        verifyClass(IRegistrationTool, RegistrationTool)

    def test_generatePassword(self):
        rtool = self._makeOne()
        self.failUnless( len( rtool.generatePassword() ) >= 5 )


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(RegistrationToolTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
