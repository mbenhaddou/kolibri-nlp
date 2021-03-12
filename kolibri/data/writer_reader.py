import logging, json
from collections import defaultdict

from kolibri.data.training_data import TrainingData
from kolibri.document import Document
from kolibri.utils.file import read_file
from kolibri.utils import json_to_string

logger = logging.getLogger(__name__)


class DataReader():
    def read_from_json(self, js, **kwargs):
        """Loads training data stored in the kolibri nlu data format."""
        validate_nlu_data(js)

        data = js['kolibri_nlu_data']
        common_examples = data.get("common_examples", [])
        intent_examples = data.get("intent_examples", [])
        entity_examples = data.get("entity_examples", [])



        if intent_examples or entity_examples:
            logger.warn("DEPRECATION warning: your data "
                        "contains 'intent_examples' "
                        "or 'entity_examples' which will be "
                        "removed in the future. Consider "
                        "putting all your examples "
                        "into the 'common_examples' section.")

        all_examples = common_examples + intent_examples + entity_examples
        training_examples = []
        for ex in all_examples:
            msg = Document.build(ex['text'], ex.get("target"),
                                ex.get("entities"))
            training_examples.append(msg)

        return TrainingData(training_examples)


class DataWriter():
    def dumps(self, training_data, **kwargs):
        """Writes Training Data to a string in json format."""

        formatted_examples = [example.as_dict()
                              for example in training_data.training_examples]

        return json_to_string({
            "kolibri_nlu_data": {
                "common_examples": formatted_examples,
            }
        }, **kwargs)




class JsonTrainingDataReader(DataReader):
    def reads(self, s, **kwargs):
        """Transforms string into json object and passes it on."""
        js = json.loads(read_file(s))
        return self.read_from_json(js, **kwargs)

    def read_from_json(self, js, **kwargs):
        """Reads TrainingData from a json object."""
        raise NotImplementedError

def validate_nlu_data(data):
    # type: (Dict[Text, Any]) -> None
    """Validatetraining data format to ensure proper training.

    Raises exception on failure."""
    from jsonschema import validate
    from jsonschema import ValidationError

    try:
        validate(data, _kolibri_data_schema())
    except ValidationError as e:
        e.message += (". Failed to validate training data, make sure your data ")
        raise e


def _kolibri_data_schema():
    training_example_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "minLength": 1},
            "target": {"type": "string"},
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "number"},
                        "end": {"type": "number"},
                        "text": {"type": "string"},
                        "entity": {"type": "string"}
                    },
                    "required": ["start", "end", "entity"]
                }
            }
        },
        "required": ["text"]
    }

    regex_feature_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "patterns": {"type": "string"},
        }
    }

    lookup_table_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "elements": {
                "oneOf": [
                    {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    {"type": "string"}
                ]
            }
        }
    }

    return {
        "type": "object",
        "properties": {
            "kolibri_nlu_data": {
                "type": "object",
                "properties": {
                    "common_examples": {
                        "type": "array",
                        "items": training_example_schema
                    },
                    "intent_examples": {
                        "type": "array",
                        "items": training_example_schema
                    },
                    "entity_examples": {
                        "type": "array",
                        "items": training_example_schema
                    },

                }
            }
        },
        "additionalProperties": False
    }
