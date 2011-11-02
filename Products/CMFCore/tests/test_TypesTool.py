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
""" Unit tests for TypesTool module. """

import unittest

from Products.CMFCore.testing import FunctionalZCMLLayer
from Products.CMFCore.tests.base.testcase import SecurityTest
from Products.CMFCore.tests.base.testcase import WarningInterceptor

class TypesToolTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.CMFCore.TypesTool import TypesTool
        return TypesTool

    def _makeOne(self):
        return self._getTargetClass()()

    def test_class_conforms_to_IActionProvider(self):
        from zope.interface.verify import verifyClass
        from Products.CMFCore.interfaces import IActionProvider
        verifyClass(IActionProvider, self._getTargetClass())

    def test_instance_conforms_to_IActionProvider(self):
        from zope.interface.verify import verifyObject
        from Products.CMFCore.interfaces import IActionProvider
        verifyObject(IActionProvider, self._makeOne())

    def test_class_conforms_to_ITypesTool(self):
        from zope.interface.verify import verifyClass
        from Products.CMFCore.interfaces import IActionProvider
        verifyClass(IActionProvider, self._getTargetClass())

    def test_instance_conforms_to_ITypesTool(self):
        from zope.interface.verify import verifyObject
        from Products.CMFCore.interfaces import IActionProvider
        verifyObject(IActionProvider, self._makeOne())

    def test_listActions_passes_all_context_information_to_TIs(self):
        from zope.interface import implements
        from Products.CMFCore.interfaces import ITypeInformation
        from Products.CMFCore.tests.base.dummy import DummyContent

        class ActionTesterTypeInfo:
            implements(ITypeInformation)
            id = 'Dummy Content'

            def listActions(self, info=None, obj=None):
                self._action_info = info
                self._action_obj = obj
                return ()

        ti = ActionTesterTypeInfo()
        tool = self._makeOne()
        setattr( tool, 'Dummy Content', ti )

        dummy = DummyContent('dummy')
        tool.listActions('fake_info', dummy)

        self.assertEqual(ti._action_info, 'fake_info')
        self.assertEqual(ti._action_obj, dummy)

class TypesToolFunctionalTests(SecurityTest):

    layer = FunctionalZCMLLayer

    def _getTargetClass(self):
        from Products.CMFCore.TypesTool import TypesTool
        return TypesTool

    def _makeOne(self):
        return self._getTargetClass()()

    def _makeSite(self):
        from Products.CMFCore.tests.base.dummy import DummySite
        from Products.CMFCore.tests.base.dummy import DummyUserFolder
        site = DummySite('site')
        site.acl_users = DummyUserFolder()
        return site

    def test_allMetaTypes(self):
        # everything returned by allMetaTypes can be traversed to.
        from Acquisition import aq_base
        from Products.PythonScripts.standard import html_quote
        from webdav.NullResource import NullResource
        site = self._makeSite().__of__(self.root)
        tool = self._makeOne().__of__(site)
        meta_types = {}
        # Seems we get NullResource if the method couldn't be traverse to
        # so we check for that. If we've got it, something is b0rked.
        for factype in tool.all_meta_types():
            meta_types[factype['name']]=1
            # The html_quote below is necessary 'cos of the one in
            # main.dtml. Could be removed once that is gone.
            act = tool.unrestrictedTraverse(html_quote(factype['action']))
            self.failIf(type(aq_base(act)) is NullResource)

        # Check the ones we're expecting are there
        self.failUnless(meta_types.has_key('Scriptable Type Information'))
        self.failUnless(meta_types.has_key('Factory-based Type Information'))

    def test_constructContent_simple_FTI(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy
        from Products.CMFCore.TypesTool import FactoryTypeInformation as FTI
        from Products.CMFCore.tests.base.dummy import DummyFolder
        from Products.CMFCore.tests.base.tidata import FTIDATA_DUMMY
        site = self._makeSite().__of__(self.root)
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
        from Products.CMFCore.TypesTool import FactoryTypeInformation as FTI
        from Products.CMFCore.tests.base.dummy import DummyFolder
        from Products.CMFCore.tests.base.tidata import FTIDATA_DUMMY
        site = self._makeSite().__of__(self.root)
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
        from Products.CMFCore.TypesTool import FactoryTypeInformation as FTI
        from Products.CMFCore.tests.base.dummy import DummyFolder
        from Products.CMFCore.tests.base.tidata import FTIDATA_DUMMY
        site = self._makeSite().__of__(self.root)
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
        from Products.CMFCore.TypesTool import FactoryTypeInformation as FTI
        from Products.CMFCore.tests.base.dummy import DummyFolder
        from Products.CMFCore.tests.base.tidata import FTIDATA_DUMMY
        site = self._makeSite().__of__(self.root)
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
        from Products.CMFCore.TypesTool import FactoryTypeInformation as FTI
        from Products.CMFCore.tests.base.dummy import DummyFolder
        from Products.CMFCore.tests.base.tidata import FTIDATA_DUMMY
        site = self._makeSite().__of__(self.root)
        acl_users = site.acl_users
        setSecurityPolicy(self._oldPolicy)
        newSecurityManager(None, acl_users.all_powerful_Oz)
        tool = self._makeOne().__of__(site)
        fti = FTIDATA_DUMMY[0].copy()
        tool._setObject('Dummy Content', FTI(**fti))
        folder = DummyFolder(id='folder', fake_product=1).__of__(site)
        tool.portal_workflow = DummyWorkflowTool(DummyWorkflow(False))

        self.assertRaises(Unauthorized,
                          tool.constructContent,
                          'Dummy Content', container=folder, id='page1')

    def test_constructContent_simple_STI(self):
        from AccessControl import Unauthorized
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy
        from Products.CMFCore.PortalFolder import PortalFolder
        from Products.CMFCore.TypesTool \
                import ScriptableTypeInformation as STI
        from Products.CMFCore.tests.base.dummy import DummyFactoryDispatcher
        from Products.CMFCore.tests.base.tidata import STI_SCRIPT
        from Products.PythonScripts.PythonScript import PythonScript
        site = self._makeSite().__of__(self.root)
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
        tool._setObject('addBaz',  script)
        folder = site._setObject( 'folder', PortalFolder(id='folder') )
        folder.manage_addProduct = {'FooProduct':
                                        DummyFactoryDispatcher(folder) }
        folder._owner = (['acl_users'], 'user_foo')
        self.assertEqual( folder.getOwner(), acl_users.user_foo )

        try:
            tool.constructContent('Baz', container=folder, id='page2')
        except Unauthorized:
            self.fail('CMF Collector issue #165 (Ownership bug): '
                      'Unauthorized raised' )

        self.assertEqual(folder.page2.portal_type, 'Baz')


class TypeInfoTests(WarningInterceptor):
    # Subclass must define _getTargetClass

    def setUp(self):
        self._trap_warning_output()

    def tearDown(self):
        self._free_warning_output()

    def _makeOne(self, id='test', **kw):
        return self._getTargetClass()(id, **kw)

    def _makeTypesTool(self):
        from Products.CMFCore.TypesTool import TypesTool

        return TypesTool()

    def test_class_conforms_to_ITypeInformation(self):
        from zope.interface.verify import verifyClass
        from Products.CMFCore.interfaces import ITypeInformation
        verifyClass(ITypeInformation, self._getTargetClass())

    def test_instance_conforms_to_ITypeInformation(self):
        from zope.interface.verify import verifyObject
        from Products.CMFCore.interfaces import ITypeInformation
        verifyObject(ITypeInformation, self._makeOne())

    def test_construction(self):
        ti = self._makeOne('Foo', description='Description', meta_type='Foo',
                           icon='foo.gif')
        self.assertEqual( ti.getId(), 'Foo' )
        self.assertEqual( ti.Title(), 'Foo' )
        self.assertEqual( ti.Description(), 'Description' )
        self.assertEqual( ti.Metatype(), 'Foo' )
        self.assertEqual( ti.getIconExprObject().text,
                          'string:${portal_url}/foo.gif' )
        self.assertEqual( ti.getIcon(), 'foo.gif' )
        self.assertEqual( ti.immediate_view, '' )

        ti = self._makeOne('Foo', immediate_view='foo_view')
        self.assertEqual( ti.immediate_view, 'foo_view' )

    def _makeAndSetInstance(self, id, **kw):
        tool = self.tool
        t = self._makeOne(id, **kw)
        tool._setObject(id,t)
        return tool[id]

    def test_allowType( self ):
        self.tool = self._makeTypesTool()
        ti = self._makeAndSetInstance( 'Foo' )
        self.failIf( ti.allowType( 'Foo' ) )
        self.failIf( ti.allowType( 'Bar' ) )

        ti = self._makeAndSetInstance( 'Foo2', allowed_content_types=( 'Bar', ) )
        self.failUnless( ti.allowType( 'Bar' ) )

        ti = self._makeAndSetInstance( 'Foo3', filter_content_types=0 )
        self.failUnless( ti.allowType( 'Foo3' ) )

    def test_GlobalHide( self ):
        self.tool = self._makeTypesTool()
        tnf = self._makeAndSetInstance( 'Folder', filter_content_types=0)
        taf = self._makeAndSetInstance( 'Allowing Folder'
                                      , allowed_content_types=( 'Hidden'
                                                              ,'Not Hidden'))
        tih = self._makeAndSetInstance( 'Hidden', global_allow=0)
        tnh = self._makeAndSetInstance( 'Not Hidden')
        # make sure we're normally hidden but everything else is visible
        self.failIf     ( tnf.allowType( 'Hidden' ) )
        self.failUnless ( tnf.allowType( 'Not Hidden') )
        # make sure we're available where we should be
        self.failUnless ( taf.allowType( 'Hidden' ) )
        self.failUnless ( taf.allowType( 'Not Hidden') )
        # make sure we're available in a non-content-type-filtered type
        # where we have been explicitly allowed
        taf2 = self._makeAndSetInstance( 'Allowing Folder2'
                                       , allowed_content_types=( 'Hidden'
                                                               , 'Not Hidden'
                                                               )
                                       , filter_content_types=0
                                       )
        self.failUnless ( taf2.allowType( 'Hidden' ) )
        self.failUnless ( taf2.allowType( 'Not Hidden') )

    def test_allowDiscussion( self ):
        ti = self._makeOne( 'Foo' )
        self.failIf( ti.allowDiscussion() )

        ti = self._makeOne( 'Foo', allow_discussion=1 )
        self.failUnless( ti.allowDiscussion() )

    def test_listActions( self ):
        from Products.CMFCore.tests.base.tidata import FTIDATA_ACTIONS
        ti = self._makeOne( 'Foo' )
        self.failIf( ti.listActions() )

        ti = self._makeOne( **FTIDATA_ACTIONS[0] )
        actions = ti.listActions()
        self.failUnless( actions )

        ids = [ x.getId() for x in actions ]
        self.failUnless( 'view' in ids )
        self.failUnless( 'edit' in ids )
        self.failUnless( 'objectproperties' in ids )
        self.failUnless( 'slot' in ids )

        names = [ x.Title() for x in actions ]
        self.failUnless( 'View' in names )
        self.failUnless( 'Edit' in names )
        self.failUnless( 'Object Properties' in names )
        self.failIf( 'slot' in names )
        self.failUnless( 'Slot' in names )

        visible = [ x.getId() for x in actions if x.getVisibility() ]
        self.failUnless( 'view' in visible )
        self.failUnless( 'edit' in visible )
        self.failUnless( 'objectproperties' in visible )
        self.failIf( 'slot' in visible )

    def test_MethodAliases_methods(self):
        from Products.CMFCore.tests.base.tidata import FTIDATA_CMF
        ti = self._makeOne( **FTIDATA_CMF[0] )
        self.assertEqual( ti.getMethodAliases(), FTIDATA_CMF[0]['aliases'] )
        self.assertEqual( ti.queryMethodID('view'), 'dummy_view' )
        self.assertEqual( ti.queryMethodID('view.html'), 'dummy_view' )

        ti.setMethodAliases( ti.getMethodAliases() )
        self.assertEqual( ti.getMethodAliases(), FTIDATA_CMF[0]['aliases'] )

    def test_getInfoData(self):
        ti_data = {'id': 'foo',
                   'title': 'Foo',
                   'description': 'Foo objects are just used for testing.',
                   'content_meta_type': 'Foo Content',
                   'factory' : 'cmf.foo',
                   'icon_expr' : 'string:${portal_url}/foo_icon_expr.gif',
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
                         set(['url', 'icon', 'available', 'allowed']))

    def test_getInfoData_without_urls(self):
        ti_data = {'id': 'foo',
                   'title': 'Foo',
                   'description': 'Foo objects are just used for testing.',
                   'content_meta_type': 'Foo Content',
                   'factory' : 'cmf.foo'}
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

        self.assertEqual(set(info_data[1]), set(['available', 'allowed']))

    def _checkContentTI(self, ti):
        from Products.CMFCore.ActionInformation import ActionInformation
        wanted_aliases = { 'view': 'dummy_view', '(Default)': 'dummy_view' }
        wanted_actions_text0 = 'string:${object_url}/dummy_view'
        wanted_actions_text1 = 'string:${object_url}/dummy_edit_form'
        wanted_actions_text2 = 'string:${object_url}/metadata_edit_form'

        self.failUnless( isinstance( ti._actions[0], ActionInformation ) )
        self.assertEqual( len( ti._actions ), 3 )
        self.assertEqual(ti._aliases, wanted_aliases)
        self.assertEqual(ti._actions[0].action.text, wanted_actions_text0)
        self.assertEqual(ti._actions[1].action.text, wanted_actions_text1)
        self.assertEqual(ti._actions[2].action.text, wanted_actions_text2)

        action0 = ti._actions[0]
        self.assertEqual( action0.getId(), 'view' )
        self.assertEqual( action0.Title(), 'View' )
        self.assertEqual( action0.getActionExpression(), wanted_actions_text0 )
        self.assertEqual( action0.getCondition(), '' )
        self.assertEqual( action0.getPermissions(), ( 'View', ) )
        self.assertEqual( action0.getCategory(), 'object' )
        self.assertEqual( action0.getVisibility(), 1 )

    def _checkFolderTI(self, ti):
        from Products.CMFCore.ActionInformation import ActionInformation
        wanted_aliases = { 'view': '(Default)' }
        wanted_actions_text0 = 'string:${object_url}'
        wanted_actions_text1 = 'string:${object_url}/dummy_edit_form'
        wanted_actions_text2 = 'string:${object_url}/folder_localrole_form'

        self.failUnless( isinstance( ti._actions[0], ActionInformation ) )
        self.assertEqual( len( ti._actions ), 3 )
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
        self.failUnless(hasattr(ti, 'icon_expr_object'))
        self.failUnless(info_data[0].get('icon'))
        self.failUnless('icon' in info_data[1])
        self.failUnless(hasattr(ti, 'add_view_expr_object'))
        self.failUnless(info_data[0].get('url'))
        self.failUnless('url' in info_data[1])
        ti.manage_changeProperties(icon_expr='', add_view_expr='')
        info_data = ti.getInfoData()
        self.failIf(hasattr(ti, 'icon_expr_object'))
        self.failIf(info_data[0].get('icon'))
        self.failIf('icon' in info_data[1])
        self.failIf(hasattr(ti, 'add_view_expr_object'))
        self.failIf(info_data[0].get('url'))
        self.failIf('url' in info_data[1])


class FTIDataTests( TypeInfoTests, unittest.TestCase ):

    def _getTargetClass(self):
        from Products.CMFCore.TypesTool import FactoryTypeInformation
        return FactoryTypeInformation

    def test_properties( self ):
        ti = self._makeOne( 'Foo' )
        self.assertEqual( ti.product, '' )
        self.assertEqual( ti.factory, '' )

        ti = self._makeOne('Foo'
                          , product='FooProduct'
                          , factory='addFoo'
                          )
        self.assertEqual( ti.product, 'FooProduct' )
        self.assertEqual( ti.factory, 'addFoo' )


class STIDataTests( TypeInfoTests, unittest.TestCase ):

    def _getTargetClass(self):
        from Products.CMFCore.TypesTool import ScriptableTypeInformation
        return ScriptableTypeInformation

    def test_properties( self ):
        ti = self._makeOne( 'Foo' )
        self.assertEqual( ti.permission, '' )
        self.assertEqual( ti.constructor_path, '' )

        ti = self._makeOne( 'Foo'
                               , permission='Add Foos'
                               , constructor_path='foo_add'
                               )
        self.assertEqual( ti.permission, 'Add Foos' )
        self.assertEqual( ti.constructor_path, 'foo_add' )


class FTIConstructionTestCase:

    def _getTargetClass(self):
        from Products.CMFCore.TypesTool import FactoryTypeInformation
        return FactoryTypeInformation

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_isConstructionAllowed_wo_Container(self):
        self.failIf(self.ti.isConstructionAllowed(None))

    def test_isConstructionAllowed_wo_ProductFactory(self):
        ti = self._makeOne('foo')
        self.failIf(ti.isConstructionAllowed(self.f))

    def test_isConstructionAllowed_wo_Security(self):
        from AccessControl.SecurityManagement import noSecurityManager
        noSecurityManager()
        self.failIf(self.ti.isConstructionAllowed(self.f))

    def test_isConstructionAllowed_for_Omnipotent(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from Products.CMFCore.tests.base.security import OmnipotentUser
        newSecurityManager(None, OmnipotentUser().__of__(self.f))
        self.failUnless(self.ti.isConstructionAllowed(self.f))

    def test_isConstructionAllowed_w_Role(self):
        self.failUnless(self.ti.isConstructionAllowed(self.f))

    def test_isConstructionAllowed_wo_Role(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from Products.CMFCore.tests.base.security import UserWithRoles
        newSecurityManager(None, UserWithRoles('FooViewer').__of__(self.f))
        self.failIf(self.ti.isConstructionAllowed(self.f))

    def test_constructInstance_wo_Roles(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.unauthorized import Unauthorized
        from Products.CMFCore.tests.base.security import UserWithRoles
        newSecurityManager(None, UserWithRoles('FooViewer').__of__(self.f))
        self.assertRaises(Unauthorized,
                          self.ti.constructInstance, self.f, 'foo')

    def test_constructInstance(self):
        self.ti.constructInstance(self.f, 'foo')
        foo = self.f._getOb('foo')
        self.assertEqual(foo.id, 'foo')

    def test_constructInstance_private(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from Products.CMFCore.tests.base.security import UserWithRoles
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
        from Products.CMFCore.tests.base.dummy import DummyFolder
        from Products.CMFCore.tests.base.security import UserWithRoles
        self.f = DummyFolder(fake_product=1)
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
        from zope.container.interfaces import IObjectAddedEvent
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
        self.assertEquals(len(events), 3)

        evt = events[0]
        self.failUnless(IObjectCreatedEvent.providedBy(evt))
        self.assertEquals(evt.object, self.f.foo)

        evt = events[1]
        self.failUnless(IObjectAddedEvent.providedBy(evt))
        self.assertEquals(evt.object, self.f.foo)
        self.assertEquals(evt.oldParent, None)
        self.assertEquals(evt.oldName, None)
        self.assertEquals(evt.newParent, self.f)
        self.assertEquals(evt.newName, 'foo')

        evt = events[2]
        self.failUnless(IContainerModifiedEvent.providedBy(evt))
        self.assertEquals(evt.object, self.f)


class FTINewstyleConstructionTests(FTIConstructionTestCase, SecurityTest):

    def setUp(self):
        from AccessControl.SecurityManagement import newSecurityManager
        from zope.component import getSiteManager
        from zope.component.interfaces import IFactory
        from Products.CMFCore.tests.base.dummy import DummyFactory
        from Products.CMFCore.tests.base.dummy import DummyFolder
        from Products.CMFCore.tests.base.security import UserWithRoles
        SecurityTest.setUp(self)
        sm = getSiteManager()
        sm.registerUtility(DummyFactory, IFactory, 'test.dummy')

        self.f = DummyFolder()
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
        from zope.container.interfaces import IObjectAddedEvent
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
        self.assertEquals(len(events), 4)

        evt = events[0]
        self.failUnless(IObjectCreatedEvent.providedBy(evt))
        self.assertEquals(evt.object, self.f.foo)

        evt = events[1]
        self.failUnless(IObjectWillBeAddedEvent.providedBy(evt))
        self.assertEquals(evt.object, self.f.foo)
        self.assertEquals(evt.oldParent, None)
        self.assertEquals(evt.oldName, None)
        self.assertEquals(evt.newParent, self.f)
        self.assertEquals(evt.newName, 'foo')

        evt = events[2]
        self.failUnless(IObjectAddedEvent.providedBy(evt))
        self.assertEquals(evt.object, self.f.foo)
        self.assertEquals(evt.oldParent, None)
        self.assertEquals(evt.oldName, None)
        self.assertEquals(evt.newParent, self.f)
        self.assertEquals(evt.newName, 'foo')

        evt = events[3]
        self.failUnless(IContainerModifiedEvent.providedBy(evt))
        self.assertEquals(evt.object, self.f)

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
    return unittest.TestSuite((
        unittest.makeSuite(TypesToolTests),
        unittest.makeSuite(TypesToolFunctionalTests),
        unittest.makeSuite(FTIDataTests),
        unittest.makeSuite(STIDataTests),
        unittest.makeSuite(FTIOldstyleConstructionTests),
        unittest.makeSuite(FTINewstyleConstructionTests),
        ))

if __name__ == '__main__':
    from Products.CMFCore.testing import run
    run(test_suite())
