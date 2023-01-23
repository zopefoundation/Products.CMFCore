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
"""Cookie crumbler xml adapter and setup handler unit tests.
"""

import unittest

from OFS.Folder import Folder
from zope.component import getSiteManager

from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from ...CookieCrumbler import CookieCrumbler
from ...interfaces import ICookieCrumbler
from ...testing import ExportImportZCMLLayer


_COOKIECRUMBLER_BODY = b"""\
<?xml version="1.0" encoding="utf-8"?>
<object name="cookie_authentication" meta_type="Cookie Crumbler">
 <property name="title"></property>
 <property name="auth_cookie">__ac</property>
 <property name="name_cookie">__ac_name</property>
 <property name="pw_cookie">__ac_password</property>
 <property name="persist_cookie">__ac_persistent</property>
 <property name="local_cookie_path">False</property>
 <property name="cache_header_value">private</property>
 <property name="log_username">True</property>
</object>
"""

_DEFAULT_EXPORT = """\
<?xml version="1.0"?>
<object name="cookie_authentication" meta_type="Cookie Crumbler">
 <property name="title"></property>
 <property name="auth_cookie">__ac</property>
 <property name="name_cookie">__ac_name</property>
 <property name="pw_cookie">__ac_password</property>
 <property name="persist_cookie">__ac_persistent</property>
 <property name="local_cookie_path">False</property>
 <property name="cache_header_value">private</property>
 <property name="log_username">True</property>
</object>
"""

_CHANGED_EXPORT = """\
<?xml version="1.0"?>
<object name="cookie_authentication" meta_type="Cookie Crumbler">
 <property name="title">I am a cookie</property>
 <property name="auth_cookie">value1</property>
 <property name="name_cookie">value3</property>
 <property name="pw_cookie">value5</property>
 <property name="persist_cookie">value4</property>
 <property name="local_cookie_path">True</property>
 <property name="cache_header_value">value2</property>
 <property name="log_username">False</property>
</object>
"""

_CMF22_IMPORT = """\
<?xml version="1.0"?>
<object name="foo_cookiecrumbler" meta_type="Cookie Crumbler">
 <property name="title"></property>
 <property name="auth_cookie">value1</property>
 <property name="name_cookie">value3</property>
 <property name="pw_cookie">value5</property>
 <property name="persist_cookie">value4</property>
 <property name="auto_login_page">value6</property>
 <property name="logout_page">value8</property>
 <property name="unauth_page">value7</property>
 <property name="local_cookie_path">True</property>
 <property name="cache_header_value">value2</property>
 <property name="log_username">False</property>
</object>
"""


class CookieCrumblerXMLAdapterTests(BodyAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..cookieauth import CookieCrumblerXMLAdapter

        return CookieCrumblerXMLAdapter

    def setUp(self):
        self._obj = CookieCrumbler()
        self._BODY = _COOKIECRUMBLER_BODY


class _CookieCrumblerSetup(BaseRegistryTests):

    def _initSite(self, use_changed=False):
        site = Folder(id='site').__of__(self.app)
        cc = CookieCrumbler()
        getSiteManager().registerUtility(cc, ICookieCrumbler)

        if use_changed:
            cc.title = 'I am a cookie'
            cc.auth_cookie = 'value1'
            cc.cache_header_value = 'value2'
            cc.name_cookie = 'value3'
            cc.log_username = 0
            cc.persist_cookie = 'value4'
            cc.pw_cookie = 'value5'
            cc.local_cookie_path = 1

        return site, cc


class exportCookieCrumblerTests(_CookieCrumblerSetup):

    layer = ExportImportZCMLLayer

    def test_unchanged(self):
        from ..cookieauth import exportCookieCrumbler

        site, _cc = self._initSite(use_changed=False)
        context = DummyExportContext(site)
        exportCookieCrumbler(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'cookieauth.xml')
        self._compareDOM(text.decode('utf8'), _DEFAULT_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_changed(self):
        from ..cookieauth import exportCookieCrumbler

        site, _cc = self._initSite(use_changed=True)
        context = DummyExportContext(site)
        exportCookieCrumbler(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'cookieauth.xml')
        self._compareDOM(text.decode('utf8'), _CHANGED_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class importCookieCrumblerTests(_CookieCrumblerSetup):

    layer = ExportImportZCMLLayer

    def test_normal(self):
        from ..cookieauth import importCookieCrumbler

        site, cc = self._initSite()

        context = DummyImportContext(site)
        context._files['cookieauth.xml'] = _CHANGED_EXPORT
        importCookieCrumbler(context)

        self.assertEqual(cc.title, 'I am a cookie')
        self.assertEqual(cc.auth_cookie, 'value1')
        self.assertEqual(cc.cache_header_value, 'value2')
        self.assertEqual(cc.name_cookie, 'value3')
        self.assertEqual(cc.log_username, 0)
        self.assertEqual(cc.persist_cookie, 'value4')
        self.assertEqual(cc.pw_cookie, 'value5')
        self.assertEqual(cc.local_cookie_path, 1)

    def test_migration(self):
        from ..cookieauth import importCookieCrumbler

        site, cc = self._initSite()

        context = DummyImportContext(site)
        context._files['cookieauth.xml'] = _CMF22_IMPORT
        importCookieCrumbler(context)

        self.assertEqual(cc.auth_cookie, 'value1')
        self.assertEqual(cc.cache_header_value, 'value2')
        self.assertEqual(cc.name_cookie, 'value3')
        self.assertEqual(cc.log_username, 0)
        self.assertEqual(cc.persist_cookie, 'value4')
        self.assertEqual(cc.pw_cookie, 'value5')
        self.assertEqual(cc.local_cookie_path, 1)


def test_suite():
    loadTestsFromTestCase = unittest.defaultTestLoader.loadTestsFromTestCase
    return unittest.TestSuite((
        loadTestsFromTestCase(CookieCrumblerXMLAdapterTests),
        loadTestsFromTestCase(exportCookieCrumblerTests),
        loadTestsFromTestCase(importCookieCrumblerTests),
    ))
