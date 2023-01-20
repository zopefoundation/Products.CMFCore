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
""" Unit tests for security on FS* modules.
"""

import logging
import unittest
from os import path

from AccessControl.Permission import Permission
from App.config import getConfiguration

from .base.testcase import LogInterceptor
from .base.testcase import WritableFSDVTest


class MetadataChecker:

    def _checkSettings(self, object, permissionname, acquire=0, roles=[]):
        # check the roles and acquire settings for a permission on an
        # object are as expected
        happy = 0
        for pstuff in object.ac_inherited_permissions(1):
            name, value = pstuff[:2]
            if name == permissionname:
                p = Permission(name, value, object)
                groles = p.getRoles(default=[])
                acquired = isinstance(groles, list)
                expected = {}
                for role in roles:
                    expected[role] = 1
                got = {}
                for role in groles:
                    got[role] = 1
                self.assertEqual((acquire, expected), (acquired, got))
                happy = 1
        if not happy:
            raise ValueError("'%s' not found in inherited permissions."
                             % permissionname)


class FSSecurityTests(WritableFSDVTest, MetadataChecker, LogInterceptor):

    def setUp(self):
        WritableFSDVTest.setUp(self)
        self._registerDirectory(self)

    def tearDown(self):
        self._ignore_log_errors(subsystem='CMFCore.DirectoryView')
        self._ignore_log_errors(subsystem='CMFCore.FSMetadata')
        WritableFSDVTest.tearDown(self)

    def test_basicPermissions(self):
        # Test basic FS permissions
        # check a normal method is as we'd expect
        self._checkSettings(self.ob.fake_skin.test1, 'View', 1, [])
        # now do some checks on the method with FS permissions
        self._checkSettings(self.ob.fake_skin.test4,
                            'View', 1, ['Manager', 'Owner'])
        self._checkSettings(self.ob.fake_skin.test4,
                            'View management screens', 1, [])

    def test_invalidPermissionNames(self):
        # Test for an invalid permission name
        from ..DirectoryView import _dirreg

        self._catch_log_errors(logging.ERROR,
                               subsystem='CMFCore.DirectoryView')
        # baseline
        _dirreg.reloadDirectory(self.ob.fake_skin._dirpath)
        self._checkSettings(self.ob.fake_skin.test5, 'View', 1, [])
        self.assertEqual(self.logged, None)
        # add
        f = open(path.join(self.skin_path_name, 'test5.py.metadata'), 'w')
        f.write('[security]\nAccess stoopid contents = 0:')
        f.close()
        # test
        _dirreg.reloadDirectory(self.ob.fake_skin._dirpath)
        self._checkSettings(self.ob.fake_skin.test5, 'View', 1, [])
        self.assertEqual(len(self.logged), 1)
        self.assertEqual(self.logged[0].getMessage(),
                         'Error setting permissions')

    def test_invalidAcquireNames(self):
        # Test for an invalid spelling of acquire
        from ..DirectoryView import _dirreg

        self._catch_log_errors(logging.ERROR,
                               subsystem='CMFCore.FSMetadata')
        # baseline
        _dirreg.reloadDirectory(self.ob.fake_skin._dirpath)
        self._checkSettings(self.ob.fake_skin.test5, 'View', 1, [])
        self.assertEqual(self.logged, None)
        # add
        f = open(path.join(self.skin_path_name, 'test5.py.metadata'), 'w')
        f.write('[security]\nView = aquire:')
        f.close()
        # test
        _dirreg.reloadDirectory(self.ob.fake_skin._dirpath)
        self._checkSettings(self.ob.fake_skin.test5, 'View', 1, [])
        self.assertEqual(len(self.logged), 1)
        self.assertEqual(self.logged[0].getMessage(),
                         'Error parsing .metadata file')


class DebugModeTests(WritableFSDVTest, MetadataChecker):

    def setUp(self):
        from ..DirectoryView import _dirreg

        WritableFSDVTest.setUp(self)
        self._registerDirectory(self)
        info = _dirreg.getDirectoryInfo(self.ob.fake_skin._dirpath)
        self.use_dir_mtime = info.use_dir_mtime
        self.saved_cfg_debug_mode = getConfiguration().debug_mode
        getConfiguration().debug_mode = True

    def tearDown(self):
        getConfiguration().debug_mode = self.saved_cfg_debug_mode
        WritableFSDVTest.tearDown(self)

    def test_addPRM(self):
        # Test adding of a .metadata
        # baseline
        self._checkSettings(self.ob.fake_skin.test5, 'View', 1, [])
        # add
        self._writeFile('test5.py.metadata',
                        '[security]\nView = 1:Manager',
                        self.use_dir_mtime)
        # test
        self._checkSettings(self.ob.fake_skin.test5, 'View', 1, ['Manager'])

    def test_delPRM(self):
        # Test deleting of a .metadata
        # baseline
        self._checkSettings(self.ob.fake_skin.test4,
                            'View', 1, ['Manager', 'Owner'])
        # delete
        self._deleteFile('test4.py.metadata', self.use_dir_mtime)
        # test
        self._checkSettings(self.ob.fake_skin.test4, 'View', 1, [])

    def DISABLED_test_editPRM(self):
        # see https://bugs.launchpad.net/zope-cmf/+bug/714525
        # Test editing a .metadata
        # baseline
        self._checkSettings(self.ob.fake_skin.test4,
                            'View', 1, ['Manager', 'Owner'])
        # edit
        self._writeFile('test4.py.metadata',
                        '[security]\nView = 1:Manager',
                        self.use_dir_mtime)
        # test
        self._checkSettings(self.ob.fake_skin.test4, 'View', 1, ['Manager'])

    def DISABLED_test_DelAddEditPRM(self):
        # see https://bugs.launchpad.net/zope-cmf/+bug/714525
        # Test deleting, then adding, then editing a .metadata file
        # baseline
        self._checkSettings(self.ob.fake_skin.test4,
                            'View', 1, ['Manager', 'Owner'])
        # delete
        self._deleteFile('test4.py.metadata', self.use_dir_mtime)
        self._checkSettings(self.ob.fake_skin.test4, 'View', 1, [])
        # add back
        self._writeFile('test4.py.metadata',
                        '[security]\nView = 0:Manager,Anonymous',
                        self.use_dir_mtime)
        self._checkSettings(self.ob.fake_skin.test4,
                            'View', 0, ['Manager', 'Anonymous'])
        # edit
        self._writeFile('test4.py.metadata',
                        '[security]\nView = 1:Manager',
                        self.use_dir_mtime)
        # test
        self._checkSettings(self.ob.fake_skin.test4, 'View', 1, ['Manager'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(
        unittest.defaultTestLoader.loadTestsFromTestCase(FSSecurityTests))
    suite.addTest(
        unittest.defaultTestLoader.loadTestsFromTestCase(DebugModeTests))
    return suite
