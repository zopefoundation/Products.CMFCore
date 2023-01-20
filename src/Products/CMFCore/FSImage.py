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
""" Customizable image objects that come from the filesystem.
"""

import os

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.special_dtml import DTMLFile
from OFS.Image import Image
from OFS.Image import getImageInfo

from .DirectoryView import registerFileExtension
from .DirectoryView import registerMetaType
from .FSObject import FSObject
from .permissions import FTPAccess
from .permissions import View
from .permissions import ViewManagementScreens
from .utils import _checkConditionalGET
from .utils import _dtmldir
from .utils import _FSCacheHeaders
from .utils import _setCacheHeaders
from .utils import _ViewEmulator


class FSImage(FSObject):

    """FSImages act like images but are not directly
    modifiable from the management interface."""
    # Note that OFS.Image.Image is not a base class because it is mutable.

    meta_type = 'Filesystem Image'
    zmi_icon = 'far fa-file-image'
    content_type = 'unknown/unknown'
    alt = ''
    height = ''
    width = ''
    _data = None

    manage_options = ({'label': 'Customize', 'action': 'manage_main'},)

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    security.declareProtected(ViewManagementScreens, 'manage_main')
    manage_main = DTMLFile('custimage', _dtmldir)

    def __init__(self, id, filepath, fullname=None, properties=None):
        id = fullname or id  # Use the whole filename.
        FSObject.__init__(self, id, filepath, fullname, properties)

    def _createZODBClone(self):
        return Image(self.getId(), '', self._readFile(1))

    def _readFile(self, reparse):
        """Read the data from the filesystem.
        """
        file = open(self._filepath, 'rb')
        try:
            data = self._data = file.read()
        finally:
            file.close()

        if reparse or self.content_type == 'unknown/unknown':
            try:
                mtime = os.stat(self._filepath).st_mtime
            except Exception:
                mtime = 0.0
            if mtime != self._file_mod_time or mtime == 0.0:
                self.ZCacheable_invalidate()
                self._file_mod_time = mtime
            ct, width, height = getImageInfo(data)
            self.content_type = ct
            self.width = width
            self.height = height
        return data

    # The following is mainly taken from OFS/Image.py

    __str__ = Image.__str__

    _image_tag = Image.tag

    @security.protected(View)
    def tag(self, *args, **kw):
        # Hook into an opportunity to reload metadata.
        self._updateFromFS()
        return self._image_tag(*args, **kw)

    @security.protected(View)
    def index_html(self, REQUEST, RESPONSE):
        """
        The default view of the contents of a File or Image.

        Returns the contents of the file or image.  Also, sets the
        Content-Type HTTP header to the objects content type.
        """
        self._updateFromFS()
        view = _ViewEmulator().__of__(self)

        # There are 2 Cache Managers which can be in play....
        # need to decide which to use to determine where the cache headers
        # are decided on.
        if self.ZCacheable_getManager() is not None:
            self.ZCacheable_set(None)
        else:
            _setCacheHeaders(view, extra_context={})

        # If we have a conditional get, set status 304 and return
        # no content
        if _checkConditionalGET(view, extra_context={}):
            return ''

        RESPONSE.setHeader('Content-Type', self.content_type)

        # old-style If-Modified-Since header handling.
        if self._setOldCacheHeaders():
            # Make sure the CachingPolicyManager gets a go as well
            _setCacheHeaders(view, extra_context={})
            return ''

        data = self._readFile(0)
        data_len = len(data)
        RESPONSE.setHeader('Content-Length', data_len)
        return data

    def _setOldCacheHeaders(self):
        # return False to disable this simple caching behaviour
        return _FSCacheHeaders(self)

    def modified(self):
        return self.getModTime()

    @security.protected(View)
    def getContentType(self):
        """Get the content type of a file or image.

        Returns the content type (MIME type) of a file or image.
        """
        self._updateFromFS()
        return self.content_type

    @security.protected(View)
    def get_size(self):
        """
            Return the size of the image.
        """
        self._updateFromFS()
        return self._data and len(self._data) or 0

    security.declareProtected(FTPAccess, 'manage_FTPget')
    manage_FTPget = index_html


InitializeClass(FSImage)

registerFileExtension('gif', FSImage)
registerFileExtension('jpg', FSImage)
registerFileExtension('jpeg', FSImage)
registerFileExtension('png', FSImage)
registerFileExtension('bmp', FSImage)
registerMetaType('Image', FSImage)
