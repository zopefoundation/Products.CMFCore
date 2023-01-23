##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""TypeInformation browser views.
"""

from xml.dom.minidom import parseString

from zope.component import queryMultiAdapter
from zope.component import queryUtility

from Products.GenericSetup.browser.utils import AddWithPresettingsViewBase
from Products.GenericSetup.interfaces import INode
from Products.GenericSetup.interfaces import ISetupTool

from ..ActionInformation import Action
from ..ActionInformation import ActionCategory


class ActionAddView(AddWithPresettingsViewBase):

    """Add view for Action.
    """

    klass = Action

    description = 'An Action object represents a reference to an action.'

    def getProfileInfos(self):
        profiles = []
        stool = queryUtility(ISetupTool)
        if stool:
            for info in stool.listContextInfos():
                obj_ids = []
                context = stool._getImportContext(info['id'])
                body = context.readDataFile('actions.xml')
                if body is None:
                    continue
                root = parseString(body).documentElement
                for node in root.childNodes:
                    if node.nodeName != 'object':
                        continue
                    obj_ids += self._extractChildren(node)
                profiles.append({'id': info['id'],
                                 'title': info['title'],
                                 'obj_ids': tuple(sorted(obj_ids))})
        return tuple(profiles)

    def _extractChildren(self, node):
        action_paths = []
        category_id = node.getAttribute('name')
        for child in node.childNodes:
            if child.nodeName != 'object':
                continue
            if child.getAttribute('meta_type') == self.klass.meta_type:
                action_id = child.getAttribute('name')
                action_paths.append(action_id)
            else:
                action_paths += self._extractChildren(child)
        return [f'{category_id}/{path}' for path in action_paths]

    def _initSettings(self, obj, profile_id, obj_path):
        stool = queryUtility(ISetupTool)
        if stool is None:
            return

        context = stool._getImportContext(profile_id)
        body = context.readDataFile('actions.xml')
        if body is None:
            return

        settings_node = None
        root = parseString(body).documentElement
        for node in root.childNodes:
            if node.nodeName != 'object':
                continue
            for obj_id in obj_path:
                for child in node.childNodes:
                    if child.nodeName != 'object':
                        continue
                    if child.getAttribute('name') != obj_id:
                        continue
                    if child.getAttribute('meta_type') == self.klass.meta_type:
                        settings_node = child
                    else:
                        node = child
                    break

        importer = queryMultiAdapter((obj, context), INode)
        if importer is None:
            return

        importer.node = settings_node
        return


class ActionCategoryAddView(AddWithPresettingsViewBase):

    """Add view for ActionCategory.
    """

    klass = ActionCategory

    description = \
        'An Action Category object represents a group of Action objects.'

    def getProfileInfos(self):
        return []

    def _initSettings(self, obj, profile_id, obj_path):
        pass
