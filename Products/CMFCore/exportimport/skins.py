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
"""Skins tool xml adapters and setup handlers.
"""

from Acquisition import aq_inner
from Acquisition import aq_parent
from zope.component import adapts
from zope.component import getSiteManager

from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import NodeAdapterBase
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects

from ..interfaces import IDirectoryView
from ..interfaces import ISkinsTool


class DirectoryViewNodeAdapter(NodeAdapterBase):

    """Node im- and exporter for DirectoryView.
    """

    adapts(IDirectoryView, ISetupEnviron)

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.setAttribute('directory', self.context.getDirPath())
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        self.context.manage_properties(str(node.getAttribute('directory')))

    node = property(_exportNode, _importNode)


class SkinsToolXMLAdapter(XMLAdapterBase, ObjectManagerHelpers):

    """XML im- and exporter for SkinsTool.
    """

    adapts(ISkinsTool, ISetupEnviron)

    _LOGGER_ID = 'skins'

    name = 'skins'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.setAttribute('default_skin', self.context.default_skin)
        node.setAttribute('request_varname', self.context.request_varname)
        node.setAttribute('allow_any', str(bool(self.context.allow_any)))
        node.setAttribute('cookie_persistence',
                          str(bool(self.context.cookie_persistence)))
        node.appendChild(self._extractObjects())
        node.appendChild(self._extractSkinPaths())

        self._logger.info('Skins tool exported.')
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        obj = self.context

        if self.environ.shouldPurge():
            obj.default_skin = ''
            obj.request_varname = 'portal_skin'
            obj.allow_any = 0
            obj.cookie_persistence = 0
            self._purgeObjects()
            self._purgeSkinPaths()

        if node.hasAttribute('default_skin'):
            obj.default_skin = str(node.getAttribute('default_skin'))
        if node.hasAttribute('request_varname'):
            obj.request_varname = str(node.getAttribute('request_varname'))
        if node.hasAttribute('allow_any'):
            allow_any = node.getAttribute('allow_any')
            obj.allow_any = int(self._convertToBoolean(allow_any))
        if node.hasAttribute('cookie_persistence'):
            persistence = node.getAttribute('cookie_persistence')
            obj.cookie_persistence = int(self._convertToBoolean(persistence))
        self._initObjects(node)
        self._initSkinPaths(node)

        self._logger.info('Skins tool imported.')

    def _extractSkinPaths(self):
        fragment = self._doc.createDocumentFragment()
        for k, v in self.context.getSkinPaths():
            node = self._doc.createElement('skin-path')
            node.setAttribute('name', k)
            for layer in [
                    layer.strip()
                    for layer in v.split(',') if layer.strip()]:
                child = self._doc.createElement('layer')
                child.setAttribute('name', layer)
                node.appendChild(child)
            fragment.appendChild(node)
        return fragment

    def _purgeSkinPaths(self):
        self.context._getSelections().clear()

    def _initSkinPaths(self, node):
        for child in node.childNodes:
            if child.nodeName != 'skin-path':
                continue
            path_id = str(child.getAttribute('name'))
            if str(child.getAttribute('remove')):
                self._removeSkin(skin_name=path_id)
                continue
            if path_id == '*':
                for path_id, path in self.context._getSelections().items():
                    path = self._updatePath(path, child)
                    self.context.addSkinSelection(path_id, path)
            else:
                path = ''
                if child.hasAttribute('based-on'):
                    try:
                        basename = child.getAttribute('based-on')
                        path = self.context._getSelections()[basename]
                    except KeyError:
                        pass
                if path_id in self.context._getSelections():
                    oldpath = self.context._getSelections()[path_id].split(',')
                    newlayerstart = child.firstChild
                    for layer in oldpath:
                        if layer not in path:
                            layernode = self._doc.createElement('layer')
                            layernode.setAttribute('name', layer)
                            if oldpath.index(layer) == 0:
                                layernode.setAttribute('insert-before', '*')
                            else:
                                pos = oldpath[oldpath.index(layer) - 1]
                                layernode.setAttribute('insert-after', pos)
                            child.insertBefore(layernode, newlayerstart)
                path = self._updatePath(path, child)
                self.context.addSkinSelection(path_id, path)
        #
        # Purge and rebuild the skin path, now that we have added our stuff.
        # Don't bother if no REQUEST is present, e.g. when running unit tests
        #
        request = getattr(self.context, 'REQUEST', None)
        skinnable = aq_parent(aq_inner(self.context))
        if request is not None and skinnable is not None:
            skinnable.clearCurrentSkin()
            skinnable.setupCurrentSkin(request)

    def _updatePath(self, path, node):
        path = [name.strip() for name in path.split(',') if name.strip()]

        for child in node.childNodes:
            if child.nodeName != 'layer':
                continue
            layer_name = child.getAttribute('name')
            if layer_name in path:
                path.remove(layer_name)

            if child.hasAttribute('insert-before'):
                insert_before = child.getAttribute('insert-before')
                if insert_before == '*':
                    path.insert(0, layer_name)
                    continue
                else:
                    try:
                        index = path.index(insert_before)
                        path.insert(index, layer_name)
                        continue
                    except ValueError:
                        pass
            elif child.hasAttribute('insert-after'):
                insert_after = child.getAttribute('insert-after')
                if insert_after == '*':
                    pass
                else:
                    try:
                        index = path.index(insert_after)
                        path.insert(index + 1, layer_name)
                        continue
                    except ValueError:
                        pass

            if not child.hasAttribute('remove'):
                path.append(layer_name)

        return str(','.join(path))

    def _removeSkin(self, skin_name=None):
        """
        Remove a skin from the skinstool
        """
        skins = self.context.getSkinSelections()
        if skin_name in skins:
            self.context.manage_skinLayers(chosen=[skin_name], del_skin=1)


def importSkinsTool(context):
    """Import skins tool FSDirViews and skin paths from an XML file.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(ISkinsTool)
    if tool is None:
        logger = context.getLogger('skins')
        logger.debug('Nothing to import.')
        return

    importObjects(tool, '', context)


def exportSkinsTool(context):
    """Export skins tool FSDVs and skin paths as an XML file.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(ISkinsTool)
    if tool is None:
        logger = context.getLogger('skins')
        logger.debug('Nothing to export.')
        return

    exportObjects(tool, '', context)
