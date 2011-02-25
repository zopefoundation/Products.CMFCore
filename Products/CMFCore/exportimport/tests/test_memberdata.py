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
import Testing

from DateTime.DateTime import DateTime
from OFS.Folder import Folder

from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from Products.CMFCore.MemberDataTool import MemberDataTool
from Products.CMFCore.testing import ExportImportZCMLLayer

_MEMBERDATATOOL_BODY = """\
<?xml version="1.0"?>
<object name="portal_memberdata" meta_type="CMF Member Data Tool">
 <property name="email" type="string"></property>
 <property name="portal_skin" type="string"></property>
 <property name="listed" type="boolean">False</property>
 <property name="login_time" type="date">1970/01/01 00:00:00 UTC</property>
 <property name="last_login_time"
    type="date">1970/01/01 00:00:00 UTC</property>
</object>
"""

_DEFAULT_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_memberdata" meta_type="CMF Member Data Tool">
 <property name="email" type="string"></property>
 <property name="portal_skin" type="string"></property>
 <property name="listed" type="boolean">False</property>
 <property name="login_time" type="date">1970/01/01 00:00:00 UTC</property>
 <property name="last_login_time"
    type="date">1970/01/01 00:00:00 UTC</property>
</object>
"""

_CHANGED_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_memberdata" meta_type="CMF Member Data Tool">
 <property name="email" type="string">value1</property>
 <property name="portal_skin" type="string">value2</property>
 <property name="listed" type="boolean">True</property>
 <property name="login_time" type="date">2010/01/01 00:00:00</property>
 <property name="last_login_time" type="date">2010/01/01 00:00:00</property>
 <property name="fullname" type="string"></property>
</object>
"""


class MemberDataToolXMLAdapterTests(BodyAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from Products.CMFCore.exportimport.memberdata \
                import MemberDataToolXMLAdapter

        return MemberDataToolXMLAdapter

    def setUp(self):
        self._obj = MemberDataTool()
        self._BODY = _MEMBERDATATOOL_BODY


class _MemberDataToolSetup(BaseRegistryTests):

    def _initSite(self, use_changed=False):
        self.root.site = Folder(id='site')
        site = self.root.site
        mdtool = site.portal_memberdata = MemberDataTool()

        if use_changed:
            mdtool._updateProperty('email', 'value1')
            mdtool._updateProperty('portal_skin', 'value2')
            mdtool._updateProperty('listed', 'True')
            mdtool._updateProperty('login_time', '2010/01/01')
            mdtool._updateProperty('last_login_time', '2010/01/01')
            mdtool.manage_addProperty('fullname', '', 'string')

        return site


class exportMemberDataToolTests(_MemberDataToolSetup):

    layer = ExportImportZCMLLayer

    def test_unchanged(self):
        from Products.CMFCore.exportimport.memberdata \
                import exportMemberDataTool

        site = self._initSite(use_changed=False)
        context = DummyExportContext(site)
        exportMemberDataTool(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'memberdata.xml')
        self._compareDOM(text, _DEFAULT_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_changed(self):
        from Products.CMFCore.exportimport.memberdata \
                import exportMemberDataTool

        site = self._initSite(use_changed=True)
        context = DummyExportContext(site)
        exportMemberDataTool(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'memberdata.xml')
        self._compareDOM(text, _CHANGED_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class importMemberDataToolTests(_MemberDataToolSetup):

    layer = ExportImportZCMLLayer

    def test_normal(self):
        from Products.CMFCore.exportimport.memberdata \
                import importMemberDataTool

        site = self._initSite()
        mdtool = site.portal_memberdata

        context = DummyImportContext(site)
        context._files['memberdata.xml'] = _CHANGED_EXPORT
        importMemberDataTool(context)

        self.assertEqual(mdtool.email, 'value1')
        self.assertEqual(mdtool.portal_skin, 'value2')
        self.assertEqual(mdtool.listed, True)
        self.assertEqual(mdtool.login_time, DateTime('2010/01/01'))
        self.assertEqual(mdtool.last_login_time, DateTime('2010/01/01'))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MemberDataToolXMLAdapterTests),
        unittest.makeSuite(exportMemberDataToolTests),
        unittest.makeSuite(importMemberDataToolTests),
        ))
