import os

from setuptools import setup


NAME = 'CMFCore'

here = os.path.abspath(os.path.dirname(__file__))


def _package_doc(name):
    f = open(os.path.join(here, name))
    return f.read()


_boundary = '\n' + ('-' * 60) + '\n\n'
README = _boundary.join([
    _package_doc('README.rst'),
    _package_doc('CHANGES.rst'),
])

setup(name='Products.%s' % NAME,
      version='3.8',
      description='Zope Content Management Framework core components',
      long_description=README,
      long_description_content_type='text/x-rst',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Framework :: Plone',
          'Framework :: Zope :: 5',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Zope Public License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Programming Language :: Python :: 3.12',
          'Programming Language :: Python :: 3.13',
          'Programming Language :: Python :: 3.14',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Software Development :: Libraries ::'
          ' Application Frameworks',
      ],
      keywords='web application server zope cmf',
      author='Zope Foundation and Contributors',
      author_email='zope-cmf@zope.org',
      url='https://github.com/zopefoundation/Products.CMFCore',
      project_urls={
          'Documentation': 'https://zope.readthedocs.io',
          'Issue Tracker': ('https://github.com/zopefoundation/'
                            'Products.CMFCore/issues'),
          'Sources': 'https://github.com/zopefoundation/Products.CMFCore',
      },
      license='ZPL-2.1',
      python_requires='>=3.10',
      install_requires=[
          'Zope >= 5',
          'docutils > 0.15',
          'five.localsitemanager',
          'Products.BTreeFolder2',
          'Products.GenericSetup >= 2.1.2',
          'Products.MailHost >= 4.0',
          'Products.PythonScripts',
          'Products.StandardCacheManagers',
          'Products.ZCatalog >= 4.0a2',  # Products.ZCTextIndex lives there now
          'zope.datetime',
          'zope.interface >= 3.8',
      ],
      extras_require={
          'test': ['Products.StandardCacheManagers'],
          'zsql': ['Products.ZSQLMethods >= 3.0.0b1'],
          'docs': ['Sphinx', 'repoze.sphinx.autointerface', 'furo'],
      },
      include_package_data=True,
      entry_points="""
      [zope2.initialize]
      Products.{} = Products.{}:initialize
      """.format(NAME, NAME),
      )
