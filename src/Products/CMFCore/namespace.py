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
"""Namespace for CMF specific add views.
"""

from zope.component import adapts
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.interface import Interface
from zope.interface import implementer
from zope.location.interfaces import LocationError
from zope.traversing.interfaces import ITraversable

from .interfaces import IFolderish
from .interfaces import ITypesTool


@implementer(ITraversable)
class AddViewTraverser:

    """Add view traverser.
    """

    adapts(IFolderish, Interface)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def traverse(self, name, ignored):
        ttool = getUtility(ITypesTool)
        ti = ttool.getTypeInfo(name)
        if ti is not None:
            add_view = queryMultiAdapter((self.context, self.request, ti),
                                         name=ti.factory)
            if add_view is None:
                add_view = queryMultiAdapter((self.context, self.request, ti))
            if add_view is not None:
                add_view.__name__ = ti.factory
                return add_view

        raise LocationError(self.context, name)
