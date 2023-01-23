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
"""Filesystem exporter / importer adapter unit tests.
"""

import unittest
from configparser import ConfigParser
from csv import reader
from io import StringIO

from zope.component import getSiteManager
from zope.testing.cleanup import cleanUp

from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from ...interfaces import ITypesTool
from ...testing import DummyWorkflow
from .test_workflow import DummyWorkflowTool


def safe_bytes(value, encoding='utf8'):
    if isinstance(value, bytes):
        return value
    return value.encode(encoding)


class SiteStructureExporterTests(unittest.TestCase):

    def _getExporter(self):
        from ..content import exportSiteStructure
        return exportSiteStructure

    def _getImporter(self):
        from ..content import importSiteStructure
        return importSiteStructure

    def _makeSetupTool(self):
        from Products.GenericSetup.tool import SetupTool
        return SetupTool('portal_setup')

    def _makeWorkflowTool(self):
        obj = DummyWorkflowTool()
        return obj

    def _setUpAdapters(self):
        from zope.component import provideAdapter

        from Products.GenericSetup.content import CSVAwareFileAdapter
        from Products.GenericSetup.content import INIAwareFileAdapter
        from Products.GenericSetup.interfaces import ICSVAware
        from Products.GenericSetup.interfaces import IFilesystemExporter
        from Products.GenericSetup.interfaces import IFilesystemImporter
        from Products.GenericSetup.interfaces import IINIAware

        from ...interfaces import IFolderish
        from ..content import StructureFolderWalkingAdapter

        provideAdapter(StructureFolderWalkingAdapter,
                       (IFolderish,),
                       IFilesystemExporter)

        provideAdapter(StructureFolderWalkingAdapter,
                       (IFolderish,),
                       IFilesystemImporter)

        provideAdapter(CSVAwareFileAdapter,
                       (ICSVAware,),
                       IFilesystemExporter)

        provideAdapter(CSVAwareFileAdapter,
                       (ICSVAware,),
                       IFilesystemImporter)

        provideAdapter(INIAwareFileAdapter,
                       (IINIAware,),
                       IFilesystemExporter)

        provideAdapter(INIAwareFileAdapter,
                       (IINIAware,),
                       IFilesystemImporter)

    def _get_config_parser(self, text):
        parser = ConfigParser()
        parser.read_file(StringIO(text))
        return parser

    def tearDown(self):
        cleanUp()

    def test_export_empty_site(self):
        self._setUpAdapters()
        site = _makeFolder('site', site_folder=True)
        site.title = 'test_export_empty_site'
        site.description = 'Testing export of an empty site.'
        context = DummyExportContext(site)
        exporter = self._getExporter()
        exporter(context)

        self.assertEqual(len(context._wrote), 2)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'structure/.objects')
        self.assertEqual(content_type, 'text/comma-separated-values')

        objects = [x for x in reader(StringIO(text))]
        self.assertEqual(len(objects), 0)

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'structure/.properties')
        self.assertEqual(content_type, 'text/plain')

        parser = self._get_config_parser(text)

        self.assertEqual(parser.get('DEFAULT', 'Title'),
                         site.title)
        self.assertEqual(parser.get('DEFAULT', 'Description'),
                         site.description)

    def test_export_empty_site_with_setup_tool(self):
        self._setUpAdapters()
        site = _makeFolder('site', site_folder=True)
        site._setObject('setup_tool', self._makeSetupTool())
        site.title = 'test_export_empty_site_with_setup_tool'
        site.description = 'Testing export of an empty site with setup tool.'
        context = DummyExportContext(site)
        exporter = self._getExporter()
        exporter(context)

        self.assertEqual(len(context._wrote), 2)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'structure/.objects')
        self.assertEqual(content_type, 'text/comma-separated-values')

        objects = [x for x in reader(StringIO(text))]
        self.assertEqual(len(objects), 0)

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'structure/.properties')
        self.assertEqual(content_type, 'text/plain')

        parser = self._get_config_parser(text)

        self.assertEqual(parser.get('DEFAULT', 'Title'),
                         site.title)
        self.assertEqual(parser.get('DEFAULT', 'Description'),
                         site.description)

    def test_export_site_with_non_exportable_simple_items(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)
        site.title = 'AAA'
        site.description = 'DESCRIPTION'
        for id in ITEM_IDS:
            site._setObject(id, _makeItem(id))

        context = DummyExportContext(site)
        exporter = self._getExporter()
        exporter(context)

        self.assertEqual(len(context._wrote), 2)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'structure/.objects')
        self.assertEqual(content_type, 'text/comma-separated-values')

        objects = [x for x in reader(StringIO(text))]
        self.assertEqual(len(objects), 3)
        for index in range(len(ITEM_IDS)):
            self.assertEqual(objects[index][0], ITEM_IDS[index])
            self.assertEqual(objects[index][1], TEST_CONTENT)

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'structure/.properties')
        self.assertEqual(content_type, 'text/plain')
        parser = self._get_config_parser(text)

        self.assertEqual(parser.get('DEFAULT', 'title'), 'AAA')
        self.assertEqual(parser.get('DEFAULT', 'description'), 'DESCRIPTION')

    def test_export_site_with_exportable_simple_items_encoded_string(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)
        site.title = 'AAA'
        site.description = 'DESCRIPTION'
        ITEMS_TITLE = 'Actualit\xe9'
        ITEMS_DESCRIPTION = 'Actualit\xe9 r\xe9centes'
        for id in ITEM_IDS:
            site._setObject(id, _makeINIAware(id))
            item = getattr(site, id)
            item.setTitle(ITEMS_TITLE.encode('utf8'))
            item.setDescription(ITEMS_DESCRIPTION.encode('utf8'))

        context = DummyExportContext(site)
        exporter = self._getExporter()
        exporter(context)

        self.assertEqual(len(context._wrote), 2 + len(ITEM_IDS))
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'structure/.objects')
        self.assertEqual(content_type, 'text/comma-separated-values')

        objects = [x for x in reader(StringIO(text))]
        self.assertEqual(len(objects), 3)
        for index in range(len(ITEM_IDS)):
            self.assertEqual(objects[index][0], ITEM_IDS[index])
            self.assertEqual(objects[index][1], TEST_INI_AWARE)

            filename, text, content_type = context._wrote[index + 2]
            self.assertEqual(filename, 'structure/%s.ini' % ITEM_IDS[index])
            object = site._getOb(ITEM_IDS[index])
            self.assertEqual(text.strip(),
                             object.as_ini().strip())
            self.assertEqual(content_type, 'text/plain')

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'structure/.properties')
        self.assertEqual(content_type, 'text/plain')
        parser = self._get_config_parser(text)

        self.assertEqual(safe_bytes(parser.get('DEFAULT', 'title')),
                         ITEMS_TITLE.encode('utf8'))
        self.assertEqual(safe_bytes(parser.get('DEFAULT', 'description')),
                         ITEMS_DESCRIPTION.encode('utf8'))

    def test_export_site_with_exportable_simple_items(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)
        site.title = 'AAA'
        site.description = 'DESCRIPTION'
        for id in ITEM_IDS:
            site._setObject(id, _makeINIAware(id))

        context = DummyExportContext(site)
        exporter = self._getExporter()
        exporter(context)

        self.assertEqual(len(context._wrote), 2 + len(ITEM_IDS))
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'structure/.objects')
        self.assertEqual(content_type, 'text/comma-separated-values')

        objects = [x for x in reader(StringIO(text))]
        self.assertEqual(len(objects), 3)
        for index in range(len(ITEM_IDS)):
            self.assertEqual(objects[index][0], ITEM_IDS[index])
            self.assertEqual(objects[index][1], TEST_INI_AWARE)

            filename, text, content_type = context._wrote[index + 2]
            self.assertEqual(filename, 'structure/%s.ini' % ITEM_IDS[index])
            object = site._getOb(ITEM_IDS[index])
            self.assertEqual(text.strip(),
                             object.as_ini().strip())
            self.assertEqual(content_type, 'text/plain')

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'structure/.properties')
        self.assertEqual(content_type, 'text/plain')
        parser = self._get_config_parser(text)

        self.assertEqual(parser.get('DEFAULT', 'title'), 'AAA')
        self.assertEqual(parser.get('DEFAULT', 'description'), 'DESCRIPTION')

    def test_export_site_includes_workflow(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)

        site._setObject('portal_workflow', self._makeWorkflowTool())
        wftool = site.portal_workflow
        wftool._setObject('foo_workflow', DummyWorkflow('foo_workflow'))
        wftool.foo_workflow.state_var = 'state'
        wftool.setDefaultChain('foo_workflow')
        wftool.setChainForPortalTypes((TEST_INI_AWARE,),
                                      'foo_workflow', verify=False)

        site.title = 'AAA'
        site.description = 'DESCRIPTION'
        for id in ITEM_IDS:
            site._setObject(id, _makeINIAware(id))
            wftool.setStatusOf('foo_workflow', site[id],
                               {'state': 'published'})

        context = DummyExportContext(site)
        exporter = self._getExporter()
        exporter(context)

        self.assertEqual(len(context._wrote), 3 + len(ITEM_IDS))
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'structure/.workflow_states')
        self.assertEqual(content_type, 'text/comma-separated-values')

        objects = [x for x in reader(StringIO(text))]
        self.assertEqual(len(objects), 3)
        for index in range(len(ITEM_IDS)):
            self.assertEqual(objects[index][0], ITEM_IDS[index])
            self.assertEqual(objects[index][1], 'foo_workflow')
            self.assertEqual(objects[index][2], 'published')

    def test_export_site_exportable_simple_items_unicode_default_charset(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)
        site.title = 'AAA'
        site.description = 'DESCRIPTION'
        ITEMS_TITLE = 'Actualit\xe9'
        ITEMS_DESCRIPTION = 'Actualit\xe9 r\xe9centes'
        for id in ITEM_IDS:
            site._setObject(id, _makeINIAware(id))
            item = getattr(site, id)
            item.setTitle(ITEMS_TITLE)
            item.setDescription(ITEMS_DESCRIPTION)

        context = DummyExportContext(site)
        exporter = self._getExporter()
        exporter(context)

        self.assertEqual(len(context._wrote), 2 + len(ITEM_IDS))
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'structure/.objects')
        self.assertEqual(content_type, 'text/comma-separated-values')

        objects = [x for x in reader(StringIO(text))]
        self.assertEqual(len(objects), 3)
        for index in range(len(ITEM_IDS)):
            self.assertEqual(objects[index][0], ITEM_IDS[index])
            self.assertEqual(objects[index][1], TEST_INI_AWARE)

            filename, text, content_type = context._wrote[index + 2]
            self.assertEqual(filename, 'structure/%s.ini' % ITEM_IDS[index])
            object = site._getOb(ITEM_IDS[index])
            self.assertEqual(text.strip(),
                             object.as_ini().strip())
            self.assertEqual(content_type, 'text/plain')

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'structure/.properties')
        self.assertEqual(content_type, 'text/plain')
        parser = self._get_config_parser(text)

        self.assertEqual(safe_bytes(parser.get('DEFAULT', 'title')),
                         ITEMS_TITLE.encode('utf8'))
        self.assertEqual(safe_bytes(parser.get('DEFAULT', 'description')),
                         ITEMS_DESCRIPTION.encode('utf8'))

    def test_export_site_with_exportable_simple_items_unicode_latin1(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)
        site._setProperty('default_charset', 'iso-8859-1', 'string')
        site.title = 'AAA'
        site.description = 'DESCRIPTION'
        ITEMS_TITLE = 'Actualit\xe9'
        ITEMS_DESCRIPTION = 'Actualit\xe9 r\xe9centes'
        for id in ITEM_IDS:
            site._setObject(id, _makeINIAware(id))
            item = getattr(site, id)
            item.setTitle(ITEMS_TITLE)
            item.setDescription(ITEMS_DESCRIPTION)

        context = DummyExportContext(site)
        exporter = self._getExporter()
        exporter(context)

        self.assertEqual(len(context._wrote), 2 + len(ITEM_IDS))
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'structure/.objects')
        self.assertEqual(content_type, 'text/comma-separated-values')

        objects = [x for x in reader(StringIO(text))]
        self.assertEqual(len(objects), 3)
        for index in range(len(ITEM_IDS)):
            self.assertEqual(objects[index][0], ITEM_IDS[index])
            self.assertEqual(objects[index][1], TEST_INI_AWARE)

            filename, text, content_type = context._wrote[index + 2]
            self.assertEqual(filename, 'structure/%s.ini' % ITEM_IDS[index])
            object = site._getOb(ITEM_IDS[index])
            self.assertEqual(text.strip(),
                             object.as_ini().strip())
            self.assertEqual(content_type, 'text/plain')

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'structure/.properties')
        self.assertEqual(content_type, 'text/plain')
        parser = self._get_config_parser(text)

        self.assertEqual(safe_bytes(parser.get('DEFAULT', 'title'), 'latin1'),
                         ITEMS_TITLE.encode('latin1'))
        self.assertEqual(safe_bytes(parser.get('DEFAULT', 'description'),
                                    'latin1'),
                         ITEMS_DESCRIPTION.encode('latin1'))

    def test_export_site_with_subfolders(self):
        self._setUpAdapters()
        FOLDER_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)
        site.title = 'AAA'
        site.description = 'DESCRIPTION'
        for id in FOLDER_IDS:
            folder = _makeFolder(id)
            folder.title = 'Title: %s' % id
            folder.description = 'xyzzy'
            site._setObject(id, folder)

        context = DummyExportContext(site)
        exporter = self._getExporter()
        exporter(context)

        self.assertEqual(len(context._wrote), 2 + (2 * len(FOLDER_IDS)))
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'structure/.objects')
        self.assertEqual(content_type, 'text/comma-separated-values')

        objects = [x for x in reader(StringIO(text))]
        self.assertEqual(len(objects), 3)

        for index in range(len(FOLDER_IDS)):
            id = FOLDER_IDS[index]
            self.assertEqual(objects[index][0], id)
            self.assertEqual(objects[index][1], TEST_FOLDER)

            filename, text, content_type = context._wrote[2 + (2 * index)]
            self.assertEqual(filename, '/'.join(('structure', id, '.objects')))
            self.assertEqual(content_type, 'text/comma-separated-values')
            subobjects = [x for x in reader(StringIO(text))]
            self.assertEqual(len(subobjects), 0)

            filename, text, content_type = context._wrote[2 + (2 * index) + 1]
            self.assertEqual(filename,
                             '/'.join(('structure', id, '.properties')))
            self.assertEqual(content_type, 'text/plain')
            parser = self._get_config_parser(text)

            self.assertEqual(parser.get('DEFAULT', 'Title'), 'Title: %s' % id)

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'structure/.properties')
        self.assertEqual(content_type, 'text/plain')

        parser = self._get_config_parser(text)

        self.assertEqual(parser.get('DEFAULT', 'title'), 'AAA')
        self.assertEqual(parser.get('DEFAULT', 'description'), 'DESCRIPTION')

    def test_export_site_with_dav_aware_folder(self):
        self._setUpAdapters()

        site = _makeFolder('site', site_folder=True)
        site.title = 'AAA'
        site.description = 'DESCRIPTION'

        folder = _makeDAVAwareFolder('foo')
        folder.title = 'foo'
        folder.description = 'xyzzy'
        folder.body = 'A content item'
        site._setObject('foo', folder)

        context = DummyExportContext(site)
        exporter = self._getExporter()
        exporter(context)

        filename, text, content_type = context._wrote[-1]
        self.assertEqual(filename, 'structure/foo/.properties')
        self.assertEqual(content_type, 'text/plain')
        self.assertEqual(text,
                         KNOWN_DAV % (folder.title, folder.description,
                                      folder.body))

    def test_export_site_with_csvaware(self):
        self._setUpAdapters()

        site = _makeFolder('site', site_folder=True)
        site.title = 'test_export_site_with_csvaware'
        site.description = 'Testing export of an site with CSV-aware content.'

        site._setObject('aware', _makeCSVAware('aware'))

        context = DummyExportContext(site)
        exporter = self._getExporter()
        exporter(context)

        self.assertEqual(len(context._wrote), 3)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'structure/.objects')
        self.assertEqual(content_type, 'text/comma-separated-values')

        objects = [x for x in reader(StringIO(text))]
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0][0], 'aware')
        self.assertEqual(objects[0][1], TEST_CSV_AWARE)

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'structure/.properties')
        self.assertEqual(content_type, 'text/plain')

        parser = self._get_config_parser(text)

        self.assertEqual(parser.get('DEFAULT', 'Title'), site.title)
        self.assertEqual(parser.get('DEFAULT', 'Description'),
                         site.description)

        filename, text, content_type = context._wrote[2]
        self.assertEqual(filename, 'structure/aware.csv')
        self.assertEqual(content_type, 'text/comma-separated-values')
        rows = [x for x in reader(StringIO(text))]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], 'one')
        self.assertEqual(rows[0][1], 'two')
        self.assertEqual(rows[0][2], 'three')
        self.assertEqual(rows[1][0], 'four')
        self.assertEqual(rows[1][1], 'five')
        self.assertEqual(rows[1][2], 'six')

    def test_import_empty_site(self):
        self._setUpAdapters()
        site = _makeFolder('site', site_folder=True)
        context = DummyImportContext(site)
        context._files['structure/.objects'] = ''
        importer = self._getImporter()
        self.assertEqual(len(site.objectIds()), 0)
        importer(context)
        self.assertEqual(len(site.objectIds()), 0)

    def test_import_empty_site_with_setup_tool(self):
        self._setUpAdapters()
        site = _makeFolder('site', site_folder=True)
        site._setObject('setup_tool', self._makeSetupTool())
        context = DummyImportContext(site)
        importer = self._getImporter()

        self.assertEqual(len(site.objectIds()), 1)
        self.assertEqual(site.objectIds()[0], 'setup_tool')
        importer(context)
        self.assertEqual(len(site.objectIds()), 1)
        self.assertEqual(site.objectIds()[0], 'setup_tool')

    def test_import_site_with_subfolders(self):
        from Products.GenericSetup.tests.test_content import \
            _PROPERTIES_TEMPLATE
        self._setUpAdapters()
        FOLDER_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)

        context = DummyImportContext(site)

        for id in FOLDER_IDS:
            context._files['structure/%s/.objects' % id] = ''
            context._files['structure/%s/.properties' % id] = (
                _PROPERTIES_TEMPLATE % id)

        _ROOT_OBJECTS = '\n'.join([f'{id},{TEST_FOLDER}' for id in FOLDER_IDS])

        context._files['structure/.objects'] = _ROOT_OBJECTS
        context._files['structure/.properties'] = (
                _PROPERTIES_TEMPLATE % 'Test Site')

        importer = self._getImporter()
        importer(context)

        content = site.contentValues()
        self.assertEqual(len(content), len(FOLDER_IDS))

    def test_import_site_with_dav_aware_folder(self):
        from Products.GenericSetup.tests.test_content import \
            _PROPERTIES_TEMPLATE
        self._setUpAdapters()
        FOLDER_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)

        context = DummyImportContext(site)

        for id in FOLDER_IDS:
            context._files['structure/%s/.objects' % id] = ''
            context._files['structure/%s/.properties' % id] = (
                KNOWN_DAV % ('Title', 'Description', 'Body'))

        _ROOT_OBJECTS = '\n'.join([f'{id},{TEST_DAV_FOLDER}'
                                  for id in FOLDER_IDS])

        context._files['structure/.objects'] = _ROOT_OBJECTS
        context._files['structure/.properties'] = (
                _PROPERTIES_TEMPLATE % 'Test Site')

        importer = self._getImporter()
        importer(context)
        content = site.contentValues()
        self.assertEqual(len(content), len(FOLDER_IDS))
        self.assertEqual(
            content[0]._was_put_as_read,
            (KNOWN_DAV % ('Title', 'Description', 'Body')).encode('UTF-8'))

    def test_import_site_with_dav_aware_folder_with_generic_file_data(self):
        from Products.GenericSetup.tests.test_content import \
            _PROPERTIES_TEMPLATE
        self._setUpAdapters()
        FOLDER_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)

        context = DummyImportContext(site)

        for id in FOLDER_IDS:
            context._files['structure/%s/.objects' % id] = ''
            context._files['structure/%s/.properties' % id] = (
                _PROPERTIES_TEMPLATE % ('Sub Folder Title',))

        _ROOT_OBJECTS = '\n'.join([f'{id},{TEST_DAV_FOLDER}'
                                   for id in FOLDER_IDS])

        context._files['structure/.objects'] = _ROOT_OBJECTS
        context._files['structure/.properties'] = (
                _PROPERTIES_TEMPLATE % 'Test Site')

        importer = self._getImporter()
        importer(context)
        content = site.contentValues()
        self.assertEqual(len(content), len(FOLDER_IDS))
        self.assertEqual(content[0].title, 'Sub Folder Title')

    def test_import_site_with_subitems(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)

        context = DummyImportContext(site)
        # We want to add 'baz' to 'foo', without losing 'bar'
        context._files['structure/.objects'] = '\n'.join(
            [f'{x},{TEST_INI_AWARE}' for x in ITEM_IDS])
        for index in range(len(ITEM_IDS)):
            id = ITEM_IDS[index]
            context._files[
                    'structure/%s.ini' % id] = KNOWN_INI % ('Title: %s' % id,
                                                            'xyzzy')
        importer = self._getImporter()
        importer(context)

        after = site.objectIds()
        self.assertEqual(len(after), len(ITEM_IDS))
        for found_id, expected_id in zip(after, ITEM_IDS):
            self.assertEqual(found_id, expected_id)

    def test_import_site_includes_workflow(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)

        site._setObject('portal_workflow', self._makeWorkflowTool())
        wftool = site.portal_workflow
        wftool._setObject('foo_workflow', DummyWorkflow('foo_workflow'))
        wftool.foo_workflow.state_var = 'state'
        wftool.setDefaultChain('foo_workflow')
        wftool.setChainForPortalTypes((TEST_INI_AWARE,),
                                      'foo_workflow', verify=False)

        context = DummyImportContext(site)
        context._files['structure/.objects'] = '\n'.join(
            [f'{x},{TEST_INI_AWARE}' for x in ITEM_IDS])
        context._files['structure/.workflow_states'] = '\n'.join(
            ['%s,foo_workflow,draft' % (x) for x in ITEM_IDS])
        for index in range(len(ITEM_IDS)):
            id = ITEM_IDS[index]
            context._files[
                    'structure/%s.ini' % id] = KNOWN_INI % ('Title: %s' % id,
                                                            'xyzzy')
        importer = self._getImporter()
        importer(context)

        for item_id in ITEM_IDS:
            wf = wftool.getStatusOf('foo_workflow', site[item_id])
            self.assertEqual(wf['state'], 'draft')

    def test_import_site_with_subitems_and_blanklines_dotobjects(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)

        context = DummyImportContext(site)
        # We want to add 'baz' to 'foo', without losing 'bar'
        correct = '\n'.join([f'{x},{TEST_INI_AWARE}' for x in ITEM_IDS])
        broken = correct + '\n\n'
        context._files['structure/.objects'] = broken
        for index in range(len(ITEM_IDS)):
            id = ITEM_IDS[index]
            context._files[
                    'structure/%s.ini' % id] = KNOWN_INI % ('Title: %s' % id,
                                                            'xyzzy')
        importer = self._getImporter()
        importer(context)

        after = site.objectIds()
        self.assertEqual(len(after), len(ITEM_IDS))
        for found_id, expected_id in zip(after, ITEM_IDS):
            self.assertEqual(found_id, expected_id)

    def test_import_site_with_subitem_unknown_portal_type(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)

        context = DummyImportContext(site)
        # We want to add 'baz' to 'foo', without losing 'bar'
        context._files['structure/.objects'] = '\n'.join(
                                ['%s,Unknown Type' % x for x in ITEM_IDS])
        for index in range(len(ITEM_IDS)):
            id = ITEM_IDS[index]
            context._files[
                    'structure/%s.ini' % id] = KNOWN_INI % ('Title: %s' % id,
                                                            'xyzzy')

        importer = self._getImporter()
        importer(context)

        after = site.objectIds()
        self.assertEqual(len(after), 0)
        self.assertEqual(len(context._notes), len(ITEM_IDS))
        for _level, component, message in context._notes:
            self.assertEqual(component, 'SFWA')
            self.assertTrue(message.startswith("Couldn't make"))

    def test_reimport_no_structure_no_delete(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)
        for id in ITEM_IDS:
            site._setObject(id, _makeItem(id))

        context = DummyImportContext(site)
        # no defined structure => no deletion
        context._files['structure/.objects'] = ''

        importer = self._getImporter()
        importer(context)

        self.assertEqual(len(site.objectIds()), len(ITEM_IDS))

    def test_reimport_with_structure_does_delete(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)
        for id in ITEM_IDS:
            site._setObject(id, _makeItem(id))
            site._getOb(id).before = True

        context = DummyImportContext(site)
        # defined structure => object deleted and recreated
        context._files['structure/.objects'] = '\n'.join(
            [f'{x},{TEST_INI_AWARE}' for x in ITEM_IDS])
        for index in range(len(ITEM_IDS)):
            id = ITEM_IDS[index]
            context._files[
                    'structure/%s.ini' % id] = KNOWN_INI % ('Title: %s' % id,
                                                            'xyzzy')

        importer = self._getImporter()
        importer(context)

        self.assertEqual(len(site.objectIds()), len(ITEM_IDS))
        for obj in site.objectValues():
            self.assertFalse(hasattr(obj, 'before'))

    def test_reimport_with_structure_and_preserve(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)
        for id in ITEM_IDS:
            site._setObject(id, _makeINIAware(id))
            site._getOb(id).before = True

        context = DummyImportContext(site)
        context._files['structure/.objects'] = '\n'.join(
            [f'{x},{TEST_INI_AWARE}' for x in ITEM_IDS])
        for index in range(len(ITEM_IDS)):
            id = ITEM_IDS[index]
            context._files[
                    'structure/%s.ini' % id] = KNOWN_INI % ('Title: %s' % id,
                                                            'xyzzy')
        context._files['structure/.preserve'] = '*'

        importer = self._getImporter()
        importer(context)

        after = site.objectIds()
        self.assertEqual(len(after), len(ITEM_IDS))
        for i in range(len(ITEM_IDS)):
            self.assertEqual(after[i], ITEM_IDS[i])
            self.assertEqual(getattr(site._getOb(after[i]), 'before', None),
                             True)

    def test_reimport_with_structure_and_preserve_partial(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)
        for id in ITEM_IDS:
            site._setObject(id, _makeINIAware(id))
            site._getOb(id).before = True

        context = DummyImportContext(site)
        context._files['structure/.objects'] = '\n'.join(
            [f'{x},{TEST_INI_AWARE}' for x in ITEM_IDS])
        for index in range(len(ITEM_IDS)):
            id = ITEM_IDS[index]
            context._files[
                    'structure/%s.ini' % id] = KNOWN_INI % ('Title: %s' % id,
                                                            'xyzzy')
        context._files['structure/.preserve'] = 'b*'

        importer = self._getImporter()
        importer(context)

        after = site.objectValues()
        self.assertEqual(len(after), len(ITEM_IDS))
        for obj in after:
            if obj.getId().startswith('b'):
                self.assertEqual(getattr(obj, 'before', None), True)
            else:
                self.assertEqual(getattr(obj, 'before', None), None)

    def test_reimport_with_structure_partial_preserve_and_delete(self):
        self._setUpAdapters()
        ITEM_IDS = ('foo', 'bar', 'baz')

        site = _makeFolder('site', site_folder=True)
        for id in ITEM_IDS:
            site._setObject(id, _makeINIAware(id))
            site._getOb(id).before = True

        context = DummyImportContext(site)
        context._files['structure/.objects'] = '\n'.join(
            [f'{x},{TEST_INI_AWARE}' for x in ITEM_IDS[:-1]])
        for index in range(len(ITEM_IDS)):
            id = ITEM_IDS[index]
            context._files[
                    'structure/%s.ini' % id] = KNOWN_INI % ('Title: %s' % id,
                                                            'xyzzy')
        context._files['structure/.preserve'] = 'foo'
        context._files['structure/.delete'] = 'baz'

        importer = self._getImporter()
        importer(context)

        after = site.objectIds()
        self.assertEqual(len(after), len(ITEM_IDS) - 1)
        self.assertFalse('baz' in after)
        self.assertEqual(getattr(site.foo, 'before', None), True)
        self.assertFalse(hasattr(site.bar, 'before'))

    def test_import_site_with_subfolders_and_preserve(self):
        self._setUpAdapters()

        site = _makeFolder('site', site_folder=True)
        site._setObject('foo', _makeFolder('foo'))
        site.foo._setObject('bar', _makeFolder('bar'))

        context = DummyImportContext(site)
        # We want to add 'baz' to 'foo', without losing 'bar'
        context._files['structure/.objects'] = 'foo,%s' % TEST_FOLDER
        context._files['structure/.preserve'] = '*'
        context._files['structure/foo/.objects'] = 'baz,%s' % TEST_FOLDER
        context._files['structure/foo/.preserve'] = '*'
        context._files['structure/foo/baz/.objects'] = ''

        importer = self._getImporter()
        importer(context)

        self.assertEqual(len(site.objectIds()), 1)
        self.assertEqual(site.objectIds()[0], 'foo')

        self.assertEqual(len(site.foo.objectIds()), 2, site.foo.objectIds())
        self.assertEqual(site.foo.objectIds()[0], 'bar')
        self.assertEqual(site.foo.objectIds()[1], 'baz')


TEST_CSV_AWARE = 'Test CSV Aware'
KNOWN_CSV = """\
one,two,three
four,five,six
"""


def _makeCSVAware(id):
    from OFS.SimpleItem import SimpleItem
    from zope.interface import implementer

    from Products.GenericSetup.interfaces import ICSVAware

    from ...interfaces import IDynamicType

    @implementer(IDynamicType, ICSVAware)
    class _TestCSVAware(SimpleItem):
        _was_put = None
        portal_type = TEST_CSV_AWARE

        def getPortalTypeName(self):
            return self.portal_type

        def as_csv(self):
            return KNOWN_CSV

        def put_csv(self, text):
            self._was_put = text

    aware = _TestCSVAware()
    aware._setId(id)

    return aware


TEST_INI_AWARE = 'Test INI Aware'
KNOWN_INI = """\
[DEFAULT]
title = %s
description = %s
"""


def _makeINIAware(id):
    from OFS.SimpleItem import SimpleItem
    from zope.interface import implementer

    from Products.GenericSetup.interfaces import IINIAware

    from ...interfaces import IDynamicType

    @implementer(IDynamicType, IINIAware)
    class _TestINIAware(SimpleItem):
        _was_put = None
        title = 'INI title'
        description = 'INI description'
        portal_type = TEST_INI_AWARE

        def getPortalTypeName(self):
            return self.portal_type

        def as_ini(self):
            return KNOWN_INI % (self.title, self.description)

        def put_ini(self, text):
            self._was_put = text

        def reindexObject(self):
            return NotImplemented

    aware = _TestINIAware()
    aware._setId(id)

    return aware


TEST_DAV_AWARE = 'Test DAV Aware'
KNOWN_DAV = """\
Title: %s
Description: %s

%s
"""


def _makeDAVAware(id):
    from OFS.SimpleItem import SimpleItem
    from zope.interface import implementer

    from Products.GenericSetup.interfaces import IDAVAware

    from ...interfaces import IDynamicType

    @implementer(IDynamicType, IDAVAware)
    class _TestDAVAware(SimpleItem):
        _was_put = None
        title = 'DAV title'
        description = 'DAV description'
        body = 'DAV body'
        portal_type = TEST_DAV_AWARE

        def getPortalTypeName(self):
            return self.portal_type

        def manage_FTPget(self):
            return KNOWN_DAV % (self.title, self.description, self.body)

        def PUT(self, REQUEST, RESPONSE):
            self._was_put = REQUEST.get('BODY', '')
            stream = REQUEST.get('BODYFILE', None)
            self._was_put_as_read = stream.read()

    aware = _TestDAVAware()
    aware._setId(id)

    return aware


TEST_DAV_FOLDER = 'Test DAV Folder'


def _makeDAVAwareFolder(id):
    from zope.interface import implementer

    from Products.GenericSetup.interfaces import IDAVAware

    from ...interfaces import IDynamicType
    from ...PortalFolder import PortalFolder

    @implementer(IDynamicType, IDAVAware)
    class _TestDAVAwareFolder(PortalFolder):
        _was_put = None
        body = 'DAV body'
        portal_type = TEST_DAV_FOLDER

        def getPortalTypeName(self):
            return self.portal_type

        def manage_FTPget(self):
            return KNOWN_DAV % (self.title, self.description, self.body)

        def PUT(self, REQUEST, RESPONSE):
            self._was_put = REQUEST.get('BODY', '')
            stream = REQUEST.get('BODYFILE', None)
            self._was_put_as_read = stream.read()

    folder = _TestDAVAwareFolder(id)
    folder.portal_type = TEST_DAV_FOLDER
    return folder


TEST_CONTENT = 'Test Content'


def _makeItem(self):
    from OFS.SimpleItem import SimpleItem
    from zope.interface import implementer

    from ...interfaces import IDynamicType

    @implementer(IDynamicType)
    class _TestContent(SimpleItem):
        portal_type = TEST_CONTENT

        def getPortalTypeName(self):
            return self.portal_type

    aware = _TestContent()
    aware._setId(id)

    return aware


TEST_FOLDER = 'Test Folder'


def _makeFolder(id, site_folder=False):
    from ...PortalFolder import PortalFolder
    from ...tests.base.dummy import DummyType
    from ...TypesTool import TypesTool

    class _TypeInfo(DummyType):
        def _getId(self):
            return self._id

        def constructInstance(self, container, id, *args, **kw):
            portal_type = self._getId()
            if portal_type == TEST_FOLDER:
                content = PortalFolder(id)
            elif portal_type == TEST_DAV_FOLDER:
                content = _makeDAVAwareFolder(id)
            elif portal_type == TEST_CONTENT:
                content = _makeItem()
                content._setId(id)
            elif portal_type == TEST_INI_AWARE:
                content = _makeINIAware(id)
            elif portal_type == TEST_CSV_AWARE:
                content = _makeCSVAware(id)
            else:
                raise ValueError('Ugh')
            content.portal_type = portal_type
            container._setObject(id, content)
            return container._getOb(id)

    folder = PortalFolder(id)
    folder.portal_type = TEST_FOLDER
    if site_folder:
        ttool = TypesTool()
        ttool._setObject(TEST_CSV_AWARE, _TypeInfo(TEST_CSV_AWARE))
        ttool._setObject(TEST_INI_AWARE, _TypeInfo(TEST_INI_AWARE))
        ttool._setObject(TEST_CONTENT, _TypeInfo(TEST_CONTENT))
        ttool._setObject(TEST_FOLDER, _TypeInfo(TEST_FOLDER))
        ttool._setObject(TEST_DAV_FOLDER, _TypeInfo(TEST_DAV_FOLDER))
        getSiteManager().registerUtility(ttool, ITypesTool)

    return folder
