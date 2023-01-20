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
""" Basic portal discussion access tool.
"""

import urllib

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime
from OFS.SimpleItem import SimpleItem
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface import implementer

from .ActionProviderBase import ActionProviderBase
from .interfaces import ICatalogTool
from .interfaces import IMembershipTool
from .interfaces import IOldstyleDiscussable
from .interfaces import IOldstyleDiscussionTool
from .permissions import AccessContentsInformation
from .permissions import ManagePortal
from .permissions import ReplyToItem
from .permissions import View
from .utils import UniqueObject
from .utils import _dtmldir


@implementer(IOldstyleDiscussable)
class OldDiscussable(Implicit):

    """
        Adapter for PortalContent to implement "old-style" discussions.
    """

    security = ClassSecurityInfo()

    def __init__(self, content):
        self.content = content

    @security.protected(ReplyToItem)
    def createReply(self, title, text, REQUEST, RESPONSE):
        """
            Create a reply in the proper place
        """

        location, id = self.getReplyLocationAndID(REQUEST)
        location.addDiscussionItem(id, title, title, 'structured-text',
                                   text, self.content)

        RESPONSE.redirect(self.absolute_url() + '/view')

    def getReplyLocationAndID(self, REQUEST):
        # It is not yet clear to me what the correct location for this hook is

        # Find the folder designated for replies, creating if missing
        mtool = getUtility(IMembershipTool)
        home = mtool.getHomeFolder()
        if not hasattr(home, 'Correspondence'):
            home.manage_addPortalFolder('Correspondence')
        location = home.Correspondence
        location.manage_permission(View, ['Anonymous'], 1)
        location.manage_permission(AccessContentsInformation, ['Anonymous'], 1)

        # Find an unused id in location
        id = int(DateTime().timeTime())
        while hasattr(location, repr(id)):
            id = id + 1

        return location, repr(id)

    @security.protected(View)
    def getReplyResults(self):
        """
            Return the ZCatalog results that represent this object's replies.

            Often, the actual objects are not needed.  This is less expensive
            than fetching the objects.
        """
        ctool = queryUtility(ICatalogTool)
        if ctool is not None:
            return ctool.searchResults(in_reply_to=urllib.parse.unquote(
                                                   '/' + self.absolute_url(1)))

    @security.protected(View)
    def getReplies(self):
        """
            Return a sequence of the DiscussionResponse objects which are
            associated with this Discussable
        """
        ctool = queryUtility(ICatalogTool)
        if ctool is not None:
            results = self.getReplyResults()
            rids = [x.data_record_id_ for x in results]
            objects = list(map(ctool.getobject, rids))
            return objects

    def quotedContents(self):
        """
            Return this object's contents in a form suitable for inclusion
            as a quote in a response.
        """

        return ''


InitializeClass(OldDiscussable)


@implementer(IOldstyleDiscussionTool)
class DiscussionTool(UniqueObject, SimpleItem, ActionProviderBase):

    id = 'portal_discussion'
    meta_type = 'Oldstyle CMF Discussion Tool'
    zmi_icon = 'far fa-comments'
    # This tool is used to find the discussion for a given content object.

    security = ClassSecurityInfo()

    manage_options = (
        ({'label': 'Overview', 'action': 'manage_overview'},) +
        SimpleItem.manage_options)

    #
    #   ZMI methods
    #
    security.declareProtected(ManagePortal, 'manage_overview')
    manage_overview = DTMLFile('explainDiscussionTool', _dtmldir)

    #
    #   'portal_discussion' interface methods
    #
    @security.public
    def getDiscussionFor(self, content):
        """Gets the PortalDiscussion object that applies to content.
        """
        return OldDiscussable(content).__of__(content)

    @security.public
    def isDiscussionAllowedFor(self, content):
        """
            Returns a boolean indicating whether a discussion is
            allowed for the specified content.
        """
        if hasattr(content, 'allow_discussion'):
            return content.allow_discussion
        typeInfo = content.getTypeInfo()
        if typeInfo:
            return typeInfo.allowDiscussion()
        return 0


InitializeClass(DiscussionTool)
