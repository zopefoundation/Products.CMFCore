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
"""Types tool xml adapters and setup handlers.
"""

from zope.component import adapts
from zope.component import getSiteManager

from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import I18NURI
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects

from ..interfaces import ITypeInformation
from ..interfaces import ITypesTool


class TypeInformationXMLAdapter(XMLAdapterBase, PropertyManagerHelpers):

    """XML im- and exporter for TypeInformation.
    """

    adapts(ITypeInformation, ISetupEnviron)

    _LOGGER_ID = 'types'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.setAttribute('xmlns:i18n', I18NURI)
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractAliases())
        node.appendChild(self._extractActions())

        self._logger.info('%r type info exported.' % self.context.getId())
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()
            self._purgeAliases()
            self._purgeActions()

        self._migrateProperties(node)
        self._initProperties(node)
        self._initAliases(node)
        self._initActions(node)

        obj_id = str(node.getAttribute('name'))
        self._logger.info('%r type info imported.' % obj_id)

    def _migrateProperties(self, node):
        # BBB: for CMF 2.1 icon settings
        for child in node.childNodes:
            if child.nodeName != 'property':
                continue
            if child.getAttribute('name') == 'icon_expr':
                return
        for child in node.childNodes:
            if child.nodeName != 'property':
                continue
            if child.getAttribute('name') != 'content_icon':
                continue
            text = self._getNodeText(child)
            icon = 'string:${portal_url}/%s' % text if text else ''
            new_child = self._doc.createElement('property')
            new_child.setAttribute('name', 'icon_expr')
            new_child.appendChild(self._doc.createTextNode(icon))
            node.replaceChild(new_child, child)

    def _extractAliases(self):
        fragment = self._doc.createDocumentFragment()
        aliases = sorted(self.context.getMethodAliases().items())
        for k, v in aliases:
            child = self._doc.createElement('alias')
            child.setAttribute('from', k)
            child.setAttribute('to', v)
            fragment.appendChild(child)
        return fragment

    def _purgeAliases(self):
        self.context.setMethodAliases({})

    def _initAliases(self, node):
        aliases = self.context.getMethodAliases()
        for child in node.childNodes:
            if child.nodeName != 'alias':
                continue
            k = str(child.getAttribute('from'))
            v = str(child.getAttribute('to'))
            aliases[k] = v
        self.context.setMethodAliases(aliases)

    def _extractActions(self):
        fragment = self._doc.createDocumentFragment()
        actions = self.context.listActions()
        for ai in actions:
            ai_info = ai.getMapping()
            child = self._doc.createElement('action')
            child.setAttribute('title', ai_info['title'])
            child.setAttribute('action_id', ai_info['id'])
            child.setAttribute('category', ai_info['category'])
            child.setAttribute('condition_expr', ai_info['condition'])
            child.setAttribute('url_expr', ai_info['action'])
            child.setAttribute('icon_expr', ai_info['icon_expr'])
            child.setAttribute('link_target', ai_info['link_target'])
            child.setAttribute('visible', str(bool(ai_info['visible'])))
            for permission in ai_info['permissions']:
                sub = self._doc.createElement('permission')
                sub.setAttribute('value', permission)
                child.appendChild(sub)
            fragment.appendChild(child)
        return fragment

    def _purgeActions(self):
        self.context._actions = ()

    def _initActions(self, node):
        for child in node.childNodes:
            if child.nodeName != 'action':
                continue
            title = str(child.getAttribute('title'))
            id = str(child.getAttribute('action_id'))
            category = str(child.getAttribute('category'))
            condition = str(child.getAttribute('condition_expr'))
            action = str(child.getAttribute('url_expr'))
            icon_expr = str(child.getAttribute('icon_expr'))
            if child.hasAttribute('link_target'):
                link_target = str(child.getAttribute('link_target'))
            else:
                link_target = ''
            visible = self._convertToBoolean(child.getAttribute('visible'))
            remove = child.hasAttribute('remove') and True or False
            permissions = []
            for sub in child.childNodes:
                if sub.nodeName != 'permission':
                    continue
                permission = sub.getAttribute('value')
                permissions.append(permission)
            action_obj = self.context.getActionObject(category+'/'+id)
            if remove:
                if action_obj is not None:
                    # Find the index for the action to remove it
                    actions = self.context.listActions()
                    indexes = [(a.category, a.id) for a in actions]
                    index = indexes.index((category, id))
                    self.context.deleteActions((index, ))
            else:
                if action_obj is None:
                    self.context.addAction(id, title, action, condition,
                                           tuple(permissions), category,
                                           visible, icon_expr=icon_expr,
                                           link_target=link_target)
                else:
                    action_obj.edit(title=title, action=action,
                                    icon_expr=icon_expr, condition=condition,
                                    permissions=tuple(permissions),
                                    visible=visible, link_target=link_target)


class TypesToolXMLAdapter(XMLAdapterBase, ObjectManagerHelpers,
                          PropertyManagerHelpers):

    """XML im- and exporter for TypesTool.
    """

    adapts(ITypesTool, ISetupEnviron)

    _LOGGER_ID = 'types'

    name = 'types'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractObjects())

        self._logger.info('Types tool exported.')
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()
            self._purgeObjects()

        self._initProperties(node)
        self._initObjects(node)

        self._logger.info('Types tool imported.')


def importTypesTool(context):
    """Import types tool and content types from XML files.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(ITypesTool)
    if tool is None:
        logger = context.getLogger('types')
        logger.debug('Nothing to import.')
        return

    importObjects(tool, '', context)


def exportTypesTool(context):
    """Export types tool content types as a set of XML files.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(ITypesTool)
    if tool is None:
        logger = context.getLogger('types')
        logger.debug('Nothing to export.')
        return

    exportObjects(tool, '', context)
