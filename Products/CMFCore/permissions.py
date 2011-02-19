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
""" CMFCore product permissions.
"""

from AccessControl import Permissions
from AccessControl.Permission import addPermission
from AccessControl.SecurityInfo import ModuleSecurityInfo
from zope.deferredimport import deprecated

deprecated("Please use addPermission from AccessControl.Permission.",
    setDefaultRoles='AccessControl.Permission:addPermission')

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


# Note that we can only use the default Zope roles in calls to
# addPermission().  The default Zope roles are:
# Anonymous, Manager, and Owner.

#
# CMF Base Permissions
#

security.declarePublic('ListFolderContents')
ListFolderContents = 'List folder contents'
addPermission(ListFolderContents, ('Manager', 'Owner'))

security.declarePublic('ListUndoableChanges')
ListUndoableChanges = 'List undoable changes'
addPermission(ListUndoableChanges, ('Manager',))  # + Member

security.declarePublic('AccessInactivePortalContent')
AccessInactivePortalContent = 'Access inactive portal content'
addPermission(AccessInactivePortalContent, ('Manager',))

security.declarePublic('ModifyCookieCrumblers')
ModifyCookieCrumblers = 'Modify Cookie Crumblers'
addPermission(ModifyCookieCrumblers, ('Manager',))

security.declarePublic('ReplyToItem')
ReplyToItem = 'Reply to item'
addPermission(ReplyToItem, ('Manager',))  # + Member

security.declarePublic('ManagePortal')
ManagePortal = 'Manage portal'
addPermission(ManagePortal, ('Manager',))

security.declarePublic('ModifyPortalContent')
ModifyPortalContent = 'Modify portal content'
addPermission(ModifyPortalContent, ('Manager',))

security.declarePublic('ListPortalMembers')
ListPortalMembers = 'List portal members'
addPermission(ListPortalMembers, ('Manager',))  # + Member

security.declarePublic('AddPortalFolders')
AddPortalFolders = 'Add portal folders'
addPermission(AddPortalFolders, ('Owner', 'Manager'))  # + Member

security.declarePublic('AddPortalContent')
AddPortalContent = 'Add portal content'
addPermission(AddPortalContent, ('Owner', 'Manager',))  # + Member

security.declarePublic('AddPortalMember')
AddPortalMember = 'Add portal member'
addPermission(AddPortalMember, ('Anonymous', 'Manager',))

security.declarePublic('SetOwnPassword')
SetOwnPassword = 'Set own password'
addPermission(SetOwnPassword, ('Manager',))  # + Member

security.declarePublic('SetOwnProperties')
SetOwnProperties = 'Set own properties'
addPermission(SetOwnProperties, ('Manager',))  # + Member

security.declarePublic('ChangeLocalRoles')
ChangeLocalRoles = 'Change local roles'
addPermission(ChangeLocalRoles, ('Owner', 'Manager'))

security.declarePublic('MailForgottenPassword')
MailForgottenPassword = 'Mail forgotten password'
addPermission(MailForgottenPassword, ('Anonymous', 'Manager',))


#
# Workflow Permissions
#

security.declarePublic('RequestReview')
RequestReview = 'Request review'
addPermission(RequestReview, ('Owner', 'Manager',))

security.declarePublic('ReviewPortalContent')
ReviewPortalContent = 'Review portal content'
addPermission(ReviewPortalContent, ('Manager',))  # + Reviewer
