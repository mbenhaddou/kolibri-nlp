import logging

import typing
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Text

from kolibri.pipeComponent import Component
from kolibri.config import ModelConfig
from kolibri.document import Document
from kolibri.data import TrainingData
from kolibri.nlp import Nlp

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from kolibri.model import Metadata


class StdNLP(Component):
    name = "nlp_std"

    provides = ["tokens", "std_nlp"]

    defaults = {
        # name of the language model to load - if it is not set
        # we will be looking for a language model that is named
        # after the language of the model, e.g. `en`
        "model": None,

        # when retrieving word vectors, this will decide if the casing
        # of the word is relevant. E.g. `hello` and `Hello` will
        # retrieve the same vector, if set to `False`. For some
        # applications and models it makes sense to differentiate
        # between these two words, therefore setting this to `True`.
        "case_sensitive": False,
    }

    def __init__(self, component_config=None, nlp=None):
        # type: (Dict[Text, Any], Language) -> None

        self.nlp = nlp
        super(StdNLP, self).__init__(component_config)

    @classmethod
    def required_packages(cls):
        # type: () -> List[Text]
        return []

    @classmethod
    def create(cls, cfg):
        # type: (ModelConfig) -> StdNLP

        component_conf = cfg.for_component(cls.name, cls.defaults)
        nlp_model_name = component_conf.get("language")
        component_conf["case_sensitive"] = cfg.get("case_sensitive")
        # if no model is specified, we fall back to the language string
        if not nlp_model_name:
            nlp_model_name = cfg.language
            component_conf["model"] = cfg.language

        logger.info("Trying to load nlp model with "
                    "name '{}'".format(nlp_model_name))

        nlp = Nlp(cfg.language)

        return StdNLP(component_conf, nlp)

    @classmethod
    def cache_key(cls, model_metadata):
        # type: (Metadata) -> Text

        component_meta = model_metadata.for_component(cls.name)

        # Fallback, use the language name, e.g. "en",
        # as the model name if no explicit name is defined
        nlp_model_name = component_meta.get("model", model_metadata.language)

        return cls.name + "-" + nlp_model_name

    def provide_context(self):
        # type: () -> Dict[Text, Any]

        return {"std_nlp": self.nlp}

    def doc_for_text(self, doc):
        return self.nlp(doc)


    def doc_for_sentence(self, sentence):
        if self.component_config.get("case_sensitive"):
            nlp_doc = self.nlp(sentence.text)
        else:
            nlp_doc = self.nlp(sentence.text.lower())
        for token in nlp_doc.tokens:
            token.start += sentence.start
            token.end += sentence.start
        return nlp_doc

    def train(self, training_data, config, **kwargs):
        # type: (TrainingData, ModelConfig, **Any) -> None

        for example in training_data.training_examples:
            self.process(example)

    def process(self, document, **kwargs):
        # type: (Document, **Any) -> None

        if 'sentences' in document:
            for sentence in document.sentences:
                sentence.nlp_doc = self.doc_for_sentence(sentence)
                sentence.tokens = sentence.nlp_doc.tokens
        else:
            document.nlp_doc = self.doc_for_text(document)
            document.tokens = document.nlp_doc.tokens

    @classmethod
    def load(cls,
             model_dir=None,
             model_metadata=None,
             cached_component=None,
             **kwargs):
        # type: (Text, Metadata, Optional[StdNLP], **Any) -> StdNLP

        if cached_component:
            return cached_component

        component_meta = model_metadata.for_component(cls.name)
        model_name = component_meta.get("model")

        nlp = Nlp('en')
        cls.ensure_proper_language_model(nlp)
        return cls(component_meta, nlp)

    @staticmethod
    def ensure_proper_language_model(nlp):
        # type: (Optional[Language]) -> None
        """Checks if the language model is properly loaded.

        Raises an exception if the model is invalid."""

        if nlp is None:
            raise Exception("Failed to load the language model. "
                            "Loading the model returned 'None'.")
