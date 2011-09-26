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
""" PortalFolder: CMF-enabled Folder objects.
"""

import base64
import marshal
import re

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import aq_parent, aq_inner, aq_base
from App.class_init import InitializeClass
from OFS.Folder import Folder
from OFS.OrderSupport import OrderSupport
from zope.component import getUtility
from zope.component import queryUtility
from zope.component.factory import Factory
from zope.interface import implements

from Products.CMFCore.CMFCatalogAware import OpaqueItemManager
from Products.CMFCore.DynamicType import DynamicType
from Products.CMFCore.exceptions import AccessControl_Unauthorized
from Products.CMFCore.exceptions import BadRequest
from Products.CMFCore.exceptions import zExceptions_Unauthorized
from Products.CMFCore.interfaces import IContentTypeRegistry
from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.interfaces import IMutableMinimalDublinCore
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.interfaces import ITypesTool
from Products.CMFCore.permissions import AddPortalContent
from Products.CMFCore.permissions import AddPortalFolders
from Products.CMFCore.permissions import DeleteObjects
from Products.CMFCore.permissions import ListFolderContents
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.permissions import ManageProperties
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import _checkPermission


class PortalFolderBase(DynamicType, OpaqueItemManager, Folder):

    """Base class for portal folder.
    """

    implements(IFolderish, IMutableMinimalDublinCore)

    security = ClassSecurityInfo()

    description = ''

    manage_options = ( Folder.manage_options[:1]
                     + ({'label': 'Components',
                         'action': 'manage_components'},)
                     + ({'label': 'Components Folder',
                         'action': '++etc++site/manage_main'},)
                     + Folder.manage_options[1:]
                     )

    def __init__(self, id, title='', description=''):
        self.id = id
        self.title = title
        self.description = description

    #
    #   'IMutableMinimalDublinCore' interface methods
    #
    security.declareProtected(View, 'Title')
    def Title(self):
        """ Dublin Core Title element - resource name.
        """
        return self.title

    security.declareProtected(View, 'Description')
    def Description(self):
        """ Dublin Core Description element - resource summary.
        """
        return self.description

    security.declareProtected(View, 'Type')
    def Type(self):
        """ Dublin Core Type element - resource type.
        """
        ti = self.getTypeInfo()
        return ti is not None and ti.Title() or 'Unknown'

    security.declareProtected(ManageProperties, 'setTitle')
    def setTitle(self, title):
        """ Set Dublin Core Title element - resource name.
        """
        self.title = title

    security.declareProtected(ManageProperties, 'setDescription')
    def setDescription(self, description):
        """ Set Dublin Core Description element - resource summary.
        """
        self.description = description

    #
    #   other methods
    #
    security.declareProtected(ManageProperties, 'edit')
    def edit(self, title='', description=''):
        """
        Edit the folder title (and possibly other attributes later)
        """
        self.setTitle( title )
        self.setDescription( description )
        # BBB: for ICatalogAware subclasses
        if getattr(self, 'reindexObject', None) is not None:
            self.reindexObject()

    security.declarePublic('allowedContentTypes')
    def allowedContentTypes( self ):
        """
            List type info objects for types which can be added in
            this folder.
        """
        ttool = getUtility(ITypesTool)
        myType = ttool.getTypeInfo(self)
        result = ttool.listTypeInfo()

        if myType is not None:
            return [t for t in result if myType.allowType(t.getId()) and
                    t.isConstructionAllowed(self)]

        return [t for t in result if t.isConstructionAllowed(self)]

    def _filteredItems( self, ids, filt ):
        """
            Apply filter, a mapping, to child objects indicated by 'ids',
            returning a sequence of ( id, obj ) tuples.
        """
        # Restrict allowed content types
        if filt is None:
            filt = {}
        else:
            # We'll modify it, work on a copy.
            filt = filt.copy()
        pt = filt.get('portal_type', [])
        if isinstance(pt, basestring):
            pt = [pt]
        ttool = getUtility(ITypesTool)
        allowed_types = ttool.listContentTypes()
        if not pt:
            pt = allowed_types
        else:
            pt = [t for t in pt if t in allowed_types]
        if not pt:
            # After filtering, no types remain, so nothing should be
            # returned.
            return []
        filt['portal_type'] = pt

        query = ContentFilter(**filt)
        result = []
        append = result.append
        get = self._getOb
        for id in ids:
            obj = get( id )
            if query(obj):
                append( (id, obj) )
        return result

    #
    #   'IFolderish' interface methods
    #
    security.declarePublic('contentItems')
    def contentItems(self, filter=None):
        # List contentish and folderish sub-objects and their IDs.
        # (method is without docstring to disable publishing)
        #
        ids = self.objectIds()
        return self._filteredItems(ids, filter)

    security.declarePublic('contentIds')
    def contentIds(self, filter=None):
        # List IDs of contentish and folderish sub-objects.
        # (method is without docstring to disable publishing)
        #
        return [ item[0] for item in self.contentItems(filter) ]

    security.declarePublic('contentValues')
    def contentValues(self, filter=None):
        # List contentish and folderish sub-objects.
        # (method is without docstring to disable publishing)
        #
        return [ item[1] for item in self.contentItems(filter) ]

    security.declareProtected(ListFolderContents, 'listFolderContents')
    def listFolderContents(self, contentFilter=None):
        """ List viewable contentish and folderish sub-objects.
        """
        l = []
        for id, obj in self.contentItems(contentFilter):
            # validate() can either raise Unauthorized or return 0 to
            # mean unauthorized.
            try:
                if getSecurityManager().validate(self, self, id, obj):
                    l.append(obj)
            except zExceptions_Unauthorized:  # Catch *all* Unauths!
                pass
        return l

    #
    #   webdav Resource method
    #

    # protected by 'WebDAV access'
    def listDAVObjects(self):
        # List sub-objects for PROPFIND requests.
        # (method is without docstring to disable publishing)
        #
        if _checkPermission(ManagePortal, self):
            return self.objectValues()
        else:
            return self.listFolderContents()

    #
    #   other methods
    #
    security.declarePublic('encodeFolderFilter')
    def encodeFolderFilter(self, REQUEST):
        """
            Parse cookie string for using variables in dtml.
        """
        filter = {}
        for key, value in REQUEST.items():
            if key[:10] == 'filter_by_':
                filter[key[10:]] = value
        encoded = base64.encodestring( marshal.dumps(filter) ).strip()
        encoded = ''.join( encoded.split('\n') )
        return encoded

    security.declarePublic('decodeFolderFilter')
    def decodeFolderFilter(self, encoded):
        """
            Parse cookie string for using variables in dtml.
        """
        filter = {}
        if encoded:
            filter.update(marshal.loads(base64.decodestring(encoded)))
        return filter

    def content_type( self ):
        """
            WebDAV needs this to do the Right Thing (TM).
        """
        return None

    def PUT_factory( self, name, typ, body ):
        """ Factory for PUT requests to objects which do not yet exist.

        Used by NullResource.PUT.

        Returns -- Bare and empty object of the appropriate type (or None, if
        we don't know what to do)
        """
        ctr = queryUtility(IContentTypeRegistry)
        if ctr is None:
            return None

        typeObjectName = ctr.findTypeName(name, typ, body)
        if typeObjectName is None:
            return None

        self.invokeFactory( typeObjectName, name )

        # invokeFactory does too much, so the object has to be removed again
        obj = aq_base( self._getOb( name ) )
        self._delObject( name )
        return obj

    security.declareProtected(AddPortalContent, 'invokeFactory')
    def invokeFactory(self, type_name, id, RESPONSE=None, *args, **kw):
        """ Invokes the portal_types tool.
        """
        ttool = getUtility(ITypesTool)
        myType = ttool.getTypeInfo(self)

        if myType is not None:
            if not myType.allowType( type_name ):
                raise ValueError('Disallowed subobject type: %s' % type_name)

        return ttool.constructContent(type_name, self, id, RESPONSE, *args, **kw)

    security.declareProtected(AddPortalContent, 'checkIdAvailable')
    def checkIdAvailable(self, id):
        try:
            self._checkId(id)
        except BadRequest:
            return False
        else:
            return True

    def MKCOL_handler(self,id,REQUEST=None,RESPONSE=None):
        """
            Handle WebDAV MKCOL.
        """
        self.manage_addFolder( id=id, title='' )

    def _checkId(self, id, allow_dup=0):
        PortalFolderBase.inheritedAttribute('_checkId')(self, id, allow_dup)

        if allow_dup:
            return

        # FIXME: needed to allow index_html for join code
        if id == 'index_html':
            return

        # Another exception: Must allow "syndication_information" to enable
        # Syndication...
        if id == 'syndication_information':
            return

        # IDs starting with '@@' are reserved for views.
        if id[:2] == '@@':
            raise BadRequest('The id "%s" is invalid because it begins with '
                             '"@@".' % id)

        # This code prevents people other than the portal manager from
        # overriding skinned names and tools.
        if not getSecurityManager().checkPermission(ManagePortal, self):
            ob = aq_inner(self)
            while ob is not None:
                if ISiteRoot.providedBy(ob):
                    break
                ob = aq_parent(ob)

            if ob is not None:
                # If the portal root has a non-contentish object by this name,
                # don't allow an override.
                if (hasattr(ob, id) and
                    id not in ob.contentIds() and
                    # Allow root doted prefixed object name overrides
                    not id.startswith('.')):
                    raise BadRequest('The id "%s" is reserved.' % id)
            # Don't allow ids used by Method Aliases.
            ti = self.getTypeInfo()
            if ti and ti.queryMethodID(id, context=self):
                raise BadRequest('The id "%s" is reserved.' % id)
        # Otherwise we're ok.

    def _verifyObjectPaste(self, object, validate_src=1):
        # This assists the version in OFS.CopySupport.
        # It enables the clipboard to function correctly
        # with objects created by a multi-factory.
        mt = getattr(object, '__factory_meta_type__', None)
        meta_types = getattr(self, 'all_meta_types', None)

        if mt is not None and meta_types is not None:
            mt_permission = None

            if callable(meta_types):
                meta_types = meta_types()

            for d in meta_types:
                if d['name'] == mt:
                    mt_permission = d.get('permission')
                    break

            if mt_permission is not None:
                sm = getSecurityManager()

                if sm.checkPermission(mt_permission, self):
                    if validate_src:
                        # Ensure the user is allowed to access the object on
                        # the clipboard.
                        parent = aq_parent(aq_inner(object))

                        if not sm.validate(None, parent, None, object):
                            raise AccessControl_Unauthorized(object.getId())

                        if validate_src == 2: # moving
                            if not sm.checkPermission(DeleteObjects, parent):
                                raise AccessControl_Unauthorized('Delete not '
                                                                 'allowed.')
                else:
                    raise AccessControl_Unauthorized('You do not possess the '
                            '%r permission in the context of the container '
                            'into which you are pasting, thus you are not '
                            'able to perform this operation.' % mt_permission)
            else:
                raise AccessControl_Unauthorized('The object %r does not '
                        'support this operation.' % object.getId())
        else:
            # Call OFS' _verifyObjectPaste if necessary
            PortalFolderBase.inheritedAttribute(
                '_verifyObjectPaste')(self, object, validate_src)

        # Finally, check allowed content types
        if hasattr(aq_base(object), 'getPortalTypeName'):

            type_name = object.getPortalTypeName()

            if type_name is not None:

                ttool = getUtility(ITypesTool)
                myType = ttool.getTypeInfo(self)

                if myType is not None and not myType.allowType(type_name):
                    raise ValueError('Disallowed subobject type: %s'
                                        % type_name)

                # Check for workflow guards
                objType = ttool.getTypeInfo(type_name)
                if ( objType is not None and
                     not objType._checkWorkflowAllowed(self) ):
                    raise ValueError('Pasting not allowed in this workflow')

    security.setPermissionDefault(AddPortalContent, ('Owner','Manager'))

    security.declareProtected(AddPortalFolders, 'manage_addFolder')
    def manage_addFolder( self
                        , id
                        , title=''
                        , REQUEST=None
                        ):
        """ Add a new folder-like object with id *id*.

        IF present, use the parent object's 'mkdir' alias; otherwise, just add
        a PortalFolder.
        """
        ti = self.getTypeInfo()
        method_id = ti and ti.queryMethodID('mkdir', context=self)
        if method_id:
            # call it
            getattr(self, method_id)(id=id)
        else:
            self.invokeFactory( type_name='Folder', id=id )

        ob = self._getOb( id )
        ob.setTitle( title )
        try:
            ob.reindexObject()
        except AttributeError:
            pass

        if REQUEST is not None:
            return self.manage_main(self, REQUEST, update_menu=1)

InitializeClass(PortalFolderBase)


class PortalFolder(OrderSupport, PortalFolderBase):

    """Implements portal content management, but not UI details.
    """

    portal_type = 'Folder'

    security = ClassSecurityInfo()

    manage_options = ( OrderSupport.manage_options +
                       PortalFolderBase.manage_options[1:] )

    security.declareProtected(AddPortalFolders, 'manage_addPortalFolder')
    def manage_addPortalFolder(self, id, title='', REQUEST=None):
        """Add a new PortalFolder object with id *id*.
        """
        ob = PortalFolder(id, title)
        self._setObject(id, ob, suppress_events=True)
        if REQUEST is not None:
            return self.folder_contents( # XXX: ick!
                self, REQUEST, portal_status_message="Folder added")

InitializeClass(PortalFolder)

PortalFolderFactory = Factory(PortalFolder)

manage_addPortalFolder = PortalFolder.manage_addPortalFolder.im_func


class ContentFilter:

    """Represent a predicate against a content object's metadata.
    """

    MARKER = []
    filterSubject = []
    def __init__( self
                , Title=MARKER
                , Creator=MARKER
                , Subject=MARKER
                , Description=MARKER
                , created=MARKER
                , created_usage='range:min'
                , modified=MARKER
                , modified_usage='range:min'
                , Type=MARKER
                , portal_type=MARKER
                , **Ignored
                ):

        self.predicates = []
        self.description = []

        if Title is not self.MARKER:
            self.predicates.append( lambda x, pat=re.compile( Title ):
                                      pat.search( x.Title() ) )
            self.description.append( 'Title: %s' % Title )

        if Creator and Creator is not self.MARKER:
            self.predicates.append( lambda x, creator=Creator:
                                    creator in x.listCreators() )
            self.description.append( 'Creator: %s' % Creator )

        if Subject and Subject is not self.MARKER:
            self.filterSubject = Subject
            self.predicates.append( self.hasSubject )
            self.description.append( 'Subject: %s' % ', '.join(Subject) )

        if Description is not self.MARKER:
            self.predicates.append( lambda x, pat=re.compile( Description ):
                                      pat.search( x.Description() ) )
            self.description.append( 'Description: %s' % Description )

        if created is not self.MARKER:
            if created_usage == 'range:min':
                self.predicates.append( lambda x, cd=created:
                                          cd <= x.created() )
                self.description.append( 'Created since: %s' % created )
            if created_usage == 'range:max':
                self.predicates.append( lambda x, cd=created:
                                          cd >= x.created() )
                self.description.append( 'Created before: %s' % created )

        if modified is not self.MARKER:
            if modified_usage == 'range:min':
                self.predicates.append( lambda x, md=modified:
                                          md <= x.modified() )
                self.description.append( 'Modified since: %s' % modified )
            if modified_usage == 'range:max':
                self.predicates.append( lambda x, md=modified:
                                          md >= x.modified() )
                self.description.append( 'Modified before: %s' % modified )

        if Type:
            if isinstance(Type, basestring):
                Type = [Type]
            self.predicates.append( lambda x, Type=Type:
                                      x.Type() in Type )
            self.description.append( 'Type: %s' % ', '.join(Type) )

        if portal_type and portal_type is not self.MARKER:
            if isinstance(portal_type, basestring):
                portal_type = [portal_type]
            self.predicates.append( lambda x, pt=portal_type:
                                    hasattr(aq_base(x), 'getPortalTypeName')
                                    and x.getPortalTypeName() in pt )
            self.description.append( 'Portal Type: %s'
                                     % ', '.join(portal_type) )

    def hasSubject( self, obj ):
        """
        Converts Subject string into a List for content filter view.
        """
        for sub in obj.Subject():
            if sub in self.filterSubject:
                return 1
        return 0

    def __call__( self, content ):

        for predicate in self.predicates:

            try:
                if not predicate( content ):
                    return 0
            except (AttributeError, KeyError, IndexError, ValueError):
                # predicates are *not* allowed to throw exceptions
                return 0

        return 1

    def __str__( self ):
        """
            Return a stringified description of the filter.
        """
        return '; '.join(self.description)
