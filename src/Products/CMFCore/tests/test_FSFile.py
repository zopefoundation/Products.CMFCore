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
""" Unit tests for FSFile module.
"""

import os
import unittest
import warnings

from zope.component import getSiteManager
from zope.datetime import rfc1123_date
from zope.testing.cleanup import cleanUp

from ..interfaces import ICachingPolicyManager
from .base.dummy import FAKE_ETAG
from .base.dummy import DummyCachingManager
from .base.dummy import DummyCachingManagerWithPolicy
from .base.testcase import FSDVTest
from .base.testcase import TransactionalTest


class FSFileTests(TransactionalTest, FSDVTest):

    def setUp(self):
        TransactionalTest.setUp(self)
        FSDVTest.setUp(self)

    def tearDown(self):
        cleanUp()
        FSDVTest.tearDown(self)
        TransactionalTest.tearDown(self)

    def _makeOne(self, id, filename):
        from ..FSFile import FSFile
        from ..FSMetadata import FSMetadata

        full_path = os.path.join(self.skin_path_name, filename)
        metadata = FSMetadata(full_path)
        metadata.read()
        return FSFile(id, full_path, properties=metadata.getProperties())

    def _extractFile(self, filename):
        path = os.path.join(self.skin_path_name, filename)
        f = open(path, 'rb')
        try:
            data = f.read()
        finally:
            f.close()

        return path, data

    def test_ctor(self):
        _path, ref = self._extractFile('test_file.swf')

        file = self._makeOne('test_file', 'test_file.swf')
        file = file.__of__(self.app)

        self.assertEqual(file.get_size(), len(ref))
        self.assertEqual(file._readFile(0), ref)

    def test_bytes(self):
        _path, ref = self._extractFile('test_file.swf')
        file = self._makeOne('test_file', 'test_file.swf')
        file = file.__of__(self.app)
        self.assertEqual(len(bytes(file)), len(bytes(ref)))

    def test_str(self):
        from ZPublisher.HTTPRequest import default_encoding

        encoded = b'Th\xc3\xaes \xc3\xaes s\xc3\xb6me t\xc3\xa9xt.'

        # This file contains UTF-8 text data
        file = self._makeOne('test_text', 'test_text.txt')
        data = str(file).strip()

        self.assertIsInstance(data, str)
        self.assertEqual(data, encoded.decode(default_encoding))

        # This file contains latin-1 test data
        file = self._makeOne('test_text', 'test_text_latin1.txt')
        data = str(file).strip()

        self.assertIsInstance(data, str)
        self.assertEqual(data, encoded.decode(default_encoding))

        # This file contains non-text binary data
        file = self._makeOne('test_binary', 'test_image.gif')
        _path, real_data = self._extractFile('test_image.gif')

        self.assertIsInstance(data, str)
        # Calling ``__str__`` on non-text binary data
        # will raise a DeprecationWarning because it makes no sense.
        # Ignore it here, the warning is irrelevant for the test.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.assertRaises(UnicodeDecodeError, file.__str__)

    def test_index_html(self):
        path, ref = self._extractFile('test_file.swf')
        mod_time = os.stat(path)[8]

        file = self._makeOne('test_file', 'test_file.swf')
        file = file.__of__(self.app)

        data = file.index_html(self.REQUEST, self.RESPONSE)

        self.assertEqual(len(data), len(ref))
        self.assertEqual(data, ref)
        # ICK!  'HTTPResponse.getHeader' doesn't case-flatten the key!
        self.assertEqual(self.RESPONSE.getHeader('Content-Length'.lower()),
                         str(len(ref)))
        self.assertEqual(self.RESPONSE.getHeader('Content-Type'.lower()),
                         'application/octet-stream')
        self.assertEqual(self.RESPONSE.getHeader('Last-Modified'.lower()),
                         rfc1123_date(mod_time))

    def test_index_html_with_304(self):
        path, _ref = self._extractFile('test_file.swf')
        mod_time = os.stat(path)[8]

        file = self._makeOne('test_file', 'test_file.swf')
        file = file.__of__(self.app)

        self.REQUEST.environ['IF_MODIFIED_SINCE'] = '%s;' % \
            rfc1123_date(mod_time + 3600)

        data = file.index_html(self.REQUEST, self.RESPONSE)

        self.assertEqual(data, '')
        # test that we don't supply a content-length
        self.assertEqual(self.RESPONSE.getHeader('Content-Length'.lower()),
                         None)
        self.assertEqual(self.RESPONSE.getStatus(), 304)

    def test_index_html_without_304(self):
        path, _ref = self._extractFile('test_file.swf')
        mod_time = os.stat(path)[8]

        file = self._makeOne('test_file', 'test_file.swf')
        file = file.__of__(self.app)

        self.REQUEST.environ['IF_MODIFIED_SINCE'] = '%s;' % \
            rfc1123_date(mod_time - 3600)

        data = file.index_html(self.REQUEST, self.RESPONSE)

        self.assertTrue(data, '')
        self.assertEqual(self.RESPONSE.getStatus(), 200)

    def test_index_html_with_304_from_cpm(self):
        cpm = DummyCachingManagerWithPolicy()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)
        path, _ref = self._extractFile('test_file.swf')
        file = self._makeOne('test_file', 'test_file.swf')
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
        path, ref = self._extractFile('test_file.swf')
        file = self._makeOne('test_file', 'test_file.swf')
        file = file.__of__(self.app)

        mod_time = os.stat(path).st_mtime

        data = file.index_html(self.REQUEST, self.RESPONSE)

        self.assertEqual(len(data), len(ref))
        self.assertEqual(data, ref)
        # ICK!  'HTTPResponse.getHeader' doesn't case-flatten the key!
        self.assertEqual(self.RESPONSE.getHeader('Content-Length'.lower()),
                         str(len(ref)))
        self.assertEqual(self.RESPONSE.getHeader('Content-Type'.lower()),
                         'application/octet-stream')
        self.assertEqual(self.RESPONSE.getHeader('Last-Modified'.lower()),
                         rfc1123_date(mod_time))

    def test_caching(self):
        cpm = DummyCachingManager()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)
        original_len = len(self.RESPONSE.headers)
        obj = self._makeOne('test_file', 'test_file.swf')
        obj = obj.__of__(self.app)
        obj.index_html(self.REQUEST, self.RESPONSE)
        headers = self.RESPONSE.headers
        self.assertTrue(len(headers) >= original_len + 3)
        self.assertTrue('foo' in headers)
        self.assertTrue('bar' in headers)
        self.assertEqual(headers['test_path'], '/test_file')

    def test_forced_content_type(self):
        path, ref = self._extractFile('test_file_two.swf')
        mod_time = os.stat(path)[8]

        file = self._makeOne('test_file', 'test_file_two.swf')
        file = file.__of__(self.app)

        data = file.index_html(self.REQUEST, self.RESPONSE)

        self.assertEqual(len(data), len(ref))
        self.assertEqual(data, ref)
        # ICK!  'HTTPResponse.getHeader' doesn't case-flatten the key!
        self.assertEqual(self.RESPONSE.getHeader('Content-Length'.lower()),
                         str(len(ref)))
        self.assertEqual(self.RESPONSE.getHeader('Content-Type'.lower()),
                         'application/x-shockwave-flash')
        self.assertEqual(self.RESPONSE.getHeader('Last-Modified'.lower()),
                         rfc1123_date(mod_time))

    def test_utf8charset_detection(self):
        import mimetypes

        file_name = 'testUtf8.js'
        mtype, _ignore_enc = mimetypes.guess_type(file_name)
        file = self._makeOne(file_name, file_name)
        file = file.__of__(self.app)
        file.index_html(self.REQUEST, self.RESPONSE)
        self.assertEqual(self.RESPONSE.getHeader('content-type'),
                         '%s; charset=utf-8' % mtype)

    def test_unnecessary_invalidation_avoidance(self):
        # See https://bugs.launchpad.net/zope-cmf/+bug/325246
        invalidated = []

        def fake_invalidate(*args, **kw):
            invalidated.append(True)

        file = self._makeOne('test_file', 'test_file.swf')
        file.ZCacheable_invalidate = fake_invalidate

        # First pass: The internal file modification representation
        # equals the filesystem modification time.
        del invalidated[:]
        file._readFile(True)
        self.assertFalse(invalidated)

        del invalidated[:]
        file._parsed = False
        file._updateFromFS()
        self.assertFalse(invalidated)

        # Second pass: Forcing a different internal file modification
        # time onto the instance. Now the file will be invalidated.
        del invalidated[:]
        file._file_mod_time = 0
        file._readFile(True)
        self.assertTrue(invalidated)

        del invalidated[:]
        file._file_mod_time = 0
        file._parsed = False
        file._updateFromFS()
        self.assertTrue(invalidated)


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(FSFileTests),
        ))
