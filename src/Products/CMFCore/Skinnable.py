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
""" Base class for object managers which can be "skinned".

Skinnable object managers inherit attributes from a skin specified in
the browser request.  Skins are stored in a fixed-name subobject.
"""

import logging
from _thread import get_ident

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from OFS.ObjectManager import ObjectManager
from ZODB.POSException import ConflictError
from zope.component import queryUtility

from .interfaces import ISkinsTool


logger = logging.getLogger('CMFCore.Skinnable')

_MARKER = object()  # Create a new marker object.

SKINDATA = {}  # mapping thread-id -> (skinobj, skinname, ignore, resolve)


class SkinDataCleanup:
    """Cleanup at the end of the request."""
    def __init__(self, tid):
        self.tid = tid

    def __del__(self):
        tid = self.tid
        # Be extra careful in __del__
        if SKINDATA is not None:
            if tid in SKINDATA:
                del SKINDATA[tid]


class SkinnableObjectManager(ObjectManager):

    security = ClassSecurityInfo()

    def __getattr__(self, name):
        """
        Looks for the name in an object with wrappers that only reach
        up to the root skins folder.

        This should be fast, flexible, and predictable.
        """
        if not name:
            raise AttributeError(name)
        if name[0] not in ('_', '@', '+') and not name.startswith('aq_'):
            sd = SKINDATA.get(get_ident())
            if sd is not None:
                ob, _skinname, ignore, resolve = sd
                if name not in ignore:
                    if name in resolve:
                        return resolve[name]
                    subob = getattr(ob, name, _MARKER)
                    if subob is not _MARKER:
                        # Return it in context of self, forgetting
                        # its location and acting as if it were located
                        # in self.
                        retval = aq_base(subob)
                        resolve[name] = retval
                        return retval
                    else:
                        ignore[name] = 1
        raise AttributeError(name)

    @security.private
    def getSkin(self, name=None):
        """Returns the requested skin.
        """
        skinob = None
        stool = queryUtility(ISkinsTool)
        if stool is not None:
            if name is not None:
                skinob = stool.getSkinByName(name)
            if skinob is None:
                skinob = stool.getSkinByName(stool.getDefaultSkin())
                if skinob is None:
                    skinob = stool.getSkinByPath('')
        return skinob

    @security.public
    def getSkinNameFromRequest(self, REQUEST=None):
        """Returns the skin name from the Request."""
        if REQUEST is None:
            return None
        stool = queryUtility(ISkinsTool)
        if stool is not None:
            name = REQUEST.get(stool.getRequestVarname(), None)
            if not name or name not in stool.getSkinSelections():
                return None
            return name

    @security.public
    def changeSkin(self, skinname, REQUEST=None):
        """Change the current skin.

        Can be called manually, allowing the user to change
        skins in the middle of a request.
        """
        skinobj = self.getSkin(skinname)
        if skinobj is not None:
            tid = get_ident()
            SKINDATA[tid] = (skinobj, skinname, {}, {})
            if REQUEST is not None:
                REQUEST._hold(SkinDataCleanup(tid))

    @security.public
    def getCurrentSkinName(self):
        """Return the current skin name.
        """
        sd = SKINDATA.get(get_ident())
        if sd is not None:
            _ob, skinname, _ignore, _resolve = sd
            if skinname is not None:
                return skinname
        # nothing here, so assume the default skin
        stool = queryUtility(ISkinsTool)
        if stool is not None:
            return stool.getDefaultSkin()
        # and if that fails...
        return None

    @security.public
    def clearCurrentSkin(self):
        """Clear the current skin."""
        tid = get_ident()
        if tid in SKINDATA:
            del SKINDATA[tid]

    @security.public
    def setupCurrentSkin(self, REQUEST=None):
        """
        Sets up skindata so that __getattr__ can find it.

        Can NOT be called manually to change skins in the middle of a
        request! Use changeSkin for that.
        """
        if REQUEST is None:
            return
        if get_ident() in SKINDATA:
            # Already set up for this request.
            return
        skinname = self.getSkinNameFromRequest(REQUEST)
        try:
            self.changeSkin(skinname, REQUEST)
        except ConflictError:
            raise
        except Exception:
            # This shouldn't happen, even if the requested skin
            # does not exist.
            logger.exception('Unable to setupCurrentSkin()')

    def _checkId(self, id, allow_dup=0):
        """
        Override of ObjectManager._checkId().

        Allows the user to create objects with IDs that match the ID of
        a skin object.
        """
        superCheckId = SkinnableObjectManager.inheritedAttribute('_checkId')
        if not allow_dup:
            # Temporarily disable skindata.
            # Note that this depends heavily on Zope's current thread
            # behavior.
            tid = get_ident()
            sd = SKINDATA.get(tid)
            if sd is not None:
                del SKINDATA[tid]
            try:
                base = getattr(self, 'aq_base', self)
                if not hasattr(base, id):
                    # Cause _checkId to not check for duplication.
                    return superCheckId(self, id, allow_dup=1)
            finally:
                if sd is not None:
                    SKINDATA[tid] = sd
        return superCheckId(self, id, allow_dup)


InitializeClass(SkinnableObjectManager)
