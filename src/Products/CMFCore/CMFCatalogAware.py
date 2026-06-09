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
""" Base class for catalog aware content items.
"""

import logging
import transaction

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import aq_base
from App.special_dtml import DTMLFile
from ExtensionClass import Base
from OFS.interfaces import IObjectClonedEvent
from OFS.interfaces import IObjectWillBeMovedEvent
from zope.component import getUtilitiesFor
from zope.component import queryUtility
from zope.component import subscribers
from zope.interface import implementer
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectCopiedEvent
from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.lifecycleevent.interfaces import IObjectMovedEvent

from .interfaces import ICallableOpaqueItem
from .interfaces import ICatalogAware
from .interfaces import ICatalogTool
from .interfaces import IContextAwareIndexProvider
from .interfaces import IOpaqueItemManager
from .interfaces import IWorkflowAware
from .interfaces import IWorkflowTool
from .permissions import AccessContentsInformation
from .permissions import ManagePortal
from .permissions import ModifyPortalContent
from .utils import _dtmldir


logger = logging.getLogger('CMFCore.CMFCatalogAware')


@implementer(ICatalogAware)
class CatalogAware(Base):

    """Mix-in for notifying the catalog tool.
    """

    security = ClassSecurityInfo()

    # The following method can be overridden using inheritance so that it's
    # possible to specify another catalog tool for a given content type
    def _getCatalogTool(self):
        return queryUtility(ICatalogTool)

    #
    #   'ICatalogAware' interface methods
    #
    @security.protected(ModifyPortalContent)
    def indexObject(self):
        """ Index the object in the portal catalog.
        """
        catalog = self._getCatalogTool()
        if catalog is not None:
            catalog.indexObject(self)

    @security.protected(ModifyPortalContent)
    def unindexObject(self):
        """ Unindex the object from the portal catalog.
        """
        catalog = self._getCatalogTool()
        if catalog is not None:
            catalog.unindexObject(self)

    @security.protected(ModifyPortalContent)
    def reindexObject(self, idxs=[], update_metadata=1, uid=None):
        """ Reindex the object in the portal catalog.
        """
        if idxs == []:
            # Update the modification date.
            if hasattr(aq_base(self), 'notifyModified'):
                self.notifyModified()
        catalog = self._getCatalogTool()
        if catalog is not None:
            catalog.reindexObject(
                self,
                idxs=idxs,
                update_metadata=update_metadata,
                uid=uid)

    _cmf_security_indexes = ('allowedRolesAndUsers',)

    @security.protected(ModifyPortalContent)
    def reindexObjectSecurity(self, skip_self=False):
        """Reindex security-related indexes on the object.

        Uses ``_unrestrictedSearchResults`` instead of
        ``unrestrictedSearchResults`` to avoid triggering
        ``processQueue()`` mid-request.  This is safe because:

        1. **Pre-existing objects** are already in the catalog, the
           search finds them, and we queue a security reindex.
           ``optimize()`` merges with any other pending REINDEX.

        2. **Objects modified in this transaction** are still in the
           catalog under their existing path.  The search finds them
           and ``optimize()`` merges both REINDEXes.

        3. **Objects created in this transaction** have pending INDEX
           operations that will be processed at commit time and will
           index *all* attributes — including ``allowedRolesAndUsers``
           — using the current security state.
        """
        catalog = self._getCatalogTool()
        if catalog is None:
            return
        path = '/'.join(self.getPhysicalPath())

        # XXX if _getCatalogTool() is overriden we will have to change
        # this method for the sub-objects.
        search = getattr(catalog, '_unrestrictedSearchResults',
                         catalog.unrestrictedSearchResults)
        for brain in search(path=path):
            brain_path = brain.getPath()
            if brain_path == path and skip_self:
                continue
            # Get the object
            try:
                ob = brain._unrestrictedGetObject()
            except (AttributeError, KeyError):
                # don't fail on catalog inconsistency
                continue
            if ob is None:
                # Expected when objects were deleted in this transaction
                # but the queue hasn't been flushed yet.
                logger.debug('reindexObjectSecurity: Cannot get %s from '
                             'catalog (pending unindex)', brain_path)
                continue
            s = getattr(ob, '_p_changed', 0)
            ob.reindexObject(idxs=self._cmf_security_indexes,
                             update_metadata=0)
            if s is None:
                ob._p_deactivate()


InitializeClass(CatalogAware)


@implementer(IWorkflowAware)
class WorkflowAware(Base):

    """Mix-in for notifying the workflow tool.
    """

    security = ClassSecurityInfo()

    manage_options = ({'label': 'Workflows', 'action': 'manage_workflowsTab'},)

    _manage_workflowsTab = DTMLFile('zmi_workflows', _dtmldir)

    #
    #   ZMI methods
    #
    @security.protected(ManagePortal)
    def manage_workflowsTab(self, REQUEST, manage_tabs_message=None):
        """ Tab displaying the current workflows for the content object.
        """
        ob = self
        wtool = self._getWorkflowTool()
        # XXX None ?
        if wtool is not None:
            wf_ids = wtool.getChainFor(ob)
            states = {}
            chain = []
            for wf_id in wf_ids:
                wf = wtool.getWorkflowById(wf_id)
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
        return queryUtility(IWorkflowTool)

    #
    #   'IWorkflowAware' interface methods
    #
    @security.private
    def notifyWorkflowCreated(self):
        """ Notify the workflow that the object was just created.
        """
        wtool = self._getWorkflowTool()
        if wtool is not None:
            wtool.notifyCreated(self)


InitializeClass(WorkflowAware)


@implementer(IOpaqueItemManager)
class OpaqueItemManager(Base):

    """Mix-in for managing opaque items.
    """

    security = ClassSecurityInfo()

    # Opaque subitems
    # ---------------

    @security.protected(AccessContentsInformation)
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
        for name in self_base.__dict__:
            obj = getattr(self, name)
            if ICallableOpaqueItem.providedBy(obj):
                items.append((obj.getId(), obj))

        return tuple(items)

    @security.protected(AccessContentsInformation)
    def opaqueIds(self):
        """
            Return opaque ids (subelements that are contained
            using something that is not an ObjectManager).
        """
        return [t[0] for t in self.opaqueItems()]

    @security.protected(AccessContentsInformation)
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


@implementer(IContextAwareIndexProvider)
class _BuiltinLocationIndexProvider:
    """Default provider for location-based context-aware indexes.

    These indexes change when an object moves to a different container
    (its path and id change).
    """

    def getIndexNames(self):
        return ('path', 'getId', 'id')


@implementer(IContextAwareIndexProvider)
class _BuiltinSecurityIndexProvider:
    """Default provider for security context-aware indexes.

    allowedRolesAndUsers must be recomputed whenever the object moves
    into a differently-protected part of the tree.
    """

    def getIndexNames(self):
        return ('allowedRolesAndUsers',)


class _MovePathsRegistryKey:
    """Singleton used as key for ``transaction.set_data`` / ``transaction.data``.

    The ``transaction`` package stores arbitrary per-transaction data via
    ``Transaction.set_data(ob, value)`` / ``Transaction.data(ob)``, keyed by
    the identity (``id``) of *ob*.  Using a module-level singleton that is
    never garbage-collected gives a stable, collision-free key.
    """


#: Singleton key for the pending-move registry stored on the transaction.
_MOVE_PATHS_KEY = _MovePathsRegistryKey()


def _pending_move_paths():
    """Return the transaction-local dict ``{oid: old_path}`` for in-flight moves.

    On ``IObjectWillBeMovedEvent`` we record each object's current physical
    path here, keyed by its ZODB ``_p_oid``.  On ``IObjectMovedEvent`` we pop
    the entry and use it to call ``CatalogTool.moveObject``, which remaps the
    catalog RID without a full unindex + reindex.

    The map is stored via ``Transaction.set_data`` / ``Transaction.data`` —
    rather than as a volatile ``_v_`` attribute directly on each object —
    because volatile attributes are discarded whenever the ZODB object cache
    evicts an object (ghostification).  For large subtrees (tens of thousands
    of children) this caused the optimisation to silently fall back to a full
    reindex for all objects ghostified between the ``IObjectWillBeMovedEvent``
    and ``IObjectMovedEvent`` phases.  Transaction-attached data lives outside
    the ZODB object graph, is never affected by cache pressure, and is
    automatically discarded when the transaction commits or aborts.
    """
    txn = transaction.get()
    try:
        return txn.data(_MOVE_PATHS_KEY)
    except KeyError:
        registry = {}
        txn.set_data(_MOVE_PATHS_KEY, registry)
        return registry


def get_context_aware_indexes():
    """Return frozenset of all context-aware catalog index names.

    Aggregates all named IContextAwareIndexProvider utilities.
    Returns an empty frozenset if no providers are registered.
    """
    indexes = set()
    for _name, provider in getUtilitiesFor(IContextAwareIndexProvider):
        indexes.update(provider.getIndexNames())
    return frozenset(indexes)


def handleContentishEvent(ob, event):
    """ Event subscriber for (IContentish, IObjectEvent) events.
    """
    if IObjectAddedEvent.providedBy(event):
        wfaware = IWorkflowAware(ob, None)
        if wfaware is not None:
            wfaware.notifyWorkflowCreated()
        ob.indexObject()

    elif IObjectMovedEvent.providedBy(event):
        if event.newParent is not None:
            oid = getattr(ob, '_p_oid', None)
            old_path = _pending_move_paths().pop(oid, None) if oid else None
            if old_path is not None:
                # True move: optimization path — preserve catalog RID.
                catalog = queryUtility(ICatalogTool)
                if catalog is not None:
                    idxs = get_context_aware_indexes()
                    catalog.moveObject(ob, old_path, idxs)
                    return
            ob.indexObject()

    elif IObjectWillBeMovedEvent.providedBy(event):
        if event.oldParent is not None:
            if event.newParent is not None:
                # True move: record the current path so IObjectMovedEvent can
                # call moveObject() to remap the catalog RID instead of doing
                # a full unindex + reindex.  The path is stored in the
                # transaction data dict (keyed by _p_oid) rather than as a
                # volatile _v_ attribute on the object itself; volatile attrs
                # are lost when ZODB ghostifies an object under cache pressure,
                # which caused the optimisation to silently degrade for large
                # subtrees.  See _pending_move_paths() for details.
                catalog = queryUtility(ICatalogTool)
                idxs = get_context_aware_indexes()
                if catalog is not None and idxs:
                    oid = getattr(ob, '_p_oid', None)
                    if oid is not None:
                        _pending_move_paths()[oid] = '/'.join(
                            ob.getPhysicalPath())
                        return  # skip unindexObject; catalog entry preserved
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
    current_user = getSecurityManager().getUser()
    if current_user is None:
        return

    current_user_id = current_user.getId()
    if current_user_id is not None:
        local_role_holders = [x[0] for x in ob.get_local_roles()]
        ob.manage_delLocalRoles(local_role_holders)
        ob.manage_setLocalRoles(current_user_id, ['Owner'])


def dispatchToOpaqueItems(ob, event):
    """Dispatch an event to opaque sub-items of a given object.
    """
    for opaque in ob.opaqueValues():
        s = getattr(opaque, '_p_changed', 0)
        for ignored in subscribers((opaque, event), None):
            pass  # They do work in the adapter fetch
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
