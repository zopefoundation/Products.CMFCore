##############################################################################
#
# Copyright (c) 2001, 2006 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" FSReSTMethod: Filesystem methodish Structured Text document. """

from docutils.core import publish_parts
from docutils.writers.html4css1 import Writer

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate

from Products.CMFCore.DirectoryView import registerFileExtension
from Products.CMFCore.DirectoryView import registerMetaType
from Products.CMFCore.FSObject import FSObject
from Products.CMFCore.permissions import FTPAccess
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ViewManagementScreens
from Products.CMFCore.utils import _dtmldir
from Products.CMFCore.utils import _checkConditionalGET
from Products.CMFCore.utils import _setCacheHeaders
from Products.CMFCore.utils import _ViewEmulator

_DEFAULT_TEMPLATE_ZPT = """\
<html metal:use-macro="context/main_template/macros/main">
<body>

<metal:block metal:fill-slot="body"
><div tal:replace="structure options/cooked">
COOKED TEXT HERE
</div>
</metal:block>

</body>
</html>
"""

_CUSTOMIZED_TEMPLATE_ZPT = """\
<html metal:use-macro="context/main_template/macros/master">
<body>

<metal:block metal:fill-slot="body"
><div tal:define="std modules/Products/PythonScripts/standard;
                  rest nocall:std/restructured_text;"
      tal:replace="structure python:rest(template.rest)">
COOKED TEXT HERE
</div>
</metal:block>

</body>
</html>
"""

class Warnings(object):

    def __init__(self):
        self.messages = []

    def write(self, message):
        self.messages.append(message)


class FSReSTMethod(FSObject):
    """ A chunk of StructuredText, rendered as a skin method of a CMF site.
    """
    meta_type = 'Filesystem ReST Method'
    _owner = None # unowned
    report_level = 1
    input_encoding = 'ascii'
    output_encoding = 'utf8'

    manage_options=({'label' : 'Customize','action' : 'manage_main'},
                    {'label' : 'View','action' : ''},
                   )

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    security.declareProtected(ViewManagementScreens, 'manage_main')
    manage_main = DTMLFile('custstx', _dtmldir)

    #
    #   FSObject interface
    #
    def _createZODBClone(self):
        """
            Create a ZODB (editable) equivalent of this object.
        """
        target = ZopePageTemplate(self.getId(), _CUSTOMIZED_TEMPLATE_ZPT)
        target._setProperty('rest', self.raw, 'text')
        return target

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
            self.cook()

    #
    #   "Wesleyan" interface (we need to be "methodish").
    #
    class func_code:
        pass

    func_code = func_code()
    func_code.co_varnames = ()
    func_code.co_argcount = 0
    func_code.__roles__ = ()

    func_defaults__roles__ = ()
    func_defaults = ()

    index_html = None   # No accidental acquisition

    default_content_type = 'text/html'

    def cook(self):
        if not hasattr(self, '_v_cooked'):
            settings = {
                'halt_level': 6,
                'report_level' : self.report_level,
                'input_encoding': self.input_encoding,
                'output_encoding': self.output_encoding,
                'initial_header_level' : 1,
                'stylesheet' : None,
                'stylesheet_path' : None,
                'pub.settings.warning_stream' :  Warnings(),
                'file_insertion_enabled' : 0,
                'raw_enabled' : 0,
                }

            parts = publish_parts(self.raw, writer=Writer(),
                                settings_overrides=settings)
            self._v_cooked = parts['html_body']
        return self._v_cooked

    _default_template = ZopePageTemplate('restmethod_view',
                                         _DEFAULT_TEMPLATE_ZPT, 'text/html')

    def __call__( self, REQUEST={}, RESPONSE=None, **kw ):
        """ Return our rendered StructuredText.
        """
        self._updateFromFS()

        if RESPONSE is not None:
            RESPONSE.setHeader( 'Content-Type', 'text/html' )

        view = _ViewEmulator(self.getId()).__of__(self)
        if _checkConditionalGET(view, extra_context={}):
            return ''

        _setCacheHeaders(view, extra_context={})

        return self._render(REQUEST, RESPONSE, **kw)

    security.declarePrivate('modified')
    def modified(self):
        return self.getModTime()

    security.declarePrivate('_render')
    def _render(self, REQUEST={}, RESPONSE=None, **kw):
        """ Find the appropriate rendering template and use it to render us.
        """
        template = getattr(self, 'restmethod_view', self._default_template)

        if getattr(template, 'isDocTemp', 0):
            #posargs = (self, REQUEST, RESPONSE)
            posargs = (self, REQUEST)
        else:
            posargs = ()

        kwargs = {'cooked': self.cook()}
        return template(*posargs, **kwargs)

    security.declareProtected(FTPAccess, 'manage_FTPget')
    def manage_FTPget(self):
        """ Fetch our source for delivery via FTP.
        """
        return self.raw

    security.declareProtected(ViewManagementScreens, 'PrincipiaSearchSource')
    def PrincipiaSearchSource(self):
        """ Fetch our source for indexing in a catalog.
        """
        return self.raw

    security.declareProtected(ViewManagementScreens, 'document_src')
    def document_src( self ):
        """ Fetch our source for rendering in the ZMI.
        """
        return self.raw

InitializeClass(FSReSTMethod)

registerFileExtension('rst', FSReSTMethod)
registerMetaType('ReST Method', FSReSTMethod)
