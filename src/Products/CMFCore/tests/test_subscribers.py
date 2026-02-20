import importlib.util
import unittest
from unittest import TestCase
from unittest.mock import patch

from Acquisition import Implicit
from zope.lifecycleevent import Attributes

from ..indexing import INDEX
from ..indexing import REINDEX
from ..indexing import UNINDEX
from ..subscribers import objectAdded as _oa


MOD = _oa.__module__


class FakeFolder(Implicit):
    """Minimal acquisition-wrapped container so filterTemporaryItems works."""

    def __init__(self, id='folder'):
        self.id = id

    def getId(self):
        return self.id

    def __contains__(self, id):
        return hasattr(self, id)


class FakeContent(Implicit):
    """Minimal content object with acquisition support."""

    def __init__(self, id='content'):
        self.id = id

    def getId(self):
        return self.id

    def getPhysicalPath(self):
        return ('', 'folder', self.id)


class FakeEvent:
    """Minimal event carrying an object reference."""

    def __init__(self, obj, **kw):
        self.object = obj
        self.__dict__.update(kw)


class FakeMovedEvent(FakeEvent):
    """Event with oldParent/newParent for move/rename/add/remove."""

    def __init__(self, obj, oldParent=None, newParent=None):
        super().__init__(obj)
        self.oldParent = oldParent
        self.newParent = newParent


class FakeQueue:
    """Records indexing operations."""

    def __init__(self):
        self.ops = []

    def index(self, obj, attributes=None):
        self.ops.append((INDEX, obj, attributes))

    def reindex(self, obj, attributes=None, update_metadata=1):
        self.ops.append((REINDEX, obj, attributes))

    def unindex(self, obj):
        self.ops.append((UNINDEX, obj, None))


def _make_obj(id='doc'):
    folder = FakeFolder()
    obj = FakeContent(id).__of__(folder)
    setattr(folder, id, obj)
    return folder, obj


class TestObjectAdded(TestCase):

    def _call(self, ev):
        from ..subscribers import objectAdded
        objectAdded(ev)

    def test_indexes_object(self):
        folder, obj = _make_obj()
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            self._call(FakeEvent(obj))
        self.assertEqual(len(queue.ops), 1)
        self.assertEqual(queue.ops[0][0], INDEX)

    def test_skips_temporary_item(self):
        obj = FakeContent('doc')
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            self._call(FakeEvent(obj))
        self.assertEqual(queue.ops, [])


class TestObjectModified(TestCase):

    def _call(self, ev):
        from ..subscribers import objectModified
        objectModified(ev)

    def test_full_reindex_without_descriptions(self):
        folder, obj = _make_obj()
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            self._call(FakeEvent(obj))
        self.assertEqual(len(queue.ops), 1)
        self.assertEqual(queue.ops[0][0], REINDEX)
        self.assertEqual(queue.ops[0][2], None)

    def test_partial_reindex_with_descriptions(self):
        folder, obj = _make_obj()
        desc = Attributes(None, 'title', 'description')
        ev = FakeEvent(obj, descriptions=(desc,))
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            self._call(ev)
        self.assertEqual(len(queue.ops), 1)
        self.assertEqual(queue.ops[0][0], REINDEX)
        self.assertIn('title', queue.ops[0][2])
        self.assertIn('description', queue.ops[0][2])

    def test_skips_temporary_item(self):
        obj = FakeContent('doc')
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            self._call(FakeEvent(obj))
        self.assertEqual(queue.ops, [])


class TestObjectCopied(TestCase):

    def test_queues_index(self):
        from ..subscribers import objectCopied

        folder, obj = _make_obj()
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            objectCopied(FakeEvent(obj))
        self.assertEqual(len(queue.ops), 1)
        self.assertEqual(queue.ops[0][0], INDEX)


class TestObjectRemoved(TestCase):

    def _call(self, ev):
        from ..subscribers import objectRemoved
        objectRemoved(ev)

    def test_queues_unindex(self):
        folder, obj = _make_obj()
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            self._call(FakeEvent(obj))
        self.assertEqual(len(queue.ops), 1)
        self.assertEqual(queue.ops[0][0], UNINDEX)

    def test_skips_temporary_item(self):
        obj = FakeContent('doc')
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            self._call(FakeEvent(obj))
        self.assertEqual(queue.ops, [])


class TestObjectMoved(TestCase):

    def _call(self, ev):
        from ..subscribers import objectMoved
        objectMoved(ev)

    def test_skips_removed_event(self):
        """newParent=None means removal, handled by objectRemoved."""
        folder, obj = _make_obj()
        ev = FakeMovedEvent(obj, oldParent=folder, newParent=None)
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            self._call(ev)
        self.assertEqual(queue.ops, [])

    def test_skips_added_event(self):
        """oldParent=None means addition, handled by objectAdded."""
        folder, obj = _make_obj()
        ev = FakeMovedEvent(obj, oldParent=None, newParent=folder)
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            self._call(ev)
        self.assertEqual(queue.ops, [])

    def test_move_between_folders(self):
        folder, obj = _make_obj()
        other = FakeFolder('other')
        ev = FakeMovedEvent(obj, oldParent=folder, newParent=other)
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            self._call(ev)
        self.assertEqual(len(queue.ops), 1)
        self.assertEqual(queue.ops[0][0], INDEX)

    def test_rename_dispatches_to_sublocations(self):
        """When oldParent is newParent it's a rename."""
        folder, obj = _make_obj()
        ev = FakeMovedEvent(obj, oldParent=folder, newParent=folder)
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue), \
                patch(f'{MOD}.dispatchToSublocations') as disp:
            self._call(ev)
            disp.assert_called_once_with(obj, ev)
        self.assertEqual(len(queue.ops), 1)
        self.assertEqual(queue.ops[0][0], INDEX)


class TestDispatchObjectMovedEvent(TestCase):

    def _call(self, ob, ev):
        from ..subscribers import dispatchObjectMovedEvent
        dispatchObjectMovedEvent(ob, ev)

    def test_noop_when_ob_is_event_object(self):
        folder, obj = _make_obj()
        ev = FakeMovedEvent(obj, oldParent=folder, newParent=folder)
        with patch(f'{MOD}.notify') as mock_notify:
            self._call(obj, ev)
            mock_notify.assert_not_called()

    def test_dispatches_modified_on_rename(self):
        folder = FakeFolder()
        parent_obj = FakeContent('parent').__of__(folder)
        child_obj = FakeContent('child').__of__(folder)
        ev = FakeMovedEvent(parent_obj, oldParent=folder, newParent=folder)
        with patch(f'{MOD}.notify') as mock_notify:
            self._call(child_obj, ev)
            mock_notify.assert_called_once()
            from zope.lifecycleevent import ObjectModifiedEvent
            notified_ev = mock_notify.call_args[0][0]
            self.assertIsInstance(notified_ev, ObjectModifiedEvent)

    def test_noop_on_real_move(self):
        folder = FakeFolder()
        other = FakeFolder('other')
        parent_obj = FakeContent('parent').__of__(folder)
        child_obj = FakeContent('child').__of__(folder)
        ev = FakeMovedEvent(parent_obj, oldParent=folder, newParent=other)
        with patch(f'{MOD}.notify') as mock_notify:
            self._call(child_obj, ev)
            mock_notify.assert_not_called()


class TestObjectTransitioned(TestCase):

    def test_queues_reindex(self):
        from ..subscribers import objectTransitioned

        folder, obj = _make_obj()
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            objectTransitioned(FakeEvent(obj))
        self.assertEqual(len(queue.ops), 1)
        self.assertEqual(queue.ops[0][0], REINDEX)

    def test_skips_temporary_item(self):
        from ..subscribers import objectTransitioned

        obj = FakeContent('doc')
        queue = FakeQueue()
        with patch(f'{MOD}.getQueue', return_value=queue):
            objectTransitioned(FakeEvent(obj))
        self.assertEqual(queue.ops, [])


# --- Integration tests: real queue, real events, ZCML-registered handlers ---

class SubscribersIntegrationTests(TestCase):
    """Integration tests exercising subscribers via real event dispatch
    with the real IndexQueue (no mocking of getQueue/filterTemporaryItems).
    """

    from ..testing import SubscribersZCMLLayer as layer

    def setUp(self):
        # Must use absolute import to get the same module instance
        # that ZCML-registered handlers use (Products.CMFCore.indexing),
        # not the relative import (CMFCore.indexing) which may be a
        # different module due to namespace package dual-import.
        from Products.CMFCore.indexing import getQueue
        self.queue = getQueue()
        self.queue.clear()

    def tearDown(self):
        self.queue.clear()

    def test_objectAdded_created_event(self):
        from zope.event import notify
        from zope.lifecycleevent import ObjectCreatedEvent

        _, obj = _make_obj()
        notify(ObjectCreatedEvent(obj))

        state = self.queue.getState()
        self.assertEqual(len(state), 1)
        self.assertEqual(state[0][0], INDEX)

    def test_objectAdded_added_event(self):
        from zope.event import notify
        from zope.lifecycleevent import ObjectAddedEvent

        folder, obj = _make_obj()
        notify(ObjectAddedEvent(obj, newParent=folder, newName='doc'))

        # ObjectAddedEvent is also an IObjectMovedEvent, so objectMoved
        # fires too but returns early (oldParent=None).  Only 1 INDEX.
        ops = [s[0] for s in self.queue.getState()]
        self.assertEqual(ops.count(INDEX), 1)

    def test_objectAdded_skips_unwrapped(self):
        from zope.event import notify
        from zope.lifecycleevent import ObjectCreatedEvent

        obj = FakeContent('doc')  # no acquisition wrapper
        notify(ObjectCreatedEvent(obj))

        self.assertEqual(self.queue.getState(), [])

    def test_objectModified_full_reindex(self):
        from zope.event import notify
        from zope.lifecycleevent import ObjectModifiedEvent

        _, obj = _make_obj()
        notify(ObjectModifiedEvent(obj))

        state = self.queue.getState()
        self.assertEqual(len(state), 1)
        op, _, attrs, _ = state[0]
        self.assertEqual(op, REINDEX)
        self.assertIsNone(attrs)

    def test_objectModified_partial_reindex(self):
        from zope.event import notify
        from zope.lifecycleevent import ObjectModifiedEvent

        _, obj = _make_obj()
        desc = Attributes(None, 'title', 'description')
        notify(ObjectModifiedEvent(obj, desc))

        state = self.queue.getState()
        self.assertEqual(len(state), 1)
        op, _, attrs, _ = state[0]
        self.assertEqual(op, REINDEX)
        self.assertIn('title', attrs)
        self.assertIn('description', attrs)

    def test_objectCopied_queues_index(self):
        from zope.event import notify
        from zope.lifecycleevent import ObjectCopiedEvent

        folder, obj = _make_obj()
        original = FakeContent('original').__of__(folder)
        setattr(folder, 'original', original)
        notify(ObjectCopiedEvent(obj, original))

        ops = [s[0] for s in self.queue.getState()]
        self.assertIn(INDEX, ops)

    def test_objectRemoved_queues_unindex(self):
        from zope.event import notify
        from zope.lifecycleevent import ObjectRemovedEvent

        folder, obj = _make_obj()
        notify(ObjectRemovedEvent(obj, oldParent=folder, oldName='doc'))

        # ObjectRemovedEvent is also IObjectMovedEvent; objectMoved fires
        # but returns early (newParent=None).
        state = self.queue.getState()
        unindex_ops = [s for s in state if s[0] == UNINDEX]
        self.assertEqual(len(unindex_ops), 1)
        # unindex wraps in PathProxy; verify path is preserved
        self.assertEqual(
            unindex_ops[0][1].getPhysicalPath(), obj.getPhysicalPath())

    def test_objectMoved_skips_add(self):
        """ObjectAddedEvent triggers objectMoved but it returns early."""
        from zope.event import notify
        from zope.lifecycleevent import ObjectAddedEvent

        folder, obj = _make_obj()
        notify(ObjectAddedEvent(obj, newParent=folder, newName='doc'))

        # objectAdded produces 1 INDEX; objectMoved should NOT add another
        ops = [s[0] for s in self.queue.getState()]
        self.assertEqual(ops.count(INDEX), 1)

    def test_objectMoved_skips_remove(self):
        """ObjectRemovedEvent triggers objectMoved but it returns early."""
        from zope.event import notify
        from zope.lifecycleevent import ObjectRemovedEvent

        folder, obj = _make_obj()
        notify(ObjectRemovedEvent(obj, oldParent=folder, oldName='doc'))

        # objectRemoved produces 1 UNINDEX; objectMoved should NOT add more
        ops = [s[0] for s in self.queue.getState()]
        self.assertEqual(ops.count(UNINDEX), 1)
        self.assertNotIn(INDEX, ops)

    def test_objectMoved_real_move(self):
        from zope.event import notify
        from zope.lifecycleevent import ObjectMovedEvent

        folder, obj = _make_obj()
        other = FakeFolder('other')

        notify(ObjectMovedEvent(obj, folder, 'doc', other, 'doc'))

        state = self.queue.getState()
        ops = [s[0] for s in state]
        self.assertIn(INDEX, ops)

    def test_objectMoved_rename(self):
        from zope.event import notify
        from zope.lifecycleevent import ObjectMovedEvent

        folder, obj = _make_obj()
        notify(ObjectMovedEvent(obj, folder, 'doc', folder, 'newdoc'))

        state = self.queue.getState()
        ops = [s[0] for s in state]
        self.assertIn(INDEX, ops)

    def test_dispatch_rename_chains_to_modified(self):
        """dispatchObjectMovedEvent fires ObjectModifiedEvent on children,
        which objectModified picks up and queues a REINDEX.
        """
        from zope.lifecycleevent import ObjectMovedEvent

        from ..subscribers import dispatchObjectMovedEvent

        folder, parent = _make_obj('parent')
        child = FakeContent('child').__of__(folder)
        setattr(folder, 'child', child)

        ev = ObjectMovedEvent(parent, folder, 'parent', folder, 'newparent')
        # Call directly — dispatchObjectMovedEvent is registered for
        # (IItem, IObjectMovedEvent) but FakeContent doesn't provide IItem.
        dispatchObjectMovedEvent(child, ev)

        # The chained notify(ObjectModifiedEvent(child)) goes through real
        # event dispatch to the ZCML-registered objectModified handler.
        state = self.queue.getState()
        self.assertEqual(len(state), 1)
        self.assertEqual(state[0][0], REINDEX)

    def test_dispatch_noop_on_real_move(self):
        from zope.lifecycleevent import ObjectMovedEvent

        from ..subscribers import dispatchObjectMovedEvent

        folder, parent = _make_obj('parent')
        other = FakeFolder('other')
        child = FakeContent('child').__of__(folder)
        setattr(folder, 'child', child)

        ev = ObjectMovedEvent(parent, folder, 'parent', other, 'parent')
        dispatchObjectMovedEvent(child, ev)

        self.assertEqual(self.queue.getState(), [])

    @unittest.skipUnless(
        importlib.util.find_spec('Products.DCWorkflow'),
        'Products.DCWorkflow not installed',
    )
    def test_objectTransitioned(self):
        from zope.event import notify
        from zope.interface import implementer

        from Products.DCWorkflow.interfaces import IAfterTransitionEvent

        @implementer(IAfterTransitionEvent)
        class FakeTransitionEvent:
            def __init__(self, ob):
                self.object = ob
                self.workflow = None
                self.old_state = None
                self.new_state = None
                self.transition = None
                self.status = {}
                self.kwargs = {}

        _, obj = _make_obj()
        notify(FakeTransitionEvent(obj))

        state = self.queue.getState()
        self.assertEqual(len(state), 1)
        self.assertEqual(state[0][0], REINDEX)
