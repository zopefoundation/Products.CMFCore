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
"""Caching policy manager xml adapter and setup handler unit tests.
"""

import unittest

from OFS.Folder import Folder
from zope.component import getSiteManager

from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.testing import NodeAdapterTestCase
from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from ...CachingPolicyManager import CachingPolicyManager
from ...interfaces import ICachingPolicyManager
from ...testing import ExportImportZCMLLayer


_CP_XML = b"""\
<caching-policy name="foo_policy" enable_304s="False" etag_func=""
   last_modified="True" max_age_secs="0" mtime_func="object/modified"
   must_revalidate="False" no_cache="False" no_store="False"
   no_transform="False" predicate="python:1" private="False"
   proxy_revalidate="False" public="False" vary=""/>
"""

_CPM_BODY = b"""\
<?xml version="1.0" encoding="utf-8"?>
<object name="caching_policy_manager" meta_type="CMF Caching Policy Manager">
 <caching-policy name="foo_policy" enable_304s="False" etag_func=""
    last_modified="True" max_age_secs="600" mtime_func="object/modified"
    must_revalidate="False" no_cache="False" no_store="False"
    no_transform="False"
    predicate="python:object.getPortalTypeName() == &#x27;Foo&#x27;"
    private="False" proxy_revalidate="False" public="False" vary=""/>
</object>
"""


class CachingPolicyNodeAdapterTests(NodeAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..cachingpolicymgr import CachingPolicyNodeAdapter

        return CachingPolicyNodeAdapter

    def setUp(self):
        from ...CachingPolicyManager import CachingPolicy

        self._obj = CachingPolicy('foo_policy', max_age_secs=0)
        self._XML = _CP_XML


class CachingPolicyManagerXMLAdapterTests(BodyAdapterTestCase,
                                          unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from ..cachingpolicymgr import CachingPolicyManagerXMLAdapter

        return CachingPolicyManagerXMLAdapter

    def _populate(self, obj):
        obj.addPolicy('foo_policy',
                      "python:object.getPortalTypeName() == 'Foo'",
                      'object/modified', 600, 0, 0, 0, '', '')

    def setUp(self):
        self._obj = CachingPolicyManager()
        self._BODY = _CPM_BODY


class _CachingPolicyManagerSetup(BaseRegistryTests):

    POLICY_ID = 'policy_id'
    PREDICATE = "python:object.getId() == 'foo'"
    MTIME_FUNC = 'object/modified'
    MAX_AGE_SECS = 60
    VARY = 'Test'
    ETAG_FUNC = 'object/getETag'
    S_MAX_AGE_SECS = 120
    PRE_CHECK = 42
    POST_CHECK = 43

    _EMPTY_EXPORT = """\
<?xml version="1.0"?>
<object name="caching_policy_manager" meta_type="CMF Caching Policy Manager"/>
"""

    _WITH_POLICY_EXPORT = """\
<?xml version="1.0"?>
<object name="caching_policy_manager" meta_type="CMF Caching Policy Manager">
 <caching-policy name="%s" enable_304s="True"
    etag_func="%s" last_modified="False" max_age_secs="%d"
    mtime_func="%s" must_revalidate="True" no_cache="True"
    no_store="True" no_transform="True" post_check="%d" pre_check="%d"
    predicate="%s" private="True"
    proxy_revalidate="True" public="True" s_max_age_secs="%d" vary="%s"/>
</object>
""" % (POLICY_ID, ETAG_FUNC, MAX_AGE_SECS, MTIME_FUNC, POST_CHECK, PRE_CHECK,
       PREDICATE, S_MAX_AGE_SECS, VARY)

    def _initSite(self, with_policy=False):
        site = Folder(id='site').__of__(self.app)
        cpm = CachingPolicyManager()
        getSiteManager().registerUtility(cpm, ICachingPolicyManager)

        if with_policy:
            cpm.addPolicy(policy_id=self.POLICY_ID,
                          predicate=self.PREDICATE,
                          mtime_func=self.MTIME_FUNC,
                          max_age_secs=self.MAX_AGE_SECS,
                          no_cache=True,
                          no_store=True,
                          must_revalidate=True,
                          vary=self.VARY,
                          etag_func=self.ETAG_FUNC,
                          s_max_age_secs=self.S_MAX_AGE_SECS,
                          proxy_revalidate=True,
                          public=True,
                          private=True,
                          no_transform=True,
                          enable_304s=True,
                          last_modified=False,
                          pre_check=self.PRE_CHECK,
                          post_check=self.POST_CHECK)

        return site, cpm


class exportCachingPolicyManagerTests(_CachingPolicyManagerSetup):

    layer = ExportImportZCMLLayer

    def test_empty(self):
        from ..cachingpolicymgr import exportCachingPolicyManager

        site, _cpm = self._initSite(with_policy=False)
        context = DummyExportContext(site)
        exportCachingPolicyManager(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'cachingpolicymgr.xml')
        self._compareDOM(text.decode('utf8'), self._EMPTY_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_with_policy(self):
        from ..cachingpolicymgr import exportCachingPolicyManager

        site, _cpm = self._initSite(with_policy=True)
        context = DummyExportContext(site)
        exportCachingPolicyManager(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'cachingpolicymgr.xml')
        self._compareDOM(text.decode('utf8'), self._WITH_POLICY_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class importCachingPolicyManagerTests(_CachingPolicyManagerSetup):

    layer = ExportImportZCMLLayer

    def test_normal(self):
        from ..cachingpolicymgr import importCachingPolicyManager

        site, cpm = self._initSite(with_policy=False)
        self.assertEqual(len(cpm.listPolicies()), 0)

        context = DummyImportContext(site)
        context._files['cachingpolicymgr.xml'] = self._WITH_POLICY_EXPORT
        importCachingPolicyManager(context)

        self.assertEqual(len(cpm.listPolicies()), 1)
        _policy_id, policy = cpm.listPolicies()[0]
        self.assertEqual(policy.getPolicyId(), self.POLICY_ID)
        self.assertEqual(policy.getPredicate(), self.PREDICATE)
        self.assertEqual(policy.getMTimeFunc(), self.MTIME_FUNC)
        self.assertEqual(policy.getVary(), self.VARY)
        self.assertEqual(policy.getETagFunc(), self.ETAG_FUNC)
        self.assertEqual(policy.getMaxAgeSecs(), self.MAX_AGE_SECS)
        self.assertEqual(policy.getSMaxAgeSecs(), self.S_MAX_AGE_SECS)
        self.assertEqual(policy.getPreCheck(), self.PRE_CHECK)
        self.assertEqual(policy.getPostCheck(), self.POST_CHECK)
        self.assertEqual(policy.getLastModified(), False)
        self.assertEqual(policy.getNoCache(), True)
        self.assertEqual(policy.getNoStore(), True)
        self.assertEqual(policy.getMustRevalidate(), True)
        self.assertEqual(policy.getProxyRevalidate(), True)
        self.assertEqual(policy.getNoTransform(), True)
        self.assertEqual(policy.getPublic(), True)
        self.assertEqual(policy.getPrivate(), True)
        self.assertEqual(policy.getEnable304s(), True)


def test_suite():
    loadTestsFromTestCase = unittest.defaultTestLoader.loadTestsFromTestCase
    return unittest.TestSuite((
        loadTestsFromTestCase(CachingPolicyNodeAdapterTests),
        loadTestsFromTestCase(CachingPolicyManagerXMLAdapterTests),
        loadTestsFromTestCase(exportCachingPolicyManagerTests),
        loadTestsFromTestCase(importCachingPolicyManagerTests),
    ))
