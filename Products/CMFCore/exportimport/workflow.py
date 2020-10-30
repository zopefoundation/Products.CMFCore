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
"""Workflow tool xml adapters and setup handlers.
"""

from zope.component import adapts
from zope.component import getSiteManager

from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects

from ..interfaces import IConfigurableWorkflowTool
from ..interfaces import IWorkflowTool


class WorkflowToolXMLAdapter(XMLAdapterBase, ObjectManagerHelpers,
                             PropertyManagerHelpers):

    """XML im- and exporter for WorkflowTool.
    """

    adapts(IConfigurableWorkflowTool, ISetupEnviron)

    _LOGGER_ID = 'workflow'

    name = 'workflows'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractObjects())
        node.appendChild(self._extractChains())

        self._logger.info('Workflow tool exported.')
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()
            self._purgeObjects()
            self._purgeChains()

        self._initProperties(node)
        self._initObjects(node)
        self._initChains(node)

        self._logger.info('Workflow tool imported.')

    def _extractChains(self):
        fragment = self._doc.createDocumentFragment()
        node = self._doc.createElement('bindings')
        child = self._doc.createElement('default')
        chain = self.context.getDefaultChain()
        for workflow_id in chain:
            sub = self._doc.createElement('bound-workflow')
            sub.setAttribute('workflow_id', workflow_id)
            child.appendChild(sub)
        node.appendChild(child)
        for type_id, chain in self.context.listChainOverrides():
            child = self._doc.createElement('type')
            child.setAttribute('type_id', type_id)
            for workflow_id in chain:
                sub = self._doc.createElement('bound-workflow')
                sub.setAttribute('workflow_id', workflow_id)
                child.appendChild(sub)
            node.appendChild(child)
        fragment.appendChild(node)
        return fragment

    def _purgeChains(self):
        self.context.setDefaultChain('')
        for type_id, _chain in self.context.listChainOverrides():
            self.context.setChainForPortalTypes((type_id,), None,
                                                verify=False)

    def _initChains(self, node):
        for child in node.childNodes:
            if child.nodeName != 'bindings':
                continue
            for sub in child.childNodes:
                if sub.nodeName == 'default':
                    self.context.setDefaultChain(self._getChain(sub))
                if sub.nodeName == 'type':
                    type_id = str(sub.getAttribute('type_id'))
                    if sub.hasAttribute('remove'):
                        chain = None
                    else:
                        chain = self._getChain(sub)
                    self.context.setChainForPortalTypes((type_id,), chain,
                                                        verify=False)

    def _getChain(self, node):
        workflow_ids = []
        for child in node.childNodes:
            if child.nodeName != 'bound-workflow':
                continue
            workflow_ids.append(str(child.getAttribute('workflow_id')))
        return ','.join(workflow_ids)


def importWorkflowTool(context):
    """Import workflow tool and contained workflow definitions from XML files.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(IWorkflowTool)
    if tool is None:
        logger = context.getLogger('workflow')
        logger.debug('Nothing to import.')
        return

    importObjects(tool, '', context)


def exportWorkflowTool(context):
    """Export workflow tool and contained workflow definitions as XML files.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(IWorkflowTool)
    if tool is None:
        logger = context.getLogger('workflow')
        logger.debug('Nothing to export.')
        return

    exportObjects(tool, '', context)
