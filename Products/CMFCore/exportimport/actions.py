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
"""Actions tool node adapters.
"""

from zope.component import adapts
from zope.component import getSiteManager

from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import I18NURI
from Products.GenericSetup.utils import NodeAdapterBase
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects

from ..interfaces import IAction
from ..interfaces import IActionCategory
from ..interfaces import IActionProvider
from ..interfaces import IActionsTool
from ..utils import getToolByName


class ActionCategoryNodeAdapter(NodeAdapterBase, ObjectManagerHelpers,
                                PropertyManagerHelpers):

    """Node im- and exporter for ActionCategory.
    """

    adapts(IActionCategory, ISetupEnviron)

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractObjects())
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        purge = self.environ.shouldPurge()
        if node.getAttribute('purge'):
            purge = self._convertToBoolean(node.getAttribute('purge'))
        if purge:
            self._purgeProperties()
            self._purgeObjects()

        self._initProperties(node)
        self._initObjects(node)

    node = property(_exportNode, _importNode)


class ActionNodeAdapter(NodeAdapterBase, PropertyManagerHelpers):

    """Node im- and exporter for Action.
    """

    adapts(IAction, ISetupEnviron)

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        purge = self.environ.shouldPurge()
        if node.getAttribute('purge'):
            purge = self._convertToBoolean(node.getAttribute('purge'))
        if purge:
            self._purgeProperties()

        self._initProperties(node)

    node = property(_exportNode, _importNode)


class ActionsToolXMLAdapter(XMLAdapterBase, ObjectManagerHelpers):

    """XML im- and exporter for ActionsTool.
    """

    adapts(IActionsTool, ISetupEnviron)

    _LOGGER_ID = 'actions'

    name = 'actions'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.setAttribute('xmlns:i18n', I18NURI)
        node.appendChild(self._extractProviders())
        node.appendChild(self._extractObjects())

        self._logger.info('Actions tool exported.')
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProviders()
            self._purgeObjects()

        self._initObjects(node)
        self._initProviders(node)

        self._logger.info('Actions tool imported.')

    def _extractProviders(self):
        fragment = self._doc.createDocumentFragment()
        for provider_id in self.context.listActionProviders():
            child = self._doc.createElement('action-provider')
            child.setAttribute('name', provider_id)
            # BBB: for CMF 1.6 action settings
            # We only do this for the portal_actions tool itself. Other
            # providers are responsible for their own action import/export.
            if provider_id == 'portal_actions':
                sub = self._extractOldstyleActions(provider_id)
                child.appendChild(sub)

            fragment.appendChild(child)

        return fragment

    def _extractOldstyleActions(self, provider_id):
        # BBB: for CMF 1.6 action settings
        # This method collects "old-style" action information and
        # formats it for import as "new-style" actions

        fragment = self._doc.createDocumentFragment()

        provider = getToolByName(self.context, provider_id)
        if not IActionProvider.providedBy(provider):
            return fragment

        if provider_id == 'portal_actions':
            actions = provider._actions
        else:
            actions = provider.listActions()

        if actions and isinstance(actions[0], dict):
            return fragment

        for ai in actions:
            if getattr(ai, 'getMapping', None) is None:
                continue
            mapping = ai.getMapping()
            child = self._doc.createElement('action')
            child.setAttribute('action_id', mapping['id'])
            child.setAttribute('category', mapping['category'])
            child.setAttribute('condition_expr', mapping['condition'])
            child.setAttribute('title', mapping['title'])
            child.setAttribute('url_expr', mapping['action'])
            child.setAttribute('visible', str(mapping['visible']))
            for permission in mapping['permissions']:
                sub = self._doc.createElement('permission')
                sub.appendChild(self._doc.createTextNode(permission))
                child.appendChild(sub)
            fragment.appendChild(child)
        return fragment

    def _purgeProviders(self):
        for provider_id in self.context.listActionProviders():
            self.context.deleteActionProvider(provider_id)

    def _initProviders(self, node):
        for child in node.childNodes:
            if child.nodeName != 'action-provider':
                continue

            provider_id = str(child.getAttribute('name'))
            if child.hasAttribute('remove'):
                if provider_id in self.context.listActionProviders():
                    self.context.deleteActionProvider(provider_id)
                continue

            if provider_id not in self.context.listActionProviders():
                self.context.addActionProvider(provider_id)

            # BBB: for CMF 1.6 action setting exports
            # We only do this for the portal_actions tool itself. Other
            # providers are responsible for their own action import/export.
            if provider_id == 'portal_actions':
                self._initOldstyleActions(child)

    def _initOldstyleActions(self, node):
        # BBB: for CMF 1.6 action setting exports
        # This code transparently migrates old export data containing
        # "old-style" action information to "new-style" actions.
        # It does this by synthesizing "new-style" export data from the
        # existing export and then importing that instead of the
        # "real" export data, which also moves these actions into the
        # actions tool.
        doc = node.ownerDocument
        fragment = doc.createDocumentFragment()
        for child in node.childNodes:
            if child.nodeName != 'action':
                continue

            parent = fragment
            for category_id in child.getAttribute('category').split('/'):
                newnode = doc.createElement('object')
                newnode.setAttribute('name', str(category_id))
                newnode.setAttribute('meta_type', 'CMF Action Category')
                newnode.setAttribute('purge', 'False')
                parent.appendChild(newnode)
                parent = newnode
            newnode = doc.createElement('object')
            newnode.setAttribute('name', str(child.getAttribute('action_id')))
            newnode.setAttribute('meta_type', 'CMF Action')
            newnode.setAttribute('purge', 'False')

            mapping = {'title': 'title',
                       'url_expr': 'url_expr',
                       'condition_expr': 'available_expr',
                       'visible': 'visible'}
            for old, new in mapping.items():
                newchild = doc.createElement('property')
                newchild.setAttribute('name', new)
                newsub = doc.createTextNode(child.getAttribute(old))
                newchild.appendChild(newsub)
                newnode.appendChild(newchild)

            newchild = doc.createElement('property')
            newchild.setAttribute('name', 'permissions')
            for sub in child.childNodes:
                if sub.nodeName == 'permission':
                    newsub = doc.createElement('element')
                    newsub.setAttribute('value', self._getNodeText(sub))
                    newchild.appendChild(newsub)
            newnode.appendChild(newchild)

            parent.appendChild(newnode)

        self._initObjects(fragment)


def importActionProviders(context):
    """Import actions tool.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(IActionsTool)
    if tool is None:
        logger = context.getLogger('actions')
        logger.debug('Nothing to import.')
        return

    importObjects(tool, '', context)


def exportActionProviders(context):
    """Export actions tool.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(IActionsTool)
    if tool is None:
        logger = context.getLogger('actions')
        logger.debug('Nothing to export.')
        return

    exportObjects(tool, '', context)
