##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Namespace for CMF specific add views. """

from zope.component import adapts
from zope.component import queryMultiAdapter
from zope.interface import implements
from zope.interface import Interface
from zope.traversing.interfaces import ITraversable
from zope.traversing.interfaces import TraversalError

from interfaces import IFolderish
from utils import getToolByName


class AddViewTraverser(object):

    """Add view traverser.
    """

    adapts(IFolderish, Interface)
    implements(ITraversable)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def traverse(self, name, ignored):
        ttool = getToolByName(self.context, 'portal_types')
        ti = ttool.getTypeInfo(name)
        if ti is not None:
            add_view = queryMultiAdapter((self.context, self.request, ti),
                                         name=ti.factory)
            if add_view is None:
                add_view = queryMultiAdapter((self.context, self.request, ti))
            if add_view is not None:
                add_view.__name__ = ti.factory
                return add_view.__of__(self.context)

        raise TraversalError(self.context, name)
