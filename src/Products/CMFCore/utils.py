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
""" Utility functions.
"""

import base64
import re
import sys
from _thread import allocate_lock
from copy import deepcopy
from os import path as os_path
from os.path import abspath
from warnings import warn

import pkg_resources

from AccessControl.class_init import InitializeClass
from AccessControl.Permission import Permission
from AccessControl.PermissionRole import rolesForPermissionOn
from AccessControl.rolemanager import gather_permissions
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityInfo import ModuleSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import Implicit
from Acquisition import aq_get
from Acquisition import aq_parent
from Acquisition.interfaces import IAcquirer
from App.Common import package_home
from App.ImageFile import ImageFile
from App.special_dtml import HTMLFile
from DateTime.DateTime import DateTime
from DateTime.interfaces import DateTimeError
from ExtensionClass import Base
from OFS.misc_ import Misc_ as MiscImage
from OFS.misc_ import misc_ as misc_images
from OFS.ObjectManager import UNIQUE
from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import SimpleItem
from zope.component import getUtility
from zope.component import queryUtility
from zope.datetime import rfc1123_date
from zope.dottedname.resolve import resolve as resolve_dotted_name
from zope.i18nmessageid import MessageFactory
from zope.interface.interfaces import ComponentLookupError

import Products

from .exceptions import AccessControl_Unauthorized
from .exceptions import NotFound
from .interfaces import ICachingPolicyManager


HAS_ZSERVER = True
try:
    dist = pkg_resources.get_distribution('ZServer')
except pkg_resources.DistributionNotFound:
    HAS_ZSERVER = False

SUBTEMPLATE = '__SUBTEMPLATE__'
ProductsPath = [abspath(ppath) for ppath in Products.__path__]
security = ModuleSecurityInfo('Products.CMFCore.utils')

_globals = globals()
_dtmldir = os_path.join(package_home(globals()), 'dtml')
_wwwdir = os_path.join(package_home(globals()), 'www')

#
#   Simple utility functions, callable from restricted code.
#
_marker = []  # Create a new marker object.

_tool_interface_registry = {}


@security.private
def registerToolInterface(tool_id, tool_interface):
    """ Register a tool ID for an interface

    This method can go away when getToolByName is going away
    """
    global _tool_interface_registry
    _tool_interface_registry[tool_id] = tool_interface


@security.private
def getToolInterface(tool_id):
    """ Get the interface registered for a tool ID
    """
    global _tool_interface_registry
    return _tool_interface_registry.get(tool_id, None)


@security.public
def getToolByName(obj, name, default=_marker):

    """ Get the tool, 'toolname', by acquiring it.

    o Application code should use this method, rather than simply
      acquiring the tool by name, to ease forward migration (e.g.,
      to Zope3).
    """
    tool_interface = _tool_interface_registry.get(name)

    if tool_interface is not None:
        try:
            utility = getUtility(tool_interface)
            # Site managers, except for five.localsitemanager, return unwrapped
            # utilities. If the result is something which is
            # acquisition-unaware but unwrapped we wrap it on the context.
            if IAcquirer.providedBy(obj) and \
                    aq_parent(utility) is None and \
                    IAcquirer.providedBy(utility):
                utility = utility.__of__(obj)
            return utility
        except ComponentLookupError:
            # behave in backwards-compatible way
            # fall through to old implementation
            pass

    try:
        tool = aq_get(obj, name, default, 1)
    except AttributeError:
        if default is _marker:
            raise
        return default
    else:
        if tool is _marker:
            raise AttributeError(name)
        return tool


@security.public
def getUtilityByInterfaceName(dotted_name, default=_marker):
    """ Get a tool by its fully-qualified dotted interface path

    This method replaces getToolByName for use in untrusted code.
    Trusted code should use zope.component.getUtility instead.
    """
    try:
        iface = resolve_dotted_name(dotted_name)
    except ImportError:
        if default is _marker:
            raise ComponentLookupError(dotted_name)
        return default

    try:
        return getUtility(iface)
    except ComponentLookupError:
        if default is _marker:
            raise
        return default


@security.public
def cookString(text):

    """ Make a Zope-friendly ID from 'text'.

    o Remove any spaces

    o Lowercase the ID.
    """
    rgx = re.compile(r'(^_|[^a-zA-Z0-9-_~\,\.])')
    cooked = re.sub(rgx, '', text).lower()
    return cooked


@security.public
def tuplize(valueName, value):

    """ Make a tuple from 'value'.

    o Use 'valueName' to generate appropriate error messages.
    """
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, str):
        return tuple(value.split())
    raise ValueError('%s of unsupported type' % valueName)


#
#   Security utilities, callable only from unrestricted code.
#
# deprecated alias
@security.private
def _getAuthenticatedUser(self):
    return getSecurityManager().getUser()


@security.private
def _checkPermission(permission, obj):
    if not isinstance(permission, str):
        permission = permission.decode()
    return getSecurityManager().checkPermission(permission, obj)


# If Zope ever provides a call to getRolesInContext() through
# the SecurityManager API, the method below needs to be updated.
@security.private
def _limitGrantedRoles(roles, context, special_roles=()):
    # Only allow a user to grant roles already possessed by that user,
    # with the exception that all special_roles can also be granted.
    user = getSecurityManager().getUser()
    if user is None:
        user_roles = ()
    else:
        user_roles = user.getRolesInContext(context)
    if 'Manager' in user_roles:
        # Assume all other roles are allowed.
        return
    for role in roles:
        if role not in special_roles and role not in user_roles:
            raise AccessControl_Unauthorized('Too many roles specified.')


@security.private
def _mergedLocalRoles(object):
    """Returns a merging of object and its ancestors'
    __ac_local_roles__."""
    # Modified from AccessControl.User.getRolesInContext().
    merged = {}
    object = getattr(object, 'aq_inner', object)
    while 1:
        if hasattr(object, '__ac_local_roles__'):
            dict = object.__ac_local_roles__ or {}
            if callable(dict):
                dict = dict()
            for k, v in dict.items():
                if k in merged:
                    merged[k] = merged[k] + v
                else:
                    merged[k] = v
        if hasattr(object, 'aq_parent'):
            object = object.aq_parent
            object = getattr(object, 'aq_inner', object)
            continue
        if hasattr(object, '__self__'):
            object = object.__self__
            object = getattr(object, 'aq_inner', object)
            continue
        break

    return deepcopy(merged)


@security.private
def _ac_inherited_permissions(ob, all=0):
    # Get all permissions not defined in ourself that are inherited
    # This will be a sequence of tuples with a name as the first item and
    # an empty tuple as the second.
    d = {}
    perms = getattr(ob, '__ac_permissions__', ())
    for p in perms:
        d[p[0]] = None
    r = gather_permissions(ob.__class__, [], d)
    if all:
        if hasattr(ob, '_subobject_permissions'):
            for p in ob._subobject_permissions():
                pname = p[0]
                if pname not in d:
                    d[pname] = 1
                    r.append(p)
        r = list(perms) + r
    return r


@security.private
def _modifyPermissionMappings(ob, map):
    """
    Modifies multiple role to permission mappings.
    """
    # This mimics what AccessControl/Role.py does.
    # Needless to say, it's crude. :-(
    something_changed = 0
    perm_info = _ac_inherited_permissions(ob, 1)
    for name, settings in map.items():
        cur_roles = rolesForPermissionOn(name, ob)
        if isinstance(cur_roles, str):
            cur_roles = [cur_roles]
        else:
            cur_roles = list(cur_roles)
        changed = 0
        for (role, allow) in settings.items():
            if not allow:
                if role in cur_roles:
                    changed = 1
                    cur_roles.remove(role)
            else:
                if role not in cur_roles:
                    changed = 1
                    cur_roles.append(role)
        if changed:
            data = ()  # The list of methods using this permission.
            for perm in perm_info:
                n, d = perm[:2]
                if n == name:
                    data = d
                    break
            p = Permission(name, data, ob)
            p.setRoles(tuple(cur_roles))
            something_changed = 1
    return something_changed


class FakeExecutableObject:

    """Fake ExecutableObject used to set proxy roles in trusted code.
    """

    def __init__(self, proxy_roles):
        self._proxy_roles = tuple(proxy_roles)

    def getOwner(self):
        return None

    getWrappedOwner = getOwner


# Parse a string of etags from an If-None-Match header
# Code follows ZPublisher.HTTPRequest.parse_cookie
parse_etags_lock = allocate_lock()


def parse_etags(text,
                result=None,
                # quoted etags (assumed separated by whitespace + a comma)
                etagre_quote=re.compile(r'(\s*\"([^\"]*)\"\s*,{0,1})'),
                # non-quoted etags (assumed separated by whitespace + a comma)
                etagre_noquote=re.compile(r'(\s*([^,]*)\s*,{0,1})'),
                acquire=parse_etags_lock.acquire,
                release=parse_etags_lock.release):

    if result is None:
        result = []
    if not len(text):
        return result

    acquire()
    try:
        m = etagre_quote.match(text)
        if m:
            # Match quoted etag (spec-observing client)
            tl = len(m.group(1))
            value = m.group(2)
        else:
            # Match non-quoted etag (lazy client)
            m = etagre_noquote.match(text)
            if m:
                tl = len(m.group(1))
                value = m.group(2)
            else:
                return result
    finally:
        release()

    if value:
        result.append(value)
    return parse_etags(*(text[tl:], result))


def _checkConditionalGET(obj, extra_context):
    """A conditional GET is done using one or both of the request
       headers:

       If-Modified-Since: Date
       If-None-Match: list ETags (comma delimited, sometimes quoted)

       If both conditions are present, both must be satisfied.

       This method checks the caching policy manager to see if
       a content object's Last-modified date and ETag satisfy
       the conditional GET headers.

       Returns the tuple (last_modified, etag) if the conditional
       GET requirements are met and None if not.

       It is possible for one of the tuple elements to be None.
       For example, if there is no If-None-Match header and
       the caching policy does not specify an ETag, we will
       just return (last_modified, None).
       """

    REQUEST = getattr(obj, 'REQUEST', None)
    if REQUEST is None:
        return False

    # check whether we need to suppress subtemplates
    call_count = getattr(REQUEST, SUBTEMPLATE, 0)
    setattr(REQUEST, SUBTEMPLATE, call_count + 1)
    if call_count != 0:
        return False

    if_modified_since = REQUEST.getHeader('If-Modified-Since', None)
    if_none_match = REQUEST.getHeader('If-None-Match', None)

    if if_modified_since is None and if_none_match is None:
        # not a conditional GET
        return False

    manager = queryUtility(ICachingPolicyManager)
    if manager is None:
        return False

    ret = manager.getModTimeAndETag(aq_parent(obj), obj.getId(), extra_context)
    if ret is None:
        # no appropriate policy or 304s not enabled
        return False

    (content_mod_time, content_etag, set_last_modified_header) = ret
    if content_mod_time:
        mod_time_secs = int(content_mod_time.timeTime())
    else:
        mod_time_secs = None

    if if_modified_since:
        # from CMFCore/FSFile.py:
        if_modified_since = if_modified_since.split(';')[0]
        # Some proxies seem to send invalid date strings for this
        # header. If the date string is not valid, we ignore it
        # rather than raise an error to be generally consistent
        # with common servers such as Apache (which can usually
        # understand the screwy date string as a lucky side effect
        # of the way they parse it).
        try:
            if_modified_since = int(DateTime(if_modified_since).timeTime())
        except Exception:
            if_modified_since = None

    client_etags = None
    if if_none_match:
        client_etags = parse_etags(if_none_match)

    if not if_modified_since and not client_etags:
        # not a conditional GET, or headers are messed up
        return False

    if if_modified_since:
        if not content_mod_time or \
           mod_time_secs < 0 or \
           mod_time_secs > if_modified_since:
            return False

    if client_etags:
        if not content_etag or \
           (content_etag not in client_etags and '*' not in client_etags):
            return False
    else:
        # If we generate an ETag, don't validate the conditional GET unless
        # the client supplies an ETag
        # This may be more conservative than the spec requires, but we are
        # already _way_ more conservative.
        if content_etag:
            return False

    response = REQUEST.RESPONSE
    if content_mod_time and set_last_modified_header:
        response.setHeader('Last-modified', str(content_mod_time))
    if content_etag:
        response.setHeader('ETag', content_etag, literal=1)
    response.setStatus(304)
    delattr(REQUEST, SUBTEMPLATE)

    return True


@security.private
def _setCacheHeaders(obj, extra_context):
    """Set cache headers according to cache policy manager for the obj."""
    REQUEST = getattr(obj, 'REQUEST', None)

    if REQUEST is not None:
        call_count = getattr(REQUEST, SUBTEMPLATE, 1) - 1
        setattr(REQUEST, SUBTEMPLATE, call_count)
        if call_count != 0:
            return

        # cleanup
        delattr(REQUEST, SUBTEMPLATE)

        content = aq_parent(obj)
        manager = queryUtility(ICachingPolicyManager)
        if manager is None:
            return

        view_name = obj.getId()
        headers = manager.getHTTPCachingHeaders(
                          content, view_name, extra_context)
        RESPONSE = REQUEST['RESPONSE']
        for key, value in headers:
            if key == 'ETag':
                RESPONSE.setHeader(key, value, literal=1)
            else:
                RESPONSE.setHeader(key, value)
        if headers:
            RESPONSE.setHeader('X-Cache-Headers-Set-By',
                               'CachingPolicyManager: %s' %
                               '/'.join(manager.getPhysicalPath()))


class _ViewEmulator(Implicit):
    """Auxiliary class used to adapt FSFile and FSImage
    for caching_policy_manager
    """
    def __init__(self, view_name=''):
        self._view_name = view_name

    def getId(self):
        return self._view_name


#
#   Base classes for tools
#
class ImmutableId(Base):

    """ Base class for objects which cannot be renamed.
    """

    def _setId(self, id):
        """ Never allow renaming!
        """
        if id != self.getId():
            raise ValueError('Changing the id of this object is forbidden: %s'
                             % self.getId())


class UniqueObject(ImmutableId):

    """ Base class for objects which cannot be "overridden" / shadowed.
    """
    zmi_icon = 'fas fa-wrench'

    def _getUNIQUE(self):
        return UNIQUE

    __replaceable__ = property(_getUNIQUE)


class SimpleItemWithProperties(PropertyManager, SimpleItem):
    """
    A common base class for objects with configurable
    properties in a fixed schema.
    """
    manage_options = (
        PropertyManager.manage_options +
        SimpleItem.manage_options)

    security = ClassSecurityInfo()
    security.declarePrivate('manage_addProperty')  # NOQA: flake8: D001
    security.declarePrivate('manage_delProperties')  # NOQA: flake8: D001
    security.declarePrivate('manage_changePropertyTypes')  # NOQA: flake8: D001

    def manage_propertiesForm(self, REQUEST, *args, **kw):
        """ An override that makes the schema fixed.
        """
        my_kw = kw.copy()
        my_kw['property_extensible_schema__'] = 0
        form = PropertyManager.manage_propertiesForm.__of__(self)
        return form(self, REQUEST, *args, **my_kw)


InitializeClass(SimpleItemWithProperties)


#
#   "Omnibus" factory framework for tools.
#
class ToolInit:

    """ Utility class for generating the factories for several tools.
    """
    __name__ = 'toolinit'

    security = ClassSecurityInfo()
    security.declareObjectPrivate()     # equivalent of __roles__ = ()

    def __init__(self, meta_type, tools, product_name=None, icon=None):
        self.meta_type = meta_type
        self.tools = tools
        if product_name is not None:
            warn('The product_name parameter of ToolInit is now ignored',
                 DeprecationWarning, stacklevel=2)
        self.icon = icon

    def initialize(self, context):
        # Add only one meta type to the folder add list.
        productObject = context._ProductContext__prod
        self.product_name = productObject.id
        context.registerClass(
            meta_type=self.meta_type,
            # This is a little sneaky: we add self to the
            # FactoryDispatcher under the name "toolinit".
            # manage_addTool() can then grab it.
            constructors=(manage_addToolForm, manage_addTool, self),
            icon=self.icon)

        if self.icon:
            icon = os_path.split(self.icon)[1]
        else:
            icon = None
        for tool in self.tools:
            tool.__factory_meta_type__ = self.meta_type
            tool.icon = f'misc_/{self.product_name}/{icon}'


InitializeClass(ToolInit)

addInstanceForm = HTMLFile('dtml/addInstance', globals())


def manage_addToolForm(self, REQUEST):

    """ Show the add tool form.
    """
    # self is a FactoryDispatcher.
    toolinit = self.toolinit
    tl = []
    for tool in toolinit.tools:
        tl.append(tool.meta_type)
    return addInstanceForm(addInstanceForm, self, REQUEST,
                           factory_action='manage_addTool',
                           factory_meta_type=toolinit.meta_type,
                           factory_product_name=toolinit.product_name,
                           factory_icon=toolinit.icon,
                           factory_types_list=tl,
                           factory_need_id=0)


def manage_addTool(self, type, REQUEST=None):

    """ Add the tool specified by name.
    """
    # self is a FactoryDispatcher.
    toolinit = self.toolinit
    obj = None
    for tool in toolinit.tools:
        if tool.meta_type == type:
            obj = tool()
            break
    if obj is None:
        raise NotFound(type)
    self._setObject(obj.getId(), obj)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)


#
#   Now, do the same for creating content factories.
#
class ContentInit:

    """ Utility class for generating factories for several content types.
    """
    __name__ = 'contentinit'

    security = ClassSecurityInfo()
    security.declareObjectPrivate()

    def __init__(self, meta_type, content_types, permission=None,
                 extra_constructors=(), fti=(), visibility='Global'):
        # BBB: fti argument is ignored
        self.meta_type = meta_type
        self.content_types = content_types
        self.permission = permission
        self.extra_constructors = extra_constructors
        self.visibility = visibility

    def initialize(self, context):
        # Add only one meta type to the folder add list.
        context.registerClass(
            meta_type=self.meta_type,
            # This is a little sneaky: we add self to the
            # FactoryDispatcher under the name "contentinit".
            # manage_addContentType() can then grab it.
            constructors=(manage_addContentForm, manage_addContent,
                          self) + self.extra_constructors,
            permission=self.permission,
            visibility=self.visibility)

        for ct in self.content_types:
            ct.__factory_meta_type__ = self.meta_type


InitializeClass(ContentInit)


def manage_addContentForm(self, REQUEST):
    """ Show the add content type form.
    """
    # self is a FactoryDispatcher.
    ci = self.contentinit
    tl = []
    for t in ci.content_types:
        tl.append(t.meta_type)
    return addInstanceForm(addInstanceForm, self, REQUEST,
                           factory_action='manage_addContent',
                           factory_meta_type=ci.meta_type,
                           factory_icon=None,
                           factory_types_list=tl,
                           factory_need_id=1)


def manage_addContent(self, id, type, REQUEST=None):
    """ Add the content type specified by name.
    """
    # self is a FactoryDispatcher.
    contentinit = self.contentinit
    obj = None
    for content_type in contentinit.content_types:
        if content_type.meta_type == type:
            obj = content_type(id)
            break
    if obj is None:
        raise NotFound(type)
    self._setObject(id, obj)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)


def registerIcon(klass, iconspec, _prefix=None):

    """ Make an icon available for a given class.

    o 'klass' is the class being decorated.

    o 'iconspec' is the path within the product where the icon lives.
    """
    modname = klass.__module__
    pid = modname.split('.')[1]
    name = os_path.split(iconspec)[1]
    klass.icon = f'misc_/{pid}/{name}'
    icon = ImageFile(iconspec, _prefix)
    icon.__roles__ = None
    if not hasattr(misc_images, pid):
        setattr(misc_images, pid, MiscImage(pid, {}))
    getattr(misc_images, pid)[name] = icon


#
#   Metadata Keyword splitter utilities
#
KEYSPLITRE = re.compile(r'[,;]')


@security.public
def keywordsplitter(headers, names=('Subject', 'Keywords'),
                    splitter=KEYSPLITRE.split):
    """ Split keywords out of headers, keyed on names.  Returns list.
    """
    out = []
    for head in names:
        keylist = splitter(headers.get(head, ''))
        keylist = [x.strip() for x in keylist]
        out.extend([key for key in keylist if key])
    return out


#
#   Metadata Contributors splitter utilities
#
CONTRIBSPLITRE = re.compile(r';')


@security.public
def contributorsplitter(headers, names=('Contributors',),
                        splitter=CONTRIBSPLITRE.split):
    """ Split contributors out of headers, keyed on names.  Returns list.
    """
    return keywordsplitter(headers, names, splitter)


#
#   Directory-handling utilities
#
@security.public
def normalize(p):
    # the first .replace is needed to help normpath when dealing with Windows
    # paths under *nix, the second to normalize to '/'
    return os_path.normpath(p.replace('\\', '/')).replace('\\', '/')


@security.private
def getContainingPackage(module):
    parts = module.split('.')
    while parts:
        name = '.'.join(parts)
        mod = sys.modules[name]
        if '__init__' in mod.__file__:
            return name
        parts = parts[:-1]

    raise ValueError('Unable to find package for module %s' % module)


@security.private
def getPackageLocation(module):
    """ Return the filesystem location of a module.

    This is a simple wrapper around the global package_home method which
    tricks it into working with just a module name.
    """
    package = getContainingPackage(module)
    return package_home({'__name__': package})


@security.private
def getPackageName(globals_):
    module = globals_['__name__']
    return getContainingPackage(module)


def _OldCacheHeaders(obj):
    # Old-style checking of modified headers

    REQUEST = getattr(obj, 'REQUEST', None)
    if REQUEST is None:
        return False

    RESPONSE = REQUEST.RESPONSE
    header = REQUEST.getHeader('If-Modified-Since', None)
    last_mod = int(obj.modified().timeTime())

    if header is not None:
        header = header.split(';')[0]
        # Some proxies seem to send invalid date strings for this
        # header. If the date string is not valid, we ignore it
        # rather than raise an error to be generally consistent
        # with common servers such as Apache (which can usually
        # understand the screwy date string as a lucky side effect
        # of the way they parse it).
        try:
            mod_since = DateTime(header)
            mod_since = int(mod_since.timeTime())
        except (TypeError, DateTimeError):
            mod_since = None

        if mod_since is not None:
            if last_mod > 0 and last_mod <= mod_since:
                RESPONSE.setStatus(304)
                return True

    # Last-Modified will get stomped on by a cache policy if there is
    # one set....
    RESPONSE.setHeader('Last-Modified', rfc1123_date(last_mod))


def _FSCacheHeaders(obj):
    # Old-style setting of modified headers for FS-based objects

    REQUEST = getattr(obj, 'REQUEST', None)
    if REQUEST is None:
        return False

    RESPONSE = REQUEST.RESPONSE
    header = REQUEST.getHeader('If-Modified-Since', None)
    # Reduce resolution to one second, else if-modified-since would
    # always be older if system resolution is higher
    last_mod = int(obj._file_mod_time)

    if header is not None:
        header = header.split(';')[0]
        # Some proxies seem to send invalid date strings for this
        # header. If the date string is not valid, we ignore it
        # rather than raise an error to be generally consistent
        # with common servers such as Apache (which can usually
        # understand the screwy date string as a lucky side effect
        # of the way they parse it).
        try:
            mod_since = DateTime(header)
            mod_since = int(mod_since.timeTime())
        except (TypeError, DateTimeError):
            mod_since = None

        if mod_since is not None:
            if last_mod > 0 and last_mod <= mod_since:
                RESPONSE.setStatus(304)
                return True

    # Last-Modified will get stomped on by a cache policy if there is
    # one set....
    RESPONSE.setHeader('Last-Modified', rfc1123_date(last_mod))


class SimpleRecord:
    """ record-like class """

    def __init__(self, **kw):
        self.__dict__.update(kw)


def base64_encode(text):
    return base64.encodebytes(text).rstrip()


def base64_decode(text):
    return base64.decodebytes(text)


security.declarePublic('Message')  # NOQA: flake8: D001
Message = MessageFactory('cmf_default')
