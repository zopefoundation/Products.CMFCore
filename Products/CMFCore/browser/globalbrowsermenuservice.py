##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Global Browser Menu Service

Five-based adaptation of the one in Zope 3.0.

$Id$
"""
from zope.interface import implementedBy
from zope.interface.interfaces import IInterface
from zope.security.interfaces import Unauthorized, Forbidden
from zope.app.publication.browser import PublicationTraverser
from zope.app.component.interface import provideInterface

from Products.Five.security import checkPermission, CheckerPublic

from types import ClassType


def addMenuItem(menu_id, interface, action, title,
                description='', filter_string=None, permission=None,
                extra=None,
                ):
    from zope.app.publisher.browser.globalbrowsermenuservice import \
        globalBrowserMenuService
    from zope.app.publisher.browser.globalbrowsermenuservice import MenuItem
    registry = globalBrowserMenuService._registry[menu_id].registry

    if permission:
        if permission == 'zope.Public':
            permission = CheckerPublic

    if interface is not None and not IInterface.providedBy(interface):
        if isinstance(interface, (type, ClassType)):
            interface = implementedBy(interface)
        else:
            raise TypeError(
                "The interface argument must be an interface (or None) "
                "or a class.")

    data = registry.get(interface) or []
    data.append(
        MenuItem(action, title, description, filter_string, permission, extra)
        )
    registry.register(interface, data)


def getMenu(menu_id, object, request, max=999999):
    from zope.app.publisher.browser.globalbrowsermenuservice import \
        globalBrowserMenuService
    traverser = PublicationTraverser()

    result = []
    seen = {}

    # stuff for figuring out the selected view
    request_url = request.getURL()

    for item in globalBrowserMenuService.getAllMenuItems(menu_id, object):

        # Make sure we don't repeat a specification for a given title
        title = item.title
        if title in seen:
            continue
        seen[title] = 1

        permission = item.permission
        action = item.action

        if permission:
            # If we have an explicit permission, check that we
            # can access it.
            if not checkPermission(permission, object):
                continue

        elif action:
            # Otherwise, test access by attempting access
            path = action
            l = action.find('?')
            if l >= 0:
               path = action[:l]
            try:
                v = traverser.traverseRelativeURL(
                    request, object, path)
                # TODO:
                # tickle the security proxy's checker
                # we're assuming that view pages are callable
                # this is a pretty sound assumption
                v.__call__
            except (Unauthorized, Forbidden):
                continue # Skip unauthorized or forbidden

        normalized_action = action
        if action.startswith('@@'):
            normalized_action = action[2:]

        if request_url.endswith('/'+normalized_action):
            selected='selected'
        elif request_url.endswith('/++view++'+normalized_action):
            selected='selected'
        elif request_url.endswith('/@@'+normalized_action):
            selected='selected'
        else:
            selected=''

        result.append({
            'title': title,
            'description': item.description,
            'action': "%s" % action,
            'filter': item.filter,
            'selected': selected,
            'extra': item.extra,
            })

        if len(result) >= max:
            return result

    return result



def menuItemDirective(_context, menu, for_,
                      action, title, description='', filter=None,
                      permission=None, extra=None):
    return menuItemsDirective(_context, menu, for_).menuItem(
        _context, action, title, description, filter, permission, extra)


class menuItemsDirective(object):

    def __init__(self, _context, menu, for_):
        self.interface = for_
        self.menu = menu

    def menuItem(self, _context, action, title, description='',
                 filter=None, permission=None, extra=None):
        _context.action(
            discriminator = ('browser:menuItem',
                             self.menu, self.interface, title),
            callable = addMenuItem,
            args = (self.menu, self.interface,
                    action, title, description, filter, permission, extra),
            ),

    def __call__(self, _context):
        _context.action(
            discriminator = None,
            callable = provideInterface,
            args = (self.interface.__module__+'.'+self.interface.getName(),
                    self.interface)
            )
