##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" PortalContent: Base class for all CMF content.

$Id$
"""

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from webdav.WriteLockInterface import WriteLockInterface as z2IWriteLock
from zope.interface import implements

from CMFCatalogAware import CMFCatalogAware
from DynamicType import DynamicType
from exceptions import NotFound
from exceptions import ResourceLockedError
from interfaces import IContentish
from interfaces.Contentish import Contentish as z2IContentish
from permissions import FTPAccess
from permissions import View
from utils import Message as _


class PortalContent(DynamicType, CMFCatalogAware, SimpleItem):

    """ Base class for portal objects.

        Provides hooks for reviewing, indexing, and CMF UI.

        Derived classes must implement the interface described in
        interfaces/DublinCore.py.
    """

    implements(IContentish)
    __implements__ = (z2IContentish, z2IWriteLock, DynamicType.__implements__)

    manage_options = ( ( { 'label'  : 'Dublin Core'
                         , 'action' : 'manage_metadata'
                         }
                       , { 'label'  : 'Edit'
                         , 'action' : 'manage_edit'
                         }
                       , { 'label'  : 'View'
                         , 'action' : 'view'
                         }
                       )
                     + CMFCatalogAware.manage_options
                     + SimpleItem.manage_options
                     )

    security = ClassSecurityInfo()

    security.declareObjectProtected(View)

    # The security for FTP methods aren't set up by default in our
    # superclasses...  :(
    security.declareProtected(FTPAccess, 'manage_FTPstat')
    security.declareProtected(FTPAccess, 'manage_FTPlist')

    def failIfLocked(self):
        """ Check if isLocked via webDav.
        """
        if self.wl_isLocked():
            raise ResourceLockedError(_(u'This resource is locked via '
                                        u'webDAV.'))
        return 0

    #
    #   Contentish interface methods
    #
    security.declareProtected(View, 'SearchableText')
    def SearchableText(self):
        """ Returns a concatination of all searchable text.

        Should be overriden by portal objects.
        """
        return "%s %s" % (self.Title(), self.Description())

    def __call__(self):
        """ Invokes the default view.
        """
        ti = self.getTypeInfo()
        method_id = ti and ti.queryMethodID('(Default)', context=self)
        if method_id and method_id!='(Default)':
            method = getattr(self, method_id)
            if getattr(aq_base(method), 'isDocTemp', 0):
                return method(self, self.REQUEST, self.REQUEST['RESPONSE'])
            else:
                return method()
        else:
            raise NotFound( 'Cannot find default view for "%s"' %
                            '/'.join( self.getPhysicalPath() ) )

InitializeClass(PortalContent)
