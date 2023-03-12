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
"""Portal skins tool.
"""

from difflib import unified_diff

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from App.special_dtml import DTMLFile
from DateTime import DateTime
from OFS.DTMLMethod import DTMLMethod
from OFS.Folder import Folder
from OFS.Image import Image
from OFS.ObjectManager import REPLACEABLE
from Persistence import PersistentMapping
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.interface import implementer

from Products.PythonScripts.PythonScript import PythonScript

from .ActionProviderBase import ActionProviderBase
from .DirectoryView import base_ignore
from .DirectoryView import ignore
from .DirectoryView import ignore_re
from .interfaces import IMembershipTool
from .interfaces import ISkinsTool
from .interfaces import IURLTool
from .permissions import AccessContentsInformation
from .permissions import ManagePortal
from .permissions import View
from .SkinsContainer import SkinsContainer
from .utils import UniqueObject
from .utils import _dtmldir
from .utils import registerToolInterface


def modifiedOptions():
    # Remove the existing "Properties" option and add our own.
    rval = []
    for o in Folder.manage_options:
        label = o.get('label', None)
        if label != 'Properties':
            rval.append(o)
    rval[1:1] = [{'label': 'Properties', 'action': 'manage_propertiesForm'}]
    return tuple(rval)


@implementer(ISkinsTool)
class SkinsTool(UniqueObject, SkinsContainer, Folder, ActionProviderBase):

    """ This tool is used to supply skins to a portal.
    """

    id = 'portal_skins'
    meta_type = 'CMF Skins Tool'
    allow_any = 0
    cookie_persistence = 0
    default_skin = ''
    request_varname = 'portal_skin'
    selections = None

    security = ClassSecurityInfo()

    manage_options = (modifiedOptions() +
                      ({'label': 'Overview', 'action': 'manage_overview'},) +
                      ActionProviderBase.manage_options)

    def __init__(self):
        self.selections = PersistentMapping()

    def _getSelections(self):
        sels = self.selections
        if sels is None:
            # Backward compatibility.
            self.selections = sels = PersistentMapping()
        return sels

    #
    #   ZMI methods
    #
    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'manage_overview')
    manage_overview = DTMLFile('explainSkinsTool', _dtmldir)

    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'manage_propertiesForm')
    manage_propertiesForm = DTMLFile('dtml/skinProps', globals())

    # the following method override the one in FindSupport, to
    # support marking of objects used in specific skins
    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'manage_findForm')
    manage_findForm = DTMLFile('findForm', _dtmldir,
                               management_view='Find')

    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'manage_compareResults')
    manage_compareResults = DTMLFile('compareResults', _dtmldir,
                                     management_view='Compare')

    @security.protected(ManagePortal)
    def manage_skinLayers(self, chosen=(), add_skin=0, del_skin=0,
                          skinname='', skinpath='', REQUEST=None):
        """ Change the skinLayers.
        """
        sels = self._getSelections()
        if del_skin:
            for name in chosen:
                del sels[name]

        if REQUEST is not None:
            for key in sels:
                fname = 'skinpath_%s' % key
                val = REQUEST[fname]

                # if val is a list from the new lines field
                # then munge it back into a comma delimited list
                # for hysterical reasons
                if isinstance(val, list):
                    val = ','.join([layer.strip() for layer in val])

                if sels[key] != val:
                    self.testSkinPath(val)
                    sels[key] = val

        if add_skin:
            skinpath = ','.join([layer.strip() for layer in skinpath])
            self.testSkinPath(skinpath)
            sels[str(skinname)] = skinpath

        if REQUEST is not None:
            msg = 'Skins changed.'
            return self.manage_propertiesForm(self, REQUEST,
                                              management_view='Properties',
                                              manage_tabs_message=msg)

    @security.protected(ManagePortal)
    def isFirstInSkin(self, template_path, skin=None):
        """
        Is the specified template the one that would get returned
        from the current skin?
        """
        if skin is None or skin == 'None':
            skin = self.getDefaultSkin()
        template = self.restrictedTraverse(template_path)
        name = template.getId()
        skin_path = self.getSkinPath(skin)
        if not skin_path:
            return 0
        parts = list(skin_path.split(','))
        found = ''
        for part in parts:
            part = part.strip()
            if part[0] == '_':
                continue
            partob = getattr(self, part, None)
            if partob:
                skin_template = getattr(partob.aq_base, name, None)
                if skin_template:
                    found = skin_template
                    break
        if found == template:
            return 1
        else:
            return 0

    @security.protected(ManagePortal)
    def manage_properties(self, default_skin='', request_varname='',
                          allow_any=0, chosen=(), add_skin=0,
                          del_skin=0, skinname='', skinpath='',
                          cookie_persistence=0, REQUEST=None):
        """ Changes portal_skin properties. """
        self.default_skin = str(default_skin)
        self.request_varname = str(request_varname)
        self.allow_any = allow_any and 1 or 0
        self.cookie_persistence = cookie_persistence and 1 or 0
        if REQUEST is not None:
            msg = 'Properties changed.'
            return self.manage_propertiesForm(self, REQUEST,
                                              management_view='Properties',
                                              manage_tabs_message=msg)

    @security.private
    def PUT_factory(self, name, typ, body):
        """
            Dispatcher for PUT requests to non-existent IDs.  Returns
            an object of the appropriate type (or None, if we don't
            know what to do).
        """
        major, minor = typ.split('/', 1)

        if major == 'image':
            return Image(id=name, title='', file='', content_type=typ)

        if major == 'text':

            if minor == 'x-python':
                return PythonScript(id=name)

            if minor in ('html', 'xml'):
                return ZopePageTemplate(name)

            return DTMLMethod(__name__=name)

        return None

    # Make the PUT_factory replaceable
    PUT_factory__replaceable__ = REPLACEABLE

    @security.private
    def testSkinPath(self, p):
        """ Calls SkinsContainer.getSkinByPath().
        """
        self.getSkinByPath(p, raise_exc=1)

    #
    #   'SkinsContainer' interface methods
    #
    @security.protected(AccessContentsInformation)
    def getSkinPath(self, name):
        """ Convert a skin name to a skin path.
        """
        sels = self._getSelections()
        p = sels.get(name, None)
        if p is None:
            if self.allow_any:
                return name
        return p  # Can be None

    @security.protected(AccessContentsInformation)
    def getDefaultSkin(self):
        """ Get the default skin name.
        """
        return self.default_skin

    @security.protected(AccessContentsInformation)
    def getRequestVarname(self):
        """ Get the variable name to look for in the REQUEST.
        """
        return self.request_varname

    #
    #   UI methods
    #
    @security.protected(AccessContentsInformation)
    def getAllowAny(self):
        """
        Used by the management UI.  Returns a flag indicating whether
        users are allowed to use arbitrary skin paths.
        """
        return self.allow_any

    @security.protected(AccessContentsInformation)
    def getCookiePersistence(self):
        """
        Used by the management UI.  Returns a flag indicating whether
        the skins cookie is persistent or not.
        """
        return self.cookie_persistence

    @security.protected(AccessContentsInformation)
    def getSkinPaths(self):
        """
        Used by the management UI.  Returns the list of skin name to
        skin path mappings as a sorted list of tuples.
        """
        sels = self._getSelections()
        rval = []
        for key, value in sorted(sels.items()):
            rval.append((key, value))
        return rval

    #
    #   'portal_skins' interface methods
    #
    @security.public
    def getSkinSelections(self):
        """ Get the sorted list of available skin names.
        """
        sels = self._getSelections()
        rval = sorted(sels)
        return rval

    @security.protected(View)
    def updateSkinCookie(self):
        """ If needed, updates the skin cookie based on the member preference.
        """
        mtool = getUtility(IMembershipTool)
        member = mtool.getAuthenticatedMember()
        if hasattr(aq_base(member), 'getProperty'):
            mskin = member.getProperty('portal_skin')
            if mskin:
                req = getRequest()
                cookie = req.cookies.get(self.request_varname, None)
                if cookie != mskin:
                    resp = req.RESPONSE
                    utool = getUtility(IURLTool)
                    portal_path = req['BASEPATH1'] + '/' + utool(1)

                    if not self.cookie_persistence:
                        # *Don't* make the cookie persistent!
                        resp.setCookie(self.request_varname, mskin,
                                       path=portal_path)
                    else:
                        expires = (DateTime('GMT') + 365).rfc822()
                        resp.setCookie(self.request_varname, mskin,
                                       path=portal_path, expires=expires)
                    # Ensure updateSkinCookie() doesn't try again
                    # within this request.
                    req.cookies[self.request_varname] = mskin
                    req[self.request_varname] = mskin
                    return 1
        return 0

    @security.protected(View)
    def clearSkinCookie(self):
        """ Expire the skin cookie.
        """
        req = getRequest()
        resp = req.RESPONSE
        utool = getUtility(IURLTool)
        portal_path = req['BASEPATH1'] + '/' + utool(1)
        resp.expireCookie(self.request_varname, path=portal_path)

    @security.protected(ManagePortal)
    def addSkinSelection(self, skinname, skinpath, test=0, make_default=0):
        """
        Adds a skin selection.
        """
        sels = self._getSelections()
        skinpath = str(skinpath)

        # Basic precaution to make sure the stuff we want to ignore in
        # DirectoryViews gets prevented from ending up in a skin path
        path_elems = [x.strip() for x in skinpath.split(',')]
        ignored = base_ignore + ignore

        for elem in path_elems[:]:
            if elem in ignored or ignore_re.match(elem):
                path_elems.remove(elem)

        skinpath = ','.join(path_elems)

        if test:
            self.testSkinPath(skinpath)
        sels[str(skinname)] = skinpath
        if make_default:
            self.default_skin = skinname

    @security.protected(AccessContentsInformation)
    def getDiff(self, item_one_path, item_two_path, reverse=0):
        """ Return a diff between one and two.
        """
        if not reverse:
            item_one = self.unrestrictedTraverse(item_one_path)
            item_two = self.unrestrictedTraverse(item_two_path)
        else:
            item_one = self.unrestrictedTraverse(item_two_path)
            item_two = self.unrestrictedTraverse(item_one_path)

        res = unified_diff(item_one.read().splitlines(),
                           item_two.read().splitlines(),
                           item_one_path, item_two_path, '', '', lineterm='')
        return res


InitializeClass(SkinsTool)
registerToolInterface('portal_skins', ISkinsTool)
