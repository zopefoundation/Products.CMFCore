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
""" Customizable objects that come from the filesystem (base class).
"""

import os

from AccessControl.class_init import InitializeClass
from AccessControl.Permission import Permission
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.config import getConfiguration
from App.special_dtml import HTML
from DateTime.DateTime import DateTime
from OFS.Cache import Cacheable
from OFS.role import RoleManager
from OFS.SimpleItem import Item
from zope.component import getUtility

from Products.PythonScripts.standard import html_quote

from .interfaces import ISkinsTool
from .permissions import ManagePortal
from .permissions import View
from .permissions import ViewManagementScreens


class FSObject(Implicit, Item, RoleManager, Cacheable):

    """FSObject is a base class for all filesystem based look-alikes.

    Subclasses of this class mimic ZODB based objects like Image and
    DTMLMethod, but are not directly modifiable from the management
    interface. They provide means to create a TTW editable copy, however.
    """

    # Always empty for FS based, non-editable objects.
    title = ''
    _file_mod_time = 0
    _parsed = 0

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    def __init__(self, id, filepath, fullname=None, properties=None):
        if properties:
            # Since props come from the filesystem, this should be
            # safe.
            self.__dict__.update(properties)
            if fullname and properties.get('keep_extension', 0):
                id = fullname

            cache = properties.get('cache')
            if cache:
                self.ZCacheable_setManagerId(cache)

        self.id = id
        self.__name__ = id  # __name__ is used in traceback reporting
        self._filepath = filepath

        try:
            self._file_mod_time = os.stat(filepath).st_mtime
        except Exception:
            pass
        self._readFile(0)

    @security.protected(ViewManagementScreens)
    def manage_doCustomize(self, folder_path, RESPONSE=None, root=None,
                           obj=None):
        """Makes a ZODB Based clone with the same data.

        Calls _createZODBClone for the actual work.
        """

        if obj is None:
            obj = self._createZODBClone()
        parent = aq_parent(aq_inner(self))

        # Preserve cache manager associations
        cachemgr_id = self.ZCacheable_getManagerId()
        if cachemgr_id and \
                getattr(obj, 'ZCacheable_setManagerId', None) is not None:
            obj.ZCacheable_setManagerId(cachemgr_id)

        # If there are proxy roles we preserve them
        proxy_roles = getattr(aq_base(self), '_proxy_roles', None)
        if proxy_roles is not None and isinstance(proxy_roles, tuple):
            obj._proxy_roles = tuple(self._proxy_roles)

        # Also, preserve any permission settings that might have come
        # from a metadata file or from fiddling in the ZMI
        old_info = [x[:2] for x in self.ac_inherited_permissions(1)]
        for old_perm, value in old_info:
            p = Permission(old_perm, value, self)
            acquired = int(isinstance(p.getRoles(default=[]), list))
            rop_info = self.rolesOfPermission(old_perm)
            roles = [x['name'] for x in rop_info if x['selected'] != '']
            try:
                # if obj is based on OFS.ObjectManager an acquisition context
                # is required for _subobject_permissions()
                obj.__of__(parent).manage_permission(old_perm, roles=roles,
                                                     acquire=acquired)
            except ValueError:
                # The permission was invalid, never mind
                pass

        id = obj.getId()
        fpath = tuple(folder_path.split('/'))
        if root is None:
            portal_skins = getUtility(ISkinsTool)
        else:
            portal_skins = root
        if folder_path == '.':
            fpath = ()
        folder = portal_skins.restrictedTraverse(fpath)
        if id in folder.objectIds():
            # we cant catch the badrequest so
            # we'll that to check before hand
            obj = folder._getOb(id)
            if RESPONSE is not None:
                RESPONSE.redirect(
                    '{}/manage_main?manage_tabs_message={}'.format(
                        obj.absolute_url(),
                        html_quote('An object with this id already exists')))
        else:
            folder._verifyObjectPaste(obj, validate_src=0)
            folder._setObject(id, obj)

            if RESPONSE is not None:
                RESPONSE.redirect(f'{folder.absolute_url()}/{id}/manage_main')

        if RESPONSE is not None:
            RESPONSE.redirect(f'{folder.absolute_url()}/{id}/manage_main')

    def _createZODBClone(self):
        """Create a ZODB (editable) equivalent of this object."""
        raise NotImplementedError('This should be implemented in a subclass.')

    def _readFile(self, reparse):
        """Read the data from the filesystem.

        Read the file indicated by self._filepath, and parse the
        data if necessary.  'reparse' is set when reading the second
        time and beyond.
        """
        raise NotImplementedError('This should be implemented in a subclass.')

    # Refresh our contents from the filesystem if that is newer and we are
    # running in debug mode.
    def _updateFromFS(self):
        parsed = self._parsed
        if not parsed or getConfiguration().debug_mode:
            try:
                mtime = os.stat(self._filepath).st_mtime
            except Exception:
                mtime = 0.0
            if not parsed or mtime != self._file_mod_time:
                self._readFile(1)
                if mtime != self._file_mod_time or mtime == 0.0:
                    self.ZCacheable_invalidate()
                    self._file_mod_time = mtime
                self._parsed = 1

    @security.protected(View)
    def get_size(self):
        """Get the size of the underlying file."""
        return os.path.getsize(self._filepath)

    @security.protected(View)
    def getModTime(self):
        """Return the last_modified date of the file we represent.

        Returns a DateTime instance.
        """
        self._updateFromFS()
        return DateTime(self._file_mod_time)

    @security.protected(View)
    def bobobase_modification_time(self):
        """Get the modification time the file did have last time it was read.
        """
        return DateTime(self._file_mod_time)

    @security.protected(ViewManagementScreens)
    def getObjectFSPath(self):
        """Return the path of the file we represent"""
        self._updateFromFS()
        return self._filepath


InitializeClass(FSObject)


class BadFile(FSObject):

    """
        Represent a file which was not readable or parseable
        as its intended type.
    """
    meta_type = 'Bad File'
    icon = 'p_/broken'

    BAD_FILE_VIEW = """\
<dtml-var manage_page_header>
<dtml-var manage_tabs>
<h2> Bad Filesystem Object: &dtml-getId; </h2>

<h3> File Contents </h3>
<pre>
<dtml-var getFileContents>
</pre>

<h3> Exception </h3>
<pre>
<dtml-var getExceptionText>
</pre>
<dtml-var manage_page_footer>
"""

    manage_options = ({'label': 'Error', 'action': 'manage_showError'},)

    def __init__(self, id, filepath, exc_str='', fullname=None,
                 properties=None):
        id = fullname or id  # Use the whole filename.
        self.exc_str = exc_str
        self.file_contents = ''
        FSObject.__init__(self, id, filepath, fullname, properties)

    security = ClassSecurityInfo()

    showError = HTML(BAD_FILE_VIEW)

    @security.protected(ManagePortal)
    def manage_showError(self, REQUEST):
        """
        """
        return self.showError(self, REQUEST)

    @security.private
    def _readFile(self, reparse):
        """Read the data from the filesystem.
        """
        try:
            file = open(self._filepath, 'rb')
            try:
                data = self.file_contents = file.read()
            finally:
                file.close()
        except Exception:  # No errors of any sort may propagate
            data = self.file_contents = None  # give up
        return data

    @security.public
    def getFileContents(self):
        """
            Return the contents of the file, if we could read it.
        """
        return self.file_contents

    @security.public
    def getExceptionText(self):
        """
            Return the exception thrown while reading or parsing
            the file.
        """
        return self.exc_str


InitializeClass(BadFile)
