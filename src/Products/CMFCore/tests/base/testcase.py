import logging
import sys
import time
import unittest
from os import chmod
from os import curdir
from os import mkdir
from os import remove
from os import rmdir
from os import stat
from os import walk
from os.path import abspath
from os.path import basename
from os.path import dirname
from os.path import join
from shutil import copytree
from shutil import ignore_patterns
from shutil import rmtree
from stat import S_IREAD
from stat import S_IWRITE
from tempfile import mktemp

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from OFS.Folder import Folder
from Testing import ZopeTestCase
from Testing.ZopeTestCase.layer import ZopeLite
from zope.component import getSiteManager

from ...interfaces import ISkinsTool
from ...utils import getPackageLocation
from .dummy import DummyFolder
from .security import AnonymousUser
from .security import OmnipotentUser
from .security import PermissiveSecurityPolicy


class LogInterceptor:

    logged = None
    installed = ()
    level = 0

    def _catch_log_errors(self, ignored_level=logging.WARNING, subsystem=''):

        if subsystem in self.installed:
            raise ValueError('Already installed filter!')

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


class TransactionalTest(unittest.TestCase):

    layer = ZopeLite

    def setUp(self):
        transaction.begin()
        self.app = self.root = ZopeTestCase.app()
        self.REQUEST = self.app.REQUEST
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

_prefix = abspath(join(_prefix, '..'))


class FSDVTest(unittest.TestCase):

    tempname = _sourceprefix = _prefix
    _skinname = 'fake_skins'
    _layername = 'fake_skin'

    def _registerDirectory(self, obj=None, ignore=None):
        from ...DirectoryView import _dirreg
        from ...DirectoryView import createDirectoryView
        if ignore is None:
            from ...DirectoryView import ignore
        filepath = join(self.tempname, self._skinname)
        subpath = basename(self.tempname)
        if subpath != 'tests':
            # we have a temp dir in tests
            subpath = 'tests/%s' % subpath
        reg_key = f'Products.CMFCore:{subpath}/{self._skinname}'
        _dirreg.registerDirectoryByKey(filepath, reg_key, ignore=ignore)
        if obj is not None:
            ob = obj.ob = DummyFolder()
            info = _dirreg.getDirectoryInfo(reg_key)
            for entry in info.getSubdirs():
                entry_reg_key = '/'.join((reg_key, entry))
                createDirectoryView(ob, entry_reg_key, entry)

    def setUp(self):
        # store the skin path name
        self.skin_path_name = join(self.tempname, self._skinname,
                                   self._layername)

    def _makeContext(self, obj_id, filename):
        newSecurityManager(None, OmnipotentUser().__of__(self.app.acl_users))

        stool = Folder('portal_skins')
        getSiteManager().registerUtility(stool, ISkinsTool)

        stool._setObject('custom', Folder('custom'))
        custom = stool.custom

        stool._setObject('fsdir', Folder('fsdir'))
        fsdir = stool.fsdir

        fsdir._setObject(obj_id, self._makeOne(obj_id, filename))

        return stool, custom, fsdir, fsdir[obj_id]


class WritableFSDVTest(FSDVTest):
    # Base class for FSDV test, creates a fake skin
    # copy that can be edited.

    def _writeFile(self, filename, stuff, use_dir_mtime=False):
        # write some stuff to a file on disk
        # make sure the file's modification time has changed
        # also make sure the skin folder mod time has changed
        thePath = join(self.skin_path_name, filename)
        try:
            mtime2 = mtime1 = stat(thePath).st_mtime
            # editing existing files doesn't change the folder
            use_dir_mtime = False
        except OSError:
            mtime2 = mtime1 = 0.0
        if use_dir_mtime:
            dir_mtime = stat(self.skin_path_name).st_mtime
        while mtime2 == mtime1:
            f = open(thePath, 'w')
            f.write(stuff)
            f.close()
            mtime2 = stat(thePath).st_mtime
        if use_dir_mtime:
            self._addedOrRemoved(dir_mtime)

    def _deleteFile(self, filename, use_dir_mtime=False):
        if use_dir_mtime:
            dir_mtime = stat(self.skin_path_name).st_mtime
        remove(join(self.skin_path_name, filename))
        if use_dir_mtime:
            self._addedOrRemoved(dir_mtime)

    def _deleteDirectory(self, subdirname, use_dir_mtime=False):
        if use_dir_mtime:
            dir_mtime = stat(self.skin_path_name).st_mtime
        rmdir(join(self.skin_path_name, subdirname))
        if use_dir_mtime:
            self._addedOrRemoved(dir_mtime)

    def _addedOrRemoved(self, old_mtime):
        # Called after adding/removing a file from self.skin_path_name.

        limit = time.time() + 60  # If it takes 60 seconds, give up.
        new_mtime = stat(self.skin_path_name).st_mtime
        while new_mtime == old_mtime:
            # Many systems have a granularity of 1 second.
            # Add/remove a file until it actually changes the
            # directory mod time.
            if time.time() > limit:
                raise RuntimeError(
                    'This platform (%s) does not update directory mod times '
                    'reliably.' % sys.platform)
            time.sleep(0.1)
            fn = join(self.skin_path_name, '.touch')
            f = open(fn, 'w')
            f.write('Temporary file')
            f.close()
            remove(fn)
            new_mtime = stat(self.skin_path_name).st_mtime

    def setUp(self):
        # store the place where the skin copy will be created
        self.tempname = mktemp(dir=getPackageLocation(
                                                     'Products.CMFCore.tests'))
        # create the temporary folder
        mkdir(self.tempname)
        # copy the source fake skin to the new location
        copytree(join(self._sourceprefix, self._skinname),
                 join(self.tempname, self._skinname),
                 ignore=ignore_patterns('.svn'))
        # make sure we have a writable copy
        for root, _dirs, files in walk(self.tempname):
            for name in files:
                chmod(join(root, name), S_IREAD + S_IWRITE)
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
