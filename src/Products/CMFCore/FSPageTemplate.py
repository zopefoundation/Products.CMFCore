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
""" Customizable page templates that come from the filesystem.
"""

import re

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from App.special_dtml import DTMLFile
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.utils import charsetFromMetaEquiv
from Products.PageTemplates.utils import encodingFromXMLPreamble
from Products.PageTemplates.ZopePageTemplate import Src
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from Products.PageTemplates.ZopePageTemplate import preferred_encodings
from Shared.DC.Scripts.Script import Script

from .DirectoryView import registerFileExtension
from .DirectoryView import registerMetaType
from .FSObject import FSObject
from .permissions import FTPAccess
from .permissions import View
from .permissions import ViewManagementScreens
from .utils import HAS_ZSERVER
from .utils import _checkConditionalGET
from .utils import _dtmldir
from .utils import _setCacheHeaders


xml_detect_re = re.compile(
    br'^\s*<\?xml\s+(?:[^>]*?encoding=["\']([^"\'>]+))?')
charset_re = re.compile(r'charset.*?=.*?(?P<charset>[\w\-]*)',
                        re.I | re.M | re.S)
_marker = object()


class FSPageTemplate(FSObject, Script, PageTemplate):

    """Wrapper for Page Template.
    """

    meta_type = 'Filesystem Page Template'
    zmi_icon = 'far fa-file-code'
    _owner = None  # Unowned

    manage_options = (
        {'label': 'Customize', 'action': 'manage_main'},)

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    security.declareProtected(ViewManagementScreens,  # NOQA: flake8: D001
                              'manage_main')
    manage_main = DTMLFile('custpt', _dtmldir)

    # Declare security for unprotected PageTemplate methods.
    security.declarePrivate('pt_edit', 'write')  # NOQA: flake8: D001

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
            file = open(self._filepath, 'br')
            try:
                data = file.read()
                data = data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
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
                    if xml_info.group(1):
                        encoding = xml_info.group(1).decode('ascii')
                    else:
                        encoding = 'utf-8'
                    self.content_type = 'text/xml; charset=%s' % encoding

            if not isinstance(data, str):
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
                            raise ValueError('Unsupported content_type: %s' %
                                             self.content_type)

                    if charset is not None:
                        preferred.insert(0, charset)

                else:
                    preferred.insert(0, encoding)

                for enc in preferred:
                    try:
                        data = str(data, enc)
                        if isinstance(data, str):
                            break
                    except UnicodeDecodeError:
                        continue
                else:
                    data = str(data)

            self.write(data)

    @security.private
    def read(self):
        # Tie in on an opportunity to auto-update
        self._updateFromFS()
        return FSPageTemplate.inheritedAttribute('read')(self)

    # The following is mainly taken from ZopePageTemplate.py

    expand = 0
    output_encoding = 'utf-8'

    __defaults__ = None
    __code__ = ZopePageTemplate.__code__
    _default_bindings = ZopePageTemplate._default_bindings

    security.declareProtected(View, '__call__')  # NOQA: flake8: D001

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
                _setCacheHeaders(self, extra_context)
                return ''

        result = FSPageTemplate.inheritedAttribute('pt_render')(
                                self, source, extra_context)
        if not source:
            _setCacheHeaders(self, extra_context)
        return result

    @security.protected(ViewManagementScreens)
    def pt_source_file(self):

        """ Return a file name to be compiled into the TAL code.
        """
        return 'file:%s' % self._filepath

    security.declarePrivate('_ZPT_exec')  # NOQA: flake8: D001
    _ZPT_exec = ZopePageTemplate._exec

    @security.private
    def _exec(self, bound_names, args, kw):
        """Call a FSPageTemplate"""
        try:
            response = self.REQUEST.RESPONSE
        except AttributeError:
            response = None
        # Read file first to get a correct content_type default value.
        self._updateFromFS()

        if 'args' not in kw:
            kw['args'] = args
        bound_names['options'] = kw

        try:
            response = self.REQUEST.RESPONSE
            if 'content-type' not in response.headers:
                response.setHeader('content-type', self.content_type)
        except AttributeError:
            pass

        security = getSecurityManager()
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
    if HAS_ZSERVER:
        security.declareProtected(FTPAccess,  # NOQA: flake8: D001
                                  'manage_FTPget')
        manage_FTPget = ZopePageTemplate.manage_FTPget

    security.declareProtected(View, 'get_size')  # NOQA: flake8: D001
    get_size = ZopePageTemplate.get_size
    getSize = get_size

    security.declareProtected(ViewManagementScreens,  # NOQA: flake8: D001
                              'PrincipiaSearchSource')
    PrincipiaSearchSource = ZopePageTemplate.PrincipiaSearchSource

    security.declareProtected(ViewManagementScreens,  # NOQA: flake8: D001
                              'document_src')
    document_src = ZopePageTemplate.document_src

    pt_getContext = ZopePageTemplate.pt_getContext

    source_dot_xml = Src()


setattr(FSPageTemplate, 'source.xml', FSPageTemplate.source_dot_xml)
setattr(FSPageTemplate, 'source.html', FSPageTemplate.source_dot_xml)
InitializeClass(FSPageTemplate)

registerFileExtension('pt', FSPageTemplate)
registerFileExtension('zpt', FSPageTemplate)
registerFileExtension('html', FSPageTemplate)
registerFileExtension('htm', FSPageTemplate)
registerMetaType('Page Template', FSPageTemplate)
