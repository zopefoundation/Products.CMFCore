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
""" Unit tests for FSImage module.
"""

import os
import unittest
from os.path import join as path_join

from zope.component import getSiteManager
from zope.datetime import rfc1123_date
from zope.testing.cleanup import cleanUp

from ..interfaces import ICachingPolicyManager
from .base.dummy import FAKE_ETAG
from .base.dummy import DummyCachingManager
from .base.dummy import DummyCachingManagerWithPolicy
from .base.testcase import FSDVTest
from .base.testcase import TransactionalTest


class FSImageTests(TransactionalTest, FSDVTest):

    def setUp(self):
        TransactionalTest.setUp(self)
        FSDVTest.setUp(self)

    def tearDown(self):
        cleanUp()
        FSDVTest.tearDown(self)
        TransactionalTest.tearDown(self)

    def _makeOne(self, id, filename):
        from ..FSImage import FSImage

        return FSImage(id, path_join(self.skin_path_name, filename))

    def _extractFile(self):
        path = path_join(self.skin_path_name, 'test_image.gif')
        f = open(path, 'rb')
        try:
            data = f.read()
        finally:
            f.close()

        return path, data

    def test_ctor(self):
        _path, ref = self._extractFile()

        image = self._makeOne('test_image', 'test_image.gif')
        image = image.__of__(self.app)

        self.assertEqual(image.get_size(), len(ref))
        self.assertEqual(image._data, ref)

    def test_index_html(self):
        path, ref = self._extractFile()
        mod_time = os.stat(path)[8]

        image = self._makeOne('test_image', 'test_image.gif')
        image = image.__of__(self.app)

        data = image.index_html(self.REQUEST, self.RESPONSE)

        self.assertEqual(len(data), len(ref))
        self.assertEqual(data, ref)
        # ICK!  'HTTPResponse.getHeader' doesn't case-flatten the key!
        self.assertEqual(self.RESPONSE.getHeader('Content-Length'.lower()),
                         str(len(ref)))
        self.assertEqual(self.RESPONSE.getHeader('Content-Type'.lower()),
                         'image/gif')
        self.assertEqual(self.RESPONSE.getHeader('Last-Modified'.lower()),
                         rfc1123_date(mod_time))

    def test_index_html_with_304(self):
        path, _ref = self._extractFile()
        mod_time = os.stat(path)[8]

        image = self._makeOne('test_image', 'test_image.gif')
        image = image.__of__(self.app)

        self.REQUEST.environ['IF_MODIFIED_SINCE'] = \
            '%s;' % rfc1123_date(mod_time + 3600)

        data = image.index_html(self.REQUEST, self.RESPONSE)

        self.assertEqual(data, '')
        # test that we don't supply a content-length
        self.assertEqual(self.RESPONSE.getHeader('Content-Length'.lower()),
                         None)
        self.assertEqual(self.RESPONSE.getStatus(), 304)

    def test_index_html_without_304(self):
        path, _ref = self._extractFile()
        mod_time = os.stat(path)[8]

        image = self._makeOne('test_image', 'test_image.gif')
        image = image.__of__(self.app)

        self.REQUEST.environ['IF_MODIFIED_SINCE'] = '%s;' % \
            rfc1123_date(mod_time - 3600)

        data = image.index_html(self.REQUEST, self.RESPONSE)

        self.assertTrue(data, '')
        self.assertEqual(self.RESPONSE.getStatus(), 200)

    def test_index_html_with_304_from_cpm(self):
        cpm = DummyCachingManagerWithPolicy()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)
        path, _ref = self._extractFile()
        file = self._makeOne('test_file', 'test_image.gif')
        file = file.__of__(self.app)

        mod_time = os.stat(path).st_mtime

        self.REQUEST.environ['IF_MODIFIED_SINCE'] = '%s;' % \
            rfc1123_date(mod_time)
        self.REQUEST.environ['IF_NONE_MATCH'] = '%s;' % FAKE_ETAG

        data = file.index_html(self.REQUEST, self.RESPONSE)
        self.assertEqual(len(data), 0)
        self.assertEqual(self.RESPONSE.getStatus(), 304)
        self.assertNotEqual(self.RESPONSE.getHeader('x-cache-headers-set-by'),
                            None)

    def test_index_html_200_with_cpm(self):
        # should behave the same as without cpm installed
        cpm = DummyCachingManagerWithPolicy()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)
        path, ref = self._extractFile()
        file = self._makeOne('test_file', 'test_image.gif')
        file = file.__of__(self.app)

        mod_time = os.stat(path).st_mtime

        data = file.index_html(self.REQUEST, self.RESPONSE)

        self.assertEqual(len(data), len(ref))
        self.assertEqual(data, ref)
        # ICK!  'HTTPResponse.getHeader' doesn't case-flatten the key!
        self.assertEqual(self.RESPONSE.getHeader('Content-Length'.lower()),
                         str(len(ref)))
        self.assertEqual(self.RESPONSE.getHeader('Content-Type'.lower()),
                         'image/gif')
        self.assertEqual(self.RESPONSE.getHeader('Last-Modified'.lower()),
                         rfc1123_date(mod_time))

    def test_caching(self):
        cpm = DummyCachingManager()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)
        original_len = len(self.RESPONSE.headers)
        obj = self._makeOne('test_image', 'test_image.gif')
        obj = obj.__of__(self.app)
        obj.index_html(self.REQUEST, self.RESPONSE)
        headers = self.RESPONSE.headers
        self.assertTrue(len(headers) >= original_len + 3)
        self.assertTrue('foo' in headers)
        self.assertTrue('bar' in headers)
        self.assertEqual(headers['test_path'], '/test_image')

    def test_index_html_with_304_and_caching(self):
        # See collector #355
        cpm = DummyCachingManager()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)
        original_len = len(self.RESPONSE.headers)
        path, _ref = self._extractFile()
        image = self._makeOne('test_image', 'test_image.gif')
        image = image.__of__(self.app)

        mod_time = os.stat(path)[8]

        self.REQUEST.environ['IF_MODIFIED_SINCE'] = '%s;' % \
            rfc1123_date(mod_time + 3600)

        data = image.index_html(self.REQUEST, self.RESPONSE)

        self.assertEqual(data, '')
        self.assertEqual(self.RESPONSE.getStatus(), 304)

        headers = self.RESPONSE.headers
        self.assertTrue(len(headers) >= original_len + 3)
        self.assertTrue('foo' in headers)
        self.assertTrue('bar' in headers)
        self.assertEqual(headers['test_path'], '/test_image')

    def test_tag_with_acquired_clashing_attrs(self):
        # See http://www.zope.org/Collectors/CMF/507
        class Clash:
            def __str__(self):
                raise NotImplementedError

        self.app.alt = Clash()
        self.app.height = Clash()
        self.app.width = Clash()

        image = self._makeOne('test_image', 'test_image.gif')
        image = image.__of__(self.app)

        tag = image.tag()
        self.assertTrue('alt=""' in tag)

    def test_unnecessary_invalidation_avoidance(self):
        # See https://bugs.launchpad.net/zope-cmf/+bug/325246
        invalidated = []

        def fake_invalidate(*args, **kw):
            invalidated.append(True)

        image = self._makeOne('test_image', 'test_image.gif')
        image.ZCacheable_invalidate = fake_invalidate

        # First pass: The images internal file modification representation
        # equals the filesystem modification time.
        del invalidated[:]
        image._readFile(True)
        self.assertFalse(invalidated)

        del invalidated[:]
        image._parsed = False
        image._updateFromFS()
        self.assertFalse(invalidated)

        # Second pass: Forcing a different internal file modification
        # time onto the image instance. Now the image will be invalidated.
        del invalidated[:]
        image._file_mod_time = 0
        image._readFile(True)
        self.assertTrue(invalidated)

        del invalidated[:]
        image._file_mod_time = 0
        image._parsed = False
        image._updateFromFS()
        self.assertTrue(invalidated)


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(FSImageTests),
        ))
