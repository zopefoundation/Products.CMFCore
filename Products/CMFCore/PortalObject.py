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
""" PortalObject: The portal root object class

$Id$
"""

from Acquisition import aq_base
from five.localsitemanager import find_next_sitemanager
from five.localsitemanager.registry import FiveVerifyingAdapterLookup
from five.localsitemanager.registry import PersistentComponents
from Globals import InitializeClass
from Products.Five.component.interfaces import IObjectManagerSite
from zope.app.publication.zopepublication import BeforeTraverseEvent
from zope.component.globalregistry import base
from zope.event import notify
from zope.interface import implements
from zope.app.component.hooks import setSite

from interfaces import ISiteRoot
from permissions import AddPortalMember
from permissions import SetOwnPassword
from permissions import SetOwnProperties
from permissions import MailForgottenPassword
from permissions import RequestReview
from permissions import ReviewPortalContent
from PortalFolder import PortalFolder
from Skinnable import SkinnableObjectManager

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

    def getSkinsFolderName(self):
        return PORTAL_SKINS_TOOL_ID

    def getSiteManager(self):
        if self._components is None:
            # BBB: for CMF 2.0 instances
            next = find_next_sitemanager(self)
            if next is None:
                next = base
            name = '/'.join(self.getPhysicalPath())
            self._components = components = PersistentComponents(name, (next,))
            components.__parent__ = self
            setSite(self)
        elif self._components.utilities.LookupClass \
                != FiveVerifyingAdapterLookup:
            # BBB: for CMF 2.1 beta instances
            # XXX: should be removed again after the CMF 2.1 release
            components = aq_base(self._components)
            components.__parent__ = self
            utilities = aq_base(components.utilities)
            utilities.LookupClass = FiveVerifyingAdapterLookup
            utilities._createLookup()
            utilities.__parent__ = components
            
        return self._components

    def __before_publishing_traverse__(self, arg1, arg2=None):
        """ Pre-traversal hook.
        """
        # XXX hack around a bug(?) in BeforeTraverse.MultiHook
        REQUEST = arg2 or arg1

        notify(BeforeTraverseEvent(self, REQUEST))
        self.setupCurrentSkin(REQUEST)

        super(PortalObjectBase,
              self).__before_publishing_traverse__(arg1, arg2)

InitializeClass(PortalObjectBase)
