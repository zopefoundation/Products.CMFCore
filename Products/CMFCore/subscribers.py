"""
Subscriber Support
------------------

The package comes with support for queueing up and performing indexing
operations via event subscribers.  The idea behind this is to not rely on
explicit calls as defined in ``CMFCatalogAware`` alone, but instead make it
possible to phase them out eventually. As the additional indexing operations
added via the subscribers are optimized away anyway, this only adds very
little processing overhead.

However, even though ``IObjectModifiedEvent`` has support for partial
reindexing by passing a list of descriptions/index names, this is currently
not used anywhere in Plone. Unfortunately that means that partial reindex
operations will be "upgraded" to full reindexes, e.g. for
``IContainerModifiedEvent`` via the ``notifyContainerModified`` helper,
which is one reason why subscriber support is not enabled by default for now.

To activate please use::

    [instance]
    ...
    zcml = Products.CMFCore:subscribers.zcml

instead of just the package name itself, re-run buildout and restart your
Plone instance.
"""
from zope.container.contained import dispatchToSublocations
from zope.event import notify
from zope.lifecycleevent import Attributes
from zope.lifecycleevent import ObjectModifiedEvent

from .indexing import filterTemporaryItems
from .indexing import getQueue


def objectAdded(ev):
    obj = filterTemporaryItems(ev.object)
    if obj is not None:
        indexer = getQueue()
        indexer.index(obj)


def objectModified(ev):
    obj = filterTemporaryItems(ev.object)
    if obj is None:
        return
    indexer = getQueue()
    if getattr(ev, 'descriptions', None):   # not used by archetypes/plone atm
        # build the list of to be updated attributes
        attrs = []
        for desc in ev.descriptions:
            if isinstance(desc, Attributes):
                attrs.extend(desc.attributes)
        indexer.reindex(obj, attrs)
        if 'allow' in attrs:    # dispatch to sublocations on security changes
            dispatchToSublocations(ev.object, ev)
    else:
        # with no descriptions (of changed attributes) just reindex all
        indexer.reindex(obj)


def objectCopied(ev):
    objectAdded(ev)


def objectRemoved(ev):
    obj = filterTemporaryItems(ev.object, checkId=False)
    if obj is not None:
        indexer = getQueue()
        indexer.unindex(obj)


def objectMoved(ev):
    if ev.newParent is None or ev.oldParent is None:
        # it's an IObjectRemovedEvent or IObjectAddedEvent
        return
    if ev.newParent is ev.oldParent:
        # it's a renaming operation
        dispatchToSublocations(ev.object, ev)
    obj = filterTemporaryItems(ev.object)
    indexer = getQueue()
    if obj is not None:
        indexer = getQueue()
        indexer.index(obj)


def dispatchObjectMovedEvent(ob, ev):
    """ dispatch events to sub-items when a folderish item has been renamed """
    if ob is not ev.object:
        if ev.oldParent is ev.newParent:
            notify(ObjectModifiedEvent(ob))


def objectTransitioned(ev):
    obj = filterTemporaryItems(ev.object)
    if obj is not None:
        indexer = getQueue()
        indexer.reindex(obj)
