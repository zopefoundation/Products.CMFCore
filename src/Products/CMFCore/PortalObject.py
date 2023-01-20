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
""" PortalObject: The portal root object class
"""

from AccessControl.class_init import InitializeClass
from five.localsitemanager.registry import PersistentComponents
from Products.Five.component.interfaces import IObjectManagerSite
from zope.event import notify
from zope.interface import implementer
from zope.interface.interfaces import ComponentLookupError
from zope.traversing.interfaces import BeforeTraverseEvent

from .interfaces import ISiteRoot
from .permissions import AddPortalMember
from .permissions import MailForgottenPassword
from .permissions import RequestReview
from .permissions import ReviewPortalContent
from .permissions import SetOwnPassword
from .permissions import SetOwnProperties
from .PortalFolder import PortalFolder
from .Skinnable import SkinnableObjectManager


@implementer(ISiteRoot, IObjectManagerSite)
class PortalObjectBase(PortalFolder, SkinnableObjectManager):

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
        super().__init__(id, title, description)
        components = PersistentComponents('++etc++site')
        components.__parent__ = self
        self.setSiteManager(components)

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

        super().__before_publishing_traverse__(arg1, arg2)


InitializeClass(PortalObjectBase)
