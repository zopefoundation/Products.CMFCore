import unittest
from Testing import ZopeTestCase
from Testing.ZopeTestCase.layer import ZopeLite

import sys
import time
import logging
from os import chmod, curdir, mkdir, remove, stat, walk
from os.path import join, abspath, dirname
from shutil import copytree, rmtree
from stat import S_IREAD, S_IWRITE
from tempfile import mktemp

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy

from dummy import DummyFolder
from security import AnonymousUser
from security import PermissiveSecurityPolicy
from Products.CMFCore.utils import getPackageLocation
from Products.CMFCore.testing import OFSZCMLLayer


class LogInterceptor:

    logged = None
    installed = ()
    level = 0

    def _catch_log_errors(self, ignored_level=logging.WARNING, subsystem=''):

        if subsystem in self.installed:
            raise ValueError, 'Already installed filter!'

        root_logger = logging.getLogger(subsystem)
        self.installed += (subsystem,)
        self.level = ignored_level
        root_logger.addFilter(self)

    def filter(self, record):
        if record.levelno > self.level:
            return True
        if self.logged is None:
            self.logged = []
        self.logged.append(record)
        return False

    def _ignore_log_errors(self, subsystem=''):

        if subsystem not in self.installed:
            return

        root_logger = logging.getLogger(subsystem)
        root_logger.removeFilter(self)
        self.installed = tuple([s for s in self.installed if s != subsystem])


class WarningInterceptor:

    _old_stderr = None
    _our_stderr_stream = None

    def _trap_warning_output( self ):

        if self._old_stderr is not None:
            return

        from StringIO import StringIO

        self._old_stderr = sys.stderr
        self._our_stderr_stream = sys.stderr = StringIO()

    def _free_warning_output( self ):

        if self._old_stderr is None:
            return

        sys.stderr = self._old_stderr


class TransactionalTest(unittest.TestCase):

    layer = ZopeLite

    def setUp(self):
        transaction.begin()
        self.app = self.root = ZopeTestCase.app()
        self.REQUEST  = self.app.REQUEST
        self.RESPONSE = self.app.REQUEST.RESPONSE

    def tearDown(self):
        transaction.abort()
        ZopeTestCase.close(self.app)

RequestTest = TransactionalTest


class SecurityTest(TransactionalTest):

    layer = ZopeLite

    def setUp(self):
        TransactionalTest.setUp(self)
        self._policy = PermissiveSecurityPolicy()
        self._oldPolicy = setSecurityPolicy(self._policy)
        newSecurityManager(None, AnonymousUser().__of__(self.app.acl_users))

    def tearDown(self):
        noSecurityManager()
        setSecurityPolicy(self._oldPolicy)
        TransactionalTest.tearDown(self)

SecurityRequestTest = SecurityTest


try:
    __file__
except NameError:
    # Test was called directly, so no __file__ global exists.
    _prefix = abspath(curdir)
else:
    # Test was called by another test.
    _prefix = abspath(dirname(__file__))

_prefix = abspath(join(_prefix,'..'))


class FSDVTest(unittest.TestCase, WarningInterceptor):

    tempname = _sourceprefix = _prefix
    _skinname = 'fake_skins'
    _layername = 'fake_skin'

    def _registerDirectory(self, object=None, ignore=None):
        self._trap_warning_output()
        from Products.CMFCore.DirectoryView import registerDirectory
        from Products.CMFCore.DirectoryView import addDirectoryViews
        if ignore is None:
            from Products.CMFCore.DirectoryView import ignore
        registerDirectory(self._skinname, self.tempname, ignore=ignore)
        if object is not None:
            ob = self.ob = DummyFolder()
            addDirectoryViews(ob, self._skinname, self.tempname)

    def setUp(self):
        # store the skin path name
        self.skin_path_name = join(self.tempname,self._skinname,self._layername)

    def tearDown(self):
        self._free_warning_output()


class WritableFSDVTest(FSDVTest):
    # Base class for FSDV test, creates a fake skin
    # copy that can be edited.

    def _writeFile(self, filename, stuff, use_dir_mtime=False):
        # write some stuff to a file on disk
        # make sure the file's modification time has changed
        # also make sure the skin folder mod time has changed
        if use_dir_mtime:
            dir_mtime = stat(self.skin_path_name).st_mtime
        thePath = join(self.skin_path_name, filename)
        try:
            dir_mtime = stat(self.skin_path_name)[8]
        except:  # XXX Why bare except?
            dir_mtime = 0
        thePath = join(self.skin_path_name,filename)
        try:
            mtime1 = stat(thePath)[8]
        except:  # XXX Why bare except?
            mtime1 = 0
        mtime2 = mtime1
        while mtime2==mtime1:
            f = open(thePath,'w')
            f.write(stuff)
            f.close()
            mtime2 = stat(thePath)[8]
        if use_dir_mtime:
            self._addedOrRemoved(dir_mtime)

    def _deleteFile(self, filename, use_dir_mtime=False):
        if use_dir_mtime:
            dir_mtime = stat(self.skin_path_name).st_mtime
        remove(join(self.skin_path_name, filename))
        if use_dir_mtime:
            self._addedOrRemoved(dir_mtime)

    def _addedOrRemoved(self, old_mtime):
        # Called after adding/removing a file from self.skin_path_name.

        limit = time.time() + 60  # If it takes 60 seconds, give up.
        new_mtime = old_mtime
        while new_mtime == old_mtime:
            # Many systems have a granularity of 1 second.
            # Add/remove a file until it actually changes the
            # directory mod time.
            if time.time() > limit:
                raise RuntimeError(
                    "This platform (%s) does not update directory mod times "
                    "reliably." % sys.platform)
            time.sleep(0.1)
            fn = join(self.skin_path_name, '.touch')
            f = open(fn, 'w')
            f.write('Temporary file')
            f.close()
            remove(fn)
            new_mtime = stat(self.skin_path_name)[8]

    def setUp(self):
        # store the place where the skin copy will be created
        self.tempname = mktemp(dir=getPackageLocation('Products.CMFCore.tests'))
        # create the temporary folder
        mkdir(self.tempname)
        # copy the source fake skin to the new location
        copytree(join(self._sourceprefix,
                      self._skinname),
                 join(self.tempname,
                      self._skinname))
        # make sure we have a writable copy
        for root, dirs, files in walk(self.tempname):
            for name in files:
                chmod(join(root, name), S_IREAD+S_IWRITE)
        FSDVTest.setUp(self)

    def tearDown(self):
        FSDVTest.tearDown(self)
        # kill the copy
        try:
            rmtree(self.tempname)
        except OSError:
            # try again (some files might be locked temporarily)
            time.sleep(0.1)
            rmtree(self.tempname)
