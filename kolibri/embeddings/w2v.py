import os
import joblib
import logging
import multiprocessing
from kolibri.pipeComponent import Component


import gensim

W2V_MODEL_FILE_NAME= "word2vec.pkl"
W2V_VECTOR_FILE_NAME= "word2vec.embeddings.{}.model"

class CustomWord2Vec(Component):

    name = "word2vec"

    provides = ["vector"]

    requires = ["sentences", "tokens"]

    defaults = {
        "dim": 100,
        "win": 10,
        "start_alpha": 0.05,
        "neg": 10,
        "min_count": 5
    }

    def __init__(self, configs):

        super().__init__(configs)

    # Get number of available cpus
        self.cores = multiprocessing.cpu_count()
        self.model=None
        self.dim=self.component_config["dim"]
        self.win=self.component_config["win"]
        self.start_alpha=self.component_config["start_alpha"]
        self.neg = self.component_config["neg"]
        self.min_count = self.component_config["min_count"]

    def train(self, training_data, cfg, **kwargs):

        # Initialize simple sentence iterator required for the Word2Vec model
        sentences = SentencesIterator(training_data)

        logging.info('Training word2vec model..')
        self.model = gensim.models.FastText(sentences=sentences, size=self.dim, min_count=self.min_count, window=self.win, workers=self.cores, negative=self.neg)
        self.model.init_sims(replace=True)
    def process(self, document, **kwargs):
        for sentence in document.sentences:
            for token in sentence.tokens:

                token.vector=self.model.wv[token.text]

    @classmethod
    def load(cls,
             model_dir=None,
             model_metadata=None,
             cached_component=None,
             **kwargs
             ):

        meta = model_metadata.for_component(cls.name)
        embeddings = meta.get("embedding_file", W2V_VECTOR_FILE_NAME)
        model_ = meta.get("word2vec_file", W2V_MODEL_FILE_NAME)

        embeddings_file = os.path.join(model_dir, embeddings)
        model_file = os.path.join(model_dir, model_)
        w2v=None
        if os.path.exists(embeddings_file):
            w2v = gensim.models.FastText.load(embeddings_file)
            w2v.init_sims(replace=True)
        if os.path.exists(model_file):
            model = joblib.load(model_file)
            model.model=w2v
            return model
        else:
            return cls(meta)


    def persist(self, model_dir):
        """Persist this model into the passed directory."""

        w2v_file = os.path.join(model_dir, W2V_VECTOR_FILE_NAME.format(self.dim))
        model_file = os.path.join(model_dir, W2V_MODEL_FILE_NAME)
        self.model.save(w2v_file)
        joblib.dump(self, model_file)

        return {"word2vec_file": W2V_MODEL_FILE_NAME, "embedding_file":W2V_VECTOR_FILE_NAME.format(self.dim)}


class SentencesIterator:
    def __init__(self, corpus):
        self.corpus = corpus

    def __iter__(self):
        for doc in self.corpus.training_examples:
            for sentence in doc.sentences:
                yield [t.text for t in sentence.tokens]