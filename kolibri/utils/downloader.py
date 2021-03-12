import os
import errno
import logging
import tarfile
import pickle
import requests
import re
from tqdm import tqdm
from kolibri.settings import resources_path
from copy import copy
DATA_DIR = resources_path
LOGGER = logging.getLogger(__name__)

remote_index_url='https://www.dropbox.com/s/l4n6m4lelbbgxki/index?dl=1'

class DownloaderBase(object):
    def __init__(self,  download_dir=DATA_DIR):
        self._error = None
        self.download_dir=download_dir

        try:
            self.local_db = dict(pickle.load(open(os.path.join(DATA_DIR, ".index"), "rb")))
        except IOError as e:
            print(e)
            self.local_db = {}
        self.server_db=_download_db()


    def download(self, file_path):

        self.pkg=os.path.splitext(os.path.basename(file_path))[0]
        file_path_key=file_path
        if file_path in self.server_db.keys():
            self.url =self.server_db[file_path]['url']
        elif file_path+'.tar.gz' in self.server_db.keys():
            file_path_key+='.tar.gz'
            self.url = self.server_db[file_path_key]['url']
        else:
            LOGGER.error("Couldn't find file {}.".format(file_path))

        if not os.path.exists(self.download_dir):
            os.mkdir(self.download_dir)
        server_file_entry=self.server_db.get(file_path_key, None)
        local_file_entry=self.local_db.get(file_path_key, None)
        if server_file_entry is not None:
            server_file_checksum=server_file_entry['checksum']
            local_file_checksum=-1
            if local_file_entry is not None:
                local_file_checksum=local_file_entry['checksum']
            if server_file_checksum != local_file_checksum or not os.path.exists(os.path.join(self.download_dir, file_path)):
                self._download_data(file_path_key)
                LOGGER.info('data already set up')
                self.local_db[file_path_key]=copy(self.server_db[file_path])
                pickle.dump(list(self.local_db.items()), open(os.path.join(DATA_DIR, ".index"), "wb"))


    @staticmethod
    def get_filename_from_cd(cd):
        """
        Get filename from content-disposition
        """
        if not cd:
            return None
        fname = re.findall('filename="(.+)"', cd)
        if len(fname) == 0:
            return None
        return fname[0]

    def _download_data(self, file_path):
        LOGGER.info('downloading data for {}...'.format(self.pkg))
        r = requests.get(self.url, stream=True)
        total_length = r.headers.get('content-length', 0)
        pbar = tqdm(
                unit='B', unit_scale=True,
                total=int(total_length))
        if total_length is None:
            LOGGER.error("Couldn't fetch model data.")
            raise Exception("Couldn't fetch model data.")
        else:
            filename = self.get_filename_from_cd(
                r.headers.get('content-disposition'))
            path = os.path.join(self.download_dir, file_path)
            if not os.path.exists(os.path.dirname(path)):
                try:
                    os.makedirs(os.path.dirname(path))
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise
            with open(path, 'wb') as f:
                for data in r.iter_content(chunk_size=4096):
                    f.write(data)
                    pbar.update(len(data))
            if filename.endswith('.tar.gz'):
                tar = tarfile.open(path, "r:gz")
                for tarinfo in tar:
                    tar.extract(tarinfo, os.path.dirname(path))
                tar.close()
                # clean raw tar gz
                os.remove(path)
            LOGGER.info('download complete')



class Downloader(DownloaderBase):
    def __init__(self, file_path, download_dir=DATA_DIR):
        super().__init__(download_dir)

        self.download(file_path)





def _download_db():
        LOGGER.info('downloading metadata db')

        r = requests.get(remote_index_url, stream=True)
        total_length = r.headers.get('content-length', 0)
        pbar = tqdm(
                unit='B', unit_scale=True,
                total=int(total_length))
        if total_length is None:
            LOGGER.error("Couldn't fetch model data.")
            raise Exception("Couldn't fetch model data.")
        else:
            filename = Downloader.get_filename_from_cd(
                r.headers.get('content-disposition'))
            path = os.path.join(DATA_DIR, filename)
            with open(path, 'wb') as f:
                for data in r.iter_content(chunk_size=4096):
                    f.write(data)
                    pbar.update(len(data))
            if filename.endswith('.tar.gz'):
                tar = tarfile.open(path, "r:gz")
                for tarinfo in tar:
                    tar.extract(tarinfo, DATA_DIR)
                tar.close()
            db= dict(pickle.load(open(os.path.join(path), "rb")))
            os.remove(path)
            LOGGER.info('download complete')
            return db
