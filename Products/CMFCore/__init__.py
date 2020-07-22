##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Portal services base objects
"""

try:
    import Products.ZSQLMethods  # noqa

    from . import FSZSQLMethod
    HAVE_ZSQL = True
except ImportError:
    HAVE_ZSQL = False

# Make sure security is initialized
from . import ActionInformation
from . import ActionsTool
from . import CachingPolicyManager
from . import CatalogTool
from . import CMFBTreeFolder
from . import ContentTypeRegistry
from . import CookieCrumbler
from . import DirectoryView
from . import DiscussionTool
from . import FSDTMLMethod
from . import FSFile
from . import FSImage
from . import FSPageTemplate
from . import FSPropertiesObject
from . import FSPythonScript
from . import FSReSTMethod  # noqa
from . import FSSTXMethod  # noqa
from . import MemberDataTool
from . import MembershipTool
from . import PortalContent  # noqa
from . import PortalFolder
from . import PortalObject  # noqa
from . import RegistrationTool
from . import SkinsTool
from . import TypesTool
from . import UndoTool
from . import URLTool
from . import WorkflowTool
from . import utils
from .permissions import AddPortalFolders


tools = (MembershipTool.MembershipTool,
         RegistrationTool.RegistrationTool,
         WorkflowTool.WorkflowTool,
         CatalogTool.CatalogTool,
         DiscussionTool.DiscussionTool,
         ActionsTool.ActionsTool,
         UndoTool.UndoTool,
         SkinsTool.SkinsTool,
         MemberDataTool.MemberDataTool,
         TypesTool.TypesTool,
         URLTool.URLTool)

# BBB: oldstyle constructors
_EXTRA_CONSTRUCTORS = (PortalFolder.manage_addPortalFolder,
                       CMFBTreeFolder.manage_addCMFBTreeFolder)

# Because persistent objects may be out there which were
# created when the module was in that product, we need
# __module_aliases__ .
__module_aliases__ = (('Products.BTreeFolder2.CMFBTreeFolder',
                       'Products.CMFCore.CMFBTreeFolder'),)


def initialize(context):
    context.registerClass(
        DirectoryView.DirectoryView,
        constructors=(('manage_addDirectoryViewForm',
                       DirectoryView.manage_addDirectoryViewForm),
                      DirectoryView.manage_addDirectoryView,
                      DirectoryView.manage_listAvailableDirectories),
        icon='images/dirview.gif')

    context.registerClass(
        CookieCrumbler.CookieCrumbler,
        constructors=(CookieCrumbler.manage_addCCForm,
                      CookieCrumbler.manage_addCC),
        icon='images/cookie.gif')

    context.registerClass(
        ContentTypeRegistry.ContentTypeRegistry,
        constructors=(ContentTypeRegistry.manage_addRegistry,),
        icon='images/registry.gif')

    context.registerClass(
        CachingPolicyManager.CachingPolicyManager,
        constructors=(CachingPolicyManager.manage_addCachingPolicyManager,),
        icon='images/registry.gif')

    utils.registerIcon(ActionInformation.ActionCategory,
                       'images/cmf_action_category.gif', globals())
    utils.registerIcon(ActionInformation.Action,
                       'images/cmf_action.gif', globals())
    utils.registerIcon(TypesTool.FactoryTypeInformation,
                       'images/typeinfo.gif', globals())
    utils.registerIcon(TypesTool.ScriptableTypeInformation,
                       'images/typeinfo.gif', globals())
    utils.registerIcon(FSDTMLMethod.FSDTMLMethod,
                       'images/fsdtml.gif', globals())
    utils.registerIcon(FSPythonScript.FSPythonScript,
                       'images/fspy.gif', globals())
    utils.registerIcon(FSImage.FSImage,
                       'images/fsimage.gif', globals())
    utils.registerIcon(FSFile.FSFile,
                       'images/fsfile.gif', globals())
    utils.registerIcon(FSPageTemplate.FSPageTemplate,
                       'images/fspt.gif', globals())
    utils.registerIcon(FSPropertiesObject.FSPropertiesObject,
                       'images/fsprops.gif', globals())
    if HAVE_ZSQL:
        utils.registerIcon(FSZSQLMethod.FSZSQLMethod,
                           'images/fssqlmethod.gif', globals())

    utils.ToolInit('CMF Core Tool', tools=tools,
                   icon='tool.gif').initialize(context)

    # BBB: register oldstyle constructors
    utils.ContentInit('CMF Core Content', content_types=(),
                      permission=AddPortalFolders,
                      extra_constructors=_EXTRA_CONSTRUCTORS,
                      visibility=None).initialize(context)
