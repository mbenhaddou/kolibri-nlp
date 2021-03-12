import re
import logging
import math
from kolibri.data import TrainingData
import pandas as pd
from kolibri.document import Document
#from KOLIBRI.DataLoader.load_dataset import csv_data_reader
CLASS = "class"
SYNONYM = "synonym"
REGEX = "regex"
LOOKUP = "lookup"
available_sections = [CLASS, SYNONYM, REGEX, LOOKUP]
ent_regex = re.compile(r'\[(?P<entity_text>[^\]]+)'
                       r'\]\((?P<entity>[^:)]*?)'
                       r'(?:\:(?P<value>[^)]+))?\)')  # [entity_text](entity_type(:entity_synonym)?)

item_regex = re.compile(r'\s*[-\*+]\s*(.+)')
comment_regex = re.compile(r'<!--[\s\S]*?--!*>', re.MULTILINE)
fname_regex = re.compile(r'\s*([^-\*+]+)')

logger = logging.getLogger(__name__)


class CsvReader():
    """Reads markdown training data and creates a TrainingData object."""

    def __init__(self, format):
        self.training_examples = []
        self.separator=','
        self.content_col=None
        self.target_col=None
        self.file_format=format
    def reads(self, s, **kwargs):
        """Read markdown string and create TrainingData object"""

        if "separator" in kwargs:
            self.separator= kwargs["separator"]

        if "content" in kwargs:
            self.content_col=kwargs["content"]

        if "target" in kwargs:
            self.target_col=kwargs["target"]

        if self.file_format=='csv':
            data=pd.read_csv(s, delimiter=self.separator)
        elif self.file_format=='xlsx':
            data=pd.read_excel(s)

        for i,  d in data.iterrows():
            self._parse_item(i, d)

        return self.training_examples


    def _parse_item(self,idx,  row):
        """Parses an md list item line based on the current section type."""
        self.training_examples.append(self._parse_training_example(idx, row))

    def _parse_training_example(self, idx, example):
        """Extract entities and synonyms, and convert to plain text."""
        text=None
        label=None
        if self.target_col:
            label=example[self.target_col]
        if self.content_col:
            text=str(example[self.content_col])
        document = Document(text, {'target': label})
        document.idx=idx
        return document
