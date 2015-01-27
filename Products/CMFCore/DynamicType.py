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
""" DynamicType: Mixin for dynamic properties.
"""

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_get
from App.class_init import InitializeClass
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.component.interfaces import ComponentLookupError
from zope.interface import implements
from zope.publisher.defaultview import queryDefaultViewName

from Products.CMFCore.Expression import getExprContext
from Products.CMFCore.interfaces import IDynamicType
from Products.CMFCore.interfaces import ITypesTool
from Products.CMFCore.interfaces import IURLTool


class DynamicType:

    """
    Mixin for portal content that allows the object to take on
    a dynamic type property.
    """

    implements(IDynamicType)

    portal_type = None

    security = ClassSecurityInfo()

    def _setPortalTypeName(self, pt):
        """ Set the portal type name.

        Called by portal_types during construction, records an ID that will be
        used later to locate the correct ContentTypeInformation.
        """
        self.portal_type = pt

    #
    #   'IDynamicType' interface methods
    #
    security.declarePublic('getPortalTypeName')
    def getPortalTypeName(self):
        """ Get the portal type name that can be passed to portal_types.
        """
        pt = self.portal_type
        if callable( pt ):
            pt = pt()
        return pt

    # deprecated alias
    _getPortalTypeName = getPortalTypeName

    security.declarePublic('getTypeInfo')
    def getTypeInfo(self):
        """ Get the TypeInformation object specified by the portal type.
        """
        tool = queryUtility(ITypesTool)
        if tool is None:
            return None
        return tool.getTypeInfo(self)  # Can return None.

    security.declarePublic('getActionInfo')
    def getActionInfo(self, action_chain, check_visibility=0,
                      check_condition=0):
        """ Get an Action info mapping specified by a chain of actions.
        """
        ti = self.getTypeInfo()
        if ti:
            return ti.getActionInfo(action_chain, self, check_visibility,
                                    check_condition)
        else:
            msg = 'Action "%s" not available for %s' % (
                        action_chain, '/'.join(self.getPhysicalPath()))
            raise ValueError(msg)

    security.declarePublic('getIconURL')
    def getIconURL(self):
        """ Get the absolute URL of the icon for the object.
        """
        ti = self.getTypeInfo()
        if ti is None:
            try:
                utool = getUtility(IURLTool)
            except ComponentLookupError:
                # BBB: fallback for CMF 2.2 instances
                utool = aq_get(self, 'portal_url')
            return '%s/misc_/OFSP/dtmldoc.gif' % utool()
        icon_expr_object = ti.getIconExprObject()
        if icon_expr_object is None:
            return ''
        ec = getExprContext(self)
        return icon_expr_object(ec)

    #
    #   'IItem' interface method
    #
    security.declarePublic('icon')
    def icon(self, relative_to_portal=0):
        """
        Using this method allows the content class
        creator to grab icons on the fly instead of using a fixed
        attribute on the class.
        """
        try:
            utool = getUtility(IURLTool)
        except ComponentLookupError:
            # BBB: fallback for CMF 2.2 instances
            utool = aq_get(self, 'portal_url')
        portal_url = utool()
        icon = self.getIconURL()
        if icon.startswith(portal_url):
            icon = icon[len(portal_url)+1:]
            if not relative_to_portal:
                # Relative to REQUEST['BASEPATH1']
                icon = '%s/%s' % (utool(relative=1), icon)
        try:
            utool.getPortalObject().unrestrictedTraverse(icon)
        except (AttributeError, KeyError):
            icon = ''
        return icon

    # deprecated alias
    security.declarePublic('getIcon')
    getIcon = icon

    def __before_publishing_traverse__(self, arg1, arg2=None):
        """ Pre-traversal hook.
        """
        # XXX hack around a bug(?) in BeforeTraverse.MultiHook
        REQUEST = arg2 or arg1

        if REQUEST['REQUEST_METHOD'] not in ('GET', 'POST'):
            return

        stack = REQUEST['TraversalRequestNameStack']
        key = stack and stack[-1] or '(Default)'

        # if there's a Zope3-style default view name set and the
        # corresponding view exists, take that in favour of the FTI's
        # default view
        if key == '(Default)':
            viewname = queryDefaultViewName(self, REQUEST)
            if (viewname and
                queryMultiAdapter((self, REQUEST), name=viewname) is not None):
                stack.append(viewname)
                REQUEST._hacked_path = 1
                return

        ti = self.getTypeInfo()
        method_id = ti and ti.queryMethodID(key, context=self)
        if method_id:
            if key != '(Default)':
                stack.pop()
            if method_id != '(Default)':
                stack.append(method_id)
            REQUEST._hacked_path = 1

InitializeClass(DynamicType)
