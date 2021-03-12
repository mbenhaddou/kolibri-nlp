import copy
import logging
import os
from . import settings
from kolibri.errors import InvalidConfigError
from yaml import parser
# Describes where to search for the config file if no location is specified
from typing import Text, Optional, Dict, Any, List
from kolibri.utils import json_to_string
from kolibri.utils.file import read_yaml_file


logger = logging.getLogger(__name__)


DEFAULT_CONFIG_LOCATION= "config.yml",
DEFAULT_CONFIG= {
    "language": "en",
    "pipeline": [],
    "data": None
}

class ModelConfig(object):
    DEFAULT_PROJECT_NAME = "default"

    def __init__(self, configuration_values=None):
        """Create a model configuration, optionally overridding
        defaults with a dictionary ``configuration_values``.
        """
        if not configuration_values:
            configuration_values = {}

        self.override(DEFAULT_CONFIG)
        self.override(configuration_values)

        if isinstance(self.__dict__['pipeline'], list):

            self.pipeline = [{"name": c} for c in self.__dict__['pipeline']]

            if self.pipeline:
                # replaces the template with the actual components
                self.__dict__['pipeline'] = self.pipeline

        for key, value in self.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        return self.__dict__[key]

    def load(self, filename=None, **kwargs):

        if filename is None and os.path.isfile(DEFAULT_CONFIG_LOCATION):
            filename = DEFAULT_CONFIG_LOCATION

        if filename is not None:
            try:
                file_config = read_yaml_file(filename)
            except parser.ParserError as e:
                raise InvalidConfigError("Failed to read configuration file "
                                         "'{}'. Error: {}".format(filename, e))

            if kwargs:
                file_config.update(kwargs)
            self.override(file_config)
        else:
            self.override(kwargs)
    @staticmethod
    def component_config_from_pipeline(
            name,  # type: Text
            pipeline,  # type: List[Dict[Text, Any]]
            defaults=None  # type: Optional[Dict[Text, Any]]
    ):
        # type: (...) -> Dict[Text, Any]
        for c in pipeline:
            if c.get("name") == name:
                return ModelConfig.override_defaults(defaults, c)
        else:
            return ModelConfig.override_defaults(defaults, {})

    @staticmethod
    def override_defaults(
            defaults,  # type: Optional[Dict[Text, Any]]
            custom  # type: Optional[Dict[Text, Any]]
    ):
        # type: (...) -> Dict[Text, Any]
        if defaults:
            cfg = copy.deepcopy(defaults)
        else:
            cfg = {}

        if custom:
            cfg.update(custom)
        return cfg

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __delitem__(self, key):
        del self.__dict__[key]

    def __contains__(self, key):
        return key in self.__dict__

    def __len__(self):
        return len(self.__dict__)

    def __getstate__(self):
        return self.as_dict()

    def __setstate__(self, state):
        self.override(state)

    def items(self):
        return list(self.__dict__.items())

    def as_dict(self):
        return dict(list(self.items()))

    def view(self):
        return json_to_string(self.__dict__, indent=4)

    def for_component(self, name, defaults=None):
        return self.component_config_from_pipeline(name, pipeline=self.pipeline, defaults=defaults)

    @property
    def component_names(self):
        if self.pipeline:
            return [c.get("name") for c in self.pipeline]
        else:
            return []

    def set_component_attr(self, name, **kwargs):
        for c in self.pipeline:
            if c.get("name") == name:
                c.update(kwargs)
        else:
            logger.warn("Tried to set configuration text for component '{}' "
                        "which is not part of the pipeline.".format(name))

    def override(self, config):
        if config:
            self.__dict__.update(config)
