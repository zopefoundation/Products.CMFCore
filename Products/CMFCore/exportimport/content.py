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
"""Filesystem exporter / importer adapters.
"""

from csv import reader
from csv import writer
from ConfigParser import ConfigParser
from StringIO import StringIO

from zope.component import getUtility
from zope.interface import implements

from Products.CMFCore.interfaces import ITypesTool
from Products.GenericSetup.content import _globtest
from Products.GenericSetup.interfaces import IFilesystemExporter
from Products.GenericSetup.interfaces import IFilesystemImporter

#
#   setup_tool handlers
#
def exportSiteStructure(context):
    IFilesystemExporter(context.getSite()).export(context, 'structure', True)

def importSiteStructure(context):
    IFilesystemImporter(context.getSite()).import_(context, 'structure', True)


def encode_if_needed(text, encoding):
    if isinstance(text, unicode):
        result = text.encode(encoding)
    else:
        # no need to encode;
        # let's avoid double encoding in case of encoded string
        result = text
    return result


#
#   Filesystem export/import adapters
#
class StructureFolderWalkingAdapter(object):
    """ Tree-walking exporter for "folderish" types.

    Folderish instances are mapped to directories within the 'structure'
    portion of the profile, where the folder's relative path within the site
    corresponds to the path of its directory under 'structure'.

    The subobjects of a folderish instance are enumerated in the '.objects'
    file in the corresponding directory.  This file is a CSV file, with one
    row per subobject, with the following wtructure::

     "<subobject id>","<subobject portal_type>"

    Subobjects themselves are represented as individual files or
    subdirectories within the parent's directory.
    If the import step finds that any objects specified to be created by the
    'structure' directory setup already exist, these objects will be deleted
    and then recreated by the profile.  The existence of a '.preserve' file
    within the 'structure' hierarchy allows specification of objects that
    should not be deleted.  '.preserve' files should contain one preserve
    rule per line, with shell-style globbing supported (i.e. 'b*' will match
    all objects w/ id starting w/ 'b'.

    Similarly, a '.delete' file can be used to specify the deletion of any
    objects that exist in the site but are NOT in the 'structure' hierarchy,
    and thus will not be recreated during the import process.
    """

    implements(IFilesystemExporter, IFilesystemImporter)

    def __init__(self, context):
        self.context = context

    def export(self, export_context, subdir, root=False):
        """ See IFilesystemExporter.
        """
        self._encoding = self.context.getProperty('default_charset', 'utf-8')

        # Enumerate exportable children
        exportable = self.context.contentItems()
        exportable = [x + (IFilesystemExporter(x, None),) for x in exportable]
        exportable = [x for x in exportable if x[1] is not None]

        stream = StringIO()
        csv_writer = writer(stream)

        for object_id, object, ignored in exportable:
            csv_writer.writerow((object_id, object.getPortalTypeName()))

        if not root:
            subdir = '%s/%s' % (subdir, self.context.getId())

        export_context.writeDataFile('.objects',
                                     text=stream.getvalue(),
                                     content_type='text/comma-separated-values',
                                     subdir=subdir,
                                    )

        parser = ConfigParser()

        title = self.context.Title()
        description = self.context.Description()
        # encode if needed; ConfigParser does not support unicode !
        title_str = encode_if_needed(title, self._encoding)
        description_str = encode_if_needed(description, self._encoding)
        parser.set('DEFAULT', 'Title', title_str)
        parser.set('DEFAULT', 'Description', description_str)

        stream = StringIO()
        parser.write(stream)

        export_context.writeDataFile('.properties',
                                    text=stream.getvalue(),
                                    content_type='text/plain',
                                    subdir=subdir,
                                    )

        for id, object in self.context.objectItems():

            adapter = IFilesystemExporter(object, None)

            if adapter is not None:
                adapter.export(export_context, subdir)

    def import_(self, import_context, subdir, root=False):
        """ See IFilesystemImporter.
        """
        context = self.context
        if not root:
            subdir = '%s/%s' % (subdir, context.getId())

        objects = import_context.readDataFile('.objects', subdir)
        if objects is None:
            return

        dialect = 'excel'
        stream = StringIO(objects)

        rowiter = reader(stream, dialect)
        ours = filter(None, tuple(rowiter))
        our_ids = set([item[0] for item in ours])

        prior = set(context.contentIds())

        preserve = import_context.readDataFile('.preserve', subdir)
        if not preserve:
            preserve = set()
        else:
            preservable = prior.intersection(our_ids)
            preserve = set(_globtest(preserve, preservable))

        delete = import_context.readDataFile('.delete', subdir)
        if not delete:
            delete= set()
        else:
            deletable = prior.difference(our_ids)
            delete = set(_globtest(delete, deletable))

        # if it's in our_ids and NOT in preserve, or if it's not in
        # our_ids but IS in delete, we're gonna delete it
        delete = our_ids.difference(preserve).union(delete)

        for id in prior.intersection(delete):
            context._delObject(id)

        existing = context.objectIds()

        for object_id, portal_type in ours:

            if object_id not in existing:
                object = self._makeInstance(object_id, portal_type,
                                            subdir, import_context)
                if object is None:
                    logger = import_context.getLogger('SFWA')
                    logger.warning("Couldn't make instance: %s/%s" %
                                   (subdir, object_id))
                    continue

            wrapped = context._getOb(object_id)

            IFilesystemImporter(wrapped).import_(import_context, subdir)

    def _makeInstance(self, id, portal_type, subdir, import_context):

        context = self.context
        properties = import_context.readDataFile('.properties',
                                                 '%s/%s' % (subdir, id))
        tool = getUtility(ITypesTool)

        try:
            tool.constructContent(portal_type, context, id)
        except ValueError: # invalid type
            return None

        content = context._getOb(id)

        if properties is not None:
            lines = properties.splitlines()

            stream = StringIO('\n'.join(lines))
            parser = ConfigParser(defaults={'title': '', 'description': 'NONE'})
            parser.readfp(stream)

            title = parser.get('DEFAULT', 'title')
            description = parser.get('DEFAULT', 'description')

            content.setTitle(title)
            content.setDescription(description)

        return content
