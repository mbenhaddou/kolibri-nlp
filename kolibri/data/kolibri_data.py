import logging
import os
import random
import warnings
from builtins import object, str
from collections import Counter
from copy import deepcopy
import pandas as pd
from langdetect import detect
from kolibri.settings import data
from kolibri.utils import write_to_file, list_to_str, lazyproperty
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

def detect_language(text):
    return detect(text[0: 300])

class kolibriData(object):
    """Holds loaded class and entity training data."""

    def __init__(self, training_examples_df: pd.DataFrame,language=None,detect_language=False):

        self.data = training_examples_df
        if training_examples_df is not None:
            self.post_process(language, detect_language)
        else:
            self.training_examples = []

        self.data_train = None
        self.data_test = None
        self.print_stats()

    def post_process(self, lang, detectlanguage=False):

        """Makes sure the training data is clean.

        removes trailing whitespaces from class annotations."""
        if '__target__' in self.data.columns:
            self.data['__target__']=self.data['__target__'].str.strip()
        if lang:
            self.data['__language__']=lang
        elif detectlanguage:
            self.data['__language__']=self.data['__content__'].str.apply(detect_language)


    @lazyproperty
    def examples_per_class(self):
        """Calculates the number of examples per class."""

        return dict(self.data['__target__'].value_counts())

    @lazyproperty
    def classes(self):
        """Returns the set of classes in the training data."""
        return self.data.__target__.unique()

    @lazyproperty
    def entities(self):
        """Returns the set of entity types in the training data."""
        entity_types = [e["entity"] for e in self.sorted_entities]
        return set(entity_types)

    @lazyproperty
    def examples_per_entity(self):
        """Calculates the number of examples per entity."""
        entity_types = [e["entity"] for e in self.sorted_entities]
        return dict(Counter(entity_types))

    def as_json(self, **kwargs):
        """Represent this set of training examples as json."""
        from kolibri.data.writer_reader import DataWriter
        return DataWriter().dumps(self)

    def persist(self, dir_name):
        """Persists this training data to disk and returns necessary
        information to load it again."""

        data_file = os.path.join(dir_name, "training_data.json")
        write_to_file(data_file, self.as_json(indent=2))

        return {
            "training_data": "training_data.json"
        }

    @lazyproperty
    def sorted_entities(self):
        """Extract all entities from examples and sorts them by entity type."""

        entity_examples = [entity
                           for ex in self.entity_examples
                           for entity in ex.entities]
        return sorted(entity_examples, key=lambda e: e["entity"])

    def validate(self):
        """Ensures that the loaded training data is valid.

        Checks that the data has a minimum of certain training examples."""

        logger.debug("Validating training data...")
        if "" in self.classes:
            warnings.warn("Found empty class, please check your "
                          "training data. This may result in wrong "
                          "class predictions.")

        # emit warnings for classs with only a few training samples
        for aClass, count in self.examples_per_class.items():
            if count < data.MIN_EXAMPLES_PER_CLASS:
                warnings.warn("Class '{}' has only {} training examples! "
                              "Minimum is {}/ Removing {}."
                              .format(aClass, count,
                                      data.MIN_EXAMPLES_PER_CLASS, aClass))
                self.data = self.data.drop(self.data[self.data.__target__==aClass].index)


    def train_test_split(self, train_frac=0.8):
        """Split into a training and test dataset, preserving the fraction of examples per class."""
        self._train_indices, self._test_indices=train_test_split(self.data.index, train_size=train_frac)

    def print_stats(self):
        logger.info("Training data stats: \n" +
                    "\t- class examples: {} ({} distinct classs)\n".format(
                        len(self.data.index), len(self.classes)) +
                    "\t- Found classes: {}\n".format(
                        list_to_str(self.classes)))
