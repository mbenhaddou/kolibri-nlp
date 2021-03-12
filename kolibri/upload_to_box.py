"""Upload the contents of your Downloads folder to Dropbox.
This is an example app for API v2.
"""

from __future__ import print_function

import argparse
import contextlib
import datetime
import os
import six
import sys, pickle
import time
import unicodedata
import hashlib

if sys.version.startswith('2'):
    input = raw_input  # noqa: E501,F821; pylint: disable=redefined-builtin,undefined-variable,useless-suppression

import dropbox

# OAuth2 access token.  TODO: login etc.
TOKEN = "qYwsaU_tSiwAAAAAAAAAARtn14mGqQldkfb5ZP_VQu3gOAKj4I1g0U7hcYv83sAT"

parser = argparse.ArgumentParser(description='Sync ~/Downloads to Dropbox')
parser.add_argument('folder', nargs='?', default='dummy_data',
                    help='Folder name in your Dropbox')
parser.add_argument('rootdir', nargs='?', default='~/Downloads/dummy_data',
                    help='Local directory to upload')
parser.add_argument('--token', default=TOKEN,
                    help='Access token '
                    '(see https://www.dropbox.com/developers/apps)')
parser.add_argument('--yes', '-y', action='store_true', default=True,
                    help='Answer yes to all questions')
parser.add_argument('--no', '-n', action='store_true',
                    help='Answer no to all questions')
parser.add_argument('--default', '-d', action='store_true',
                    help='Take default answer on all questions')


class DropboxManager():
    def __init__(self, local_dir, dbox_folder, token=None, default_yes=True):
        if token is not None:
            self.token=token
        else:
            self.token=TOKEN
        self.folder = dbox_folder
        self.rootdir=local_dir
    def synchronize(self):
        """Main program.
        Parse command line, then iterate over files and directories under
        rootdir and upload all files.  Skips some temporary files and
        directories, and avoids duplicate uploads by comparing size and
        mtime with the server.
        """
        args = parser.parse_args()
        if sum([bool(b) for b in (args.yes, args.no, args.default)]) > 1:
            print('At most one of --yes, --no, --default is allowed')
            sys.exit(2)
        if not args.token:
            print('--token is mandatory')
            sys.exit(2)


        rootdir = os.path.expanduser(self.rootdir)
        print('Dropbox folder name:', self.folder)
        print('Local directory:', self.rootdir)
        if not os.path.exists(self.rootdir):
            print(rootdir, 'does not exist on your filesystem')
            sys.exit(1)
        elif not os.path.isdir(self.rootdir):
            print(rootdir, 'is not a folder on your filesystem')
            sys.exit(1)
        try:
            local_db = dict(pickle.load(open(os.path.join(self.rootdir, "index"), "rb")))

        except:
            local_db={}
        dbx = dropbox.Dropbox(self.token)

        for dn, dirs, files in os.walk(self.rootdir):
            subfolder = dn[len(self.rootdir):].strip(os.path.sep)
            listing = list_folder(dbx, self.folder, subfolder)
            print('Descending into', subfolder, '...')

            # First do all the files.
            for name in files:
                fullname = os.path.join(dn, name)
                if not isinstance(name, six.text_type):
                    name = name.decode('utf-8')
                nname = unicodedata.normalize('NFC', name)
                if name.startswith('.'):
                    print('Skipping dot file:', name)
                    continue
                elif name.startswith('@') or name.endswith('~'):
                    print('Skipping temporary file:', name)
                    continue
                elif name.endswith('.pyc') or name.endswith('.pyo'):
                    print('Skipping generated file:', name)
                    continue
                elif nname in listing:
                    md = listing[nname]
                    mtime = os.path.getmtime(fullname)
                    mtime_dt = datetime.datetime(*time.gmtime(mtime)[:6])
                    size = os.path.getsize(fullname)
                    if (isinstance(md, dropbox.files.FileMetadata) and
                            mtime_dt == md.client_modified and size == md.size):
                        print(name, 'is already synced [stats match]')
                        continue
                    else:
                        print(name, 'exists with different stats, downloading')
                        res = download(dbx, self.folder, subfolder, name)
                        with open(fullname, "rb") as f:
                            data = f.read()
                        if res == data:
                            print(name, 'is already synced [content match]')
                        else:
                            print(name, 'has changed since last sync')
                            if yesno('Refresh %s' % name, False, args):
                                upload(dbx, fullname, self.folder, subfolder, name,
                                       overwrite=True)
                elif yesno('Upload %s' % name, True, args):
                    upload(dbx, fullname, self.folder, subfolder, name)
                path = '/%s/%s/%s' % (self.folder, subfolder.replace(os.path.sep, '/'), name)
                while '//' in path:
                    path = path.replace('//', '/')
                shared_links = dbx.sharing_list_shared_links()


                file_link=[l for l in shared_links.links if l.path_lower==path.lower()]
                if file_link:
                    url=file_link[0]
                else:
                    url=dbx.sharing_create_shared_link_with_settings(path)

                url=list(url.url)
                url[-1]=str(1)
                url="".join(url)
                checksum = md5(fullname)
                if subfolder !="":
                    path_key = '%s/%s' % (subfolder.replace(os.path.sep, '/'), name)
                else:
                    path_key=name
                local_db[path_key]={}
                local_db[path_key]['url']=url
                local_db[path_key]['checksum']=checksum

            pickle.dump(list(local_db.items()), open(os.path.join(rootdir, "index"),"wb"))
            time.sleep(2)
            upload(dbx, os.path.join(rootdir, "index"), self.folder, subfolder, "index")
            # Then choose which subdirectories to traverse.
            keep = []
            for name in dirs:
                if name.startswith('.'):
                    print('Skipping dot directory:', name)
                elif name.startswith('@') or name.endswith('~'):
                    print('Skipping temporary directory:', name)
                elif name == '__pycache__':
                    print('Skipping generated directory:', name)
                elif yesno('Descend into %s' % name, True, args):
                    print('Keeping directory:', name)
                    keep.append(name)
                else:
                    print('OK, skipping directory:', name)
            dirs[:] = keep

        dbx.close()

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def list_folder(dbx, folder, subfolder):
    """List a folder.
    Return a dict mapping unicode filenames to
    FileMetadata|FolderMetadata entries.
    """
    path = '/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'))
    while '//' in path:
        path = path.replace('//', '/')
    path = path.rstrip('/')
    try:
        with stopwatch('list_folder'):
            res = dbx.files_list_folder(path)
    except dropbox.exceptions.ApiError as err:
        print('Folder listing failed for', path, '-- assumed empty:', err)
        return {}
    else:
        rv = {}
        for entry in res.entries:
            rv[entry.name] = entry
        return rv

def download(dbx, folder, subfolder, name):
    """Download a file.
    Return the bytes of the file, or None if it doesn't exist.
    """
    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    with stopwatch('download'):
        try:
            md, res = dbx.files_download(path)
        except dropbox.exceptions.HttpError as err:
            print('*** HTTP error', err)
            return None
    data = res.content
    print(len(data), 'bytes; md:', md)
    return data

def upload(dbx, fullname, folder, subfolder, name, overwrite=False):
    """Upload a file.
    Return the request response, or None in case of error.
    """
    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)
    mtime = os.path.getmtime(fullname)
    with open(fullname, 'rb') as f:
        data = f.read()
    with stopwatch('upload %d bytes' % len(data)):
        try:
            res = dbx.files_upload(
                data, path, mode,
                client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                mute=True)
        except dropbox.exceptions.ApiError as err:
            print('*** API error', err)
            return None
    print('uploaded as', res.name.encode('utf8'))
    return res

def yesno(message, default, args):
    """Handy helper function to ask a yes/no question.
    Command line arguments --yes or --no force the answer;
    --default to force the default answer.
    Otherwise a blank line returns the default, and answering
    y/yes or n/no returns True or False.
    Retry on unrecognized answer.
    Special answers:
    - q or quit exits the program
    - p or pdb invokes the debugger
    """
    if args.default:
        print(message + '? [auto]', 'Y' if default else 'N')
        return default
    if args.yes:
        print(message + '? [auto] YES')
        return True
    if args.no:
        print(message + '? [auto] NO')
        return False
    if default:
        message += '? [Y/n] '
    else:
        message += '? [N/y] '
    while True:
        answer = input(message).strip().lower()
        if not answer:
            return default
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        if answer in ('q', 'quit'):
            print('Exit')
            raise SystemExit(0)
        if answer in ('p', 'pdb'):
            import pdb
            pdb.set_trace()
        print('Please answer YES or NO.')

@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        print('Total elapsed time for %s: %.3f' % (message, t1 - t0))

if __name__ == '__main__':
    dbx=DropboxManager(local_dir="/Users/mohamedmentis/Dropbox/My Mac (MacBook-Pro.local)/Documents/Mentis/Development/Data/kolibri_data", dbox_folder='kolibri_data')
    dbx.synchronize()