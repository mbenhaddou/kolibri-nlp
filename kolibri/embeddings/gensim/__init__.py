from typing import List, Dict, Any, Optional, Union

from kolibri.embeddings import Embedding
from kolibri.utils import POOL_FUNC_MAP
import gensim
from smart_open import open
from tqdm import tqdm
import os
import numpy as np
from numpy import dtype, float32 as real, fromstring


class Embeddings(object):

    EMBEDDING_MODELS: List[Embedding] = []

    EMBEDDING_MODELS: Dict[str, Embedding] = {embedding.name: embedding for embedding in EMBEDDING_MODELS}

    def __init__(self):
        self.word_vectors=None
        self.model_name = None

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        return [x.lower().strip() for x in text.split()]

    def load_model(self, model: str, model_path: str):
        try:

            if os.path.isfile(os.path.join(model_path,model)):
                model_file=os.path.join(model_path,model)
            else:
                model_file = [f for f in os.listdir(model_path) if os.path.isfile(os.path.join(model_path, f))]
            self.word_vectors = gensim.models.FastText.load(model_file)
            print("Model loaded Successfully !")
            return self
        except Exception as e:
            print('Error loading Model, ', str(e))


    def encode(self, texts,
               pooling: str,
               max_seq_length: int,
               is_tokenized: bool = False,
               **kwargs
               ) -> Optional[np.array]:
        dim=self.word_vectors.wv.vector_size
        return  self.word_vectors[texts]

