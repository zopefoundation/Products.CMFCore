##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit test security.
"""

from AccessControl.interfaces import IUser
from AccessControl.PermissionRole import rolesForPermissionOn
from Acquisition import Implicit
from zope.interface import implementer


class PermissiveSecurityPolicy:

    """Very permissive security policy for unit testing purposes.
    """

    #
    #   Standard SecurityPolicy interface
    #
    def validate(self, accessed=None, container=None, name=None, value=None,
                 context=None, roles=None, *args, **kw):
        if name and name.startswith('hidden'):
            return False
        else:
            return True

    def checkPermission(self, permission, object, context):
        roles = rolesForPermissionOn(permission, object)
        if isinstance(roles, str):
            roles = [roles]
        return context.user.allowed(object, roles)


@implementer(IUser)
class _BaseUser(Implicit):

    def getId(self):
        return self._id

    def getUserName(self):
        return self._name

    def getRoles(self):
        return self._roles

    def getRolesInContext(self, object):
        return self._roles

    def getDomains(self):
        return self._domains

    def allowed(self, object, object_roles=None):
        if object_roles is None or 'Anonymous' in object_roles:
            return True
        return any(r in self._roles for r in object_roles)

    def _check_context(self, object):
        return True


class OmnipotentUser(_BaseUser):

    """Omnipotent user for unit testing purposes.
    """

    _id = 'all_powerful_Oz'
    _name = 'All Powerful Oz'
    _roles = ('Manager',)

    def allowed(self, object, object_roles=None):
        return True


class UserWithRoles(_BaseUser):

    """User with roles specified in constructor for unit testing purposes.
    """

    _id = 'high_roller'
    _name = 'High Roller'

    def __init__(self, *roles):
        self._roles = roles


class DummyUser(_BaseUser):

    """ A dummy User.
    """

    _roles = ('Authenticated', 'Dummy', 'Member')

    def __init__(self, id='dummy'):
        self._id = id
        self._name = 'name of %s' % id


class AnonymousUser(_BaseUser):

    """Anonymous user for unit testing purposes.
    """

    _id = None
    _name = 'Anonymous User'
    _roles = ('Anonymous',)
