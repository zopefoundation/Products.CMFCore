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
""" Customizable page templates that come from the filesystem. """

import re

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.utils import charsetFromMetaEquiv
from Products.PageTemplates.utils import encodingFromXMLPreamble
from Products.PageTemplates.ZopePageTemplate import preferred_encodings
from Products.PageTemplates.ZopePageTemplate import Src
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from Shared.DC.Scripts.Script import Script

from Products.CMFCore.DirectoryView import registerFileExtension
from Products.CMFCore.DirectoryView import registerMetaType
from Products.CMFCore.FSObject import FSObject
from Products.CMFCore.permissions import FTPAccess
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ViewManagementScreens
from Products.CMFCore.utils import _checkConditionalGET
from Products.CMFCore.utils import _dtmldir
from Products.CMFCore.utils import _setCacheHeaders


xml_detect_re = re.compile('^\s*<\?xml\s+(?:[^>]*?encoding=["\']([^"\'>]+))?')
charset_re = re.compile(r'charset.*?=.*?(?P<charset>[\w\-]*)', re.I|re.M|re.S)
_marker = object()


class FSPageTemplate(FSObject, Script, PageTemplate):

    """Wrapper for Page Template.
    """

    meta_type = 'Filesystem Page Template'
    _owner = None  # Unowned

    manage_options=({'label':'Customize', 'action':'manage_main'},
                    {'label':'Test', 'action':'ZScriptHTML_tryForm'},
                   )

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    security.declareProtected(ViewManagementScreens, 'manage_main')
    manage_main = DTMLFile('custpt', _dtmldir)

    # Declare security for unprotected PageTemplate methods.
    security.declarePrivate('pt_edit', 'write')

    def __init__(self, id, filepath, fullname=None, properties=None):
        FSObject.__init__(self, id, filepath, fullname, properties)
        self.ZBindings_edit(self._default_bindings)

    def _createZODBClone(self):
        """Create a ZODB (editable) equivalent of this object."""
        obj = ZopePageTemplate(self.getId(), self._text, self.content_type)
        obj.expand = 0
        obj.write(self.read())
        return obj

#    def ZCacheable_isCachingEnabled(self):
#        return 0

    def _readFile(self, reparse):
        """Read the data from the filesystem.
        """
        if reparse:
            file = open(self._filepath, 'rU') # not 'rb', as this is a text file!
            try:
                data = file.read()
            finally:
                file.close()

            # If we already have a content_type set it must come from a
            # .metadata file and we should always honor that. The content
            # type is initialized as text/html by default, so we only
            # attempt further detection if the default is encountered.
            # One previous misbehavior remains: It is not possible to
            # force a text/html type if parsing detects it as XML.
            encoding = None
            preferred = preferred_encodings[:]

            if getattr(self, 'content_type', 'text/html') == 'text/html':
                xml_info = xml_detect_re.match(data)
                if xml_info:
                    # Smells like xml
                    # set "content_type" from the XML declaration
                    encoding = xml_info.group(1) or 'utf-8'
                    self.content_type = 'text/xml; charset=%s' % encoding

            if not isinstance(data, unicode):
                if encoding is None:
                    charset = getattr(self, 'charset', None)

                    if charset is None:
                        if self.content_type.startswith('text/html'):
                            mo = charset_re.search(self.content_type)
                            if mo:
                                charset = mo.group(1).lower()

                            if charset is None:
                                charset = charsetFromMetaEquiv(data)
                                
                        elif self.content_type.startswith('text/xml'):
                            charset = encodingFromXMLPreamble(data)

                        else:
                            raise ValueError('Unsupported content_type: %s'
                                                % self.content_type)

                    if charset is not None:
                        preferred.insert(0, charset)

                else:
                    preferred.insert(0, encoding)

                for enc in preferred:
                    try:
                        data = unicode(data, enc)
                        if isinstance(data, unicode):
                            break
                    except UnicodeDecodeError:
                            continue
                else:
                    data = unicode(data)

            self.write(data)


    security.declarePrivate('read')
    def read(self):
        # Tie in on an opportunity to auto-update
        self._updateFromFS()
        return FSPageTemplate.inheritedAttribute('read')(self)

    ### The following is mainly taken from ZopePageTemplate.py ###

    expand = 0

    func_defaults = None
    func_code = ZopePageTemplate.func_code
    _default_bindings = ZopePageTemplate._default_bindings

    security.declareProtected(View, '__call__')

    def pt_macros(self):
        # Tie in on an opportunity to auto-reload
        self._updateFromFS()
        return FSPageTemplate.inheritedAttribute('pt_macros')(self)

    def pt_render(self, source=0, extra_context={}):
        self._updateFromFS()  # Make sure the template has been loaded.

        if not source:
            # If we have a conditional get, set status 304 and return
            # no content
            if _checkConditionalGET(self, extra_context):
                return ''

        result = FSPageTemplate.inheritedAttribute('pt_render')(
                                self, source, extra_context
                                )
        if not source:
            _setCacheHeaders(self, extra_context)
        return result

    security.declareProtected(ViewManagementScreens, 'pt_source_file')
    def pt_source_file(self):

        """ Return a file name to be compiled into the TAL code.
        """
        return 'file:%s' % self._filepath

    security.declarePrivate( '_ZPT_exec' )
    _ZPT_exec = ZopePageTemplate._exec.im_func

    security.declarePrivate( '_exec' )
    def _exec(self, bound_names, args, kw):
        """Call a FSPageTemplate"""
        try:
            response = self.REQUEST.RESPONSE
        except AttributeError:
            response = None
        # Read file first to get a correct content_type default value.
        self._updateFromFS()

        if not kw.has_key('args'):
            kw['args'] = args
        bound_names['options'] = kw

        try:
            response = self.REQUEST.RESPONSE
            if not response.headers.has_key('content-type'):
                response.setHeader('content-type', self.content_type)
        except AttributeError:
            pass

        security=getSecurityManager()
        bound_names['user'] = security.getUser()

        # Retrieve the value from the cache.
        keyset = None
        if self.ZCacheable_isCachingEnabled():
            # Prepare a cache key.
            keyset = {
                      # Why oh why?
                      # All this code is cut and paste
                      # here to make sure that we
                      # dont call _getContext and hence can't cache
                      # Annoying huh?
                      'here': self.aq_parent.getPhysicalPath(),
                      'bound_names': bound_names}
            result = self.ZCacheable_get(keywords=keyset)
            if result is not None:
                # Got a cached value.
                return result

        # Execute the template in a new security context.
        security.addContext(self)
        try:
            result = self.pt_render(extra_context=bound_names)
            if keyset is not None:
                # Store the result in the cache.
                self.ZCacheable_set(result, keywords=keyset)
            return result
        finally:
            security.removeContext(self)

        return result

    # Copy over more methods
    security.declareProtected(FTPAccess, 'manage_FTPget')
    manage_FTPget = ZopePageTemplate.manage_FTPget.im_func

    security.declareProtected(View, 'get_size')
    get_size = ZopePageTemplate.get_size.im_func
    getSize = get_size

    security.declareProtected(ViewManagementScreens, 'PrincipiaSearchSource')
    PrincipiaSearchSource = ZopePageTemplate.PrincipiaSearchSource.im_func

    security.declareProtected(ViewManagementScreens, 'document_src')
    document_src = ZopePageTemplate.document_src.im_func

    pt_getContext = ZopePageTemplate.pt_getContext.im_func

    ZScriptHTML_tryParams = ZopePageTemplate.ZScriptHTML_tryParams.im_func

    source_dot_xml = Src()

setattr(FSPageTemplate, 'source.xml',  FSPageTemplate.source_dot_xml)
setattr(FSPageTemplate, 'source.html', FSPageTemplate.source_dot_xml)
InitializeClass(FSPageTemplate)

registerFileExtension('pt', FSPageTemplate)
registerFileExtension('zpt', FSPageTemplate)
registerFileExtension('html', FSPageTemplate)
registerFileExtension('htm', FSPageTemplate)
registerMetaType('Page Template', FSPageTemplate)
