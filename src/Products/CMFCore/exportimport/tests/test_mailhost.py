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
"""Mailhost setup handler unit tests.
"""

import unittest

from OFS.Folder import Folder
from Zope2.App import zcml
from zope.component import getSiteManager

from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext
from Products.MailHost.interfaces import IMailHost

from ...testing import ExportImportZCMLLayer


_DEFAULT_EXPORT = """\
<?xml version="1.0"?>
<object name="MailHost" meta_type="Mail Host" smtp_host="localhost"
   smtp_port="25" smtp_pwd="" smtp_queue="False" smtp_queue_directory="/tmp"
   smtp_uid=""/>
"""

_CHANGED_EXPORT = """\
<?xml version="1.0"?>
<object name="MailHost" meta_type="Mail Host" smtp_host="value2"
   smtp_port="1" smtp_pwd="value1" smtp_queue="False"
   smtp_queue_directory="/tmp" smtp_uid="value3"/>
"""

_ZOPE211_EXPORT = """\
<?xml version="1.0"?>
<object name="MailHost" meta_type="Mail Host" smtp_host="value2"
   smtp_port="1" smtp_pwd="value1" smtp_uid="value3"/>
"""


class _MailHostSetup(BaseRegistryTests):

    def _initSite(self, use_changed=False):
        import Products.MailHost
        from Products.MailHost.MailHost import MailHost

        zcml.load_config('exportimport.zcml', Products.MailHost)

        site = Folder(id='site').__of__(self.app)
        mh = MailHost('MailHost')
        getSiteManager().registerUtility(mh, IMailHost)

        if use_changed:
            mh.smtp_port = '1'
            mh.smtp_pwd = 'value1'
            mh.smtp_host = 'value2'
            mh.smtp_uid = 'value3'

        return site, mh


class exportMailHostTests(_MailHostSetup):

    layer = ExportImportZCMLLayer

    def test_unchanged(self):
        from ..mailhost import exportMailHost

        site, _mh = self._initSite(use_changed=False)
        context = DummyExportContext(site)
        exportMailHost(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'mailhost.xml')
        self._compareDOM(text.decode('utf8'), _DEFAULT_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_changed(self):
        from ..mailhost import exportMailHost

        site, _mh = self._initSite(use_changed=True)
        context = DummyExportContext(site)
        exportMailHost(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'mailhost.xml')
        self._compareDOM(text.decode('utf8'), _CHANGED_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class importMailHostTests(_MailHostSetup):

    layer = ExportImportZCMLLayer

    def test_normal(self):
        from ..mailhost import importMailHost

        site, mh = self._initSite()
        context = DummyImportContext(site)
        context._files['mailhost.xml'] = _CHANGED_EXPORT
        importMailHost(context)

        self.assertEqual(mh.smtp_pwd, 'value1')
        self.assertEqual(mh.smtp_host, 'value2')
        self.assertEqual(mh.smtp_uid, 'value3')
        self.assertEqual(mh.smtp_port, 1)
        self.assertEqual(mh.smtp_queue, False)
        self.assertEqual(mh.smtp_queue_directory, '/tmp')

    def test_migration(self):
        from ..mailhost import importMailHost

        site, mh = self._initSite()
        context = DummyImportContext(site)
        context._files['mailhost.xml'] = _ZOPE211_EXPORT
        importMailHost(context)

        self.assertEqual(mh.smtp_pwd, 'value1')
        self.assertEqual(mh.smtp_host, 'value2')
        self.assertEqual(mh.smtp_uid, 'value3')
        self.assertEqual(mh.smtp_port, 1)
        self.assertEqual(mh.smtp_queue, False)
        self.assertEqual(mh.smtp_queue_directory, '/tmp')


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(exportMailHostTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(importMailHostTests),
        ))
