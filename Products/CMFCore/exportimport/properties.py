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
"""Site properties xml adapters and setup handlers.
"""

from zope.component import adapts
from zope.component import queryMultiAdapter

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.utils import XMLAdapterBase

from ..interfaces import ISiteRoot


_FILENAME = 'properties.xml'


class PropertiesXMLAdapter(XMLAdapterBase, PropertyManagerHelpers):

    """XML im- and exporter for properties.
    """

    adapts(ISiteRoot, ISetupEnviron)

    _LOGGER_ID = 'properties'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        self._encoding = self.context.getProperty(
            'default_charset',
            self._encoding,
        )

        node = self._doc.createElement('site')
        node.appendChild(self._extractProperties())

        self._logger.info('Site properties exported.')
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        for child in node.childNodes:
            if child.nodeName != 'property':
                continue
            if child.getAttribute('name') != 'default_charset':
                continue
            self._encoding = self._getNodeText(child) or self._encoding
            break

        if self.environ.shouldPurge():
            self._purgeProperties()
        self._initProperties(node)

        self._logger.info('Site properties imported.')


def importSiteProperties(context):
    """ Import site properties from an XML file.
    """
    site = context.getSite()
    logger = context.getLogger('properties')

    body = context.readDataFile(_FILENAME)
    if body is None:
        logger.debug('Nothing to import.')
        return

    importer = queryMultiAdapter((site, context), IBody)
    if importer is None:
        logger.warning('Import adapter missing.')
        return

    importer.body = body


def exportSiteProperties(context):
    """ Export site properties as an XML file.
    """
    site = context.getSite()
    logger = context.getLogger('properties')

    exporter = queryMultiAdapter((site, context), IBody)
    if exporter is None:
        logger.warning('Export adapter missing.')
        return

    context.writeDataFile(_FILENAME, exporter.body, exporter.mime_type)
