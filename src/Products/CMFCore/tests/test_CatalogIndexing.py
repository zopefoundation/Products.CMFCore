from threading import Thread
from threading import current_thread
from time import sleep
from unittest import TestCase

from Acquisition import Implicit
from transaction import abort
from transaction import commit
from transaction import savepoint
from zope.component import provideUtility
from zope.interface import implementer
from zope.testing.cleanup import CleanUp

from ..indexing import INDEX
from ..indexing import REINDEX
from ..indexing import UNINDEX
from ..indexing import IndexQueue
from ..indexing import QueueTM
from ..indexing import getQueue
from ..interfaces import IIndexing
from ..interfaces import IIndexQueue
from ..interfaces import IIndexQueueProcessor
from .base.dummy import DummyContent
from .base.dummy import DummyFolder


@implementer(IIndexing)
class MockIndexer:

    def __init__(self):
        self.queue = []

    def index(self, obj, attributes=None):
        self.queue.append((INDEX, obj, attributes))

    def reindex(self, obj, attributes=None):
        self.queue.append((REINDEX, obj, attributes))

    def unindex(self, obj):
        self.queue.append((UNINDEX, obj, None))


@implementer(IIndexQueue)
class MockQueue(MockIndexer):

    processed = None

    def hook(self):
        pass

    def index(self, obj, attributes=None):
        super().index(obj, attributes)
        self.hook()

    def reindex(self, obj, attributes=None, update_metadata=1):
        super().reindex(obj, attributes)
        self.hook()

    def unindex(self, obj):
        super().unindex(obj)
        self.hook()

    def getState(self):
        return list(self.queue)     # better return a copy... :)

    def setState(self, state):
        self.queue = state

    def optimize(self):
        pass

    def process(self):
        self.processed = self.queue
        self.clear()
        return len(self.processed)

    def clear(self):
        self.queue = []


@implementer(IIndexQueueProcessor)
class MockQueueProcessor(MockQueue):

    state = 'unknown'

    def begin(self):
        self.state = 'started'

    def commit(self):
        self.state = 'finished'

    def abort(self):
        self.clear()
        self.state = 'aborted'


class QueueTests(CleanUp, TestCase):

    def setUp(self):
        self.queue = IndexQueue()

    def tearDown(self):
        self.queue.clear()

    def testInterface(self):
        self.assertTrue(IIndexQueue.providedBy(self.queue))

    def testQueueHook(self):
        class CaptainHook:
            def __init__(self):
                self.hooked = 0

            def __call__(self):
                self.hooked += 1

        hook = CaptainHook()
        queue = self.queue
        queue.setHook(hook)
        self.assertEqual(hook.hooked, 0)
        queue.index('foo')
        queue.reindex('foo')
        queue.reindex('bar')
        self.assertEqual(len(queue.getState()), 3)
        self.assertEqual(hook.hooked, 3)
        self.assertEqual(queue.process(), 2)
        self.assertEqual(hook.hooked, 3)

    def testQueueState(self):
        queue = self.queue
        queue.index('foo')
        self.assertEqual(queue.getState(), [(INDEX, 'foo', None, None)])
        state = queue.getState()
        queue.reindex('bar')
        self.assertEqual(queue.getState(),
                         [(INDEX, 'foo', None, None),
                          (REINDEX, 'bar', None, 1)])
        queue.setState(state)
        self.assertEqual(queue.getState(), [(INDEX, 'foo', None, None)])
        self.assertEqual(queue.process(), 1)

    def testQueueProcessor(self):
        queue = self.queue
        proc = MockQueueProcessor()
        provideUtility(proc, IIndexQueueProcessor)
        queue.index('foo')
        self.assertEqual(queue.process(), 1)    # also do the processing...
        self.assertEqual(queue.getState(), [])
        self.assertEqual(proc.getState(), [(INDEX, 'foo', [])])
        # the real queue won't update the state...
        self.assertEqual(proc.state, 'started')
        queue.commit()
        self.assertEqual(proc.state, 'finished')

    def testMultipleQueueProcessors(self):
        queue = self.queue
        proc1 = MockQueueProcessor()
        proc2 = MockQueueProcessor()
        provideUtility(proc1, IIndexQueueProcessor, name='proc1')
        provideUtility(proc2, IIndexQueueProcessor, name='proc2')
        queue.index('foo')
        self.assertEqual(queue.process(), 1)    # also do the processing...
        self.assertEqual(queue.getState(), [])
        self.assertEqual(proc1.getState(), [(INDEX, 'foo', [])])
        self.assertEqual(proc2.getState(), [(INDEX, 'foo', [])])
        self.assertEqual(proc1.state, 'started')    # the real queue won't...
        self.assertEqual(proc2.state, 'started')    # update the state...
        queue.commit()
        self.assertEqual(proc1.state, 'finished')
        self.assertEqual(proc2.state, 'finished')

    def testQueueOperations(self):
        queue = self.queue
        proc = MockQueueProcessor()
        provideUtility(proc, IIndexQueueProcessor)
        queue.index('foo')
        queue.reindex('foo')
        self.assertEqual(queue.process(), 1)
        self.assertEqual(queue.getState(), [])
        self.assertEqual(proc.getState(), [(INDEX, 'foo', [])])
        # the real queue won't update the state
        self.assertEqual(proc.state, 'started')
        queue.commit()
        self.assertEqual(proc.state, 'finished')

    def testQueueOptimization(self):
        queue = self.queue
        queue.index('foo')
        queue.reindex('foo')
        queue.unindex('foo')
        queue.index('foo', 'bar')
        queue.optimize()
        self.assertEqual(queue.getState(), [(INDEX, 'foo', [], None)])

    def testCustomQueueOptimization(self):
        def optimize(self):
            self.setState([op for op in self.getState() if not
                           op[0] == UNINDEX])

        queue = self.queue
        queue.index('foo')
        queue.reindex('foo')
        queue.unindex('foo')
        queue.index('foo', 'bar')
        queue.optimize()
        self.assertEqual(queue.getState(), [(INDEX, 'foo', [], None)])
        queue.clear()
        # hook up the custom optimize
        orig_optimize = queue.optimize
        try:
            queue.optimize = optimize
            queue.index('foo')
            queue.reindex('foo')
            queue.unindex('foo')
            queue.index('foo', 'bar')
            queue.optimize(queue)
            self.assertEqual(queue.getState(),
                             [(INDEX, 'foo', None, None),
                              (REINDEX, 'foo', None, 1),
                              (INDEX, 'foo', 'bar', None)])
        finally:
            queue.optimize = orig_optimize

    def testQueueAbortBeforeProcessing(self):
        queue = self.queue
        proc = MockQueueProcessor()
        provideUtility(proc, IIndexQueueProcessor)
        queue.index('foo')
        queue.reindex('foo')
        self.assertNotEqual(queue.getState(), [])
        queue.abort()
        self.assertEqual(queue.process(), 0)    # nothing left...
        self.assertEqual(queue.getState(), [])
        self.assertEqual(proc.getState(), [])
        self.assertEqual(proc.state, 'aborted')

    def testQueueAbortAfterProcessing(self):
        queue = self.queue
        proc = MockQueueProcessor()
        provideUtility(proc, IIndexQueueProcessor)
        queue.index('foo')
        queue.reindex('foo')
        self.assertEqual(queue.process(), 1)
        self.assertNotEqual(proc.getState(), [])
        queue.abort()
        self.assertEqual(queue.getState(), [])
        self.assertEqual(proc.getState(), [])
        self.assertEqual(proc.state, 'aborted')

    def testOptimizeQueuexx(self):
        queue = self.queue
        queue.setState([(REINDEX, 'A', None, 1), (REINDEX, 'A', None, 1)])
        queue.optimize()
        self.assertEqual(queue.getState(), [(REINDEX, 'A', [], 1)])

        queue.setState([(INDEX, 'A', None, 1), (REINDEX, 'A', None, 1)])
        queue.optimize()
        self.assertEqual(queue.getState(), [(INDEX, 'A', [], 1)])

        queue.setState([(INDEX, 'A', None, None), (UNINDEX, 'A', None, None)])
        queue.optimize()
        self.assertEqual(queue.getState(), [])

        queue.setState([(UNINDEX, 'A', None, None), (INDEX, 'A', None, None)])
        queue.optimize()
        self.assertEqual(queue.getState(), [(REINDEX, 'A', [], None)])

        queue.setState([(UNINDEX, 'A', None, None), (REINDEX, 'A', [], 1)])
        queue.optimize()
        self.assertEqual(queue.getState(), [(REINDEX, 'A', [], 1)])

    def testOptimizeQueueWithAttributes(self):
        queue = self.queue

        queue.setState([(REINDEX, 'A', None, 1),
                        (REINDEX, 'A', ('a', 'b'), 1)])
        queue.optimize()
        self.assertEqual(queue.getState(), [(REINDEX, 'A', [], 1)])

        queue.setState([(REINDEX, 'A', ('a', 'b'), 1),
                        (REINDEX, 'A', None, 1)])
        queue.optimize()
        self.assertEqual(queue.getState(), [(REINDEX, 'A', [], 1)])

        queue.setState([(REINDEX, 'A', ('a', 'b'), 1),
                        (REINDEX, 'A', ('b', 'c'), 1)])
        queue.optimize()
        self.assertEqual(queue.getState(),
                         [(REINDEX, 'A', ['a', 'b', 'c'], 1)])

        queue.setState([(INDEX, 'A', None, None), (REINDEX, 'A', None, 1)])
        queue.optimize()
        self.assertEqual(queue.getState(), [(INDEX, 'A', [], 1)])

        queue.setState([(REINDEX, 'A', ('a', 'b'), 1),
                        (UNINDEX, 'A', None, None),
                        (INDEX, 'A', None, 1)])
        queue.optimize()
        self.assertEqual(queue.getState(), [(REINDEX, 'A', [], 1)])

    def testOptimizeQueueSortsByOpcode(self):
        queue = self.queue

        queue.setState([(INDEX, 'C', None, 1), (UNINDEX, 'B', None, None)])
        queue.optimize()
        self.assertEqual(queue.getState(),
                         [(UNINDEX, 'B', [], None), (INDEX, 'C', [], 1)])

        queue.setState([(REINDEX, 'A', None, 1), (UNINDEX, 'B', None, None)])
        queue.optimize()
        self.assertEqual(queue.getState(),
                         [(UNINDEX, 'B', [], None), (REINDEX, 'A', [], 1)])

        queue.setState([(REINDEX, 'A', None, 1),
                        (UNINDEX, 'B', None, None),
                        (INDEX, 'C', None, 1)])
        queue.optimize()
        self.assertEqual(queue.getState(),
                         [(UNINDEX, 'B', [], None),
                         (REINDEX, 'A', [], 1),
                         (INDEX, 'C', [], 1)])


class QueueThreadTests(TestCase):
    """ thread tests modeled after zope.thread doctests """

    def setUp(self):
        self.me = getQueue()
        self.assertTrue(IIndexQueue.providedBy(self.me),
                        'non-queued indexer found')

    def tearDown(self):
        self.me.clear()

    def testLocalQueues(self):
        me = self.me                    # get the queued indexer...
        other = []

        def runner():                   # a callable for the thread to run...
            me.reindex('bar')
            other[:] = me.getState()

        thread = Thread(target=runner)  # another thread is created...
        thread.start()                  # and started...
        while thread.is_alive():
            pass                        # wait until it's done...
        self.assertEqual(other, [(REINDEX, 'bar', None, 1)])
        self.assertEqual(me.getState(), [])
        me.index('foo')                 # something happening on our side...
        self.assertEqual(other, [(REINDEX, 'bar', None, 1)])
        self.assertEqual(me.getState(), [(INDEX, 'foo', None, None)])
        thread.join()                   # finally the threads are re-united...

    def testQueuesOnTwoThreads(self):
        me = self.me                    # get the queued indexer...
        first = []

        def runner1():                  # and callables for the first...
            me.index('foo')
            first[:] = me.getState()

        thread1 = Thread(target=runner1)
        second = []

        def runner2():                  # and second thread
            me.index('bar')
            second[:] = me.getState()

        thread2 = Thread(target=runner2)
        self.assertEqual(first, [])     # clean table before we start...
        self.assertEqual(second, [])
        self.assertEqual(me.getState(), [])
        thread1.start()                 # do stuff here...
        sleep(0.01)                     # allow thread to do work
        self.assertEqual(first, [(INDEX, 'foo', None, None)])
        self.assertEqual(second, [])
        self.assertEqual(me.getState(), [])
        thread2.start()                 # and there...
        sleep(0.01)                     # allow thread to do work
        self.assertEqual(first, [(INDEX, 'foo', None, None)])
        self.assertEqual(second, [(INDEX, 'bar', None, None)])
        self.assertEqual(me.getState(), [])
        thread1.join()                  # re-unite with first thread and...
        me.unindex('f00')               # let something happening on our side
        self.assertEqual(first, [(INDEX, 'foo', None, None)])
        self.assertEqual(second, [(INDEX, 'bar', None, None)])
        self.assertEqual(me.getState(), [(UNINDEX, 'f00', None, None)])
        thread2.join()                  # also re-unite the second and...
        me.unindex('f00')               # let something happening again...
        self.assertEqual(first, [(INDEX, 'foo', None, None)])
        self.assertEqual(second, [(INDEX, 'bar', None, None)])
        self.assertEqual(me.getState(),
                         [(UNINDEX, 'f00', None, None),
                          (UNINDEX, 'f00', None, None)])

    def testManyThreads(self):
        me = self.me                    # get the queued indexer...
        queues = {}                     # container for local queues

        def makeRunner(name, idx):
            def runner():
                for n in range(idx):    # index idx times
                    me.index(name)
                queues[current_thread()] = me.queue
            return runner

        threads = []
        for idx in range(99):
            threads.append(Thread(target=makeRunner('t%d' % idx, idx)))
        for thread in threads:
            thread.start()
            sleep(0.01)                 # just in case
        for thread in threads:
            thread.join()
        for idx, thread in enumerate(threads):
            tid = 't%d' % idx
            queue = queues[thread]
            names = [name for op, name, attrs, metadata in queue]
            self.assertEqual(names, [tid] * idx)


class QueueTransactionManagerTests(TestCase):

    def setUp(self):
        self.queue = MockQueueProcessor()
        self.tman = QueueTM(self.queue)
        self.queue.hook = self.tman.register    # transaction manager hook

    def testFlushQueueOnCommit(self):
        self.queue.index('foo')
        commit()
        self.assertEqual(self.queue.getState(), [])
        self.assertEqual(self.queue.processed, [(INDEX, 'foo', None)])
        self.assertEqual(self.queue.state, 'finished')

    def testFlushQueueOnAbort(self):
        self.queue.index('foo')
        abort()
        self.assertEqual(self.queue.getState(), [])
        self.assertEqual(self.queue.processed, None)
        self.assertEqual(self.queue.state, 'aborted')

    def testUseSavePoint(self):
        self.queue.index('foo')
        savepoint()
        self.queue.reindex('bar')
        commit()
        self.assertEqual(self.queue.getState(), [])
        self.assertEqual(self.queue.processed,
                         [(INDEX, 'foo', None),
                          (REINDEX, 'bar', None)])
        self.assertEqual(self.queue.state, 'finished')

    def testRollbackSavePoint(self):
        self.queue.index('foo')
        sp = savepoint()
        self.queue.reindex('bar')
        sp.rollback()
        commit()
        self.assertEqual(self.queue.getState(), [])
        self.assertEqual(self.queue.processed, [(INDEX, 'foo', None)])
        self.assertEqual(self.queue.state, 'finished')


class FakeFolder(Implicit):
    id = 'portal'

    def getPhysicalPath(self):
        return ('portal',)


class UnindexWrapperTests(TestCase):

    def setUp(self):
        self.root = FakeFolder()
        self.root.sub1 = DummyFolder('sub1')
        self.root.sub1.testcontent = DummyContent('testcontent')
        self.root.sub1.testcontent.title = 'Test Title'

    def test_wrap_content(self):
        from ..indexing import wrap

        unwrapped = self.root.sub1.testcontent
        wrapped = wrap(unwrapped)

        self.assertTrue(unwrapped.getPhysicalPath()[-1], 'testcontent')
        self.assertEqual(unwrapped.getPhysicalPath(),
                         wrapped.getPhysicalPath())
        self.assertEqual(hash(unwrapped), hash(wrapped))
        self.assertEqual(unwrapped.Title(), wrapped.Title())

        # change the id of our test content, which changes getPhysicalPath
        # All other attributes/methods remain unchanged
        unwrapped.id = 'test2'
        self.assertTrue(unwrapped.getPhysicalPath()[-1], 'test2')
        self.assertNotEqual(unwrapped.getPhysicalPath(),
                            wrapped.getPhysicalPath())
        self.assertEqual(hash(unwrapped), hash(wrapped))
        self.assertEqual(unwrapped.Title(), wrapped.Title())
