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

import itertools
import operator
from configparser import ConfigParser
from csv import reader
from csv import writer
from io import StringIO

from DateTime import DateTime
from zope.component import getUtility
from zope.interface import implementer
from zope.publisher.interfaces.http import MethodNotAllowed

from Products.GenericSetup.content import DAVAwareFileAdapter
from Products.GenericSetup.content import _globtest
from Products.GenericSetup.interfaces import IFilesystemExporter
from Products.GenericSetup.interfaces import IFilesystemImporter

from ..interfaces import ITypesTool


#
#   setup_tool handlers
#
def exportSiteStructure(context):
    IFilesystemExporter(context.getSite()).export(context, 'structure', True)


def importSiteStructure(context):
    IFilesystemImporter(context.getSite()).import_(context, 'structure', True)


def encode_if_needed(text, encoding):
    if not isinstance(text, str):
        text = text.decode(encoding)
    # no need to encode;
    # let's avoid double encoding in case of encoded string
    return text


class FolderishDAVAwareFileAdapter(DAVAwareFileAdapter):
    """ A version of the DAVAwareFileAdapter that uses .properties to store
    the DAV result, rather than its own id. For use in serialising folderish
    objects. """

    def _getFileName(self):
        """ Return the name under which our file data is stored.
        """
        return '.properties'


#
#   Filesystem export/import adapters
#
@implementer(IFilesystemExporter, IFilesystemImporter)
class StructureFolderWalkingAdapter:
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

    def __init__(self, context):
        self.context = context
        self._encoding = self.context.getProperty('default_charset', 'utf-8')

    def read_data_file(self, import_context, datafile, subdir):
        out = import_context.readDataFile(datafile, subdir)
        if out is None:
            return out
        return encode_if_needed(out, self._encoding)

    def export(self, export_context, subdir, root=False):
        """ See IFilesystemExporter.
        """
        content_type = 'text/comma-separated-values'

        # Enumerate exportable children
        exportable = self.context.contentItems()
        exportable = [x + (IFilesystemExporter(x, None),) for x in exportable]
        exportable = [x for x in exportable if x[1] is not None]

        objects_stream = StringIO()
        objects_csv_writer = writer(objects_stream)
        wf_stream = StringIO()
        wf_csv_writer = writer(wf_stream)

        if not root:
            subdir = f'{subdir}/{self.context.getId()}'

        try:
            wft = self.context.portal_workflow
        except AttributeError:
            # No workflow tool to export definitions from
            for object_id, object, ignored in exportable:
                objects_csv_writer.writerow((object_id,
                                             object.getPortalTypeName()))
        else:
            for object_id, object, ignored in exportable:
                objects_csv_writer.writerow((object_id,
                                             object.getPortalTypeName()))

                workflows = wft.getWorkflowsFor(object)
                for workflow in workflows:
                    workflow_id = workflow.getId()
                    state_variable = workflow.state_var
                    state_record = wft.getStatusOf(workflow_id, object)
                    if state_record is None:
                        continue
                    state = state_record.get(state_variable)
                    wf_csv_writer.writerow((object_id, workflow_id, state))

            export_context.writeDataFile('.workflow_states',
                                         text=wf_stream.getvalue(),
                                         content_type=content_type,
                                         subdir=subdir)

        export_context.writeDataFile('.objects',
                                     text=objects_stream.getvalue(),
                                     content_type=content_type,
                                     subdir=subdir)

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

        try:
            FolderishDAVAwareFileAdapter(self.context).export(export_context,
                                                              subdir, root)
        except (AttributeError, MethodNotAllowed):
            export_context.writeDataFile('.properties',
                                         text=stream.getvalue(),
                                         content_type='text/plain',
                                         subdir=subdir)

        for id, object in self.context.objectItems():

            adapter = IFilesystemExporter(object, None)

            if adapter is not None:
                adapter.export(export_context, subdir)

    def import_(self, import_context, subdir, root=False):
        """ See IFilesystemImporter.
        """
        context = self.context
        if not root:
            subdir = f'{subdir}/{context.getId()}'

        objects = self.read_data_file(import_context, '.objects', subdir)
        workflow_states = self.read_data_file(import_context,
                                              '.workflow_states', subdir)
        if objects is None:
            return

        dialect = 'excel'
        object_stream = StringIO(objects)
        wf_stream = StringIO(workflow_states)

        object_rowiter = reader(object_stream, dialect)
        ours = [_f for _f in tuple(object_rowiter) if _f]
        our_ids = {item[0] for item in ours}

        prior = set(context.contentIds())

        preserve = self.read_data_file(import_context, '.preserve', subdir)
        if not preserve:
            preserve = set()
        else:
            preservable = prior.intersection(our_ids)
            preserve = set(_globtest(preserve, preservable))

        delete = self.read_data_file(import_context, '.delete', subdir)
        if not delete:
            delete = set()
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

        if workflow_states is not None:
            existing = context.objectIds()
            wft = context.portal_workflow
            wf_rowiter = reader(wf_stream, dialect)
            wf_by_objectid = itertools.groupby(wf_rowiter,
                                               operator.itemgetter(0))

            for object_id, states in wf_by_objectid:
                if object_id not in existing:
                    logger = import_context.getLogger('SFWA')
                    logger.warning("Couldn't set workflow for object %s/%s, it"
                                   " doesn't exist" % (context.id, object_id))
                    continue

                object = context[object_id]
                for object_id, workflow_id, state_id in states:
                    workflow = wft.getWorkflowById(workflow_id)
                    state_variable = workflow.state_var
                    wf_state = {'action': None,
                                'actor': None,
                                'comments': 'Setting state to %s' % state_id,
                                state_variable: state_id,
                                'time': DateTime()}

                    wft.setStatusOf(workflow_id, object, wf_state)
                    workflow.updateRoleMappingsFor(object)

                object.reindexObject()

    def _makeInstance(self, id, portal_type, subdir, import_context):

        context = self.context
        subdir = f'{subdir}/{id}'
        properties = self.read_data_file(import_context, '.properties',
                                         subdir)
        tool = getUtility(ITypesTool)

        try:
            tool.constructContent(portal_type, context, id)
        except ValueError:  # invalid type
            return None

        content = context._getOb(id)

        if properties is not None:
            if '[DEFAULT]' not in properties:
                try:
                    adp = FolderishDAVAwareFileAdapter
                    adp(content).import_(import_context, subdir)
                    return content
                except (AttributeError, MethodNotAllowed):
                    # Fall through to old implemenatation below
                    pass

            lines = properties.splitlines()

            stream = StringIO('\n'.join(lines))
            parser = ConfigParser(defaults={'title': '',
                                            'description': 'NONE'})
            parser.read_file(stream)

            title = parser.get('DEFAULT', 'title')
            description = parser.get('DEFAULT', 'description')

            content.setTitle(title)
            content.setDescription(description)

        return content
