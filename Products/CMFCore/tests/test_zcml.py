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
"""Unit tests for zcml module.
"""

import doctest
import unittest


def test_registerDirectory():
    """
    Use the cmf:registerDirectory directive::

      >>> import Products.CMFCore
      >>> from Zope2.App import zcml
      >>> configure_zcml = '''
      ... <configure xmlns:cmf="http://namespaces.zope.org/cmf">
      ...   <cmf:registerDirectory
      ...       name="fake_skin"
      ...       directory="tests/fake_skins/fake_skin"
      ...       recursive="True"
      ...       ignore="foo bar"
      ...       />
      ... </configure>'''
      >>> zcml.load_config('meta.zcml', Products.CMFCore)
      >>> zcml.load_string(configure_zcml)

    Make sure the directory is registered correctly::

      >>> from Products.CMFCore.DirectoryView import _dirreg
      >>> reg_keys = (
      ...   'Products.CMFCore:tests/fake_skins/fake_skin',
      ...   'Products.CMFCore:tests/fake_skins/fake_skin/test_directory')
      >>> reg_keys[0] in _dirreg._directories
      True
      >>> reg_keys[1] in _dirreg._directories
      True
      >>> info = _dirreg._directories[reg_keys[0]]
      >>> info._reg_key == reg_keys[0]
      True
      >>> info.ignore
      ('.', '..', 'foo', 'bar')

    Clean up and make sure the cleanup works::

      >>> from zope.testing.cleanup import cleanUp
      >>> cleanUp()
      >>> reg_keys[0] in _dirreg._directories
      False
      >>> reg_keys[1] in _dirreg._directories
      False
    """


def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite(),
        ))
