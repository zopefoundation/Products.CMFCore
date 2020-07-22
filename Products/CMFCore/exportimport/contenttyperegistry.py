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
"""Content type registry xml adapters and setup handlers.
"""

from zope.component import adapts
from zope.component import getSiteManager

from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects

from ..interfaces import IContentTypeRegistry


class ContentTypeRegistryXMLAdapter(XMLAdapterBase):

    """XML im- and exporter for ContentTypeRegistry.
    """

    adapts(IContentTypeRegistry, ISetupEnviron)

    _LOGGER_ID = 'contenttypes'

    name = 'contenttyperegistry'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractPredicates())

        self._logger.info('Content type registry exported.')
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgePredicates()

        self._initPredicates(node)

        self._logger.info('Content type registry imported.')

    def _extractPredicates(self):
        fragment = self._doc.createDocumentFragment()
        for predicate_id, info in self.context.listPredicates():
            child = self._doc.createElement('predicate')
            child.setAttribute('name', predicate_id)
            child.setAttribute('predicate_type', info[0].PREDICATE_TYPE)
            child.setAttribute('content_type_name', info[1])
            for argument in self._crackArgs(info[0]):
                sub = self._doc.createElement('argument')
                sub.setAttribute('value', argument)
                child.appendChild(sub)
            fragment.appendChild(child)
        return fragment

    def _purgePredicates(self):
        self.context.__init__()

    def _initPredicates(self, node):
        for child in node.childNodes:
            if child.nodeName != 'predicate':
                continue
            parent = self.context

            predicate_id = str(child.getAttribute('name'))
            if predicate_id not in parent.predicate_ids:
                predicate_type = str(child.getAttribute('predicate_type'))
                parent.addPredicate(predicate_id, predicate_type)

            if child.hasAttribute('content_type_name'):
                ct_type_name = str(child.getAttribute('content_type_name'))
                parent.assignTypeName(predicate_id, ct_type_name)

            if child.hasAttribute('insert-before'):
                insert_before = child.getAttribute('insert-before')
                self._movePredicate(predicate_id, insert_before, 0)
            elif child.hasAttribute('insert-after'):
                insert_after = child.getAttribute('insert-after')
                self._movePredicate(predicate_id, insert_after, 1)

            arguments = []
            for sub in child.childNodes:
                if sub.nodeName != 'argument':
                    continue
                arguments.append(str(sub.getAttribute('value')))
            if arguments:
                parent.getPredicate(predicate_id).edit(*arguments)

    _KNOWN_PREDICATE_TYPES = {
        'major_minor': lambda x: (','.join(x.major or ()),
                                  ','.join(x.minor or ())),
        'extension': lambda x: (','.join(x.extensions or ()),),
        'mimetype_regex': lambda x: (x.pattern and x.pattern.pattern or '',),
        'name_regex': lambda x: (x.pattern and x.pattern.pattern or '',),
    }

    def _crackArgs(self, predicate):
        cracker = self._KNOWN_PREDICATE_TYPES.get(predicate.PREDICATE_TYPE)
        if cracker is not None:
            return cracker(predicate)
        return ()  # XXX:  raise?

    def _movePredicate(self, id, position_id, delta=0):
        predicate_ids = list(self.context.predicate_ids)
        if position_id == '*':
            position_id = predicate_ids[-delta]
        if position_id == id:
            return
        try:
            predicate_ids.remove(id)
            position = predicate_ids.index(position_id)
            predicate_ids.insert(position + delta, id)
        except ValueError:
            return
        self.context.predicate_ids = tuple(predicate_ids)


def importContentTypeRegistry(context):
    """Import content type registry settings from an XML file.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(IContentTypeRegistry)
    if tool is None:
        logger = context.getLogger('contenttypes')
        logger.debug('Nothing to import.')
        return

    importObjects(tool, '', context)


def exportContentTypeRegistry(context):
    """Export content type registry settings as an XML file.
    """
    sm = getSiteManager(context.getSite())
    tool = sm.queryUtility(IContentTypeRegistry)
    if tool is None:
        logger = context.getLogger('contenttypes')
        logger.debug('Nothing to export.')
        return

    exportObjects(tool, '', context)
