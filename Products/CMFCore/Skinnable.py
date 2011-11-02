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
the browser request.  Skins are stored in a fixed-name subobject. """

import logging
from thread import get_ident
from warnings import warn

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from OFS.ObjectManager import ObjectManager
from ZODB.POSException import ConflictError

logger = logging.getLogger('CMFCore.Skinnable')


_MARKER = object()  # Create a new marker object.


SKINDATA = {} # mapping thread-id -> (skinobj, skinname, ignore, resolve)

class SkinDataCleanup:
    """Cleanup at the end of the request."""
    def __init__(self, tid):
        self.tid = tid
    def __del__(self):
        tid = self.tid
        # Be extra careful in __del__
        if SKINDATA is not None:
            if SKINDATA.has_key(tid):
                del SKINDATA[tid]


class SkinnableObjectManager(ObjectManager):

    security = ClassSecurityInfo()

    security.declarePrivate('getSkinsFolderName')
    def getSkinsFolderName(self):
        # Not implemented.
        return None

    def __getattr__(self, name):
        '''
        Looks for the name in an object with wrappers that only reach
        up to the root skins folder.

        This should be fast, flexible, and predictable.
        '''
        if not name.startswith('_') and not name.startswith('aq_'):
            sd = SKINDATA.get(get_ident())
            if sd is not None:
                ob, skinname, ignore, resolve = sd
                if not name in ignore:
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
        raise AttributeError, name

    security.declarePrivate('getSkin')
    def getSkin(self, name=None):
        """Returns the requested skin.
        """
        skinob = None
        sfn = self.getSkinsFolderName()

        if sfn is not None:
            sf = getattr(self, sfn, None)
            if sf is not None:
               if name is not None:
                   skinob = sf.getSkinByName(name)
               if skinob is None:
                   skinob = sf.getSkinByName(sf.getDefaultSkin())
                   if skinob is None:
                       skinob = sf.getSkinByPath('')
        return skinob

    security.declarePublic('getSkinNameFromRequest')
    def getSkinNameFromRequest(self, REQUEST=None):
        '''Returns the skin name from the Request.'''
        if REQUEST is None:
            return None
        sfn = self.getSkinsFolderName()
        if sfn is not None:
            sf = getattr(self, sfn, None)
            if sf is not None:
                return REQUEST.get(sf.getRequestVarname(), None)

    security.declarePublic('changeSkin')
    def changeSkin(self, skinname, REQUEST=_MARKER):
        '''Change the current skin.

        Can be called manually, allowing the user to change
        skins in the middle of a request.
        '''
        skinobj = self.getSkin(skinname)
        if skinobj is not None:
            tid = get_ident()
            SKINDATA[tid] = (skinobj, skinname, {}, {})
            if REQUEST is _MARKER:
                REQUEST = getattr(self, 'REQUEST', None)
                warn("changeSkin should be called with 'REQUEST' as second "
                     "argument. The BBB code will be removed in CMF 2.3.",
                     DeprecationWarning, stacklevel=2)
            if REQUEST is not None:
                REQUEST._hold(SkinDataCleanup(tid))

    security.declarePublic('getCurrentSkinName')
    def getCurrentSkinName(self):
        '''Return the current skin name.
        '''
        sd = SKINDATA.get(get_ident())
        if sd is not None:
            ob, skinname, ignore, resolve = sd
            if skinname is not None:
                return skinname
        # nothing here, so assume the default skin
        sfn = self.getSkinsFolderName()
        if sfn is not None:
            sf = getattr(self, sfn, None)
            if sf is not None:
                return sf.getDefaultSkin()
        # and if that fails...
        return None

    security.declarePublic('clearCurrentSkin')
    def clearCurrentSkin(self):
        """Clear the current skin."""
        tid = get_ident()
        if SKINDATA.has_key(tid):
            del SKINDATA[tid]

    security.declarePublic('setupCurrentSkin')
    def setupCurrentSkin(self, REQUEST=_MARKER):
        '''
        Sets up skindata so that __getattr__ can find it.

        Can NOT be called manually to change skins in the middle of a
        request! Use changeSkin for that.
        '''
        if REQUEST is _MARKER:
            REQUEST = getattr(self, 'REQUEST', None)
            warn("setupCurrentSkin should be called with 'REQUEST' as "
                 "argument. The BBB code will be removed in CMF 2.3.",
                 DeprecationWarning, stacklevel=2)
        if REQUEST is None:
            # self is not fully wrapped at the moment.  Don't
            # change anything.
            return
        if SKINDATA.has_key(get_ident()):
            # Already set up for this request.
            return
        skinname = self.getSkinNameFromRequest(REQUEST)
        try:
            self.changeSkin(skinname, REQUEST)
        except ConflictError:
            raise
        except:
            # This shouldn't happen, even if the requested skin
            # does not exist.
            logger.exception("Unable to setupCurrentSkin()")

    def _checkId(self, id, allow_dup=0):
        '''
        Override of ObjectManager._checkId().

        Allows the user to create objects with IDs that match the ID of
        a skin object.
        '''
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
                base = getattr(self,  'aq_base', self)
                if not hasattr(base, id):
                    # Cause _checkId to not check for duplication.
                    return superCheckId(self, id, allow_dup=1)
            finally:
                if sd is not None:
                    SKINDATA[tid] = sd
        return superCheckId(self, id, allow_dup)

InitializeClass(SkinnableObjectManager)
