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
""" Unit tests for FSPageTemplate module.
"""

import unittest
from os.path import join as path_join

from Acquisition import aq_base
from OFS.Folder import Folder
from Testing import ZopeTestCase
from zope.component import getSiteManager
from zope.tales.tales import Undefined
from zope.testing.cleanup import cleanUp

from Products.StandardCacheManagers import RAMCacheManager

from ..FSMetadata import FSMetadata
from ..interfaces import ICachingPolicyManager
from ..testing import TraversingZCMLLayer
from .base.dummy import DummyCachingManager
from .base.testcase import FSDVTest
from .base.testcase import SecurityTest
from .base.testcase import TransactionalTest


ZopeTestCase.installProduct('PageTemplates', 1)


class FSPTMaker(FSDVTest):

    def _makeOne(self, id, filename):
        from ..FSPageTemplate import FSPageTemplate

        path = path_join(self.skin_path_name, filename)
        metadata = FSMetadata(path)
        metadata.read()
        return FSPageTemplate(id, path, properties=metadata.getProperties())


class FSPageTemplateTests(TransactionalTest, FSPTMaker):

    layer = TraversingZCMLLayer

    def setUp(self):
        TransactionalTest.setUp(self)
        FSPTMaker.setUp(self)

    def tearDown(self):
        FSPTMaker.tearDown(self)
        TransactionalTest.tearDown(self)

    def test___call__(self):
        script = self._makeOne('testPT', 'testPT.pt')
        script = script.__of__(self.app)
        self.assertEqual(script(), 'nohost')

    def test_ContentType(self):
        script = self._makeOne('testXMLPT', 'testXMLPT.pt')
        script = script.__of__(self.app)
        script()
        self.assertEqual(script.content_type, 'text/xml; charset=utf-8')
        self.assertEqual(self.RESPONSE.getHeader('content-type'),
                         'text/xml; charset=utf-8')
        # purge RESPONSE Content-Type header for new test
        del self.RESPONSE.headers['content-type']
        script = self._makeOne('testPT', 'testPT.pt')
        script = script.__of__(self.app)
        script()
        self.assertEqual(script.content_type, 'text/html')
        self.assertEqual(self.RESPONSE.getHeader('content-type'),
                         'text/html; charset=utf-8')

    def test_ContentTypeDetection(self):
        script = self._makeOne(
            'testXMLPT_with_encoding', 'testXMLPT_with_encoding.pt')
        script = script.__of__(self.app)
        script()
        self.assertEqual(script.content_type, 'text/xml; charset=utf-8')
        self.assertEqual(self.RESPONSE.getHeader('content-type'),
                         'text/xml; charset=utf-8')

    def test_ContentTypeOverride(self):
        script = self._makeOne('testPT_utf8', 'testPT_utf8.pt')
        script = script.__of__(self.app)
        script()
        self.assertEqual(self.RESPONSE.getHeader('content-type'),
                         'text/html; charset=utf-8')

    def test_ContentTypeFromFSMetadata(self):
        # Test to see if a content_type specified in a .metadata file
        # is respected
        script = self._makeOne('testPT2', 'testPT2.pt')
        script = script.__of__(self.app)
        script()
        self.assertEqual(self.RESPONSE.getHeader('content-type'),
                         'text/xml; charset=utf-8')

    def test_CharsetFromFSMetadata(self):
        # testPT3 is an UTF-16 encoded file (see its .metadatafile)
        # is respected
        unencoded = '123\xfc\xf6\xe4\xdf'
        script = self._makeOne('testPT3', 'testPT3.pt')
        script = script.__of__(self.app)
        script.charset = 'utf-16'
        data = script.read()
        self.assertTrue(unencoded in data)
        self.assertEqual(script.content_type, 'text/html')

    def test_CharsetFrom2FSMetadata(self):
        # testPT4 is an UTF-8 encoded file (see its .metadatafile)
        # is respected
        unencoded = '123\xfc\xf6\xe4\xdf'
        script = self._makeOne('testPT4', 'testPT4.pt')
        script = script.__of__(self.app)
        data = script.read()
        self.assertTrue(unencoded in data)
        self.assertEqual(script.content_type, 'text/html')

    def test_CharsetFromContentTypeMetadata(self):
        unencoded = '123\xfc\xf6\xe4\xdf'
        script = self._makeOne('testPT5', 'testPT5.pt')
        script = script.__of__(self.app)
        data = script.read()
        self.assertTrue(unencoded in data)
        self.assertEqual(script.content_type, 'text/html; charset=utf-16')

    def test_BadCall(self):
        script = self._makeOne('testPTbad', 'testPTbad.pt')
        script = script.__of__(self.app)

        try:  # can't use assertRaises, because different types raised.
            script()
        except (Undefined, KeyError):
            pass
        else:
            self.fail('Calling a bad template did not raise an exception')

    def test_caching(self):
        #   Test HTTP caching headers.
        cpm = DummyCachingManager()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)
        original_len = len(self.RESPONSE.headers)
        obj = self._makeOne('testPT', 'testPT.pt')
        obj = obj.__of__(self.app)
        obj()
        self.assertTrue(len(self.RESPONSE.headers) >= original_len + 2)
        self.assertTrue('foo' in self.RESPONSE.headers)
        self.assertTrue('bar' in self.RESPONSE.headers)

    def test_pt_properties(self):
        script = self._makeOne('testPT', 'testPT.pt')
        self.assertEqual(script.pt_source_file(),
                         'file:%s' % path_join(self.skin_path_name,
                                               'testPT.pt'))

    def test_foreign_line_endings(self):
        # Lead the various line ending files and get their output
        for fformat in ('unix', 'dos', 'mac'):
            script = self._makeOne(fformat,
                                   'testPT_multiline_python_%s.pt' % fformat)
            script = script.__of__(self.app)
            self.assertEqual(script(), 'foo bar spam eggs\n')


class FSPageTemplateCustomizationTests(SecurityTest, FSPTMaker):

    def setUp(self):
        FSPTMaker.setUp(self)
        SecurityTest.setUp(self)
        self.skins, self.custom, self.fsdir, self.fsPT = self._makeContext(
                                                         'testPT', 'testPT.pt')

    def tearDown(self):
        cleanUp()
        SecurityTest.tearDown(self)
        FSPTMaker.tearDown(self)

    def test_customize(self):
        self.fsPT.manage_doCustomize(folder_path='custom')

        self.assertEqual(len(self.custom.objectIds()), 1)
        self.assertTrue('testPT' in self.custom.objectIds())

    def test_customize_alternate_root(self):
        self.app.other = Folder('other')

        self.fsPT.manage_doCustomize(folder_path='other', root=self.app)

        self.assertFalse('testPT' in self.custom.objectIds())
        self.assertTrue('testPT' in self.app.other.objectIds())

    def test_customize_fspath_as_dot(self):
        self.fsPT.manage_doCustomize(folder_path='.')

        self.assertFalse('testPT' in self.custom.objectIds())
        self.assertTrue('testPT' in self.skins.objectIds())

    def test_customize_manual_clone(self):
        clone = Folder('testPT')

        self.fsPT.manage_doCustomize(folder_path='custom', obj=clone)

        self.assertTrue('testPT' in self.custom.objectIds())
        self.assertTrue(aq_base(self.custom._getOb('testPT')) is clone)

    def test_customize_caching(self):
        # Test to ensure that cache manager associations survive customizing
        cache_id = 'gofast'
        RAMCacheManager.manage_addRAMCacheManager(self.app, cache_id,
                                                  REQUEST=None)
        self.fsPT.ZCacheable_setManagerId(cache_id, REQUEST=None)

        self.assertEqual(self.fsPT.ZCacheable_getManagerId(), cache_id)

        self.fsPT.manage_doCustomize(folder_path='custom')
        custom_pt = self.custom.testPT

        self.assertEqual(custom_pt.ZCacheable_getManagerId(), cache_id)

    def test_dontExpandOnCreation(self):
        self.fsPT.manage_doCustomize(folder_path='custom')

        customized = self.custom.testPT
        self.assertFalse(customized.expand)


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(FSPageTemplateTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            FSPageTemplateCustomizationTests),
        ))
