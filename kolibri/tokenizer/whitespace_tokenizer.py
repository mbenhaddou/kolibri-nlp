import re
from typing import Any, List, Text

from kolibri.pipeComponent import Component
from kolibri.config import ModelConfig
from kolibri.tokenizer import Tokenizer, Token
from kolibri.document import Document


class WhitespaceTokenizer(Tokenizer, Component):
    name = "tokenizer_whitespace"

    provides = ["tokens"]

    def train(self, training_data, config, **kwargs):
        # type: (TrainingData, ModelConfig, **Any) -> None

        for example in training_data.training_examples:
            example.set("tokens", self.tokenize(example.text))

    def process(self, document, **kwargs):
        # type: (Document, **Any) -> None

        document.set("tokens", self.tokenize(document.text))

    def tokenize(self, text):
        # type: (Text) -> List[Token]

        # there is space or end of string after punctuation
        # because we do not want to replace 10.000 with 10 000
        words = re.sub(r'[.,!?]+(\s|$)', ' ', text).split()

        running_offset = 0
        tokens = []
        for i, word in enumerate(words):
            word_offset = text.index(word, running_offset)
            word_len = len(word)
            running_offset = word_offset + word_len
            tokens.append(Token(text=word, start=word_offset, index=i))
        return tokens
