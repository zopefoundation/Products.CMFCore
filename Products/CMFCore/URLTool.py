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
""" CMFCore portal_url tool.

$Id$
"""

from AccessControl import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from Globals import DTMLFile
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from zope.interface import implements

from ActionProviderBase import ActionProviderBase
from interfaces import IURLTool
from interfaces.portal_url import portal_url as z2IURLTool
from permissions import ManagePortal
from permissions import View
from utils import _dtmldir
from utils import UniqueObject


class URLTool(UniqueObject, SimpleItem, ActionProviderBase):

    """ CMF URL Tool.
    """

    implements(IURLTool)
    __implements__ = (z2IURLTool, ActionProviderBase.__implements__)

    id = 'portal_url'
    meta_type = 'CMF URL Tool'

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    manage_options = ( ActionProviderBase.manage_options
                     + ( {'label':'Overview',
                          'action':'manage_overview'}
                       ,
                       )
                     + SimpleItem.manage_options
                     )

    #
    #   ZMI methods
    #
    security.declareProtected(ManagePortal, 'manage_overview')
    manage_overview = DTMLFile('explainURLTool', _dtmldir)

    #
    #   'portal_url' interface methods
    #
    security.declarePublic('__call__')
    def __call__(self, relative=0, *args, **kw):
        """ Get by default the absolute URL of the portal.
        """
        # XXX: this method violates the rules for tools/utilities:
        # absolute_url() depends implicitly on REQUEST
        return self.getPortalObject().absolute_url(relative=relative)

    security.declarePublic('getPortalObject')
    def getPortalObject(self):
        """ Get the portal object itself.
        """
        # XXX: this method violates the rules for tools/utilities:
        # queryUtility(ISiteRoot) doesn't work because we need the REQUEST
        return aq_parent( aq_inner(self) )

    security.declarePublic('getRelativeContentPath')
    def getRelativeContentPath(self, content):
        """ Get the path for an object, relative to the portal root.
        """
        portal_path_length = len( self.getPortalObject().getPhysicalPath() )
        content_path = content.getPhysicalPath()
        return content_path[portal_path_length:]

    security.declarePublic('getRelativeContentURL')
    def getRelativeContentURL(self, content):
        """ Get the URL for an object, relative to the portal root.
        """
        return '/'.join( self.getRelativeContentPath(content) )

    security.declarePublic('getRelativeUrl')
    getRelativeUrl = getRelativeContentURL

    security.declarePublic('getPortalPath')
    def getPortalPath(self):
        """ Get the portal object's URL without the server URL component.
        """
        return '/'.join( self.getPortalObject().getPhysicalPath() )

InitializeClass(URLTool)
