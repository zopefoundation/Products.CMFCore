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
"""Actions tool node adapter unit tests.
"""

import unittest

from Acquisition import Implicit
from Acquisition import aq_parent
from OFS.OrderedFolder import OrderedFolder
from zope.component import getSiteManager
from zope.interface import implementer

from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.testing import NodeAdapterTestCase
from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from ...ActionProviderBase import ActionProviderBase
from ...interfaces import IActionProvider
from ...interfaces import IActionsTool
from ...interfaces import IMembershipTool
from ...testing import ExportImportZCMLLayer
from ...tests.base.dummy import DummySite


_ACTION_XML = b"""\
<object name="foo_action" meta_type="CMF Action">
 <property name="title">Foo</property>
 <property name="description"></property>
 <property name="url_expr">string:${object_url}/foo</property>
 <property name="link_target"></property>
 <property name="icon_expr"></property>
 <property name="available_expr">python:1</property>
 <property name="permissions"/>
 <property name="visible">True</property>
</object>
"""

_ACTIONCATEGORY_XML = b"""\
<object name="foo_category" meta_type="CMF Action Category">
 <property name="title"></property>
 <object name="foo_action" meta_type="CMF Action">
  <property name="title"></property>
  <property name="description"></property>
  <property name="url_expr"></property>
  <property name="link_target"></property>
  <property name="icon_expr"></property>
  <property name="available_expr"></property>
  <property name="permissions"/>
  <property name="visible">True</property>
 </object>
</object>
"""

_ACTIONSTOOL_BODY = b"""\
<?xml version="1.0" encoding="utf-8"?>
<object name="portal_actions" meta_type="CMF Actions Tool"
   xmlns:i18n="http://xml.zope.org/namespaces/i18n">
 <action-provider name="portal_actions"/>
 <object name="foo_category" meta_type="CMF Action Category">
  <property name="title"></property>
  <object name="foo_action" meta_type="CMF Action" i18n:domain="foo_domain">
   <property name="title" i18n:translate=""></property>
   <property name="description" i18n:translate=""></property>
   <property name="url_expr"></property>
   <property name="link_target"></property>
   <property name="icon_expr"></property>
   <property name="available_expr"></property>
   <property name="permissions"/>
   <property name="visible">True</property>
  </object>
 </object>
</object>
"""

_EMPTY_EXPORT = b"""\
<?xml version="1.0"?>
<object name="portal_actions" meta_type="CMF Actions Tool"
   xmlns:i18n="http://xml.zope.org/namespaces/i18n">
 <action-provider name="portal_actions"/>
</object>
"""

_OLD_EXPORT = b"""\
<?xml version="1.0"?>
<object name="portal_actions" meta_type="CMF Actions Tool"
   xmlns:i18n="http://xml.zope.org/namespaces/i18n">
 <action-provider name="portal_actions">
  <action action_id="baz"
          title="Baz"
          url_expr="string:${object_url}/baz"
          condition_expr="python:1"
          category="dummy"
          visible="True"/>
 </action-provider>
 <action-provider name="portal_foo">
  <action action_id="foo"
          title="Foo"
          url_expr="string:${object_url}/foo"
          condition_expr="python:1"
          category="dummy"
          visible="True"/>
 </action-provider>
 <action-provider name="portal_bar">
  <action action_id="bar"
          title="Bar"
          url_expr="string:${object_url}/bar"
          condition_expr="python:0"
          category="dummy"
          visible="False">
   <permission>Manage portal</permission>
  </action>
 </action-provider>
</object>
"""

_NORMAL_EXPORT = """\
<?xml version="1.0" encoding="utf-8"?>
<object name="portal_actions" meta_type="CMF Actions Tool"
   xmlns:i18n="http://xml.zope.org/namespaces/i18n">
 <action-provider name="portal_actions">
  <action action_id="baz"
          title="Baz"
          url_expr="string:${object_url}/baz"
          condition_expr="python:1"
          category="dummy"
          visible="True"/>
 </action-provider>
 <action-provider name="portal_foo"/>
 <action-provider name="portal_bar"/>
</object>
"""

_NEWSYTLE_EXPORT = b"""\
<?xml version="1.0"?>
<object name="portal_actions" meta_type="CMF Actions Tool"
   xmlns:i18n="http://xml.zope.org/namespaces/i18n">
 <action-provider name="portal_actions"/>
 <action-provider name="portal_foo"/>
 <action-provider name="portal_bar"/>
 <object name="dummy" meta_type="CMF Action Category">
  <property name="title"></property>
  <object name="baz" meta_type="CMF Action">
   <property name="title">Baz</property>
   <property name="description"></property>
   <property name="url_expr">string:${object_url}/baz</property>
   <property name="link_target"></property>
   <property name="icon_expr"></property>
   <property name="available_expr">python:1</property>
   <property name="permissions"></property>
   <property name="visible">True</property>
  </object>
 </object>
</object>
"""

_I18N_IMPORT = """\
<?xml version="1.0"?>
<object name="portal_actions" meta_type="CMF Actions Tool"
   xmlns:i18n="http://xml.zope.org/namespaces/i18n">
 <action-provider name="portal_actions"/>
 <object name="dummy" meta_type="CMF Action Category">
  <property name="title"></property>
  <object name="foo" meta_type="CMF Action" i18n:domain="foo_domain">
   <property name="title" i18n:translate="">Foo</property>
   <property name="description" i18n:translate=""></property>
   <property name="url_expr">string:${object_url}/foo</property>
   <property name="link_target"></property>
   <property name="icon_expr"></property>
   <property name="available_expr">python:1</property>
   <property name="permissions"></property>
   <property name="visible">True</property>
  </object>
 </object>
</object>
"""

_INSERT_IMPORT = """\
<?xml version="1.0"?>
<object name="portal_actions">
 <object name="dummy">
 <object name="spam" meta_type="CMF Action" insert-before="*">
  <property name="title">Spam</property>
  <property name="description"></property>
  <property name="url_expr">string:${object_url}/spam</property>
  <property name="icon_expr">string:spam_icon.png</property>
  <property name="available_expr"></property>
  <property name="permissions">
   <element value="View" /></property>
  <property name="visible">True</property>
 </object>
 <object name="baz" insert-after="*">
  <property name="icon_expr">string:baz_icon.png</property>
 </object>
 </object>
</object>
"""

_REMOVE_IMPORT = """\
<?xml version="1.0"?>
<object name="portal_actions">
 <action-provider name="portal_actions" remove=""/>
 <action-provider name="not_existing" remove=""/>
 <action-provider name="portal_bar" remove=""/>
</object>
"""


@implementer(IActionProvider)
class DummyTool(OrderedFolder, ActionProviderBase):
    pass


class DummyUser(Implicit):

    def getId(self):
        return 'dummy'


class DummyMembershipTool(DummyTool):

    def isAnonymousUser(self):
        return False

    def getAuthenticatedMember(self):
        return DummyUser().__of__(aq_parent(self))


@implementer(IActionsTool)
class DummyActionsTool(DummyTool):

    id = 'portal_actions'
    meta_type = 'CMF Actions Tool'

    def __init__(self):
        self._providers = []

    def addActionProvider(self, provider_name):
        self._providers.append(provider_name)

    def listActionProviders(self):
        return self._providers[:]

    def deleteActionProvider(self, provider_name):
        self._providers = [x for x in self._providers if x != provider_name]


class ActionNodeAdapterTests(NodeAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..actions import ActionNodeAdapter

        return ActionNodeAdapter

    def _populate(self, obj):
        obj._setPropValue('title', 'Foo')
        obj._setPropValue('url_expr', 'string:${object_url}/foo')
        obj._setPropValue('available_expr', 'python:1')

    def _verifyImport(self, obj):
        self.assertEqual(type(obj.title), str)
        self.assertEqual(obj.title, 'Foo')
        self.assertEqual(type(obj.description), str)
        self.assertEqual(obj.description, '')
        self.assertEqual(type(obj.url_expr), str)
        self.assertEqual(obj.url_expr, 'string:${object_url}/foo')
        self.assertEqual(type(obj.icon_expr), str)
        self.assertEqual(obj.icon_expr, '')
        self.assertEqual(type(obj.available_expr), str)
        self.assertEqual(obj.available_expr, 'python:1')
        self.assertEqual(type(obj.permissions), tuple)
        self.assertEqual(obj.permissions, ())
        self.assertEqual(type(obj.visible), bool)
        self.assertEqual(obj.visible, True)

    def setUp(self):
        from ...ActionInformation import Action

        self._obj = Action('foo_action')
        self._XML = _ACTION_XML


class ActionCategoryNodeAdapterTests(NodeAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..actions import ActionCategoryNodeAdapter

        return ActionCategoryNodeAdapter

    def _populate(self, obj):
        from ...ActionInformation import Action

        obj._setObject('foo_action', Action('foo_action'))

    def _verifyImport(self, obj):
        self.assertEqual(type(obj.title), str)
        self.assertEqual(obj.title, '')

    def setUp(self):
        from ...ActionInformation import ActionCategory

        self._obj = ActionCategory('foo_category')
        self._XML = _ACTIONCATEGORY_XML


class ActionsToolXMLAdapterTests(BodyAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..actions import ActionsToolXMLAdapter

        return ActionsToolXMLAdapter

    def _populate(self, obj):
        from ...ActionInformation import Action
        from ...ActionInformation import ActionCategory

        obj._setObject('foo_category', ActionCategory('foo_category'))
        obj.action_providers = ('portal_actions',)
        obj.foo_category._setObject('foo_action', Action('foo_action'))
        obj.foo_category.foo_action.i18n_domain = 'foo_domain'

    def _verifyImport(self, obj):
        self.assertEqual(type(obj.action_providers), tuple)
        self.assertEqual(obj.action_providers, ('portal_actions',))
        self.assertEqual(type(obj.action_providers[0]), str)
        self.assertEqual(obj.action_providers[0], 'portal_actions')

    def setUp(self):
        from ...ActionsTool import ActionsTool

        self._obj = ActionsTool('portal_actions')
        self._BODY = _ACTIONSTOOL_BODY
        getSiteManager().registerUtility(self._obj, IActionsTool)


class _ActionSetup(BaseRegistryTests):

    def _initSite(self, foo=2, bar=2):
        site = DummySite('site')
        sm = getSiteManager()
        sm.registerUtility(DummyMembershipTool(), IMembershipTool)
        atool = DummyActionsTool()
        atool.addActionProvider('portal_actions')
        sm.registerUtility(atool, IActionsTool)

        if foo > 0:
            site.portal_foo = DummyTool()

        if foo > 1:
            site.portal_foo.addAction(id='foo',
                                      name='Foo',
                                      action='foo',
                                      condition='python:1',
                                      permission=(),
                                      category='dummy',
                                      visible=1)
            atool.addActionProvider('portal_foo')

        if bar > 0:
            site.portal_bar = DummyTool()

        if bar > 1:
            site.portal_bar.addAction(id='bar',
                                      name='Bar',
                                      action='bar',
                                      condition='python:0',
                                      permission=('Manage portal',),
                                      category='dummy',
                                      visible=0)
            atool.addActionProvider('portal_bar')

        return site, atool


class exportActionProvidersTests(_ActionSetup):

    layer = ExportImportZCMLLayer

    def test_unchanged(self):
        from ..actions import exportActionProviders

        site, _atool = self._initSite(0, 0)
        context = DummyExportContext(site)
        exportActionProviders(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'actions.xml')
        self._compareDOM(text.decode('utf8'), _EMPTY_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_normal(self):
        from ..actions import exportActionProviders

        site, atool = self._initSite()
        # Set up an old action for added difficulty
        atool.addAction(id='baz',
                        name='Baz',
                        action='baz',
                        condition='python:1',
                        permission=(),
                        category='dummy',
                        visible=1)

        context = DummyExportContext(site)
        exportActionProviders(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'actions.xml')
        self._compareDOM(text.decode('utf-8'), _NORMAL_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class importActionProvidersTests(_ActionSetup):

    layer = ExportImportZCMLLayer

    def test_empty_default_purge(self):
        from ..actions import importActionProviders

        site, atool = self._initSite(2, 0)

        self.assertEqual(len(atool.listActionProviders()), 2)
        self.assertTrue('portal_foo' in atool.listActionProviders())
        self.assertTrue('portal_actions' in atool.listActionProviders())

        context = DummyImportContext(site)
        context._files['actions.xml'] = _EMPTY_EXPORT
        importActionProviders(context)

        self.assertEqual(len(atool.listActionProviders()), 1)
        self.assertFalse('portal_foo' in atool.listActionProviders())
        self.assertTrue('portal_actions' in atool.listActionProviders())
        self.assertEqual(len(atool.objectIds()), 0)

    def test_empty_explicit_purge(self):
        from ..actions import importActionProviders

        site, atool = self._initSite(2, 0)

        self.assertEqual(len(atool.listActionProviders()), 2)
        self.assertTrue('portal_foo' in atool.listActionProviders())
        self.assertTrue('portal_actions' in atool.listActionProviders())

        context = DummyImportContext(site, True)
        context._files['actions.xml'] = _EMPTY_EXPORT
        importActionProviders(context)

        self.assertEqual(len(atool.listActionProviders()), 1)
        self.assertFalse('portal_foo' in atool.listActionProviders())
        self.assertTrue('portal_actions' in atool.listActionProviders())
        self.assertEqual(len(atool.objectIds()), 0)

    def test_empty_skip_purge(self):
        from ..actions import importActionProviders

        site, atool = self._initSite(2, 0)

        self.assertEqual(len(atool.listActionProviders()), 2)
        self.assertTrue('portal_foo' in atool.listActionProviders())
        self.assertTrue('portal_actions' in atool.listActionProviders())

        context = DummyImportContext(site, False)
        context._files['actions.xml'] = _EMPTY_EXPORT
        importActionProviders(context)

        self.assertEqual(len(atool.listActionProviders()), 2)
        self.assertTrue('portal_foo' in atool.listActionProviders())
        self.assertTrue('portal_actions' in atool.listActionProviders())

    def test_normal(self):
        from ..actions import exportActionProviders
        from ..actions import importActionProviders

        site, atool = self._initSite(1, 1)
        foo = site.portal_foo
        bar = site.portal_bar

        self.assertEqual(len(atool.listActionProviders()), 1)
        self.assertFalse('portal_foo' in atool.listActionProviders())
        self.assertFalse(foo.listActions())
        self.assertFalse('portal_bar' in atool.listActionProviders())
        self.assertFalse(bar.listActions())
        self.assertTrue('portal_actions' in atool.listActionProviders())

        context = DummyImportContext(site)
        context._files['actions.xml'] = _OLD_EXPORT
        importActionProviders(context)

        self.assertEqual(len(atool.listActionProviders()), 3)
        self.assertTrue('portal_bar' in atool.listActionProviders())
        self.assertTrue('portal_foo' in atool.listActionProviders())
        self.assertTrue('portal_actions' in atool.listActionProviders())

        self.assertEqual(len(atool.objectIds()), 1)
        self.assertTrue('dummy' in atool.objectIds())
        # Only one action appears. The importer only deals with actions
        # defined by the actions tool. Other tools are responsible for
        # exporting/importing actions themselves.
        self.assertEqual(len(atool.dummy.objectIds()), 1)
        self.assertTrue('baz' in atool.dummy.objectIds())
        self.assertFalse(foo.listActions())
        self.assertFalse(bar.listActions())

        # complete the roundtrip
        context = DummyExportContext(site)
        exportActionProviders(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'actions.xml')
        self._compareDOM(text.decode('utf8'), _NEWSYTLE_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_i18n(self):
        from ..actions import exportActionProviders
        from ..actions import importActionProviders

        site, atool = self._initSite(0, 0)

        context = DummyImportContext(site)
        context._files['actions.xml'] = _I18N_IMPORT
        importActionProviders(context)

        self.assertEqual(len(atool.listActionProviders()), 1)
        self.assertEqual(atool.objectIds(), ['dummy'])
        self.assertEqual(atool.dummy.objectIds(), ['foo'])
        self.assertEqual(atool.dummy.foo.i18n_domain, 'foo_domain')

        # complete the roundtrip
        context = DummyExportContext(site)
        exportActionProviders(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'actions.xml')
        self._compareDOM(text.decode('utf8'), _I18N_IMPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_insert_skip_purge(self):
        from ..actions import importActionProviders

        site, atool = self._initSite(0, 0)

        context = DummyImportContext(site)
        context._files['actions.xml'] = _NEWSYTLE_EXPORT
        importActionProviders(context)

        self.assertEqual(len(atool.listActionProviders()), 3)
        self.assertEqual(atool.objectIds(), ['dummy'])
        self.assertEqual(atool.dummy.objectIds(), ['baz'])
        self.assertEqual(atool.dummy.baz.icon_expr, '')

        context = DummyImportContext(site, False)
        context._files['actions.xml'] = _INSERT_IMPORT
        importActionProviders(context)

        self.assertEqual(len(atool.listActionProviders()), 3)
        self.assertEqual(atool.objectIds(), ['dummy'])
        self.assertEqual(atool.dummy.objectIds(), ['spam', 'baz'])
        self.assertEqual(atool.dummy.baz.icon_expr, 'string:baz_icon.png')

    def test_remove_skip_purge(self):
        from ..actions import importActionProviders

        site, atool = self._initSite(2, 2)

        self.assertEqual(atool.listActionProviders(),
                         ['portal_actions', 'portal_foo', 'portal_bar'])

        context = DummyImportContext(site, False)
        context._files['actions.xml'] = _REMOVE_IMPORT
        importActionProviders(context)

        self.assertEqual(atool.listActionProviders(), ['portal_foo'])


def test_suite():
    loadTestsFromTestCase = unittest.defaultTestLoader.loadTestsFromTestCase
    return unittest.TestSuite((
        loadTestsFromTestCase(ActionNodeAdapterTests),
        loadTestsFromTestCase(ActionCategoryNodeAdapterTests),
        loadTestsFromTestCase(ActionsToolXMLAdapterTests),
        loadTestsFromTestCase(exportActionProvidersTests),
        loadTestsFromTestCase(importActionProvidersTests),
    ))
