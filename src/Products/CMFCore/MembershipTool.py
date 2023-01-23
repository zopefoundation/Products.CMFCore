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
""" Basic membership tool.
"""

import logging
from warnings import warn

from AccessControl.class_init import InitializeClass
from AccessControl.requestmethod import postonly
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.users import nobody
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.Dialogs import MessageDialog
from App.special_dtml import DTMLFile
from OFS.Folder import Folder
from Persistence import PersistentMapping
from ZODB.POSException import ConflictError
from zope.component import getUtility
from zope.component import queryUtility
from zope.component.interfaces import IFactory
from zope.globalrequest import getRequest
from zope.interface import implementedBy
from zope.interface import implementer
from ZPublisher.BaseRequest import RequestContainer

from .exceptions import AccessControl_Unauthorized
from .exceptions import BadRequest
from .interfaces import ICookieCrumbler
from .interfaces import IMemberDataTool
from .interfaces import IMembershipTool
from .interfaces import IRegistrationTool
from .interfaces import ISiteRoot
from .interfaces import ITypesTool
from .permissions import AccessContentsInformation
from .permissions import ChangeLocalRoles
from .permissions import ListPortalMembers
from .permissions import ManagePortal
from .permissions import ManageUsers
from .permissions import SetOwnPassword
from .permissions import View
from .PortalFolder import PortalFolder
from .utils import Message as _
from .utils import UniqueObject
from .utils import _checkPermission
from .utils import _dtmldir
from .utils import registerToolInterface


logger = logging.getLogger('CMFCore.MembershipTool')


@implementer(IMembershipTool)
class MembershipTool(UniqueObject, Folder):

    """ This tool accesses member data through an acl_users object.

    It can be replaced with something that accesses member data in a
    different way.
    """

    id = 'portal_membership'
    meta_type = 'CMF Membership Tool'
    zmi_icon = 'fa fa-users'
    memberareaCreationFlag = 1
    _HOME_FOLDER_FACTORY_NAME = 'cmf.folder.home.bbb1'

    security = ClassSecurityInfo()

    manage_options = (
        ({'label': 'Configuration', 'action': 'manage_mapRoles'},
         {'label': 'Overview', 'action': 'manage_overview'}) +
        Folder.manage_options)

    #
    #   ZMI methods
    #
    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'manage_overview')
    manage_overview = DTMLFile('explainMembershipTool', _dtmldir)

    #
    #   'portal_membership' interface methods
    #
    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'manage_mapRoles')
    manage_mapRoles = DTMLFile('membershipRolemapping', _dtmldir)

    @security.protected(SetOwnPassword)
    @postonly
    def setPassword(self, password, domains=None, REQUEST=None):
        """Allows the authenticated member to set his/her own password.
        """
        if not self.isAnonymousUser():
            member = self.getAuthenticatedMember()
            rtool = queryUtility(IRegistrationTool)
            if rtool is not None:
                failMessage = rtool.testPasswordValidity(password)
                if failMessage is not None:
                    raise BadRequest(failMessage)
            member.setSecurityProfile(password=password, domains=domains)
        else:
            raise BadRequest('Not logged in.')

    @security.public
    def getAuthenticatedMember(self):
        """
        Returns the currently authenticated member object
        or the Anonymous User.  Never returns None.
        """
        u = getSecurityManager().getUser()
        if u is None:
            u = nobody
        return self.wrapUser(u)

    @security.private
    def wrapUser(self, u, wrap_anon=0):
        """ Set up the correct acquisition wrappers for a user object.

        Provides an opportunity for a portal_memberdata tool to retrieve and
        store member data independently of the user object.
        """
        b = getattr(u, 'aq_base', None)
        if b is None:
            # u isn't wrapped at all.  Wrap it in self.acl_users.
            b = u
            u = u.__of__(self.acl_users)
        if (b is nobody and not wrap_anon) or hasattr(b, 'getMemberId'):
            # This user is either not recognized by acl_users or it is
            # already registered with something that implements the
            # member data tool at least partially.
            return u

        # Apply any role mapping if we have it
        if hasattr(self, 'role_map'):
            for portal_role in self.role_map:
                if (self.role_map.get(portal_role) in u.roles and
                        portal_role not in u.roles):
                    u.roles.append(portal_role)

        mdtool = queryUtility(IMemberDataTool)
        if mdtool is not None:
            try:
                u = mdtool.wrapUser(u)
            except ConflictError:
                raise
            except Exception:
                logger.exception('Error during wrapUser')
        return u

    @security.protected(ManagePortal)
    def getPortalRoles(self):
        """
        Return all local roles defined by the portal itself,
        which means roles that are useful and understood
        by the portal object
        """
        parent = self.aq_inner.aq_parent
        roles = list(parent.userdefined_roles())

        # This is *not* a local role in the portal but used by it
        roles.append('Manager')
        roles.append('Owner')

        return roles

    @security.protected(ManagePortal)
    @postonly
    def setRoleMapping(self, portal_role, userfolder_role, REQUEST=None):
        """
        set the mapping of roles between roles understood by
        the portal and roles coming from outside user sources
        """
        if not hasattr(self, 'role_map'):
            self.role_map = PersistentMapping()

        if len(userfolder_role) < 1:
            del self.role_map[portal_role]
        else:
            self.role_map[portal_role] = userfolder_role

        return MessageDialog(
               title='Mapping updated',
               message='The Role mappings have been updated',
               action='manage_mapRoles')

    @security.protected(ManagePortal)
    def getMappedRole(self, portal_role):
        """
        returns a role name if the portal role is mapped to
        something else or an empty string if it is not
        """
        if hasattr(self, 'role_map'):
            return self.role_map.get(portal_role, '')
        else:
            return ''

    @security.public
    def getMembersFolder(self):
        """ Get the members folder object.
        """
        parent = aq_parent(aq_inner(self))
        members_folder = getattr(parent, 'Members', None)
        if members_folder is None:
            return None
        request_container = RequestContainer(REQUEST=getRequest())
        return members_folder.__of__(request_container)

    @security.protected(ManagePortal)
    def getMemberareaCreationFlag(self):
        """
        Returns the flag indicating whether the membership tool
        will create a member area if an authenticated user from
        an underlying user folder logs in first without going
        through the join process
        """
        return self.memberareaCreationFlag

    @security.protected(ManagePortal)
    def setMemberareaCreationFlag(self):
        """
        sets the flag indicating whether the membership tool
        will create a member area if an authenticated user from
        an underlying user folder logs in first without going
        through the join process
        """
        if not hasattr(self, 'memberareaCreationFlag'):
            self.memberareaCreationFlag = 0

        if self.memberareaCreationFlag == 0:
            self.memberareaCreationFlag = 1
        else:
            self.memberareaCreationFlag = 0

        return MessageDialog(
               title='Member area creation flag changed',
               message='Member area creation flag has been updated',
               action='manage_mapRoles')

    @security.public
    def createMemberArea(self, member_id=''):
        """ Create a member area for 'member_id' or authenticated user.
        """
        if not self.getMemberareaCreationFlag():
            return None
        members = self.getMembersFolder()
        if members is None:
            return None
        if self.isAnonymousUser():
            return None
        if member_id:
            if not self.isMemberAccessAllowed(member_id):
                return None
            member = self.getMemberById(member_id)
            if member is None:
                return None
        else:
            member = self.getAuthenticatedMember()
            member_id = member.getId()
        if hasattr(aq_base(members), member_id):
            return None

        factory_name = self._HOME_FOLDER_FACTORY_NAME
        portal_type_name = 'Folder'
        ttool = queryUtility(ITypesTool)
        if ttool is not None:
            portal_type = ttool.getTypeInfo('Home Folder')
            if portal_type is not None:
                factory_name = portal_type.factory
                portal_type_name = portal_type.getId()

        factory = getUtility(IFactory, factory_name)
        obj = factory(id=member_id)
        obj._setPortalTypeName(portal_type_name)
        members._setObject(member_id, obj)
        f = members._getOb(member_id)
        f.changeOwnership(member)
        return f

    security.declarePublic('createMemberarea')  # NOQA: flake8: D001
    createMemberarea = createMemberArea

    @security.protected(ManageUsers)
    @postonly
    def deleteMemberArea(self, member_id, REQUEST=None):
        """ Delete member area of member specified by member_id.
        """
        members = self.getMembersFolder()
        if not members:
            return 0
        if hasattr(aq_base(members), member_id):
            members.manage_delObjects(member_id)
            return 1
        else:
            return 0

    @security.public
    def isAnonymousUser(self):
        """
        Returns 1 if the user is not logged in.
        """
        u = getSecurityManager().getUser()
        if u is None or u.getUserName() == 'Anonymous User':
            return 1
        return 0

    @security.public
    def checkPermission(self, permissionName, object, subobjectName=None):
        """
        Checks whether the current user has the given permission on
        the given object or subobject.
        """
        if subobjectName is not None:
            object = getattr(object, subobjectName)
        return _checkPermission(permissionName, object)

    @security.protected(ManageUsers)
    def isMemberAccessAllowed(self, member_id):
        """Check if the authenticated user is this member or an user manager.
        """
        sm = getSecurityManager()
        user = sm.getUser()
        if user is None:
            return False
        if member_id == user.getId():
            return True
        return sm.checkPermission(ManageUsers, self)

    @security.public
    def credentialsChanged(self, password, REQUEST=None):
        """
        Notifies the authentication mechanism that this user has changed
        passwords.  This can be used to update the authentication cookie.
        Note that this call should *not* cause any change at all to user
        databases.
        """
        if not self.isAnonymousUser():
            user = getSecurityManager().getUser()
            name = user.getUserName()
            # this really does need to be the user name, and not the user id,
            # because we're dealing with authentication credentials
            cctool = queryUtility(ICookieCrumbler)
            if cctool is not None:
                cctool.credentialsChanged(user, name, password, REQUEST)

    @security.protected(ManageUsers)
    def getMemberById(self, id):
        """
        Returns the given member.
        """
        user = self._huntUser(id, self)
        if user is not None:
            user = self.wrapUser(user)
        return user

    def _huntUserFolder(self, member_id, context):
        """Find userfolder containing user in the hierarchy
           starting from context
        """
        uf = context.acl_users
        while uf is not None:
            user = uf.getUserById(member_id)
            if user is not None:
                return uf
            container = aq_parent(aq_inner(uf))
            parent = aq_parent(aq_inner(container))
            uf = getattr(parent, 'acl_users', None)
        return None

    def _huntUser(self, member_id, context):
        """Find user in the hierarchy of userfolders
           starting from context
        """
        uf = self._huntUserFolder(member_id, context)
        if uf is not None:
            return uf.getUserById(member_id).__of__(uf)

    def __getPUS(self):
        """ Retrieve the nearest user folder
        """
        warn('__getPUS is deprecated and will be removed in CMF 2.4, '
             'please acquire "acl_users" instead.', DeprecationWarning,
             stacklevel=2)
        return self.acl_users

    @security.protected(ManageUsers)
    def listMemberIds(self):
        """Lists the ids of all members.  This may eventually be
        replaced with a set of methods for querying pieces of the
        list rather than the entire list at once.
        """
        user_folder = self.acl_users
        return [x.getId() for x in user_folder.getUsers()]

    @security.protected(ManageUsers)
    def listMembers(self):
        """Gets the list of all members.
        """
        return list(map(self.wrapUser, self.acl_users.getUsers()))

    @security.protected(ListPortalMembers)
    def searchMembers(self, search_param, search_term):
        """ Search the membership """
        mdtool = queryUtility(IMemberDataTool)
        if mdtool is not None:
            return mdtool.searchMemberData(search_param, search_term)
        return None

    @security.protected(View)
    def getCandidateLocalRoles(self, obj):
        """ What local roles can I assign?
        """
        member = self.getAuthenticatedMember()
        member_roles = member.getRolesInContext(obj)
        if _checkPermission(ManageUsers, obj):
            local_roles = self.getPortalRoles()
            if 'Manager' not in member_roles:
                local_roles.remove('Manager')
        else:
            local_roles = [role for role in member_roles
                           if role not in ('Member', 'Authenticated')]
        return tuple(sorted(local_roles))

    @security.protected(View)
    @postonly
    def setLocalRoles(self, obj, member_ids, member_role, reindex=1,
                      REQUEST=None):
        """ Add local roles on an item.
        """
        if _checkPermission(ChangeLocalRoles, obj) and \
           member_role in self.getCandidateLocalRoles(obj):
            for member_id in member_ids:
                roles = list(obj.get_local_roles_for_userid(userid=member_id))

                if member_role not in roles:
                    roles.append(member_role)
                    obj.manage_setLocalRoles(member_id, roles)

        if reindex and hasattr(aq_base(obj), 'reindexObjectSecurity'):
            obj.reindexObjectSecurity()

    @security.protected(View)
    @postonly
    def deleteLocalRoles(self, obj, member_ids, reindex=1, recursive=0,
                         REQUEST=None):
        """ Delete local roles of specified members.
        """
        if _checkPermission(ChangeLocalRoles, obj):
            for member_id in member_ids:
                if obj.get_local_roles_for_userid(userid=member_id):
                    obj.manage_delLocalRoles(userids=member_ids)
                    break

        if recursive and hasattr(aq_base(obj), 'contentValues'):
            for subobj in obj.contentValues():
                self.deleteLocalRoles(subobj, member_ids, 0, 1)

        if reindex and hasattr(aq_base(obj), 'reindexObjectSecurity'):
            # reindexObjectSecurity is always recursive
            obj.reindexObjectSecurity()

    @security.private
    def addMember(self, id, password, roles, domains, properties=None):
        """Adds a new member to the user folder.  Security checks will have
        already been performed.  Called by portal_registration.
        """
        self.acl_users._doAddUser(id, password, roles, domains)

        if properties is not None:
            member = self.getMemberById(id)
            member.setMemberProperties(properties)

    @security.protected(ManageUsers)
    @postonly
    def deleteMembers(self, member_ids, delete_memberareas=1,
                      delete_localroles=1, REQUEST=None):
        """ Delete members specified by member_ids.
        """
        # Delete members in acl_users.
        acl_users = self.acl_users
        if _checkPermission(ManageUsers, acl_users):
            if isinstance(member_ids, str):
                member_ids = (member_ids,)
            member_ids = list(member_ids)
            for member_id in member_ids[:]:
                if not acl_users.getUserById(member_id, None):
                    member_ids.remove(member_id)
            try:
                acl_users.userFolderDelUsers(member_ids)
            except (AttributeError, NotImplementedError):
                raise NotImplementedError('The underlying User Folder '
                                          "doesn't support deleting members.")
        else:
            raise AccessControl_Unauthorized("You need the 'Manage users' "
                                             'permission for the underlying '
                                             'User Folder.')

        # Delete member data in portal_memberdata.
        mdtool = queryUtility(IMemberDataTool)
        if mdtool is not None:
            for member_id in member_ids:
                mdtool.deleteMemberData(member_id)

        # Delete members' home folders including all content items.
        if delete_memberareas:
            for member_id in member_ids:
                self.deleteMemberArea(member_id)

        # Delete members' local roles.
        if delete_localroles:
            self.deleteLocalRoles(getUtility(ISiteRoot), member_ids,
                                  reindex=1, recursive=1)

        return tuple(member_ids)

    @security.public
    def getHomeFolder(self, id=None, verifyPermission=0):
        """Returns a member's home folder object or None.
        Set verifyPermission to 1 to return None when the user
        doesn't have the View permission on the folder.
        """
        return None

    @security.public
    def getHomeUrl(self, id=None, verifyPermission=0):
        """Returns the URL to a member's home folder or None.
        Set verifyPermission to 1 to return None when the user
        doesn't have the View permission on the folder.
        """
        return None


InitializeClass(MembershipTool)
registerToolInterface('portal_membership', IMembershipTool)


@implementer(IFactory)
class HomeFolderFactoryBase:

    """Creates a home folder.
    """

    title = _('Home Folder')
    description = _('A home folder for portal members.')

    def __call__(self, id, title=None, *args, **kw):
        if title is None:
            title = f"{id}'s Home"
        item = PortalFolder(id, title, *args, **kw)
        item.manage_setLocalRoles(id, ['Owner'])
        return item

    def getInterfaces(self):
        return implementedBy(PortalFolder)


class _BBBHomeFolderFactory(HomeFolderFactoryBase):

    """Creates a home folder.
    """

    description = _('Classic CMFCore home folder for portal members.')

    def __call__(self, id, title=None, *args, **kw):
        item = super().__call__(id, title=title, *args, **kw)

        item.manage_permission(View,
                               ['Owner', 'Manager', 'Reviewer'], 0)
        item.manage_permission(AccessContentsInformation,
                               ['Owner', 'Manager', 'Reviewer'], 0)
        return item


BBBHomeFolderFactory = _BBBHomeFolderFactory()
