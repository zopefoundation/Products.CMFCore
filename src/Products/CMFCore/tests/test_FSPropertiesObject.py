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
"""Unit tests for FSPropertiesObject module.
"""

import unittest

from Acquisition import aq_base
from zope.testing.cleanup import cleanUp

from .base.testcase import FSDVTest
from .base.testcase import SecurityTest


class FSPOTests(SecurityTest, FSDVTest):

    def setUp(self):
        FSDVTest.setUp(self)
        SecurityTest.setUp(self)

    def tearDown(self):
        cleanUp()
        SecurityTest.tearDown(self)
        FSDVTest.tearDown(self)

    def _getTargetClass(self):
        from ..FSPropertiesObject import FSPropertiesObject

        return FSPropertiesObject

    def _makeOne(self, id, filename):
        from os.path import join
        path = join(self.skin_path_name, filename)
        return self._getTargetClass()(id, path)

    def test__readFile(self):
        from DateTime.DateTime import DateTime

        _stool, _custom, _fsdir, fspo = self._makeContext('test_props',
                                                          'test_props.props')

        self.assertEqual(fspo.getProperty('title'), 'Test properties')
        self.assertEqual(fspo.getProperty('value1'), 'one')
        self.assertEqual(fspo.getProperty('value2'), 'two')
        self.assertEqual(fspo.getProperty('an_int'), 42)
        self.assertEqual(fspo.getProperty('a_float'), 3.1415926)
        self.assertEqual(fspo.getProperty('a_boolean'), False)
        self.assertEqual(fspo.getProperty('a_long'), 40000000000)
        self.assertEqual(fspo.getProperty('a_date'), DateTime('01/01/2001'))
        self.assertEqual(fspo.getProperty('a_tokens'),
                         ['peter', 'paul', 'mary'])

    def test__createZODBClone(self):
        from OFS.Folder import Folder

        _stool, _custom, _fsdir, fspo = self._makeContext('test_props',
                                                          'test_props.props')

        target = fspo._createZODBClone()
        self.assertTrue(isinstance(target, Folder))
        for prop_id in fspo.propertyIds():
            self.assertEqual(target.getProperty(prop_id),
                             fspo.getProperty(prop_id))

    def test_manage_doCustomize(self):
        _stool, custom, _fsdir, fspo = self._makeContext('test_props',
                                                         'test_props.props')

        fspo.manage_doCustomize(folder_path='custom')

        self.assertEqual(len(custom.objectIds()), 1)
        self.assertTrue('test_props' in custom.objectIds())

    def test_manage_doCustomize_alternate_root(self):
        from OFS.Folder import Folder

        _stool, custom, _fsdir, fspo = self._makeContext('test_props',
                                                         'test_props.props')
        self.app.other = Folder('other')

        fspo.manage_doCustomize(folder_path='other', root=self.app)

        self.assertFalse('test_props' in custom.objectIds())
        self.assertTrue('test_props' in self.app.other.objectIds())

    def test_manage_doCustomize_fspath_as_dot(self):
        stool, custom, _fsdir, fspo = self._makeContext('test_props',
                                                        'test_props.props')
        fspo.manage_doCustomize(folder_path='.')

        self.assertFalse('test_props' in custom.objectIds())
        self.assertTrue('test_props' in stool.objectIds())

    def test_manage_doCustomize_manual_clone(self):
        from OFS.Folder import Folder

        _stool, custom, _fsdir, fspo = self._makeContext('test_props',
                                                         'test_props.props')
        clone = Folder('test_props')
        fspo.manage_doCustomize(folder_path='custom', obj=clone)

        self.assertTrue('test_props' in custom.objectIds())
        self.assertTrue(aq_base(custom._getOb('test_props')) is clone)


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(FSPOTests),
        ))
