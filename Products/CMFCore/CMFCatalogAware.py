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
""" Base class for catalog aware content items. """

import logging

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from ExtensionClass import Base
from OFS.interfaces import IObjectClonedEvent
from OFS.interfaces import IObjectWillBeMovedEvent
from zope.component import subscribers
from zope.container.interfaces import IObjectAddedEvent
from zope.container.interfaces import IObjectMovedEvent
from zope.interface import implements
from zope.lifecycleevent.interfaces import IObjectCopiedEvent
from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from Products.CMFCore.interfaces import ICallableOpaqueItem
from Products.CMFCore.interfaces import ICatalogAware
from Products.CMFCore.interfaces import IOpaqueItemManager
from Products.CMFCore.interfaces import IWorkflowAware
from Products.CMFCore.permissions import AccessContentsInformation
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import _dtmldir
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore.utils import getToolByName

logger = logging.getLogger('CMFCore.CMFCatalogAware')


class CatalogAware(Base):

    """Mix-in for notifying the catalog tool.
    """

    implements(ICatalogAware)

    security = ClassSecurityInfo()

    # The following method can be overridden using inheritance so that it's
    # possible to specify another catalog tool for a given content type
    def _getCatalogTool(self):
        return getToolByName(self, 'portal_catalog', None)

    #
    #   'ICatalogAware' interface methods
    #
    security.declareProtected(ModifyPortalContent, 'indexObject')
    def indexObject(self):
        """ Index the object in the portal catalog.
        """
        catalog = self._getCatalogTool()
        if catalog is not None:
            catalog.indexObject(self)

    security.declareProtected(ModifyPortalContent, 'unindexObject')
    def unindexObject(self):
        """ Unindex the object from the portal catalog.
        """
        catalog = self._getCatalogTool()
        if catalog is not None:
            catalog.unindexObject(self)

    security.declareProtected(ModifyPortalContent, 'reindexObject')
    def reindexObject(self, idxs=[]):
        """ Reindex the object in the portal catalog.
        """
        if idxs == []:
            # Update the modification date.
            if hasattr(aq_base(self), 'notifyModified'):
                self.notifyModified()
        catalog = self._getCatalogTool()
        if catalog is not None:
            catalog.reindexObject(self, idxs=idxs)

    _cmf_security_indexes = ('allowedRolesAndUsers',)

    security.declareProtected(ModifyPortalContent, 'reindexObjectSecurity')
    def reindexObjectSecurity(self, skip_self=False):
        """ Reindex security-related indexes on the object.
        """
        catalog = self._getCatalogTool()
        if catalog is None:
            return
        path = '/'.join(self.getPhysicalPath())

        # XXX if _getCatalogTool() is overriden we will have to change
        # this method for the sub-objects.
        for brain in catalog.unrestrictedSearchResults(path=path):
            brain_path = brain.getPath()
            if brain_path == path and skip_self:
                continue
            # Get the object
            ob = brain._unrestrictedGetObject()
            if ob is None:
                # BBB: Ignore old references to deleted objects.
                # Can happen only when using
                # catalog-getObject-raises off in Zope 2.8
                logger.warning("reindexObjectSecurity: Cannot get %s from "
                               "catalog", brain_path)
                continue
            # Recatalog with the same catalog uid.
            s = getattr(ob, '_p_changed', 0)
            catalog.reindexObject(ob, idxs=self._cmf_security_indexes,
                                  update_metadata=0, uid=brain_path)
            if s is None: ob._p_deactivate()

InitializeClass(CatalogAware)


class WorkflowAware(Base):

    """Mix-in for notifying the workflow tool.
    """

    implements(IWorkflowAware)

    security = ClassSecurityInfo()

    manage_options = ({'label': 'Workflows',
                       'action': 'manage_workflowsTab'},)

    _manage_workflowsTab = DTMLFile('zmi_workflows', _dtmldir)

    #
    #   ZMI methods
    #
    security.declareProtected(ManagePortal, 'manage_workflowsTab')
    def manage_workflowsTab(self, REQUEST, manage_tabs_message=None):
        """ Tab displaying the current workflows for the content object.
        """
        ob = self
        wftool = self._getWorkflowTool()
        # XXX None ?
        if wftool is not None:
            wf_ids = wftool.getChainFor(ob)
            states = {}
            chain = []
            for wf_id in wf_ids:
                wf = wftool.getWorkflowById(wf_id)
                if wf is not None:
                    # XXX a standard API would be nice
                    if hasattr(wf, 'getReviewStateOf'):
                        # Default Workflow
                        state = wf.getReviewStateOf(ob)
                    elif hasattr(wf, '_getWorkflowStateOf'):
                        # DCWorkflow
                        state = wf._getWorkflowStateOf(ob, id_only=1)
                    else:
                        state = '(Unknown)'
                    states[wf_id] = state
                    chain.append(wf_id)
        return self._manage_workflowsTab(
            REQUEST,
            chain=chain,
            states=states,
            management_view='Workflows',
            manage_tabs_message=manage_tabs_message)

    # The following method can be overridden using inheritance so that it's
    # possible to specify another workflow tool for a given content type
    def _getWorkflowTool(self):
        return getToolByName(self, 'portal_workflow', None)

    #
    #   'IWorkflowAware' interface methods
    #
    security.declarePrivate('notifyWorkflowCreated')
    def notifyWorkflowCreated(self):
        """ Notify the workflow that the object was just created.
        """
        wftool = self._getWorkflowTool()
        if wftool is not None:
            wftool.notifyCreated(self)

InitializeClass(WorkflowAware)


class OpaqueItemManager(Base):

    """Mix-in for managing opaque items.
    """

    implements(IOpaqueItemManager)

    security = ClassSecurityInfo()

    # Opaque subitems
    # ---------------

    security.declareProtected(AccessContentsInformation, 'opaqueItems')
    def opaqueItems(self):
        """
            Return opaque items (subelements that are contained
            using something that is not an ObjectManager).
        """
        items = []

        # Call 'talkback' knowing that it is an opaque item.
        # This will remain here as long as the discussion item does
        # not implement ICallableOpaqueItem (backwards compatibility).
        if hasattr(aq_base(self), 'talkback'):
            talkback = self.talkback
            if talkback is not None:
                items.append((talkback.id, talkback))

        # Other opaque items than 'talkback' may have callable
        # manage_after* and manage_before* hooks.
        # Loop over all attributes and add those to 'items'
        # implementing 'ICallableOpaqueItem'.
        self_base = aq_base(self)
        for name in self_base.__dict__.keys():
            obj = getattr(self, name)
            if ICallableOpaqueItem.providedBy(obj):
                items.append((obj.getId(), obj))

        return tuple(items)

    security.declareProtected(AccessContentsInformation, 'opaqueIds')
    def opaqueIds(self):
        """
            Return opaque ids (subelements that are contained
            using something that is not an ObjectManager).
        """
        return [t[0] for t in self.opaqueItems()]

    security.declareProtected(AccessContentsInformation, 'opaqueValues')
    def opaqueValues(self):
        """
            Return opaque values (subelements that are contained
            using something that is not an ObjectManager).
        """
        return [t[1] for t in self.opaqueItems()]

InitializeClass(OpaqueItemManager)


class CMFCatalogAware(CatalogAware, WorkflowAware, OpaqueItemManager):

    """Mix-in for notifying catalog and workflow and managing opaque items.
    """


def handleContentishEvent(ob, event):
    """ Event subscriber for (IContentish, IObjectEvent) events.
    """
    if IObjectAddedEvent.providedBy(event):
        ob.notifyWorkflowCreated()
        ob.indexObject()

    elif IObjectMovedEvent.providedBy(event):
        if event.newParent is not None:
            ob.indexObject()

    elif IObjectWillBeMovedEvent.providedBy(event):
        if event.oldParent is not None:
            ob.unindexObject()

    elif IObjectCopiedEvent.providedBy(event):
        if hasattr(aq_base(ob), 'workflow_history'):
            del ob.workflow_history

    elif IObjectCreatedEvent.providedBy(event):
        if hasattr(aq_base(ob), 'addCreator'):
            ob.addCreator()

def handleDynamicTypeCopiedEvent(ob, event):
    """ Event subscriber for (IDynamicType, IObjectCopiedEvent) events.
    """
    # Make sure owner local role is set after pasting
    # The standard Zope mechanisms take care of executable ownership
    current_user = _getAuthenticatedUser(ob)
    if current_user is None:
        return

    current_user_id = current_user.getId()
    if current_user_id is not None:
        local_role_holders = [ x[0] for x in ob.get_local_roles() ]
        ob.manage_delLocalRoles(local_role_holders)
        ob.manage_setLocalRoles(current_user_id, ['Owner'])

def dispatchToOpaqueItems(ob, event):
    """Dispatch an event to opaque sub-items of a given object.
    """
    for opaque in ob.opaqueValues():
        s = getattr(opaque, '_p_changed', 0)
        for ignored in subscribers((opaque, event), None):
            pass # They do work in the adapter fetch
        if s is None:
            opaque._p_deactivate()

def handleOpaqueItemEvent(ob, event):
    """ Event subscriber for (ICallableOpaqueItemEvents, IObjectEvent) events.
    """
    if IObjectAddedEvent.providedBy(event):
        if event.newParent is not None:
            ob.manage_afterAdd(ob, event.newParent)

    elif IObjectClonedEvent.providedBy(event):
        ob.manage_afterClone(ob)

    elif IObjectMovedEvent.providedBy(event):
        if event.newParent is not None:
            ob.manage_afterAdd(ob, event.newParent)

    elif IObjectWillBeMovedEvent.providedBy(event):
        if event.oldParent is not None:
            ob.manage_beforeDelete(ob, event.oldParent)
