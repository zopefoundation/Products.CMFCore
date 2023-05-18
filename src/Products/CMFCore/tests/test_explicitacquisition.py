from io import StringIO

from zExceptions import NotFound
from zope.event import notify
from zope.interface import alsoProvides
from zope.publisher.interfaces.browser import IBrowserRequest
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.pubevents import PubAfterTraversal

from ..interfaces import IPublishableThroughAcquisition
from ..testing import FunctionalZCMLLayer
from .base.dummy import DummyContent
from .base.testcase import RequestTest


class TestExplicitAcquisition(RequestTest):
    layer = FunctionalZCMLLayer

    def setUp(self):
        super().setUp()
        environment = {
            "URL": "",
            "PARENTS": [self.app],
            "REQUEST_METHOD": "GET",
            "SERVER_PORT": "80",
            "REQUEST_METHOD": "GET",
            "steps": [],
            "SERVER_NAME": "localhost",
            "_hacked_path": 0,
        }
        self.request = request = HTTPRequest(StringIO(), environment, HTTPResponse())
        request.other.update(environment)
        alsoProvides(request, IBrowserRequest)

        self.app.snuk = DummyContent(id="snuk")
        self.app.foo = DummyContent(id="foo")
        self.app.foo.bar = DummyContent(id="bar")

    def test_notfound_when_acquired(self):
        self.assertFalse(IPublishableThroughAcquisition.providedBy(self.request))
        self.request.traverse("foo/foo/bar/snuk/foo")
        with self.assertRaises(NotFound):
            notify(PubAfterTraversal(self.request))

    def test_allow_for_item(self):
        self.assertFalse(IPublishableThroughAcquisition.providedBy(self.request))
        alsoProvides(self.app.snuk, IPublishableThroughAcquisition)
        self.request.traverse("foo/foo/bar/snuk/foo")
        notify(PubAfterTraversal(self.request))

    def test_allow_for_request(self):
        self.assertFalse(IPublishableThroughAcquisition.providedBy(self.request))
        # not allowed
        self.request.traverse("foo/foo/bar/snuk/foo")
        with self.assertRaises(NotFound):
            notify(PubAfterTraversal(self.request))
        # allowed
        alsoProvides(self.request, IPublishableThroughAcquisition)
        notify(PubAfterTraversal(self.request))
