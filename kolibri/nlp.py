from kolibri.tokenizer import StructuredTokenizer
from kolibri.lemmatizer.fr.french_lefff_lemmatizer import FrenchLefffLemmatizer
from kolibri.lemmatizer.en.formlemmatizer import FormWordNetLematizer
from kolibri import Sent, Doc
from kolibri.pos_tagger.pos_tagger import pos_tag
from kolibri.features.word2vec.word2vec import get_embedding
from kolibri.tokenizer.sentence_tokenizer import split_single
from kolibri.stemmer import WordStemer
import logging


class Nlp:
    DEFAULT_PROPERTIES = {}
    DEFAULT_OUTPUT_FORMAT = "serialized"
    DEFAULT_ANNOTATORS = "tokenize ssplit lemma pos ner depparse".split()

    def __init__(self, language='en', logging_level=logging.WARNING):
        self.logging_level = logging_level
        self.default_properties = self.DEFAULT_PROPERTIES
        self.default_properties["language"]=language
        self.default_output_format = self.DEFAULT_OUTPUT_FORMAT
        self.tokenizer = StructuredTokenizer(self.default_properties)
        self.stemmer=WordStemer(language)
        self.lemmatizer=None
        if language=='fr':
            self.lemmatizer=FrenchLefffLemmatizer()
        if language=='en':
            self.lemmatizer=FormWordNetLematizer()

        self.language=language
        logging.basicConfig(level=self.logging_level)

    def __enter__(self):
        return self


    def _process_sentence(self, document):
        doc = Sent()

        doc.tokens=self.tokenizer.tokenize(document)
        doc = pos_tag(doc, self.language)
        if self.lemmatizer:
            doc = self.lemmatizer.lemmatize(doc)
        doc=self.stemmer.stemDoc(doc)
        doc.vector = get_embedding(document)

        return doc
    def __call__(self, text, split_sentences=False):
        doc=Doc()
        if split_sentences:
            sents=split_single(text)
            for sent in sents:
                sentence=self._process_sentence(sent[0])
                sentence.start=sent[1]
                sentence.end=sent[2]
                doc.sentences.append(sentence)
        else:
            doc = self._process_sentence(text)

        return doc
