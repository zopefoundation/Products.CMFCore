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
"""Content type registry xml adapter and setup handler unit tests.
"""

import unittest

from OFS.Folder import Folder
from zope.component import getSiteManager

from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from ...interfaces import IContentTypeRegistry
from ...testing import ExportImportZCMLLayer


_TEST_PREDICATES = (
 ('plain_text', 'major_minor', ('text', 'plain,javascript'), 'File'),
 ('stylesheets', 'extension', ('css,xsl,xslt',), 'Text File'),
 ('images', 'mimetype_regex', ('image/.*',), 'Image'),
 ('logfiles', 'name_regex', ('error_log-.*',), 'Log File'),
)

_CTR_BODY = b"""\
<?xml version="1.0" encoding="utf-8"?>
<object name="content_type_registry" meta_type="Content Type Registry">
 <predicate name="foo_predicate" content_type_name="Foo Type"
    predicate_type="major_minor">
  <argument value="foo_major"/>
  <argument value="foo_minor"/>
 </predicate>
 <predicate name="bar_predicate" content_type_name="Bar Type"
    predicate_type="extension">
  <argument value="bar"/>
 </predicate>
 <predicate name="baz_predicate" content_type_name="Baz Type"
    predicate_type="mimetype_regex">
  <argument value="baz/.*"/>
 </predicate>
 <predicate name="foobar_predicate" content_type_name="Foobar Type"
    predicate_type="name_regex">
  <argument value="foobar-.*"/>
 </predicate>
</object>
"""

_FRAGMENT1_IMPORT = """\
<?xml version="1.0"?>
<object name="content_type_registry">
 <predicate name="plain_text" insert-after="*"/>
 <predicate name="logfiles" insert-before="*"/>
</object>
"""

_FRAGMENT2_IMPORT = """\
<?xml version="1.0"?>
<object name="content_type_registry">
 <predicate name="plain_text" insert-after="stylesheets"/>
 <predicate name="logfiles" insert-before="images"/>
</object>
"""


class ContentTypeRegistryXMLAdapterTests(BodyAdapterTestCase,
                                         unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..contenttyperegistry import ContentTypeRegistryXMLAdapter

        return ContentTypeRegistryXMLAdapter

    def _populate(self, obj):
        obj.addPredicate('foo_predicate', 'major_minor')
        obj.getPredicate('foo_predicate').edit('foo_major', 'foo_minor')
        obj.assignTypeName('foo_predicate', 'Foo Type')
        obj.addPredicate('bar_predicate', 'extension')
        obj.getPredicate('bar_predicate').edit('bar')
        obj.assignTypeName('bar_predicate', 'Bar Type')
        obj.addPredicate('baz_predicate', 'mimetype_regex')
        obj.getPredicate('baz_predicate').edit('baz/.*')
        obj.assignTypeName('baz_predicate', 'Baz Type')
        obj.addPredicate('foobar_predicate', 'name_regex')
        obj.getPredicate('foobar_predicate').edit('foobar-.*')
        obj.assignTypeName('foobar_predicate', 'Foobar Type')

    def setUp(self):
        from ...ContentTypeRegistry import ContentTypeRegistry

        self._obj = ContentTypeRegistry()
        self._BODY = _CTR_BODY


class _ContentTypeRegistrySetup(BaseRegistryTests):

    MAJOR_MINOR_ID = _TEST_PREDICATES[0][0]
    MAJOR = _TEST_PREDICATES[0][2][0]
    MINOR = _TEST_PREDICATES[0][2][1]
    MAJOR_MINOR_TYPENAME = _TEST_PREDICATES[0][3]
    EXTENSION_ID = _TEST_PREDICATES[1][0]
    EXTENSIONS = _TEST_PREDICATES[1][2][0]
    EXTENSION_TYPENAME = _TEST_PREDICATES[1][3]
    MIMETYPE_REGEX_ID = _TEST_PREDICATES[2][0]
    MIMETYPE_REGEX = _TEST_PREDICATES[2][2][0]
    MIMETYPE_REGEX_TYPENAME = _TEST_PREDICATES[2][3]
    NAME_REGEX_ID = _TEST_PREDICATES[3][0]
    NAME_REGEX = _TEST_PREDICATES[3][2][0]
    NAME_REGEX_TYPENAME = _TEST_PREDICATES[3][3]

    _EMPTY_EXPORT = """\
<?xml version="1.0" encoding="utf-8"?>
<object name="content_type_registry" meta_type="Content Type Registry"/>
"""

    _WITH_POLICY_EXPORT = f"""\
<?xml version="1.0"  encoding="utf-8"?>
<object name="content_type_registry" meta_type="Content Type Registry">
 <predicate name="{MAJOR_MINOR_ID}" content_type_name="{MAJOR_MINOR_TYPENAME}"
    predicate_type="major_minor">
  <argument value="{MAJOR}"/>
  <argument value="{MINOR}"/>
 </predicate>
 <predicate name="{EXTENSION_ID}" content_type_name="{EXTENSION_TYPENAME}"
    predicate_type="extension">
  <argument value="{EXTENSIONS}"/>
 </predicate>
 <predicate name="{MIMETYPE_REGEX_ID}" content_type_name="{MIMETYPE_REGEX_TYPENAME}"
    predicate_type="mimetype_regex">
  <argument value="{MIMETYPE_REGEX}"/>
 </predicate>
 <predicate name="{NAME_REGEX_ID}" content_type_name="{NAME_REGEX_TYPENAME}"
    predicate_type="name_regex">
  <argument value="{NAME_REGEX}"/>
 </predicate>
</object>
"""  # NOQA: E501 line too long

    def _initSite(self, mit_predikat=False):
        from ...ContentTypeRegistry import ContentTypeRegistry

        site = Folder(id='site').__of__(self.app)
        ctr = ContentTypeRegistry()
        getSiteManager().registerUtility(ctr, IContentTypeRegistry)

        if mit_predikat:
            for (predicate_id, predicate_type, edit_args,
                 content_type_name) in _TEST_PREDICATES:
                ctr.addPredicate(predicate_id, predicate_type)
                predicate = ctr.getPredicate(predicate_id)
                predicate.edit(*edit_args)
                ctr.assignTypeName(predicate_id, content_type_name)

        return site, ctr


class exportContentTypeRegistryTests(_ContentTypeRegistrySetup):

    layer = ExportImportZCMLLayer

    def test_empty(self):
        from ..contenttyperegistry import exportContentTypeRegistry

        site, _ctr = self._initSite(mit_predikat=False)
        context = DummyExportContext(site)
        exportContentTypeRegistry(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'contenttyperegistry.xml')
        self._compareDOM(text.decode('utf8'), self._EMPTY_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_with_policy(self):
        from ..contenttyperegistry import exportContentTypeRegistry

        site, _ctr = self._initSite(mit_predikat=True)
        context = DummyExportContext(site)
        exportContentTypeRegistry(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'contenttyperegistry.xml')
        self._compareDOM(text.decode('utf8'), self._WITH_POLICY_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class importContentTypeRegistryTests(_ContentTypeRegistrySetup):

    layer = ExportImportZCMLLayer

    _FRAGMENT1_IMPORT = _FRAGMENT1_IMPORT
    _FRAGMENT2_IMPORT = _FRAGMENT2_IMPORT

    def test_normal(self):
        from ..contenttyperegistry import importContentTypeRegistry

        site, ctr = self._initSite(mit_predikat=False)
        self.assertEqual(len(ctr.listPredicates()), 0)

        context = DummyImportContext(site)
        context._files['contenttyperegistry.xml'] = self._WITH_POLICY_EXPORT
        importContentTypeRegistry(context)

        self.assertEqual(len(ctr.listPredicates()), len(_TEST_PREDICATES))
        predicate_id, (predicate, content_type_name) = ctr.listPredicates()[0]
        self.assertEqual(predicate_id, self.MAJOR_MINOR_ID)
        self.assertEqual(predicate.PREDICATE_TYPE, 'major_minor')
        self.assertEqual(content_type_name, self.MAJOR_MINOR_TYPENAME)
        self.assertEqual(predicate.major, self.MAJOR.split(','))
        self.assertEqual(predicate.minor, self.MINOR.split(','))
        predicate_id, (predicate, content_type_name) = ctr.listPredicates()[1]
        self.assertEqual(predicate_id, self.EXTENSION_ID)
        self.assertEqual(predicate.PREDICATE_TYPE, 'extension')
        self.assertEqual(content_type_name, self.EXTENSION_TYPENAME)
        self.assertEqual(predicate.extensions, self.EXTENSIONS.split(','))
        predicate_id, (predicate, content_type_name) = ctr.listPredicates()[2]
        self.assertEqual(predicate_id, self.MIMETYPE_REGEX_ID)
        self.assertEqual(predicate.PREDICATE_TYPE, 'mimetype_regex')
        self.assertEqual(content_type_name, self.MIMETYPE_REGEX_TYPENAME)
        self.assertEqual(predicate.pattern.pattern, self.MIMETYPE_REGEX)
        predicate_id, (predicate, content_type_name) = ctr.listPredicates()[3]
        self.assertEqual(predicate_id, self.NAME_REGEX_ID)
        self.assertEqual(predicate.PREDICATE_TYPE, 'name_regex')
        self.assertEqual(content_type_name, self.NAME_REGEX_TYPENAME)
        self.assertEqual(predicate.pattern.pattern, self.NAME_REGEX)

    def test_fragment1_skip_purge(self):
        from ..contenttyperegistry import importContentTypeRegistry

        site, ctr = self._initSite(mit_predikat=True)
        self.assertEqual(len(ctr.listPredicates()), len(_TEST_PREDICATES))
        self.assertEqual(ctr.predicate_ids, ('plain_text', 'stylesheets',
                                             'images', 'logfiles'))

        context = DummyImportContext(site, False)
        context._files['contenttyperegistry.xml'] = self._FRAGMENT1_IMPORT
        importContentTypeRegistry(context)

        self.assertEqual(len(ctr.listPredicates()), len(_TEST_PREDICATES))
        self.assertEqual(ctr.predicate_ids, ('logfiles', 'stylesheets',
                                             'images', 'plain_text'))

    def test_fragment2_skip_purge(self):
        from ..contenttyperegistry import importContentTypeRegistry

        site, ctr = self._initSite(mit_predikat=True)
        self.assertEqual(len(ctr.listPredicates()), len(_TEST_PREDICATES))
        self.assertEqual(ctr.predicate_ids, ('plain_text', 'stylesheets',
                                             'images', 'logfiles'))

        context = DummyImportContext(site, False)
        context._files['contenttyperegistry.xml'] = self._FRAGMENT2_IMPORT
        importContentTypeRegistry(context)

        self.assertEqual(len(ctr.listPredicates()), len(_TEST_PREDICATES))
        self.assertEqual(ctr.predicate_ids, ('stylesheets', 'plain_text',
                                             'logfiles', 'images'))


def test_suite():
    loadTestsFromTestCase = unittest.defaultTestLoader.loadTestsFromTestCase
    return unittest.TestSuite((
        loadTestsFromTestCase(ContentTypeRegistryXMLAdapterTests),
        loadTestsFromTestCase(exportContentTypeRegistryTests),
        loadTestsFromTestCase(importContentTypeRegistryTests),
    ))
