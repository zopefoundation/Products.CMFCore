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
""" Customizable Python scripts that come from the filesystem.
"""

from difflib import unified_diff

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.special_dtml import DTMLFile
from ComputedAttribute import ComputedAttribute
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Shared.DC.Scripts.Script import Script

from Products.PythonScripts.PythonScript import PythonScript

from .DirectoryView import registerFileExtension
from .DirectoryView import registerMetaType
from .FSObject import FSObject
from .permissions import FTPAccess
from .permissions import View
from .permissions import ViewManagementScreens
from .utils import _dtmldir


_marker = object()


class CustomizedPythonScript(PythonScript):

    """ Subclass which captures the "source" version's text.
    """

    # meta_type = 'Customized Python Script'  #(need permissions here)

    security = ClassSecurityInfo()

    def __init__(self, id, text):
        super().__init__(id)
        self.write(text)
        self.original_source = text

    @security.protected(ViewManagementScreens)
    def getDiff(self):
        """ Return a diff of the current source with the original source.
        """
        return unified_diff(self.original_source.splitlines(),
                            self.read().splitlines(),
                            'original',
                            'modified',
                            '',
                            '',
                            lineterm='')

    security.declareProtected(ViewManagementScreens,  # NOQA: flake8: D001
                              'manage_showDiff')
    manage_showDiff = PageTemplateFile('www/cpsDiff.pt', globals())

    manage_options = (
        PythonScript.manage_options[:1] +
        ({'label': 'Diff', 'action': 'manage_showDiff'},) +
        PythonScript.manage_options[1:])


InitializeClass(CustomizedPythonScript)


class FSPythonScript(FSObject, Script):

    """FSPythonScripts act like Python Scripts but are not directly
    modifiable from the management interface."""

    meta_type = 'Filesystem Script (Python)'
    zmi_icon = 'fa fa-terminal'
    _params = _body = ''
    _proxy_roles = ()
    _owner = None  # Unowned

    manage_options = (
        {'label': 'Customize', 'action': 'manage_main'},)

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    security.declareProtected(ViewManagementScreens,  # NOQA: flake8: D001
                              'manage_main')
    manage_main = DTMLFile('custpy', _dtmldir)

    security.declareProtected(View, 'index_html')  # NOQA: flake8: D001
    # Prevent the bindings from being edited TTW
    security.declarePrivate('ZBindings_edit',  # NOQA: flake8: D001
                            'ZBindingsHTML_editForm',
                            'ZBindingsHTML_editAction')

    def _createZODBClone(self):
        """Create a ZODB (editable) equivalent of this object."""
        return CustomizedPythonScript(self.getId(), self.read())

    def _readFile(self, reparse):
        """Read the data from the filesystem.
        """
        file = open(self._filepath)
        try:
            data = file.read()
        finally:
            file.close()

        if reparse:
            self._write(data, reparse)

    def _validateProxy(self, roles=None):
        pass

    def __render_with_namespace__(self, namespace):
        """Calls the script."""
        self._updateFromFS()
        return Script.__render_with_namespace__(self, namespace)

    def __call__(self, *args, **kw):
        """Calls the script."""
        self._updateFromFS()
        return Script.__call__(self, *args, **kw)

    _exec = PythonScript._exec

    security.declareProtected(ViewManagementScreens,  # NOQA: flake8: D001
                              'getModTime')
    # getModTime defined in FSObject

    def ZScriptHTML_tryParams(self):
        """Parameters to test the script with."""
        param_names = []
        for name in self._params.split(','):
            name = name.strip()
            if name and name[0] != '*':
                param_names.append(name.split('=', 1)[0])
        return param_names

    @security.protected(ViewManagementScreens)
    def read(self):
        self._updateFromFS()
        return self._source

    @security.protected(ViewManagementScreens)
    def document_src(self, REQUEST=None, RESPONSE=None):
        """Return unprocessed document source."""

        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', 'text/plain')
        return self._source

    @security.protected(ViewManagementScreens)
    def PrincipiaSearchSource(self):
        """Support for searching - the document's contents are searched."""
        return f'{self._params}\n{self._body}'

    @security.protected(ViewManagementScreens)
    def params(self):
        return self._params

    security.declareProtected(ViewManagementScreens,  # NOQA: flake8: D001
                              'manage_haveProxy')
    manage_haveProxy = PythonScript.manage_haveProxy

    @security.protected(ViewManagementScreens)
    def body(self):
        return self._body

    @security.protected(ViewManagementScreens)
    def get_size(self):
        return len(self.read())

    @security.protected(FTPAccess)
    def manage_FTPget(self):
        """Get source for FTP download"""
        self.REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.read()

    def _write(self, text, compile):
        """
        Parses the source, storing the body, params, title, bindings,
        and source in self.  If compile is set, compiles the
        function.
        """
        ps = PythonScript(self.id)
        ps.write(text)
        if compile:
            ps._makeFunction()
            self._v_ft = ps._v_ft
            self.__code__ = ps.__code__
            self.__defaults__ = ps.__defaults__
        self._body = ps._body
        self._params = ps._params
        self.title = ps.title
        self._setupBindings(ps.getBindingAssignments().getAssignedNames())
        self._source = ps.read()  # Find out what the script sees.

    def _func_defaults(self):
        # This ensures __code__ and __defaults__ are
        # set when the code hasn't been compiled yet,
        # just in time for mapply().  Truly odd, but so is mapply(). :P
        self._updateFromFS()
        return self.__dict__.get('__defaults__', None)
    __defaults__ = ComputedAttribute(_func_defaults, 1)

    def _func_code(self):
        # See func_defaults.
        self._updateFromFS()
        return self.__dict__.get('__code__', None)
    __code__ = ComputedAttribute(_func_code, 1)

    def title(self):
        # See func_defaults.
        self._updateFromFS()
        return self.__dict__.get('title', None)
    title = ComputedAttribute(title, 1)

    def getBindingAssignments(self):
        # Override of the version in Bindings.py.
        # This version ensures that bindings get loaded on demand.
        if not hasattr(self, '_bind_names'):
            # Set a default first to avoid recursion
            self._setupBindings()
            # Now do it for real
            self._updateFromFS()
        return self._bind_names


InitializeClass(FSPythonScript)

registerFileExtension('py', FSPythonScript)
registerMetaType('Script (Python)', FSPythonScript)
