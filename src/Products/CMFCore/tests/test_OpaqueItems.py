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
""" Unit tests for IOpaqueItems implementations.
"""

import unittest

import six

from zope.component import getSiteManager
from zope.interface import implementer

from ..interfaces import ICallableOpaqueItem
from ..interfaces import ICallableOpaqueItemEvents
from ..interfaces import IContentish
from ..interfaces import ITypesTool
from ..PortalFolder import PortalFolder
from ..testing import TraversingEventZCMLLayer
from ..TypesTool import TypesTool
from .base.dummy import DummyContent as OriginalDummyContent
from .base.testcase import SecurityTest


# -------------------------------------------
# Helper classes and functions
# -------------------------------------------

def extra_meta_types():
    return [{'name': 'Dummy', 'action': 'manage_addFolder',
             'permission': 'View'}]


def addDummyContent(container, id, opaqueItem):
    container._setObject(id,
                         DummyContent(id, opaqueItem=opaqueItem, catalog=1))
    return getattr(container, id)


@implementer(IContentish)
class DummyContent(OriginalDummyContent):

    """ A Dummy piece of PortalContent with additional attributes
    """

    def __init__(self, id='dummy', opaqueItem=None, *args, **kw):
        OriginalDummyContent.__init__(self, id, *args, **kw)
        if opaqueItem is None:
            self.opaqueItem = 'noncallable'
            self.opaqueItemsId = 'opaqueItem'
        elif isinstance(opaqueItem, six.string_types):
            Hooks(self, opaqueItem)
            self.opaqueItemsId = opaqueItem
        else:
            opaqueItem(self, 'opaqueItem')
            self.opaqueItemsId = 'opaqueItem'

    # Ensure additional attributes get copied
    def _getCopy(self, container):
        obj = DummyContent(self.id, catalog=self.catalog)
        setattr(obj, self.opaqueItemsId, getattr(self, self.opaqueItemsId))
        return obj

    def isNotifiedByAfterAdd(self):
        return getattr(getattr(self, self.opaqueItemsId), 'addCount', None)

    def isNotifiedByAfterClone(self):
        return getattr(getattr(self, self.opaqueItemsId), 'cloneCount', None)

    def isNotifiedByBeforeDelete(self):
        return getattr(getattr(self, self.opaqueItemsId), 'deleteCount', None)


class OpaqueBase:
    """ Dummy opaque item without manage_after/before hookes
    """
    def __init__(self, obj, id):
        self.addCount = self.cloneCount = self.deleteCount = 0
        self.addCounter = self.cloneCounter = self.deleteCounter = 1
        self.id = id
        setattr(obj, id, self)

    def __call__(self):
        return

    def getId(self):
        return self.id


@implementer(ICallableOpaqueItem)
class Marker(OpaqueBase):
    """ Opaque item without manage_after/before hookes but marked as callable
    """
    pass


@implementer(ICallableOpaqueItemEvents)
class Hooks(OpaqueBase):
    """ Opaque item with manage_after/before hooks but not marked as callable
    """

    def manage_afterAdd(self, item, container):
        self.addCount = self.addCounter
        self.addCounter += 1

    def manage_afterClone(self, item):
        self.cloneCount = self.cloneCounter
        self.cloneCounter += 1

    def manage_beforeDelete(self, item, container):
        self.deleteCount = self.deleteCounter
        self.deleteCounter += 1


class MarkerAndHooks(Marker, Hooks):

    """ Opaque item with manage_after/before hookes and marked as callable
    """


# -------------------------------------------
# Unit Tests
# -------------------------------------------

class ManageBeforeAfterTests(SecurityTest):

    layer = TraversingEventZCMLLayer

    def setUp(self):
        SecurityTest.setUp(self)

        # setting up types tool
        getSiteManager().registerUtility(TypesTool(), ITypesTool)

        # setup portal
        try:
            self.app._delObject('test')
        except AttributeError:
            pass
        self.app._setObject('test', PortalFolder('test', ''))
        self.test = test = self.app.test

        # setting up folders
        test._setObject('folder', PortalFolder('folder', ''))
        folder = self.folder = test.folder
        folder._setObject('sub', PortalFolder('sub', ''))
        sub = self.sub = folder.sub

        # ----- hacks to allow pasting (see also test_PortalFolder)
        # WAAA! force sub to allow paste of Dummy object.
        sub.all_meta_types = extra_meta_types()

        # delete items if necessary
        try:
            folder._delObject('dummy')
        except AttributeError:
            pass
        try:
            sub._delObject('dummy')
        except AttributeError:
            pass

    def test_nonCallableItem(self):
        # no exception should be raised
        folder = self.folder
        sub = self.sub
        dummy = addDummyContent(folder, 'dummy', None)

        # WAAAA! must get _p_jar set
        old, dummy._p_jar = sub._p_jar, self.app._p_jar
        try:
            cp = folder.manage_copyObjects(ids=['dummy'])
            sub.manage_pasteObjects(cp)
        finally:
            dummy._p_jar = old

    def test_callableItemWithMarkerOnly(self):
        folder = self.folder
        sub = self.sub
        dummy = addDummyContent(folder, 'dummy', Marker)

        self.assertFalse(dummy.isNotifiedByAfterAdd())
        self.assertFalse(dummy.isNotifiedByAfterClone())
        self.assertFalse(dummy.isNotifiedByBeforeDelete())

        # WAAAA! must get _p_jar set
        old, dummy._p_jar = sub._p_jar, self.app._p_jar
        try:
            cp = folder.manage_copyObjects(ids=['dummy'])
            sub.manage_pasteObjects(cp)
        finally:
            dummy._p_jar = old

        self.assertFalse(dummy.isNotifiedByAfterAdd())
        self.assertFalse(dummy.isNotifiedByAfterClone())
        self.assertFalse(dummy.isNotifiedByBeforeDelete())

    def test_callableItemWithHooksOnly(self):
        folder = self.folder
        sub = self.sub
        dummy = addDummyContent(folder, 'dummy', Hooks)

        self.assertFalse(dummy.isNotifiedByAfterAdd())
        self.assertFalse(dummy.isNotifiedByAfterClone())
        self.assertFalse(dummy.isNotifiedByBeforeDelete())

        # WAAAA! must get _p_jar set
        old, dummy._p_jar = sub._p_jar, self.app._p_jar
        try:
            cp = folder.manage_copyObjects(ids=['dummy'])
            sub.manage_pasteObjects(cp)
        finally:
            dummy._p_jar = old

        self.assertFalse(dummy.isNotifiedByAfterAdd())
        self.assertFalse(dummy.isNotifiedByAfterClone())
        self.assertFalse(dummy.isNotifiedByBeforeDelete())

    def test_callableItemWithMarkerAndHooks(self):
        folder = self.folder
        sub = self.sub
        dummy = addDummyContent(folder, 'dummy', MarkerAndHooks)

        self.assertEqual(dummy.isNotifiedByAfterAdd(), 1)
        self.assertFalse(dummy.isNotifiedByAfterClone())
        self.assertFalse(dummy.isNotifiedByBeforeDelete())

        # WAAAA! must get _p_jar set
        old, dummy._p_jar = sub._p_jar, self.app._p_jar
        try:
            cp = folder.manage_copyObjects(ids=['dummy'])
            sub.manage_pasteObjects(cp)
        finally:
            dummy._p_jar = old

        self.assertEqual(dummy.isNotifiedByAfterAdd(), 2)
        self.assertEqual(dummy.isNotifiedByAfterClone(), 1)
        self.assertFalse(dummy.isNotifiedByBeforeDelete())

    def test_talkbackItem(self):
        folder = self.folder
        sub = self.sub

        dummy = addDummyContent(folder, 'dummy', 'talkback')

        self.assertEqual(dummy.isNotifiedByAfterAdd(), 1)
        self.assertFalse(dummy.isNotifiedByAfterClone())
        self.assertFalse(dummy.isNotifiedByBeforeDelete())

        # WAAAA! must get _p_jar set
        old, dummy._p_jar = sub._p_jar, self.app._p_jar
        try:
            cp = folder.manage_copyObjects(ids=['dummy'])
            sub.manage_pasteObjects(cp)
        finally:
            dummy._p_jar = old

        self.assertEqual(dummy.isNotifiedByAfterAdd(), 2)
        self.assertEqual(dummy.isNotifiedByAfterClone(), 1)
        self.assertFalse(dummy.isNotifiedByBeforeDelete())


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ManageBeforeAfterTests),
        ))
