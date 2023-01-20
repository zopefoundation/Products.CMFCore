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
""" Unit tests for FSSTXMethod module.
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


class FSSTXMaker(FSDVTest):

    def _makeOne(self, id, filename):
        from ..FSMetadata import FSMetadata
        from ..FSSTXMethod import FSSTXMethod

        path = os.path.join(self.skin_path_name, filename)
        metadata = FSMetadata(path)
        metadata.read()
        return FSSTXMethod(id, path, properties=metadata.getProperties())


_EXPECTED_HTML = """\
<html>
<body>

<h1>Title Goes Here</h1>
<h2>  Subhead Here</h2>
<p>    And this is a paragraph,
    broken across lines.</p>

</body>
</html>
"""

_TEST_MAIN_TEMPLATE = """\
<html metal:define-macro="master">
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


class _TemplateSwitcher:

    def setUp(self):
        from .. import FSSTXMethod
        self._old_STX_TEMPLATE = FSSTXMethod._STX_TEMPLATE

    def tearDown(self):
        self._setWhichTemplate(self._old_STX_TEMPLATE)
        TransactionalTest.tearDown(self)
        FSSTXMaker.tearDown(self)

    def _setWhichTemplate(self, which):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate

        from .. import FSSTXMethod
        FSSTXMethod._STX_TEMPLATE = which

        if which == 'DTML':
            self.app.standard_html_header = (
                    lambda *args, **kw: '<html>\n<body>\n')
            self.app.standard_html_footer = (
                    lambda *args, **kw: '</body>\n</html>\n')
        elif which == 'ZPT':
            main = ZopePageTemplate('main_template', _TEST_MAIN_TEMPLATE)
            self.app._setOb('main_template', main)


class FSSTXMethodTests(TransactionalTest, FSSTXMaker, _TemplateSwitcher):

    layer = TraversingZCMLLayer

    def setUp(self):
        _TemplateSwitcher.setUp(self)
        TransactionalTest.setUp(self)
        FSSTXMaker.setUp(self)

    def tearDown(self):
        FSSTXMaker.tearDown(self)
        _TemplateSwitcher.tearDown(self)
        TransactionalTest.tearDown(self)

    def test___call___with_DTML(self):
        self._setWhichTemplate('DTML')
        script = self._makeOne('testSTX', 'testSTX.stx')
        script = script.__of__(self.app)
        self.assertEqual(_normalize_whitespace(script(self.REQUEST)),
                         _normalize_whitespace(_EXPECTED_HTML))

    def test___call___with_ZPT(self):
        self._setWhichTemplate('ZPT')
        script = self._makeOne('testSTX', 'testSTX.stx')
        script = script.__of__(self.app)
        self.assertEqual(_normalize_whitespace(script(self.REQUEST)),
                         _normalize_whitespace(_EXPECTED_HTML))

    def test_caching(self):
        #   Test HTTP caching headers.
        self._setWhichTemplate('DTML')
        cpm = DummyCachingManager()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)
        original_len = len(self.RESPONSE.headers)
        obj = self._makeOne('testSTX', 'testSTX.stx')
        obj = obj.__of__(self.app)
        obj(self.REQUEST, self.RESPONSE)
        self.assertTrue(len(self.RESPONSE.headers) >= original_len + 2)
        self.assertTrue('foo' in self.RESPONSE.headers)
        self.assertTrue('bar' in self.RESPONSE.headers)

    def test_ownership(self):
        script = self._makeOne('testSTX', 'testSTX.stx')
        script = script.__of__(self.app)
        # FSSTXMethod has no owner
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
        script = self._makeOne('testSTX', 'testSTX.stx')
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


class FSSTXMethodCustomizationTests(SecurityTest,
                                    FSSTXMaker,
                                    _TemplateSwitcher):

    def setUp(self):
        _TemplateSwitcher.setUp(self)
        SecurityTest.setUp(self)
        FSSTXMaker.setUp(self)
        self.skins, self.custom, self.fsdir, self.fsSTX = self._makeContext(
                                                      'testSTX', 'testSTX.stx')

    def tearDown(self):
        cleanUp()
        FSSTXMaker.tearDown(self)
        _TemplateSwitcher.tearDown(self)
        SecurityTest.tearDown(self)

    def test_customize_alternate_root(self):
        from OFS.Folder import Folder

        self._setWhichTemplate('DTML')
        self.app.other = Folder('other')

        self.fsSTX.manage_doCustomize(folder_path='other', root=self.app)

        self.assertFalse('testSTX' in self.custom.objectIds())
        self.assertTrue('testSTX' in self.app.other.objectIds())

    def test_customize_fspath_as_dot(self):
        self._setWhichTemplate('DTML')

        self.fsSTX.manage_doCustomize(folder_path='.')

        self.assertFalse('testSTX' in self.custom.objectIds())
        self.assertTrue('testSTX' in self.skins.objectIds())

    def test_customize_manual_clone(self):
        from OFS.Folder import Folder

        clone = Folder('testSTX')

        self._setWhichTemplate('DTML')

        self.fsSTX.manage_doCustomize(folder_path='custom', obj=clone)

        self.assertTrue('testSTX' in self.custom.objectIds())
        self.assertTrue(aq_base(self.custom._getOb('testSTX')) is clone)

    def test_customize_with_DTML(self):
        from OFS.DTMLDocument import DTMLDocument

        from ..FSSTXMethod import _CUSTOMIZED_TEMPLATE_DTML

        self._setWhichTemplate('DTML')

        self.fsSTX.manage_doCustomize(folder_path='custom')

        self.assertEqual(len(self.custom.objectIds()), 1)
        self.assertTrue('testSTX' in self.custom.objectIds())
        target = self.custom._getOb('testSTX')

        self.assertTrue(isinstance(target, DTMLDocument))

        propinfo = target.propdict()['stx']
        self.assertEqual(propinfo['type'], 'text')
        self.assertEqual(target.stx, self.fsSTX.raw)

        self.assertEqual(target.document_src(), _CUSTOMIZED_TEMPLATE_DTML)

    def test_customize_with_ZPT(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate

        from ..FSSTXMethod import _CUSTOMIZED_TEMPLATE_ZPT

        self._setWhichTemplate('ZPT')
        self.custom.all_meta_types = ZPT_META_TYPES

        self.fsSTX.manage_doCustomize(folder_path='custom')

        self.assertEqual(len(self.custom.objectIds()), 1)
        self.assertTrue('testSTX' in self.custom.objectIds())
        target = self.custom._getOb('testSTX')

        self.assertTrue(isinstance(target, ZopePageTemplate))

        propinfo = target.propdict()['stx']
        self.assertEqual(propinfo['type'], 'text')
        self.assertEqual(target.stx, self.fsSTX.raw)

        self.assertEqual(_normalize_whitespace(target.document_src()),
                         _normalize_whitespace(_CUSTOMIZED_TEMPLATE_ZPT))

    def test_customize_caching(self):
        # Test to ensure that cache manager associations survive customizing
        from Products.StandardCacheManagers import RAMCacheManager
        cache_id = 'gofast'
        self._setWhichTemplate('ZPT')
        self.custom.all_meta_types = ZPT_META_TYPES
        RAMCacheManager.manage_addRAMCacheManager(self.app, cache_id,
                                                  REQUEST=None)
        self.fsSTX.ZCacheable_setManagerId(cache_id, REQUEST=None)

        self.assertEqual(self.fsSTX.ZCacheable_getManagerId(), cache_id)

        self.fsSTX.manage_doCustomize(folder_path='custom')
        custom_pt = self.custom.testSTX

        self.assertEqual(custom_pt.ZCacheable_getManagerId(), cache_id)


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(FSSTXMethodTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            FSSTXMethodCustomizationTests),
        ))
