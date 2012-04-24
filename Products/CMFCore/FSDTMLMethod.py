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
""" Customizable DTML methods that come from the filesystem.
"""

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from App.special_dtml import HTML
from DocumentTemplate.security import RestrictedDTML
from OFS.DTMLMethod import DTMLMethod, decapitate, guess_content_type
from OFS.role import RoleManager

from Products.CMFCore.DirectoryView import registerFileExtension
from Products.CMFCore.DirectoryView import registerMetaType
from Products.CMFCore.FSObject import FSObject
from Products.CMFCore.permissions import FTPAccess
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ViewManagementScreens
from Products.CMFCore.utils import _checkConditionalGET
from Products.CMFCore.utils import _dtmldir
from Products.CMFCore.utils import _setCacheHeaders

_marker = object()


class FSDTMLMethod(RestrictedDTML, RoleManager, FSObject, HTML):

    """FSDTMLMethods act like DTML methods but are not directly
    modifiable from the management interface.
    """

    meta_type = 'Filesystem DTML Method'
    _owner = None
    _proxy_roles = ()
    _cache_namespace_keys = ()
    _reading = 0

    manage_options = (
        {'label': 'Customize', 'action': 'manage_main'},
        {'label': 'View', 'action': ''},
        {'label': 'Proxy', 'action': 'manage_proxyForm'})

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    security.declareProtected(ViewManagementScreens, 'manage_main')
    manage_main = DTMLFile('custdtml', _dtmldir)

    def __init__(self, id, filepath, fullname=None, properties=None):
        FSObject.__init__(self, id, filepath, fullname, properties)
        # Normally called via HTML.__init__ but we don't need the rest that
        # happens there.
        self.initvars(None, {})

    def _createZODBClone(self):
        """Create a ZODB (editable) equivalent of this object."""
        return DTMLMethod(self.read(), __name__=self.getId())

    def _readFile(self, reparse):
        """Read the data from the filesystem.
        """
        file = open(self._filepath, 'r') # not 'rb', as this is a text file!
        try:
            data = file.read()
        finally:
            file.close()
        self.raw = data

        if reparse:
            self._reading = 1  # Avoid infinite recursion
            try:
                self.cook()
            finally:
                self._reading = 0

    # Hook up chances to reload in debug mode
    security.declarePrivate('read_raw')
    def read_raw(self):
        if not self._reading:
            self._updateFromFS()
        return HTML.read_raw(self)

    #### The following is mainly taken from OFS/DTMLMethod.py ###

    index_html = None # Prevent accidental acquisition

    # Documents masquerade as functions:
    func_code = DTMLMethod.func_code

    default_content_type = 'text/html'

    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
        """Render the document given a client object, REQUEST mapping,
        Response, and key word arguments."""

        self._updateFromFS()

        kw['document_id'] = self.getId()
        kw['document_title'] = self.title

        if client is not None:
            if _checkConditionalGET(self, kw):
                return ''

        if not self._cache_namespace_keys:
            data = self.ZCacheable_get(default=_marker)
            if data is not _marker:
                # Return cached results.
                return data

        __traceback_info__ = self._filepath
        security = getSecurityManager()
        security.addContext(self)
        try:
            r = HTML.__call__(self, client, REQUEST, **kw)

            if client is None:
                # Called as subtemplate, so don't need error propagation!
                if RESPONSE is None:
                    result = r
                else:
                    result = decapitate(r, RESPONSE)
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(result)
                return result

            if not isinstance(r, basestring) or RESPONSE is None:
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(r)
                return r

        finally:
            security.removeContext(self)

        headers = RESPONSE.headers
        if not ('content-type' in headers or 'Content-Type' in headers):
            if 'content_type' in self.__dict__:
                c = self.content_type
            else:
                c, _e = guess_content_type(self.getId(), r)
            RESPONSE.setHeader('Content-Type', c)
        if RESPONSE is not None:
            # caching policy manager hook
            _setCacheHeaders(self, {})
        result = decapitate(r, RESPONSE)
        if not self._cache_namespace_keys:
            self.ZCacheable_set(result)
        return result

    def getCacheNamespaceKeys(self):
        '''
        Returns the cacheNamespaceKeys.
        '''
        return self._cache_namespace_keys

    def setCacheNamespaceKeys(self, keys, REQUEST=None):
        '''
        Sets the list of names that should be looked up in the
        namespace to provide a cache key.
        '''
        ks = []
        for key in keys:
            key = str(key).strip()
            if key:
                ks.append(key)
        self._cache_namespace_keys = tuple(ks)
        if REQUEST is not None:
            return self.ZCacheable_manage(self, REQUEST)

    # Zope 2.3.x way:
    def validate(self, inst, parent, name, value, md=None):
        return getSecurityManager().validate(inst, parent, name, value)

    security.declareProtected(FTPAccess, 'manage_FTPget')
    manage_FTPget = DTMLMethod.manage_FTPget.im_func

    security.declareProtected(ViewManagementScreens, 'PrincipiaSearchSource')
    PrincipiaSearchSource = DTMLMethod.PrincipiaSearchSource.im_func

    security.declareProtected(ViewManagementScreens, 'document_src')
    document_src = DTMLMethod.document_src.im_func

    security.declareProtected(ViewManagementScreens, 'manage_haveProxy')
    manage_haveProxy = DTMLMethod.manage_haveProxy.im_func

InitializeClass(FSDTMLMethod)

registerFileExtension('dtml', FSDTMLMethod)
registerMetaType('DTML Method', FSDTMLMethod)
