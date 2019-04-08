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
""" CMFCore portal_url tool.
"""

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.special_dtml import DTMLFile
from OFS.SimpleItem import SimpleItem
from zope.component import queryUtility
from zope.globalrequest import getRequest
from zope.interface import implementer
from ZPublisher.BaseRequest import RequestContainer

from .ActionProviderBase import ActionProviderBase
from .interfaces import ISiteRoot
from .interfaces import IURLTool
from .permissions import ManagePortal
from .permissions import View
from .utils import UniqueObject
from .utils import _dtmldir
from .utils import registerToolInterface


@implementer(IURLTool)
class URLTool(UniqueObject, SimpleItem, ActionProviderBase):

    """ CMF URL Tool.
    """

    id = 'portal_url'
    meta_type = 'CMF URL Tool'
    zmi_icon = 'fas fa-compass'

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    manage_options = (ActionProviderBase.manage_options
                      + ({'label': 'Overview', 'action': 'manage_overview'},)
                      + SimpleItem.manage_options)

    #
    #   ZMI methods
    #
    security.declareProtected(ManagePortal, 'manage_overview')
    manage_overview = DTMLFile('explainURLTool', _dtmldir)

    #
    #   'portal_url' interface methods
    #
    @security.public
    def __call__(self, relative=0, *args, **kw):
        """ Get by default the absolute URL of the portal.
        """
        return self.getPortalObject().absolute_url(relative=relative)

    @security.public
    def getPortalObject(self):
        """ Get the portal object itself.
        """
        request_container = RequestContainer(REQUEST=getRequest())
        portal_obj = queryUtility(ISiteRoot)
        if portal_obj is None:
            # fallback for bootstrap
            portal_obj = aq_parent(aq_inner(self))
        return portal_obj.__of__(request_container)

    @security.public
    def getRelativeContentPath(self, content):
        """ Get the path for an object, relative to the portal root.
        """
        portal_path_length = len(self.getPortalObject().getPhysicalPath())
        content_path = content.getPhysicalPath()
        return content_path[portal_path_length:]

    @security.public
    def getRelativeContentURL(self, content):
        """ Get the URL for an object, relative to the portal root.
        """
        return '/'.join(self.getRelativeContentPath(content))

    security.declarePublic('getRelativeUrl')
    getRelativeUrl = getRelativeContentURL

    @security.public
    def getPortalPath(self):
        """ Get the portal object's URL without the server URL component.
        """
        return '/'.join(self.getPortalObject().getPhysicalPath())


InitializeClass(URLTool)
registerToolInterface('portal_url', IURLTool)
