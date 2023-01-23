##############################################################################
#
# Copyright (c) 2011 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Member data tool xml adapter and setup handler unit tests.
"""

import unittest

from DateTime.DateTime import DateTime
from OFS.Folder import Folder
from zope.component import getSiteManager

from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from ...interfaces import IMemberDataTool
from ...MemberDataTool import MemberDataTool
from ...testing import ExportImportZCMLLayer


_MEMBERDATATOOL_BODY = b"""\
<?xml version="1.0" encoding="utf-8"?>
<object name="portal_memberdata" meta_type="CMF Member Data Tool">
 <property name="email"></property>
 <property name="portal_skin"></property>
 <property name="listed">False</property>
 <property name="login_time">1970/01/01 00:00:00 UTC</property>
 <property name="last_login_time">1970/01/01 00:00:00 UTC</property>
 <property name="fullname"></property>
</object>
"""

_DEFAULT_EXPORT = b"""\
<?xml version="1.0" encoding="utf-8"?>
<object name="portal_memberdata" meta_type="CMF Member Data Tool">
 <property name="email"></property>
 <property name="portal_skin"></property>
 <property name="listed">False</property>
 <property name="login_time">1970/01/01 00:00:00 UTC</property>
 <property name="last_login_time">1970/01/01 00:00:00 UTC</property>
 <property name="fullname"></property>
</object>
"""

_CHANGED_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_memberdata" meta_type="CMF Member Data Tool">
 <property name="email">value1</property>
 <property name="portal_skin">value2</property>
 <property name="listed">True</property>
 <property name="login_time">2010/01/01 00:00:00</property>
 <property name="last_login_time">2010/01/01 00:00:00</property>
 <property name="fullname">value3</property>
 <property name="home_page" type="string"></property>
</object>
"""


class MemberDataToolXMLAdapterTests(BodyAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..memberdata import MemberDataToolXMLAdapter

        return MemberDataToolXMLAdapter

    def setUp(self):
        self._obj = MemberDataTool()
        self._BODY = _MEMBERDATATOOL_BODY


class _MemberDataToolSetup(BaseRegistryTests):

    def _initSite(self, use_changed=False):
        site = Folder(id='site').__of__(self.app)
        mdtool = MemberDataTool()
        getSiteManager().registerUtility(mdtool, IMemberDataTool)

        if use_changed:
            mdtool._updateProperty('email', 'value1')
            mdtool._updateProperty('portal_skin', 'value2')
            mdtool._updateProperty('listed', 'True')
            mdtool._updateProperty('login_time', '2010/01/01')
            mdtool._updateProperty('last_login_time', '2010/01/01')
            mdtool._updateProperty('fullname', 'value3')
            mdtool.manage_addProperty('home_page', '', 'string')

        return site, mdtool


class exportMemberDataToolTests(_MemberDataToolSetup):

    layer = ExportImportZCMLLayer

    def test_unchanged(self):
        from ..memberdata import exportMemberDataTool

        site, _mdtool = self._initSite(use_changed=False)
        context = DummyExportContext(site)
        exportMemberDataTool(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'memberdata.xml')
        self._compareDOM(text.decode('utf8'), _DEFAULT_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_changed(self):
        from ..memberdata import exportMemberDataTool

        site, _mdtool = self._initSite(use_changed=True)
        context = DummyExportContext(site)
        exportMemberDataTool(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'memberdata.xml')
        self._compareDOM(text.decode('utf8'), _CHANGED_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class importMemberDataToolTests(_MemberDataToolSetup):

    layer = ExportImportZCMLLayer

    def test_normal(self):
        from ..memberdata import importMemberDataTool

        site, mdtool = self._initSite()

        context = DummyImportContext(site)
        context._files['memberdata.xml'] = _CHANGED_EXPORT
        importMemberDataTool(context)

        self.assertEqual(mdtool.email, 'value1')
        self.assertEqual(mdtool.portal_skin, 'value2')
        self.assertEqual(mdtool.listed, True)
        self.assertEqual(mdtool.login_time, DateTime('2010/01/01'))
        self.assertEqual(mdtool.last_login_time, DateTime('2010/01/01'))


def test_suite():
    loadTestsFromTestCase = unittest.defaultTestLoader.loadTestsFromTestCase
    return unittest.TestSuite((
        loadTestsFromTestCase(MemberDataToolXMLAdapterTests),
        loadTestsFromTestCase(exportMemberDataToolTests),
        loadTestsFromTestCase(importMemberDataToolTests),
    ))
