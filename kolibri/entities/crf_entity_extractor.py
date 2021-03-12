import logging
import os, csv, operator

import typing
from builtins import str
from typing import Any, Dict, List, Optional, Text, Tuple
from kolibri.classifier.model import KolibriModel
from kolibri.config import ModelConfig, InvalidConfigError
from kolibri.entities import EntityExtractor
from kolibri.model import Metadata
from kolibri.document import Document
from kolibri.data import TrainingData
from kolibri.utils import overlap
from kolibri.utils import alnum_or_num
from seqeval.metrics.sequence_labeling import get_entities

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    import sklearn_crfsuite

CRF_MODEL_FILE_NAME = "crf_model.pkl"


class CRFEntityExtractor(EntityExtractor):
    name = "ner_crf"

    provides = ["entities"]

    requires = ["tokens"]

    defaults = {
        # BILOU_flag determines whether to use BILOU tagging or not.
        # More rigorous however requires more examples per entity
        # rule of thumb: use only if more than 100 egs. per entity
        "BILOU_flag": False,

        # crf_features is [before, word, after] array with before, word,
        # after holding keys about which
        # features to use for each word, for example, 'title' in
        # array before will have the feature
        # "is the preceding word in title case?"
        # POS features require spaCy to be installed
        "features": [
            ["low", "title", "upper",  "pos", "pos2", "digit", 'lemma'],
            ["bias", "low", "prefix5", "prefix2", "suffix5", "suffix3","pos", "pos2",
             "suffix2", "upper", "title", "digit", "patterns", "pos", "lemma"],
            ["low", "title", "upper", "pos", "pos2", "lemma"]],

        # The maximum number of iterations for optimization algorithms.
        "max_iterations": 50,

        # weight of theL1 regularization
        "L1_c": 0.1,

        # weight of the L2 regularization
        "L2_c": 0.1
    }

    function_dict = {
        'low': lambda doc: doc[0].lower(),
        'title': lambda doc: doc[0].istitle(),
        'prefix5': lambda doc: doc[0][:5],
        'prefix2': lambda doc: doc[0][:2],
        'suffix5': lambda doc: doc[0][-5:],
        'suffix3': lambda doc: doc[0][-3:],
        'suffix2': lambda doc: doc[0][-2:],
        'suffix1': lambda doc: doc[0][-1:],
        'pos': lambda doc: doc[1],
        'pos2': lambda doc: doc[1][:2],
        'bias': lambda doc: 'bias',
        'upper': lambda doc: doc[0].isupper(),
        'digit': lambda doc: doc[0].isdigit(),
        'patterns': lambda doc: doc[4],
        'lemma': lambda doc: doc[3]
    }

    def __init__(self, component_config=None, ent_tagger=None):

        super(CRFEntityExtractor, self).__init__(component_config)

        self.ent_tagger = ent_tagger

        self._validate_configuration()

        self._check_pos_features_and_nlp()

        self._nb_standard_features=4
    def _check_pos_features_and_nlp(self):
        import itertools
        features = self.component_config.get("features", [])
        fts = set(itertools.chain.from_iterable(features))
        self.pos_features = ('pos' in fts or 'pos2' in fts)


    def _validate_configuration(self):
        if len(self.component_config.get("features", [])) % 2 != 1:
            raise ValueError("Need an odd number of crf feature "
                             "lists to have a center word.")

    @classmethod
    def required_packages(cls):
        return ["sklearn_crfsuite", "sklearn"]

    def train(self, training_data, config, **kwargs):
        # type: (TrainingData, ModelConfig) -> None

        self.component_config = config.for_component(self.name, self.defaults)

        self._validate_configuration()

        # checks whether there is at least one
        # example with an entity annotation
        if training_data.entity_examples:
            self._check_nlp_doc(training_data.training_examples[0])

            # filter out pre-trained entity examples
            filtered_entity_examples = self.filter_trainable_entities(
                    training_data.training_examples)

            # convert the dataset into features
            # this will train on ALL examples, even the ones
            # without annotations
            dataset = self._create_dataset(filtered_entity_examples)

            self._train_model(dataset)

    def _create_dataset(self, examples):
        # type: (List[Document]) -> List[List[Tuple[Text, Text, Text, Text]]]
        dataset = []
        for i, example in enumerate(examples):
            entity_offsets = self._convert_example(example)
            if "sentences" in example:
                for sentence in example.sentences:
                    dataset.append(self._from_json_to_crf(sentence, entity_offsets))
            else:
                dataset.append(self._from_json_to_crf(example, entity_offsets))

        i=0
        with open('data.csv', 'w') as csv_file:
            wr = csv.writer(csv_file, delimiter=',')

            for d in dataset:
                i += 1
                for e in d:
                    e+=(i,)
                    wr.writerow(list(e))
        return dataset

    def process(self, message, **kwargs):
        # type: (Document, **Any) -> None

        self._check_nlp_doc(message)
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
        # type: (Document) -> List[Tuple[int, int, Text]]

        def convert_entity(entity):
            return entity["start"], entity["end"], entity["entity"]

        return [convert_entity(ent) for ent in example.get("entities", [])]

    def extract_entities(self, message):
        # type: (Document) -> List[Dict[Text, Any]]
        """Take a sentence and return entities in json format"""

        if self.ent_tagger is not None:
            text_data = self._from_text_to_crf(message)
            features = self._sentence_to_features(text_data)
            ents = self.ent_tagger.model.predict_marginals_single(features)


            preds=[max(e.items(), key=operator.itemgetter(1))[0] for e in ents]
            probs=[max(e.items(), key=operator.itemgetter(1))[1] for e in ents]

            return self._build_response(message, preds, probs)
        else:
            return []

    def _create_entity_dict(self, tokens, start, end, entity, confidence):

        _start = tokens[start].start
        _end = tokens[end].end
        value = ' '.join(t.text for t in tokens[start:end + 1])

        return {
            'start': _start,
            'end': _end,
            'value': value,
            'entity': entity,
            'confidence': confidence
        }

    @staticmethod
    def _entity_from_label(label):
        return label[2:]

    @staticmethod
    def _bilou_from_label(label):
        if len(label) >= 2 and label[1] == "-":
            return label[0].upper()
        return None


    @classmethod
    def load(cls,
             model_dir=None,  # type: Text
             model_metadata=None,  # type: Metadata
             cached_component=None,  # type: Optional[CRFEntityExtractor]
             **kwargs  # type: Any
             ):
        # type: (...) -> CRFEntityExtractor
        from sklearn.externals import joblib

        meta = model_metadata.for_component(cls.name)
        file_name = meta.get("classifier_file", CRF_MODEL_FILE_NAME)
        model_file = os.path.join(model_dir, file_name)

        if os.path.exists(model_file):
            ent_tagger = joblib.load(model_file)
            return cls(meta, ent_tagger)
        else:
            return cls(meta)

    def persist(self, model_dir):
        # type: (Text) -> Optional[Dict[Text, Any]]
        """Persist this model into the passed directory.

        Returns the metadata necessary to load the model again."""

        from sklearn.externals import joblib

        if self.ent_tagger:
            model_file_name = os.path.join(model_dir, CRF_MODEL_FILE_NAME)

            joblib.dump(self.ent_tagger, model_file_name)

        return {"classifier_file": CRF_MODEL_FILE_NAME}

    def _sentence_to_features(self, sentence):
        # type: (List[Tuple[Text, Text, Text, Text]]) -> List[Dict[Text, Any]]
        """Convert a word into discrete features in self.crf_features,
        including word before and word after."""

        configured_features = self.component_config["features"]
        sentence_features = []

        sentence_features=[self.token2features(sentence, i, None) for i in range(len(sentence))]
        return sentence_features

    @staticmethod
    def _sentence_to_labels(sentence):
        # type: (List[Tuple[Text, Text, Text, Text]]) -> List[Text]

        return [token[2] for token in sentence]

    def _from_json_to_crf(self,
                          message,  # type: Document
                          entity_offsets  # type: List[Tuple[int, int, Text]]
                          ):
        # type: (...) -> List[Tuple[Text, Text, Text, Text]]
        """Convert json examples to format of underlying crfsuite."""


        tokens = message.get("tokens")


        if self.component_config["BILOU_flag"]:
            ents = self._bilou_tags_from_offsets(tokens, entity_offsets)
        else:
            ents = self._bio_tags_from_offsets(tokens, entity_offsets)
        if '-' in ents:
            logger.warning("Misaligned entity annotation in sentence '{}'. "
                           "Make sure the start and end values of the "
                           "annotated training examples end at token "
                           "boundaries (e.g. don't include trailing "
                           "whitespaces or punctuation)."
                           "".format(message.text))


        return self._from_text_to_crf(message, ents)

    @staticmethod
    def _bilou_tags_from_offsets(tokens, entities, missing='O'):
        starts = {token.start: i for i, token in enumerate(tokens)}
        ends = {token.end: i for i, token in enumerate(tokens)}
        bilou = ['-' for _ in tokens]
        # Handle entity cases
        for start_char, end_char, label in entities:
            start_token = starts.get(start_char)
            end_token = ends.get(end_char)
            # Only interested if the tokenization is correct
            if start_token is not None and end_token is not None:
                if start_token == end_token:
                    bilou[start_token] = 'U-%s' % label
                else:
                    bilou[start_token] = 'B-%s' % label
                    for i in range(start_token + 1, end_token):
                        bilou[i] = 'I-%s' % label
                    bilou[end_token] = 'L-%s' % label
        # Now distinguish the O cases from ones where we miss the tokenization
        entity_chars = set()
        for start_char, end_char, label in entities:
            for i in range(start_char, end_char):
                entity_chars.add(i)
        for n, token in enumerate(tokens):
            for i in range(token.start, token.end):
                if i in entity_chars:
                    break
            else:
                bilou[n] = missing

        return bilou

    @staticmethod
    def _bio_tags_from_offsets(tokens, entities):

        entities = sorted(entities, key=lambda k: k[0])
        for token in tokens:
            token.data['tag'] = 'O'

        start = 0
        for ent in entities:
            for i in range(start, len(tokens)):
                if overlap(ent[0], ent[1], tokens[i].start, tokens[i].end):
                    tokens[i].data['tag'] = "B-{0}".format(ent[2])
                    i = i + 1
                    start = i
                    while i< len(tokens) and overlap(ent[0], ent[1], tokens[i].start, tokens[i].end):
                        tokens[i].data['tag'] = "I-{0}".format(ent[2])
                        i = i + 1
                        start = i
                    break

        return [t.data['tag'] for t in tokens]


    @staticmethod
    def __pattern_of_token(message, i):
        patterns=()
        if message.tokens is not None:
            for key in message.tokens[i].patterns:
                patterns+=(message.tokens[i].patterns[key],)

        return patterns

    @staticmethod
    def __tag_of_token(token):
        return token.pos

    def _from_text_to_crf(self, message, entities=None):
        # type: (Document, List[Text]) -> List[Tuple[Text, Text, Text, Text]]
        """Takes a sentence and switches it to crfsuite format."""

        crf_format = []
        if self.pos_features:
            tokens = message.nlp_doc.tokens
        else:
            tokens = message.tokens
        for i, token in enumerate(tokens):
            patterns = self.__pattern_of_token(message, i)
            entity = entities[i] if entities else "N/A"
            tag = self.__tag_of_token(token) if self.pos_features else None
            lemma=token.lemma
            data_tuple=(token.text, tag, entity, lemma)+patterns
            crf_format.append(data_tuple)
        return crf_format

    def _train_model(self, df_train):
        # type: (List[List[Tuple[Text, Text, Text, Text]]]) -> None
        """Train the crf tagger based on the training data."""
        import sklearn_crfsuite
        logger.info('Start training CRF model')
        X_train = [self._sentence_to_features(sent) for sent in df_train]
        y_train = [self._sentence_to_labels(sent) for sent in df_train]

        self.ent_tagger = KolibriModel(sklearn_crfsuite.CRF(
                algorithm='lbfgs',
                # coefficient for L1 penalty
                c1=self.component_config["L1_c"],
                # coefficient for L2 penalty
                c2=self.component_config["L2_c"],
                # stop earlier
                max_iterations=self.component_config["max_iterations"],
                # include transitions that are possible, but not observed
                all_possible_transitions=True
        ))
        report=self.ent_tagger.fit(X_train, y_train)
#        print(report)
        logger.info(report)


    def token2features(self, sent, i, resourceList=None):

        word = str(sent[i][0])
        postag = sent[i][1]
        features = {
            'bias': 1.0,
            'word.lower()': word.lower(),
            'word.lemma': sent[i][3],
            'word[-3:]': word[-3:],
            'word.isupper()': word.isupper(),
            'word.istitle()': word.istitle(),
            'word.isdigit()': word.isdigit(),
            'word.alnum': alnum_or_num(word),
            'postag': postag,
            'postag[:2]': postag[:2],
        }
        if len(sent[i])>self._nb_standard_features:
            for j in range(self._nb_standard_features,len(sent[i])):
                features.update({
                  'patten_'+str(j-4):sent[i][j],
                })
        if i >0:
            word1 = str(sent[i-1][0])
            postag1 = sent[i-1][1]
            features.update({
                '-1:word.lower()': word1.lower(),
                '-1:word.lemma': sent[i-1][3],
                '-1:word.istitle()': word1.istitle(),
                '-1:word.isupper()': word1.isupper(),
                '-1:postag': postag1,
                '-1:postag[:2]': postag1[:2],

            })
            if len(sent[i]) > self._nb_standard_features:
                for j in range(self._nb_standard_features, len(sent[i])):
                    features.update({
                        '-1:patten_' + str(j - 4): sent[i-1][j],
                    })
        if i>1:
            word2 = str(sent[i-2][0])
            postag2 = sent[i-2][1]
            features.update({
                '-2:word.lower()': word2.lower(),
                '-2:word.istitle()': word2.istitle(),
                '-2:word.isupper()': word2.isupper(),
                '-2:postag': postag2,
                '-2:postag[:2]': postag2[:2],
            })
        if i > 2:
            word3 = str(sent[i - 3][0])
            postag3 = sent[i - 3][1]
            features.update({
                '-3:word.lower()': word3.lower(),
                '-3:word.istitle()': word3.istitle(),
                '-3:word.isupper()': word3.isupper(),
                '-3:postag': postag3,
                '-3:postag[:2]': postag3[:2],
            })

        if i==0:
            features['BOS'] = True

        if i < len(sent)-1:
            word1 = str(sent[i+1][0])
            postag1 = sent[i+1][1]
            features.update({
                '+1:word.lower()': word1.lower(),
                '+1:word.lemma()': sent[i+1][3],
                '+1:word.istitle()': word1.istitle(),
                '+1:word.isupper()': word1.isupper(),
                '+1:postag': postag1,
                '+1:postag[:2]': postag1[:2],
            })
        if i < len(sent)-2:
            word2 = str(sent[i+2][0])
            postag2 = sent[i+2][1]
            features.update({
                '+2:word.lower()': word2.lower(),
                '+2:word.lemma()': sent[i+2][3],
                '+2:word.istitle()': word2.istitle(),
                '+2:word.isupper()': word2.isupper(),
                '+2:postag': postag2,
                '+2:postag[:2]': postag2[:2],
            })
        if i < len(sent)-3:
            word3 = str(sent[i+3][0])
            postag3 = sent[i+3][1]
            features.update({
                '+2:word.lower()': word2.lower(),
                '+2:word.lemma()': sent[i+3][3],
                '+2:word.istitle()': word3.istitle(),
                '+2:word.isupper()': word3.isupper(),
                '+2:postag': postag3,
                '+2:postag[:2]': postag3[:2],
            })

        if i ==len(sent):
            features['EOS'] = True
        if resourceList is not None:
            for resource in resourceList:
                key=list(resource)[0]
                features.update({
                    'Matched_Res_'+key: word in resource[key]
                })
        return features
