##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Basic undo tool.

$Id$
"""

from AccessControl import ClassSecurityInfo
from Globals import DTMLFile
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from zope.interface import implements

from exceptions import AccessControl_Unauthorized
from interfaces import IUndoTool
from interfaces.portal_undo import portal_undo as z2IUndoTool
from permissions import ListUndoableChanges
from permissions import ManagePortal
from utils import _checkPermission
from utils import _dtmldir
from utils import _getAuthenticatedUser
from utils import registerToolInterface
from utils import UniqueObject


class UndoTool(UniqueObject, SimpleItem):

    """ This tool is used to undo changes.
    """

    implements(IUndoTool)
    __implements__ = (z2IUndoTool, )

    id = 'portal_undo'
    meta_type = 'CMF Undo Tool'

    security = ClassSecurityInfo()

    manage_options = ( SimpleItem.manage_options
                     + ({'label': 'Overview',
                         'action': 'manage_overview'},)
                     )

    #
    #   ZMI methods
    #
    security.declareProtected(ManagePortal, 'manage_overview')
    manage_overview = DTMLFile( 'explainUndoTool', _dtmldir )

    #
    #   'IUndoTool' interface methods
    #
    security.declareProtected(ListUndoableChanges, 'listUndoableTransactionsFor')
    def listUndoableTransactionsFor(self, object,
                                    first_transaction=None,
                                    last_transaction=None,
                                    PrincipiaUndoBatchSize=None):
        """ List all transaction IDs the user is allowed to undo on 'object'.
        """
        transactions = object.undoable_transactions(
            first_transaction=first_transaction,
            last_transaction=last_transaction,
            PrincipiaUndoBatchSize=PrincipiaUndoBatchSize)
        for t in transactions:
            # Ensure transaction ids don't have embedded LF.
            t['id'] = t['id'].replace('\n', '')
        if not _checkPermission(ManagePortal, object):
            # Filter out transactions done by other members of the portal.
            user_id = _getAuthenticatedUser(self).getId()
            transactions = filter(
                lambda record, user_id=user_id:
                record['user_name'].split()[-1] == user_id,
                transactions
                )
        return transactions

    security.declarePublic('undo')
    def undo(self, object, transaction_info):
        """
            Undo the list of transactions passed in 'transaction_info',
            first verifying that the current user is allowed to undo them.
        """
        # Belt and suspenders:  make sure that the user is actually
        # allowed to undo the transation(s) in transaction_info.

        xids = {}  # set of allowed transaction IDs

        allowed = self.listUndoableTransactionsFor( object )

        for xid in map( lambda x: x['id'], allowed ):
            xids[xid] = 1

        if type( transaction_info ) == type( '' ):
            transaction_info = [ transaction_info ]

        for tinfo in transaction_info:
            if not xids.get( tinfo, None ):
                raise AccessControl_Unauthorized

        object.manage_undo_transactions(transaction_info)

InitializeClass(UndoTool)
registerToolInterface('portal_undo', IUndoTool)
