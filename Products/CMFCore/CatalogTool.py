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
""" Basic portal catalog.
"""

from AccessControl.PermissionRole import rolesForPermissionOn
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import aq_base
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime
from Products.PluginIndexes.common import safe_callable
from Products.ZCatalog.ZCatalog import ZCatalog
from zope.component import adapts
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.interface import implements
from zope.interface import providedBy
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import ObjectSpecification
from zope.interface.declarations import ObjectSpecificationDescriptor

from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import IIndexableObject
from Products.CMFCore.interfaces import IIndexableObjectWrapper
from Products.CMFCore.interfaces import IWorkflowTool
from Products.CMFCore.permissions import AccessInactivePortalContent
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import _dtmldir
from Products.CMFCore.utils import _mergedLocalRoles
from Products.CMFCore.utils import registerToolInterface
from Products.CMFCore.utils import UniqueObject


class IndexableObjectSpecification(ObjectSpecificationDescriptor):

    # This class makes the wrapper transparent, adapter lookup is
    # carried out based on the interfaces of the wrapped object.

    def __get__(self, inst, cls=None):
        if inst is None:
            return getObjectSpecification(cls)
        else:
            provided = providedBy(inst._IndexableObjectWrapper__ob)
            cls = type(inst)
            return ObjectSpecification(provided, cls)


class IndexableObjectWrapper(object):

    implements(IIndexableObjectWrapper, IIndexableObject)
    adapts(IContentish, ICatalogTool)
    __providedBy__ = IndexableObjectSpecification()

    def __init__(self, ob, catalog):
        # look up the workflow variables for the object
        wtool = queryUtility(IWorkflowTool)
        if wtool is not None:
            self.__vars = wtool.getCatalogVariablesFor(ob)
        else:
            self.__vars = {}
        self.__ob = ob

    def __str__(self):
        try:
            # __str__ is used to get the data of File objects
            return self.__ob.__str__()
        except AttributeError:
            return object.__str__(self)

    def __getattr__(self, name):
        vars = self.__vars
        if name in vars:
            return vars[name]
        return getattr(self.__ob, name)

    def allowedRolesAndUsers(self):
        """
        Return a list of roles and users with View permission.
        Used by PortalCatalog to filter out items you're not allowed to see.
        """
        ob = self.__ob
        allowed = {}
        for r in rolesForPermissionOn(View, ob):
            allowed[r] = 1
        localroles = _mergedLocalRoles(ob)
        for user, roles in localroles.items():
            for role in roles:
                if role in allowed:
                    allowed['user:' + user] = 1
        if 'Owner' in allowed:
            del allowed['Owner']
        return list(allowed.keys())

    def cmf_uid(self):
        """
        Return the CMFUid UID of the object while making sure
        it is not accidentally acquired.
        """
        cmf_uid = getattr(aq_base(self.__ob), 'cmf_uid', '')
        if safe_callable(cmf_uid):
            return cmf_uid()
        return cmf_uid


class CatalogTool(UniqueObject, ZCatalog, ActionProviderBase):

    """ This is a ZCatalog that filters catalog queries.
    """

    implements(ICatalogTool)

    id = 'portal_catalog'
    meta_type = 'CMF Catalog'

    security = ClassSecurityInfo()

    manage_options = (
        ZCatalog.manage_options +
        ActionProviderBase.manage_options +
        ({'label': 'Overview', 'action': 'manage_overview'},))

    def __init__(self):
        ZCatalog.__init__(self, self.getId())

    #
    #   ZMI methods
    #
    security.declareProtected(ManagePortal, 'manage_overview')
    manage_overview = DTMLFile('explainCatalogTool', _dtmldir)

    #
    #   'portal_catalog' interface methods
    #

    def _listAllowedRolesAndUsers(self, user):
        effective_roles = user.getRoles()
        sm = getSecurityManager()
        if sm.calledByExecutable():
            eo = sm._context.stack[-1]
            proxy_roles = getattr(eo, '_proxy_roles', None)
            if proxy_roles:
                effective_roles = proxy_roles
        result = list(effective_roles)
        result.append('Anonymous')
        result.append('user:%s' % user.getId())
        return result

    def _convertQuery(self, kw):
        # Convert query to modern syntax
        for k in 'effective', 'expires':
            kusage = k + '_usage'
            if not kusage in kw:
                continue
            usage = kw[kusage]
            if not usage.startswith('range:'):
                raise ValueError("Incorrect usage %s" % repr(usage))
            kw[k] = {'query': kw[k], 'range': usage[6:]}
            del kw[kusage]

    # searchResults has inherited security assertions.
    def searchResults(self, REQUEST=None, **kw):
        """
            Calls ZCatalog.searchResults with extra arguments that
            limit the results to what the user is allowed to see.
        """
        user = getSecurityManager().getUser()
        kw['allowedRolesAndUsers'] = self._listAllowedRolesAndUsers(user)

        if not _checkPermission(AccessInactivePortalContent, self):
            now = DateTime()

            self._convertQuery(kw)

            # Intersect query restrictions with those implicit to the tool
            for k in 'effective', 'expires':
                if k in kw:
                    range = kw[k]['range'] or ''
                    query = kw[k]['query']
                    if not isinstance(query, (tuple, list)):
                        query = (query,)
                else:
                    range = ''
                    query = None
                if range.find('min') > -1:
                    lo = min(query)
                else:
                    lo = None
                if range.find('max') > -1:
                    hi = max(query)
                else:
                    hi = None
                if k == 'effective':
                    if hi is None or hi > now:
                        hi = now
                    if lo is not None and hi < lo:
                        return ()
                else: # 'expires':
                    if lo is None or lo < now:
                        lo = now
                    if hi is not None and hi < lo:
                        return ()
                # Rebuild a query
                if lo is None:
                    query = hi
                    range = 'max'
                elif hi is None:
                    query = lo
                    range = 'min'
                else:
                    query = (lo, hi)
                    range = 'min:max'
                kw[k] = {'query': query, 'range': range}

        return ZCatalog.searchResults(self, REQUEST, **kw)

    __call__ = searchResults

    security.declarePrivate('unrestrictedSearchResults')
    def unrestrictedSearchResults(self, REQUEST=None, **kw):
        """Calls ZCatalog.searchResults directly without restrictions.

        This method returns every also not yet effective and already expired
        objects regardless of the roles the caller has.

        CAUTION: Care must be taken not to open security holes by
        exposing the results of this method to non authorized callers!

        If you're in doubt if you should use this method or
        'searchResults' use the latter.
        """
        return ZCatalog.searchResults(self, REQUEST, **kw)

    def __url(self, ob):
        return '/'.join(ob.getPhysicalPath())

    manage_catalogFind = DTMLFile('catalogFind', _dtmldir)

    def catalog_object(self, obj, uid=None, idxs=None, update_metadata=1,
                       pghandler=None):
        # Wraps the object with workflow and accessibility
        # information just before cataloging.
        if IIndexableObject.providedBy(obj):
            w = obj
        else:
            w = queryMultiAdapter((obj, self), IIndexableObject)
            if w is None:
                # BBB
                w = IndexableObjectWrapper(obj, self)
        ZCatalog.catalog_object(self, w, uid, idxs, update_metadata,
                                pghandler)

    security.declarePrivate('indexObject')
    def indexObject(self, object):
        """Add to catalog.
        """
        url = self.__url(object)
        self.catalog_object(object, url)

    security.declarePrivate('unindexObject')
    def unindexObject(self, object):
        """Remove from catalog.
        """
        url = self.__url(object)
        self.uncatalog_object(url)

    security.declarePrivate('reindexObject')
    def reindexObject(self, object, idxs=[], update_metadata=1, uid=None):
        """Update catalog after object data has changed.

        The optional idxs argument is a list of specific indexes
        to update (all of them by default).

        The update_metadata flag controls whether the object's
        metadata record is updated as well.

        If a non-None uid is passed, it will be used as the catalog uid
        for the object instead of its physical path.
        """
        if uid is None:
            uid = self.__url(object)
        if idxs != []:
            # Filter out invalid indexes.
            valid_indexes = self._catalog.indexes.keys()
            idxs = [i for i in idxs if i in valid_indexes]
        self.catalog_object(object, uid, idxs, update_metadata)

InitializeClass(CatalogTool)
registerToolInterface('portal_catalog', ICatalogTool)
