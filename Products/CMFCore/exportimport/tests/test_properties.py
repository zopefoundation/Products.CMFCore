# -*- coding: iso-8859-1 -*-
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
"""Site properties xml adapter and setup handler unit tests.
"""

import unittest
import Testing

from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from Products.CMFCore.testing import ExportImportZCMLLayer

_PROPERTIES_BODY = u"""\
<?xml version="1.0"?>
<site>
 <property name="title">Foo</property>
 <property name="default_charset" type="string">iso-8859-1</property>
 <property name="foo_string" type="string">foo</property>
 <property name="bar_string" type="string">B\xe4r</property>
 <property name="foo_boolean" type="boolean">False</property>
</site>
""".encode('utf-8')

_EMPTY_EXPORT = """\
<?xml version="1.0" ?>
<site>
 <property name="title"/>
</site>
"""

_NORMAL_EXPORT = """\
<?xml version="1.0" ?>
<site>
 <property name="title"/>
 <property name="foo" type="string">Foo</property>
 <property name="bar" type="tokens">
  <element value="Bar"/>
 </property>
 <property name="moo" type="tokens">
  <element value="Moo"/>
 </property>
</site>
"""


class PropertiesXMLAdapterTests(BodyAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from Products.CMFCore.exportimport.properties \
                import PropertiesXMLAdapter

        return PropertiesXMLAdapter

    def _populate(self, obj):
        obj._setPropValue('title', 'Foo')
        obj._setProperty('default_charset', 'iso-8859-1', 'string')
        obj._setProperty('foo_string', 'foo', 'string')
        obj._setProperty('bar_string', u'B\xe4r'.encode('iso-8859-1'),
                         'string')
        obj._setProperty('foo_boolean', False, 'boolean')

    def _verifyImport(self, obj):
        self.assertEqual(type(obj.title), str)
        self.assertEqual(obj.title, 'Foo')
        self.assertEqual(type(obj.foo_string), str)
        self.assertEqual(obj.foo_string, 'foo')
        self.assertEqual(type(obj.bar_string), str)
        self.assertEqual(obj.bar_string, u'B\xe4r'.encode('iso-8859-1'))
        self.assertEqual(type(obj.foo_boolean), bool)
        self.assertEqual(obj.foo_boolean, False)

    def setUp(self):
        from Products.CMFCore.PortalObject import PortalObjectBase

        self._obj = PortalObjectBase('foo_site')
        self._BODY = _PROPERTIES_BODY


class _SitePropertiesSetup(BaseRegistryTests):

    def _initSite(self, foo=2, bar=2):
        from Products.CMFCore.PortalObject import PortalObjectBase

        self.app.site = PortalObjectBase('foo_site')
        site = self.app.site

        if foo > 0:
            site._setProperty('foo', '', 'string')
        if foo > 1:
            site._updateProperty('foo', 'Foo')

        if bar > 0:
            site._setProperty('bar', (), 'tokens')
            site._setProperty('moo', (), 'tokens')
        if bar > 1:
            site._updateProperty('bar', ('Bar',))
            site.moo = ['Moo']

        return site


class exportSitePropertiesTests(_SitePropertiesSetup):

    layer = ExportImportZCMLLayer

    def test_empty(self):
        from Products.CMFCore.exportimport.properties \
                import exportSiteProperties

        site = self._initSite(0, 0)
        context = DummyExportContext(site)
        exportSiteProperties(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'properties.xml')
        self._compareDOM(text, _EMPTY_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_normal(self):
        from Products.CMFCore.exportimport.properties \
                import exportSiteProperties

        site = self._initSite()
        context = DummyExportContext(site)
        exportSiteProperties(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'properties.xml')
        self._compareDOM(text, _NORMAL_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class importSitePropertiesTests(_SitePropertiesSetup):

    layer = ExportImportZCMLLayer

    def test_empty_default_purge(self):
        from Products.CMFCore.exportimport.properties \
                import importSiteProperties

        site = self._initSite()

        self.assertEqual(len(site.propertyIds()), 4)
        self.assertTrue('foo' in site.propertyIds())
        self.assertEqual(site.getProperty('foo'), 'Foo')
        self.assertTrue('bar' in site.propertyIds())
        self.assertEqual(site.getProperty('bar'), ('Bar',))

        context = DummyImportContext(site)
        context._files['properties.xml'] = _EMPTY_EXPORT
        importSiteProperties(context)

        self.assertEqual(len(site.propertyIds()), 1)

    def test_empty_explicit_purge(self):
        from Products.CMFCore.exportimport.properties \
                import importSiteProperties

        site = self._initSite()

        self.assertEqual(len(site.propertyIds()), 4)
        self.assertTrue('foo' in site.propertyIds())
        self.assertEqual(site.getProperty('foo'), 'Foo')
        self.assertTrue('bar' in site.propertyIds())
        self.assertEqual(site.getProperty('bar'), ('Bar',))

        context = DummyImportContext(site, True)
        context._files['properties.xml'] = _EMPTY_EXPORT
        importSiteProperties(context)

        self.assertEqual(len(site.propertyIds()), 1)

    def test_empty_skip_purge(self):
        from Products.CMFCore.exportimport.properties \
                import importSiteProperties

        site = self._initSite()

        self.assertEqual(len(site.propertyIds()), 4)
        self.assertTrue('foo' in site.propertyIds())
        self.assertEqual(site.getProperty('foo'), 'Foo')
        self.assertTrue('bar' in site.propertyIds())
        self.assertEqual(site.getProperty('bar'), ('Bar',))

        context = DummyImportContext(site, False)
        context._files['properties.xml'] = _EMPTY_EXPORT
        importSiteProperties(context)

        self.assertEqual(len(site.propertyIds()), 4)
        self.assertTrue('foo' in site.propertyIds())
        self.assertEqual(site.getProperty('foo'), 'Foo')
        self.assertTrue('bar' in site.propertyIds())
        self.assertEqual(site.getProperty('bar'), ('Bar',))

    def test_normal(self):
        from Products.CMFCore.exportimport.properties \
                import importSiteProperties

        site = self._initSite(0, 0)

        self.assertEqual(len(site.propertyIds()), 1)

        context = DummyImportContext(site)
        context._files['properties.xml'] = _NORMAL_EXPORT
        importSiteProperties(context)

        self.assertEqual(len(site.propertyIds()), 4)
        self.assertTrue('foo' in site.propertyIds())
        self.assertEqual(site.getProperty('foo'), 'Foo')
        self.assertTrue('bar' in site.propertyIds())
        self.assertEqual(site.getProperty('bar'), ('Bar',))


class roundtripSitePropertiesTests(_SitePropertiesSetup):

    layer = ExportImportZCMLLayer

    def test_nonascii_no_default_charset(self):
        from Products.CMFCore.exportimport.properties \
                import exportSiteProperties
        from Products.CMFCore.exportimport.properties \
                import importSiteProperties

        NONASCII = u'B\xe4r'.encode('utf-8')
        site = self._initSite(foo=0, bar=0)
        site._updateProperty('title', NONASCII)

        self.assertEqual(site.title, NONASCII)

        # export the site properties
        context = DummyExportContext(site)
        exportSiteProperties(context)
        _filename, text, _content_type = context._wrote[0]

        # Clear the title property
        site._updateProperty('title', '')
        self.assertEqual(site.title, '')

        # Import from the previous export
        context = DummyImportContext(site)
        context._files['properties.xml'] = text
        importSiteProperties(context)

        self.assertEqual(site.title, NONASCII)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(PropertiesXMLAdapterTests),
        unittest.makeSuite(exportSitePropertiesTests),
        unittest.makeSuite(importSitePropertiesTests),
        unittest.makeSuite(roundtripSitePropertiesTests),
        ))
