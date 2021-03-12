from typing import Any, List, Text

from kolibri.pipeComponent import Component
from kolibri.config import ModelConfig
from kolibri.tokenizer.tokenizer import Tokenizer
from kolibri.document import Document
from kolibri.tokenizer import RegexpTokenizer
from kolibri.tokenizer.token_ import Token, Tokens

pattern =u'(?ui)\\b\\w*[a-z]+\\w*\\b'


class WordTokenizer(Tokenizer, Component):
    name = "tokenizer_word"

    provides = ["tokens"]
    def __init__(self, config):
        self.tknzr = RegexpTokenizer(pattern, config=config)
        super(WordTokenizer, self).__init__(config=config)
#        self.component_config = config.for_component(self.name, self.defaults)




    def train(self, training_data, config, **kwargs):

        for example in training_data.training_examples:
            self.process(example)

    def process(self, document, **kwargs):
        if 'sentences' in document:
            for sent in document.sentences:
                self.process(sent)
        else:
            document.tokens= self.tokenize(document.text)

    def tokenize(self, text):


        return self.tknzr.tokenize(text)


