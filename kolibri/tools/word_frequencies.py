from functools import lru_cache
import logging
import math
import json
import os
from kolibri.settings import resources_path
from kolibri.utils.file import list_files
logger = logging.getLogger(__name__)

DATA_PATH = os.path.join(resources_path, 'corpora/wordfreq')


def available_languages():
    """
    Given a wordlist name, return a dictionary of language codes to filenames,
    representing all the languages in which that wordlist is available.
    """


    available = {}
    for path in list_files(DATA_PATH):
        filename=os.path.basename(path)
        list_name = filename.split('.')[0]
        lang = list_name.split('_')[2]
        available[lang] = str(path)
    return available

def zipf_to_freq(zipf):
    """
    Convert a word frequency from the Zipf scale to a proportion between 0 and
    1.

    The Zipf scale is a logarithmic frequency scale proposed by Marc Brysbaert,
    who compiled the SUBTLEX data. The goal of the Zipf scale is to map
    reasonable word frequencies to understandable, small positive numbers.

    A word rates as x on the Zipf scale when it occurs 10**x times per billion
    words. For example, a word that occurs once per million words is at 3.0 on
    the Zipf scale.
    """
    return 10 ** zipf / 1e9

def freq_to_zipf(freq):
    """
    Convert a word frequency from a proportion between 0 and 1 to the
    Zipf scale (see `zipf_to_freq`).
    """
    return math.log(freq, 10) + 9

@lru_cache(maxsize=None)
def get_frequency_dict(lang):
    """
    Get a word frequency list as a dictionary, mapping tokens to
    frequencies as floating-point probabilities.
    """
    languages=available_languages()
    if lang in languages:
        freqs= json.loads()
    else:
        raise Exception(lang+" language is not available")
    return freqs



