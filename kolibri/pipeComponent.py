#import config, logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Hashable
from kolibri.config import ModelConfig, override_defaults
from .errors import *
import logging
logger = logging.getLogger(__name__)


def find_unavailable_packages(package_names):
    # type: (List[Text]) -> Set[Text]
    """Tries to import all the package names and returns
    the packages where it failed."""
    import importlib

    failed_imports = set()
    for package in package_names:
        try:
            importlib.import_module(package)
        except ImportError:
            failed_imports.add(package)
    return failed_imports


def validate_requirements(component_names):
    # type: (List[Text]) -> None
    """Ensures that all required python packages are installed to
    instantiate and used the passed components."""
    from kolibri import modules

    # Validate that all required packages are installed
    failed_imports = set()
    for component_name in component_names:
        component_class = modules.get_component_class(component_name)
        failed_imports.update(find_unavailable_packages(
                component_class.required_packages()))
    if failed_imports:  # pragma: no cover
        # if available, use the development file to figure out the correct
        # version numbers for each requirement
        raise Exception("Not all required packages are installed. " +
                        "To use this pipeline, you need to install the "
                        "missing dependencies. " +
                        "Please install {}".format(", ".join(failed_imports)))


def validate_arguments(pipeline, context, allow_empty_pipeline=False):
    # type: (List[Component], Dict[Text, Any], bool) -> None
    """Validates a pipeline before it is run. Ensures, that all
    arguments are present to train the pipeline."""

    # Ensure the pipeline is not empty
    if not allow_empty_pipeline and len(pipeline) == 0:
        raise ValueError("Can not train an empty pipeline. "
                         "Make sure to specify a proper pipeline in "
                         "the configuration using the `pipeline` key." +
                         "The `backend` configuration key is "
                         "NOT supported anymore.")

    provided_properties = set(context.keys())

    for component in pipeline:
        for r in component.requires:
            if r not in provided_properties:
                raise Exception("Failed to validate at component "
                                "'{}'. Missing property: '{}'"
                                "".format(component.name, r))
        provided_properties.update(component.provides)


class Component(object):
    """A component is a document processing unit in a pipeline.

    Components are collected sequentially in a pipeline. Each component
    is called one after another. This holds for
    initialization, training, persisting and loading the components.
    If a component comes first in a pipeline, its
    methods will be called first.
"""

    # Name of the component to be used when integrating it in a
    # pipeline. E.g. ``[ComponentA, ComponentB]``
    # will be a proper pipeline definition where ``ComponentA``
    # is the name of the first component of the pipeline.
    name = ""

    # Defines what attributes the pipeline component will
    # provide when called. The listed attributes
    # should be set by the component on the document object
    # during test and train, e.g.
    # ```document.set("entities", [...])```
    provides = []

    # Which attributes on a document are required by this
    # component. e.g. if requires contains "tokens", than a
    # previous component in the pipeline needs to have "tokens"
    # within the above described `provides` property.
    requires = []

    # Defines the default configuration parameters of a component
    # these values can be overwritten in the pipeline configuration
    # of the model. The component should choose sensible defaults
    # and should be able to create reasonable results with the defaults.
    defaults = {}

    # Defines what language(s) this component can handle.
    # This attribute is designed for instance method: `can_handle_language`.
    # Default text is None which means it can handle all languages.
    # This is an important feature for backwards compatibility of components.
    language_list = None

    def __init__(self, component_config=None):
        if not component_config:
            component_config = {}

        # makes sure the name of the configuration is part of the config
        # this is important for e.g. persistence
        component_config["name"] = self.name

        self.component_config = override_defaults(
                self.defaults, component_config)
        self.pos_features=False
        self.partial_processing_pipeline = None
        self.partial_processing_context = None

    @classmethod
    def required_packages(cls):
        # type: () -> List[Text]
        """Specify which python packages need to be installed to use this
        component, e.g. ``["spacy"]``.

        This list of requirements allows us to fail early during training
        if a required package is not installed."""
        return []

    @classmethod
    def load(cls,
             model_dir=None,   # type: Optional[Text]
             model_metadata=None,   # type: Optional[Metadata]
             cached_component=None,   # type: Optional[Component]
             **kwargs  # type: Any
             ):
        # type: (...) -> Component
        """Load this component from file.

        After a component has been trained, it will be persisted by
        calling `persist`. When the pipeline gets loaded again,
        this component needs to be able to restore itself.
        Components can rely on any context attributes that are
        created by :meth:`components.Component.pipeline_init`
        calls to components previous
        to this one."""
        if cached_component:
            return cached_component
        else:
            component_config = model_metadata.for_component(cls.name)
            return cls(component_config)

    @classmethod
    def create(cls, cfg):
        # type: (ModelConfig) -> Component
        """Creates this component (e.g. before a training is started).

        Method can access all configuration parameters."""

        # Check language supporting
        language = cfg.language
        if not cls.can_handle_language(language):
            # check failed
            raise UnsupportedLanguageError(cls.name, language)

        return cls(cfg)

    def provide_context(self):
        """Initialize this component for a new pipeline

        This function will be called before the training
        is started and before the first document is processed using
        the interpreter. The component gets the opportunity to
        add information to the context that is passed through
        the pipeline during training and document parsing. Most
        components do not need to implement this method.
        It's mostly used to initialize framework environments
        like MITIE and spacy
        (e.g. loading word vectors for the pipeline)."""
        pass

    def train(self, training_data, cfg, **kwargs):
        """Train this component.

        This is the components chance to train itself provided
        with the training data. The component can rely on
        any context attribute to be present, that gets created
        by a call to :meth:`components.Component.pipeline_init`
        of ANY component and
        on any context attributes created by a call to
        :meth:`components.Component.train`
        of components previous to this one."""
        pass

    def process(self, document, **kwargs):
        """Process an incoming document.

        This is the components chance to process an incoming
        document. The component can rely on
        any context attribute to be present, that gets created
        by a call to :meth:`components.Component.pipeline_init`
        of ANY component and
        on any context attributes created by a call to
        :meth:`components.Component.process`
        of components previous to this one."""
        pass

    def persist(self, model_dir):
        """Persist this component to disk for future loading."""

        pass

    @classmethod
    def cache_key(cls, model_metadata):
        """This key is used to cache components.

        If a component is unique to a model it should return None.
        Otherwise, an instantiation of the
        component will be reused for all models where the
        metadata creates the same key."""

        return None

    def __getstate__(self):
        d = self.__dict__.copy()
        # these properties should not be pickled
        if "partial_processing_context" in d:
            del d["partial_processing_context"]
        if "partial_processing_pipeline" in d:
            del d["partial_processing_pipeline"]
        return d

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def _check_nlp_doc(self, message):
        if "sentences" in message:
            if self.pos_features and message.sentences[0].get("nlp_doc") is None:
                raise InvalidConfigError(
                    'Could not find `nlp_doc` attribute for '
                    'message {}\n'
                    'POS features require a pipeline component '
                    'that provides `nlp_doc` attributes, i.e. `nlp_doc`.'.format(message.text))
        elif self.pos_features and message.get("nlp_doc") is None:
            raise InvalidConfigError(
                'Could not find `nlp_doc` attribute for '
                'message {}\n'
                
                'POS features require a pipeline component '
                'that provides `nlp_doc` attributes, i.e. `nlp_doc`.'.format(message.text))

    def prepare_partial_processing(self, pipeline, context):
        """Sets the pipeline and context used for partial processing.

        The pipeline should be a list of components that are
        previous to this one in the pipeline and
        have already finished their training (and can therefore
        be safely used to process documents)."""

        self.partial_processing_pipeline = pipeline
        self.partial_processing_context = context

    def partially_process(self, document):
        """Allows the component to process documents during
        training (e.g. external training data).

        The passed document will be processed by all components
        previous to this one in the pipeline."""

        if self.partial_processing_context is not None:
            for component in self.partial_processing_pipeline:
                component.process(document, **self.partial_processing_context)
        else:
            logger.info("Failed to run partial processing due "
                        "to missing pipeline.")
        return document

    @classmethod
    def can_handle_language(cls, language):
        # type: (Hashable) -> bool
        """Check if component supports a specific language.

        This method can be overwritten when needed. (e.g. dynamically
        determine which language is supported.)"""

        # if language_list is set to `None` it means: support all languages
        if language is None or cls.language_list is None:
            return True

        return language in cls.language_list


class ComponentBuilder(object):
    """Creates trainers and interpreters based on configurations.

    Caches components for reuse."""

    def __init__(self, use_cache=True):
        self.use_cache = use_cache
        # Reuse nlp and featurizers where possible to save memory,
        # every component that implements a cache-key will be cached
        self.component_cache = {}

    def __get_cached_component(self, component_name, model_metadata):
        # type: (Text, Metadata) -> Tuple[Optional[Component], Optional[Text]]
        """Load a component from the cache, if it exists.

        Returns the component, if found, and the cache key."""
        from kolibri import modules
        from kolibri.model import Metadata

        component_class = modules.get_component_class(component_name)
        cache_key = component_class.cache_key(model_metadata)
        if (cache_key is not None
                and self.use_cache
                and cache_key in self.component_cache):
            return self.component_cache[cache_key], cache_key
        else:
            return None, cache_key

    def __add_to_cache(self, component, cache_key):
        # type: (Component, Text) -> None
        """Add a component to the cache."""

        if cache_key is not None and self.use_cache:
            self.component_cache[cache_key] = component
            logger.info("Added '{}' to component cache. Key '{}'."
                        "".format(component.name, cache_key))

    def load_component(self,
                       component_name,
                       model_dir,
                       model_metadata,
                       **context):
        # type: (Text, Text, Metadata, **Any) -> Component
        """Tries to retrieve a component from the cache, else calls
        ``load`` to create a new component.

        Args:
            component_name (str): the name of the component to load
            model_dir (str): the directory to read the model from
            model_metadata (Metadata): the model's
            :class:`models.Metadata`

        Returns:
            Component: the loaded component.
        """
        from kolibri import modules
        from kolibri.model import Metadata

        try:
            cached_component, cache_key = self.__get_cached_component(
                    component_name, model_metadata)
            component = modules.load_component_by_name(
                    component_name, model_dir, model_metadata,
                    cached_component, **context)
            if not cached_component:
                # If the component wasn't in the cache,
                # let us add it if possible
                self.__add_to_cache(component, cache_key)
            return component
        except MissingArgumentError as e:  # pragma: no cover
            raise Exception("Failed to load component '{}'. "
                            "{}".format(component_name, e))

    def create_component(self, component_name, cfg):
        # type: (Text, ModelConfig) -> Component
        """Tries to retrieve a component from the cache,
        calls `create` to create a new component."""
        from kolibri import modules
        from kolibri.model import Metadata

        try:
            component, cache_key = self.__get_cached_component(
                    component_name, Metadata(cfg.as_dict(), None))
            if component is None:
                component = modules.create_component_by_name(component_name,
                                                              cfg)
                self.__add_to_cache(component, cache_key)
            return component
        except MissingArgumentError as e:  # pragma: no cover
            raise Exception("Failed to create component '{}'. "
                            "{}".format(component_name, e))
