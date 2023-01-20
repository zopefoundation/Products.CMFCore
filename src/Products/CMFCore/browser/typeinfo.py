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
"""TypeInformation browser views.
"""

from xml.dom.minidom import parseString

from zope.component import queryMultiAdapter
from zope.component import queryUtility

from Products.GenericSetup.browser.utils import AddWithPresettingsViewBase
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupTool

from ..TypesTool import FactoryTypeInformation
from ..TypesTool import ScriptableTypeInformation


class FactoryTypeInformationAddView(AddWithPresettingsViewBase):

    """Add view for FactoryTypeInformation.
    """

    klass = FactoryTypeInformation

    description = 'A type information object defines a portal type.'

    def getProfileInfos(self):
        profiles = []
        stool = queryUtility(ISetupTool)
        if stool:
            for info in stool.listContextInfos():
                obj_ids = []
                context = stool._getImportContext(info['id'])
                file_ids = context.listDirectory('types')
                for file_id in file_ids or ():
                    if not file_id.endswith('.xml'):
                        continue

                    filename = 'types/%s' % file_id
                    body = context.readDataFile(filename)
                    if body is None:
                        continue

                    root = parseString(body).documentElement
                    meta_type = str(root.getAttribute('meta_type'))
                    if meta_type != self.klass.meta_type:
                        continue

                    obj_id = str(root.getAttribute('name'))
                    obj_ids.append(obj_id)
                if not obj_ids:
                    continue
                profiles.append({'id': info['id'],
                                 'title': info['title'],
                                 'obj_ids': tuple(sorted(obj_ids))})
        return tuple(profiles)

    def _initSettings(self, obj, profile_id, obj_path):
        stool = queryUtility(ISetupTool)
        if stool is None:
            return

        context = stool._getImportContext(profile_id)
        file_ids = context.listDirectory('types')
        for file_id in file_ids or ():
            if not file_id.endswith('.xml'):
                continue

            filename = 'types/%s' % file_id
            body = context.readDataFile(filename)
            if body is None:
                continue

            root = parseString(body).documentElement
            new_id = str(root.getAttribute('name'))
            if new_id != obj_path[0]:
                continue

            meta_type = str(root.getAttribute('meta_type'))
            if meta_type != self.klass.meta_type:
                continue

            importer = queryMultiAdapter((obj, context), IBody)
            if importer is None:
                continue

            importer.body = body
            return


class ScriptableTypeInformationAddView(FactoryTypeInformationAddView):

    """Add view for ScriptableTypeInformation.
    """

    klass = ScriptableTypeInformation
