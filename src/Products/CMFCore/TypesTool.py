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
""" Type registration tool.
"""

import logging
from warnings import warn

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_get
from App.special_dtml import DTMLFile
from OFS.ObjectManager import IFAwareObjectManager
from OFS.OrderedFolder import OrderedFolder
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.component import getUtility
from zope.component import queryUtility
from zope.component.interfaces import IFactory
from zope.container.contained import ObjectAddedEvent
from zope.container.contained import notifyContainerModified
from zope.event import notify
from zope.globalrequest import getRequest
from zope.i18nmessageid import Message
from zope.interface import implementer
from zope.lifecycleevent import ObjectCreatedEvent

from .ActionProviderBase import ActionProviderBase
from .exceptions import AccessControl_Unauthorized
from .exceptions import BadRequest
from .exceptions import zExceptions_Unauthorized
from .Expression import Expression
from .interfaces import IAction
from .interfaces import ITypeInformation
from .interfaces import ITypesTool
from .interfaces import IWorkflowTool
from .permissions import AccessContentsInformation
from .permissions import AddPortalContent
from .permissions import ManagePortal
from .permissions import View
from .utils import SimpleItemWithProperties
from .utils import UniqueObject
from .utils import _checkPermission
from .utils import _dtmldir
from .utils import _wwwdir
from .utils import registerToolInterface


logger = logging.getLogger('CMFCore.TypesTool')

_marker = []  # Create a new marker.


@implementer(IAction)
class TypeInformation(SimpleItemWithProperties, ActionProviderBase):

    """ Base class for information about a content type.
    """

    manage_options = (
        SimpleItemWithProperties.manage_options[:1] +
        ({'label': 'Aliases', 'action': 'manage_aliases'},) +
        ActionProviderBase.manage_options +
        SimpleItemWithProperties.manage_options[1:])

    security = ClassSecurityInfo()

    security.declareProtected(ManagePortal, 'manage_editProperties')
    security.declareProtected(ManagePortal, 'manage_changeProperties')
    security.declareProtected(ManagePortal, 'manage_propertiesForm')

    _basic_properties = (
        {'id': 'title', 'type': 'string', 'mode': 'w',
         'label': 'Title'},
        {'id': 'description', 'type': 'text', 'mode': 'w',
         'label': 'Description'},
        {'id': 'i18n_domain', 'type': 'string', 'mode': 'w',
         'label': 'I18n Domain'},
        {'id': 'icon_expr', 'type': 'string', 'mode': 'w',
         'label': 'Icon (Expression)'},
        {'id': 'content_meta_type', 'type': 'string', 'mode': 'w',
         'label': 'Product meta type'},
        )

    _advanced_properties = (
        {'id': 'add_view_expr', 'type': 'string', 'mode': 'w',
         'label': 'Add view URL (Expression)'},
        {'id': 'link_target', 'type': 'string', 'mode': 'w',
         'label': 'Add view link target'},
        {'id': 'immediate_view', 'type': 'string', 'mode': 'w',
         'label': 'Initial view name'},
        {'id': 'global_allow', 'type': 'boolean', 'mode': 'w',
         'label': 'Implicitly addable?'},
        {'id': 'filter_content_types', 'type': 'boolean', 'mode': 'w',
         'label': 'Filter content types?'},
        {'id': 'allowed_content_types', 'type': 'multiple selection',
         'mode': 'w', 'label': 'Allowed content types',
         'select_variable': 'listContentTypes'},
        {'id': 'allow_discussion', 'type': 'boolean', 'mode': 'w',
         'label': 'Allow Discussion?'})

    title = ''
    description = ''
    i18n_domain = ''
    content_meta_type = ''
    icon_expr = ''
    add_view_expr = ''
    immediate_view = ''
    filter_content_types = True
    allowed_content_types = ()
    allow_discussion = False
    global_allow = True
    link_target = ''

    def __init__(self, id, **kw):

        self.id = id
        self._actions = ()
        self._aliases = {}

        if not kw:
            return

        kw = kw.copy()  # Get a modifiable dict.

        if 'content_meta_type' not in kw and 'meta_type' in kw:
            kw['content_meta_type'] = kw['meta_type']

        if 'content_icon' in kw or 'icon' in kw:
            if 'icon' in kw:
                kw['content_icon'] = kw['icon']
                warn('TypeInformation got a deprecated argument icon.'
                     'Support for the icon argument will be removed in '
                     'CMF 2.4. Please use the icon_expr argument instead.',
                     DeprecationWarning, stacklevel=2)
            else:
                warn('TypeInformation got a deprecated argument content_icon.'
                     'Support for the content_icon argument will be removed '
                     'in CMF 2.4. Please use the icon_expr argument instead.',
                     DeprecationWarning, stacklevel=2)

            if 'icon_expr' not in kw:
                kw['icon_expr'] = ('string:${portal_url}/%s'
                                   % kw['content_icon'])

        self.manage_changeProperties(**kw)

        actions = kw.get('actions', ())
        for action in actions:
            self.addAction(
                id=action['id'],
                name=action['title'],
                action=action['action'],
                condition=action.get('condition'),
                permission=action.get('permissions', ()),
                category=action.get('category', 'object'),
                visible=action.get('visible', True),
                icon_expr=action.get('icon_expr', ''),
                link_target=action.get('link_target', ''))

        self.setMethodAliases(kw.get('aliases', {}))

    #
    #   ZMI methods
    #
    security.declareProtected(ManagePortal, 'manage_aliases')
    manage_aliases = PageTemplateFile('typeinfoAliases.zpt', _wwwdir)

    @security.protected(ManagePortal)
    def manage_setMethodAliases(self, REQUEST):
        """ Config method aliases.
        """
        form = REQUEST.form
        aliases = {}
        for k, v in form['aliases'].items():
            v = v.strip()
            if v:
                aliases[k] = v

        _dict = {}
        for k, v in form['methods'].items():
            if k in aliases:
                _dict[aliases[k]] = v
        self.setMethodAliases(_dict)
        REQUEST.RESPONSE.redirect('%s/manage_aliases' % self.absolute_url())

    #
    #   Accessors
    #
    @security.protected(View)
    def Title(self):
        """
            Return the "human readable" type name (note that it
            may not map exactly to the 'portal_type', e.g., for
            l10n/i18n or where a single content class is being
            used twice, under different names.
        """
        if self.title and self.i18n_domain:
            return Message(self.title, self.i18n_domain)
        else:
            return self.title or self.getId()

    @security.protected(View)
    def Description(self):
        """
            Textual description of the class of objects (intended
            for display in a "constructor list").
        """
        if self.description and self.i18n_domain:
            return Message(self.description, self.i18n_domain)
        else:
            return self.description

    @security.protected(View)
    def Metatype(self):
        """
            Returns the Zope 'meta_type' for this content object.
            May be used for building the list of portal content
            meta types.
        """
        return self.content_meta_type

    @security.protected(View)
    def getIcon(self):
        """ Returns the icon for this content object.
        """
        warn('getIcon() is deprecated and provides only limited backwards '
             'compatibility. It will be removed in CMF 2.4. Please use '
             'getIconExprObject() instead.',
             DeprecationWarning, stacklevel=2)
        if self.icon_expr.startswith('string:${portal_url}/'):
            return self.icon_expr[len('string:${portal_url}/'):]
        return self.icon_expr

    @security.private
    def getIconExprObject(self):
        """ Get the expression object representing the icon for this type.
        """
        return getattr(self, 'icon_expr_object', None)

    @security.public
    def allowType(self, contentType):
        """
            Can objects of 'contentType' be added to containers whose
            type object we are?
        """
        if not self.filter_content_types:
            ti = self.getTypeInfo(contentType)
            if ti is None or ti.globalAllow():
                return 1

        # If a type is enabled to filter and no content_types are allowed
        if not self.allowed_content_types:
            return 0

        if contentType in self.allowed_content_types:
            return 1

        return 0

    @security.public
    def getId(self):
        return self.id

    @security.public
    def allowDiscussion(self):
        """
            Can this type of object support discussion?
        """
        return self.allow_discussion

    @security.public
    def globalAllow(self):
        """
        Should this type be implicitly addable anywhere?
        """
        return self.global_allow

    @security.public
    def listActions(self, info=None, object=None):
        """ Return a sequence of the action info objects for this type.
        """
        return self._actions or ()

    @security.public
    def constructInstance(self, container, id, *args, **kw):
        """Build an instance of the type.

        Builds the instance in 'container', using 'id' as its id.
        Returns the object.
        """
        if not self.isConstructionAllowed(container):
            raise AccessControl_Unauthorized('Cannot create %s' % self.getId())

        return self._constructInstance(container, id, *args, **kw)

    @security.protected(ManagePortal)
    def getMethodAliases(self):
        """ Get method aliases dict.
        """
        aliases = self._aliases
        # for aliases created with CMF 1.5.0beta
        for key, method_id in aliases.items():
            if isinstance(method_id, tuple):
                aliases[key] = method_id[0]
                self._p_changed = True
        return aliases.copy()

    @security.protected(ManagePortal)
    def setMethodAliases(self, aliases):
        """ Set method aliases dict.
        """
        _dict = {}
        for k, v in aliases.items():
            v = v.strip()
            if v:
                _dict[k.strip()] = v
        if not getattr(self, '_aliases', None) == _dict:
            self._aliases = _dict
            return True
        else:
            return False

    @security.public
    def queryMethodID(self, alias, default=None, context=None):
        """ Query method ID by alias.
        """
        aliases = self._aliases
        method_id = aliases.get(alias, default)
        # for aliases created with CMF 1.5.0beta
        if isinstance(method_id, tuple):
            method_id = method_id[0]
        return method_id

    @security.private
    def _checkWorkflowAllowed(self, container):
        """ Check if a workflow veto object creation
        """
        wtool = queryUtility(IWorkflowTool)
        if wtool is None:
            return True

        type_id = self.getId()
        workflows = wtool.getWorkflowsFor(type_id)
        for workflow in workflows:
            # DCWorkflow workflows define an instance creation guard
            guard = getattr(workflow, 'allowCreate', None)

            if guard is None:
                continue

            if not guard(container, type_id):
                return False

        return True

    #
    #   'IAction' interface methods
    #
    @security.private
    def getInfoData(self):
        """ Get the data needed to create an ActionInfo.
        """
        lazy_keys = ['available', 'allowed']
        lazy_map = {}

        lazy_map['id'] = self.getId()
        lazy_map['category'] = 'folder/add'
        lazy_map['title'] = self.Title()
        lazy_map['description'] = self.Description()
        if self.add_view_expr:
            lazy_map['url'] = self.add_view_expr_object
            lazy_keys.append('url')
        else:
            lazy_map['url'] = ''
        if self.icon_expr:
            lazy_map['icon'] = self.icon_expr_object
            lazy_keys.append('icon')
        else:
            lazy_map['icon'] = ''
        lazy_map['link_target'] = self.link_target or None
        lazy_map['visible'] = True
        lazy_map['available'] = self._checkAvailable
        lazy_map['allowed'] = self._checkAllowed

        return (lazy_map, lazy_keys)

    def _setPropValue(self, id, value):
        self._wrapperCheck(value)
        if isinstance(value, list):
            value = tuple(value)
        setattr(self, id, value)
        if id.endswith('_expr'):
            attr = '%s_object' % id
            if value:
                setattr(self, attr, Expression(value))
            elif hasattr(self, attr):
                delattr(self, attr)

    def _checkAvailable(self, ec):
        """ Check if the action is available in the current context.
        """
        return ec.contexts['folder'].getTypeInfo().allowType(self.getId())

    def _checkAllowed(self, ec):
        """ Check if the action is allowed in the current context.
        """
        container = ec.contexts['folder']
        if not _checkPermission(AddPortalContent, container):
            return False
        return self.isConstructionAllowed(container)


InitializeClass(TypeInformation)


@implementer(ITypeInformation)
class FactoryTypeInformation(TypeInformation):

    """ Portal content factory.
    """

    security = ClassSecurityInfo()

    _properties = (TypeInformation._basic_properties +
                   ({'id': 'product', 'type': 'string', 'mode': 'w',
                     'label': 'Product name'},
                    {'id': 'factory', 'type': 'string', 'mode': 'w',
                     'label': 'Product factory'}) +
                   TypeInformation._advanced_properties)

    product = ''
    factory = ''

    #
    #   Agent methods
    #
    def _getFactoryMethod(self, container, check_security=1):
        if not self.product or not self.factory:
            raise ValueError('Product factory for %s was undefined' %
                             self.getId())
        p = container.manage_addProduct[self.product]
        m = getattr(p, self.factory, None)
        if m is None:
            raise ValueError('Product factory for %s was invalid' %
                             self.getId())
        if not check_security:
            return m
        if getSecurityManager().validate(p, p, self.factory, m):
            return m
        raise AccessControl_Unauthorized('Cannot create %s' % self.getId())

    def _queryFactoryMethod(self, container, default=None):

        if not self.product or not self.factory or container is None:
            return default

        # In case we aren't wrapped.
        dispatcher = getattr(container, 'manage_addProduct', None)

        if dispatcher is None:
            return default

        try:
            p = dispatcher[self.product]
        except AttributeError:
            logger.exception('_queryFactoryMethod raised an exception')
            return default

        m = getattr(p, self.factory, None)

        if m:
            try:
                # validate() can either raise Unauthorized or return 0 to
                # mean unauthorized.
                if getSecurityManager().validate(p, p, self.factory, m):
                    return m
            except zExceptions_Unauthorized:  # Catch *all* Unauths!
                pass

        return default

    @security.public
    def isConstructionAllowed(self, container):
        """
        a. Does the factory method exist?

        b. Is the factory method usable?

        c. Does the current user have the permission required in
        order to invoke the factory method?

        d. Do all workflows authorize the creation?
        """
        ti_check = False

        if self.product:
            # oldstyle factory
            m = self._queryFactoryMethod(container)
            ti_check = m is not None

        elif container is not None:
            # newstyle factory
            m = queryUtility(IFactory, self.factory, None)
            if m is not None:
                meta_types = container.all_meta_types
                if callable(meta_types):
                    meta_types = meta_types()
                for d in meta_types:
                    if d['name'] == self.content_meta_type:
                        sm = getSecurityManager()
                        ti_check = sm.checkPermission(d['permission'],
                                                      container)
                        break

        if not ti_check:
            return False
        else:
            return self._checkWorkflowAllowed(container)

    @security.private
    def _constructInstance(self, container, id, *args, **kw):
        """Build a bare instance of the appropriate type.

        Does not do any security checks.
        """
        id = str(id)

        if self.product:
            # oldstyle factory
            m = self._getFactoryMethod(container, check_security=0)

            if getattr(aq_base(m), 'isDocTemp', 0):
                kw['id'] = id
                request = aq_get(self, 'REQUEST', None)
                if request is None:
                    request = getRequest()
                newid = m(m.aq_parent, request, *args, **kw)
            else:
                newid = m(id, *args, **kw)
            # allow factory to munge ID
            newid = newid or id
            obj = container._getOb(newid)
            if hasattr(obj, '_setPortalTypeName'):
                obj._setPortalTypeName(self.getId())
            notify(ObjectCreatedEvent(obj))
            notify(ObjectAddedEvent(obj, container, newid))
            notifyContainerModified(container)

        else:
            # newstyle factory
            factory = getUtility(IFactory, self.factory)
            obj = factory(id, *args, **kw)
            if hasattr(obj, '_setPortalTypeName'):
                obj._setPortalTypeName(self.getId())
            notify(ObjectCreatedEvent(obj))
            rval = container._setObject(id, obj)
            newid = isinstance(rval, str) and rval or id
            obj = container._getOb(newid)

        return obj


InitializeClass(FactoryTypeInformation)


@implementer(ITypeInformation)
class ScriptableTypeInformation(TypeInformation):

    """ Invokes a script rather than a factory to create the content.
    """

    security = ClassSecurityInfo()

    _properties = (TypeInformation._basic_properties +
                   ({'id': 'permission', 'type': 'string', 'mode': 'w',
                     'label': 'Constructor permission'},
                    {'id': 'constructor_path', 'type': 'string', 'mode': 'w',
                     'label': 'Constructor path'}) +
                   TypeInformation._advanced_properties)

    permission = ''
    constructor_path = ''

    #
    #   Agent methods
    #
    @security.public
    def isConstructionAllowed(self, container):
        """
        Does the current user have the permission required in
        order to construct an instance?
        """
        permission = self.permission
        if permission and not _checkPermission(permission, container):
            return 0
        return self._checkWorkflowAllowed(container)

    @security.private
    def _constructInstance(self, container, id, *args, **kw):
        """Build a bare instance of the appropriate type.

        Does not do any security checks.
        """
        constructor = self.restrictedTraverse(self.constructor_path)

        # make sure ownership is explicit before switching the context
        if not hasattr(aq_base(constructor), '_owner'):
            constructor._owner = aq_get(constructor, '_owner')
        #   Rewrap to get into container's context.
        constructor = aq_base(constructor).__of__(container)

        id = str(id)
        obj = constructor(container, id, *args, **kw)
        if hasattr(obj, '_setPortalTypeName'):
            obj._setPortalTypeName(self.getId())
        notify(ObjectAddedEvent(obj, container, obj.getId()))
        notifyContainerModified(container)
        return obj


InitializeClass(ScriptableTypeInformation)


allowedTypes = [
    'Script (Python)',
    'Python Method',
    'DTML Method',
    'External Method',
   ]


@implementer(ITypesTool)
class TypesTool(UniqueObject, IFAwareObjectManager, OrderedFolder,
                ActionProviderBase):

    """ Provides a configurable registry of portal content types.
    """

    id = 'portal_types'
    meta_type = 'CMF Types Tool'
    _product_interfaces = (ITypeInformation,)

    security = ClassSecurityInfo()

    manage_options = (
        OrderedFolder.manage_options[:1] +
        ({'label': 'Aliases', 'action': 'manage_aliases'},) +
        ActionProviderBase.manage_options +
        ({'label': 'Overview', 'action': 'manage_overview'},) +
        OrderedFolder.manage_options[1:])

    #
    #   ZMI methods
    #
    security.declareProtected(ManagePortal, 'manage_overview')
    manage_overview = DTMLFile('explainTypesTool', _dtmldir)

    security.declareProtected(ManagePortal, 'manage_aliases')
    manage_aliases = PageTemplateFile('typesAliases.zpt', _wwwdir)

    #
    #   ObjectManager methods
    #
    def all_meta_types(self, interfaces=None):
        # this is a workaround and should be removed again if allowedTypes
        # have an interface we can use in _product_interfaces
        import Products
        all = TypesTool.inheritedAttribute('all_meta_types')(self)
        others = [mt for mt in Products.meta_types
                  if mt['name'] in allowedTypes]
        return tuple(all) + tuple(others)

    #
    #   other methods
    #
    @security.protected(ManagePortal)
    def manage_addTypeInformation(self, add_meta_type, id=None,
                                  typeinfo_name=None, RESPONSE=None):
        """Create a TypeInformation in self.
        """
        # BBB: typeinfo_name is ignored
        import Products
        if not id:
            raise BadRequest('An id is required.')
        for mt in Products.meta_types:
            if mt['name'] == add_meta_type:
                klass = mt['instance']
                break
        else:
            raise ValueError('Meta type %s is not a type class.'
                             % add_meta_type)
        id = str(id)
        ob = klass(id)
        self._setObject(id, ob)
        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_main' % self.absolute_url())

    @security.protected(ManagePortal)
    def manage_setTIMethodAliases(self, REQUEST):
        """ Config method aliases.
        """
        form = REQUEST.form
        aliases = {}
        for k, v in form['aliases'].items():
            v = v.strip()
            if v:
                aliases[k] = v

        for ti in self.listTypeInfo():
            _dict = {}
            for k, v in form[ti.getId()].items():
                if k in aliases:
                    _dict[aliases[k]] = v
            ti.setMethodAliases(_dict)
        REQUEST.RESPONSE.redirect('%s/manage_aliases' % self.absolute_url())

    @security.protected(AccessContentsInformation)
    def getTypeInfo(self, contentType):
        """
            Return an instance which implements the
            TypeInformation interface, corresponding to
            the specified 'contentType'.  If contentType is actually
            an object, rather than a string, attempt to look up
            the appropriate type info using its portal_type.
        """
        if not isinstance(contentType, str):
            if hasattr(aq_base(contentType), 'getPortalTypeName'):
                contentType = contentType.getPortalTypeName()
                if contentType is None:
                    return None
            else:
                return None
        ob = getattr(self, contentType, None)
        if ITypeInformation.providedBy(ob):
            return ob
        else:
            return None

    @security.protected(AccessContentsInformation)
    def listTypeInfo(self, container=None):
        """
            Return a sequence of instances which implement the
            TypeInformation interface, one for each content
            type registered in the portal.
        """
        rval = []
        for t in self.objectValues():
            # Filter out things that aren't TypeInformation and
            # types for which the user does not have adequate permission.
            if ITypeInformation.providedBy(t):
                rval.append(t)
        # Skip items with no ID:  old signal for "not ready"
        rval = [t for t in rval if t.getId()]
        # check we're allowed to access the type object
        if container is not None:
            rval = [t for t in rval if t.isConstructionAllowed(container)]
        return rval

    @security.protected(AccessContentsInformation)
    def listContentTypes(self, container=None, by_metatype=0):
        """ List type info IDs.

        Passing 'by_metatype' is deprecated (type information may not
        correspond 1:1 to an underlying meta_type). This argument will be
        removed when CMFCore/dtml/catalogFind.dtml doesn't need it anymore.
        """
        typenames = {}
        for t in self.listTypeInfo(container):

            if by_metatype:
                warn('TypeInformation.listContentTypes(by_metatype=1) is '
                     'deprecated.',
                     DeprecationWarning)
                name = t.Metatype()
            else:
                name = t.getId()

            if name:
                typenames[name] = None

        result = sorted(typenames)
        return result

    @security.public
    def constructContent(self, type_name, container, id, RESPONSE=None, *args,
                         **kw):
        """
            Build an instance of the appropriate content class in
            'container', using 'id'.
        """
        info = self.getTypeInfo(type_name)
        if info is None:
            raise ValueError('No such content type: %s' % type_name)

        ob = info.constructInstance(container, id, *args, **kw)

        if RESPONSE is not None:
            RESPONSE.redirect(f'{ob.absolute_url()}/{info.immediate_view}')

        return ob.getId()

    @security.private
    def listActions(self, info=None, object=None):
        """ List all the actions defined by a provider.
        """
        oldstyle_actions = self._actions or ()
        if oldstyle_actions:
            warn('Old-style actions are deprecated and will be removed in CMF '
                 '2.4. Use Action and Action Category objects instead.',
                 DeprecationWarning, stacklevel=2)
        actions = list(oldstyle_actions)

        if object is None and info is not None:
            object = info.object
        if object is not None:
            type_info = self.getTypeInfo(object)
            if type_info is not None:
                actions.extend(type_info.listActions(info, object))

        add_actions = [ti for ti in self.objectValues()
                       if IAction.providedBy(ti)]
        actions.extend(add_actions)

        return actions

    @security.protected(ManagePortal)
    def listMethodAliasKeys(self):
        """ List all defined method alias names.
        """
        _dict = {}
        for ti in self.listTypeInfo():
            aliases = ti.getMethodAliases()
            for k in aliases:
                _dict[k] = 1
        rval = sorted(_dict)
        return rval


InitializeClass(TypesTool)
registerToolInterface('portal_types', ITypesTool)
