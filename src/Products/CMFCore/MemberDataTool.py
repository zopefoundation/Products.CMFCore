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
""" Basic member data tool.
"""

from AccessControl.class_init import InitializeClass
from AccessControl.interfaces import IUser
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.special_dtml import DTMLFile
from BTrees.OOBTree import OOBTree
from DateTime.DateTime import DateTime
from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import SimpleItem
from Persistence import Persistent
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface import implementer
from ZPublisher.Converters import type_converters

from .exceptions import BadRequest
from .interfaces import IMember
from .interfaces import IMemberDataTool
from .interfaces import IMembershipTool
from .interfaces import IRegistrationTool
from .permissions import ManagePortal
from .permissions import SetOwnProperties
from .permissions import ViewManagementScreens
from .utils import UniqueObject
from .utils import _dtmldir
from .utils import registerToolInterface


_marker = []  # Create a new marker object.


@implementer(IMemberDataTool)
class MemberDataTool(UniqueObject, SimpleItem, PropertyManager):

    """ This tool wraps user objects, making them act as Member objects.
    """

    id = 'portal_memberdata'
    meta_type = 'CMF Member Data Tool'
    zmi_icon = 'fas fa-database'
    _properties = (
        {'id': 'email', 'type': 'string', 'mode': 'w'},
        {'id': 'portal_skin', 'type': 'string', 'mode': 'w'},
        {'id': 'listed', 'type': 'boolean', 'mode': 'w'},
        {'id': 'login_time', 'type': 'date', 'mode': 'w'},
        {'id': 'last_login_time', 'type': 'date', 'mode': 'w'},
        {'id': 'fullname', 'type': 'string', 'mode': 'w'},
        )
    email = ''
    fullname = ''
    last_login_time = DateTime('1970/01/01 00:00:00 UTC')  # epoch
    listed = False
    login_time = DateTime('1970/01/01 00:00:00 UTC')  # epoch
    portal_skin = ''

    security = ClassSecurityInfo()

    manage_options = (
        ({'label': 'Overview', 'action': 'manage_overview'},
         {'label': 'Contents', 'action': 'manage_showContents'}) +
        PropertyManager.manage_options +
        SimpleItem.manage_options)

    #
    #   ZMI methods
    #
    security.declareProtected(ManagePortal, 'manage_overview')
    manage_overview = DTMLFile('explainMemberDataTool', _dtmldir)

    security.declareProtected(ViewManagementScreens, 'manage_showContents')
    manage_showContents = DTMLFile('memberdataContents', _dtmldir)

    def __init__(self):
        self._members = OOBTree()

    #
    #   'portal_memberdata' interface methods
    #
    @security.private
    def getMemberDataContents(self):
        """
        Return the number of members stored in the _members
        BTree and some other useful info
        """
        mtool = getUtility(IMembershipTool)
        members = self._members
        user_list = mtool.listMemberIds()
        member_list = list(members)
        member_count = len(member_list)
        orphan_count = 0

        for member in member_list:
            if member not in user_list:
                orphan_count = orphan_count + 1

        return [{'member_count': member_count,
                 'orphan_count': orphan_count}]

    @security.private
    def searchMemberData(self, search_param, search_term, attributes=()):
        """ Search members. """
        res = []

        if not search_param:
            return res

        mtool = getUtility(IMembershipTool)

        if len(attributes) == 0:
            attributes = ('id', 'email')

        if search_param == 'username':
            search_param = 'id'

        for user_id in self._members:
            u = mtool.getMemberById(user_id)

            if u is not None:
                memberProperty = u.getProperty
                searched = memberProperty(search_param, None)

                if searched is not None and searched.find(search_term) != -1:
                    user_data = {}

                    for desired in attributes:
                        if desired == 'id':
                            user_data['username'] = memberProperty(desired, '')
                        else:
                            user_data[desired] = memberProperty(desired, '')

                    res.append(user_data)

        return res

    @security.private
    def searchMemberDataContents(self, search_param, search_term):
        """ Search members. This method will be deprecated soon. """
        res = []

        if search_param == 'username':
            search_param = 'id'

        mtool = getUtility(IMembershipTool)

        for member_id in self._members:

            user_wrapper = mtool.getMemberById(member_id)

            if user_wrapper is not None:
                memberProperty = user_wrapper.getProperty
                searched = memberProperty(search_param, None)

                if searched is not None and searched.find(search_term) != -1:

                    res.append({'username': memberProperty('id'),
                                'email': memberProperty('email', '')})
        return res

    @security.private
    def pruneMemberDataContents(self):
        """ Delete data contents of all members not listet in acl_users.
        """
        mtool = getUtility(IMembershipTool)
        members = self._members
        user_list = mtool.listMemberIds()

        for member_id in list(members):
            if member_id not in user_list:
                del members[member_id]

    @security.private
    def wrapUser(self, u):
        """
        If possible, returns the Member object that corresponds
        to the given User object.
        """
        return getMultiAdapter((u, self), IMember)

    @security.private
    def registerMemberData(self, m, id):
        """ Add the given member data to the _members btree.
        """
        self._members[id] = aq_base(m)

    @security.private
    def deleteMemberData(self, member_id):
        """ Delete member data of specified member.
        """
        members = self._members
        if member_id in members:
            del members[member_id]
            return 1
        else:
            return 0


InitializeClass(MemberDataTool)
registerToolInterface('portal_memberdata', IMemberDataTool)


class MemberData(Persistent):

    def __init__(self, id):
        self.id = id


@implementer(IMember)
class MemberAdapter:

    """Member data adapter.
    """

    adapts(IUser, IMemberDataTool)

    security = ClassSecurityInfo()

    def __init__(self, user, tool):
        self._user = user
        self._tool = tool
        self.__parent__ = aq_parent(aq_inner(user))
        id = user.getId()
        self._md = tool._members.get(id, MemberData(id))

    @security.private
    def notifyModified(self):
        # Links self to parent for full persistence.
        self._tool.registerMemberData(self._md, self.getId())

    @security.public
    def getUser(self):
        return self._user

    @security.public
    def getMemberId(self):
        return self._user.getId()

    @security.protected(SetOwnProperties)
    def setProperties(self, properties=None, **kw):
        """Allows the authenticated member to set his/her own properties.
        Accepts either keyword arguments or a mapping for the "properties"
        argument.
        """
        mtool = getUtility(IMembershipTool)
        if not mtool.isMemberAccessAllowed(self._user.getId()):
            raise BadRequest('Only own properties can be set.')
        if properties is None:
            properties = kw
        rtool = queryUtility(IRegistrationTool)
        if rtool is not None:
            failMessage = rtool.testPropertiesValidity(properties, self)
            if failMessage is not None:
                raise BadRequest(failMessage)
        self.setMemberProperties(properties)

    @security.private
    def setMemberProperties(self, mapping):
        """Sets the properties of the member.
        """
        # Sets the properties given in the MemberDataTool.
        tool = self._tool
        for id in tool.propertyIds():
            if id in mapping:
                if id not in self._md.__class__.__dict__:
                    value = mapping[id]
                    if isinstance(value, str):
                        proptype = tool.getPropertyType(id) or 'string'
                        if proptype in type_converters:
                            value = type_converters[proptype](value)
                    setattr(self._md, id, value)
        # Hopefully we can later make notifyModified() implicit.
        self.notifyModified()

    @security.public
    def getProperty(self, id, default=_marker):
        # First, check the wrapper (w/o acquisition).
        value = getattr(self._md, id, _marker)
        if value is not _marker:
            return value

        # Then, check the tool and the user object for a value.
        tool_value = self._tool.getProperty(id, _marker)
        user_value = getattr(self._user, id, _marker)

        # If the tool doesn't have the property, use user_value or default
        if tool_value is _marker:
            if user_value is not _marker:
                return user_value
            elif default is not _marker:
                return default
            else:
                raise ValueError('The property %s does not exist' % id)

        # If the tool has an empty property and we have a user_value, use it
        if not tool_value and user_value is not _marker:
            return user_value

        # Otherwise return the tool value
        return tool_value

    @security.private
    def getPassword(self):
        """Return the password of the user."""
        return self._user._getPassword()

    @security.private
    def setSecurityProfile(self, password=None, roles=None, domains=None):
        """Set the user's basic security profile"""
        u = self._user

        # The Zope User API is stupid, it should check for None.
        if roles is None:
            roles = list(u.getRoles())
            if 'Authenticated' in roles:
                roles.remove('Authenticated')
        if domains is None:
            domains = u.getDomains()

        u.userFolderEditUser(u.getId(), password, roles, domains)

    def __str__(self):
        return self._user.getId()

    #
    #   'IUser' interface methods
    #
    @security.public
    def getId(self):
        """Get the ID of the user.
        """
        return self._user.getId()

    @security.public
    def getUserName(self):
        """Get the name used by the user to log into the system.
        """
        return self._user.getUserName()

    @security.public
    def getRoles(self):
        """Get a sequence of the global roles assigned to the user.
        """
        return self._user.getRoles()

    @security.public
    def getRolesInContext(self, object):
        """Get a sequence of the roles assigned to the user in a context.
        """
        return self._user.getRolesInContext(object)

    @security.public
    def getDomains(self):
        """Get a sequence of the domain restrictions for the user.
        """
        return self._user.getDomains()

    @security.public
    def has_role(self, roles, object=None):
        """Check to see if a user has a given role or roles."""
        return self._user.has_role(roles, object)

    # There are other parts of the interface but they are
    # deprecated for use with CMF applications.


InitializeClass(MemberAdapter)
