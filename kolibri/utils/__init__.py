import simplejson, os, io, re, six
import json
import numpy as np
from typing import Text, Any
import errno, inspect
from .file import binary_search_file
from .probability import *
import requests
from requests.exceptions import InvalidURL
from .dict import Dict
from kolibri.utils.file import create_temporary_file
import subprocess
from kolibri.utils._collections import *
import logging


logger = logging.getLogger(__name__)


def overlap(start1, end1, start2, end2):
    return not (end1 <= start2 or start1 >= end2)


def alnum_or_num(text):
    return any(char.isdigit() for char in text)

# noinspection PyPep8Naming
class bcolors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def ensure_list(iterable):
    """
    An Iterable may be a list or a generator.
    This ensures we get a list without making an unnecessary copy.
    """
    if isinstance(iterable, list):
        return iterable
    else:
        return list(iterable)


def namespace_match(pattern: str, namespace: str):
    """
    Matches a namespace pattern against a namespace string.  For example, ``*tags`` matches
    ``passage_tags`` and ``question_tags`` and ``tokens`` matches ``tokens`` but not
    ``stemmed_tokens``.
    """
    if pattern[0] == "*" and namespace.endswith(pattern[1:]):
        return True
    elif pattern == namespace:
        return True
    return False

def wrap_with_color(text, color):
    return color + text + bcolors.ENDC


def print_color(text, color):
    print(wrap_with_color(text, color))

def reduce_mean_max(vectors: np.ndarray):
    return np.hstack(np.mean(vectors, 0), np.max(vectors, 0))


def np_first(vectors: np.ndarray):
    return np.array(vectors)[0]


def np_last(vectors: np.ndarray):
    return np.array(vectors)[-1]

POOL_FUNC_MAP = {
    "reduce_mean": np.mean,
    "reduce_max": np.max,
    "reduce_min": np.min,
    "reduce_mean_max": reduce_mean_max,
    "first_token": np_first,
    "last_token": np_last
}

def module_path_from_object(o):
    """Returns the fully qualified class path of the instantiated object."""
    return o.__class__.__module__ + "." + o.__class__.__name__


def is_limit_reached(num_messages, limit):
    return limit is not None and num_messages >= limit

def configure_file_logging(loglevel, logfile):
    if logfile:
        fh = logging.FileHandler(logfile)
        fh.setLevel(loglevel)
        logging.getLogger('').addHandler(fh)
    logging.captureWarnings(True)


def generate_id(prefix="", max_chars=None):
    import uuid
    gid = uuid.uuid4().hex
    if max_chars:
        gid = gid[:max_chars]

    return "{}{}".format(prefix, gid)

def lazyproperty(fn):
    """Allows to avoid recomputing a property over and over.

    The result gets stored in a local var. Computation of the property
    will happen once, on the first call of the property. All
    succeeding calls will use the text stored in the private property."""

    attr_name = '_lazy_' + fn.__name__

    @property
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazyprop



def as_text_type(t):
    if isinstance(t, six.text_type):
        return t
    else:
        return six.text_type(t)

def arguments_of(func):
    """Return the parameters of the function `func` as a list of their names."""

    try:
        # python 3.x is used
        return list(inspect.signature(func).parameters.keys())
    except AttributeError:
        # python 2.x is used
        # noinspection PyDeprecation
        return list(inspect.getargspec(func).args)


def json_to_string(obj, **kwargs):
    indent = kwargs.pop("indent", 2)
    ensure_ascii = kwargs.pop("ensure_ascii", False)
    return json.dumps(obj, indent=indent, ensure_ascii=ensure_ascii, **kwargs)


def write_json_to_file(filename, obj, **kwargs):
    # type: (Text, Any) -> None
    """Write an object as a json string to a file."""

    write_to_file(filename, json_to_string(obj, **kwargs))

def remove_none_values(obj):
    """Remove all keys that store a `None` text."""
    return {k: v for k, v in obj.items() if v is not None}

def write_to_file(filename, text):
    # type: (Text, Text) -> None
    """Write a text to a file."""

    with io.open(filename, 'w', encoding="utf-8") as f:
        f.write(str(text))


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj




def list_to_str(l, delim=", ", quote="'"):
    return delim.join([quote + e + quote for e in l])


def is_int(value):
    # type: (Any) -> bool
    """Checks if a value is an integer.

    The type of the value is not important, it might be an int or a float."""

    # noinspection PyBroadException
    try:
        return value == int(value)
    except Exception:
        return False
def add_logging_option_arguments(parser, default=logging.WARNING):
    """Add options to an argument parser to configure logging levels."""

    # arguments for logging configuration
    parser.add_argument(
            '--debug',
            help="Print lots of debugging statements. "
                 "Sets logging level to DEBUG",
            action="store_const",
            dest="loglevel",
            const=logging.DEBUG,
            default=default,
    )
    parser.add_argument(
            '-v', '--verbose',
            help="Be verbose. Sets logging level to INFO",
            action="store_const",
            dest="loglevel",
            const=logging.INFO,
    )



def extract_args(kwargs,  # type: Dict[Text, Any]
                 keys_to_extract  # type: Set[Text]
                 ):
    # type: (...) -> Tuple[Dict[Text, Any], Dict[Text, Any]]
    """Go through the kwargs and filter out the specified keys.

    Return both, the filtered kwargs as well as the remaining kwargs."""

    remaining = {}
    extracted = {}
    for k, v in kwargs.items():
        if k in keys_to_extract:
            extracted[k] = v
        else:
            remaining[k] = v

    return extracted, remaining

def is_url(resource_name):
    """Return True if string is an http, ftp, or file URL path.

    This implementation is the same as the one used by matplotlib"""

    URL_REGEX = re.compile(r'http://|https://|ftp://|file://|file:\\')
    return URL_REGEX.match(resource_name) is not None


def download_file_from_url(url):
    # type: (Text) -> Text
    """Download a story file from a url and persists it into a temp file.

    Returns the file path of the temp file that contains the
    downloaded content."""

    if not is_url(url):
        raise InvalidURL(url)

    response = requests.get(url)
    response.raise_for_status()
    filename = create_temporary_file(response.content,
                                               mode="w+b")

    return filename


def build_entity(start, end, value, entity_type, **kwargs):
    """Builds a standard entity dictionary.

    Adds additional keyword parameters."""

    entity = Dict({
        "start": start,
        "end": end,
        "text": value,
        "entity": entity_type
    })

    entity.update(kwargs)
    return entity

def check_output(stdout=subprocess.PIPE, *popenargs, **kwargs):
    r"""Run OS command with the given arguments and return its output as a byte string.
    Backported from Python 2.7 with a few minor modifications. Widely used for :mod:`gensim.models.wrappers`.
    Behaves very similar to https://docs.python.org/2/library/subprocess.html#subprocess.check_output.
    """
    try:
        logger.debug("COMMAND: %s %s", popenargs, kwargs)
        process = subprocess.Popen(stdout=stdout, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            error = subprocess.CalledProcessError(retcode, cmd)
            error.output = output
            raise error
        return output
    except KeyboardInterrupt:
        process.terminate()
        raise

def argsort(x, topn=None, reverse=False):
    """Efficiently calculate indices of the `topn` smallest elements in array `x`.
    Parameters
    ----------
    x : array_like
        Array to get the smallest element indices from.
    topn : int, optional
        Number of indices of the smallest (greatest) elements to be returned.
        If not given, indices of all elements will be returned in ascending (descending) order.
    reverse : bool, optional
        Return the `topn` greatest elements in descending order,
        instead of smallest elements in ascending order?
    Returns
    -------
    numpy.ndarray
        Array of `topn` indices that sort the array in the requested order.
    """
    x = np.asarray(x)  # unify code path for when `x` is not a np array (list, tuple...)
    if topn is None:
        topn = x.size
    if topn <= 0:
        return []
    if reverse:
        x = -x
    if topn >= x.size or not hasattr(np, 'argpartition'):
        return np.argsort(x)[:topn]
    # np >= 1.8 has a fast partial argsort, use that!
    most_extreme = np.argpartition(x, topn)[:topn]
    return most_extreme.take(np.argsort(x.take(most_extreme)))  # resort topn into order

def subsample_array(arr, max_values, can_modify_incoming_array=True,
                    rand=None):
    # type: (List[Any], int, bool, Optional[Random]) -> List[Any]
    """Shuffles the array and returns `max_values` number of elements."""
    import random

    if not can_modify_incoming_array:
        arr = arr[:]
    if rand is not None:
        rand.shuffle(arr)
    else:
        random.shuffle(arr)
    return arr[:max_values]

class ArgSingleton(type):
    """ This is a Singleton metaclass. All classes affected by this metaclass
    have the property that only one instance is created for each set of arguments
    passed to the class constructor."""

    def __init__(cls, name, bases, dict):
        super(ArgSingleton, cls).__init__(cls, bases, dict)
        cls._instanceDict = {}

    def __call__(cls, *args, **kwargs):
        argdict = {'args': args}
        argdict.update(kwargs)
        argset = frozenset(sorted(argdict.items()))
        if argset not in cls._instanceDict:
            cls._instanceDict[argset] = super(ArgSingleton, cls).__call__(*args, **kwargs)
        return cls._instanceDict[argset]