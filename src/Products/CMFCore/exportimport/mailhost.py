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
"""Mailhost setup handlers.
"""

from zope.component import getSiteManager

from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from Products.MailHost.interfaces import IMailHost


def importMailHost(context):
    """Import mailhost settings from an XML file.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(IMailHost)
    if tool is None:
        logger = context.getLogger('mailhost')
        logger.debug('Nothing to import.')
        return

    importObjects(tool, '', context)


def exportMailHost(context):
    """Export mailhost settings as an XML file.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(IMailHost)
    if tool is None:
        logger = context.getLogger('mailhost')
        logger.debug('Nothing to export.')
        return

    exportObjects(tool, '', context)
