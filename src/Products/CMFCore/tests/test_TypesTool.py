##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for TypesTool module.
"""

import unittest
import warnings

from AccessControl.Permission import Permission
from zope.component import getSiteManager

from ..interfaces import IWorkflowTool
from ..testing import FunctionalZCMLLayer
from ..utils import HAS_ZSERVER
from .base.testcase import SecurityTest


class TypesToolTests(unittest.TestCase):

    def _getTargetClass(self):
        from ..TypesTool import TypesTool
        return TypesTool

    def _makeOne(self):
        return self._getTargetClass()()

    def test_class_conforms_to_IActionProvider(self):
        from zope.interface.verify import verifyClass

        from ..interfaces import IActionProvider
        verifyClass(IActionProvider, self._getTargetClass())

    def test_instance_conforms_to_IActionProvider(self):
        from zope.interface.verify import verifyObject

        from ..interfaces import IActionProvider
        verifyObject(IActionProvider, self._makeOne())

    def test_class_conforms_to_ITypesTool(self):
        from zope.interface.verify import verifyClass

        from ..interfaces import IActionProvider
        verifyClass(IActionProvider, self._getTargetClass())

    def test_instance_conforms_to_ITypesTool(self):
        from zope.interface.verify import verifyObject

        from ..interfaces import IActionProvider
        verifyObject(IActionProvider, self._makeOne())

    def test_listActions_passes_all_context_information_to_TIs(self):
        from zope.interface import implementer

        from ..interfaces import ITypeInformation
        from .base.dummy import DummyContent

        @implementer(ITypeInformation)
        class ActionTesterTypeInfo:
            id = 'Dummy Content'

            def listActions(self, info=None, obj=None):
                self._action_info = info
                self._action_obj = obj
                return ()

        ti = ActionTesterTypeInfo()
        tool = self._makeOne()
        setattr(tool, 'Dummy Content', ti)

        dummy = DummyContent('dummy')
        tool.listActions('fake_info', dummy)

        self.assertEqual(ti._action_info, 'fake_info')
        self.assertEqual(ti._action_obj, dummy)


class TypesToolFunctionalTests(SecurityTest):

    layer = FunctionalZCMLLayer

    def _getTargetClass(self):
        from ..TypesTool import TypesTool
        return TypesTool

    def _makeOne(self):
        return self._getTargetClass()()

    def _makeSite(self):
        from .base.dummy import DummySite
        from .base.dummy import DummyUserFolder
        site = DummySite('site')
        site.acl_users = DummyUserFolder()
        return site

    def test_allMetaTypes(self):
        # all typeinfo's returned by allMetaTypes can be traversed to.
        from Acquisition import aq_base

        from ..interfaces import ITypeInformation
        if HAS_ZSERVER:
            from webdav.NullResource import NullResource
        else:
            NullResource = object()
        site = self._makeSite().__of__(self.app)
        tool = self._makeOne().__of__(site)
        meta_types = {}
        # Seems we get NullResource if the method couldn't be traverse to
        # so we check for that. If we've got it, something is b0rked.
        for factype in tool.all_meta_types():
            if ITypeInformation not in factype['interfaces']:
                continue
            meta_types[factype['name']] = 1
            act = tool.unrestrictedTraverse(factype['action'])
            self.assertFalse(type(aq_base(act)) is NullResource)

        # Check the ones we're expecting are there
        self.assertTrue('Scriptable Type Information' in meta_types)
        self.assertTrue('Factory-based Type Information' in meta_types)

    def test_constructContent_simple_FTI(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy

        from ..TypesTool import FactoryTypeInformation as FTI
        from .base.dummy import DummyFolder
        from .base.tidata import FTIDATA_DUMMY
        site = self._makeSite().__of__(self.app)
        acl_users = site.acl_users
        setSecurityPolicy(self._oldPolicy)
        newSecurityManager(None, acl_users.all_powerful_Oz)
        tool = self._makeOne().__of__(site)
        fti = FTIDATA_DUMMY[0].copy()
        tool._setObject('Dummy Content', FTI(**fti))
        folder = DummyFolder(id='folder', fake_product=1).__of__(site)

        tool.constructContent('Dummy Content', container=folder, id='page1')

        self.assertEqual(folder.page1.portal_type, 'Dummy Content')

    def test_constructContent_FTI_w_wftool_no_workflows(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy

        from ..TypesTool import FactoryTypeInformation as FTI
        from .base.dummy import DummyFolder
        from .base.tidata import FTIDATA_DUMMY
        site = self._makeSite().__of__(self.app)
        acl_users = site.acl_users
        setSecurityPolicy(self._oldPolicy)
        newSecurityManager(None, acl_users.all_powerful_Oz)
        tool = self._makeOne().__of__(site)
        fti = FTIDATA_DUMMY[0].copy()
        tool._setObject('Dummy Content', FTI(**fti))
        folder = DummyFolder(id='folder', fake_product=1).__of__(site)
        tool.portal_workflow = DummyWorkflowTool()

        tool.constructContent('Dummy Content', container=folder, id='page1')

        self.assertEqual(folder.page1.portal_type, 'Dummy Content')

    def test_constructContent_FTI_w_wftool_w_workflow_no_guard(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy

        from ..TypesTool import FactoryTypeInformation as FTI
        from .base.dummy import DummyFolder
        from .base.tidata import FTIDATA_DUMMY
        site = self._makeSite().__of__(self.app)
        acl_users = site.acl_users
        setSecurityPolicy(self._oldPolicy)
        newSecurityManager(None, acl_users.all_powerful_Oz)
        tool = self._makeOne().__of__(site)
        fti = FTIDATA_DUMMY[0].copy()
        tool._setObject('Dummy Content', FTI(**fti))
        folder = DummyFolder(id='folder', fake_product=1).__of__(site)
        tool.portal_workflow = DummyWorkflowTool(object())

        tool.constructContent('Dummy Content', container=folder, id='page1')

        self.assertEqual(folder.page1.portal_type, 'Dummy Content')

    def test_constructContent_FTI_w_wftool_w_workflow_w_guard_allows(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy

        from ..TypesTool import FactoryTypeInformation as FTI
        from .base.dummy import DummyFolder
        from .base.tidata import FTIDATA_DUMMY
        site = self._makeSite().__of__(self.app)
        acl_users = site.acl_users
        setSecurityPolicy(self._oldPolicy)
        newSecurityManager(None, acl_users.all_powerful_Oz)
        tool = self._makeOne().__of__(site)
        fti = FTIDATA_DUMMY[0].copy()
        tool._setObject('Dummy Content', FTI(**fti))
        folder = DummyFolder(id='folder', fake_product=1).__of__(site)
        tool.portal_workflow = DummyWorkflowTool(DummyWorkflow(True))

        tool.constructContent('Dummy Content', container=folder, id='page1')

        self.assertEqual(folder.page1.portal_type, 'Dummy Content')

    def test_constructContent_FTI_w_wftool_w_workflow_w_guard_denies(self):
        from AccessControl import Unauthorized
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy

        from ..TypesTool import FactoryTypeInformation as FTI
        from .base.dummy import DummyFolder
        from .base.tidata import FTIDATA_DUMMY
        site = self._makeSite().__of__(self.app)
        acl_users = site.acl_users
        setSecurityPolicy(self._oldPolicy)
        newSecurityManager(None, acl_users.all_powerful_Oz)
        tool = self._makeOne().__of__(site)
        fti = FTIDATA_DUMMY[0].copy()
        tool._setObject('Dummy Content', FTI(**fti))
        folder = DummyFolder(id='folder', fake_product=1).__of__(site)
        tool.portal_workflow = DummyWorkflowTool(DummyWorkflow(False))
        getSiteManager().registerUtility(tool.portal_workflow, IWorkflowTool)

        self.assertRaises(Unauthorized,
                          tool.constructContent,
                          'Dummy Content', container=folder, id='page1')

        getSiteManager().unregisterUtility(provided=IWorkflowTool)

    def test_constructContent_simple_STI(self):
        from AccessControl import Unauthorized
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy

        from Products.PythonScripts.PythonScript import PythonScript

        from ..PortalFolder import PortalFolder
        from ..TypesTool import ScriptableTypeInformation as STI
        from .base.dummy import DummyFactoryDispatcher
        from .base.tidata import STI_SCRIPT
        site = self._makeSite().__of__(self.app)
        acl_users = site.acl_users
        setSecurityPolicy(self._oldPolicy)
        newSecurityManager(None, acl_users.all_powerful_Oz)
        tool = self._makeOne().__of__(site)
        sti_baz = STI('Baz',
                      permission='Add portal content',
                      constructor_path='addBaz')
        tool._setObject('Baz', sti_baz)
        script = PythonScript('addBaz')
        script.write(STI_SCRIPT)
        tool._setObject('addBaz', script)
        folder = site._setObject('folder', PortalFolder(id='folder'))
        folder.manage_addProduct = {'FooProduct':
                                    DummyFactoryDispatcher(folder)}
        folder._owner = (['acl_users'], 'user_foo')
        self.assertEqual(folder.getOwner(), acl_users.user_foo)

        try:
            tool.constructContent('Baz', container=folder, id='page2')
        except Unauthorized:
            self.fail('CMF Collector issue #165 (Ownership bug): '
                      'Unauthorized raised')

        self.assertEqual(folder.page2.portal_type, 'Baz')


class TypeInfoTests:
    # Subclass must define _getTargetClass

    def _makeOne(self, id='test', **kw):
        return self._getTargetClass()(id, **kw)

    def _makeTypesTool(self):
        from ..TypesTool import TypesTool

        return TypesTool()

    def test_class_conforms_to_ITypeInformation(self):
        from zope.interface.verify import verifyClass

        from ..interfaces import ITypeInformation
        verifyClass(ITypeInformation, self._getTargetClass())

    def test_instance_conforms_to_ITypeInformation(self):
        from zope.interface.verify import verifyObject

        from ..interfaces import ITypeInformation
        verifyObject(ITypeInformation, self._makeOne())

    def test_construction(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            ti = self._makeOne('Foo', description='Description',
                               meta_type='Foo', icon='foo.gif')
        self.assertEqual(ti.getId(), 'Foo')
        self.assertEqual(ti.Title(), 'Foo')
        self.assertEqual(ti.Description(), 'Description')
        self.assertEqual(ti.Metatype(), 'Foo')
        self.assertEqual(ti.getIconExprObject().text,
                         'string:${portal_url}/foo.gif')

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.assertEqual(ti.getIcon(), 'foo.gif')
        self.assertEqual(ti.immediate_view, '')

        ti = self._makeOne('Foo', immediate_view='foo_view')
        self.assertEqual(ti.immediate_view, 'foo_view')

    def _makeAndSetInstance(self, id, **kw):
        tool = self.tool
        t = self._makeOne(id, **kw)
        tool._setObject(id, t)
        return tool[id]

    def test_allowType(self):
        self.tool = self._makeTypesTool()
        ti = self._makeAndSetInstance('Foo')
        self.assertFalse(ti.allowType('Foo'))
        self.assertFalse(ti.allowType('Bar'))

        ti = self._makeAndSetInstance('Foo2', allowed_content_types=('Bar',))
        self.assertTrue(ti.allowType('Bar'))

        ti = self._makeAndSetInstance('Foo3', filter_content_types=0)
        self.assertTrue(ti.allowType('Foo3'))

    def test_GlobalHide(self):
        self.tool = self._makeTypesTool()
        tnf = self._makeAndSetInstance('Folder', filter_content_types=0)
        taf = self._makeAndSetInstance('Allowing Folder',
                                       allowed_content_types=('Hidden',
                                                              'Not Hidden'))
        self._makeAndSetInstance('Hidden', global_allow=0)
        self._makeAndSetInstance('Not Hidden')
        # make sure we're normally hidden but everything else is visible
        self.assertFalse(tnf.allowType('Hidden'))
        self.assertTrue(tnf.allowType('Not Hidden'))
        # make sure we're available where we should be
        self.assertTrue(taf.allowType('Hidden'))
        self.assertTrue(taf.allowType('Not Hidden'))
        # make sure we're available in a non-content-type-filtered type
        # where we have been explicitly allowed
        taf2 = self._makeAndSetInstance('Allowing Folder2',
                                        allowed_content_types=('Hidden',
                                                               'Not Hidden'),
                                        filter_content_types=0)
        self.assertTrue(taf2.allowType('Hidden'))
        self.assertTrue(taf2.allowType('Not Hidden'))

    def test_allowDiscussion(self):
        ti = self._makeOne('Foo')
        self.assertFalse(ti.allowDiscussion())

        ti = self._makeOne('Foo', allow_discussion=1)
        self.assertTrue(ti.allowDiscussion())

    def test_listActions(self):
        from .base.tidata import FTIDATA_ACTIONS
        ti = self._makeOne('Foo')
        self.assertFalse(ti.listActions())

        ti = self._makeOne(**FTIDATA_ACTIONS[0])
        actions = ti.listActions()
        self.assertTrue(actions)

        ids = [x.getId() for x in actions]
        self.assertTrue('view' in ids)
        self.assertTrue('edit' in ids)
        self.assertTrue('objectproperties' in ids)
        self.assertTrue('slot' in ids)

        names = [x.Title() for x in actions]
        self.assertTrue('View' in names)
        self.assertTrue('Edit' in names)
        self.assertTrue('Object Properties' in names)
        self.assertFalse('slot' in names)
        self.assertTrue('Slot' in names)

        visible = [x.getId() for x in actions if x.getVisibility()]
        self.assertTrue('view' in visible)
        self.assertTrue('edit' in visible)
        self.assertTrue('objectproperties' in visible)
        self.assertFalse('slot' in visible)

    def test_MethodAliases_methods(self):
        from .base.tidata import FTIDATA_CMF
        ti = self._makeOne(**FTIDATA_CMF[0])
        self.assertEqual(ti.getMethodAliases(), FTIDATA_CMF[0]['aliases'])
        self.assertEqual(ti.queryMethodID('view'), 'dummy_view')

        ti.setMethodAliases(ti.getMethodAliases())
        self.assertEqual(ti.getMethodAliases(), FTIDATA_CMF[0]['aliases'])

    def test_getInfoData(self):
        ti_data = {'id': 'foo',
                   'title': 'Foo',
                   'description': 'Foo objects are just used for testing.',
                   'content_meta_type': 'Foo Content',
                   'factory': 'cmf.foo',
                   'icon_expr': 'string:${portal_url}/foo_icon_expr.gif',
                   'add_view_expr': 'string:${folder_url}/foo_add_view',
                   'link_target': '_new'}
        ti = self._makeOne(**ti_data)
        info_data = ti.getInfoData()
        self.assertEqual(len(info_data), 2)

        self.assertEqual(len(info_data[0]), 10)
        self.assertEqual(info_data[0]['id'], ti_data['id'])
        self.assertEqual(info_data[0]['category'], 'folder/add')
        self.assertEqual(info_data[0]['title'], ti_data['title'])
        self.assertEqual(info_data[0]['description'], ti_data['description'])
        self.assertEqual(info_data[0]['url'].text,
                         'string:${folder_url}/foo_add_view')
        self.assertEqual(info_data[0]['icon'].text,
                         'string:${portal_url}/foo_icon_expr.gif')
        self.assertEqual(info_data[0]['visible'], True)
        self.assertEqual(info_data[0]['available'], ti._checkAvailable)
        self.assertEqual(info_data[0]['allowed'], ti._checkAllowed)
        self.assertEqual(info_data[0]['link_target'], ti.link_target)

        self.assertEqual(set(info_data[1]),
                         {'url', 'icon', 'available', 'allowed'})

    def test_getInfoData_without_urls(self):
        ti_data = {'id': 'foo',
                   'title': 'Foo',
                   'description': 'Foo objects are just used for testing.',
                   'content_meta_type': 'Foo Content',
                   'factory': 'cmf.foo'}
        ti = self._makeOne(**ti_data)
        info_data = ti.getInfoData()
        self.assertEqual(len(info_data), 2)

        self.assertEqual(len(info_data[0]), 10)
        self.assertEqual(info_data[0]['id'], ti_data['id'])
        self.assertEqual(info_data[0]['category'], 'folder/add')
        self.assertEqual(info_data[0]['title'], ti_data['title'])
        self.assertEqual(info_data[0]['description'], ti_data['description'])
        self.assertEqual(info_data[0]['url'], '')
        self.assertEqual(info_data[0]['icon'], '')
        self.assertEqual(info_data[0]['visible'], True)
        self.assertEqual(info_data[0]['available'], ti._checkAvailable)
        self.assertEqual(info_data[0]['allowed'], ti._checkAllowed)
        self.assertEqual(info_data[0]['link_target'], None)

        self.assertEqual(set(info_data[1]), {'available', 'allowed'})

    def _checkContentTI(self, ti):
        from ..ActionInformation import ActionInformation
        wanted_aliases = {'view': 'dummy_view', '(Default)': 'dummy_view'}
        wanted_actions_text0 = 'string:${object_url}/dummy_view'
        wanted_actions_text1 = 'string:${object_url}/dummy_edit_form'
        wanted_actions_text2 = 'string:${object_url}/metadata_edit_form'

        self.assertTrue(isinstance(ti._actions[0], ActionInformation))
        self.assertEqual(len(ti._actions), 3)
        self.assertEqual(ti._aliases, wanted_aliases)
        self.assertEqual(ti._actions[0].action.text, wanted_actions_text0)
        self.assertEqual(ti._actions[1].action.text, wanted_actions_text1)
        self.assertEqual(ti._actions[2].action.text, wanted_actions_text2)

        action0 = ti._actions[0]
        self.assertEqual(action0.getId(), 'view')
        self.assertEqual(action0.Title(), 'View')
        self.assertEqual(action0.getActionExpression(), wanted_actions_text0)
        self.assertEqual(action0.getCondition(), '')
        self.assertEqual(action0.getPermissions(), ('View',))
        self.assertEqual(action0.getCategory(), 'object')
        self.assertEqual(action0.getVisibility(), 1)

    def _checkFolderTI(self, ti):
        from ..ActionInformation import ActionInformation
        wanted_aliases = {'view': '(Default)'}
        wanted_actions_text0 = 'string:${object_url}'
        wanted_actions_text1 = 'string:${object_url}/dummy_edit_form'
        wanted_actions_text2 = 'string:${object_url}/folder_localrole_form'

        self.assertTrue(isinstance(ti._actions[0], ActionInformation))
        self.assertEqual(len(ti._actions), 3)
        self.assertEqual(ti._aliases, wanted_aliases)
        self.assertEqual(ti._actions[0].action.text, wanted_actions_text0)
        self.assertEqual(ti._actions[1].action.text, wanted_actions_text1)
        self.assertEqual(ti._actions[2].action.text, wanted_actions_text2)

    def test_clearExprObjects(self):
        """When a *_expr property is set, a *_expr_object attribute is
        also set which should also be cleared when the *_expr is
        cleared."""
        ti_data = {'id': 'foo',
                   'title': 'Foo',
                   'description': 'Foo objects are just used for testing.',
                   'content_meta_type': 'Foo Content',
                   'factory': 'cmf.foo',
                   'icon_expr': 'string:${portal_url}/foo_icon_expr.gif',
                   'add_view_expr': 'string:${folder_url}/foo_add_view',
                   'link_target': '_new'}
        ti = self._makeOne(**ti_data)
        info_data = ti.getInfoData()
        self.assertTrue(hasattr(ti, 'icon_expr_object'))
        self.assertTrue(info_data[0].get('icon'))
        self.assertTrue('icon' in info_data[1])
        self.assertTrue(hasattr(ti, 'add_view_expr_object'))
        self.assertTrue(info_data[0].get('url'))
        self.assertTrue('url' in info_data[1])
        ti.manage_changeProperties(icon_expr='', add_view_expr='')
        info_data = ti.getInfoData()
        self.assertFalse(hasattr(ti, 'icon_expr_object'))
        self.assertFalse(info_data[0].get('icon'))
        self.assertFalse('icon' in info_data[1])
        self.assertFalse(hasattr(ti, 'add_view_expr_object'))
        self.assertFalse(info_data[0].get('url'))
        self.assertFalse('url' in info_data[1])


class FTIDataTests(TypeInfoTests, unittest.TestCase):

    def _getTargetClass(self):
        from ..TypesTool import FactoryTypeInformation
        return FactoryTypeInformation

    def test_properties(self):
        ti = self._makeOne('Foo')
        self.assertEqual(ti.product, '')
        self.assertEqual(ti.factory, '')

        ti = self._makeOne('Foo', product='FooProduct', factory='addFoo')
        self.assertEqual(ti.product, 'FooProduct')
        self.assertEqual(ti.factory, 'addFoo')


class STIDataTests(TypeInfoTests, unittest.TestCase):

    def _getTargetClass(self):
        from ..TypesTool import ScriptableTypeInformation
        return ScriptableTypeInformation

    def test_properties(self):
        ti = self._makeOne('Foo')
        self.assertEqual(ti.permission, '')
        self.assertEqual(ti.constructor_path, '')

        ti = self._makeOne('Foo', permission='Add Foos',
                           constructor_path='foo_add')
        self.assertEqual(ti.permission, 'Add Foos')
        self.assertEqual(ti.constructor_path, 'foo_add')


class FTIConstructionTestCase:

    def _getTargetClass(self):
        from ..TypesTool import FactoryTypeInformation
        return FactoryTypeInformation

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_isConstructionAllowed_wo_Container(self):
        self.assertFalse(self.ti.isConstructionAllowed(None))

    def test_isConstructionAllowed_wo_ProductFactory(self):
        ti = self._makeOne('foo')
        self.assertFalse(ti.isConstructionAllowed(self.f))

    def test_isConstructionAllowed_wo_Security(self):
        from AccessControl.SecurityManagement import noSecurityManager
        noSecurityManager()
        self.assertFalse(self.ti.isConstructionAllowed(self.f))

    def test_isConstructionAllowed_for_Omnipotent(self):
        from AccessControl.SecurityManagement import newSecurityManager

        from .base.security import OmnipotentUser
        newSecurityManager(None, OmnipotentUser().__of__(self.f))
        self.assertTrue(self.ti.isConstructionAllowed(self.f))

    def test_isConstructionAllowed_w_Role(self):
        self.assertTrue(self.ti.isConstructionAllowed(self.f))

    def test_isConstructionAllowed_wo_Role(self):
        from AccessControl.SecurityManagement import newSecurityManager

        from .base.security import UserWithRoles
        newSecurityManager(None, UserWithRoles('FooViewer').__of__(self.f))
        self.assertFalse(self.ti.isConstructionAllowed(self.f))

    def test_isConstructionAllowed_w_all_meta_types_not_callable(self):
        self.f.all_meta_types = ({'name': 'Dummy', 'permission': 'addFoo'},)
        self.assertTrue(self.ti.isConstructionAllowed(self.f))

    def test_constructInstance_wo_Roles(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.unauthorized import Unauthorized

        from .base.security import UserWithRoles
        newSecurityManager(None, UserWithRoles('FooViewer').__of__(self.f))
        self.assertRaises(Unauthorized,
                          self.ti.constructInstance, self.f, 'foo')

    def test_constructInstance(self):
        self.ti.constructInstance(self.f, 'foo')
        foo = self.f._getOb('foo')
        self.assertEqual(foo.id, 'foo')

    def test_constructInstance_private(self):
        from AccessControl.SecurityManagement import newSecurityManager

        from .base.security import UserWithRoles
        newSecurityManager(None, UserWithRoles('NotAFooAdder').__of__(self.f))
        self.ti._constructInstance(self.f, 'foo')
        foo = self.f._getOb('foo')
        self.assertEqual(foo.id, 'foo')

    def test_constructInstance_w_args_kw(self):
        self.ti.constructInstance(self.f, 'bar', 0, 1)
        bar = self.f._getOb('bar')
        self.assertEqual(bar.id, 'bar')
        self.assertEqual(bar._args, (0, 1))

        self.ti.constructInstance(self.f, 'baz', frickle='natz')
        baz = self.f._getOb('baz')
        self.assertEqual(baz.id, 'baz')
        self.assertEqual(baz._kw['frickle'], 'natz')

        self.ti.constructInstance(self.f, 'bam', 0, 1, frickle='natz')
        bam = self.f._getOb('bam')
        self.assertEqual(bam.id, 'bam')
        self.assertEqual(bam._args, (0, 1))
        self.assertEqual(bam._kw['frickle'], 'natz')


class FTIOldstyleConstructionTests(FTIConstructionTestCase, unittest.TestCase):

    def setUp(self):
        from AccessControl.SecurityManagement import newSecurityManager

        from .base.dummy import DummyFolder
        from .base.security import UserWithRoles

        self.f = DummyFolder(fake_product=1)
        Permission('addFoo', (), self.f).setRoles(('Manager', 'FooAdder'))
        self.ti = self._makeOne('Foo', product='FooProduct', factory='addFoo')
        newSecurityManager(None, UserWithRoles('FooAdder').__of__(self.f))

    def tearDown(self):
        from AccessControl.SecurityManagement import noSecurityManager
        from zope.testing.cleanup import cleanUp

        cleanUp()
        noSecurityManager()

    def test_constructInstance_w_id_munge(self):
        self.f._prefix = 'majyk'
        self.ti.constructInstance(self.f, 'dust')
        majyk_dust = self.f._getOb('majyk_dust')
        self.assertEqual(majyk_dust.id, 'majyk_dust')

    def test_events(self):
        from OFS.interfaces import IObjectWillBeAddedEvent
        from zope.component import adapter
        from zope.component import provideHandler
        from zope.container.interfaces import IContainerModifiedEvent
        from zope.lifecycleevent.interfaces import IObjectAddedEvent
        from zope.lifecycleevent.interfaces import IObjectCreatedEvent
        events = []

        @adapter(IObjectCreatedEvent)
        def _handleObjectCreated(event):
            events.append(event)
        provideHandler(_handleObjectCreated)

        @adapter(IObjectWillBeAddedEvent)
        def _handleObjectWillBeAdded(event):
            events.append(event)
        provideHandler(_handleObjectWillBeAdded)

        @adapter(IObjectAddedEvent)
        def _handleObjectAdded(event):
            events.append(event)
        provideHandler(_handleObjectAdded)

        @adapter(IContainerModifiedEvent)
        def _handleContainerModified(event):
            events.append(event)
        provideHandler(_handleContainerModified)

        self.ti.constructInstance(self.f, 'foo')
        self.assertEqual(len(events), 3)

        evt = events[0]
        self.assertTrue(IObjectCreatedEvent.providedBy(evt))
        self.assertEqual(evt.object, self.f.foo)

        evt = events[1]
        self.assertTrue(IObjectAddedEvent.providedBy(evt))
        self.assertEqual(evt.object, self.f.foo)
        self.assertEqual(evt.oldParent, None)
        self.assertEqual(evt.oldName, None)
        self.assertEqual(evt.newParent, self.f)
        self.assertEqual(evt.newName, 'foo')

        evt = events[2]
        self.assertTrue(IContainerModifiedEvent.providedBy(evt))
        self.assertEqual(evt.object, self.f)


class FTINewstyleConstructionTests(FTIConstructionTestCase, SecurityTest):

    def setUp(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from zope.component.interfaces import IFactory

        from .base.dummy import DummyFactory
        from .base.dummy import DummyFolder
        from .base.security import UserWithRoles

        SecurityTest.setUp(self)
        sm = getSiteManager()
        sm.registerUtility(DummyFactory, IFactory, 'test.dummy')

        self.f = DummyFolder()
        Permission('addFoo', (), self.f).setRoles(('Manager', 'FooAdder'))
        self.ti = self._makeOne('Foo', meta_type='Dummy',
                                factory='test.dummy')
        newSecurityManager(None, UserWithRoles('FooAdder').__of__(self.f))

    def tearDown(self):
        from zope.testing.cleanup import cleanUp

        cleanUp()
        SecurityTest.tearDown(self)

    def test_events(self):
        from OFS.interfaces import IObjectWillBeAddedEvent
        from zope.component import adapter
        from zope.component import provideHandler
        from zope.container.interfaces import IContainerModifiedEvent
        from zope.lifecycleevent.interfaces import IObjectAddedEvent
        from zope.lifecycleevent.interfaces import IObjectCreatedEvent
        events = []

        @adapter(IObjectCreatedEvent)
        def _handleObjectCreated(event):
            events.append(event)
        provideHandler(_handleObjectCreated)

        @adapter(IObjectWillBeAddedEvent)
        def _handleObjectWillBeAdded(event):
            events.append(event)
        provideHandler(_handleObjectWillBeAdded)

        @adapter(IObjectAddedEvent)
        def _handleObjectAdded(event):
            events.append(event)
        provideHandler(_handleObjectAdded)

        @adapter(IContainerModifiedEvent)
        def _handleContainerModified(event):
            events.append(event)
        provideHandler(_handleContainerModified)

        self.ti.constructInstance(self.f, 'foo')
        self.assertEqual(len(events), 4)

        evt = events[0]
        self.assertTrue(IObjectCreatedEvent.providedBy(evt))
        self.assertEqual(evt.object, self.f.foo)

        evt = events[1]
        self.assertTrue(IObjectWillBeAddedEvent.providedBy(evt))
        self.assertEqual(evt.object, self.f.foo)
        self.assertEqual(evt.oldParent, None)
        self.assertEqual(evt.oldName, None)
        self.assertEqual(evt.newParent, self.f)
        self.assertEqual(evt.newName, 'foo')

        evt = events[2]
        self.assertTrue(IObjectAddedEvent.providedBy(evt))
        self.assertEqual(evt.object, self.f.foo)
        self.assertEqual(evt.oldParent, None)
        self.assertEqual(evt.oldName, None)
        self.assertEqual(evt.newParent, self.f)
        self.assertEqual(evt.newName, 'foo')

        evt = events[3]
        self.assertTrue(IContainerModifiedEvent.providedBy(evt))
        self.assertEqual(evt.object, self.f)


class DummyWorkflowTool:

    def __init__(self, *workflows):
        self._workflows = workflows

    def getWorkflowsFor(self, type_id):
        return self._workflows


class DummyWorkflow:

    def __init__(self, allow):
        self._allow = allow

    def allowCreate(self, container, type_id):
        return self._allow


def test_suite():
    loadTestsFromTestCase = unittest.defaultTestLoader.loadTestsFromTestCase
    return unittest.TestSuite((
        loadTestsFromTestCase(TypesToolTests),
        loadTestsFromTestCase(TypesToolFunctionalTests),
        loadTestsFromTestCase(FTIDataTests),
        loadTestsFromTestCase(STIDataTests),
        loadTestsFromTestCase(FTIOldstyleConstructionTests),
        loadTestsFromTestCase(FTINewstyleConstructionTests),
    ))
