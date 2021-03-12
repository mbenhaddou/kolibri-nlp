
import functools
import textwrap
import io, six, yaml, simplejson
import os, errno
import datetime
import sys, tempfile
from pathlib import Path
import hashlib
import zipfile
import tarfile
import gzip
import requests
import shutil
import gzip
import stat
from abc import ABCMeta, abstractmethod
from gzip import GzipFile, WRITE as GZ_WRITE
from io import BytesIO
from six import add_metaclass
from six import string_types, text_type
from six.moves.urllib.request import urlopen, url2pathname
from typing import Text, Any

from collections import Mapping


import io
import os
import json
import re
from smart_open import open


try:
    import cPickle as pickle
except ImportError:
    import pickle

try:  # Python 3.
    textwrap_indent = functools.partial(textwrap.indent, prefix='  ')
except AttributeError:  # Python 2; indent() not available for Python2.
    textwrap_fill = functools.partial(
        textwrap.fill,
        initial_indent='  ',
        subsequent_indent='  ',
        replace_whitespace=False,
    )


    def textwrap_indent(text):
        return '\n'.join(textwrap_fill(line) for line in text.splitlines())

try:
    from zlib import Z_SYNC_FLUSH as FLUSH
except ImportError:
    from zlib import Z_FINISH as FLUSH

import logging
logger = logging.getLogger(__name__)


def dump_obj_as_json_to_file(filename, obj):
    # type: (Text, Any) -> None
    """Dump an object as a json string to a file."""

    dump_obj_as_str_to_file(filename, json.dumps(obj, indent=2))


def read_file(filename, encoding="utf-8"):
    """Read text from a file."""
    with io.open(filename, encoding=encoding) as f:
        return f.read()


def read_json_file(filename):
    """Read json from a file."""
    content = read_file(filename)
    try:
        return simplejson.loads(content)
    except ValueError as e:
        raise ValueError("Failed to read json from '{}'. Error: "
                         "{}".format(os.path.abspath(filename), e))

def _path_from(parent, child):
    if os.path.split(parent)[1] == "":
        parent = os.path.split(parent)[0]
    path = []
    while parent != child:
        child, dirname = os.path.split(child)
        path.insert(0, dirname)
        assert os.path.split(child)[0] != child
    return path

def home_directory():
    """
    Return home directory path
    Returns:
        str: home path
    """
    return str(Path.home())

def get_hashed_name(name: str):
    """
   Generate hashed name
   Args:
       name: string to be hashed
   Returns:
      str: hashed string
   """
    return hashlib.sha224(name.encode('utf-8')).hexdigest()



def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_from_url(url: str, download_path: str):
    """
    Download file/data from given url to download path
    Args:
        url:
        download_path:
    Returns:
        None
    """
    with open(download_path, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            total_kb = int(total/1024)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}] {} % [{}/{} kb]'.
                                 format('|' * done, '.' * (50-done), int(done * 2),
                                        int(downloaded/1024), total_kb))
                sys.stdout.flush()
    sys.stdout.write('\n')

def extract_file(zip_path: str, target_path: str = '.') -> None:
    """
    Unzip file at zip_path to target_path
    Args:
        zip_path:
        target_path:
    Returns:
    """
    if zip_path.endswith('.gz') and not zip_path.endswith('.tar.gz'):
        os.mkdir(target_path)
        f_in=gzip.open(zip_path, 'rb').read()
        with open(os.path.join(target_path, os.path.basename(target_path)), 'wb') as f_out:
            f_out.write(f_in)
        os.remove(zip_path)


        return

    if zip_path.endswith('.zip'):
        opener, mode = zipfile.ZipFile, 'r'
    elif zip_path.endswith('.tar.gz') or zip_path.endswith('.tgz'):
        opener, mode = tarfile.open, 'r:gz'
    elif zip_path.endswith('.tar.bz2') or zip_path.endswith('.tbz'):
        opener, mode = tarfile.open, 'r:bz2'
    else:
        raise(ValueError, f"Could not extract `{zip_path}` as no appropriate extractor is found")

    with opener(zip_path, mode) as zipObj:
        zipObj.extractall(target_path)


def read_yaml_file(filename):
    return yaml.load(read_file(filename, "utf-8"))

def create_dir(dir_path):
    # type: (Text) -> None
    """Creates a directory and its super paths.

    Succeeds even if the path already exists."""

    try:
        os.makedirs(dir_path)
    except OSError as e:
        # be happy if someone already created the path
        if e.errno != errno.EEXIST:
            raise


def _dump_yaml(obj, output):
    if six.PY2:
        import yaml

        yaml.safe_dump(obj, output,
                       default_flow_style=False,
                       allow_unicode=True)
    else:
        import ruamel.yaml

        yaml_writer = ruamel.yaml.YAML(pure=True, typ="safe")
        yaml_writer.unicode_supplementary = True
        yaml_writer.default_flow_style = False
        yaml_writer.version = "1.1"

        yaml_writer.dump(obj, output)


def dump_obj_as_str_to_file(filename, text):
    # type: (Text, Text) -> None
    """Dump a text to a file."""

    with io.open(filename, 'w', encoding="utf-8") as f:
        # noinspection PyTypeChecker
        f.write(str(text))

def dump_obj_as_yaml_to_file(filename, obj):
    """Writes data (python dict) to the filename in yaml repr."""
    with io.open(filename, 'w', encoding="utf-8") as output:
        _dump_yaml(obj, output)


def dump_obj_as_yaml_to_string(obj):
    """Writes data (python dict) to a yaml string."""
    str_io = io.StringIO()
    _dump_yaml(obj, str_io)
    return str_io.getvalue()

def create_temporary_file(data, suffix="", mode="w+"):
    """Creates a tempfile.NamedTemporaryFile object for data.

    mode defines NamedTemporaryFile's  mode parameter in py3."""


    f = tempfile.NamedTemporaryFile(mode=mode, suffix=suffix,
                                        delete=False)
    f.write(data)


    f.close()
    return f.name

def get_type(full_path):
    """Get the type (socket, file, dir, symlink, ...) for the provided path"""
    status = {'type': []}
    if os.path.ismount(full_path):
        status['type'] += ['mount-point']
    elif os.path.islink(full_path):
        status['type'] += ['symlink']
    if os.path.isfile(full_path):
        status['type'] += ['file']
    elif os.path.isdir(full_path):
        status['type'] += ['dir']
    if not status['type']:
        if os.stat.S_ISSOCK(status['mode']):
            status['type'] += ['socket']
        elif os.stat.S_ISCHR(status['mode']):
            status['type'] += ['special']
        elif os.stat.S_ISBLK(status['mode']):
            status['type'] += ['block-device']
        elif os.stat.S_ISFIFO(status['mode']):
            status['type'] += ['pipe']
    if not status['type']:
        status['type'] += ['unknown']
    elif status['type'] and status['type'][-1] == 'symlink':
        status['type'] += ['broken']
    return status['type']

def create_dir(dir_path):
    # type: (Text) -> None
    """Creates a directory and its super paths.

    Succeeds even if the path already exists."""

    try:
        os.makedirs(dir_path)
    except OSError as e:
        # be happy if someone already created the path
        if e.errno != errno.EEXIST:
            raise

def expand_path(path, follow_links=False):
    """ Expand shell variables ("$VAR"), user directory symbols (~), and return absolute path
    """
    path = os.path.expandvars(os.path.expanduser(path))
    if follow_links:
        return os.path.realpath(path)
    return os.path.abspath(path)


def mkdir_p(path):
    """`mkdir -p` functionality (don't raise exception if path exists)
    Make containing directory and parent directories in `path`, if they don't exist.
    Arguments:
                    path (str): Full or relative path to a directory to be created with mkdir -p
    Returns:
                    str: 'pre-existing' or 'new'
    References:
                    http://stackoverflow.com/a/600612/623735
    """
    path = expand_path(path)
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno == errno.EEXIST and os.path.isdir(path):
            return 'pre-existing: ' + path
        else:
            raise
    return 'new: ' + path

def get_stat(full_path):
    """Use python builtin equivalents to unix `stat` command and return dict containing stat data about a file"""
    status = {}
    status['size'] = os.path.getsize(full_path)
    status['accessed'] = datetime.datetime.fromtimestamp(os.path.getatime(full_path))
    status['modified'] = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
    status['changed_any'] = datetime.datetime.fromtimestamp(os.path.getctime(full_path))
    # first 3 digits are User, Group, Other permissions: 1=execute,2=write,4=read
    status['mode'] = os.stat(full_path).st_mode
    status['type'] = get_type(full_path)
    return status


def path_status(path, filename='', status=None, deep=False, verbosity=0):
    """ Retrieve the access, modify, and create timetags for a path along with its size
    Arguments:
        path (str): full path to the file or directory to be statused
        status (dict): optional existing status to be updated/overwritten with new status values
        try_open (bool): whether to try to open the file to get its encoding and openability
    Returns:
        dict: {'size': bytes (int), 'accessed': (datetime), 'modified': (datetime), 'changed_any': (datetime)}
    'file'
    """
    status = {} if status is None else status

    path = expand_path(path)
    if filename:
        dir_path = path
    else:
        dir_path, filename = os.path.split(path)  # this will split off a dir as `filename` if path doesn't end in a /
    full_path = os.path.join(dir_path, filename)
    if verbosity > 1:
        print('stat: {}'.format(full_path))
    status['name'] = filename
    status['path'] = full_path
    status['dir'] = dir_path
    status['type'] = []
    try:
        status.update(get_stat(full_path))
    except OSError:
        status['type'] = ['nonexistent'] + status['type']
        logger.info("Unable to stat path '{}'".format(full_path))
    status['type'] = '->'.join(status['type'])

    return status

def create_dir_for_file(file_path):
    """Creates any missing parent directories of this files path."""

    try:
        os.makedirs(os.path.dirname(file_path))
    except OSError as e:
        # be happy if someone already created the path
        if e.errno != errno.EEXIST:
            raise

######################################################################
# Search Path
######################################################################

path = []
"""A list of directories where the Dolphin data package might reside.
   These directories will be checked in order when looking for a
   resource in the data package.  Note that this allows users to
   substitute in their own versions of resources, if they have them
   (e.g., in their home directory under ~/data)."""

# User-specified locations:
_paths_from_env = os.environ.get('KOLIBRI_DATA', str('')).split(os.pathsep)
path += [d for d in _paths_from_env if d]
if 'APPENGINE_RUNTIME' not in os.environ and os.path.expanduser('~/') != '~/':
    path.append(os.path.expanduser(str('~/data')))

    # Common locations on UNIX & OS X:
path += [
        os.path.join(sys.prefix, str('data')),
        os.path.join(sys.prefix, str('share'), str('data')),
        os.path.join(sys.prefix, str('lib'), str('data')),
        str('/Users/mbenhaddou/Documents/Mentis/Developement/Python/Kolibri/'),
    ]


def walk_level(path, level=1):
    """Like os.walk, but takes `level` kwarg that indicates how deep the recursion will go.
    Notes:
        TODO: refactor `level`->`depth`
    References:
        http://stackoverflow.com/a/234329/623735
    Args:
        path (str):  Root path to begin file tree traversal (walk)
            level (int, optional): Depth of file tree to halt recursion at.
            None = full recursion to as deep as it goes
            0 = nonrecursive, just provide a list of files at the root level of the tree
            1 = one level of depth deeper in the tree
    """
    if level is None:
        level = float('inf')
    path = expand_path(path)
    if os.path.isdir(path):
        root_level = path.count(os.path.sep)
        for root, dirs, files in os.walk(path):
            yield root, dirs, files
            if root.count(os.path.sep) >= root_level + level:
                del dirs[:]
    elif os.path.isfile(path):
        yield os.path.dirname(path), [], [os.path.basename(path)]
    else:
        raise RuntimeError("Can't find a valid folder or file for path {0}".format(repr(path)))


def generate_files(path='', ext='', level=None, dirs=False, files=True, verbosity=0):
    """ Recursively generate files (and thier stats) in the indicated directory
    Filter by the indicated file name extension (ext)
    Args:
        path (str):  Root/base path to search.
        ext (str or list of str):  File name extension(s).
            Only file paths that ".endswith()" this string will be returned
        level (int, optional): Depth of file tree to halt recursion at.
            None = full recursion to as deep as it goes
            0 = nonrecursive, just provide a list of files at the root level of the tree
            1 = one level of depth deeper in the tree
        typ (type):  output type (default: list). if a mapping type is provided the keys will be the full paths (unique)
        dirs (bool):  Whether to yield dir paths along with file paths (default: False)
        files (bool): Whether to yield file paths (default: True)
            `dirs=True`, `files=False` is equivalent to `ls -d`
    Returns:
        list of dicts: dict keys are { 'path', 'name', 'bytes', 'created', 'modified', 'accessed', 'permissions' }
        path (str): Full, absolute paths to file beneath the indicated directory and ending with `ext`
        name (str): File name only (everythin after the last slash in the path)
        size (int): File size in bytes
        changed_any (datetime): Timestamp for modification of either metadata (e.g. permissions) or content
        modified (datetime): File content modification timestamp from file system
        accessed (datetime): File access timestamp from file system
        permissions (int): File permissions bytes as a chown-style integer with a maximum of 4 digits
        type (str): One of 'file', 'dir', 'symlink->file', 'symlink->dir', 'symlink->broken'
                e.g.: 777 or 1755
    Examples:
        >>> 'util.py' in [d['name'] for d in generate_files(os.path.dirname(__file__), ext='.py', level=0)]
        True
        >>> next(d for d in generate_files(os.path.dirname(__file__), ext='.py')
        ...      if d['name'] == 'util.py')['size'] > 1000
        True
        >>> sorted(next(generate_files()).keys())
        ['accessed', 'changed_any', 'dir', 'mode', 'modified', 'name', 'path', 'size', 'type']
        There should be an __init__ file in the same directory as this script.
        And it should be at the top of the list.
        >>> sorted(d['name'] for d in generate_files(os.path.dirname(__file__), ext='.py', level=0))[0]
        '__init__.py'
        >>> len(list(generate_files(__file__, ext='.')))
        0
        >>> len(list(generate_files(__file__, ext=['invalidexttesting123', False])))
        0
        >>> len(list(generate_files(__file__, ext=['.py', '.pyc', 'invalidexttesting123', False]))) > 0
        True
        >>> sorted(generate_files(__file__))[0]['name'] == os.path.basename(__file__)
        True
        >>> sorted(list(generate_files())[0].keys())
        ['accessed', 'changed_any', 'dir', 'mode', 'modified', 'name', 'path', 'size', 'type']
        >>> all(d['type'] in ('file', 'dir',
        ...                   'symlink->file', 'symlink->dir', 'symlink->broken',
        ...                   'mount-point->file', 'mount-point->dir',
        ...                   'block-device', 'pipe', 'special', 'socket', 'unknown')
        ...     for d in generate_files(level=1, files=True, dirs=True))
        True
    """
    path = expand_path(path or '.')
    # None interpreted as '', False is interpreted as '.' (no ext will be accepted)
    ext = '.' if ext is False else ext
    # multiple extensions can be specified in a list or tuple
    ext = ext if ext and isinstance(ext, (list, tuple)) else [ext]
    # case-insensitive extensions, '.' ext means only no-extensions are accepted
    ext = set(x.lower() if x else '.' if x is False else '' for x in ext)

    if os.path.isfile(path):
        fn = os.path.basename(path)
        # only yield the stat dict if the extension is among those that match or files without any ext are desired
        if not ext or any(path.lower().endswith(x) or (x == '.' and '.' not in fn) for x in ext):
            yield path_status(os.path.dirname(path), os.path.basename(path), verbosity=verbosity)
    else:
        for dir_path, dir_names, filenames in walk_level(path, level=level):
            if verbosity > 0:
                print('Checking path "{}"'.format(dir_path))
            if files:
                for fn in filenames:  # itertools.chain(filenames, dir_names)
                    if ext and not any((fn.lower().endswith(x) or (x == '.' and x not in fn) for x in ext)):
                        continue
                    stat = path_status(dir_path, fn, verbosity=verbosity)
                    if stat and stat['name'] and stat['path']:
                        yield stat
            if dirs:
                for fn in dir_names:
                    if ext and not any((fn.lower().endswith(x) or (x == '.' and x not in fn) for x in ext)):
                        continue
                    yield path_status(dir_path, fn, verbosity=verbosity)

def find_files(path='', ext='', level=None, typ=list, dirs=False, files=True, verbosity=0):
    """ Recursively find all files in the indicated directory
    Filter by the indicated file name extension (ext)
    Args:
        path (str):  Root/base path to search.
        ext (str):   File name extension. Only file paths that ".endswith()" this string will be returned
        level (int, optional): Depth of file tree to halt recursion at.
                None = full recursion to as deep as it goes
                0 = nonrecursive, just provide a list of files at the root level of the tree
                1 = one level of depth deeper in the tree
        typ (type):  output type (default: list). if a mapping type is provided the keys will be the full paths (unique)
        dirs (bool):  Whether to yield dir paths along with file paths (default: False)
        files (bool): Whether to yield file paths (default: True)
                `dirs=True`, `files=False` is equivalent to `ls -d`
    Returns:
        list of dicts: dict keys are { 'path', 'name', 'bytes', 'created', 'modified', 'accessed', 'permissions' }
                path (str): Full, absolute paths to file beneath the indicated directory and ending with `ext`
                name (str): File name only (everythin after the last slash in the path)
                size (int): File size in bytes
                created (datetime): File creation timestamp from file system
                modified (datetime): File modification timestamp from file system
                accessed (datetime): File access timestamp from file system
                permissions (int): File permissions bytes as a chown-style integer with a maximum of 4 digits
                type (str): One of 'file', 'dir', 'symlink->file', 'symlink->dir', 'symlink->broken'
                              e.g.: 777 or 1755
    Examples:
        >>> 'util.py' in [d['name'] for d in find_files(os.path.dirname(__file__), ext='.py', level=0)]
        True
        >>> next(d for d in find_files(os.path.dirname(__file__), ext='.py')
        ...      if d['name'] == 'util.py')['size'] > 1000
        True
        There should be an __init__ file in the same directory as this script.
        And it should be at the top of the list.
        >>> sorted(d['name'] for d in find_files(os.path.dirname(__file__), ext='.py', level=0))[0]
        '__init__.py'
        >>> all(d['type'] in ('file', 'dir',
        ...                   'symlink->file', 'symlink->dir', 'symlink->broken',
        ...                   'mount-point->file', 'mount-point->dir',
        ...                   'block-device', 'pipe', 'special', 'socket', 'unknown')
        ...     for d in find_files(level=1, files=True, dirs=True))
        True
        >>> os.path.join(os.path.dirname(__file__), '__init__.py') in find_files(
        ... os.path.dirname(__file__), ext='.py', level=0, typ=dict)
        True
    """
    path = expand_path(path)
    gen = generate_files(path, ext=ext, level=level, dirs=dirs, files=files, verbosity=verbosity)
    if isinstance(typ(), Mapping):
        return typ((ff['path'], ff) for ff in gen)
    elif typ is not None:
        return typ(gen)
    else:
        return gen

######################################################################
# Util Functions
######################################################################

def is_writable(path):
    # Ensure that it exists.
    if not os.path.exists(path):
        return False

    # If we're on a posix system, check its permissions.
    if hasattr(os, "getuid"):
        statdata = os.stat(path)
        perm = stat.S_IMODE(statdata.st_mode)
        # is it world-writable?
        if perm & 0o002:
            return True
        # do we own it?
        elif statdata.st_uid == os.getuid() and (perm & 0o200):
            return True
        # are we in a group that can write to it?
        elif (statdata.st_gid in [os.getgid()] + os.getgroups()) and (perm & 0o020):
            return True
        # otherwise, we can't write to it.
        else:
            return False

    # Otherwise, we'll assume it's writable.
    # [xx] should we do other checks on other platforms?
    return True



def fix_yaml_loader():
    """Ensure that any string read by yaml is represented as unicode."""
    from yaml import Loader, SafeLoader

    def construct_yaml_str(self, node):
        # Override the default string handling function
        # to always return unicode objects
        return self.construct_scalar(node)

    Loader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)
    SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)


def read_yaml_string(string):
    if six.PY2:
        import yaml

        fix_yaml_loader()
        return yaml.load(string)
    else:
        import ruamel.yaml

        yaml_parser = ruamel.yaml.YAML(typ="safe")
        yaml_parser.version = "1.1"
        yaml_parser.unicode_supplementary = True

        return yaml_parser.load(string)

def read_yaml(content):
    fix_yaml_loader()
    return yaml.load(content)


def read_yaml_file(filename):
    fix_yaml_loader()
    return yaml.load(read_file(filename, "utf-8"))

# inherited from pywordnet, by Oliver Steele
def binary_search_file(file, key, cache={}, cacheDepth=-1):
    """
    Return the line from the file with first word key.
    Searches through a sorted file using the binary search algorithm.
    :type file: file
    :param file: the file to be searched through.
    :type key: str
    :param key: the identifier we are searching for.
    """

    key = key + ' '
    keylen = len(key)
    start = 0
    currentDepth = 0

    if hasattr(file, 'name'):
        end = os.stat(file.name).st_size - 1
    else:
        file.seek(0, 2)
        end = file.tell() - 1
        file.seek(0)

    while start < end:
        lastState = start, end
        middle = (start + end) // 2

        if cache.get(middle):
            offset, line = cache[middle]

        else:
            line = ""
            while True:
                file.seek(max(0, middle - 1))
                if middle > 0:
                    file.discard_line()
                offset = file.tell()
                line = file.readline()
                if line != "":
                    break
                # at EOF; try to find start of the last line
                middle = (start + middle) // 2
                if middle == end - 1:
                    return None
            if currentDepth < cacheDepth:
                cache[middle] = (offset, line)

        if offset > end:
            assert end != middle - 1, "infinite loop"
            end = middle - 1
        elif line[:keylen] == key:
            return line
        elif line > key:
            assert end != middle - 1, "infinite loop"
            end = middle - 1
        elif line < key:
            start = offset + len(line) - 1

        currentDepth += 1
        thisState = start, end

        if lastState == thisState:
            # Detects the condition where we're searching past the end
            # of the file, which is otherwise difficult to detect
            return None

    return None


def gzip_open_unicode(
        filename,
        mode="rb",
        compresslevel=9,
        encoding='utf-8',
        fileobj=None,
        errors=None,
        newline=None,
):
    if fileobj is None:
        fileobj = GzipFile(filename, mode, compresslevel, fileobj)
    return io.TextIOWrapper(fileobj, encoding, errors, newline)


def split_resource_url(resource_url):
    """
    Splits a resource url into "<protocol>:<path>".
    """
    protocol, path_ = resource_url.split(':', 1)
    if protocol == 'file':
        if path_.startswith('/'):
            path_ = '/' + path_.lstrip('/')
    else:
        path_ = re.sub(r'^/{0,2}', '', path_)
    return protocol, path_

def make_path_absolute(path):
    if path and not os.path.isabs(path):
        return os.path.join(os.getcwd(), path)
    else:
        return path

def normalize_resource_url(resource_url):
    r"""
    Normalizes a resource url
    """
    try:
        protocol, name = split_resource_url(resource_url)
    except ValueError:
        # the resource url has no protocol, use the nltk protocol by default
        protocol = 'nltk'
        name = resource_url
    # use file protocol if the path is an absolute path
    if protocol == 'nltk' and os.path.isabs(name):
        protocol = 'file://'
        name = normalize_resource_name(name, False, None)
    elif protocol == 'file':
        protocol = 'file://'
        # name is absolute
        name = normalize_resource_name(name, False, None)
    elif protocol == 'nltk':
        protocol = 'nltk:'
        name = normalize_resource_name(name, True)
    else:
        # handled by urllib
        protocol += '://'
    return ''.join([protocol, name])


def normalize_resource_name(resource_name, allow_relative=True, relative_path=None):
    """
    :type resource_name: str or unicode
    :param resource_name: The name of the resource to search for.
        Resource names are posix-style relative path names, such as
        ``corpora/brown``.  Directory names will automatically
        be converted to a platform-appropriate path separator.
        Directory trailing slashes are preserved

    True
    """
    is_dir = bool(re.search(r'[\\/.]$', resource_name)) or resource_name.endswith(
        os.path.sep
    )
    if sys.platform.startswith('win'):
        resource_name = resource_name.lstrip('/')
    else:
        resource_name = re.sub(r'^/+', '/', resource_name)
    if allow_relative:
        resource_name = os.path.normpath(resource_name)
    else:
        if relative_path is None:
            relative_path = os.curdir
        resource_name = os.path.abspath(os.path.join(relative_path, resource_name))
    resource_name = resource_name.replace('\\', '/').replace(os.path.sep, '/')
    if sys.platform.startswith('win') and os.path.isabs(resource_name):
        resource_name = '/' + resource_name
    if is_dir and not resource_name.endswith('/'):
        resource_name += '/'
    return resource_name


######################################################################
# Access Functions
######################################################################

# Don't use a weak dictionary, because in the common case this
# causes a lot more reloading that necessary.
_resource_cache = {}


#: A dictionary describing the formats that are supported by the
#: load() method.  Keys are format names, and values are format
#: descriptions.
FORMATS = {
    'pickle': "A serialized python object, stored using the pickle module.",
    'json': "A serialized python object, stored using the json module.",
    'yaml': "A serialized python object, stored using the yaml module.",
    'cfg': "A context free grammar.",
    'pcfg': "A probabilistic CFG.",
    'fcfg': "A feature CFG.",
    'raw': "The raw (byte string) contents of a file.",
    'text': "The raw (unicode string) contents of a file. ",
    'csv': "tabulated mixed data format"
}

#: A dictionary mapping from file extensions to format names, used
#: by load() when format="auto" to decide the format for a
#: given resource url.
AUTO_FORMATS = {
    'pickle': 'pickle',
    'json': 'json',
    'yaml': 'yaml',
    'cfg': 'cfg',
    'logic': 'logic',
    'val': 'val',
    'txt': 'text',
    'text': 'text',
    'csv':'text',
}

def list_directory(path):
    # type: (Text) -> List[Text]
    """Returns all files and folders excluding hidden files.

    If the path points to a file, returns the file. This is a recursive
    implementation returning files in any depth of the path."""

    if not isinstance(path, six.string_types):
        raise ValueError("Resourcename must be a string type")

    if os.path.isfile(path):
        return [path]
    elif os.path.isdir(path):
        results = []
        for base, dirs, files in os.walk(path):
            # remove hidden files
            goodfiles = filter(lambda x: not x.startswith('.'), files)
            results.extend(os.path.join(base, f) for f in goodfiles)
        return results
    else:
        raise ValueError("Could not locate the resource '{}'."
                         "".format(os.path.abspath(path)))


def list_files(path):
    # type: (Text) -> List[Text]
    """Returns all files excluding hidden files.

    If the path points to a file, returns the file."""

    return [fn for fn in list_directory(path) if os.path.isfile(fn)]

def clear_cache():
    """
    Remove all objects from the resource cache.
    :see: load()
    """
    _resource_cache.clear()

def any2utf8(text, errors='strict', encoding='utf8'):
    """Convert a unicode or bytes string in the given encoding into a utf8 bytestring.

    Parameters
    ----------
    text : str
        Input text.
    errors : str, optional
        Error handling behaviour if `text` is a bytestring.
    encoding : str, optional
        Encoding of `text` if it is a bytestring.

    Returns
    -------
    str
        Bytestring in utf8.

    """

    if isinstance(text, str):
        return text.encode('utf8')
    # do bytestring -> unicode -> utf8 full circle, to ensure valid utf8
    return str(text, encoding, errors=errors).encode('utf8')



