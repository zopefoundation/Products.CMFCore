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
"""Unit tests for FSZSQLMethod module.
"""

import unittest
from Testing import ZopeTestCase
ZopeTestCase.installProduct('ZSQLMethods', 1)

from os.path import join

from Acquisition import aq_base
from zope.testing.cleanup import cleanUp

from Products.CMFCore.FSMetadata import FSMetadata
from Products.CMFCore.FSZSQLMethod import FSZSQLMethod
from Products.CMFCore.tests.base.testcase import FSDVTest
from Products.CMFCore.tests.base.testcase import SecurityTest


class FSZSQLMaker(FSDVTest):

    def _makeOne(self, id, filename):
        path = join(self.skin_path_name, filename)
        metadata = FSMetadata(path)
        metadata.read()
        return FSZSQLMethod(id, path, properties=metadata.getProperties())


class FSZSQLMethodTests(FSDVTest):

    def setUp(self):
        FSDVTest.setUp(self)
        self._registerDirectory(self)

    def test_initialization(self):
        zsql = self.ob.fake_skin.testsql
        self.assertEqual(zsql.title, 'This is a title')
        self.assertEqual(zsql.connection_id, 'testconn')
        self.assertEqual(zsql.arguments_src, 'id')
        self.assertEqual(zsql.max_rows_, 1000)
        self.assertEqual(zsql.max_cache_, 100)
        self.assertEqual(zsql.cache_time_, 10)
        self.assertEqual(zsql.class_name_, 'MyRecord')
        self.assertEqual(zsql.class_file_, 'CMFCore.TestRecord')
        self.assertEqual(zsql.connection_hook, 'MyHook')
        self.assertFalse(zsql.allow_simple_one_argument_traversal is None)


class FSZSQLMethodCustomizationTests(SecurityTest, FSZSQLMaker):

    def setUp(self):
        FSZSQLMaker.setUp(self)
        SecurityTest.setUp(self)
        self.skins, self.custom, self.fsdir, self.fsZSQL = self._makeContext(
                                                     'testsql', 'testsql.zsql')

    def tearDown(self):
        cleanUp()
        SecurityTest.tearDown(self)
        FSZSQLMaker.tearDown(self)

    def test_customize(self):
        self.fsZSQL.manage_doCustomize(folder_path='custom')

        self.assertEqual(len(self.custom.objectIds()), 1)
        self.assertTrue('testsql' in self.custom.objectIds())

    def test_customize_alternate_root(self):
        from OFS.Folder import Folder

        self.app.other = Folder('other')

        self.fsZSQL.manage_doCustomize(folder_path='other', root=self.app)

        self.assertFalse('testsql' in self.custom.objectIds())
        self.assertTrue('testsql' in self.app.other.objectIds())

    def test_customize_fspath_as_dot(self):
        self.fsZSQL.manage_doCustomize(folder_path='.')

        self.assertFalse('testsql' in self.custom.objectIds())
        self.assertTrue('testsql' in self.skins.objectIds())

    def test_customize_manual_clone(self):
        from OFS.Folder import Folder

        clone = Folder('testsql')

        self.fsZSQL.manage_doCustomize(folder_path='custom', obj=clone)

        self.assertTrue('testsql' in self.custom.objectIds())
        self.assertTrue(aq_base(self.custom._getOb('testsql')) is clone)

    def test_customize_properties(self):
        # Make sure all properties are coming across
        self.fsZSQL.manage_doCustomize(folder_path='custom')
        zsql = self.custom.testsql

        self.assertEqual(zsql.title, 'This is a title')
        self.assertEqual(zsql.connection_id, 'testconn')
        self.assertEqual(zsql.arguments_src, 'id')
        self.assertEqual(zsql.max_rows_, 1000)
        self.assertEqual(zsql.max_cache_, 100)
        self.assertEqual(zsql.cache_time_, 10)
        self.assertEqual(zsql.class_name_, 'MyRecord')
        self.assertEqual(zsql.class_file_, 'CMFCore.TestRecord')
        self.assertEqual(zsql.connection_hook, 'MyHook')
        self.assertFalse(zsql.allow_simple_one_argument_traversal is None)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FSZSQLMethodTests),
        unittest.makeSuite(FSZSQLMethodCustomizationTests),
        ))
