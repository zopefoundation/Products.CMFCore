##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" CMFCore event interfaces.
"""

from zope.interface import Attribute
from zope.interface.interfaces import IObjectEvent


class IWorkflowActionEvent(IObjectEvent):

    """Base interface for events around workflow action invocation
    """

    __module__ = 'Products.CMFCore.interfaces'

    workflow = Attribute('The workflow definition object')
    action = Attribute('The name of the action being invoked')


class IActionWillBeInvokedEvent(IWorkflowActionEvent):

    """Event fired immediately before a workflow action is invoked
    """

    __module__ = 'Products.CMFCore.interfaces'


class IActionRaisedExceptionEvent(IWorkflowActionEvent):

    """Event fired when a workflow action raised an exception
    """

    __module__ = 'Products.CMFCore.interfaces'

    exc = Attribute('The exception info for the exception raised')


class IActionSucceededEvent(IWorkflowActionEvent):

    """Event fired when a workflow action succeeded
    """

    __module__ = 'Products.CMFCore.interfaces'

    result = Attribute('The result of the workflow action')
