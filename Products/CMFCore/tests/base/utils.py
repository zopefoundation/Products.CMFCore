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
""" CMF test utils. """

def has_path( catalog, path ):
    """
        Verify that catalog has an object at path.
    """
    if type( path ) is type( () ):
        path = '/'.join(path)
    rids = map( lambda x: x.data_record_id_, catalog.searchResults() )
    for rid in rids:
        if catalog.getpath( rid ) == path:
            return 1
    return 0

def _setUpDefaultTraversable():
    from zope.interface import Interface
    from zope.component import provideAdapter
    from zope.traversing.interfaces import ITraversable
    from zope.traversing.adapters import DefaultTraversable

    provideAdapter(DefaultTraversable, (Interface,), ITraversable)
