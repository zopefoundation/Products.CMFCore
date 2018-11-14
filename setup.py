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
README = _boundary.join([
    _package_doc('README.rst'),
    _package_doc('CHANGES.rst'),
])

setup(name='Products.%s' % NAME,
      version='2.4.0b6.dev0',
      description='Zope Content Management Framework core components',
      long_description=README,
      classifiers=[
          "Development Status :: 4 - Beta",
          "Framework :: Plone",
          "Framework :: Zope :: 4",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: Zope Public License",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: Implementation :: CPython",
          "Topic :: Software Development :: Libraries :: Application Frameworks",  # noqa
      ],
      keywords='web application server zope cmf',
      author="Zope Foundation and Contributors",
      author_email="zope-cmf@zope.org",
      url="https://github.com/zopefoundation/Products.CMFCore",
      license="ZPL 2.1",
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['Products'],
      zip_safe=False,
      setup_requires=[
          'eggtestinfo',
      ],
      install_requires=[
          'setuptools',
          'Zope >= 4.0b8',
          'docutils',
          'five.localsitemanager',
          'Products.BTreeFolder2',
          'Products.GenericSetup >= 2.0b1',
          'Products.MailHost >= 4.0',
          'Products.PythonScripts',
          'Products.StandardCacheManagers',
          'Products.ZCTextIndex',
          'six',
          'zope.interface >= 3.8',
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
