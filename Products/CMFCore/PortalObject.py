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
""" PortalObject: The portal root object class """

from App.class_init import InitializeClass
from five.localsitemanager.registry import PersistentComponents
from Products.Five.component.interfaces import IObjectManagerSite
from zope.component.interfaces import ComponentLookupError
from zope.event import notify
from zope.interface import implements
try:
    from zope.traversing.interfaces import BeforeTraverseEvent
except ImportError:
    # BBB: for Zope < 2.13
    from zope.app.publication.zopepublication import BeforeTraverseEvent

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.permissions import AddPortalMember
from Products.CMFCore.permissions import SetOwnPassword
from Products.CMFCore.permissions import SetOwnProperties
from Products.CMFCore.permissions import MailForgottenPassword
from Products.CMFCore.permissions import RequestReview
from Products.CMFCore.permissions import ReviewPortalContent
from Products.CMFCore.PortalFolder import PortalFolder
from Products.CMFCore.Skinnable import SkinnableObjectManager

PORTAL_SKINS_TOOL_ID = 'portal_skins'


class PortalObjectBase(PortalFolder, SkinnableObjectManager):

    implements(ISiteRoot, IObjectManagerSite)
    meta_type = 'Portal Site'

    # Ensure certain attributes come from the correct base class.
    __getattr__ = SkinnableObjectManager.__getattr__
    _checkId = SkinnableObjectManager._checkId

    # Ensure all necessary permissions exist.
    __ac_permissions__ = (
        (AddPortalMember, ()),
        (SetOwnPassword, ()),
        (SetOwnProperties, ()),
        (MailForgottenPassword, ()),
        (RequestReview, ()),
        (ReviewPortalContent, ()),
        )

    def __init__(self, id, title='', description=''):
        super(PortalObjectBase, self).__init__(id, title, description)
        components = PersistentComponents('++etc++site')
        components.__parent__ = self
        self.setSiteManager(components)

    def getSkinsFolderName(self):
        return PORTAL_SKINS_TOOL_ID

    def __before_publishing_traverse__(self, arg1, arg2=None):
        """ Pre-traversal hook.
        """
        # XXX hack around a bug(?) in BeforeTraverse.MultiHook
        REQUEST = arg2 or arg1

        try:
            notify(BeforeTraverseEvent(self, REQUEST))
        except ComponentLookupError:
            # allow ZMI access, even if the portal's site manager is missing
            pass
        self.setupCurrentSkin(REQUEST)

        super(PortalObjectBase,
              self).__before_publishing_traverse__(arg1, arg2)

InitializeClass(PortalObjectBase)
