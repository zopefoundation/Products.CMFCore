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
""" PortalContent: Base class for all CMF content.
"""

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from OFS.SimpleItem import SimpleItem
from zope.interface import implementer

from .CMFCatalogAware import CMFCatalogAware
from .DynamicType import DynamicType
from .exceptions import NotFound
from .exceptions import ResourceLockedError
from .interfaces import IContentish
from .permissions import View
from .utils import Message as _


@implementer(IContentish)
class PortalContent(DynamicType, CMFCatalogAware, SimpleItem):

    """ Base class for portal objects.

        Provides hooks for reviewing, indexing, and CMF UI.

        Derived classes must implement the interface described in
        interfaces/DublinCore.py.
    """

    manage_options = (({'label': 'Dublin Core', 'action': 'manage_metadata'},
                       {'label': 'Edit', 'action': 'manage_edit'},
                       {'label': 'View', 'action': 'view'})
                      + CMFCatalogAware.manage_options
                      + SimpleItem.manage_options)

    security = ClassSecurityInfo()

    security.declareObjectProtected(View)

    def failIfLocked(self):
        """ Check if isLocked via webDav.
        """
        if self.wl_isLocked():
            raise ResourceLockedError(_('This resource is locked via '
                                        'webDAV.'))
        return 0

    #
    #   Contentish interface methods
    #
    @security.protected(View)
    def SearchableText(self):
        """ Returns a concatination of all searchable text.

        Should be overriden by portal objects.
        """
        return f'{self.Title()} {self.Description()}'

    def __call__(self):
        """ Invokes the default view.
        """
        ti = self.getTypeInfo()
        method_id = ti and ti.queryMethodID('(Default)', context=self)
        if method_id and method_id != '(Default)':
            method = getattr(self, method_id)
            if getattr(aq_base(method), 'isDocTemp', 0):
                return method(self, self.REQUEST, self.REQUEST['RESPONSE'])
            else:
                return method()
        else:
            raise NotFound('Cannot find default view for "%s"' %
                           '/'.join(self.getPhysicalPath()))


InitializeClass(PortalContent)
