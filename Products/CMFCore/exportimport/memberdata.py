##############################################################################
#
# Copyright (c) 2011 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Member data tool xml adapter and setup handlers.
"""

from zope.component import adapts
from zope.component import getSiteManager

from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects

from ..interfaces import IMemberDataTool


class MemberDataToolXMLAdapter(XMLAdapterBase, PropertyManagerHelpers):

    """XML im- and exporter for MemberDataTool.
    """

    adapts(IMemberDataTool, ISetupEnviron)

    _LOGGER_ID = 'memberdata'

    name = 'memberdata'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())

        self._logger.info('Member data tool exported.')
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()

        self._initProperties(node)

        self._logger.info('Member data tool imported.')


def importMemberDataTool(context):
    """Import member data tool settings from an XML file.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(IMemberDataTool)
    if tool is None:
        logger = context.getLogger('memberdata')
        logger.debug('Nothing to import.')
        return

    importObjects(tool, '', context)


def exportMemberDataTool(context):
    """Export member data tool settings as an XML file.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(IMemberDataTool)
    if tool is None:
        logger = context.getLogger('memberdata')
        logger.debug('Nothing to export.')
        return

    exportObjects(tool, '', context)
