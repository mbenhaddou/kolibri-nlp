import typing
from typing import Any, List

from kolibri.pipeComponent import Component
from kolibri.config import ModelConfig
from kolibri.tokenizer import Tokenizer, Token
from kolibri.document import Document
from kolibri.data import TrainingData


class NlpTokenizer(Tokenizer, Component):
    name = "tokenizer_nlp"

    provides = ["tokens"]

    requires = ["nlp_doc"]

    def train(self, training_data, config, **kwargs):
        # type: (TrainingData, ModelConfig, **Any) -> None

        for example in training_data.training_examples:
            example.tokens= self.tokenize(example.nlp_doc)

    def process(self, document, **kwargs):
        # type: (Document, **Any) -> None

        document.tokens=self.tokenize(document.nlp_doc)

    def tokenize(self, doc):
        # type: (Document) -> List[Token]

        return doc.tokens
