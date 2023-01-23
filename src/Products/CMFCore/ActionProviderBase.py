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
""" Implement a shared base for tools which provide actions.
"""

from warnings import warn

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.special_dtml import DTMLFile
from zope.interface import implementer

from .ActionInformation import ActionInfo
from .ActionInformation import ActionInformation
from .ActionInformation import getOAI
from .exceptions import AccessControl_Unauthorized
from .Expression import getExprContext
from .interfaces import IActionProvider
from .permissions import ManagePortal
from .utils import _dtmldir


@implementer(IActionProvider)
class ActionProviderBase:

    """ Provide ActionTabs and management methods for ActionProviders
    """

    security = ClassSecurityInfo()
    _actions = ()
    _actions_form = DTMLFile('editToolsActions', _dtmldir)

    manage_options = ({'label': 'Actions', 'action': 'manage_editActionsForm',
                       'help': ('CMFCore', 'Actions.stx')},)

    #
    #   ActionProvider interface
    #
    @security.private
    def listActions(self, info=None, object=None):
        """ List all the actions defined by a provider.
        """
        oldstyle_actions = self._actions or ()
        if oldstyle_actions:
            warn('Old-style actions are deprecated and will be removed in CMF '
                 '2.4. Use Action and Action Category objects instead.',
                 DeprecationWarning, stacklevel=2)

        return oldstyle_actions

    @security.private
    def getActionObject(self, action):
        """Return the actions object or None if action doesn't exist.
        """
        # separate cataegory and id from action
        sep = action.rfind('/')
        if sep == -1:
            raise ValueError('Actions must have the format <category>/<id>.')
        category, id = action[:sep], action[sep+1:]

        # search for action and return first one found
        for ai in self.listActions():
            try:
                if id == ai.getId() and category == ai.getCategory():
                    return ai
            except AttributeError:
                continue

        # no action found
        return None

    @security.public
    def listActionInfos(self, action_chain=None, object=None,
                        check_visibility=1, check_permissions=1,
                        check_condition=1, max=-1):
        # List ActionInfo objects.
        # (method is without docstring to disable publishing)
        #
        ec = self._getExprContext(object)
        actions = self.listActions(object=object)
        actions = [ActionInfo(action, ec) for action in actions]

        if action_chain:
            filtered_actions = []
            if isinstance(action_chain, str):
                action_chain = (action_chain,)
            for action_ident in action_chain:
                sep = action_ident.rfind('/')
                category, id = action_ident[:sep], action_ident[sep+1:]
                for ai in actions:
                    if id == ai['id'] and category == ai['category']:
                        filtered_actions.append(ai)
            actions = filtered_actions

        action_infos = []
        for ai in actions:
            if check_visibility and not ai['visible']:
                continue
            if check_permissions and not ai['allowed']:
                continue
            if check_condition and not ai['available']:
                continue
            action_infos.append(ai)
            if max + 1 and len(action_infos) >= max:
                break
        return action_infos

    @security.public
    def getActionInfo(self, action_chain, object=None, check_visibility=0,
                      check_condition=0):
        """ Get an ActionInfo object specified by a chain of actions.
        """
        action_infos = self.listActionInfos(action_chain, object,
                                            check_visibility=check_visibility,
                                            check_permissions=False,
                                            check_condition=check_condition)
        if not action_infos:
            if object is None:
                provider = self
            else:
                provider = object
            msg = 'Action "{}" not available for {}'.format(
                        action_chain, '/'.join(provider.getPhysicalPath()))
            raise ValueError(msg)
        for ai in action_infos:
            if ai['allowed']:
                return ai
        raise AccessControl_Unauthorized('You are not allowed to access any '
                                         'of the specified Actions.')

    #
    #   ZMI methods
    #
    @security.protected(ManagePortal)
    def manage_editActionsForm(self, REQUEST, manage_tabs_message=None):

        """ Show the 'Actions' management tab.
        """
        actions = []
        for action in self.listActions():
            # The Actions tab currently only shows old-style actions,
            # so we need to weed out everything else.
            if getattr(action, 'getMapping', None) is not None:
                actions.append(action.getMapping())

        # possible_permissions is in AccessControl.Role.RoleManager.
        pp = self.possible_permissions()
        return self._actions_form(self, REQUEST, actions=actions,
                                  possible_permissions=pp,
                                  management_view='Actions',
                                  manage_tabs_message=manage_tabs_message)

    @security.protected(ManagePortal)
    def addAction(self, id, name, action, condition, permission, category,
                  visible=1, icon_expr='', link_target='', REQUEST=None):
        """ Add an action to our list.
        """
        if not name:
            raise ValueError('A name is required.')

        action = action and str(action) or ''
        condition = condition and str(condition) or ''

        if not isinstance(permission, tuple):
            permission = (str(permission),)

        new_actions = self._cloneActions()

        new_action = ActionInformation(id=str(id), title=str(name),
                                       category=str(category),
                                       condition=condition,
                                       permissions=permission,
                                       visible=bool(visible),
                                       action=action,
                                       icon_expr=icon_expr,
                                       link_target=link_target)

        new_actions.append(new_action)
        self._actions = tuple(new_actions)

        if REQUEST is not None:
            return self.manage_editActionsForm(
                REQUEST, manage_tabs_message='Added.')

    @security.protected(ManagePortal)
    def changeActions(self, properties=None, REQUEST=None):

        """ Update our list of actions.
        """
        if properties is None:
            properties = REQUEST

        actions = []

        for index in range(len(self._actions)):
            actions.append(self._extractAction(properties, index))

        self._actions = tuple(actions)

        if REQUEST is not None:
            msg = 'Actions changed.'
            return self.manage_editActionsForm(REQUEST,
                                               manage_tabs_message=msg)

    @security.protected(ManagePortal)
    def deleteActions(self, selections=(), REQUEST=None):

        """ Delete actions indicated by indexes in 'selections'.
        """
        sels = list(map(int, selections))  # Convert to a list of integers.

        old_actions = self._cloneActions()
        new_actions = []

        for index in range(len(old_actions)):
            if index not in sels:
                new_actions.append(old_actions[index])

        self._actions = tuple(new_actions)

        if REQUEST is not None:
            msg = 'Deleted %d action(s).' % len(sels)
            return self.manage_editActionsForm(REQUEST,
                                               manage_tabs_message=msg)

    @security.protected(ManagePortal)
    def moveUpActions(self, selections=(), REQUEST=None):

        """ Move the specified actions up one slot in our list.
        """
        sels = sorted(map(int, selections))  # Convert to list of ints

        new_actions = self._cloneActions()

        for idx in sels:
            idx2 = idx - 1
            if idx2 < 0:
                # Wrap to the bottom.
                idx2 = len(new_actions) - 1
            # Swap.
            a = new_actions[idx2]
            new_actions[idx2] = new_actions[idx]
            new_actions[idx] = a

        self._actions = tuple(new_actions)

        if REQUEST is not None:
            msg = 'Moved up %d action(s).' % len(sels)
            return self.manage_editActionsForm(REQUEST,
                                               manage_tabs_message=msg)

    @security.protected(ManagePortal)
    def moveDownActions(self, selections=(), REQUEST=None):

        """ Move the specified actions down one slot in our list.
        """
        sels = sorted(list(map(int, selections)))  # Convert to list of ints
        sels.reverse()

        new_actions = self._cloneActions()

        for idx in sels:
            idx2 = idx + 1
            if idx2 >= len(new_actions):
                # Wrap to the top.
                idx2 = 0
            # Swap.
            a = new_actions[idx2]
            new_actions[idx2] = new_actions[idx]
            new_actions[idx] = a

        self._actions = tuple(new_actions)

        if REQUEST is not None:
            msg = 'Moved down %d action(s).' % len(sels)
            return self.manage_editActionsForm(REQUEST,
                                               manage_tabs_message=msg)

    #
    #   Helper methods
    #
    @security.private
    def _cloneActions(self):

        """ Return a list of actions, cloned from our current list.
        """
        return [x.clone() for x in list(self._actions)]

    @security.private
    def _extractAction(self, properties, index):

        """ Extract an ActionInformation from the funky form properties.
        """
        id = str(properties.get('id_%d' % index, ''))
        title = str(properties.get('name_%d' % index, ''))
        action = str(properties.get('action_%d' % index, ''))
        icon_expr = str(properties.get('icon_expr_%d' % index, ''))
        condition = str(properties.get('condition_%d' % index, ''))
        category = str(properties.get('category_%d' % index, ''))
        visible = bool(properties.get('visible_%d' % index, False))
        permissions = properties.get('permission_%d' % index, ())
        link_target = str(properties.get('link_target_%d' % index, ''))

        if not title:
            raise ValueError('A title is required.')

        if category == '':
            category = 'object'

        if isinstance(permissions, str):
            permissions = (permissions,)

        return ActionInformation(id=id, title=title, action=action,
                                 condition=condition,
                                 permissions=permissions,
                                 category=category,
                                 visible=visible,
                                 icon_expr=icon_expr,
                                 link_target=link_target)

    def _getOAI(self, object):
        return getOAI(self, object)

    def _getExprContext(self, object):
        return getExprContext(self, object)


InitializeClass(ActionProviderBase)
