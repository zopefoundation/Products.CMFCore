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
"""CMFCore ZCML directives.
"""

from os import path

from zope.configuration.fields import Bool
from zope.configuration.fields import Path
from zope.configuration.fields import PythonIdentifier
from zope.configuration.fields import Tokens
from zope.interface import Interface
from zope.schema import ASCIILine
from zope.testing.cleanup import addCleanUp

from .DirectoryView import _dirreg
from .DirectoryView import _generateKey
from .DirectoryView import ignore


class IRegisterDirectoryDirective(Interface):

    """Register directories with the global registry.
    """

    name = PythonIdentifier(
        title='Name',
        description='Name of the directory.',
        required=True)

    directory = Path(
        title='Path',
        description='Path relative to the package. If not specified, '
                    "'skins/<name>' is used.",
        required=False)

    recursive = Bool(
        title='Recursive?',
        description='False by default. If true, register all subdirectories '
                    'as well.',
        required=False)

    ignore = Tokens(
        title='Ignore',
        description='Files and subdirectories that should be ignored. If '
                    "not specified, 'CVS' and '.svn' are ignored.",
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
        subdir = str(directory[len(_context.package.__path__[0]) + 1:])
        filepath = str(directory)

    reg_key = _generateKey(_context.package.__name__, subdir)
    _directory_regs.append(reg_key)

    _context.action(
        discriminator=('registerDirectory', reg_key),
        callable=_dirreg.registerDirectoryByKey,
        args=(filepath, reg_key, int(recursive), ignore),
        )


def cleanUp():
    global _directory_regs
    for reg_key in _directory_regs:
        for key in list(_dirreg._directories):
            if key.startswith(reg_key):
                del _dirreg._directories[key]
    _directory_regs = []


addCleanUp(cleanUp)
del addCleanUp
