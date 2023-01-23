from logging import getLogger
from operator import itemgetter
from threading import local
from warnings import warn

from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from transaction import get as getTransaction
from transaction.interfaces import ISavepointDataManager
from zope.component import getSiteManager
from zope.interface import implementer
from zope.proxy import ProxyBase
from zope.proxy import non_overridable
from zope.publisher.interfaces.browser import IBrowserRequest

from .interfaces import IIndexQueue
from .interfaces import IIndexQueueProcessor
from .interfaces import InvalidQueueOperation
from .interfaces import IPortalCatalogQueueProcessor
from .utils import getToolByName


# constants for indexing operations
UNINDEX = -1
REINDEX = 0
INDEX = 1

logger = getLogger('Products.CMFCore.indexing')
debug = logger.debug

localQueue = None
processing = set()


@implementer(IPortalCatalogQueueProcessor)
class PortalCatalogProcessor:
    """An index queue processor for the standard portal catalog via
       the `CatalogMultiplex` and `CMFCatalogAware` mixin classes """

    def index(self, obj, attributes=None):
        catalog = getToolByName(obj, 'portal_catalog', None)
        if catalog is not None:
            catalog._indexObject(obj)

    def reindex(self, obj, attributes=None, update_metadata=1):
        catalog = getToolByName(obj, 'portal_catalog', None)
        if catalog is not None:
            catalog._reindexObject(
                obj,
                idxs=attributes,
                update_metadata=update_metadata)

    def unindex(self, obj):
        catalog = getToolByName(obj, 'portal_catalog', None)
        if catalog is not None:
            catalog._unindexObject(obj)

    def begin(self):
        pass

    def commit(self):
        pass

    def abort(self):
        pass

    @staticmethod
    def get_dispatcher(obj, name):
        """ return named indexing method according on the used mixin class """
        warn('get_dispatcher is deprecated and will be removed in version 2.5')
        catalog = getToolByName(obj, 'portal_catalog', None)
        if catalog is None:
            return
        attr = getattr(catalog, f'_{name}', None)
        if attr is None:
            return
        return attr.__func__


def getQueue():
    """ return a (thread-local) queue object, create one if necessary """
    global localQueue
    if localQueue is None:
        localQueue = IndexQueue()
    return localQueue


def processQueue():
    """ process the queue (for this thread) immediately """
    queue = getQueue()
    processed = 0
    if queue.length() and queue not in processing:
        debug('auto-flushing %d items: %r', queue.length(), queue.getState())
        try:
            processing.add(queue)
            processed = queue.process()
        finally:
            processing.remove(queue)
    return processed


class PathProxy(ProxyBase):

    def __init__(self, obj):
        super().__init__(obj)
        self._old_path = obj.getPhysicalPath()

    @non_overridable
    def getPhysicalPath(self):
        return self._old_path


def wrap(obj):
    """ the indexing key, i.e. the path to the object in the case of the
        portal catalog, might have changed while the unindex operation was
        delayed, for example due to renaming the object;  it was probably not
        such a good idea to use a key that can change in the first place, but
        to work around this a proxy object is used, which can provide the
        original path;  of course, access to other attributes must still be
        possible, since alternate indexers (i.e. solr etc) might use another
        unique key, usually the object's uid;  also the inheritence tree
        must match """
    if getattr(aq_base(obj), 'getPhysicalPath', None) is None:
        return obj

    return PathProxy(obj)


@implementer(IIndexQueue)
class IndexQueue(local):

    def __init__(self):
        self.queue = []
        self.tmhook = None

    def hook(self):
        """ register a hook into the transaction machinery if that hasn't
            already been done;  this is to make sure the queue's processing
            method gets called back just before the transaction is about to
            be committed """
        if self.tmhook is None:
            self.tmhook = QueueTM(self).register
        self.tmhook()

    def index(self, obj, attributes=None):
        self.queue.append((INDEX, obj, attributes, None))
        self.hook()

    def reindex(self, obj, attributes=None, update_metadata=1):
        self.queue.append((REINDEX, obj, attributes, update_metadata))
        self.hook()

    def unindex(self, obj):
        self.queue.append((UNINDEX, wrap(obj), None, None))
        self.hook()

    def setHook(self, hook):
        self.tmhook = hook

    def getState(self):
        return self.queue[:]

    def setState(self, state):
        self.queue[:] = state

    def length(self):
        """ return number of currently queued items;  please note that
            we cannot use `__len__` here as this will cause test failures
            due to the way objects are compared """
        return len(self.queue)

    def optimize(self):
        res = {}
        for iop, obj, iattr, imetadata in self.getState():
            hash_id = hash(obj)
            func = getattr(obj, 'getPhysicalPath', None)
            if callable(func):
                hash_id = hash_id, func()
            op, dummy, attr, metadata = res.get(hash_id,
                                                (0, obj, iattr, imetadata))
            # If we are going to delete an item that was added in this
            # transaction, ignore it
            if op == INDEX and iop == UNINDEX:
                del res[hash_id]
            else:
                if op == UNINDEX and iop == REINDEX:
                    op = REINDEX
                else:
                    # Operators are -1, 0 or 1 which makes it safe to add them
                    op += iop
                    # operator always within -1 and 1
                    op = min(max(op, UNINDEX), INDEX)

                # Handle attributes, None means all fields,
                # and takes precedence
                if attr and iattr and isinstance(attr, (tuple, list)) and \
                        isinstance(iattr, (tuple, list)):
                    attr = sorted(set(attr).union(iattr))
                else:
                    attr = []

                if imetadata == 1 or metadata == 1:
                    metadata = 1

                res[hash_id] = (op, obj, attr, metadata)

        debug('finished reducing; %d item(s) in queue...', len(res))
        # Sort so unindex operations come first
        self.setState(sorted(res.values(), key=itemgetter(0)))

    def process(self):
        self.optimize()
        if not self.queue:
            return 0
        sm = getSiteManager()
        utilities = list(sm.getUtilitiesFor(IIndexQueueProcessor))
        processed = 0
        for name, util in utilities:
            util.begin()
        # ??? must the queue be handled independently for each processor?
        for op, obj, attributes, metadata in self.queue:
            for name, util in utilities:
                if op == INDEX:
                    util.index(obj, attributes)
                elif op == REINDEX:
                    util.reindex(obj, attributes, update_metadata=metadata)
                elif op == UNINDEX:
                    util.unindex(obj)
                else:
                    raise InvalidQueueOperation(op)
            processed += 1
        debug('finished processing %d items...', processed)
        self.clear()
        return processed

    def commit(self):
        sm = getSiteManager()
        for name, util in sm.getUtilitiesFor(IIndexQueueProcessor):
            util.commit()

    def abort(self):
        sm = getSiteManager()
        for name, util in sm.getUtilitiesFor(IIndexQueueProcessor):
            util.abort()
        self.clear()

    def clear(self):
        del self.queue[:]
        # release transaction manager
        self.tmhook = None


def filterTemporaryItems(obj, checkId=True):
    """ check if the item has an acquisition chain set up and is not of
        temporary nature, i.e. still handled by the `portal_factory`;  if
        so return it, else return None """
    parent = aq_parent(aq_inner(obj))
    if parent is None:
        return None
    if IBrowserRequest.providedBy(parent):
        return None
    if checkId and getattr(obj, 'getId', None):
        parent = aq_base(parent)
        if getattr(parent, '__contains__', None) is None:
            return None
        elif obj.getId() not in parent:
            return None
    isTemporary = getattr(obj, 'isTemporary', None)
    if isTemporary is not None:
        try:
            if obj.isTemporary():
                return None
        except TypeError:
            return None  # `isTemporary` on the `FactoryTool` expects 2 args
    return obj


class QueueSavepoint:
    """ transaction savepoints using the IIndexQueue interface """

    def __init__(self, queue):
        self.queue = queue
        self.state = queue.getState()

    def rollback(self):
        self.queue.setState(self.state)


@implementer(ISavepointDataManager)
class QueueTM(local):
    """ transaction manager hook for the indexing queue """

    def __init__(self, queue):
        local.__init__(self)
        self.registered = False
        self.vote = False
        self.queue = queue

    def register(self):
        if not self.registered:
            transaction = getTransaction()
            transaction.join(self)
            transaction.addBeforeCommitHook(self.before_commit)
            self.registered = True

    def savepoint(self):
        return QueueSavepoint(self.queue)

    def tpc_begin(self, transaction):
        pass

    def commit(self, transaction):
        pass

    def before_commit(self):
        self.queue.process()
        self.queue.clear()

    def tpc_vote(self, transaction):
        pass

    def tpc_finish(self, transaction):
        self.queue.commit()
        self.registered = False

    def tpc_abort(self, transaction):
        self.queue.abort()
        self.queue.clear()
        self.registered = False

    abort = tpc_abort

    def sortKey(self):
        return str(id(self))
