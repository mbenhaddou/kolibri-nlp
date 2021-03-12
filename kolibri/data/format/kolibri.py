import logging
from collections import defaultdict

from kolibri.data import  TrainingData
from kolibri.document import Document

from kolibri.utils import json_to_string
logger = logging.getLogger(__name__)
from kolibri.data.writer_reader import JsonTrainingDataReader, DataWriter

class KolibriReader(JsonTrainingDataReader):
    def read_from_json(self, js, **kwargs):
        """Loads training data stored in theNLU data format."""
        validate_nlu_data(js)

        data = js['kolibri_nlu_data']
        common_examples = data.get("common_examples", [])
        class_examples = data.get("class_examples", [])
        entity_examples = data.get("entity_examples", [])

        if class_examples or entity_examples:
            logger.warn("DEPRECATION warning: yourdata "
                        "contains 'class_examples' "
                        "or 'entity_examples' which will be "
                        "removed in the future. Consider "
                        "putting all your examples "
                        "into the 'common_examples' section.")

        all_examples = common_examples + class_examples + entity_examples
        training_examples = []
        classlabel="class"
        if 'target' in kwargs:
            classlabel=kwargs['target']
        for ex in all_examples:
            doc = Document.build(ex['text'], ex.get(classlabel),
                                ex.get("entities"))
            training_examples.append(doc)

        return training_examples


class KolibriWriter(DataWriter):
    def dumps(self, training_data, **kwargs):
        """Writes Training Data to a string in json format."""
        js_entity_synonyms = defaultdict(list)
        for k, v in training_data.entity_synonyms.items():
            if k != v:
                js_entity_synonyms[v].append(k)

        formatted_synonyms = [{'value': value, 'synonyms': syns}
                              for value, syns in js_entity_synonyms.items()]

        formatted_examples = [example.as_dict()
                              for example in training_data.training_examples]

        return json_to_string({
            "kolibri_data": {
                "common_examples": formatted_examples
            }
        }, **kwargs)


def validate_nlu_data(data):
    # type: (Dict[Text, Any]) -> None
    """Validatetraining data format to ensure proper training.

    Raises exception on failure."""
    from jsonschema import validate
    from jsonschema import ValidationError

    try:
        validate(data, _nlu_data_schema())
    except ValidationError as e:
        e.message += (". Failed to validate training data, make sure your data "
                      "is valid.")
        raise e


def _nlu_data_schema():
    training_example_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "minLength": 1},
            "class": {"type": "string"},
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "number"},
                        "end": {"type": "number"},
                        "value": {"type": "string"},
                        "entity": {"type": "string"}
                    },
                    "required": ["start", "end", "entity"]
                }
            }
        },
        "required": ["text"]
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
                    "class_examples": {
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
