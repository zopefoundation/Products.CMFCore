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
"""Skins tool xml adapter and setup handler unit tests.
"""

import os
import unittest

from OFS.Folder import Folder
from Testing import ZopeTestCase
from zope.component import getSiteManager
from zope.interface import implementer

from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.testing import NodeAdapterTestCase
from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from ...interfaces import ISkinsTool
from ...testing import ExportImportZCMLLayer


ZopeTestCase.installProduct('CMFCore', 1)

_TESTS_PATH = os.path.split(__file__)[0]

_DIRECTORYVIEW_XML = b"""\
<object name="foo_directoryview" meta_type="Filesystem Directory View"
   directory="Products.CMFCore.exportimport.tests:one"/>
"""

_SKINSTOOL_BODY = b"""\
<?xml version="1.0" encoding="utf-8"?>
<object name="portal_skins" meta_type="CMF Skins Tool" allow_any="False"
   cookie_persistence="False" default_skin="" request_varname="portal_skin">
 <object name="foo_directoryview" meta_type="Filesystem Directory View"
    directory="Products.CMFCore.exportimport.tests:one"/>
 <skin-path name="foo_path">
  <layer name="one"/>
 </skin-path>
</object>
"""

_EMPTY_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_skins" meta_type="Dummy Skins Tool" allow_any="False"
   cookie_persistence="False" default_skin="default_skin"
   request_varname="request_varname"/>
"""

_NORMAL_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_skins" meta_type="Dummy Skins Tool" allow_any="True"
   cookie_persistence="True" default_skin="basic" request_varname="skin_var">
 <object name="one" meta_type="Filesystem Directory View"
    directory="Products.CMFCore.exportimport.tests:one"/>
 <object name="three" meta_type="Filesystem Directory View"
    directory="Products.CMFCore.exportimport.tests:three"/>
 <object name="two" meta_type="Filesystem Directory View"
    directory="Products.CMFCore.exportimport.tests:two"/>
 <skin-path name="basic">
  <layer name="one"/>
 </skin-path>
 <skin-path name="fancy">
  <layer name="three"/>
  <layer name="two"/>
  <layer name="one"/>
 </skin-path>
</object>
"""

_FRAGMENT1_IMPORT = """\
<?xml version="1.0"?>
<object name="portal_skins" meta_type="Dummy Skins Tool">
 <object name="three" meta_type="Filesystem Directory View"
    package="Products.CMFCore" path="exportimport/tests/three"/>
 <skin-path name="*">
  <layer name="three" insert-before="two"/>
 </skin-path>
</object>
"""

_FRAGMENT2_IMPORT = """\
<?xml version="1.0"?>
<object name="portal_skins" meta_type="Dummy Skins Tool">
 <object name="four" meta_type="Filesystem Directory View"
    directory="Products.CMFCore.exportimport.tests:four"/>
 <skin-path name="*">
  <layer name="four" insert-after="three"/>
 </skin-path>
</object>
"""

_FRAGMENT3_IMPORT = """\
<?xml version="1.0"?>
<object name="portal_skins" meta_type="Dummy Skins Tool">
 <object name="three" meta_type="Filesystem Directory View"
    directory="Products.CMFCore.exportimport.tests:three"/>
 <object name="four" meta_type="Filesystem Directory View"
    directory="Products.CMFCore.exportimport.tests:four"/>
 <skin-path name="*">
  <layer name="three" insert-before="*"/>
  <layer name="four" insert-after="*"/>
 </skin-path>
</object>
"""

_FRAGMENT4_IMPORT = """\
<?xml version="1.0"?>
<object name="portal_skins" meta_type="Dummy Skins Tool">
 <skin-path name="*">
  <layer name="three" remove="1"/>
 </skin-path>
</object>
"""

_FRAGMENT5_IMPORT = """\
<?xml version="1.0"?>
<object name="portal_skins" meta_type="Dummy Skins Tool">
 <skin-path name="existing" based-on="basic">
 </skin-path>
 <skin-path name="new" based-on="basic">
  <layer name="two" insert-before="three"/>
 </skin-path>
 <skin-path name="wrongbase" based-on="invalid_base_id">
  <layer name="two" insert-before="three"/>
 </skin-path>
</object>"""


_FRAGMENT6_IMPORT = """\
<?xml version="1.0"?>
<object name="portal_skins" meta_type="Dummy Skins Tool" allow_any="True"
   cookie_persistence="True" default_skin="basic" request_varname="skin_var">
 <object name="one" meta_type="Filesystem Directory View"
    directory="Products.CMFCore.exportimport.tests:one"/>
 <object name="three" meta_type="Filesystem Directory View"
    directory="Products.CMFCore.exportimport.tests:three"/>
 <object name="two" meta_type="Filesystem Directory View"
    directory="Products.CMFCore.exportimport.tests:two"/>
 <skin-path name="basic">
  <layer name="one"/>
 </skin-path>
 <skin-path name="fancy" remove="True"/>
 <skin-path name="invalid" remove="True"/>
</object>
"""

_FRAGMENT7_IMPORT = """\
<?xml version="1.0"?>
<object name="portal_skins" meta_type="Dummy Skins Tool">
 <skin-path name="existing">
  <layer name="two" insert-after="one"/>
 </skin-path>
</object>"""


class DummySite(Folder):

    _skin_setup_called = False

    def clearCurrentSkin(self):
        pass

    def setupCurrentSkin(self, REQUEST):
        self._skin_setup_called = True


@implementer(ISkinsTool)
class DummySkinsTool(Folder):

    meta_type = 'Dummy Skins Tool'
    default_skin = 'default_skin'
    request_varname = 'request_varname'
    allow_any = False
    cookie_persistence = False

    def __init__(self, selections=None, fsdvs=()):
        self._selections = selections or {}

        for id, obj in fsdvs:
            self._setObject(id, obj)

    def _getSelections(self):
        return self._selections

    getSkinSelections = _getSelections

    def getId(self):
        return 'portal_skins'

    def getSkinPaths(self):
        result = sorted(self._selections.items())
        return result

    def addSkinSelection(self, skinname, skinpath, test=0, make_default=0):
        self._selections[skinname] = skinpath

    def manage_skinLayers(self, chosen=(), add_skin=0, del_skin=0,
                          skinname='', skinpath='', REQUEST=None):
        if del_skin:
            for skin_name in chosen:
                del self._selections[skin_name]


class _DVRegistrySetup:

    def setUp(self):
        from ... import DirectoryView

        self._olddirreg = DirectoryView._dirreg
        DirectoryView._dirreg = DirectoryView.DirectoryRegistry()
        self._dirreg = DirectoryView._dirreg
        self._dirreg.registerDirectory('one', globals())
        self._dirreg.registerDirectory('two', globals())
        self._dirreg.registerDirectory('three', globals())
        self._dirreg.registerDirectory('four', globals())

    def tearDown(self):
        from ... import DirectoryView

        DirectoryView._dirreg = self._olddirreg


class DirectoryViewAdapterTests(_DVRegistrySetup,
                                NodeAdapterTestCase,
                                unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..skins import DirectoryViewNodeAdapter

        return DirectoryViewNodeAdapter

    def _populate(self, obj):
        obj._dirpath = 'Products.CMFCore.exportimport.tests:one'

    def setUp(self):
        from ...DirectoryView import DirectoryView

        _DVRegistrySetup.setUp(self)
        self._obj = DirectoryView('foo_directoryview').__of__(Folder())
        self._XML = _DIRECTORYVIEW_XML

    def tearDown(self):
        _DVRegistrySetup.tearDown(self)


class SkinsToolXMLAdapterTests(_DVRegistrySetup,
                               BodyAdapterTestCase,
                               unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..skins import SkinsToolXMLAdapter

        return SkinsToolXMLAdapter

    def _populate(self, obj):
        from ...DirectoryView import DirectoryView

        obj._setObject('foo_directoryview',
                       DirectoryView(
                            'foo_directoryview',
                            'Products.CMFCore.exportimport.tests:one'))
        obj.addSkinSelection('foo_path', 'one')

    def _verifyImport(self, obj):
        pass

    def setUp(self):
        from ...SkinsTool import SkinsTool

        _DVRegistrySetup.setUp(self)
        self._obj = SkinsTool()
        self._BODY = _SKINSTOOL_BODY

    def tearDown(self):
        _DVRegistrySetup.tearDown(self)


class _SkinsSetup(_DVRegistrySetup, BaseRegistryTests):

    def _initSite(self, selections={}, ids=()):
        from ...DirectoryView import DirectoryView

        site = DummySite()
        fsdvs = [(id,
                  DirectoryView(id,
                                'Products.CMFCore.exportimport.tests:%s' % id))
                 for id in ids]
        stool = DummySkinsTool(selections, fsdvs).__of__(site)
        getSiteManager().registerUtility(stool, ISkinsTool)

        site.REQUEST = 'exists'
        return site, stool

    def setUp(self):
        BaseRegistryTests.setUp(self)
        _DVRegistrySetup.setUp(self)

    def tearDown(self):
        _DVRegistrySetup.tearDown(self)
        BaseRegistryTests.tearDown(self)


class exportSkinsToolTests(_SkinsSetup):

    layer = ExportImportZCMLLayer

    def test_empty(self):
        from ..skins import exportSkinsTool

        site, _stool = self._initSite()
        context = DummyExportContext(site)
        exportSkinsTool(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'skins.xml')
        self._compareDOM(text.decode('utf8'), _EMPTY_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_normal(self):
        from ..skins import exportSkinsTool

        _IDS = ('one', 'two', 'three')
        _PATHS = {'basic': 'one', 'fancy': 'three, two, one'}

        site, tool = self._initSite(selections=_PATHS, ids=_IDS)

        tool.default_skin = 'basic'
        tool.request_varname = 'skin_var'
        tool.allow_any = True
        tool.cookie_persistence = True

        context = DummyExportContext(site)
        exportSkinsTool(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'skins.xml')
        self._compareDOM(text.decode('utf8'), _NORMAL_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class importSkinsToolTests(_SkinsSetup):

    layer = ExportImportZCMLLayer

    _EMPTY_EXPORT = _EMPTY_EXPORT
    _FRAGMENT1_IMPORT = _FRAGMENT1_IMPORT
    _FRAGMENT2_IMPORT = _FRAGMENT2_IMPORT
    _FRAGMENT3_IMPORT = _FRAGMENT3_IMPORT
    _FRAGMENT4_IMPORT = _FRAGMENT4_IMPORT
    _FRAGMENT5_IMPORT = _FRAGMENT5_IMPORT
    _FRAGMENT6_IMPORT = _FRAGMENT6_IMPORT
    _FRAGMENT7_IMPORT = _FRAGMENT7_IMPORT
    _NORMAL_EXPORT = _NORMAL_EXPORT

    def test_remove_skin_path(self):
        from ..skins import importSkinsTool

        _IDS = ('one', 'two', 'three')
        _PATHS = {'basic': 'one', 'fancy': 'three, two, one'}

        site, skins_tool = self._initSite(selections=_PATHS, ids=_IDS)

        self.assertTrue('fancy' in skins_tool._getSelections())

        context = DummyImportContext(site)
        context._files['skins.xml'] = self._FRAGMENT6_IMPORT
        importSkinsTool(context)

        self.assertFalse('fancy' in skins_tool._getSelections())

    def test_empty_default_purge(self):
        from ..skins import importSkinsTool

        _IDS = ('one', 'two', 'three')
        _PATHS = {'basic': 'one', 'fancy': 'three, two, one'}

        site, skins_tool = self._initSite(selections=_PATHS, ids=_IDS)

        self.assertFalse(site._skin_setup_called)
        self.assertEqual(len(skins_tool.getSkinPaths()), 2)
        self.assertEqual(len(skins_tool.objectItems()), 3)

        context = DummyImportContext(site)
        context._files['skins.xml'] = self._EMPTY_EXPORT
        importSkinsTool(context)

        self.assertEqual(skins_tool.default_skin, 'default_skin')
        self.assertEqual(skins_tool.request_varname, 'request_varname')
        self.assertFalse(skins_tool.allow_any)
        self.assertFalse(skins_tool.cookie_persistence)
        self.assertTrue(site._skin_setup_called)
        self.assertEqual(len(skins_tool.getSkinPaths()), 0)
        self.assertEqual(len(skins_tool.objectItems()), 0)

    def test_empty_explicit_purge(self):
        from ..skins import importSkinsTool

        _IDS = ('one', 'two', 'three')
        _PATHS = {'basic': 'one', 'fancy': 'three, two, one'}

        site, skins_tool = self._initSite(selections=_PATHS, ids=_IDS)

        self.assertFalse(site._skin_setup_called)
        self.assertEqual(len(skins_tool.getSkinPaths()), 2)
        self.assertEqual(len(skins_tool.objectItems()), 3)

        context = DummyImportContext(site, True)
        context._files['skins.xml'] = self._EMPTY_EXPORT
        importSkinsTool(context)

        self.assertEqual(skins_tool.default_skin, 'default_skin')
        self.assertEqual(skins_tool.request_varname, 'request_varname')
        self.assertFalse(skins_tool.allow_any)
        self.assertFalse(skins_tool.cookie_persistence)
        self.assertTrue(site._skin_setup_called)
        self.assertEqual(len(skins_tool.getSkinPaths()), 0)
        self.assertEqual(len(skins_tool.objectItems()), 0)

    def test_empty_skip_purge(self):
        from ..skins import importSkinsTool

        _IDS = ('one', 'two', 'three')
        _PATHS = {'basic': 'one', 'fancy': 'three, two, one'}

        site, skins_tool = self._initSite(selections=_PATHS, ids=_IDS)

        self.assertFalse(site._skin_setup_called)
        self.assertEqual(len(skins_tool.getSkinPaths()), 2)
        self.assertEqual(len(skins_tool.objectItems()), 3)

        context = DummyImportContext(site, False)
        context._files['skins.xml'] = self._EMPTY_EXPORT
        importSkinsTool(context)

        self.assertEqual(skins_tool.default_skin, 'default_skin')
        self.assertEqual(skins_tool.request_varname, 'request_varname')
        self.assertFalse(skins_tool.allow_any)
        self.assertFalse(skins_tool.cookie_persistence)
        self.assertTrue(site._skin_setup_called)
        self.assertEqual(len(skins_tool.getSkinPaths()), 2)
        self.assertEqual(len(skins_tool.objectItems()), 3)

    def test_normal(self):
        from ..skins import importSkinsTool

        site, skins_tool = self._initSite()

        self.assertFalse(site._skin_setup_called)
        self.assertEqual(len(skins_tool.getSkinPaths()), 0)
        self.assertEqual(len(skins_tool.objectItems()), 0)

        context = DummyImportContext(site)
        context._files['skins.xml'] = self._NORMAL_EXPORT
        importSkinsTool(context)

        self.assertEqual(skins_tool.default_skin, 'basic')
        self.assertEqual(skins_tool.request_varname, 'skin_var')
        self.assertTrue(skins_tool.allow_any)
        self.assertTrue(skins_tool.cookie_persistence)
        self.assertTrue(site._skin_setup_called)
        self.assertEqual(len(skins_tool.getSkinPaths()), 2)
        self.assertEqual(len(skins_tool.objectItems()), 3)

    def test_fragment_skip_purge(self):
        from ..skins import importSkinsTool

        _IDS = ('one', 'two')
        _PATHS = {'basic': 'one', 'fancy': 'two,one'}

        site, skins_tool = self._initSite(selections=_PATHS, ids=_IDS)

        self.assertFalse(site._skin_setup_called)
        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 2)
        self.assertEqual(skin_paths[0], ('basic', 'one'))
        self.assertEqual(skin_paths[1], ('fancy', 'two,one'))
        self.assertEqual(len(skins_tool.objectItems()), 2)

        context = DummyImportContext(site, False)
        context._files['skins.xml'] = self._FRAGMENT1_IMPORT
        importSkinsTool(context)

        self.assertEqual(skins_tool.default_skin, 'default_skin')
        self.assertEqual(skins_tool.request_varname, 'request_varname')
        self.assertFalse(skins_tool.allow_any)
        self.assertFalse(skins_tool.cookie_persistence)
        self.assertTrue(site._skin_setup_called)
        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 2)
        self.assertEqual(skin_paths[0], ('basic', 'one,three'))
        self.assertEqual(skin_paths[1], ('fancy', 'three,two,one'))
        self.assertEqual(len(skins_tool.objectItems()), 3)

        context._files['skins.xml'] = self._FRAGMENT2_IMPORT
        importSkinsTool(context)

        self.assertEqual(skins_tool.default_skin, 'default_skin')
        self.assertEqual(skins_tool.request_varname, 'request_varname')
        self.assertFalse(skins_tool.allow_any)
        self.assertFalse(skins_tool.cookie_persistence)
        self.assertTrue(site._skin_setup_called)
        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 2)
        self.assertEqual(skin_paths[0], ('basic', 'one,three,four'))
        self.assertEqual(skin_paths[1], ('fancy', 'three,four,two,one'))
        self.assertEqual(len(skins_tool.objectItems()), 4)

    def test_fragment3_skip_purge(self):
        from ..skins import importSkinsTool

        _IDS = ('one', 'two')
        _PATHS = {'basic': 'one', 'fancy': 'two,one'}

        site, skins_tool = self._initSite(selections=_PATHS, ids=_IDS)

        self.assertFalse(site._skin_setup_called)
        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 2)
        self.assertEqual(skin_paths[0], ('basic', 'one'))
        self.assertEqual(skin_paths[1], ('fancy', 'two,one'))
        self.assertEqual(len(skins_tool.objectItems()), 2)

        context = DummyImportContext(site, False)
        context._files['skins.xml'] = self._FRAGMENT3_IMPORT
        importSkinsTool(context)

        self.assertEqual(skins_tool.default_skin, 'default_skin')
        self.assertEqual(skins_tool.request_varname, 'request_varname')
        self.assertFalse(skins_tool.allow_any)
        self.assertFalse(skins_tool.cookie_persistence)
        self.assertTrue(site._skin_setup_called)
        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 2)
        self.assertEqual(skin_paths[0], ('basic', 'three,one,four'))
        self.assertEqual(skin_paths[1],
                         ('fancy', 'three,two,one,four'))
        self.assertEqual(len(skins_tool.objectItems()), 4)

    def test_fragment4_removal(self):
        from ..skins import importSkinsTool

        _IDS = ('one', 'two')
        _PATHS = {'basic': 'one', 'fancy': 'two,one'}

        site, skins_tool = self._initSite(selections=_PATHS, ids=_IDS)

        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 2)
        self.assertEqual(skin_paths[0], ('basic', 'one'))
        self.assertEqual(skin_paths[1], ('fancy', 'two,one'))
        self.assertEqual(len(skins_tool.objectItems()), 2)

        context = DummyImportContext(site, False)
        context._files['skins.xml'] = self._FRAGMENT3_IMPORT
        importSkinsTool(context)

        self.assertTrue(site._skin_setup_called)
        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 2)
        self.assertEqual(skin_paths[0], ('basic', 'three,one,four'))
        self.assertEqual(skin_paths[1], ('fancy', 'three,two,one,four'))
        self.assertEqual(len(skins_tool.objectItems()), 4)

        context = DummyImportContext(site, False)
        context._files['skins.xml'] = self._FRAGMENT4_IMPORT

        importSkinsTool(context)

        self.assertTrue(site._skin_setup_called)
        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 2)
        self.assertEqual(skin_paths[0], ('basic', 'one,four'))
        self.assertEqual(skin_paths[1], ('fancy', 'two,one,four'))
        self.assertEqual(len(skins_tool.objectItems()), 4)

    def test_fragment5_based_skin(self):
        from ..skins import importSkinsTool

        _IDS = ('one', 'two', 'three', 'four')
        _PATHS = {'basic': 'one,three,four', 'existing': 'one,two,four'}

        site, skins_tool = self._initSite(selections=_PATHS, ids=_IDS)

        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 2)
        self.assertEqual(skin_paths[0], ('basic', 'one,three,four'))
        self.assertEqual(skin_paths[1], ('existing', 'one,two,four'))
        self.assertEqual(len(skins_tool.objectItems()), 4)

        context = DummyImportContext(site, False)
        context._files['skins.xml'] = self._FRAGMENT5_IMPORT

        importSkinsTool(context)

        self.assertTrue(site._skin_setup_called)
        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 4)
        self.assertEqual(skin_paths[0], ('basic', 'one,three,four'))
        self.assertEqual(skin_paths[1], ('existing', 'one,two,three,four'))
        self.assertEqual(skin_paths[2], ('new', 'one,two,three,four'))
        self.assertEqual(skin_paths[3], ('wrongbase', 'two'))
        self.assertEqual(len(skins_tool.objectItems()), 4)

    def test_fragment7_modified_skin(self):
        # https://bugs.launchpad.net/zope-cmf/+bug/161732
        from ..skins import importSkinsTool

        _IDS = ('one', 'two', 'three', 'four')
        _PATHS = {'existing': 'one,three,four'}

        site, skins_tool = self._initSite(selections=_PATHS, ids=_IDS)

        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 1)
        self.assertEqual(skin_paths[0], ('existing', 'one,three,four'))
        self.assertEqual(len(skins_tool.objectItems()), 4)

        context = DummyImportContext(site, False)
        context._files['skins.xml'] = self._FRAGMENT7_IMPORT

        importSkinsTool(context)

        self.assertTrue(site._skin_setup_called)
        skin_paths = skins_tool.getSkinPaths()
        self.assertEqual(len(skin_paths), 1)
        self.assertEqual(skin_paths[0], ('existing', 'one,two,three,four'))
        self.assertEqual(len(skins_tool.objectItems()), 4)


def test_suite():
    loadTestsFromTestCase = unittest.defaultTestLoader.loadTestsFromTestCase
    return unittest.TestSuite((
        loadTestsFromTestCase(DirectoryViewAdapterTests),
        loadTestsFromTestCase(SkinsToolXMLAdapterTests),
        loadTestsFromTestCase(exportSkinsToolTests),
        loadTestsFromTestCase(importSkinsToolTests),
    ))
