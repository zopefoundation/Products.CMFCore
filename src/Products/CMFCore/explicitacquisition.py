import os

from zExceptions import NotFound
from zope.component import adapter
from ZPublisher.interfaces import IPubAfterTraversal

from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import IPublishableThroughAcquisition
from Products.CMFCore.interfaces import IShouldAllowAcquiredItemPublication


PTA_ENV_KEY = "PUBLISHING_EXPLICIT_ACQUISITION"
SKIP_PTA = os.environ.get(PTA_ENV_KEY, "true") == "false"


@adapter(IPubAfterTraversal)
def after_traversal_hook(event):
    if SKIP_PTA or IPublishableThroughAcquisition.providedBy(event.request):
        return
    context = event.request["PARENTS"][0]
    if IShouldAllowAcquiredItemPublication(context, None) is False:
        raise NotFound()


@adapter(IContentish)
def content_allowed(context):
    if IPublishableThroughAcquisition.providedBy(context):
        return True
    return context.aq_chain == context.aq_inner.aq_chain
