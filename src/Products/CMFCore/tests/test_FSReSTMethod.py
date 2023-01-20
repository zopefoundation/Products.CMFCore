##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for FSReSTMethod module.
"""

import os
import re
import unittest

from Acquisition import aq_base
from DateTime import DateTime
from zope.component import getSiteManager
from zope.datetime import rfc1123_date
from zope.testing.cleanup import cleanUp

from ..interfaces import ICachingPolicyManager
from ..testing import TraversingZCMLLayer
from .base.dummy import DummyCachingManager
from .base.dummy import DummyCachingManagerWithPolicy
from .base.testcase import FSDVTest
from .base.testcase import SecurityTest
from .base.testcase import TransactionalTest


class FSReSTMaker(FSDVTest):

    def setUp(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate

        FSDVTest.setUp(self)
        main = ZopePageTemplate('main_template', _TEST_MAIN_TEMPLATE)
        self.app._setOb('main_template', main)

    def _makeOne(self, id, filename):
        from ..FSMetadata import FSMetadata
        from ..FSReSTMethod import FSReSTMethod

        path = os.path.join(self.skin_path_name, filename)
        metadata = FSMetadata(path)
        metadata.read()
        return FSReSTMethod(id, path, properties=metadata.getProperties())


_EXPECTED_HTML = """\
<html>
<body>

<div class="document" id="title-goes-here">
<h1 class="title">Title Goes Here</h1>
<h2 class="subtitle" id="subhead-here">Subhead Here</h2>
<p>And this is a paragraph,
    broken across lines.</p>

</div>

</body>
</html>
"""

_TEST_MAIN_TEMPLATE = """\
<html metal:define-macro="main">
<body>

<metal:block define-slot="body">
BODY GOES HERE
</metal:block>
</body>
</html>
"""

WS = re.compile(r'\s+')


def _normalize_whitespace(text):
    return ' '.join(WS.split(text.rstrip()))


class FSReSTMethodTests(TransactionalTest, FSReSTMaker):

    layer = TraversingZCMLLayer

    def setUp(self):
        TransactionalTest.setUp(self)
        FSReSTMaker.setUp(self)

    def tearDown(self):
        FSReSTMaker.tearDown(self)
        TransactionalTest.tearDown(self)

    def test___call__(self):
        script = self._makeOne('testReST', 'testReST.rst')
        script = script.__of__(self.app)
        self.assertEqual(_normalize_whitespace(script(self.REQUEST)),
                         _normalize_whitespace(_EXPECTED_HTML))

    def test_caching(self):
        #   Test HTTP caching headers.
        cpm = DummyCachingManager()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)
        original_len = len(self.RESPONSE.headers)
        obj = self._makeOne('testReST', 'testReST.rst')
        obj = obj.__of__(self.app)
        obj(self.REQUEST, self.RESPONSE)
        self.assertTrue(len(self.RESPONSE.headers) >= original_len + 2)
        self.assertTrue('foo' in self.RESPONSE.headers)
        self.assertTrue('bar' in self.RESPONSE.headers)

    def test_ownership(self):
        script = self._makeOne('testReST', 'testReST.rst')
        script = script.__of__(self.app)
        # FSReSTMethod has no owner
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
        script = self._makeOne('testReST', 'testReST.rst')
        script = script.__of__(self.app)
        self.REQUEST.environ['IF_MODIFIED_SINCE'] = '%s;' % \
            rfc1123_date(mod_time + 3600)
        data = script(self.REQUEST, self.RESPONSE)

        self.assertEqual(data, '')
        self.assertEqual(self.RESPONSE.getStatus(), 304)
        self.assertNotEqual(self.RESPONSE.getHeader('x-cache-headers-set-by'),
                            None)


ADD_ZPT = 'Add page templates'
ZPT_META_TYPES = ({'name': 'Page Template',
                   'action': 'manage_addPageTemplate',
                   'permission': ADD_ZPT},)


class FSReSTMethodCustomizationTests(SecurityTest, FSReSTMaker):

    def setUp(self):
        SecurityTest.setUp(self)
        FSReSTMaker.setUp(self)
        self.skins, self.custom, self.fsdir, self.fsReST = self._makeContext(
                                                    'testReST', 'testReST.rst')

    def tearDown(self):
        cleanUp()
        FSReSTMaker.tearDown(self)
        SecurityTest.tearDown(self)

    def test_customize(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate

        from ..FSReSTMethod import _CUSTOMIZED_TEMPLATE_ZPT

        self.custom.all_meta_types = ZPT_META_TYPES

        self.fsReST.manage_doCustomize(folder_path='custom')

        self.assertEqual(len(self.custom.objectIds()), 1)
        self.assertTrue('testReST' in self.custom.objectIds())
        target = self.custom._getOb('testReST')

        self.assertTrue(isinstance(target, ZopePageTemplate))

        propinfo = target.propdict()['rest']
        self.assertEqual(propinfo['type'], 'text')
        self.assertEqual(target.rest, self.fsReST.raw)

        self.assertEqual(_normalize_whitespace(target.document_src()),
                         _normalize_whitespace(_CUSTOMIZED_TEMPLATE_ZPT))

    def test_customize_alternate_root(self):
        from OFS.Folder import Folder

        self.app.other = Folder('other')

        self.fsReST.manage_doCustomize(folder_path='other', root=self.app)

        self.assertFalse('testReST' in self.custom.objectIds())
        self.assertTrue('testReST' in self.app.other.objectIds())

    def test_customize_fpath_as_dot(self):

        self.fsReST.manage_doCustomize(folder_path='.')

        self.assertFalse('testReST' in self.custom.objectIds())
        self.assertTrue('testReST' in self.skins.objectIds())

    def test_customize_manual_clone(self):
        from OFS.Folder import Folder

        clone = Folder('testReST')

        self.fsReST.manage_doCustomize(folder_path='custom', obj=clone)

        self.assertTrue('testReST' in self.custom.objectIds())
        self.assertTrue(aq_base(self.custom._getOb('testReST')) is clone)

    def test_customize_caching(self):
        # Test to ensure that cache manager associations survive customizing
        from Products.StandardCacheManagers import RAMCacheManager
        cache_id = 'gofast'
        self.custom.all_meta_types = ZPT_META_TYPES
        RAMCacheManager.manage_addRAMCacheManager(self.app, cache_id,
                                                  REQUEST=None)
        self.fsReST.ZCacheable_setManagerId(cache_id, REQUEST=None)

        self.assertEqual(self.fsReST.ZCacheable_getManagerId(), cache_id)

        self.fsReST.manage_doCustomize(folder_path='custom')
        custom_pt = self.custom.testReST

        self.assertEqual(custom_pt.ZCacheable_getManagerId(), cache_id)


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(FSReSTMethodTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            FSReSTMethodCustomizationTests),
        ))
