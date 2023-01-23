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
"""Types tool xml adapter and setup handler unit tests.
"""

import unittest

from OFS.Folder import Folder
from zope.component import getSiteManager

from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from ...interfaces import ITypesTool
from ...permissions import AccessContentsInformation
from ...permissions import ModifyPortalContent
from ...permissions import View
from ...testing import ExportImportZCMLLayer
from ...TypesTool import FactoryTypeInformation
from ...TypesTool import ScriptableTypeInformation
from ...TypesTool import TypesTool


_FTI_BODY = b"""\
<?xml version="1.0" encoding="utf-8"?>
<object name="foo_fti" meta_type="Factory-based Type Information"
   xmlns:i18n="http://xml.zope.org/namespaces/i18n">
 <property name="title"></property>
 <property name="description"></property>
 <property name="icon_expr"></property>
 <property name="content_meta_type"></property>
 <property name="product"></property>
 <property name="factory"></property>
 <property name="add_view_expr"></property>
 <property name="link_target"></property>
 <property name="immediate_view"></property>
 <property name="global_allow">True</property>
 <property name="filter_content_types">True</property>
 <property name="allowed_content_types"/>
 <property name="allow_discussion">False</property>
 <alias from="(Default)" to="foo"/>
 <alias from="view" to="foo"/>
 <action title="Foo" action_id="foo_action" category="Bar"
    condition_expr="python:1" icon_expr="string:${portal_url}/icon.png"
    link_target="" url_expr="string:${object_url}/foo" visible="True"/>
</object>
"""

_TYPESTOOL_BODY = b"""\
<?xml version="1.0" encoding="utf-8"?>
<object name="portal_types" meta_type="CMF Types Tool">
 <property name="title"></property>
 <object name="foo_type" meta_type="Factory-based Type Information"/>
</object>
"""

_TI_LIST = ({
    'id':                    'foo',
    'title':                 'Foo',
    'description':           'Foo things',
    'i18n_domain':           'foo_domain',
    'content_meta_type':     'Foo Thing',
    'icon_expr':             'string:${portal_url}/foo.png',
    'product':               'CMFSetup',
    'factory':               'addFoo',
    'add_view_expr':         'string:${folder_url}/foo_add_view',
    'link_target':           '_new',
    'immediate_view':        'foo_view',
    'filter_content_types':  False,
    'allowed_content_types': (),
    'allow_discussion':      False,
    'global_allow':          False,
    'aliases': {'(Default)': 'foo_view',
                'view':      'foo_view',
                },
    'actions': ({'id':     'view',
                 'title':  'View',
                 'action': 'string:${object_url}/foo_view',
                 'icon_expr': 'string:${portal_url}/preview_icon.png',
                 'link_target': '_new',
                 'permissions': (View,),
                 },
                {'id':     'edit',
                 'title':  'Edit',
                 'action': 'string:${object_url}/foo_edit_form',
                 'icon_expr': 'string:${portal_url}/edit_icon.png',
                 'permissions': (ModifyPortalContent,),
                 },
                {'id':     'metadata',
                 'title':  'Metadata',
                 'action': 'string:${object_url}/metadata_edit_form',
                 'icon_expr': 'string:${portal_url}/metadata_icon.png',
                 'permissions': (ModifyPortalContent,),
                 },
                ),
    }, {
    'id':                    'bar',
    'title':                 'Bar',
    'description':           'Bar things',
    'content_meta_type':     'Bar Thing',
    'icon_expr':             'string:${portal_url}/bar.png',
    'constructor_path':      'make_bar',
    'permission':            'Add portal content',
    'add_view_expr':         'string:${folder_url}/bar_add_view',
    'link_target':           '',
    'immediate_view':        'bar_view',
    'filter_content_types':  True,
    'allowed_content_types': ('foo',),
    'allow_discussion':      True,
    'global_allow':          True,
    'aliases': {'(Default)': 'bar_view',
                'view':      'bar_view',
                },
    'actions': ({'id':     'view',
                 'title':  'View',
                 'action': 'string:${object_url}/bar_view',
                 'permissions': (View,)},
                {'id':     'edit',
                 'title':  'Edit',
                 'action': 'string:${object_url}/bar_edit_form',
                 'permissions': (ModifyPortalContent,)},
                {'id':     'contents',
                 'title':  'Contents',
                 'action': 'string:${object_url}/folder_contents',
                 'permissions': (AccessContentsInformation,)},
                {'id':     'metadata',
                 'title':  'Metadata',
                 'action': 'string:${object_url}/metadata_edit_form',
                 'permissions': (ModifyPortalContent,)})})

_TI_LIST_WITH_FILENAME = []

for original in _TI_LIST:
    duplicate = original.copy()
    duplicate['id'] = '%s object' % original['id']
    _TI_LIST_WITH_FILENAME.append(duplicate)

_EMPTY_TOOL_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_types" meta_type="CMF Types Tool">
 <property name="title"/>
</object>
"""

_NORMAL_TOOL_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_types" meta_type="CMF Types Tool">
 <property name="title"/>
 <object name="foo" meta_type="Factory-based Type Information"/>
 <object name="bar" meta_type="Scriptable Type Information"/>
</object>
"""

_EXTENDED_TOOL_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_types" meta_type="CMF Types Tool">
 <property name="title"/>
 <object name="foo" meta_type="Factory-based Type Information"/>
 <object name="bar" meta_type="Scriptable Type Information"/>
 <object name="baz" meta_type="Scriptable Type Information"/>
</object>
"""

_FILENAME_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_types" meta_type="CMF Types Tool">
 <property name="title"/>
 <object name="foo object" meta_type="Factory-based Type Information"/>
 <object name="bar object" meta_type="Scriptable Type Information"/>
</object>
"""

_UPDATE_TOOL_IMPORT = """\
<?xml version="1.0"?>
<types-tool>
 <type id="foo"/>
</types-tool>
"""

_FOO_EXPORT = """\
<?xml version="1.0"?>
<object name="%s" meta_type="Factory-based Type Information"
   i18n:domain="foo_domain" xmlns:i18n="http://xml.zope.org/namespaces/i18n">
 <property name="title" i18n:translate="">Foo</property>
 <property name="description" i18n:translate="">Foo things</property>
 <property name="icon_expr">string:${portal_url}/foo.png</property>
 <property name="content_meta_type">Foo Thing</property>
 <property name="product">CMFSetup</property>
 <property name="factory">addFoo</property>
 <property name="add_view_expr">string:${folder_url}/foo_add_view</property>
 <property name="link_target">_new</property>
 <property name="immediate_view">foo_view</property>
 <property name="global_allow">False</property>
 <property name="filter_content_types">False</property>
 <property name="allowed_content_types"/>
 <property name="allow_discussion">False</property>
 <alias from="(Default)" to="foo_view"/>
 <alias from="view" to="foo_view"/>
 <action title="View" action_id="view" category="object" condition_expr=""
    url_expr="string:${object_url}/foo_view"
    icon_expr="string:${portal_url}/preview_icon.png" link_target="_new"
    visible="True">
  <permission value="View"/>
 </action>
 <action title="Edit" action_id="edit" category="object" condition_expr=""
    url_expr="string:${object_url}/foo_edit_form"
    icon_expr="string:${portal_url}/edit_icon.png" link_target=""
    visible="True">
  <permission value="Modify portal content"/>
 </action>
 <action title="Metadata" action_id="metadata" category="object"
    condition_expr="" url_expr="string:${object_url}/metadata_edit_form"
    icon_expr="string:${portal_url}/metadata_icon.png" link_target=""
    visible="True">
  <permission value="Modify portal content"/>
 </action>
</object>
"""

_BAR_EXPORT = """\
<?xml version="1.0"?>
<object name="%s" meta_type="Scriptable Type Information"
   xmlns:i18n="http://xml.zope.org/namespaces/i18n">
 <property name="title">Bar</property>
 <property name="description">Bar things</property>
 <property name="icon_expr">string:${portal_url}/bar.png</property>
 <property name="content_meta_type">Bar Thing</property>
 <property name="permission">Add portal content</property>
 <property name="constructor_path">make_bar</property>
 <property name="add_view_expr">string:${folder_url}/bar_add_view</property>
 <property name="link_target"/>
 <property name="immediate_view">bar_view</property>
 <property name="global_allow">True</property>
 <property name="filter_content_types">True</property>
 <property name="allowed_content_types">
  <element value="foo"/>
 </property>
 <property name="allow_discussion">True</property>
 <alias from="(Default)" to="bar_view"/>
 <alias from="view" to="bar_view"/>
 <action title="View" action_id="view" category="object" condition_expr=""
    url_expr="string:${object_url}/bar_view"
    icon_expr="" link_target="" visible="True">
  <permission value="View"/>
 </action>
 <action title="Edit" action_id="edit" category="object" condition_expr=""
    url_expr="string:${object_url}/bar_edit_form"
    icon_expr="" link_target="" visible="True">
  <permission value="Modify portal content"/>
 </action>
 <action title="Contents" action_id="contents" category="object"
    condition_expr="" url_expr="string:${object_url}/folder_contents"
    icon_expr="" link_target="" visible="True">
  <permission value="Access contents information"/>
 </action>
 <action title="Metadata" action_id="metadata" category="object"
    condition_expr="" url_expr="string:${object_url}/metadata_edit_form"
    icon_expr="" link_target="" visible="True">
  <permission value="Modify portal content"/>
 </action>
</object>
"""

_BAR_CMF21_IMPORT = """\
<?xml version="1.0"?>
<object name="%s" meta_type="Scriptable Type Information"
   xmlns:i18n="http://xml.zope.org/namespaces/i18n">
 <property name="title">Bar</property>
 <property name="description">Bar things</property>
 <property name="content_icon">bar.png</property>
 <property name="content_meta_type">Bar Thing</property>
 <property name="permission">Add portal content</property>
 <property name="constructor_path">make_bar</property>
 <property name="add_view_expr">string:${folder_url}/bar_add_view</property>
 <property name="link_target"/>
 <property name="immediate_view">bar_view</property>
 <property name="global_allow">True</property>
 <property name="filter_content_types">True</property>
 <property name="allowed_content_types">
  <element value="foo"/>
 </property>
 <property name="allow_discussion">True</property>
 <alias from="(Default)" to="bar_view"/>
 <alias from="view" to="bar_view"/>
 <action title="View" action_id="view" category="object" condition_expr=""
    url_expr="string:${object_url}/bar_view"
    icon_expr="" link_target="" visible="True">
  <permission value="View"/>
 </action>
 <action title="Edit" action_id="edit" category="object" condition_expr=""
    url_expr="string:${object_url}/bar_edit_form"
    icon_expr="" link_target="" visible="True">
  <permission value="Modify portal content"/>
 </action>
 <action title="Contents" action_id="contents" category="object"
    condition_expr="" url_expr="string:${object_url}/folder_contents"
    icon_expr="" link_target="" visible="True">
  <permission value="Access contents information"/>
 </action>
 <action title="Metadata" action_id="metadata" category="object"
    condition_expr="" url_expr="string:${object_url}/metadata_edit_form"
    icon_expr="" link_target="" visible="True">
  <permission value="Modify portal content"/>
 </action>
</object>
"""

_BAZ_CMF21_IMPORT = """\
<?xml version="1.0"?>
<object name="%s" meta_type="Scriptable Type Information"
   xmlns:i18n="http://xml.zope.org/namespaces/i18n">
 <property name="title">Baz</property>
 <property name="description">Baz things</property>
 <property name="content_icon"></property>
 <property name="content_meta_type">Baz Thing</property>
 <property name="permission">Add portal content</property>
 <property name="constructor_path">make_bar</property>
 <property name="add_view_expr">string:${folder_url}/baz_add_view</property>
 <property name="link_target"/>
 <property name="immediate_view">baz_view</property>
 <property name="global_allow">True</property>
 <property name="filter_content_types">True</property>
 <property name="allowed_content_types">
  <element value="foo"/>
 </property>
 <property name="allow_discussion">True</property>
 <alias from="(Default)" to="baz_view"/>
 <alias from="view" to="baz_view"/>
 <action title="View" action_id="view" category="object" condition_expr=""
    url_expr="string:${object_url}/baz_view"
    icon_expr="" link_target="" visible="True">
  <permission value="View"/>
 </action>
 <action title="Edit" action_id="edit" category="object" condition_expr=""
    url_expr="string:${object_url}/baz_edit_form"
    icon_expr="" link_target="" visible="True">
  <permission value="Modify portal content"/>
 </action>
 <action title="Contents" action_id="contents" category="object"
    condition_expr="" url_expr="string:${object_url}/folder_contents"
    icon_expr="" link_target="" visible="True">
  <permission value="Access contents information"/>
 </action>
 <action title="Metadata" action_id="metadata" category="object"
    condition_expr="" url_expr="string:${object_url}/metadata_edit_form"
    icon_expr="" link_target="" visible="True">
  <permission value="Modify portal content"/>
 </action>
</object>
"""

_UPDATE_FOO_IMPORT = """\
<object name="foo">
 <alias from="spam" to="eggs"/>
</object>
"""


class TypeInformationXMLAdapterTests(BodyAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..typeinfo import TypeInformationXMLAdapter

        return TypeInformationXMLAdapter

    def _populate(self, obj):
        obj.setMethodAliases({'(Default)': 'foo', 'view': 'foo'})
        obj.addAction('foo_action', 'Foo', 'string:${object_url}/foo',
                      'python:1', (), 'Bar',
                      icon_expr='string:${portal_url}/icon.png')

    def _verifyImport(self, obj):
        self.assertEqual(type(obj._aliases), dict)
        self.assertEqual(obj._aliases, {'(Default)': 'foo', 'view': 'foo'})
        self.assertEqual(type(obj._aliases['view']), str)
        self.assertEqual(obj._aliases['view'], 'foo')
        self.assertEqual(type(obj._actions), tuple)
        self.assertEqual(type(obj._actions[0].id), str)
        self.assertEqual(obj._actions[0].id, 'foo_action')
        self.assertEqual(type(obj._actions[0].title), str)
        self.assertEqual(obj._actions[0].title, 'Foo')
        self.assertEqual(type(obj._actions[0].description), str)
        self.assertEqual(obj._actions[0].description, '')
        self.assertEqual(type(obj._actions[0].category), str)
        self.assertEqual(obj._actions[0].category, 'Bar')
        self.assertEqual(type(obj._actions[0].condition.text), str)
        self.assertEqual(obj._actions[0].condition.text, 'python:1')
        self.assertEqual(type(obj._actions[0].icon_expr.text), str)
        self.assertEqual(obj._actions[0].icon_expr.text,
                         'string:${portal_url}/icon.png')

    def setUp(self):
        self._obj = FactoryTypeInformation('foo_fti')
        self._BODY = _FTI_BODY


class TypesToolXMLAdapterTests(BodyAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..typeinfo import TypesToolXMLAdapter

        return TypesToolXMLAdapter

    def _populate(self, obj):
        obj._setObject('foo_type', FactoryTypeInformation('foo_type'))

    def setUp(self):
        self._obj = TypesTool()
        self._BODY = _TYPESTOOL_BODY


class _TypeInfoSetup(BaseRegistryTests):

    def _initSite(self, foo=0):
        site = Folder(id='site').__of__(self.app)
        ttool = TypesTool()
        getSiteManager().registerUtility(ttool, ITypesTool)

        if foo == 1:
            fti = _TI_LIST[0].copy()
            ttool._setObject(fti['id'], FactoryTypeInformation(**fti))
            sti = _TI_LIST[1].copy()
            ttool._setObject(sti['id'], ScriptableTypeInformation(**sti))
        elif foo == 2:
            fti = _TI_LIST_WITH_FILENAME[0].copy()
            ttool._setObject(fti['id'], FactoryTypeInformation(**fti))
            sti = _TI_LIST_WITH_FILENAME[1].copy()
            ttool._setObject(sti['id'], ScriptableTypeInformation(**sti))

        return site, ttool


class exportTypesToolTests(_TypeInfoSetup):

    layer = ExportImportZCMLLayer

    def test_empty(self):
        from ..typeinfo import exportTypesTool

        site = self._initSite()
        context = DummyExportContext(site)
        exportTypesTool(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'types.xml')
        self._compareDOM(text.decode('utf8'), _EMPTY_TOOL_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_normal(self):
        from ..typeinfo import exportTypesTool

        site, _ttool = self._initSite(1)
        context = DummyExportContext(site)
        exportTypesTool(context)

        self.assertEqual(len(context._wrote), 3)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'types.xml')
        self._compareDOM(text.decode('utf8'), _NORMAL_TOOL_EXPORT)
        self.assertEqual(content_type, 'text/xml')

        filename, text, content_type = context._wrote[2]
        self.assertEqual(filename, 'types/bar.xml')
        self._compareDOM(text.decode('utf8'), _BAR_EXPORT % 'bar')
        self.assertEqual(content_type, 'text/xml')

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'types/foo.xml')
        self._compareDOM(text.decode('utf8'), _FOO_EXPORT % 'foo')
        self.assertEqual(content_type, 'text/xml')

    def test_with_filenames(self):
        from ..typeinfo import exportTypesTool

        site, _ttool = self._initSite(2)
        context = DummyExportContext(site)
        exportTypesTool(context)

        self.assertEqual(len(context._wrote), 3)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'types.xml')
        self._compareDOM(text.decode('utf8'), _FILENAME_EXPORT)
        self.assertEqual(content_type, 'text/xml')
        filename, text, content_type = context._wrote[2]
        self.assertEqual(filename, 'types/bar_object.xml')
        self._compareDOM(text.decode('utf8'), _BAR_EXPORT % 'bar object')
        self.assertEqual(content_type, 'text/xml')
        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'types/foo_object.xml')
        self._compareDOM(text.decode('utf8'), _FOO_EXPORT % 'foo object')
        self.assertEqual(content_type, 'text/xml')


class importTypesToolTests(_TypeInfoSetup):

    layer = ExportImportZCMLLayer

    _EMPTY_TOOL_EXPORT = _EMPTY_TOOL_EXPORT
    _FILENAME_EXPORT = _FILENAME_EXPORT
    _NORMAL_TOOL_EXPORT = _NORMAL_TOOL_EXPORT
    _EXTENDED_TOOL_EXPORT = _EXTENDED_TOOL_EXPORT

    def test_empty_default_purge(self):
        from ..typeinfo import importTypesTool

        site, tool = self._initSite(1)

        self.assertEqual(len(tool.objectIds()), 2)

        context = DummyImportContext(site)
        context._files['types.xml'] = self._EMPTY_TOOL_EXPORT
        importTypesTool(context)

        self.assertEqual(len(tool.objectIds()), 0)

    def test_empty_explicit_purge(self):
        from ..typeinfo import importTypesTool

        site, tool = self._initSite(1)

        self.assertEqual(len(tool.objectIds()), 2)

        context = DummyImportContext(site, True)
        context._files['types.xml'] = self._EMPTY_TOOL_EXPORT
        importTypesTool(context)

        self.assertEqual(len(tool.objectIds()), 0)

    def test_empty_skip_purge(self):
        from ..typeinfo import importTypesTool

        site, tool = self._initSite(1)

        self.assertEqual(len(tool.objectIds()), 2)

        context = DummyImportContext(site, False)
        context._files['types.xml'] = self._EMPTY_TOOL_EXPORT
        importTypesTool(context)

        self.assertEqual(len(tool.objectIds()), 2)

    def test_normal(self):
        from ..typeinfo import importTypesTool

        site, tool = self._initSite()

        self.assertEqual(len(tool.objectIds()), 0)

        context = DummyImportContext(site)
        context._files['types.xml'] = self._NORMAL_TOOL_EXPORT
        context._files['types/foo.xml'] = _FOO_EXPORT % 'foo'
        context._files['types/bar.xml'] = _BAR_EXPORT % 'bar'
        importTypesTool(context)

        self.assertEqual(len(tool.objectIds()), 2)
        self.assertTrue('foo' in tool.objectIds())
        self.assertTrue('bar' in tool.objectIds())

    def test_with_filenames(self):
        from ..typeinfo import importTypesTool

        site, tool = self._initSite()

        self.assertEqual(len(tool.objectIds()), 0)

        context = DummyImportContext(site)
        context._files['types.xml'] = self._FILENAME_EXPORT
        context._files['types/foo_object.xml'] = _FOO_EXPORT % 'foo object'
        context._files['types/bar_object.xml'] = _BAR_EXPORT % 'bar object'
        importTypesTool(context)

        self.assertEqual(len(tool.objectIds()), 2)
        self.assertTrue('foo object' in tool.objectIds())
        self.assertTrue('bar object' in tool.objectIds())

    def test_migration(self):
        from ..typeinfo import importTypesTool

        site, tool = self._initSite()

        self.assertEqual(len(tool.objectIds()), 0)

        context = DummyImportContext(site)
        context._files['types.xml'] = self._EXTENDED_TOOL_EXPORT
        context._files['types/foo.xml'] = _FOO_EXPORT % 'foo'
        context._files['types/bar.xml'] = _BAR_CMF21_IMPORT % 'bar'
        context._files['types/baz.xml'] = _BAZ_CMF21_IMPORT % 'baz'
        importTypesTool(context)

        self.assertEqual(len(tool.objectIds()), 3)
        self.assertTrue('foo' in tool.objectIds())
        self.assertTrue('bar' in tool.objectIds())
        self.assertTrue('baz' in tool.objectIds())
        self.assertEqual(tool.bar.icon_expr, 'string:${portal_url}/bar.png')
        self.assertEqual(tool.baz.icon_expr, '')

    def test_normal_update(self):
        from ..typeinfo import importTypesTool

        site, tool = self._initSite()

        context = DummyImportContext(site)
        context._files['types.xml'] = self._NORMAL_TOOL_EXPORT
        context._files['types/foo.xml'] = _FOO_EXPORT % 'foo'
        context._files['types/bar.xml'] = _BAR_EXPORT % 'bar'
        importTypesTool(context)

        self.assertEqual(tool.foo.title, 'Foo')
        self.assertEqual(tool.foo.content_meta_type, 'Foo Thing')
        self.assertEqual(tool.foo.icon_expr, 'string:${portal_url}/foo.png')
        self.assertEqual(tool.foo.immediate_view, 'foo_view')
        self.assertEqual(tool.foo._aliases,
                         {'(Default)': 'foo_view', 'view': 'foo_view'})

        context = DummyImportContext(site, False)
        context._files['types.xml'] = _UPDATE_TOOL_IMPORT
        context._files['types/foo.xml'] = _UPDATE_FOO_IMPORT
        importTypesTool(context)

        self.assertEqual(tool.foo.title, 'Foo')
        self.assertEqual(tool.foo.content_meta_type, 'Foo Thing')
        self.assertEqual(tool.foo.icon_expr, 'string:${portal_url}/foo.png')
        self.assertEqual(tool.foo.immediate_view, 'foo_view')
        self.assertEqual(tool.foo._aliases,
                         {'(Default)': 'foo_view', 'view': 'foo_view',
                          'spam': 'eggs'})

    def test_action_remove(self):
        from ..typeinfo import importTypesTool

        site, tool = self._initSite()

        self.assertEqual(len(tool.objectIds()), 0)

        context = DummyImportContext(site, False)

        # Make sure removing a non-existant action doesn't fail
        _TOOL = """\
        <?xml version="1.0"?>
        <object name="portal_types" meta_type="CMF Types Tool">
         <object name="%s" meta_type="Factory-based Type Information"/>
        </object>
        """
        context._files['types.xml'] = (_TOOL % 'baz').strip()

        _BAZ_SETUP = """\
        <?xml version="1.0"?>
        <object name="%s" meta_type="Factory-based Type Information">
         <property name="title">Baz</property>
         <action title="View" action_id="view" category="object"
            condition_expr="" url_expr="string:${object_url}/baz_view"
            icon_expr="" visible="True">
          <permission value="View"/>
         </action>
         <action action_id="edit" category="object" remove="True" />
        </object>
        """
        context._files['types/baz.xml'] = (_BAZ_SETUP % 'baz').strip()
        importTypesTool(context)

        self.assertEqual(len(tool.objectIds()), 1)
        self.assertTrue('baz' in tool.objectIds())
        baz = tool['baz']
        actions = baz.listActions()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].title, 'View')

        # Remove an already existing action
        _BAZ_REMOVE = """\
        <?xml version="1.0"?>
        <object name="%s" meta_type="Factory-based Type Information">
         <property name="title">Baz</property>
         <action action_id="view" category="object" remove="True" />
        </object>
        """
        context._files['types/baz.xml'] = (_BAZ_REMOVE % 'baz').strip()
        importTypesTool(context)

        self.assertEqual(len(tool.objectIds()), 1)
        self.assertTrue('baz' in tool.objectIds())
        baz = tool['baz']
        actions = baz.listActions()
        self.assertEqual(len(actions), 0)


def test_suite():
    loadTestsFromTestCase = unittest.defaultTestLoader.loadTestsFromTestCase
    return unittest.TestSuite((
        loadTestsFromTestCase(TypeInformationXMLAdapterTests),
        loadTestsFromTestCase(TypesToolXMLAdapterTests),
        loadTestsFromTestCase(exportTypesToolTests),
        loadTestsFromTestCase(importTypesToolTests),
    ))
