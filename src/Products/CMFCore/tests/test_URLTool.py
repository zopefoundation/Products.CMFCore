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
""" Unit tests for URLTool module.
"""

import unittest

from zope.component import getSiteManager
from zope.interface.verify import verifyClass
from zope.testing.cleanup import cleanUp

from ..interfaces import ISiteRoot
from .base.dummy import DummyContent
from .base.dummy import DummyFolder
from .base.dummy import DummySite


class URLToolTests(unittest.TestCase):

    def setUp(self):
        self.site = DummySite(id='foo')
        sm = getSiteManager()
        sm.registerUtility(self.site, ISiteRoot)

    def tearDown(self):
        cleanUp()

    def _makeOne(self, *args, **kw):
        from ..URLTool import URLTool

        url_tool = URLTool(*args, **kw)
        return url_tool.__of__(self.site)

    def test_interfaces(self):
        from ..interfaces import IActionProvider
        from ..interfaces import IURLTool
        from ..URLTool import URLTool

        verifyClass(IActionProvider, URLTool)
        verifyClass(IURLTool, URLTool)

    def test_portal_methods(self):
        url_tool = self._makeOne()
        self.assertEqual(url_tool(), 'http://www.foobar.com/bar/foo')
        self.assertEqual(url_tool.getPortalObject(), self.site)
        self.assertEqual(url_tool.getPortalPath(), '/bar/foo')

    def test_content_methods(self):
        url_tool = self._makeOne()
        self.site._setObject('folder', DummyFolder(id='buz'))
        self.site.folder._setObject('item', DummyContent(id='qux.html'))
        obj = self.site.folder.item
        self.assertEqual(url_tool.getRelativeContentPath(obj),
                         ('buz', 'qux.html'))
        self.assertEqual(url_tool.getRelativeContentURL(obj), 'buz/qux.html')
        self.assertEqual(url_tool.getRelativeUrl(obj), 'buz/qux.html')
