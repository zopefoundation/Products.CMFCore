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
""" Unit tests for FSPythonScript module.
"""

import os
import unittest
import warnings
from _thread import start_new_thread
from os.path import join
from sys import exc_info
from time import sleep

from Acquisition import aq_base
from DateTime.DateTime import DateTime
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from Testing import ZopeTestCase
from zope.testing.cleanup import cleanUp

from Products.StandardCacheManagers import RAMCacheManager

from ..FSMetadata import FSMetadata
from ..FSPythonScript import FSPythonScript
from .base.testcase import FSDVTest
from .base.testcase import SecurityTest


ZopeTestCase.installProduct('PythonScripts', 1)


class FSPSMaker(FSDVTest):

    def _makeOne(self, id, filename):
        path = join(self.skin_path_name, filename)
        metadata = FSMetadata(path)
        metadata.read()
        return FSPythonScript(id, path, properties=metadata.getProperties())


class FSPythonScriptTests(FSPSMaker):

    def test_get_size(self):
        # Test get_size returns correct value
        script = self._makeOne('test1', 'test1.py')
        self.assertEqual(len(script.read()), script.get_size())

    def test_getModTime(self):
        script = self._makeOne('test1', 'test1.py')
        self.assertTrue(isinstance(script.getModTime(), DateTime))
        self.assertEqual(script.getModTime(),
                         DateTime(os.stat(script._filepath).st_mtime))

    def test_bobobase_modification_time(self):
        script = self._makeOne('test1', 'test1.py')
        self.assertTrue(isinstance(script.bobobase_modification_time(),
                                   DateTime))
        self.assertEqual(script.bobobase_modification_time(),
                         DateTime(os.stat(script._filepath).st_mtime))

    def test_initialization_race_condition(self):
        # Tries to exercise a former race condition where
        # FSObject._updateFromFS() set self._parsed before the
        # object was really parsed.
        for _n in range(10):
            f = Folder()
            script = self._makeOne('test1', 'test1.py').__of__(f)
            res = []

            def call_script(script=script, res=res):
                try:
                    res.append(script())
                except Exception:
                    res.append('%s: %s' % exc_info()[:2])

            start_new_thread(call_script, ())
            call_script()
            while len(res) < 2:
                sleep(0.05)
            self.assertEqual(res, ['test1', 'test1'], res)

    def test_foreign_line_endings(self):
        # Load the various line ending files and get their output
        container = Folder('container_for_execution')
        for fformat in ('unix', 'dos', 'mac'):
            container._setObject(fformat,
                                 self._makeOne(fformat,
                                               'test_%s.py' % fformat))
            script = getattr(container, fformat)
            self.assertEqual(script(), fformat)


class FSPythonScriptCustomizationTests(SecurityTest, FSPSMaker):

    def setUp(self):
        FSPSMaker.setUp(self)
        SecurityTest.setUp(self)

    def tearDown(self):
        cleanUp()
        SecurityTest.tearDown(self)
        FSPSMaker.tearDown(self)

    def test_customize(self):
        from ..FSPythonScript import CustomizedPythonScript

        _stool, custom, _fsdir, fsPS = self._makeContext('test6', 'test6.py')

        fsPS.manage_doCustomize(folder_path='custom')

        self.assertEqual(len(custom.objectIds()), 1)
        self.assertTrue('test6' in custom.objectIds())

        test6 = custom._getOb('test6')

        self.assertTrue(isinstance(test6, CustomizedPythonScript))
        self.assertEqual(test6.original_source, fsPS.read())

    def test_customize_alternate_root(self):
        _stool, custom, _fsdir, fsPS = self._makeContext('test6', 'test6.py')
        self.app.other = Folder('other')

        fsPS.manage_doCustomize(folder_path='other', root=self.app)

        self.assertFalse('test6' in custom.objectIds())
        self.assertTrue('test6' in self.app.other.objectIds())

    def test_customize_fspath_as_dot(self):
        stool, custom, _fsdir, fsPS = self._makeContext('test6', 'test6.py')

        fsPS.manage_doCustomize(folder_path='.')

        self.assertFalse('test6' in custom.objectIds())
        self.assertTrue('test6' in stool.objectIds())

    def test_customize_manual_clone(self):
        _stool, custom, _fsdir, fsPS = self._makeContext('test6', 'test6.py')
        clone = Folder('test6')

        fsPS.manage_doCustomize(folder_path='custom', obj=clone)

        self.assertTrue('test6' in custom.objectIds())
        self.assertTrue(aq_base(custom._getOb('test6')) is clone)

    def test_customize_caching(self):
        # Test to ensure that cache manager associations survive customizing
        _stool, custom, _fsdir, fsPS = self._makeContext('test6', 'test6.py')

        cache_id = 'gofast'
        RAMCacheManager.manage_addRAMCacheManager(self.app, cache_id,
                                                  REQUEST=None)
        fsPS.ZCacheable_setManagerId(cache_id, REQUEST=None)

        self.assertEqual(fsPS.ZCacheable_getManagerId(), cache_id)

        fsPS.manage_doCustomize(folder_path='custom')
        custom_ps = custom.test6

        self.assertEqual(custom_ps.ZCacheable_getManagerId(), cache_id)

    def test_customize_proxyroles(self):
        # Test to ensure that proxy roles survive customizing
        _stool, custom, _fsdir, fsPS = self._makeContext('test6', 'test6.py')

        fsPS._proxy_roles = ('Manager', 'Anonymous')
        self.assertTrue(fsPS.manage_haveProxy('Anonymous'))
        self.assertTrue(fsPS.manage_haveProxy('Manager'))

        fsPS.manage_doCustomize(folder_path='custom')
        custom_ps = custom.test6
        self.assertTrue(custom_ps.manage_haveProxy('Anonymous'))
        self.assertTrue(custom_ps.manage_haveProxy('Manager'))

    def test_customization_permissions(self):
        # Test to ensure that permission settings survive customizing
        _stool, custom, _fsdir, fsPS = self._makeContext('test6', 'test6.py')
        perm = 'View management screens'

        # First, set a permission to an odd role and verify
        fsPS.manage_permission(perm, roles=('Anonymous',), acquire=0)
        rop = fsPS.rolesOfPermission(perm)
        for rop_info in rop:
            if rop_info['name'] == 'Anonymous':
                self.assertFalse(rop_info['selected'] == '')
            else:
                self.assertTrue(rop_info['selected'] == '')

        # Now customize and verify again
        fsPS.manage_doCustomize(folder_path='custom')
        custom_ps = custom.test6
        rop = custom_ps.rolesOfPermission(perm)
        for rop_info in rop:
            if rop_info['name'] == 'Anonymous':
                self.assertFalse(rop_info['selected'] == '')
            else:
                self.assertTrue(rop_info['selected'] == '')


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
        from ..FSPythonScript import CustomizedPythonScript
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
        self.assertEqual([line.rstrip() for line in cps.getDiff()],
                         _DIFF_TEXT.splitlines())


class WarnMe(SimpleItem):
    """Emits a UserWarning when called"""

    def __init__(self, stacklevel):
        self._stacklevel = stacklevel

    def __call__(self):
        warnings.warn('foo', stacklevel=self._stacklevel)


class FSPythonScriptWarningsTests(SecurityTest, FSPSMaker):

    def setUp(self):
        SecurityTest.setUp(self)
        FSPSMaker.setUp(self)

    def tearDown(self):
        FSPSMaker.tearDown(self)
        SecurityTest.tearDown(self)

    def testFSPSWarn(self):
        self.app._setObject('warn_me', WarnMe(2))
        self.app._setObject('warn1', self._makeOne('warn1', 'test_warn.py'))
        # This used to raise an error:
        #   File "/usr/local/python2.3/lib/python2.3/warnings.py", line 63,
        #   in warn_explicit
        #     if module[-3:].lower() == ".py":
        # TypeError: unsubscriptable object
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.app.warn_me()
            self.app.warn1()


def test_suite():
    loadTestsFromTestCase = unittest.defaultTestLoader.loadTestsFromTestCase
    return unittest.TestSuite((
        loadTestsFromTestCase(FSPythonScriptTests),
        loadTestsFromTestCase(FSPythonScriptCustomizationTests),
        loadTestsFromTestCase(CustomizedPythonScriptTests),
        loadTestsFromTestCase(FSPythonScriptWarningsTests),
    ))
