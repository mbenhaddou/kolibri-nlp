import logging
import os
import random
import warnings
from builtins import object, str
from collections import Counter
from copy import deepcopy

from langdetect import detect

from kolibri.settings import data
from kolibri.utils import write_to_file, list_to_str, lazyproperty

logger = logging.getLogger(__name__)


class TrainingData(object):
    """Holds loaded class and entity training data."""

    def __init__(self, language=None, training_examples=None, detect_language=False):

        if training_examples:
            self.training_examples = self.post_process(training_examples, language, detect_language)
        else:
            self.training_examples = []

        self.data_train = None
        self.data_test = None
        self.print_stats()

    def merge(self, *others):
        """Return merged instance of this data with other training data."""

        training_examples = deepcopy(self.training_examples)

        for o in others:
            training_examples.extend(deepcopy(o.training_examples))

        return TrainingData(training_examples)

    @staticmethod
    def post_process(examples, lang, detectlanguage):

        """Makes sure the training data is clean.

        removes trailing whitespaces from class annotations."""

        for ex in examples:
            ex.language = lang
            if detectlanguage:
                ex.detectedlanguage=detect(ex.text[0: 500])
            if ex.target:
                if isinstance(ex.target, str):
                    ex.target = ex.target.strip()
        return examples

    @lazyproperty
    def class_examples(self):
        return [ex
                for ex in self.training_examples
                if ex.target]

    @lazyproperty
    def entity_examples(self):
        return [ex
                for ex in self.training_examples
                if ex.entities]

    def targets(self, tag):
        """Returns the set of targets in the training data."""
        return set([ex.tag for ex in self.training_examples]) - {None}

    @lazyproperty
    def classes(self):
        """Returns the set of classes in the training data."""
        return self.targets("target")

    @lazyproperty
    def examples_per_class(self):
        """Calculates the number of examples per class."""
        classes = [ex.target for ex in self.training_examples]
        return dict(Counter(classes))

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

    def sorted_class_examples(self):
        """Sorts the class examples by the name of the class."""

        return sorted(self.class_examples, key=lambda e: e.target)

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
                self.training_examples = [example for example in self.training_examples if example['target'] != aClass]

        # emit warnings for entities with only a few training samples
        for entity_type, count in self.examples_per_entity.items():
            if count < data.MIN_EXAMPLES_PER_ENTITY:
                warnings.warn("Entity '{}' has only {} training examples! "
                              "minimum is {}. Removing {}."
                              "".format(entity_type, count,
                                        data.MIN_EXAMPLES_PER_ENTITY, entity_type))

                self.remove_entity_type(entity_type)

    def remove_entity_type(self, entity_type):
        for example in self.entity_examples:
            example['entities'] = [entity for entity in example['entities'] if entity['entity'] != entity_type]

    def train_test_split(self, train_frac=0.8):
        """Split into a training and test dataset, preserving the fraction of examples per class."""
        train, test = [], []
        for aClass, count in self.examples_per_class.items():
            ex = [e for e in self.class_examples if e.data["target"] == aClass]
            random.shuffle(ex)
            n_train = int(count * train_frac)
            train.extend(ex[:n_train])
            test.extend(ex[n_train:])

        self.data_train = TrainingData(
            train
        )
        self.data_test = TrainingData(
            test
        )

    def print_stats(self):
        logger.info("Training data stats: \n" +
                    "\t- class examples: {} ({} distinct classs)\n".format(
                        len(self.class_examples), len(self.classes)) +
                    "\t- Found classes: {}\n".format(
                        list_to_str(self.classes)) +
                    "\t- entity examples: {} ({} distinct entities)\n".format(
                        len(self.entity_examples), len(self.entities)) +
                    "\t- found entities: {}\n".format(
                        list_to_str(self.entities)))
