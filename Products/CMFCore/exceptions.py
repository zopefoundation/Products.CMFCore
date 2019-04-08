##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" CMFCore product exceptions.
"""

from AccessControl import ModuleSecurityInfo  # noqa
from AccessControl import Unauthorized as AccessControl_Unauthorized
from OFS.CopySupport import CopyError  # noqa
from zExceptions import BadRequest  # noqa; noqa
from zExceptions import NotFound  # noqa
from zExceptions import Unauthorized as zExceptions_Unauthorized


try:
    from zExceptions import ResourceLockedError  # noqa
except ImportError:
    from webdav.Lockable import ResourceLockedError  # noqa


security = ModuleSecurityInfo('Products.CMFCore.exceptions')

# Use AccessControl_Unauthorized to raise Unauthorized errors and
# zExceptions_Unauthorized to catch them all.

security.declarePublic('AccessControl_Unauthorized')
security.declarePublic('BadRequest')
security.declarePublic('CopyError')
security.declarePublic('NotFound')


@security.public
class SkinPathError(Exception):
    """ Invalid skin path error.
    """
    pass
