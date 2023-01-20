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
""" Basic Site content type registry
"""

import os
import re
import urllib

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.special_dtml import DTMLFile
from OFS.SimpleItem import SimpleItem
from Persistence import PersistentMapping
from zope.component import getUtility
from zope.interface import implementer
from ZPublisher.mapply import mapply

from .interfaces import IContentTypeRegistry
from .interfaces import IContentTypeRegistryPredicate
from .interfaces import ITypesTool
from .permissions import ManagePortal
from .utils import _dtmldir
from .utils import registerToolInterface


@implementer(IContentTypeRegistryPredicate)
class MajorMinorPredicate(SimpleItem):

    """
        Predicate matching on 'major/minor' content types.
        Empty major or minor implies wildcard (all match).
    """

    major = minor = None
    PREDICATE_TYPE = 'major_minor'

    security = ClassSecurityInfo()

    def __init__(self, id):
        self.id = id

    @security.protected(ManagePortal)
    def getMajorType(self):
        """ Get major content types.
        """
        if self.major is None:
            return 'None'
        return ' '.join(self.major)

    @security.protected(ManagePortal)
    def getMinorType(self):
        """ Get minor content types.
        """
        if self.minor is None:
            return 'None'
        return ' '.join(self.minor)

    @security.protected(ManagePortal)
    def edit(self, major, minor, COMMA_SPLIT=re.compile(r'[, ]')):

        if major == 'None':
            major = None
        if isinstance(major, str):
            major = [_f for _f in COMMA_SPLIT.split(major) if _f]

        if minor == 'None':
            minor = None
        if isinstance(minor, str):
            minor = [_f for _f in COMMA_SPLIT.split(minor) if _f]

        self.major = major
        self.minor = minor

    #
    #   ContentTypeRegistryPredicate interface
    #
    security.declareObjectPublic()

    def __call__(self, name, typ, body):
        """
            Return true if the rule matches, else false.
        """
        if self.major is None:
            return 0

        if self.minor is None:
            return 0

        typ = typ or '/'
        if '/' not in typ:
            typ = typ + '/'
        major, minor = typ.split('/', 1)

        if self.major and major not in self.major:
            return 0

        if self.minor and minor not in self.minor:
            return 0

        return 1

    @security.protected(ManagePortal)
    def getTypeLabel(self):
        """
            Return a human-readable label for the predicate type.
        """
        return self.PREDICATE_TYPE

    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'predicateWidget')
    predicateWidget = DTMLFile('majorMinorWidget', _dtmldir)


InitializeClass(MajorMinorPredicate)


@implementer(IContentTypeRegistryPredicate)
class ExtensionPredicate(SimpleItem):

    """
        Predicate matching on filename extensions.
    """

    extensions = None
    PREDICATE_TYPE = 'extension'

    security = ClassSecurityInfo()

    def __init__(self, id):
        self.id = id

    @security.protected(ManagePortal)
    def getExtensions(self):
        """ Get filename extensions.
        """
        if self.extensions is None:
            return 'None'
        return ' '.join(self.extensions)

    @security.protected(ManagePortal)
    def edit(self, extensions, COMMA_SPLIT=re.compile(r'[, ]')):

        if extensions == 'None':
            extensions = None
        if isinstance(extensions, str):
            extensions = [_f for _f in COMMA_SPLIT.split(extensions) if _f]

        self.extensions = extensions

    #
    #   ContentTypeRegistryPredicate interface
    #
    security.declareObjectPublic()

    def __call__(self, name, typ, body):
        """
            Return true if the rule matches, else false.
        """
        if self.extensions is None:
            return 0

        _base, ext = os.path.splitext(name)
        if ext and ext[0] == '.':
            ext = ext[1:]

        return ext in self.extensions

    @security.protected(ManagePortal)
    def getTypeLabel(self):
        """
            Return a human-readable label for the predicate type.
        """
        return self.PREDICATE_TYPE

    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'predicateWidget')
    predicateWidget = DTMLFile('extensionWidget', _dtmldir)


InitializeClass(ExtensionPredicate)


@implementer(IContentTypeRegistryPredicate)
class MimeTypeRegexPredicate(SimpleItem):

    """
        Predicate matching only on 'typ', using regex matching for
        string patterns (other objects conforming to 'match' can
        also be passed).
    """

    pattern = None
    PREDICATE_TYPE = 'mimetype_regex'

    security = ClassSecurityInfo()

    def __init__(self, id):
        self.id = id

    @security.protected(ManagePortal)
    def getPatternStr(self):
        if self.pattern is None:
            return 'None'
        return self.pattern.pattern

    @security.protected(ManagePortal)
    def edit(self, pattern):
        if pattern == 'None':
            pattern = None
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        self.pattern = pattern

    #
    #   ContentTypeRegistryPredicate interface
    #
    security.declareObjectPublic()

    def __call__(self, name, typ, body):
        """
            Return true if the rule matches, else false.
        """
        if self.pattern is None:
            return 0

        return self.pattern.match(typ)

    @security.protected(ManagePortal)
    def getTypeLabel(self):
        """
            Return a human-readable label for the predicate type.
        """
        return self.PREDICATE_TYPE

    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'predicateWidget')
    predicateWidget = DTMLFile('patternWidget', _dtmldir)


InitializeClass(MimeTypeRegexPredicate)


@implementer(IContentTypeRegistryPredicate)
class NameRegexPredicate(SimpleItem):

    """
        Predicate matching only on 'name', using regex matching
        for string patterns (other objects conforming to 'match'
        and 'pattern' can also be passed).
    """

    pattern = None
    PREDICATE_TYPE = 'name_regex'

    security = ClassSecurityInfo()

    def __init__(self, id):
        self.id = id

    @security.protected(ManagePortal)
    def getPatternStr(self):
        """
            Return a string representation of our pattern.
        """
        if self.pattern is None:
            return 'None'
        return self.pattern.pattern

    @security.protected(ManagePortal)
    def edit(self, pattern):
        if pattern == 'None':
            pattern = None
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        self.pattern = pattern

    #
    #   ContentTypeRegistryPredicate interface
    #
    security.declareObjectPublic()

    def __call__(self, name, typ, body):
        """
            Return true if the rule matches, else false.
        """
        if self.pattern is None:
            return 0

        return self.pattern.match(name)

    @security.protected(ManagePortal)
    def getTypeLabel(self):
        """
            Return a human-readable label for the predicate type.
        """
        return self.PREDICATE_TYPE

    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'predicateWidget')
    predicateWidget = DTMLFile('patternWidget', _dtmldir)


InitializeClass(NameRegexPredicate)


_predicate_types = []


def registerPredicateType(typeID, klass):
    """
        Add a new predicate type.
    """
    _predicate_types.append((typeID, klass))


for klass in (MajorMinorPredicate, ExtensionPredicate, MimeTypeRegexPredicate,
              NameRegexPredicate):
    registerPredicateType(klass.PREDICATE_TYPE, klass)


@implementer(IContentTypeRegistry)
class ContentTypeRegistry(SimpleItem):

    """
        Registry for rules which map PUT args to a CMF Type Object.
    """

    meta_type = 'Content Type Registry'
    id = 'content_type_registry'
    zmi_icon = 'fas fa-expand-arrows-alt'
    zmi_show_add_dialog = False

    manage_options = (
        ({'label': 'Predicates', 'action': 'manage_predicates'},
         {'label': 'Test', 'action': 'manage_testRegistry'}) +
        SimpleItem.manage_options)

    security = ClassSecurityInfo()

    def __init__(self):
        self.predicate_ids = ()
        self.predicates = PersistentMapping()

    #
    #   ZMI
    #
    @security.public
    def listPredicateTypes(self):
        """
        """
        return [x[0] for x in _predicate_types]

    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'manage_predicates')
    manage_predicates = DTMLFile('registryPredList', _dtmldir)

    @security.protected(ManagePortal)
    def doAddPredicate(self, predicate_id, predicate_type, REQUEST):
        """
        """
        self.addPredicate(predicate_id, predicate_type)
        REQUEST['RESPONSE'].redirect(self.absolute_url()
                                     + '/manage_predicates'
                                     + '?manage_tabs_message=Predicate+added.')

    @security.protected(ManagePortal)
    def doUpdatePredicate(self, predicate_id, predicate, typeObjectName,
                          REQUEST):
        """
        """
        self.updatePredicate(predicate_id, predicate, typeObjectName)
        pth = '/manage_predicates?manage_tabs_message=Predicate+updated.'
        REQUEST['RESPONSE'].redirect(f'{self.absolute_url()}{pth}')

    @security.protected(ManagePortal)
    def doMovePredicateUp(self, predicate_id, REQUEST):
        """
        """
        predicate_ids = list(self.predicate_ids)
        ndx = predicate_ids.index(predicate_id)
        if ndx == 0:
            msg = 'Predicate+already+first.'
        else:
            self.reorderPredicate(predicate_id, ndx - 1)
            msg = 'Predicate+moved.'
        REQUEST['RESPONSE'].redirect(self.absolute_url()
                                     + '/manage_predicates'
                                     + '?manage_tabs_message=%s' % msg)

    @security.protected(ManagePortal)
    def doMovePredicateDown(self, predicate_id, REQUEST):
        """
        """
        predicate_ids = list(self.predicate_ids)
        ndx = predicate_ids.index(predicate_id)
        if ndx == len(predicate_ids) - 1:
            msg = 'Predicate+already+last.'
        else:
            self.reorderPredicate(predicate_id, ndx + 1)
            msg = 'Predicate+moved.'
        REQUEST['RESPONSE'].redirect(self.absolute_url()
                                     + '/manage_predicates'
                                     + '?manage_tabs_message=%s' % msg)

    @security.protected(ManagePortal)
    def doRemovePredicate(self, predicate_id, REQUEST):
        """
        """
        self.removePredicate(predicate_id)
        pth = '/manage_predicates?manage_tabs_message=Predicate+removed.'
        REQUEST['RESPONSE'].redirect(f'{self.absolute_url()}{pth}')

    security.declareProtected(ManagePortal,  # NOQA: flake8: D001
                              'manage_testRegistry')
    manage_testRegistry = DTMLFile('registryTest', _dtmldir)

    @security.protected(ManagePortal)
    def doTestRegistry(self, name, content_type, body, REQUEST):
        """
        """
        typeName = self.findTypeName(name, content_type, body)
        if typeName is None:
            typeName = '<unknown>'
        else:
            ttool = getUtility(ITypesTool)
            typeName = ttool.getTypeInfo(typeName).Title()
        REQUEST['RESPONSE'].redirect(self.absolute_url()
                                     + '/manage_testRegistry'
                                     + '?testResults=Type:+%s'
                                     % urllib.parse.quote(typeName))

    #
    #   Predicate manipulation
    #
    @security.public
    def getPredicate(self, predicate_id):
        """
            Find the predicate whose id is 'id';  return the predicate
            object, if found, or else None.
        """
        return self.predicates.get(predicate_id, (None, None))[0]

    @security.public
    def listPredicates(self):
        """List '(id, (predicate, typeObjectName))' tuples for all predicates.
        """
        return tuple([(id, self.predicates[id]) for id in self.predicate_ids])

    @security.public
    def getTypeObjectName(self, predicate_id):
        """
            Find the predicate whose id is 'id';  return the name of
            the type object, if found, or else None.
        """
        return self.predicates.get(predicate_id, (None, None))[1]

    @security.protected(ManagePortal)
    def addPredicate(self, predicate_id, predicate_type):
        """
            Add a predicate to this element of type 'typ' to the registry.
        """
        if predicate_id in self.predicate_ids:
            raise ValueError('Existing predicate: %s' % predicate_id)

        klass = None
        for key, value in _predicate_types:
            if key == predicate_type:
                klass = value

        if klass is None:
            raise ValueError('Unknown predicate type: %s' % predicate_type)

        self.predicates[predicate_id] = (klass(predicate_id), None)
        self.predicate_ids = self.predicate_ids + (predicate_id,)

    @security.protected(ManagePortal)
    def updatePredicate(self, predicate_id, predicate, typeObjectName):
        """
            Update a predicate in this element.
        """
        if predicate_id not in self.predicate_ids:
            raise ValueError('Unknown predicate: %s' % predicate_id)

        predObj = self.predicates[predicate_id][0]
        mapply(predObj.edit, (), predicate.__dict__)
        self.assignTypeName(predicate_id, typeObjectName)

    @security.protected(ManagePortal)
    def removePredicate(self, predicate_id):
        """
            Remove a predicate from the registry.
        """
        del self.predicates[predicate_id]
        idlist = list(self.predicate_ids)
        ndx = idlist.index(predicate_id)
        idlist = idlist[:ndx] + idlist[ndx + 1:]
        self.predicate_ids = tuple(idlist)

    @security.protected(ManagePortal)
    def reorderPredicate(self, predicate_id, newIndex):
        """
            Move a given predicate to a new location in the list.
        """
        idlist = list(self.predicate_ids)
        ndx = idlist.index(predicate_id)
        pred = idlist[ndx]
        idlist = idlist[:ndx] + idlist[ndx + 1:]
        idlist.insert(newIndex, pred)
        self.predicate_ids = tuple(idlist)

    @security.protected(ManagePortal)
    def assignTypeName(self, predicate_id, typeObjectName):
        """
            Bind the given predicate to a particular type object.
        """
        pred, _oldTypeObjName = self.predicates[predicate_id]
        self.predicates[predicate_id] = (pred, typeObjectName)

    #
    #   ContentTypeRegistry interface
    #
    def findTypeName(self, name, typ, body):
        """
            Perform a lookup over a collection of rules, returning the
            the name of the Type object corresponding to name/typ/body.
            Return None if no match found.
        """
        for predicate_id in self.predicate_ids:
            pred, typeObjectName = self.predicates[predicate_id]
            if pred(name, typ, body):
                return typeObjectName

        return None


InitializeClass(ContentTypeRegistry)
registerToolInterface('content_type_registry', IContentTypeRegistry)


def manage_addRegistry(self, REQUEST=None):
    """
        Add a CTR to self.
    """
    CTRID = ContentTypeRegistry.id
    reg = ContentTypeRegistry()
    self._setObject(CTRID, reg)
    reg = self._getOb(CTRID)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()
                                     + '/manage_main'
                                     + '?manage_tabs_message=Registry+added.')
