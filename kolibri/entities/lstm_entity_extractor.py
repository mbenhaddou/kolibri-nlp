import logging
import os
import typing
from typing import Any, List, Text, Tuple

from kolibri.classifier.dnn.api import DnnModel
from kolibri.document import Document
from kolibri.entities import EntityExtractor
from kolibri.entities.preprocessing import from_json_to_bio
from seqeval.metrics.sequence_labeling import get_entities
import numpy as np

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    pass

LSTM_MODEL_FILE_NAME = "lstm_model.pkl"
LSTM_PREPROCESS_FILE_NAME = "preprocessing.json"
LSTM_PARAM_FILE_NAME = "parameters.json"


class LSTMEntityExtractor(EntityExtractor):
    name = "ner_lstm"

    provides = ["entities"]

    requires = ["tokens"]

    defaults = {
        # BILOU_flag determines whether to use BILOU tagging or not.
        # More rigorous however requires more examples per entity
        # rule of thumb: use only if more than 100 egs. per entity
        "BILOU_flag": False,

        # The maximum number of iterations for optimization algorithms.
        "epochs": 5,
        "optimizer": "rmsprop",
        "loss": "categorical_crossentropy",
        "metrics": ["accuracy"],
        "embeddings_dim": 50,
        "batch-size": 10,
        "drop-out": 0.1,
        "activation": "softmax",
        "max_sentence_length": 60,
        "use_lemma": True,
        "model_type": 'bi-lstm-crf'

    }

    def __init__(self, component_config=None, ent_tagger=None, w2idx=None, t2idx=None):

        super(LSTMEntityExtractor, self).__init__(component_config)

        self.ent_tagger = ent_tagger

        self._validate_configuration()

        self._check_pos_features_and_nlp()

        self._nb_standard_features = 4

        self.word2idx = w2idx

        self.tag2idx = t2idx

        if self.tag2idx:
            self.idx2tag = {i: w for w, i in self.tag2idx.items()}

    def _validate_configuration(self):
        return True

    def _check_pos_features_and_nlp(self):
        import itertools
        features = self.component_config.get("features", [])
        fts = set(itertools.chain.from_iterable(features))
        self.pos_features = ('pos' in fts or 'pos2' in fts)

    @classmethod
    def required_packages(cls):
        return ["keras", "seqeval"]

    def train(self, training_data, config, **kwargs):

        self._validate_configuration()

        # filter out pre-trained entity examples
        filtered_entity_examples = self.filter_trainable_entities(training_data.training_examples)

        # convert the dataset into features
        # this will train on ALL examples, even the ones
        # without annotations
        dataset = self._create_dataset(filtered_entity_examples)

        self._train_model(dataset)

    def _create_dataset(self, examples):
        dataset = []
        for i, example in enumerate(examples):
            entity_offsets = self._convert_example(example)
            if "sentences" in example:
                for sentence in example.sentences:
                    processed = from_json_to_bio(sentence, entity_offsets)
                    dataset.append(processed)

            else:
                processed = from_json_to_bio(example, entity_offsets)
                dataset.append(processed)

        return dataset

    def process(self, message, **kwargs):

        message.set_output_property("entities")
        if "sentences" in message:

            for sentence in message.sentences:
                extracted = self.add_extractor_name(self.extract_entities(sentence))
                message.entities = message.entities + extracted
        else:
            extracted = self.add_extractor_name(self.extract_entities(message))
            message.entities = message.entities + extracted

    @staticmethod
    def _convert_example(example):

        def convert_entity(entity):
            return entity["start"], entity["end"], entity["entity"]

        return [convert_entity(ent) for ent in example.get("entities", [])]

    @classmethod
    def load(cls,
             model_dir=None,
             model_metadata=None,
             cached_component=None,
             **kwargs  # type: Any
             ):

        meta = model_metadata.for_component(cls.name)

        model_file = os.path.join(model_dir, LSTM_MODEL_FILE_NAME)
        preprocessing_file = os.path.join(model_dir, LSTM_PREPROCESS_FILE_NAME)
        param_file_name = os.path.join(model_dir, LSTM_PARAM_FILE_NAME)

        if os.path.exists(model_file):
            ent_tagger = DnnModel.load(params_file=param_file_name, weights_file=model_file,
                                       preprocessor_file=preprocessing_file)
            return cls(meta, ent_tagger)
        else:
            return cls(meta)

    def persist(self, model_dir):
        """Persist this model into the passed directory.

        Returns the metadata necessary to load the model again."""

        if self.ent_tagger:
            model_file_name = os.path.join(model_dir, LSTM_MODEL_FILE_NAME)
            preprocessing_file_name = os.path.join(model_dir, LSTM_PREPROCESS_FILE_NAME)
            param_file_name = os.path.join(model_dir, LSTM_PARAM_FILE_NAME)

            self.ent_tagger.save(model_file_name, param_file_name, preprocessing_file_name)

        return {"classifier_file": LSTM_MODEL_FILE_NAME, "preprocessing_file": LSTM_PREPROCESS_FILE_NAME}

    def _train_model(self, df_train):
        word_offset = 0
        if self.component_config["use_lemma"] and self.pos_features:
            word_offset = 3
        X = [[w[word_offset] for w in s] for s in df_train]
        y = [[w[2] for w in s] for s in df_train]

        model = DnnModel(model_type= self.component_config['model_type'])

        model.fit(X, y, epochs=self.component_config['epochs'], batch_size=self.component_config['batch-size'])
        self.ent_tagger = model
        self.component_config["Avg_cross_val_score_f1"] = self.ent_tagger.current_score

    def extract_entities(self, message):
        """Take a sentence and return entities in json format"""
        if self.ent_tagger is not None:
            if self.component_config["use_lemma"] and self.pos_features:
                x = [t.lemma for t in message.tokens]
            else:
                x = [t.text for t in message.tokens]
            pred, prob = self.ent_tagger.predict([x])
            return self._build_response(message, pred, prob)
        else:
            return []
