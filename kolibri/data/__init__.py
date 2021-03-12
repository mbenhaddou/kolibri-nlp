import os, sys
from kolibri.data.training_data import TrainingData

import logging
from kolibri.utils.file import list_files
from kolibri.data.format.kolibri import KolibriReader
from kolibri.data.format.json import JsonReader
from kolibri.data.format.Csv import CsvReader
from kolibri.data.format import _guess_format
from kolibri.utils.file import *

#supported formats
UNK="unknown"
KOLIBRI= "kolibri"
MARKDOWN="ms"
JSON="json"
CSV="csv"
XLSX="xlsx"

logger = logging.getLogger(__name__)


def load_data(resource_name, **kwargs):
    """Load training data from disk.

    Merges them if loaded from disk and multiple files are found."""

    files = list_files(resource_name)
    data_sets = [_load(f, **kwargs) for f in files]
    data_sets = [ds for ds in data_sets if ds is not None]
    language=None
    if "language" in kwargs:
        language=kwargs["language"]
    if len(data_sets) == 0:
        training_data = TrainingData(language=language)
    elif len(data_sets) == 1:
        training_data = TrainingData(language=language, training_examples=data_sets[0])
    else:
        training_data = data_sets[0].merge(*data_sets[1:], ignore_index=True)

    training_data.validate()

    return training_data


def _reader_factory(fformat):
    """Generates the appropriate reader class based on the file format."""
    reader = None
    if fformat == KOLIBRI:
        reader = KolibriReader()
    elif fformat == CSV or fformat==XLSX:
        reader = CsvReader(fformat)

    elif fformat ==JSON:
        reader = JsonReader()

    return reader


def _load(filename, **kwargs):
    """Loads a single training data file from disk."""

    if 'format' not in kwargs:
        fformat = _guess_format(filename)
    else:
        fformat=kwargs['format']
    if fformat == UNK:
        raise ValueError("Unknown data format for file {}".format(filename))

    logger.info("Training data format of {} is {}".format(filename, fformat))
    reader = _reader_factory(fformat)

    if reader:
        kwargs["fformat"]=fformat
        return reader.reads(filename, **kwargs)
    else:
        return None


