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
"""Cookie crumbler xml adapters and setup handlers.
"""

from zope.component import adapts
from zope.component import getSiteManager

from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects

from ..interfaces import ICookieCrumbler


class CookieCrumblerXMLAdapter(XMLAdapterBase, PropertyManagerHelpers):

    """XML im- and exporter for CookieCrumbler.
    """

    adapts(ICookieCrumbler, ISetupEnviron)

    _LOGGER_ID = 'cookies'

    name = 'cookieauth'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())

        self._logger.info('Cookie crumbler exported.')
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()

        self._migrateProperties(node)
        self._initProperties(node)

        self._logger.info('Cookie crumbler imported.')

    def _migrateProperties(self, node):
        # BBB: for CMF 2.2 settings
        for child in node.childNodes:
            if child.nodeName != 'property':
                continue
            if child.getAttribute('name') not in ('auto_login_page',
                                                  'unauth_page',
                                                  'logout_page'):
                continue
            node.removeChild(child)
            child.unlink()


def importCookieCrumbler(context):
    """Import cookie crumbler settings from an XML file.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(ICookieCrumbler)
    if tool is None:
        logger = context.getLogger('cookies')
        logger.debug('Nothing to import.')
        return

    importObjects(tool, '', context)


def exportCookieCrumbler(context):
    """Export cookie crumbler settings as an XML file.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(ICookieCrumbler)
    if tool is None:
        logger = context.getLogger('cookies')
        logger.debug('Nothing to export.')
        return

    exportObjects(tool, '', context)
