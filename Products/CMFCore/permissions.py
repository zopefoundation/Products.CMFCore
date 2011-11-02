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
""" CMFCore product permissions. """

from AccessControl import Permissions
from AccessControl.Permission import _registeredPermissions
from AccessControl.Permission import ApplicationDefaultPermissions
from AccessControl.Permission import pname
from AccessControl.SecurityInfo import ModuleSecurityInfo


security = ModuleSecurityInfo('Products.CMFCore.permissions')

#
# General Zope permissions
#

security.declarePublic('AccessContentsInformation')
AccessContentsInformation = Permissions.access_contents_information

security.declarePublic('ChangePermissions')
ChangePermissions = Permissions.change_permissions

security.declarePublic('DeleteObjects')
DeleteObjects = Permissions.delete_objects

security.declarePublic('FTPAccess')
FTPAccess = Permissions.ftp_access

security.declarePublic('ManageProperties')
ManageProperties = Permissions.manage_properties

security.declarePublic('ManageUsers')
ManageUsers = Permissions.manage_users

security.declarePublic('UndoChanges')
UndoChanges = Permissions.undo_changes

security.declarePublic('View')
View = Permissions.view

security.declarePublic('ViewManagementScreens')
ViewManagementScreens = Permissions.view_management_screens

addPermission = None
try:
    from AccessControl.Permission import addPermission
except ImportError:
    pass

security.declarePrivate('setDefaultRoles')
def setDefaultRoles(permission, roles):
    '''
    Sets the defaults roles for a permission.
    '''
    if addPermission is not None:
        addPermission(permission, roles)
    else:
        # BBB This is in AccessControl starting in Zope 2.13
        import Products
        registered = _registeredPermissions
        if not registered.has_key(permission):
            registered[permission] = 1
            Products.__ac_permissions__=(
                Products.__ac_permissions__+((permission,(),roles),))
            mangled = pname(permission)
            setattr(ApplicationDefaultPermissions, mangled, roles)

# Note that we can only use the default Zope roles in calls to
# setDefaultRoles().  The default Zope roles are:
# Anonymous, Manager, and Owner.

#
# CMF Base Permissions
#

security.declarePublic('ListFolderContents')
ListFolderContents = 'List folder contents'
setDefaultRoles( ListFolderContents, ( 'Manager', 'Owner' ) )

security.declarePublic('ListUndoableChanges')
ListUndoableChanges = 'List undoable changes'
setDefaultRoles( ListUndoableChanges, ('Manager',) )  # + Member

security.declarePublic('AccessInactivePortalContent')
AccessInactivePortalContent = 'Access inactive portal content'
setDefaultRoles(AccessInactivePortalContent, ('Manager',))

security.declarePublic('ModifyCookieCrumblers')
ModifyCookieCrumblers = 'Modify Cookie Crumblers'
setDefaultRoles(ModifyCookieCrumblers, ('Manager',))

security.declarePublic('ReplyToItem')
ReplyToItem = 'Reply to item'
setDefaultRoles(ReplyToItem, ('Manager',))  # + Member

security.declarePublic('ManagePortal')
ManagePortal = 'Manage portal'
setDefaultRoles(ManagePortal, ('Manager',))

security.declarePublic('ModifyPortalContent')
ModifyPortalContent = 'Modify portal content'
setDefaultRoles(ModifyPortalContent, ('Manager',))

security.declarePublic('ListPortalMembers')
ListPortalMembers = 'List portal members'
setDefaultRoles( ListPortalMembers, ('Manager',) )  # + Member

security.declarePublic('AddPortalFolders')
AddPortalFolders = 'Add portal folders'
setDefaultRoles(AddPortalFolders, ('Owner','Manager'))  # + Member

security.declarePublic('AddPortalContent')
AddPortalContent = 'Add portal content'
setDefaultRoles(AddPortalContent, ('Owner','Manager',))  # + Member

security.declarePublic('AddPortalMember')
AddPortalMember = 'Add portal member'
setDefaultRoles(AddPortalMember, ('Anonymous', 'Manager',))

security.declarePublic('SetOwnPassword')
SetOwnPassword = 'Set own password'
setDefaultRoles(SetOwnPassword, ('Manager',))  # + Member

security.declarePublic('SetOwnProperties')
SetOwnProperties = 'Set own properties'
setDefaultRoles(SetOwnProperties, ('Manager',))  # + Member

security.declarePublic('ChangeLocalRoles')
ChangeLocalRoles = 'Change local roles'
setDefaultRoles(ChangeLocalRoles, ('Owner', 'Manager'))

security.declarePublic('MailForgottenPassword')
MailForgottenPassword = 'Mail forgotten password'
setDefaultRoles(MailForgottenPassword, ('Anonymous', 'Manager',))


#
# Workflow Permissions
#

security.declarePublic('RequestReview')
RequestReview = 'Request review'
setDefaultRoles(RequestReview, ('Owner', 'Manager',))

security.declarePublic('ReviewPortalContent')
ReviewPortalContent = 'Review portal content'
setDefaultRoles(ReviewPortalContent, ('Manager',))  # + Reviewer

