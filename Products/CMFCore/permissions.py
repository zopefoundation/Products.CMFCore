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


deprecated('Please use addPermission from AccessControl.Permission.',
           setDefaultRoles='AccessControl.Permission:addPermission')

security = ModuleSecurityInfo('Products.CMFCore.permissions')

#
# General Zope permissions
#

security.declarePublic('AccessContentsInformation')  # NOQA: flake8: D001
AccessContentsInformation = Permissions.access_contents_information

security.declarePublic('ChangePermissions')  # NOQA: flake8: D001
ChangePermissions = Permissions.change_permissions

security.declarePublic('DeleteObjects')  # NOQA: flake8: D001
DeleteObjects = Permissions.delete_objects

security.declarePublic('FTPAccess')  # NOQA: flake8: D001
FTPAccess = Permissions.ftp_access

security.declarePublic('ManageProperties')  # NOQA: flake8: D001
ManageProperties = Permissions.manage_properties

security.declarePublic('ManageUsers')  # NOQA: flake8: D001
ManageUsers = Permissions.manage_users

security.declarePublic('UndoChanges')  # NOQA: flake8: D001
UndoChanges = Permissions.undo_changes

security.declarePublic('View')  # NOQA: flake8: D001
View = Permissions.view

security.declarePublic('ViewManagementScreens')  # NOQA: flake8: D001
ViewManagementScreens = Permissions.view_management_screens


# Note that we can only use the default Zope roles in calls to
# addPermission().  The default Zope roles are:
# Anonymous, Manager, and Owner.

#
# CMF Base Permissions
#

security.declarePublic('ListFolderContents')  # NOQA: flake8: D001
ListFolderContents = 'List folder contents'
addPermission(ListFolderContents, ('Manager', 'Owner'))

security.declarePublic('ListUndoableChanges')  # NOQA: flake8: D001
ListUndoableChanges = 'List undoable changes'
addPermission(ListUndoableChanges, ('Manager',))  # + Member

security.declarePublic('AccessInactivePortalContent')  # NOQA: flake8: D001
AccessInactivePortalContent = 'Access inactive portal content'
addPermission(AccessInactivePortalContent, ('Manager',))

security.declarePublic('ModifyCookieCrumblers')  # NOQA: flake8: D001
ModifyCookieCrumblers = 'Modify Cookie Crumblers'
addPermission(ModifyCookieCrumblers, ('Manager',))

security.declarePublic('ReplyToItem')  # NOQA: flake8: D001
ReplyToItem = 'Reply to item'
addPermission(ReplyToItem, ('Manager',))  # + Member

security.declarePublic('ManagePortal')  # NOQA: flake8: D001
ManagePortal = 'Manage portal'
addPermission(ManagePortal, ('Manager',))

security.declarePublic('ModifyPortalContent')  # NOQA: flake8: D001
ModifyPortalContent = 'Modify portal content'
addPermission(ModifyPortalContent, ('Manager',))

security.declarePublic('ListPortalMembers')  # NOQA: flake8: D001
ListPortalMembers = 'List portal members'
addPermission(ListPortalMembers, ('Manager',))  # + Member

security.declarePublic('AddPortalFolders')  # NOQA: flake8: D001
AddPortalFolders = 'Add portal folders'
addPermission(AddPortalFolders, ('Owner', 'Manager'))  # + Member

security.declarePublic('AddPortalContent')  # NOQA: flake8: D001
AddPortalContent = 'Add portal content'
addPermission(AddPortalContent, ('Owner', 'Manager'))  # + Member

security.declarePublic('AddPortalMember')  # NOQA: flake8: D001
AddPortalMember = 'Add portal member'
addPermission(AddPortalMember, ('Anonymous', 'Manager'))

security.declarePublic('SetOwnPassword')  # NOQA: flake8: D001
SetOwnPassword = 'Set own password'
addPermission(SetOwnPassword, ('Manager',))  # + Member

security.declarePublic('SetOwnProperties')  # NOQA: flake8: D001
SetOwnProperties = 'Set own properties'
addPermission(SetOwnProperties, ('Manager',))  # + Member

security.declarePublic('ChangeLocalRoles')  # NOQA: flake8: D001
ChangeLocalRoles = 'Change local roles'
addPermission(ChangeLocalRoles, ('Owner', 'Manager'))

security.declarePublic('MailForgottenPassword')  # NOQA: flake8: D001
MailForgottenPassword = 'Mail forgotten password'
addPermission(MailForgottenPassword, ('Anonymous', 'Manager'))


#
# Workflow Permissions
#

security.declarePublic('RequestReview')  # NOQA: flake8: D001
RequestReview = 'Request review'
addPermission(RequestReview, ('Owner', 'Manager'))

security.declarePublic('ReviewPortalContent')  # NOQA: flake8: D001
ReviewPortalContent = 'Review portal content'
addPermission(ReviewPortalContent, ('Manager',))  # + Reviewer
