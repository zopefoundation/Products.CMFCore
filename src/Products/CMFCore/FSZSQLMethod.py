##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Customizable ZSQL methods that come from the filesystem.
"""

import logging

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import ImplicitAcquisitionWrapper
from App.config import getConfiguration
from App.special_dtml import DTMLFile

from Products.ZSQLMethods.SQL import SQL

from .DirectoryView import registerFileExtension
from .DirectoryView import registerMetaType
from .FSObject import FSObject
from .permissions import View
from .permissions import ViewManagementScreens
from .utils import _dtmldir


logger = logging.getLogger('CMFCore.FSZSQLMethod')


class FSZSQLMethod(SQL, FSObject):

    """FSZSQLMethods act like Z SQL Methods but are not directly
    modifiable from the management interface."""

    meta_type = 'Filesystem Z SQL Method'

    manage_options = (
        {'label': 'Customize', 'action': 'manage_customise'},
        {'label': 'Test', 'action': 'manage_testForm',
         'help': ('ZSQLMethods', 'Z-SQL-Method_Test.stx')})

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    # Make mutators private
    security.declarePrivate('manage_main')
    security.declarePrivate('manage_edit')
    security.declarePrivate('manage_advanced')
    security.declarePrivate('manage_advancedForm')
    manage = None

    security.declareProtected(ViewManagementScreens, 'manage_customise')
    manage_customise = DTMLFile('custzsql', _dtmldir)

    def __init__(self, id, filepath, fullname=None, properties=None):
        FSObject.__init__(self, id, filepath, fullname, properties)

    def _createZODBClone(self):
        """Create a ZODB (editable) equivalent of this object."""
        # I guess it's bad to 'reach inside' ourselves like this,
        # but Z SQL Methods don't have accessor methdods ;-)
        s = SQL(self.id,
                self.title,
                self.connection_id,
                self.arguments_src,
                self.src)
        s.manage_advanced(self.max_rows_,
                          self.max_cache_,
                          self.cache_time_,
                          self.class_name_,
                          self.class_file_,
                          connection_hook=self.connection_hook,
                          direct=self.allow_simple_one_argument_traversal)
        return s

    def _readFile(self, reparse):
        """Read the data from the filesystem.
        """
        file = open(self._filepath)  # not 'rb', as this is a text file!
        try:
            data = file.read()
        finally:
            file.close()

        # parse parameters
        parameters = {}
        start = data.find('<dtml-comment>')
        end = data.find('</dtml-comment>')
        if start == -1 or end == -1 or start > end:
            raise ValueError('Could not find parameter block')
        block = data[start + 14:end]

        for line in block.split('\n'):
            pair = line.split(':', 1)
            if len(pair) != 2:
                continue
            parameters[pair[0].strip().lower()] = pair[1].strip()

        # check for required parameters
        try:
            connection_id = (parameters.get('connection id', '') or
                             parameters['connection_id'])
        except KeyError as e:
            raise ValueError("The '%s' parameter is required "
                             'but was not supplied' % e)

        # Optional parameters
        title = parameters.get('title', '')
        arguments = parameters.get('arguments', '')
        max_rows = parameters.get('max_rows', 1000)
        max_cache = parameters.get('max_cache', 100)
        cache_time = parameters.get('cache_time', 0)
        class_name = parameters.get('class_name', '')
        class_file = parameters.get('class_file', '')
        connection_hook = parameters.get('connection_hook', None)
        direct = parameters.get('allow_simple_one_argument_traversal', None)

        self.manage_edit(title, connection_id, arguments, template=data)

        self.manage_advanced(max_rows,
                             max_cache,
                             cache_time,
                             class_name,
                             class_file,
                             connection_hook=connection_hook,
                             direct=direct)

        # do we need to do anything on reparse?

    if getConfiguration().debug_mode:
        # Provide an opportunity to update the properties.
        def __of__(self, parent):
            try:
                self = ImplicitAcquisitionWrapper(self, parent)
                self._updateFromFS()
                return self
            except Exception:
                logger.exception('Error during __of__')
                raise


InitializeClass(FSZSQLMethod)

registerFileExtension('zsql', FSZSQLMethod)
registerMetaType('Z SQL Method', FSZSQLMethod)
