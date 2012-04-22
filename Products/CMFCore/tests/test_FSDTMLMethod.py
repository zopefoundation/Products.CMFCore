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
""" Unit tests for FSDTMLMethod module.
"""

import unittest
import Testing

from os.path import join as path_join

from Acquisition import aq_base
from App.Common import rfc1123_date
from DateTime import DateTime
from OFS.Folder import Folder
from Products.StandardCacheManagers import RAMCacheManager
from zope.component import getSiteManager
from zope.component.hooks import setHooks
from zope.testing.cleanup import cleanUp

from Products.CMFCore.FSMetadata import FSMetadata
from Products.CMFCore.interfaces import ICachingPolicyManager
from Products.CMFCore.tests.base.dummy import DummyCachingManager
from Products.CMFCore.tests.base.dummy import DummyCachingManagerWithPolicy
from Products.CMFCore.tests.base.dummy import DummyContent
from Products.CMFCore.tests.base.testcase import FSDVTest
from Products.CMFCore.tests.base.testcase import SecurityTest
from Products.CMFCore.tests.base.testcase import TransactionalTest


class FSDTMLMaker(FSDVTest):

    def _makeOne(self, id, filename):
        from Products.CMFCore.FSDTMLMethod import FSDTMLMethod

        path = path_join(self.skin_path_name, filename)
        metadata = FSMetadata(path)
        metadata.read()
        return FSDTMLMethod(id, path, properties=metadata.getProperties())


class FSDTMLMethodTests(TransactionalTest, FSDTMLMaker):

    def setUp(self):
        TransactionalTest.setUp(self)
        FSDTMLMaker.setUp(self)
        setHooks()

    def tearDown(self):
        cleanUp()
        FSDTMLMaker.tearDown(self)
        TransactionalTest.tearDown(self)

    def test___call__(self):
        script = self._makeOne('testDTML', 'testDTML.dtml')
        script = script.__of__(self.app)
        self.assertEqual(script(self.app, self.REQUEST), 'nohost\n')

    def test_caching(self):
        #   Test HTTP caching headers.
        cpm = DummyCachingManager()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)
        original_len = len(self.RESPONSE.headers)
        obj = self._makeOne('testDTML', 'testDTML.dtml')
        obj = obj.__of__(self.app)
        obj(self.app, self.REQUEST, self.RESPONSE)
        self.assertTrue(len(self.RESPONSE.headers) >= original_len + 2)
        self.assertTrue('foo' in self.RESPONSE.headers.keys())
        self.assertTrue('bar' in self.RESPONSE.headers.keys())

    def test_ownership(self):
        script = self._makeOne('testDTML', 'testDTML.dtml')
        script = script.__of__(self.app)
        # fsdtmlmethod has no owner
        owner_tuple = script.getOwnerTuple()
        self.assertEqual(owner_tuple, None)

        # and ownership is not acquired [CMF/450]
        self.app._owner = ('/foobar', 'baz')
        owner_tuple = script.getOwnerTuple()
        self.assertEqual(owner_tuple, None)

    def test_304_response_from_cpm(self):
        # test that we get a 304 response from the cpm via this template
        mod_time = DateTime()
        cpm = DummyCachingManagerWithPolicy()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)
        content = DummyContent(id='content')
        content.modified_date = mod_time
        content = content.__of__(self.app)
        script = self._makeOne('testDTML', 'testDTML.dtml')
        script = script.__of__(content)
        self.REQUEST.environ['IF_MODIFIED_SINCE'
                            ] = '%s;' % rfc1123_date(mod_time + 3600)
        data = script(content, self.REQUEST, self.RESPONSE)

        self.assertEqual(data, '')
        self.assertEqual(self.RESPONSE.getStatus(), 304)


class FSDTMLMethodCustomizationTests(SecurityTest, FSDTMLMaker):

    def setUp(self):
        FSDTMLMaker.setUp(self)
        SecurityTest.setUp(self)
        self.skins, self.custom, self.fsdir, self.fsDTML = self._makeContext(
                                                   'testDTML', 'testDTML.dtml')

    def tearDown(self):
        cleanUp()
        SecurityTest.tearDown(self)
        FSDTMLMaker.tearDown(self)

    def test_customize(self):

        self.fsDTML.manage_doCustomize(folder_path='custom')

        self.assertEqual(len(self.custom.objectIds()), 1)
        self.assertTrue('testDTML' in self.custom.objectIds())

    def test_customize_alternate_root(self):
        self.app.other = Folder('other')

        self.fsDTML.manage_doCustomize(folder_path='other', root=self.app)

        self.assertFalse('testDTML' in self.custom.objectIds())
        self.assertTrue('testDTML' in self.app.other.objectIds())

    def test_customize_fspath_as_dot(self):

        self.fsDTML.manage_doCustomize(folder_path='.')

        self.assertFalse('testDTML' in self.custom.objectIds())
        self.assertTrue('testDTML' in self.skins.objectIds())

    def test_customize_manual_clone(self):
        clone = Folder('testDTML')

        self.fsDTML.manage_doCustomize(folder_path='custom', obj=clone)

        self.assertTrue('testDTML' in self.custom.objectIds())
        self.assertTrue(aq_base(self.custom._getOb('testDTML')) is clone)

    def test_customize_caching(self):
        # Test to ensure that cache manager associations survive customizing
        cache_id = 'gofast'
        RAMCacheManager.manage_addRAMCacheManager(self.app, cache_id,
                                                  REQUEST=None)
        self.fsDTML.ZCacheable_setManagerId(cache_id, REQUEST=None)

        self.assertEqual(self.fsDTML.ZCacheable_getManagerId(), cache_id)

        self.fsDTML.manage_doCustomize(folder_path='custom')
        custom_pt = self.custom.testDTML

        self.assertEqual(custom_pt.ZCacheable_getManagerId(), cache_id)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FSDTMLMethodTests),
        unittest.makeSuite(FSDTMLMethodCustomizationTests),
        ))
