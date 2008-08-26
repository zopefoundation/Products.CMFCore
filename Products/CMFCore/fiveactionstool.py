##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Five actions tool.

$Id$
"""

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from zope.app.publisher.browser.menu import getMenu
from zope.app.publisher.interfaces.browser import IBrowserMenu
from zope.component import getUtilitiesFor

from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.Expression import Expression
from Products.CMFCore.utils import UniqueObject

def _listMenuIds():
    return [id for id, utility in getUtilitiesFor(IBrowserMenu)]


class FiveActionsTool( UniqueObject, SimpleItem, ActionProviderBase ):

    """ Links content to discussions.
    """

    id = 'portal_fiveactions'
    meta_type = 'Five Actions Tool'

    security = ClassSecurityInfo()

    def getRequestURL(self):
        return self.REQUEST.URL

    security.declarePrivate('listActions')
    def listActions(self, info=None, object=None):
        """ List all the actions defined by a provider.
        """
        if object is None:
            if  info is None:
                # There is no support for global actions
                return ()
            else:
                object = info.content

        actions = []
        for menu_id in _listMenuIds():
            for entry in getMenu(menu_id, object, self.REQUEST):
                # The action needs a unique name, so I'll build one
                # from the object_id and the action url. That is sure
                # to be unique.
                action = str(entry['action'])
                if object is None:
                    act_id = 'action_%s' % action
                else:
                    act_id = 'action_%s_%s' % (object.getId(), action)

                if entry.get('filter') is None:
                    filter = None
                else:
                    filter = Expression(text=str(entry['filter']))

                title = entry['title']
                # Having bits of unicode here can make rendering very confused,
                # so we convert it to plain strings, but NOT if it is a 
                # messageID. In Zope 3.2 there are two types of messages,
                # Message and MessageID, where MessageID is depracated. We can 
                # type-check for both but that provokes a deprecation warning, 
                # so we check for the "domain" attribute instead. 
                if not hasattr(title, 'domain'):
                    title = str(title)
                act = ActionInformation(id=act_id,
                    title=title,
                    action=Expression(text='string:%s' % action),
                    condition=filter,
                    category=str(menu_id),
                    visible=1)
                actions.append(act)

        return tuple(actions)

InitializeClass( FiveActionsTool )
