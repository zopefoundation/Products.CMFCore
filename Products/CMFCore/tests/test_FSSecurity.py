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
""" Unit tests for security on FS* modules. """

import unittest
import Testing

from time import sleep

from AccessControl.Permission import Permission
from App.config import getConfiguration

from Products.CMFCore.tests.base.testcase import LogInterceptor
from Products.CMFCore.tests.base.testcase import RequestTest
from Products.CMFCore.tests.base.testcase import WritableFSDVTest


class MetadataChecker(object):

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


class FSSecurityBase(RequestTest, WritableFSDVTest, LogInterceptor,
                     MetadataChecker):

    def setUp( self ):
        # initialise skins
        WritableFSDVTest.setUp(self)
        self._registerDirectory(self)
        # set up ZODB
        RequestTest.setUp(self)
        # put object in ZODB
        root=self.root
        try: root._delObject('fake_skin')
        except AttributeError: pass
        root._setObject( 'fake_skin', self.ob.fake_skin )

    def tearDown( self ):
        RequestTest.tearDown(self)
        WritableFSDVTest.tearDown(self)
        self._ignore_log_errors()
        self._ignore_log_errors(subsystem='CMFCore.DirectoryView')


class FSSecurityTests( FSSecurityBase, LogInterceptor ):

    def test_basicPermissions( self ):
        # Test basic FS permissions
        # check a normal method is as we'd expect
        self._checkSettings(self.ob.fake_skin.test1,'View',1,[])
        # now do some checks on the method with FS permissions
        self._checkSettings(self.ob.fake_skin.test4,
                            'View',1,['Manager','Owner'])
        self._checkSettings(self.ob.fake_skin.test4,
                            'Access contents information',0,[])

    def test_invalidPermissionNames( self ):
        import logging
        self._catch_log_errors(logging.ERROR,subsystem='CMFCore.DirectoryView')
        # Test for an invalid permission name
        # baseline
        self._checkSettings(self.ob.fake_skin.test5,'View',1,[])
        # add .rpm with dodgy permission name
        self._writeFile('test5.py.metadata',
                        '[security]\nAccess stoopid contents = 0:')
        # check baseline
        self._checkSettings(self.ob.fake_skin.test5,'View',1,[])

    def test_invalidAcquireNames( self ):
        # Test for an invalid spelling of acquire
        # baseline
        self._checkSettings(self.ob.fake_skin.test5,'View',1,[])
        # add dodgy .rpm
        self._writeFile('test5.py.metadata','[security]\nView = aquire:')
        # check baseline
        self._checkSettings(self.ob.fake_skin.test5,'View',1,[])


class DebugModeTests(WritableFSDVTest, MetadataChecker):

    def setUp(self):
        from Products.CMFCore.DirectoryView import _dirreg

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
        self._checkSettings(self.ob.fake_skin.test5,'View',1,[])
        # add
        self._writeFile('test5.py.metadata',
                        '[security]\nView = 1:Manager',
                        self.use_dir_mtime)
        # test
        self._checkSettings(self.ob.fake_skin.test5,'View',1,['Manager'])

    def test_delPRM( self ):
        # Test deleting of a .metadata
        # baseline
        self._checkSettings(self.ob.fake_skin.test5,'View',1,[])
        self._writeFile('test5.py.metadata',
                        '[security]\nView = 1:Manager')
        self._checkSettings(self.ob.fake_skin.test5,'View',1,['Manager'])
        # delete
        self._deleteFile('test4.py.metadata', self.use_dir_mtime)
        # test
        self._checkSettings(self.ob.fake_skin.test5,'View',1,[])

    def test_editPRM( self ):
        # Test editing a .metadata
        # we need to wait a second here or the mtime will actually
        # have the same value as set in the last test.
        # Maybe someone brainier than me can figure out a way to make this
        # suck less :-(
        sleep(1)

        # baseline
        self._writeFile('test5.py.metadata',
                        '[security]\nView = 0:Manager,Anonymous')
        self._checkSettings(self.ob.fake_skin.test5,
                            'View',0,['Manager','Anonymous'])
        # edit
        self._writeFile('test5.py.metadata',
                        '[security]\nView = 1:Manager',
                        self.use_dir_mtime)
        # test
        self._checkSettings(self.ob.fake_skin.test5,'View',1,['Manager'])

    def test_DelAddEditPRM( self ):
        # Test deleting, then adding, then editing a .metadata file
        # baseline
        self._writeFile('test5.py.metadata','[security]\nView = 0:Manager')
        # delete
        self._deleteFile('test4.py.metadata', self.use_dir_mtime)
        self._checkSettings(self.ob.fake_skin.test4, 'View', 1, [])
        # add back
        self._writeFile('test5.py.metadata',
                        '[security]\nView = 0:Manager,Anonymous',
                        self.use_dir_mtime)
        self._checkSettings(self.ob.fake_skin.test5,
                            'View',0,['Manager','Anonymous'])

        # edit
        self._writeFile('test5.py.metadata',
                        '[security]\nView = 1:Manager',
                        self.use_dir_mtime)
        # test
        self._checkSettings(self.ob.fake_skin.test5,'View',1,['Manager'])

def test_suite():
    import Globals # for data
    tests = [unittest.makeSuite(FSSecurityTests)]
    if Globals.DevelopmentMode:
        tests.append(unittest.makeSuite(DebugModeTests))

    return unittest.TestSuite(tests)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
