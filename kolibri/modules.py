"""This is a somewhat delicate package. It contains all registered components
and preconfigured templates.

Hence, it imports all of the components. To avoid cycles, no component should
import this in module scope."""

from typing import Any
from typing import Optional
from typing import Text
from typing import Type
#import utils
#from .config import ModelConfig
from .pipeComponent import Component
from kolibri.tokenizer import WordTokenizer
from kolibri.features import TFIDFFeaturizer
from kolibri.features.embedding_featurizer import EmbeddingsFeaturizer
from kolibri.features.supervised_featurizer import CBTWFeaturizer
from kolibri.classifier.sklearn_classifier import SkLearnClassifier
from kolibri.data.cleaner.email_ import EmailCleaner
from kolibri.entities.crf_entity_extractor import CRFEntityExtractor
from kolibri.entities.lstm_entity_extractor import LSTMEntityExtractor
from kolibri.entities.entity_synonyms import EntitySynonymMapper
from kolibri.tokenizer.sentence_tokenizer import SentenceTokenizer
from kolibri.tokenizer.structured_tokenizer import StructuredTokenizer
from kolibri.features.svd_featurizer import TDIDFSVDFeaturizer
from kolibri.tools.std_nlp import StdNLP
from kolibri.embeddings.w2v import CustomWord2Vec
from kolibri.tokenizer.nlp_tokenizer import NlpTokenizer
from kolibri.cluster.topics_lda import LdaMallet
from kolibri.classifier.ecoc.ecoc_classifier import ECOC
# Classes of all known components. If a new component should be added,
# its class name should be listed here.
component_classes = [
EmailCleaner, WordTokenizer, TFIDFFeaturizer, SkLearnClassifier,
StdNLP, NlpTokenizer, EmbeddingsFeaturizer,CRFEntityExtractor,EntitySynonymMapper, SentenceTokenizer, LSTMEntityExtractor,
LdaMallet, StructuredTokenizer, ECOC, CBTWFeaturizer, CustomWord2Vec, TDIDFSVDFeaturizer
#    TFIDFFeaturizer, SkLearnClassifier, , NlpFeaturizer,,, StdNLP, NlpTokenizer
]

# Mapping from a components name to its class to allow name based lookup.
registered_components = {c.name: c for c in component_classes}


def class_from_module_path(module_path):
    """Given the module name and path of a class, tries to retrieve the class.

    The loaded class can be used to instantiate new objects. """
    import importlib

    # load the module, will raise ImportError if module cannot be loaded
    if "." in module_path:
        module_name, _, class_name = module_path.rpartition('.')

        m = importlib.import_module(module_name)
        # get the class, will raise AttributeError if class cannot be found
        return getattr(m, class_name)
    else:
        return globals()[module_path]


def get_component_class(component_name):
    # type: (Text) -> Optional[Type[Component]]
    """Resolve component name to a registered components class."""
    if component_name not in registered_components:
        try:
            return class_from_module_path(component_name)
        except Exception:
            raise Exception(
                    "Failed to find component class for '{}'. Unknown "
                    "component name. Check your configured pipeline and make "
                    "sure the mentioned component is not misspelled. If you "
                    "are creating your own component, make sure it is either "
                    "listed as part of the `component_classes` in "
                    "`kolibti.modulesy.py` or is a proper name of a class "
                    "in a module.".format(component_name))
    return registered_components[component_name]


def load_component_by_name(component_name,  # type: Text
                           model_dir,  # type: Text
                           metadata,  # type: Metadata
                           cached_component,  # type: Optional[Component]
                           **kwargs  # type: Any
                           ):
    # type: (...) -> Optional[Component]
    """Resolves a component and calls its load method to init it based on a
    previously persisted model."""

    component_clz = get_component_class(component_name)
    return component_clz.load(model_dir, metadata, cached_component, **kwargs)


def create_component_by_name(component_name, config):
    # type: (Text, ModelConfig) -> Optional[Component]
    """Resolves a component and calls it's create method to init it based on a
    previously persisted model."""

    component_clz = get_component_class(component_name)
    return component_clz.create(config)


def module_path_from_instance(inst):
    # type: (Any) -> Text
    """Return the module path of an instances class."""
    return inst.__module__ + "." + inst.__class__.__name__

def all_subclasses(cls):
    # type: (Any) -> List[Any]
    """Returns all known (imported) subclasses of a class."""

    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]


def add_component(Component):
    component_classes.append(Component)
    global registered_components
    registered_components = {c.name: c for c in component_classes}
