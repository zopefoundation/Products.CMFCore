##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Views of filesystem directories as folders.
"""

import logging
import os
import re
from sys import platform
from warnings import warn

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.config import getConfiguration
from App.special_dtml import DTMLFile
from App.special_dtml import HTMLFile
from OFS.Folder import Folder
from OFS.ObjectManager import bad_id
from Persistence import Persistent
from zope.interface import implementer

from .FSMetadata import FSMetadata
from .FSObject import BadFile
from .interfaces import IDirectoryView
from .permissions import AccessContentsInformation as ACI
from .permissions import ManagePortal
from .utils import ProductsPath
from .utils import _dtmldir
from .utils import getPackageLocation
from .utils import getPackageName


logger = logging.getLogger('CMFCore.DirectoryView')

__reload_module__ = 0

# Ignore filesystem artifacts
base_ignore = ('.', '..')
# Ignore version control subdirectories
ignore = ('CVS', '.svn')
# Ignore suspected backups and hidden files
ignore_re = re.compile(r'\.|(.*~$)|#')


# and special names.
def _filtered_listdir(path, ignore):
    return [name for name in os.listdir(path)
            if name not in ignore and not ignore_re.match(name)]


class _walker:
    def __init__(self, ignore):
        # make a dict for faster lookup
        self.ignore = {x: None for x in ignore}

    def __call__(self, dirlist, dirname, names):
        # filter names inplace, so filtered directories don't get visited
        names[:] = [name for name in names
                    if name not in self.ignore and not ignore_re.match(name)]
        # append with stat info
        results = [(name, os.stat(os.path.join(dirname, name)).st_mtime)
                   for name in names]
        dirlist.extend(results)


def _generateKey(package, subdir):
    """Generate a key for a path inside a package.

    The key has the quality that keys for subdirectories can be derived by
    simply appending to the key.
    """
    return ':'.join((package, subdir.replace('\\', '/')))


def _findProductForPath(path, subdir=None):
    # like minimalpath, but raises an error if path is not inside a product
    p = os.path.abspath(path)
    for ppath in ProductsPath:
        if p.startswith(ppath):
            dirpath = p[len(ppath)+1:]
            parts = dirpath.replace('\\', '/').split('/', 1)
            parts.append('')
            if subdir:
                subdir = '/'.join((parts[1], subdir))
                if subdir.startswith('/'):
                    subdir = subdir[1:]
            else:
                subdir = parts[1]
            return ('Products.' + parts[0], subdir)

    raise ValueError('Path is not inside a product')


class DirectoryInformation:
    data = None
    use_dir_mtime = True
    _v_last_read = 0
    _v_last_filelist = []  # Only used on Win32

    def __init__(self, filepath, reg_key, ignore=ignore):
        self._filepath = filepath
        self._reg_key = reg_key
        self.ignore = base_ignore + tuple(ignore)
        if platform == 'win32':
            try:
                ntfs_detected = bool(os.stat(self._filepath).st_mtime % 1)
            except OSError:
                ntfs_detected = False
            if not ntfs_detected:
                self.use_dir_mtime = False
                self._walker = _walker(self.ignore)
        subdirs = []
        for entry in _filtered_listdir(self._filepath, ignore=self.ignore):
            entry_filepath = os.path.join(self._filepath, entry)
            if os.path.isdir(entry_filepath):
                subdirs.append(entry)
        self.subdirs = tuple(subdirs)

    def getSubdirs(self):
        return self.subdirs

    def _isAllowableFilename(self, entry):
        if entry[-1:] == '~':
            return 0
        if entry[:1] in ('_', '#'):
            return 0
        return 1

    def reload(self):
        self.data = None

    def _readTypesFile(self):
        """ Read the .objects file produced by FSDump.
        """
        types = {}
        try:
            f = open(os.path.join(self._filepath, '.objects'))
        except OSError:
            pass
        else:
            lines = f.readlines()
            f.close()
            for line in lines:
                try:
                    obname, meta_type = line.split(':')
                except ValueError:
                    pass
                else:
                    types[obname.strip()] = meta_type.strip()
        return types

    def _changed(self):
        if not getConfiguration().debug_mode:
            return 0
        mtime = 0.0
        filelist = []
        try:
            mtime = os.stat(self._filepath).st_mtime
            if not self.use_dir_mtime:
                # some Windows directories don't change mtime
                # when a file is added to or deleted from them :-(
                # So keep a list of files as well, and see if that
                # changes
                os.path.walk(self._filepath, self._walker, filelist)
                filelist.sort()
        except Exception:
            logger.exception('Error checking for directory modification')

        if mtime != self._v_last_read or filelist != self._v_last_filelist:
            self._v_last_read = mtime
            self._v_last_filelist = filelist

            return 1

        return 0

    def getContents(self, registry):
        changed = self._changed()
        if self.data is None or changed:
            try:
                self.data, self.objects = self.prepareContents(registry)
            except Exception:
                logger.exception('Error during prepareContents')
                self.data = {}
                self.objects = ()

        return self.data, self.objects

    def prepareContents(self, registry):
        # Creates objects for each file.
        data = {}
        objects = []
        types = self._readTypesFile()
        for entry in _filtered_listdir(self._filepath, ignore=self.ignore):
            if not self._isAllowableFilename(entry):
                continue
            entry_filepath = os.path.join(self._filepath, entry)
            if os.path.isdir(entry_filepath):
                # Add a subdirectory only if it was previously registered.
                entry_reg_key = '/'.join((self._reg_key, entry))
                info = registry.getDirectoryInfo(entry_reg_key)
                if info is not None:
                    # Folders on the file system have no extension or
                    # meta_type, as a crutch to enable customizing what gets
                    # created to represent a filesystem folder in a
                    # DirectoryView we use a fake type "FOLDER". That way
                    # other implementations can register for that type and
                    # circumvent the hardcoded assumption that all filesystem
                    # directories will turn into DirectoryViews.
                    mt = types.get(entry) or 'FOLDER'
                    t = registry.getTypeByMetaType(mt)
                    if t is None:
                        t = DirectoryView
                    metadata = FSMetadata(entry_filepath)
                    metadata.read()
                    ob = t(entry, entry_reg_key,
                           properties=metadata.getProperties())
                    ob_id = ob.getId()
                    data[ob_id] = ob
                    objects.append({'id': ob_id, 'meta_type': ob.meta_type})
            else:
                pos = entry.rfind('.')
                if pos >= 0:
                    name = entry[:pos]
                    ext = os.path.normcase(entry[pos + 1:])
                else:
                    name = entry
                    ext = ''
                if not name or name == 'REQUEST':
                    # Not an allowable id.
                    continue
                mo = bad_id(name)
                if mo is not None and mo != -1:  # Both re and regex formats
                    # Not an allowable id.
                    continue
                t = None
                mt = types.get(entry, None)
                if mt is None:
                    mt = types.get(name, None)
                if mt is not None:
                    t = registry.getTypeByMetaType(mt)
                if t is None:
                    t = registry.getTypeByExtension(ext)

                if t is not None:
                    metadata = FSMetadata(entry_filepath)
                    metadata.read()
                    try:
                        ob = t(name, entry_filepath, fullname=entry,
                               properties=metadata.getProperties())
                    except Exception:
                        import sys
                        import traceback
                        typ, val, tb = sys.exc_info()
                        try:
                            logger.exception('prepareContents')

                            exc_lines = traceback.format_exception(typ, val,
                                                                   tb)
                            ob = BadFile(name,
                                         entry_filepath,
                                         exc_str='\r\n'.join(exc_lines),
                                         fullname=entry)
                        finally:
                            tb = None   # Avoid leaking frame!

                    # FS-based security
                    permissions = metadata.getSecurity()
                    if permissions is not None:
                        for name in permissions:
                            acquire, roles = permissions[name]
                            try:
                                ob.manage_permission(name, roles, acquire)
                            except ValueError:
                                logger.exception('Error setting permissions')

                    # only DTML Methods and Python Scripts can have proxy roles
                    if hasattr(ob, '_proxy_roles'):
                        try:
                            ob._proxy_roles = tuple(metadata.getProxyRoles())
                        except Exception:
                            logger.exception('Error setting proxy role')

                    ob_id = ob.getId()
                    data[ob_id] = ob
                    objects.append({'id': ob_id, 'meta_type': ob.meta_type})

        return data, tuple(objects)


class DirectoryRegistry:

    def __init__(self):
        self._meta_types = {}
        self._object_types = {}
        self._directories = {}

    def registerFileExtension(self, ext, klass):
        self._object_types[ext] = klass

    def registerMetaType(self, mt, klass):
        self._meta_types[mt] = klass

    def getTypeByExtension(self, ext):
        return self._object_types.get(ext, None)

    def getTypeByMetaType(self, mt):
        return self._meta_types.get(mt, None)

    def registerDirectory(self, name, _prefix, subdirs=1, ignore=ignore):
        # This what is actually called to register a
        # file system directory to become a FSDV.
        package = getPackageName(_prefix)
        filepath = os.path.join(getPackageLocation(package), name)
        reg_key = _generateKey(package, name)
        self.registerDirectoryByKey(filepath, reg_key, subdirs, ignore)

    def registerDirectoryByKey(self, filepath, reg_key, subdirs=1,
                               ignore=ignore):
        info = DirectoryInformation(filepath, reg_key, ignore)
        self._directories[reg_key] = info
        if subdirs:
            for entry in info.getSubdirs():
                entry_filepath = os.path.join(filepath, entry)
                entry_reg_key = '/'.join((reg_key, entry))
                self.registerDirectoryByKey(entry_filepath, entry_reg_key,
                                            subdirs, ignore)

    def reloadDirectory(self, reg_key):
        info = self.getDirectoryInfo(reg_key)
        if info is not None:
            info.reload()

    def getDirectoryInfo(self, reg_key):
        # This is called when we need to get hold of the information
        # for a minimal path. Can return None.
        return self._directories.get(reg_key, None)

    def listDirectories(self):
        dirs = sorted(self._directories)
        return dirs


_dirreg = DirectoryRegistry()
registerDirectory = _dirreg.registerDirectory
registerFileExtension = _dirreg.registerFileExtension
registerMetaType = _dirreg.registerMetaType


def listFolderHierarchy(ob, path, rval, adding_meta_type=None):
    if not hasattr(ob, 'objectValues'):
        return
    for subob in ob.objectValues():
        base = getattr(subob, 'aq_base', subob)
        if getattr(base, 'isPrincipiaFolderish', 0):

            if adding_meta_type is not None and \
               hasattr(base, 'filtered_meta_types'):
                # Include only if the user is allowed to
                # add the given meta type in this location.
                meta_types = subob.filtered_meta_types()
                found = 0
                for mt in meta_types:
                    if mt['name'] == adding_meta_type:
                        found = 1
                        break
                if not found:
                    continue

            if path:
                subpath = path + '/' + subob.getId()
            else:
                subpath = subob.getId()
            title = getattr(subob, 'title', None)
            if title:
                name = f'{subpath} ({title})'
            else:
                name = subpath
            rval.append((subpath, name))
            listFolderHierarchy(subob, subpath, rval, adding_meta_type)


@implementer(IDirectoryView)
class DirectoryView(Persistent):

    """ Directory views mount filesystem directories.
    """

    meta_type = 'Filesystem Directory View'
    _dirpath = None
    _objects = ()

    def __init__(self, id, reg_key='', fullname=None, properties=None):
        if properties:
            # Since props come from the filesystem, this should be
            # safe.
            self.__dict__.update(properties)

        self.id = id
        self._dirpath = reg_key

    def __of__(self, parent):
        reg_key = self._dirpath
        info = _dirreg.getDirectoryInfo(reg_key)
        if info is None:
            # During GenericSetup a view will be created with an empty
            # reg_key. This is expected behaviour, so do not warn about it.
            if reg_key:
                warn('DirectoryView %s refers to a non-existing path %r' %
                     (self.id, reg_key), UserWarning)
            data = {}
            objects = ()
        else:
            data, objects = info.getContents(_dirreg)
        s = DirectoryViewSurrogate(self, data, objects)
        res = s.__of__(parent)
        return res

    def getId(self):
        return self.id


InitializeClass(DirectoryView)


@implementer(IDirectoryView)
class DirectoryViewSurrogate(Folder):

    """ Folderish DirectoryView.
    """

    meta_type = 'Filesystem Directory View'
    zmi_icon = 'far fa-folder-open'
    all_meta_types = ()

    security = ClassSecurityInfo()

    def __init__(self, real, data, objects):
        d = self.__dict__
        d.update(data)
        d.update(real.__dict__)
        d['_real'] = real
        d['_objects'] = objects

    def __setattr__(self, name, value):
        d = self.__dict__
        d[name] = value
        setattr(d['_real'], name, value)

    def __delattr__(self, name):
        d = self.__dict__
        del d[name]
        delattr(d['_real'], name)

    security.declareProtected(ManagePortal, 'manage_propertiesForm')
    manage_propertiesForm = DTMLFile('dirview_properties', _dtmldir)

    @security.protected(ManagePortal)
    def manage_properties(self, reg_key, REQUEST=None):
        """ Update the directory path of the DirectoryView.
        """
        self.__dict__['_real']._dirpath = reg_key
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect('%s/manage_propertiesForm' %
                                         self.absolute_url())

    @security.protected(ACI)
    def getCustomizableObject(self):
        ob = aq_parent(aq_inner(self))
        while ob:
            if IDirectoryView.providedBy(ob):
                ob = aq_parent(ob)
            else:
                break
        return ob

    @security.protected(ACI)
    def listCustFolderPaths(self, adding_meta_type=None):
        """ List possible customization folders as key, value pairs.
        """
        rval = []
        ob = self.getCustomizableObject()
        listFolderHierarchy(ob, '', rval, adding_meta_type)
        rval.sort()
        return rval

    @security.protected(ACI)
    def getDirPath(self):
        return self.__dict__['_real']._dirpath

    @security.public
    def getId(self):
        return self.id


InitializeClass(DirectoryViewSurrogate)


manage_addDirectoryViewForm = HTMLFile('dtml/addFSDirView', globals())


def createDirectoryView(parent, reg_key, id=None):
    """ Add either a DirectoryView or a derivative object.
    """
    if not id:
        id = reg_key.split('/')[-1]
    else:
        id = str(id)
    ob = DirectoryView(id, reg_key)
    parent._setObject(id, ob)


def addDirectoryViews(ob, name, _prefix):
    """ Add a directory view for every subdirectory of the given directory.

    Meant to be called by filesystem-based code. Note that registerDirectory()
    still needs to be called by product initialization code to satisfy
    persistence demands.
    """
    package = getPackageName(_prefix)
    reg_key = _generateKey(package, name)
    info = _dirreg.getDirectoryInfo(reg_key)
    if info is None:
        raise ValueError('Not a registered directory: %s' % reg_key)
    for entry in info.getSubdirs():
        entry_reg_key = '/'.join((reg_key, entry))
        createDirectoryView(ob, entry_reg_key, entry)


def manage_addDirectoryView(self, reg_key, id=None, REQUEST=None):
    """ Add either a DirectoryView or a derivative object.
    """
    createDirectoryView(self, reg_key, id)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)


def manage_listAvailableDirectories(*args):
    """ List registered directories.
    """
    return list(_dirreg.listDirectories())
