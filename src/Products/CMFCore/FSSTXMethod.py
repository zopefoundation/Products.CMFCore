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
""" FSSTXMethod: Filesystem methodish Structured Text document.
"""

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.special_dtml import DTMLFile
from DocumentTemplate.DT_HTML import HTML as DTML_HTML
from OFS.DTMLDocument import DTMLDocument
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zope.structuredtext import stx2html

from .DirectoryView import registerFileExtension
from .DirectoryView import registerMetaType
from .FSObject import FSObject
from .permissions import FTPAccess
from .permissions import View
from .permissions import ViewManagementScreens
from .utils import _checkConditionalGET
from .utils import _dtmldir
from .utils import _setCacheHeaders
from .utils import _ViewEmulator


_STX_TEMPLATE = 'ZPT'  # or 'DTML'

_DEFAULT_TEMPLATE_DTML = """\
<dtml-var standard_html_header>
<dtml-var cooked>
<dtml-var standard_html_footer>"""

_CUSTOMIZED_TEMPLATE_DTML = """\
<dtml-var standard_html_header>
<dtml-var stx fmt="structured-text">
<dtml-var standard_html_footer>"""

_DEFAULT_TEMPLATE_ZPT = """\
<html metal:use-macro="context/main_template/macros/master">
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
                  stx nocall:std/structured_text;"
      tal:replace="structure python:stx(template.stx)">
COOKED TEXT HERE
</div>
</metal:block>

</body>
</html>
"""


class FSSTXMethod(FSObject):
    """ A chunk of StructuredText, rendered as a skin method of a CMF site.
    """
    meta_type = 'Filesystem STX Method'
    _owner = None  # unowned

    manage_options = ({'label': 'Customize', 'action': 'manage_main'},
                      {'label': 'View', 'action': ''})

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
        if _STX_TEMPLATE == 'DTML':
            target = DTMLDocument(_CUSTOMIZED_TEMPLATE_DTML,
                                  __name__=self.getId())
        elif _STX_TEMPLATE == 'ZPT':
            target = ZopePageTemplate(self.getId(), _CUSTOMIZED_TEMPLATE_ZPT)

        target._setProperty('stx', self.raw, 'text')
        return target

    def _readFile(self, reparse):
        """Read the data from the filesystem.
        """
        file = open(self._filepath)  # not 'rb', as this is a text file!
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
    class _func_code:
        pass

    __code__ = _func_code()
    __code__.co_varnames = ()
    __code__.co_argcount = 0

    __defaults__ = ()

    index_html = None   # No accidental acquisition

    default_content_type = 'text/html'

    def cook(self):
        if not hasattr(self, '_v_cooked'):
            self._v_cooked = stx2html(self.raw, level=1, header=0)
        return self._v_cooked

    _default_DTML_template = DTML_HTML(_DEFAULT_TEMPLATE_DTML)
    _default_ZPT_template = ZopePageTemplate('stxmethod_view',
                                             _DEFAULT_TEMPLATE_ZPT,
                                             'text/html')

    def __call__(self, REQUEST={}, RESPONSE=None, **kw):
        """ Return our rendered StructuredText.
        """
        self._updateFromFS()

        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', 'text/html')

        view = _ViewEmulator(self.getId()).__of__(self)
        _setCacheHeaders(view, extra_context={})

        if _checkConditionalGET(view, extra_context={}):
            return ''

        return self._render(REQUEST, RESPONSE, **kw)

    @security.private
    def modified(self):
        return self.getModTime()

    @security.private
    def _render(self, REQUEST={}, RESPONSE=None, **kw):
        """ Find the appropriate rendering template and use it to render us.
        """
        if _STX_TEMPLATE == 'DTML':
            default_template = self._default_DTML_template
        elif _STX_TEMPLATE == 'ZPT':
            default_template = self._default_ZPT_template
        else:
            raise TypeError('Invalid STX template: %s' % _STX_TEMPLATE)

        template = getattr(self, 'stxmethod_view', default_template)

        if getattr(template, 'isDocTemp', 0):
            posargs = (self, REQUEST)
        else:
            posargs = ()

        kwargs = {'cooked': self.cook()}
        return template(*posargs, **kwargs)

    @security.protected(FTPAccess)
    def manage_FTPget(self):
        """ Fetch our source for delivery via FTP.
        """
        return self.raw

    @security.protected(ViewManagementScreens)
    def PrincipiaSearchSource(self):
        """ Fetch our source for indexing in a catalog.
        """
        return self.raw

    @security.protected(ViewManagementScreens)
    def document_src(self):
        """ Fetch our source for rendering in the ZMI.
        """
        return self.raw


InitializeClass(FSSTXMethod)

registerFileExtension('stx', FSSTXMethod)
registerMetaType('STX Method', FSSTXMethod)
