##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit test dummies.
"""

from Acquisition import Implicit
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from OFS.event import ObjectWillBeAddedEvent
from OFS.event import ObjectWillBeRemovedEvent
from OFS.interfaces import IObjectManager
from OFS.SimpleItem import Item
from zope.component.factory import Factory
from zope.container.contained import ObjectAddedEvent
from zope.container.contained import ObjectRemovedEvent
from zope.container.contained import notifyContainerModified
from zope.datetime import rfc1123_date
from zope.event import notify
from zope.interface import implementer

from ...ActionProviderBase import ActionProviderBase
from ...interfaces import IContentish
from ...interfaces import ISiteRoot
from ...interfaces import ITypeInformation
from ...PortalContent import PortalContent
from ..base.security import DummyUser
from ..base.security import OmnipotentUser


class DummyObject(Implicit):
    """
    A dummy callable object.
    Comes with getIconURL and restrictedTraverse
    methods.
    """
    def __init__(self, id='dummy', **kw):
        self._id = id
        self.__dict__.update(kw)

    def __str__(self):
        return self._id

    def __call__(self):
        return self._id

    def restrictedTraverse(self, path):
        if not path:
            return self

        parent = self
        path_elements = path.split('/')
        path_elements.reverse()
        while path_elements:
            path_element = path_elements.pop()
            parent = getattr(parent, path_element)

        return parent

    def icon(self):
        return f'{self._id} ICON'

    def getIconURL(self):
        return f'{self._id} ICON'

    def getId(self):
        return self._id


@implementer(ITypeInformation)
class DummyType(DummyObject):
    """ A Dummy Type object """

    def __init__(self, id='Dummy Content', title='Dummy Content', actions=()):
        """ To fake out some actions, pass in a sequence of tuples where the
        first element represents the ID or alias of the action and the
        second element is the path to the object to be invoked, such as
        a page template.
        """

        self.id = self._id = id
        self.title = title
        self._actions = {}

        self._setActions(actions)

    def _setActions(self, actions=()):
        for action_id, action_path in actions:
            self._actions[action_id] = action_path

    def Title(self):
        return self.title

    def allowType(self, contentType):
        return True

    def allowDiscussion(self):
        return False

    def queryMethodID(self, alias, default=None, context=None):
        return self._actions.get(alias, default)

    def isConstructionAllowed(self, container):
        return True


@implementer(IContentish)
class DummyContent(PortalContent, Item):
    """
    A Dummy piece of PortalContent
    """

    meta_type = 'Dummy'
    portal_type = 'Dummy Content'
    url = 'foo_url'
    after_add_called = before_delete_called = 0

    def __init__(self, id='dummy', *args, **kw):
        self.id = id
        self._args = args
        self._kw = {}
        self._kw.update(kw)

        self.reset()
        self.catalog = kw.get('catalog', 0)
        self.url = kw.get('url', None)
        self.view_id = kw.get('view_id', None)

    def manage_afterAdd(self, item, container):
        self.after_add_called = 1

    def manage_beforeDelete(self, item, container):
        self.before_delete_called = 1

    def absolute_url(self):
        return self.url

    def reset(self):
        self.after_add_called = self.before_delete_called = 0

    # Make sure normal Database export/import stuff doesn't trip us up.
    def _getCopy(self, container):
        return DummyContent(self.id, catalog=self.catalog)

    def _safe_get(self, attr):
        if self.catalog:
            return getattr(self, attr, '')
        else:
            return getattr(self, attr)

    def Title(self):
        return self.title

    def listCreators(self):
        return self._safe_get('creators')

    def Subject(self):
        return self._safe_get('subject')

    def Description(self):
        return self._safe_get('description')

    def created(self):
        return self._safe_get('created_date')

    def modified(self):
        return self._safe_get('modified_date')

    def Type(self):
        return 'Dummy Content Title'

    def __call__(self):
        if self.view_id is None:
            return DummyContent.inheritedAttribute('__call__')(self)
        else:
            # view_id control for testing
            template = getattr(self, self.view_id)
            if getattr(aq_base(template), 'isDocTemp', 0):
                return template(self, self.REQUEST, self.REQUEST['RESPONSE'])
            else:
                return template()


DummyFactory = Factory(DummyContent)


class DummyFactoryDispatcher:

    """
    Dummy Product Factory Dispatcher
    """
    def __init__(self, folder):
        self._folder = folder

    def getId(self):
        return 'DummyFactoryDispatcher'

    def addFoo(self, id, *args, **kw):
        if getattr(self._folder, '_prefix', None):
            id = f'{self._folder._prefix}_{id}'
        foo = DummyContent(id, *args, **kw)
        self._folder._setObject(id, foo, suppress_events=True)
        if getattr(self._folder, '_prefix', None):
            return id

    __roles__ = ('FooAdder',)
    __allow_access_to_unprotected_subobjects__ = {'addFoo': 1}


@implementer(IObjectManager)
class DummyFolder(DummyObject):

    """Dummy Container for testing.
    """

    def __init__(self, id='dummy', fake_product=0, prefix=''):
        self._prefix = prefix
        self._id = id

        if fake_product:
            self.manage_addProduct = {
                                   'FooProduct': DummyFactoryDispatcher(self)}

    def _setOb(self, id, object):
        setattr(self, id, object)

    def _delOb(self, id):
        delattr(self, id)

    def _getOb(self, id):
        return getattr(self, id)

    def _setObject(self, id, object, suppress_events=False):
        if not suppress_events:
            notify(ObjectWillBeAddedEvent(object, self, id))
        self._setOb(id, object)
        object = self._getOb(id)
        if hasattr(aq_base(object), 'manage_afterAdd'):
            object.manage_afterAdd(object, self)
        if not suppress_events:
            notify(ObjectAddedEvent(object, self, id))
            notifyContainerModified(self)
        return object

    def _delObject(self, id):
        object = self._getOb(id)
        notify(ObjectWillBeRemovedEvent(object, self, id))
        if hasattr(aq_base(object), 'manage_beforeDelete'):
            object.manage_beforeDelete(object, self)
        self._delOb(id)
        notify(ObjectRemovedEvent(object, self, id))
        notifyContainerModified(self)

    def getPhysicalPath(self):
        p = aq_parent(aq_inner(self))
        path = (self._id,)
        if p is not None:
            path = p.getPhysicalPath() + path
        return path

    def getId(self):
        return self._id

    def reindexObjectSecurity(self):
        pass

    def contentIds(self):
        return ('user_bar',)

    def all_meta_types(self):
        return ({'name': 'Dummy', 'permission': 'addFoo'},)

    def getTypeInfo(self):
        return self.portal_types.getTypeInfo(self)  # Can return None.


@implementer(ISiteRoot)
class DummySite(DummyFolder):
    """ A dummy portal folder.
    """

    _domain = 'http://www.foobar.com'
    _path = 'bar'

    def absolute_url(self, relative=0):
        return '/'.join((self._domain, self._path, self._id))

    def getPhysicalPath(self):
        return ('', self._path, self._id)

    def getPhysicalRoot(self):
        return self

    def unrestrictedTraverse(self, path, default=None, restricted=0):
        if path == ['acl_users']:
            return self.acl_users
        else:
            obj = self
            for id in path[3:]:
                obj = getattr(obj, id)
            return obj

    def userdefined_roles(self):
        return ('Member', 'Reviewer')

    def getProperty(self, id, default=None):
        return getattr(self, id, default)


class DummyUserFolder(Implicit):
    """ A dummy User Folder with 2 dummy Users.
    """

    id = 'acl_users'

    def __init__(self):
        setattr(self, 'user_foo', DummyUser(id='user_foo'))
        setattr(self, 'user_bar', DummyUser(id='user_bar'))
        setattr(self, 'all_powerful_Oz', OmnipotentUser())

    def getUsers(self):
        pass

    def getUser(self, name):
        return getattr(self, name, None)

    def getUserById(self, id, default=None):
        return self.getUser(id)

    def userFolderDelUsers(self, names):
        for user_id in names:
            delattr(self, user_id)


class DummyTool(Implicit, ActionProviderBase):
    """
    This is a Dummy Tool that behaves as a
    a MemberShipTool, a URLTool and an
    Action Provider
    """

    def __init__(self, anon=1):
        self.anon = anon

    # IMembershipTool
    def getAuthenticatedMember(self):
        return DummyUser()

    def isAnonymousUser(self):
        return self.anon

    def checkPermission(self, permissionName, object, subobjectName=None):
        return True

    # ITypesTool
    _type_id = 'Dummy Content'
    _type_actions = (('', 'dummy_view'),
                     ('view', 'dummy_view'),
                     ('(Default)', 'dummy_view'))

    def getTypeInfo(self, contentType):
        return DummyType(self._type_id, title=self._type_id,
                         actions=self._type_actions)

    def listTypeInfo(self, container=None):
        return (DummyType(self._type_id, title=self._type_id,
                          actions=self._type_actions),)

    def listContentTypes(self, container=None, by_metatype=0):
        return (self._type_id,)

    # IURLTool
    def __call__(self, relative=0):
        return self.getPortalObject().absolute_url()

    def getPortalObject(self):
        return aq_parent(aq_inner(self))

    getPortalPath = __call__

    # IWorkflowTool
    test_notified = None

    def notifyCreated(self, ob):
        self.test_notified = ob

    def getCatalogVariablesFor(self, obj):
        return {}


class DummyCachingManager:

    def getHTTPCachingHeaders(self, content, view_name, keywords, time=None):
        return (
             ('foo', 'Foo'), ('bar', 'Bar'),
             ('test_path', '/'.join(content.getPhysicalPath())),
            )

    def getModTimeAndETag(self, content, view_method, keywords, time=None):
        return (None, None, False)

    def getPhysicalPath(self):
        return ('baz',)


FAKE_ETAG = None  # '--FAKE ETAG--'


class DummyCachingManagerWithPolicy(DummyCachingManager):

    # dummy fixture implementing a single policy:
    #  - always set the last-modified date if available
    #  - calculate the date using the modified method on content

    def getHTTPCachingHeaders(self, content, view_name, keywords, time=None):
        # if the object has a modified method, add it as last-modified
        if hasattr(content, 'modified'):
            headers = (('Last-modified', rfc1123_date(content.modified())),)
        return headers

    def getModTimeAndETag(self, content, view_method, keywords, time=None):
        modified_date = None
        if hasattr(content, 'modified'):
            modified_date = content.modified()
        set_last_modified = (modified_date is not None)
        return (modified_date, FAKE_ETAG, set_last_modified)
