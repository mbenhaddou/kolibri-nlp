import json
import os, logging
from kolibri.settings import resources_path
from kolibri.utils.downloader import Downloader
DATA_DIR = resources_path
LOGGER = logging.getLogger(__name__)


STOP_WORDS_DIR = os.path.join(resources_path,'stop-words')
STOP_WORDS_CACHE = {}

class Stopwords(Downloader):

    def __init__(self):
        """
        :param with_additional_file: Allows to load LEFFF without the additional file. (Default: True)
        :type with_additional_file: bool
        :param load_only_pos: Allows to load LEFFF with only some pos tags: WordNet pos tags [a, r, n, v]. (Default: all)
        :type load_only_pos: list
        """
        #        data_file_path = os.path.dirname(os.path.realpath(__file__))
        super().__init__(
            file_path="stop-words",
            download_dir=DATA_DIR)
        with open(os.path.join(STOP_WORDS_DIR, 'languages.json'), 'rb') as map_file:
            buffer = map_file.read()
            buffer = buffer.decode('ascii')
            self.LANGUAGE_MAPPING = json.loads(buffer)

        self.AVAILABLE_LANGUAGES = list(self.LANGUAGE_MAPPING.values())




class StopWordError(Exception):
    pass

sw=Stopwords()

def get_stop_words(language, cache=True, aggressive=False):
    """
    :type language: basestring
    :rtype: list
    """
    try:
        language = sw.LANGUAGE_MAPPING[language]
    except KeyError:
        if language not in sw.AVAILABLE_LANGUAGES:
            raise StopWordError('{0}" language is unavailable.'.format(
                language
            ))

    if cache and language in STOP_WORDS_CACHE:
        return STOP_WORDS_CACHE[language]
    language_name=language
    if aggressive:
        language_name+"-aggressive"
    language_filename = os.path.join(STOP_WORDS_DIR, language_name + '.txt')
    try:
        with open(language_filename, 'rb') as language_file:
            stop_words = [line.decode('utf-8').strip()
                          for line in language_file.readlines()]
    except IOError:
        raise StopWordError(
            '{0}" file is unreadable, check your installation.'.format(
                language_filename
            )
        )

    if cache:
        STOP_WORDS_CACHE[language] = stop_words

    return stop_words




