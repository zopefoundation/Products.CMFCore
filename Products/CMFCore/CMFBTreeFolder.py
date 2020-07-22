##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""CMFBTreeFolder
"""

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from zope.component.factory import Factory

from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2Base

from .permissions import AddPortalFolders
from .PortalFolder import PortalFolder
from .PortalFolder import PortalFolderBase


def manage_addCMFBTreeFolder(dispatcher, id, title='', REQUEST=None):
    """Adds a new BTreeFolder object with id *id*.
    """
    id = str(id)
    ob = CMFBTreeFolder(id)
    ob.title = str(title)
    dispatcher._setObject(id, ob, suppress_events=True)
    ob = dispatcher._getOb(id)
    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(ob.absolute_url() + '/manage_main')


class CMFBTreeFolder(BTreeFolder2Base, PortalFolderBase):

    """BTree folder for CMF sites.
    """

    security = ClassSecurityInfo()

    def __init__(self, id, title=''):
        PortalFolderBase.__init__(self, id, title)
        BTreeFolder2Base.__init__(self, id)

    def _checkId(self, id, allow_dup=0):
        PortalFolderBase._checkId(self, id, allow_dup)
        BTreeFolder2Base._checkId(self, id, allow_dup)

    @security.protected(AddPortalFolders)
    def manage_addPortalFolder(self, id, title='', REQUEST=None):
        """Add a new PortalFolder object with id *id*.
        """
        ob = PortalFolder(id, title)
        self._setObject(id, ob, suppress_events=True)
        if REQUEST is not None:
            return self.folder_contents(  # XXX: ick!
                self, REQUEST, portal_status_message='Folder added')


InitializeClass(CMFBTreeFolder)

CMFBTreeFolderFactory = Factory(CMFBTreeFolder)
