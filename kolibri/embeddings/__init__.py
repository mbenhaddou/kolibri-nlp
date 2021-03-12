from typing import NamedTuple


MODELS_DIR = '.embeddings'


class Embedding(NamedTuple):
    name: str
    dimensions: int
    corpus_size: str
    vocabulary_size: str
    download_url: str
    embedding_path: str
    format: str
    architecture: str
    trained_data: str
    language: str