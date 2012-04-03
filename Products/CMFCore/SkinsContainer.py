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
""" Base class for objects that supply skins.
"""

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from zope.interface import implements

from Products.CMFCore.exceptions import SkinPathError
from Products.CMFCore.interfaces import ISkinsContainer
from Products.CMFCore.permissions import AccessContentsInformation


class SkinsContainer:

    implements(ISkinsContainer)

    security = ClassSecurityInfo()

    security.declareProtected(AccessContentsInformation, 'getSkinPath')
    def getSkinPath(self, name):
        """ Convert a skin name to a skin path.
        """
        raise NotImplementedError

    security.declareProtected(AccessContentsInformation, 'getDefaultSkin')
    def getDefaultSkin(self):
        """ Get the default skin name.
        """
        raise NotImplementedError

    security.declareProtected(AccessContentsInformation, 'getRequestVarname')
    def getRequestVarname(self):
        """ Get the variable name to look for in the REQUEST.
        """
        raise NotImplementedError

    security.declarePrivate('getSkinByPath')
    def getSkinByPath(self, path, raise_exc=0):
        """ Get a skin at the given path.
        """
        baseself = aq_base(self)
        skinob = None
        parts = list( path.split(',') )
        parts.reverse()
        for part_path in parts:
            partob = baseself
            for name in part_path.strip().split('/'):
                if name == '':
                    continue
                if name[:1] == '_':
                    # Not allowed.
                    partob = None
                    if raise_exc:
                        raise SkinPathError('Underscores are not allowed')
                    break
                # Allow acquisition tricks.
                partob = getattr(partob, name, None)
                if partob is None:
                    # Not found.  Cancel the search.
                    if raise_exc:
                        raise SkinPathError('Name not found: %s' % part_path)
                    break
            if partob is not None:
                # Now partob has containment and context.
                # Build the final skinob by creating an object
                # that puts the former skinob in the context
                # of the new skinob.
                partob = aq_base(partob)
                if skinob is None:
                    skinob = partob
                else:
                    skinob = partob.__of__(skinob)
        return skinob

    security.declarePrivate('getSkinByName')
    def getSkinByName(self, name):
        """ Get the named skin.
        """
        path = self.getSkinPath(name)
        if path is None:
            return None
        return self.getSkinByPath(path)

InitializeClass( SkinsContainer )
