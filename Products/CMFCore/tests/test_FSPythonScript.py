##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for FSPythonScript module. """

import unittest
from Testing import ZopeTestCase
ZopeTestCase.installProduct('PythonScripts', 1)

from os.path import join
from sys import exc_info
from thread import start_new_thread
from time import sleep

from Acquisition import aq_base
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from Products.StandardCacheManagers import RAMCacheManager

from Products.CMFCore.FSMetadata import FSMetadata
from Products.CMFCore.FSPythonScript import FSPythonScript
from Products.CMFCore.tests.base.testcase import FSDVTest
from Products.CMFCore.tests.base.testcase import SecurityTest
from Products.CMFCore.tests.base.testcase import WarningInterceptor


class FSPSMaker(FSDVTest):

    def _makeOne( self, id, filename ):
        path = join(self.skin_path_name, filename)
        metadata = FSMetadata(path)
        metadata.read()
        return FSPythonScript( id, path, properties=metadata.getProperties() ) 


class FSPythonScriptTests(FSPSMaker):

    def test_get_size( self ):
        # Test get_size returns correct value
        script = self._makeOne('test1', 'test1.py')
        self.assertEqual(len(script.read()),script.get_size())

    def test_initialization_race_condition(self):
        # Tries to exercise a former race condition where
        # FSObject._updateFromFS() set self._parsed before the
        # object was really parsed.
        for n in range(10):
            f = Folder()
            script = self._makeOne('test1', 'test1.py').__of__(f)
            res = []

            def call_script(script=script, res=res):
                try:
                    res.append(script())
                except:
                    res.append('%s: %s' % exc_info()[:2])

            start_new_thread(call_script, ())
            call_script()
            while len(res) < 2:
                sleep(0.05)
            self.assertEqual(res, ['test1', 'test1'], res)

    def test_foreign_line_endings( self ):
        # Load the various line ending files and get their output
        container = Folder('container_for_execution')
        for fformat in ('unix', 'dos', 'mac'):
            container._setObject(fformat,
                self._makeOne(fformat, 'test_%s.py' % fformat))
            script = getattr(container, fformat)
            self.assertEqual(script(), fformat)


class FSPythonScriptCustomizationTests(SecurityTest, FSPSMaker):

    def setUp( self ):
        FSPSMaker.setUp(self)
        SecurityTest.setUp( self )

    def tearDown(self):
        SecurityTest.tearDown(self)
        FSPSMaker.tearDown(self)

    def _makeSkins(self):

        root = self.root
        root._setObject( 'portal_skins', Folder( 'portal_skins' ) )
        tool = self.root.portal_skins

        tool._setObject( 'custom', Folder( 'custom' ) )
        custom = tool.custom

        tool._setObject( 'fsdir', Folder( 'fsdir' ) )
        fsdir = tool.fsdir

        fsdir._setObject( 'test6'
                        , self._makeOne( 'test6', 'test6.py' ) )

        fsPS = fsdir.test6

        return root, tool, custom, fsdir, fsPS

    def test_customize( self ):

        from Products.CMFCore.FSPythonScript import CustomizedPythonScript

        root, tool, custom, fsdir, fsPS = self._makeSkins()

        fsPS.manage_doCustomize( folder_path='custom' )

        self.assertEqual( len( custom.objectIds() ), 1 )
        self.failUnless( 'test6' in custom.objectIds() )  

        test6 = custom._getOb('test6')

        self.failUnless(isinstance(test6, CustomizedPythonScript))
        self.assertEqual(test6.original_source, fsPS.read())

    def test_customize_alternate_root( self ):

        root, tool, custom, fsdir, fsPS = self._makeSkins()
        root.other = Folder('other')

        fsPS.manage_doCustomize( folder_path='other', root=root )

        self.failIf( 'test6' in custom.objectIds() )  
        self.failUnless( 'test6' in root.other.objectIds() )  

    def test_customize_fspath_as_dot( self ):

        root, tool, custom, fsdir, fsPS = self._makeSkins()

        fsPS.manage_doCustomize( folder_path='.' )

        self.failIf( 'test6' in custom.objectIds() )  
        self.failUnless( 'test6' in root.portal_skins.objectIds() )  

    def test_customize_manual_clone( self ):

        root, tool, custom, fsdir, fsPS = self._makeSkins()
        clone = Folder('test6')

        fsPS.manage_doCustomize( folder_path='custom', obj=clone )

        self.failUnless( 'test6' in custom.objectIds() )  
        self.failUnless( aq_base(custom._getOb('test6')) is clone )  

    def test_customize_caching(self):
        # Test to ensure that cache manager associations survive customizing
        root, tool, custom, fsdir, fsPS = self._makeSkins()

        cache_id = 'gofast'
        RAMCacheManager.manage_addRAMCacheManager( root
                                                 , cache_id
                                                 , REQUEST=None
                                                 )
        fsPS.ZCacheable_setManagerId(cache_id, REQUEST=None)

        self.assertEqual(fsPS.ZCacheable_getManagerId(), cache_id)

        fsPS.manage_doCustomize(folder_path='custom')
        custom_ps = custom.test6

        self.assertEqual(custom_ps.ZCacheable_getManagerId(), cache_id)

    def test_customize_proxyroles(self):
        # Test to ensure that proxy roles survive customizing
        root, tool, custom, fsdir, fsPS = self._makeSkins()

        fsPS._proxy_roles = ('Manager', 'Anonymous')
        self.failUnless(fsPS.manage_haveProxy('Anonymous'))
        self.failUnless(fsPS.manage_haveProxy('Manager'))

        fsPS.manage_doCustomize(folder_path='custom')
        custom_ps = custom.test6
        self.failUnless(custom_ps.manage_haveProxy('Anonymous'))
        self.failUnless(custom_ps.manage_haveProxy('Manager'))

    def test_customization_permissions(self):
        # Test to ensure that permission settings survive customizing
        root, tool, custom, fsdir, fsPS = self._makeSkins()
        perm = 'View management screens'

        # First, set a permission to an odd role and verify
        fsPS.manage_permission( perm
                              , roles=('Anonymous',)
                              , acquire=0
                              )
        rop = fsPS.rolesOfPermission(perm)
        for rop_info in rop:
            if rop_info['name'] == 'Anonymous':
                self.failIf(rop_info['selected'] == '')
            else:
                self.failUnless(rop_info['selected'] == '')

        # Now customize and verify again
        fsPS.manage_doCustomize(folder_path='custom')
        custom_ps = custom.test6
        rop = custom_ps.rolesOfPermission(perm)
        for rop_info in rop:
            if rop_info['name'] == 'Anonymous':
                self.failIf(rop_info['selected'] == '')
            else:
                self.failUnless(rop_info['selected'] == '')

_ORIGINAL_TEXT = """\
## Script (Python) "cps"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
return 'cps'
"""

_REPLACEMENT_TEXT = """\
## Script (Python) "cps"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
return 'cps -- replaced'
"""

_DIFF_TEXT = """\
--- original 
+++ modified 
@@ -7,4 +7,4 @@
 ##parameters=
 ##title=
 ##
-return 'cps'
+return 'cps -- replaced'
"""

class CustomizedPythonScriptTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.CMFCore.FSPythonScript import CustomizedPythonScript
        return CustomizedPythonScript

    def _makeOne(self, id, text):
        return self._getTargetClass()(id, text)

    def test_write_leaves_original_source(self):
        cps = self._makeOne('cps', _ORIGINAL_TEXT)
        self.assertEqual(cps.read(), _ORIGINAL_TEXT)
        self.assertEqual(cps.original_source, _ORIGINAL_TEXT)
        cps.write(_REPLACEMENT_TEXT)
        self.assertEqual(cps.read(), _REPLACEMENT_TEXT)
        self.assertEqual(cps.original_source, _ORIGINAL_TEXT)

    def test_getDiff(self):
        cps = self._makeOne('cps', _ORIGINAL_TEXT)
        self.assertEqual(len(list(cps.getDiff())), 0)

        cps.write(_REPLACEMENT_TEXT)
        self.assertEqual(list(cps.getDiff()), _DIFF_TEXT.splitlines())


class WarnMe(SimpleItem):
    """Emits a UserWarning when called"""

    def __init__(self, stacklevel):
        self._stacklevel = stacklevel

    def __call__(self):
        import warnings
        warnings.warn('foo', stacklevel=self._stacklevel)


class FSPythonScriptWarningsTests(SecurityTest, FSPSMaker, WarningInterceptor):

    def setUp( self ):
        SecurityTest.setUp(self)
        FSPSMaker.setUp(self)
        self._trap_warning_output()

    def tearDown(self):
        self._free_warning_output()
        FSPSMaker.tearDown(self)
        SecurityTest.tearDown(self)

    def testFSPSWarn(self):
        self.root._setObject('warn_me', WarnMe(2))
        self.root._setObject('warn1', self._makeOne('warn1', 'test_warn.py'))
        # This used to raise an error:
        #   File "/usr/local/python2.3/lib/python2.3/warnings.py", line 63, in warn_explicit
        #     if module[-3:].lower() == ".py":
        # TypeError: unsubscriptable object
        self.root.warn1()


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FSPythonScriptTests),
        unittest.makeSuite(FSPythonScriptCustomizationTests),
        unittest.makeSuite(CustomizedPythonScriptTests),
        unittest.makeSuite(FSPythonScriptWarningsTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
