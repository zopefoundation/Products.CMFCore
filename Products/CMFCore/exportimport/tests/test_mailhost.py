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
"""Mailhost setup handler unit tests. """

import unittest
import Testing

from OFS.Folder import Folder
from Products.MailHost.interfaces import IMailHost

from zope.component import getSiteManager

from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from Products.CMFCore.testing import ExportImportZCMLLayer

_DEFAULT_EXPORT = """\
<?xml version="1.0"?>
<object name="MailHost" meta_type="Mail Host" smtp_host="localhost"
   smtp_port="25" smtp_pwd=""
   smtp_queue="False" smtp_queue_directory="/tmp" smtp_uid=""/>
"""

_CHANGED_EXPORT = """\
<?xml version="1.0"?>
<object name="MailHost" meta_type="Mail Host" smtp_host="value2"
   smtp_port="1" smtp_pwd="value1"
   smtp_queue="False" smtp_queue_directory="/tmp" smtp_uid="value3"/>
"""


class _MailHostSetup(BaseRegistryTests):

    def _initSite(self, use_changed=False):
        from Products.MailHost.MailHost import MailHost

        self.root.site = Folder(id='site')
        site = self.root.site
        mh = site.MailHost = MailHost('MailHost')
        sm = getSiteManager()
        sm.registerUtility(site.MailHost, IMailHost)
 
        if use_changed:
           mh.smtp_port='1'
           mh.smtp_pwd="value1"
           mh.smtp_host="value2"
           mh.smtp_uid="value3"

        return site


class exportMailHostTests(_MailHostSetup):

    layer = ExportImportZCMLLayer

    def test_unchanged(self):
        from Products.CMFCore.exportimport.mailhost import exportMailHost

        site = self._initSite(use_changed=False)
        context = DummyExportContext(site)
        exportMailHost(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'mailhost.xml')
        self._compareDOM(text, _DEFAULT_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_changed(self):
        from Products.CMFCore.exportimport.mailhost import exportMailHost

        site = self._initSite(use_changed=True)
        context = DummyExportContext(site)
        exportMailHost(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'mailhost.xml')
        self._compareDOM(text, _CHANGED_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class importMailHostTests(_MailHostSetup):

    layer = ExportImportZCMLLayer

    def test_normal(self):
        from Products.CMFCore.exportimport.mailhost import importMailHost

        site = self._initSite()
        mh = site.MailHost

        context = DummyImportContext(site)
        context._files['mailhost.xml'] = _CHANGED_EXPORT
        importMailHost(context)

        self.assertEqual( mh.smtp_pwd, 'value1' )
        self.assertEqual( mh.smtp_host, 'value2' )
        self.assertEqual( mh.smtp_uid, 'value3' )
        self.assertEqual( mh.smtp_port, 1 )


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(exportMailHostTests),
        unittest.makeSuite(importMailHostTests),
        ))

if __name__ == '__main__':
    from Products.CMFCore.testing import run
    run(test_suite())
