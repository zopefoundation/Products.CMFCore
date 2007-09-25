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
"""Catalog tool setup handlers.

$Id$
"""

from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects

from Products.CMFCore.utils import getToolByName


def importCatalogTool(context):
    """Import catalog tool.
    """
    site = context.getSite()
    tool = getToolByName(site, 'portal_catalog')

    importObjects(tool, '', context)

def exportCatalogTool(context):
    """Export catalog tool.
    """
    site = context.getSite()
    tool = getToolByName(site, 'portal_catalog', None)
    if tool is None:
        logger = context.getLogger('catalog')
        logger.info('Nothing to export.')
        return

    exportObjects(tool, '', context)
