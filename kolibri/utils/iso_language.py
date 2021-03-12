
import json
from pathlib import Path
import os, logging
from kolibri.settings import resources_path
from kolibri.utils.downloader import Downloader
DATA_DIR = resources_path
LOGGER = logging.getLogger(__name__)
PACKAGE = 'corpora'
SUBPACKAGE = "gazetteers"
URL_MODEL="https://www.dropbox.com/s/3yavanlodzoj80k/gazetteers.tar.gz?dl=1"


db = str(Path(__file__).resolve().parent.joinpath('language_codes.db'))

data_file = os.path.join(os.sep, resources_path+os.sep, 'corpora'+os.sep, 'gazetteers'+os.sep,'languages.json')
if os.path.exists(data_file):
    language_data_iso2 = json.loads(open(data_file, encoding='utf-8').read())
else:
    dw=Downloader(PACKAGE, SUBPACKAGE, URL_MODEL)
    language_data_iso2 = json.loads(open(data_file, encoding='utf-8').read())
language_data_name = {y['Name'].lower(): {"iso2": x, "Autonym": y["Autonym"]} for x,y in language_data_iso2.items()}

def language(code):
    """Get name and autonym for a given two-letter language code.

    :param code: two-letter ISO language code
    :type code: str
    :return: {'Name': String with english name,
              'Autonym': String with native name}
    :rtype: dict
    :raises KeyError: raises key exception
    :raises TypeError: raises type exception
    :raises AssertionError: raises assert exception

    """
    if (len(code) == 2):
        return language_data_iso2[code.lower()]
    else:
        return language_data_name[code.lower()]

def language_name(code):
    """Get name for a given two-letter language code.

    :param code: two-letter ISO language code
    :type code: str

    """
    if (len(code) == 2):
        return language_data_iso2[code.lower()]['Name']
    else:
        return code

def language_iso2(code):
    if (len(code) == 2):
        return code
    else:
        if code.lower() in language_data_name:
            return language_data_name[code.lower()]['iso2']

        raise Exception("Unknown language: "+code)


def language_autonym(code):
    """Get autonym for a given two-letter ISO language code.

    :param code: two-letter ISO language code
    :type code: str

    """
    if (len(code) == 2) :
        return language_data_iso2[code.lower()]['Autonym']
    else:
        return language_data_name[code.lower()]['Autonym']


def language_dictionary():
    """Get entire dictionary. Two-letter code as keys."""
    return language_data_iso2

