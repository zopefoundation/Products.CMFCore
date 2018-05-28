import os
from setuptools import setup
from setuptools import find_packages

NAME = 'CMFCore'

here = os.path.abspath(os.path.dirname(__file__))
package = os.path.join(here, 'Products', NAME)

def _package_doc(name):
    f = open(os.path.join(here, name))
    return f.read()

_boundary = '\n' + ('-' * 60) + '\n\n'
README = ( _package_doc('README.txt')
         + _boundary
         + _package_doc('CHANGES.txt')
         + _boundary
         + "Download\n========"
         )

setup(name='Products.%s' % NAME,
      version='2.4.0b3.dev0',
      description='Zope Content Management Framework core components',
      long_description=README,
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Zope2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        ],
      keywords='web application server zope zope2 cmf',
      author="Zope Foundation and Contributors",
      author_email="zope-cmf@zope.org",
      url="http://pypi.python.org/pypi/Products.CMFCore",
      license="ZPL 2.1 (http://www.zope.org/Resources/License/ZPL-2.1)",
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['Products'],
      zip_safe=False,
      setup_requires=['eggtestinfo',
                     ],
      install_requires=[
          'setuptools',
          'Zope2 >= 4.0a3',
          'docutils',
          'five.localsitemanager',
          'Products.BTreeFolder2',
          'Products.GenericSetup',
          'Products.MailHost >= 4.0',
          'Products.PythonScripts',
          'Products.StandardCacheManagers',
          'Products.ZCTextIndex',
          'six',
          ],
      tests_require=[
          'zope.testing >= 3.7.0',
          'Products.StandardCacheManagers',
          ],
      extras_require={
          'test': ['Products.StandardCacheManagers'],
          'zsql': ['Products.ZSQLMethods >= 3.0.0b1'],
          },
      test_loader='zope.testing.testrunner.eggsupport:SkipLayers',
      test_suite='Products.%s' % NAME,
      entry_points="""
      [zope2.initialize]
      Products.%s = Products.%s:initialize
      [distutils.commands]
      ftest = zope.testing.testrunner.eggsupport:ftest
      """ % (NAME, NAME),
      )
