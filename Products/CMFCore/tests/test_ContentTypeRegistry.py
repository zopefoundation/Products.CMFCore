##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for ContentTypeRegistry module.
"""

import unittest
import Testing

from zope.interface.verify import verifyClass


class MajorMinorPredicateTests(unittest.TestCase):

    def _makeOne(self, *args, **kw):
        from Products.CMFCore.ContentTypeRegistry import MajorMinorPredicate

        return MajorMinorPredicate(*args, **kw)

    def test_interfaces(self):
        from Products.CMFCore.ContentTypeRegistry import MajorMinorPredicate
        from Products.CMFCore.interfaces import IContentTypeRegistryPredicate

        verifyClass(IContentTypeRegistryPredicate, MajorMinorPredicate)

    def test_empty(self):
        pred = self._makeOne('empty')
        self.assertEqual(pred.getMajorType(), 'None')
        self.assertEqual(pred.getMinorType(), 'None')
        self.assertFalse(pred('foo', 'text/plain', 'asdfljksadf'))

    def test_simple(self):
        pred = self._makeOne('plaintext')
        pred.edit('text', 'plain')
        self.assertEqual(pred.getMajorType(), 'text')
        self.assertEqual(pred.getMinorType(), 'plain')
        self.assertTrue(pred('foo', 'text/plain', 'asdfljksadf'))
        self.assertFalse(pred('foo', 'text/html', 'asdfljksadf'))
        self.assertFalse(pred('', '', ''))
        self.assertFalse(pred('', 'asdf', ''))

    def test_wildcard(self):
        pred = self._makeOne('alltext')
        pred.edit('text', '')
        self.assertEqual(pred.getMajorType(), 'text')
        self.assertEqual(pred.getMinorType(), '')
        self.assertTrue(pred('foo', 'text/plain', 'asdfljksadf'))
        self.assertTrue(pred('foo', 'text/html', 'asdfljksadf'))
        self.assertFalse(pred('foo', 'image/png', 'asdfljksadf'))

        pred.edit('', 'html')
        self.assertEqual(pred.getMajorType(), '')
        self.assertEqual(pred.getMinorType(), 'html')
        self.assertFalse(pred('foo', 'text/plain', 'asdfljksadf'))
        self.assertTrue(pred('foo', 'text/html', 'asdfljksadf'))
        self.assertFalse(pred('foo', 'image/png', 'asdfljksadf'))


class ExtensionPredicateTests(unittest.TestCase):

    def _makeOne(self, *args, **kw):
        from Products.CMFCore.ContentTypeRegistry import ExtensionPredicate

        return ExtensionPredicate(*args, **kw)

    def test_interfaces(self):
        from Products.CMFCore.ContentTypeRegistry import ExtensionPredicate
        from Products.CMFCore.interfaces import IContentTypeRegistryPredicate

        verifyClass(IContentTypeRegistryPredicate, ExtensionPredicate)

    def test_empty(self):
        pred = self._makeOne('empty')
        self.assertEqual(pred.getExtensions(), 'None')
        self.assertFalse(pred('foo', 'text/plain', 'asdfljksadf'))
        self.assertFalse(pred('foo.txt', 'text/plain', 'asdfljksadf'))
        self.assertFalse(pred('foo.bar', 'text/html', 'asdfljksadf'))

    def test_simple(self):
        pred = self._makeOne('stardottext')
        pred.edit('txt')
        self.assertEqual(pred.getExtensions(), 'txt')
        self.assertFalse(pred('foo', 'text/plain', 'asdfljksadf'))
        self.assertTrue(pred('foo.txt', 'text/plain', 'asdfljksadf'))
        self.assertFalse(pred('foo.bar', 'text/html', 'asdfljksadf'))

    def test_multi(self):
        pred = self._makeOne('stardottext')
        pred.edit('txt text html htm')
        self.assertEqual(pred.getExtensions(), 'txt text html htm')
        self.assertFalse(pred('foo', 'text/plain', 'asdfljksadf'))
        self.assertTrue(pred('foo.txt', 'text/plain', 'asdfljksadf'))
        self.assertTrue(pred('foo.text', 'text/plain', 'asdfljksadf'))
        self.assertTrue(pred('foo.html', 'text/plain', 'asdfljksadf'))
        self.assertTrue(pred('foo.htm', 'text/plain', 'asdfljksadf'))
        self.assertFalse(pred('foo.bar', 'text/html', 'asdfljksadf'))


class MimeTypeRegexPredicateTests(unittest.TestCase):

    def _makeOne(self, *args, **kw):
        from Products.CMFCore.ContentTypeRegistry \
                import MimeTypeRegexPredicate

        return MimeTypeRegexPredicate(*args, **kw)

    def test_interfaces(self):
        from Products.CMFCore.ContentTypeRegistry \
                import MimeTypeRegexPredicate
        from Products.CMFCore.interfaces import IContentTypeRegistryPredicate

        verifyClass(IContentTypeRegistryPredicate, MimeTypeRegexPredicate)

    def test_empty(self):
        pred = self._makeOne('empty')
        self.assertEqual(pred.getPatternStr(), 'None')
        self.assertFalse(pred('foo', 'text/plain', 'asdfljksadf'))

    def test_simple(self):
        pred = self._makeOne('plaintext')
        pred.edit('text/plain')
        self.assertEqual(pred.getPatternStr(), 'text/plain')
        self.assertTrue(pred('foo', 'text/plain', 'asdfljksadf'))
        self.assertFalse(pred('foo', 'text/html', 'asdfljksadf'))

    def test_pattern(self):
        pred = self._makeOne('alltext')
        pred.edit('text/*')
        self.assertEqual(pred.getPatternStr(), 'text/*')
        self.assertTrue(pred('foo', 'text/plain', 'asdfljksadf'))
        self.assertTrue(pred('foo', 'text/html', 'asdfljksadf'))
        self.assertFalse(pred('foo', 'image/png', 'asdfljksadf'))


class NameRegexPredicateTests(unittest.TestCase):

    def _makeOne(self, *args, **kw):
        from Products.CMFCore.ContentTypeRegistry import NameRegexPredicate

        return NameRegexPredicate(*args, **kw)

    def test_interfaces(self):
        from Products.CMFCore.ContentTypeRegistry import NameRegexPredicate
        from Products.CMFCore.interfaces import IContentTypeRegistryPredicate

        verifyClass(IContentTypeRegistryPredicate, NameRegexPredicate)

    def test_empty(self):
        pred = self._makeOne('empty')
        self.assertEqual(pred.getPatternStr(), 'None')
        self.assertFalse(pred('foo', 'text/plain', 'asdfljksadf'))

    def test_simple(self):
        pred = self._makeOne('onlyfoo')
        pred.edit('foo')
        self.assertEqual(pred.getPatternStr(), 'foo')
        self.assertTrue(pred('foo', 'text/plain', 'asdfljksadf'))
        self.assertFalse(pred('fargo', 'text/plain', 'asdfljksadf'))
        self.assertFalse(pred('bar', 'text/plain', 'asdfljksadf'))

    def test_pattern(self):
        pred = self._makeOne('allfwords')
        pred.edit('f.*')
        self.assertEqual(pred.getPatternStr(), 'f.*')
        self.assertTrue(pred('foo', 'text/plain', 'asdfljksadf'))
        self.assertTrue(pred('fargo', 'text/plain', 'asdfljksadf'))
        self.assertFalse(pred('bar', 'text/plain', 'asdfljksadf'))


class ContentTypeRegistryTests(unittest.TestCase):

    def _makeOne(self, *args, **kw):
        from Products.CMFCore.ContentTypeRegistry import ContentTypeRegistry

        return ContentTypeRegistry(*args, **kw)

    def setUp(self):
        self.reg = self._makeOne()

    def test_interfaces(self):
        from Products.CMFCore.ContentTypeRegistry import ContentTypeRegistry
        from Products.CMFCore.interfaces import IContentTypeRegistry

        verifyClass(IContentTypeRegistry, ContentTypeRegistry)

    def test_empty(self):
        reg = self.reg
        self.assertTrue(reg.findTypeName('foo', 'text/plain', 'asdfljksadf')
                        is None)
        self.assertTrue(reg.findTypeName('fargo', 'text/plain', 'asdfljksadf')
                        is None)
        self.assertTrue(reg.findTypeName('bar', 'text/plain', 'asdfljksadf')
                        is None)
        self.assertFalse(reg.listPredicates())
        self.assertRaises(KeyError, reg.removePredicate, 'xyzzy')

    def test_reorder(self):
        reg = self.reg
        predIDs = ('foo', 'bar', 'baz', 'qux')
        for predID in predIDs:
            reg.addPredicate(predID, 'name_regex')
        ids = tuple(map(lambda x: x[0], reg.listPredicates()))
        self.assertEqual(ids, predIDs)
        reg.reorderPredicate('bar', 3)
        ids = tuple(map(lambda x: x[0], reg.listPredicates()))
        self.assertEqual(ids, ('foo', 'baz', 'qux', 'bar'))

    def test_lookup(self):
        reg = self.reg
        reg.addPredicate('image', 'major_minor')
        reg.getPredicate('image').edit('image', '')
        reg.addPredicate('onlyfoo', 'name_regex')
        reg.getPredicate('onlyfoo').edit('foo')
        reg.assignTypeName('onlyfoo', 'Foo')
        self.assertEqual(reg.findTypeName('foo', 'text/plain', 'asdfljksadf'),
                         'Foo')
        self.assertFalse(reg.findTypeName('fargo', 'text/plain',
                                          'asdfljksadf'))
        self.assertFalse(reg.findTypeName('bar', 'text/plain', 'asdfljksadf'))
        self.assertEqual(reg.findTypeName('foo', '', ''), 'Foo')
        self.assertEqual(reg.findTypeName('foo', None, None), 'Foo')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MajorMinorPredicateTests),
        unittest.makeSuite(ExtensionPredicateTests),
        unittest.makeSuite(MimeTypeRegexPredicateTests),
        unittest.makeSuite(NameRegexPredicateTests),
        unittest.makeSuite(ContentTypeRegistryTests),
        ))
