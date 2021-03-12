from typing import Any, List, Text

from kolibri.pipeComponent import Component
from kolibri.config import ModelConfig
from kolibri.tokenizer import Tokenizer, Token
from kolibri.document import Document
from kolibri.tokenizer.sentence_splitter import split_single



class SentenceTokenizer(Tokenizer, Component):
    name = "tokenizer_sentence"

    provides = ["sentences"]

    def train(self, training_data, config, **kwargs):
        # type: (TrainingData, ModelConfig, **Any) -> None

        for example in training_data.training_examples:
            self.process(example)

    def process(self, document, **kwargs):
        # type: (Document, **Any) -> None
        if "clean" in document:
            text=document["clean"]
        else:
            text=document.text
        document["sentences"]= self.tokenize(text)

    def tokenize(self, text):
        # type: (Text) -> List[Token]


        sentences= split_single(text)

        sentences_ = []
        for sent in sentences:
            if len(sent[0].strip())>0:
                sentence = Document()
                sentence.raw_text=sent[0]
                sentence.start=sent[1]
                sentence.end=sent[2]

                sentences_.append(sentence)
        return sentences_
