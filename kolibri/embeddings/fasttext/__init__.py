from itertools import islice
from typing import List, Dict, Any, Optional, Union
import numpy as np
from tqdm import tqdm
import os
import cProfile

from kolibri.embeddings import Embedding
from kolibri.utils import POOL_FUNC_MAP


class Embeddings(object):

    EMBEDDING_MODELS: List[Embedding] = [
        Embedding(name=u'wiki_news_300',
                  dimensions=300,
                  corpus_size='16B',
                  vocabulary_size='1M',
                  download_url='https://dl.fbaipublicfiles.com/fasttext/vectors-english/'
                               'wiki-news-300d-1M.vec.zip',
                  embedding_path='',
                  format='zip',
                  architecture='CBOW',
                  trained_data='Wikipedia 2017',
                  language='en'),

        Embedding(name=u'wiki_news_300_sub',
                  dimensions=300,
                  corpus_size='16B',
                  vocabulary_size='1M',
                  download_url='https://dl.fbaipublicfiles.com/fasttext/vectors-english/'
                               'wiki-news-300d-1M-subword.vec.zip',
                  embedding_path='',
                  format='zip',
                  architecture='CBOW',
                  trained_data='Wikipedia 2017',
                  language='en'),

        Embedding(name=u'common_crawl_300',
                  dimensions=300,
                  corpus_size='600B',
                  vocabulary_size='2M',
                  download_url='https://dl.fbaipublicfiles.com/fasttext/vectors-english/'
                               'crawl-300d-2M.vec.zip',
                  embedding_path='',
                  format='zip',
                  architecture='CBOW',
                  trained_data='Common Crawl (600B tokens)',
                  language='en'),

        Embedding(name=u'common_crawl_300_sub',
                  dimensions=300,
                  corpus_size='600B',
                  vocabulary_size='2M',
                  download_url='https://dl.fbaipublicfiles.com/fasttext/vectors-english/'
                               'crawl-300d-2M-subword.zip',
                  embedding_path='',
                  format='zip',
                  architecture='CBOW',
                  trained_data='Common Crawl (600B tokens)',
                  language='en'),

    ]

    EMBEDDING_MODELS: Dict[str, Embedding] = {embedding.name: embedding for embedding in EMBEDDING_MODELS}

    def __init__(self):
        self.word_vectors: Dict[Any, Any] = {}
        self.model_name = None

    @classmethod
    def tokenize(cls, text):
        return [x.lower().strip() for x in text.split()]

    def load_model(self, model: str, model_path: str):
        try:
            model_file = [f for f in os.listdir(model_path) if os.path.isfile(os.path.join(model_path, f))]

            with open(os.path.join(model_path, model_file[0]), 'r') as f:
                    for line in tqdm(f):
                        split_line = line.split()
                        word = split_line[0]
                        self.word_vectors[word] = split_line[1:]
            print("Model loaded Successfully !")
            self.model_name = model
            return self
        except Exception as e:
            print('Error loading Model, ', str(e))
        return self


    def _single_encode_text(self, text: Union[str, List[str]], oov_vector: np.array, max_seq_length: int,
                            is_tokenized: bool):

        tokens = text
        if not is_tokenized:
            tokens = Embeddings.tokenize(text)
        if len(tokens) > max_seq_length:
            tokens = tokens[0: max_seq_length]
        embeddings=[]
        for token in tokens:
            embeddings.append(np.array(self.word_vectors.get(token, oov_vector)))

        return np.array(embeddings)

    def encode(self, texts: Union[List[str], List[List[str]]],
               pooling: str,
               max_seq_length: int,
               is_tokenized: bool = False,
               **kwargs
               ) -> Optional[np.array]:
        oov_vector = np.zeros(Embeddings.EMBEDDING_MODELS[self.model_name].dimensions, dtype="float32")

        return np.array(self.word_vectors.get(texts, oov_vector))