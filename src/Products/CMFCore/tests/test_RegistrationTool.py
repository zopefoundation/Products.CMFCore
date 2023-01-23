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
""" Unit tests for RegistrationTool module.
"""

import unittest

from zope.interface.verify import verifyClass


class RegistrationToolTests(unittest.TestCase):

    def _makeOne(self):
        from ..RegistrationTool import RegistrationTool

        return RegistrationTool()

    def test_interfaces(self):
        from ..interfaces import IRegistrationTool
        from ..RegistrationTool import RegistrationTool

        verifyClass(IRegistrationTool, RegistrationTool)

    def test_generatePassword(self):
        rtool = self._makeOne()
        self.assertTrue(len(rtool.generatePassword()) >= 5)
