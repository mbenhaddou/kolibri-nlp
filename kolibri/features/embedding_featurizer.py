import numpy as np
from typing import Any
from kolibri.features.features import Features
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from kolibri.embeddings.Embedder import Embedder
import os
from kolibri.embeddings.fasttext import Embeddings as fastext, Embedding
from kolibri.embeddings.word2vec import  Embeddings as word2vec
from kolibri.embeddings.gensim import  Embeddings as gensim
from kolibri.features.word2vec_vectorizer import Transform2WordVectors
from string import punctuation

def ndim(_nlp):
    """Number of features used to represent a document / sentence."""
    return _nlp.vocab.vectors_length


def features_for_doc( doc):
    """Feature vector for a single document / sentence."""


    return doc.vector


class EmbeddingsFeaturizer(Features):
    name = "embedding_featurizer"

    provides = ["text_features"]

    requires = ["tokens"]
    defaults = {
        # the parameters are taken from
        # sklearn's CountVectorizer

        # regular expression for tokens
        "token_pattern": r'(?u)\b\w\w+\b',

        # remove accents during the preprocessing step
        "strip_accents": None,  # {'ascii', 'unicode', None}

        # list of stop words
        "stop_words": None,  # string {'en'}, list, or None (default)

        # min document frequency of a word to add to vocabulary
        # float - the parameter represents a proportion of documents
        # integer - absolute counts
        "min_df": 7,  # float in range [0.0, 1.0] or int

        # max document frequency of a word to add to vocabulary
        # float - the parameter represents a proportion of documents
        # integer - absolute counts
        "max_df": 0.7,  # float in range [0.0, 1.0] or int

        # set range of ngrams to be extracted
        "min_ngram": 1,  # int
        "max_ngram": 1,  # int

        # limit vocabulary size
        "max_features": 5000,  # int or None

        # if convert all characters to lowercase
        "case_sensitive": True,  # bool
        "use_bigram_model": False,
        "embedding_file": None,
        "language": "en",
        "embedding_type": "fasttext"

    }

    def __init__(self, config):
        super().__init__(config)
        model=None
        if self.component_config["embedding_file"]:
            model=os.path.basename(self.component_config["embedding_file"])
            e=Embedding(name=model,
                      dimensions=100,
                      corpus_size='',
                      vocabulary_size='',
                      download_url='',
                      embedding_path=os.path.dirname(self.component_config["embedding_file"]),
                      format='gz',
                      architecture='CBOW',
                      trained_data='Wikipedia 2017',
                      language=self.component_config["language"])
            if self.component_config["embedding_type"]=="word2vec":
                word2vec.EMBEDDING_MODELS[os.path.basename(self.component_config["embedding_file"])]=e
            elif self.component_config["embedding_type"] == "fasttext":
                fastext.EMBEDDING_MODELS[os.path.basename(self.component_config["embedding_file"])] = e
            elif self.component_config["embedding_type"]=="gensim":
                gensim.EMBEDDING_MODELS[os.path.basename(self.component_config["embedding_file"])]=e

        self.embeddings=Embedder(embedding=self.component_config["embedding_type"], language=self.component_config["language"],model=model, download=True)
    def train(self, training_data, config, **kwargs):




        lem_exs = [self._get_document_text(example, not self.component_config["case_sensitive"])
                   for example in training_data.training_examples]

        self.tfidf = CountVectorizer(min_df=self.component_config["min_df"], max_df=self.component_config["max_df"], tokenizer=lambda x: x, lowercase=False)
        try:
            X = self.tfidf.fit_transform(lem_exs).toarray()
        except ValueError:
            self.vectorizer = None
            return

        self.vectorizer = Transform2WordVectors(self.embeddings, self.tfidf.vocabulary_)
        try:
            X = self.vectorizer.fit(X)
        except ValueError:
            self.vectorizer = None
            return

        for i, example in enumerate(training_data.training_examples):
            # create bag for each example
            example.text_features=self._combine_with_existing_features(example,
                                                                  X[i])


    def process(self, message, **kwargs):


        for token in message.tokens:
            token.vector=self.embeddings.encode(token.text)
        self._set_nlp_features(message)

    def _set_nlp_features(self, message):
        """Adds  word vectors to the messages text features."""
        fs=np.mean([t.vector for t in message.tokens], axis=0)

        features = self._combine_with_existing_features(message, fs)
        message.text_features= features
    @staticmethod
    def _get_document_text(document, lowercase):
        if document.nlp_doc and len(document.nlp_doc.tokens)>0:  # if lemmatize is possible
            if document.nlp_doc.tokens[0].lemma:
                tokens = [t for t in document.nlp_doc.tokens if not t.is_stopword and t.text not in punctuation]
                if lowercase:
                    return [t.lemma.lower() if t.abstract is None else t.abstract for t in tokens]
                return [t.lemma if t.abstract is not None else t.abstract for t in tokens]
            elif document.nlp_doc.tokens[0].stem:
                tokens = [t for t in document.nlp_doc.tokens if not t.is_stopword and t.text not in punctuation]
                if lowercase:
                    return [t.stem.lower() if t.abstract is None else t.abstract for t in tokens]
                return [t.stem if t.abstract is None else t.abstract for t in tokens]
        elif document.tokens:  # if directly tokens is provided
            tokens = [t for t in document.tokens if not t.is_stopword and t.text not in punctuation]
            if lowercase:
                return [t.text.lower() if t.abstract is None else t.abstract for t in tokens]
            return [t.text if t.abstract is None else t.abstract for t in tokens]
        else:
            return document.text

