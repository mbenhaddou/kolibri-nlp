import os, logging
from kolibri.settings import resources_path
from kolibri.data.downloader import DownloaderBase
DATA_DIR = resources_path
LOGGER = logging.getLogger(__name__)

class Ressources(DownloaderBase):

    def __init__(self):
        """

        """
        super().__init__(
            download_dir=DATA_DIR)

    def get(self, resource_path):
        self.download(resource_path)
        self.path=os.path.join(DATA_DIR, resource_path)
        return self