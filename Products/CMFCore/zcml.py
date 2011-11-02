##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""CMFCore ZCML directives. """

from os import path

from zope.configuration.fields import Bool
from zope.configuration.fields import Path
from zope.configuration.fields import PythonIdentifier
from zope.configuration.fields import Tokens
from zope.interface import Interface
from zope.schema import ASCIILine

from DirectoryView import _dirreg
from DirectoryView import _generateKey
from DirectoryView import ignore


class IRegisterDirectoryDirective(Interface):

    """Register directories with the global registry.
    """

    name = PythonIdentifier(
        title=u'Name',
        description=u'Name of the directory.',
        required=True)

    directory = Path(
        title=u'Path',
        description=u'Path relative to the package. If not specified, '
                    u"'skins/<name>' is used.",
        required=False)

    recursive = Bool(
        title=u'Recursive?',
        description=u'False by default. If true, register all subdirectories '
                    u'as well.',
        required=False)

    ignore = Tokens(
        title=u'Ignore',
        description=u'Files and subdirectories that should be ignored. If '
                    u"not specified, 'CVS' and '.svn' are ignored.",
        value_type=ASCIILine(),
        required=False)


_directory_regs = []
def registerDirectory(_context, name, directory=None, recursive=False,
                      ignore=ignore):
    """ Add a new directory to the registry.
    """
    if directory is None:
        subdir = 'skins/%s' % str(name)
        filepath = path.join(_context.package.__path__[0], 'skins', str(name))
    else:
        subdir = str(directory[len(_context.package.__path__[0])+1:])
        filepath = str(directory)

    reg_key = _generateKey(_context.package.__name__, subdir)
    _directory_regs.append(reg_key)

    _context.action(
        discriminator = ('registerDirectory', reg_key),
        callable = _dirreg.registerDirectoryByKey,
        args = (filepath, reg_key, int(recursive), ignore)
        )


def cleanUp():
    global _directory_regs
    for reg_key in _directory_regs:
        for key in _dirreg._directories.keys():
            if key.startswith(reg_key):
               del _dirreg._directories[key]
    _directory_regs = []

from zope.testing.cleanup import addCleanUp
addCleanUp(cleanUp)
del addCleanUp
