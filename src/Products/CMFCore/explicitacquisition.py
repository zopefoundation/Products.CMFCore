from zExceptions import NotFound
from zope.component import adapter
from ZPublisher.interfaces import IPubAfterTraversal

from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import IPublishableThroughAcquisition
from Products.CMFCore.interfaces import IShouldAllowAcquiredItemPublication


@adapter(IPubAfterTraversal)
def after_traversal_hook(event):
    context = event.request["PARENTS"][0]
    if IShouldAllowAcquiredItemPublication(context, None) is False:
        raise NotFound()


@adapter(IContentish)
def content_allowed(context):
    if IPublishableThroughAcquisition.providedBy(context):
        return True
    parents = context.REQUEST["PARENTS"]
    parent_ids = [item.getId() for item in parents]
    parent_ids.reverse()
    return parent_ids == list(context.getPhysicalPath())
