import re
import logging, json

from kolibri.data import TrainingData
from kolibri.document import Document
from kolibri.utils import build_entity

CLASS = "class"
SYNONYM = "synonym"
REGEX = "regex"
LOOKUP = "lookup"
available_sections = [CLASS, SYNONYM, REGEX, LOOKUP]
ent_regex = re.compile(r'\[(?P<entity_text>[^\]]+)'
                       r'\]\((?P<entity>[^:)]*?)'
                       r'(?:\:(?P<value>[^)]+))?\)')  # [entity_text](entity_type(:entity_synonym)?)

item_regex = re.compile(r'\s*[-\*+]\s*(.+)')
comment_regex = re.compile(r'<!--[\s\S]*?--!*>', re.MULTILINE)
fname_regex = re.compile(r'\s*([^-\*+]+)')

logger = logging.getLogger(__name__)


class JsonReader():
    """Reads markdown training data and creates a TrainingData object."""

    def __init__(self):
        self.current_title = None
        self.current_section = None
        self.training_examples = []

    def reads(self, s, **kwargs):
        """Read markdown string and create TrainingData object"""
        self.__init__()
        data=json.loads(open(s).read())
 #       texts, labels = csv_data_reader(s, kwargs["col_sep"], kwargs["has_column_names"], kwargs["content_column"], kwargs["label_column"])
        class_id=kwargs['target']

        for d in data:
            self._parse_item(d)


        return TrainingData(self.training_examples)

    @staticmethod
    def _strip_comments(text):
        """ Removes comments defined by `comment_regex` from `text`. """
        return re.sub(comment_regex, '', text)

    @staticmethod
    def _create_section_regexes(section_names):
        def make_regex(section_name):
            return re.compile(r'##\s*{}:(.+)'.format(section_name))

        return {sn: make_regex(sn) for sn in section_names}

    def _parse_item(self, line):
        """Parses an md list item line based on the current section type."""
        self.training_examples.append(line)

    def _find_entities_in_training_example(self, example):
        """Extracts entities from a markdown intent example."""
        entities = []
        offset = 0
        for match in re.finditer(ent_regex, example):
            entity_text = match.groupdict()['entity_text']
            entity_type = match.groupdict()['entity']
            entity_value = match.groupdict()['value'] if match.groupdict()['value'] else entity_text

            start_index = match.start() - offset
            end_index = start_index + len(entity_text)
            offset += len(match.group(0)) - len(entity_text)

            entity = build_entity(start_index, end_index, entity_value, entity_type)
            entities.append(entity)

        return entities


    def _parse_training_example(self, example):
        """Extract entities and synonyms, and convert to plain text."""
        entities = self._find_entities_in_training_example(example)
        plain_text = re.sub(ent_regex, lambda m: m.groupdict()['entity_text'], example)
        document = Document(plain_text, {'target': self.current_title})
        if len(entities) > 0:
            document.set('entities', entities)
        return document


class JsonWriter():

    def dumps(self, training_data):
        """Transforms a TrainingData object into a markdown string."""
        md = u''
        md += self._generate_training_examples_md(training_data)
        md += self._generate_synonyms_md(training_data)
        md += self._generate_regex_features_md(training_data)
        md += self._generate_lookup_tables_md(training_data)

        return md

    def _generate_training_examples_md(self, training_data):
        """generates markdown training examples."""
        training_examples = sorted([e.as_dict() for e in training_data.training_examples],
                                   key=lambda k: k['intent'])
        md = u''
        for i, example in enumerate(training_examples):
            if i == 0 or training_examples[i - 1]['intent'] != example['intent']:
                md += self._generate_section_header_md(CLASS, example['intent'], i != 0)

            md += self._generate_item_md(self._generate_document_md(example))

        return md


    def _generate_item_md(self, text):
        """generates markdown for a list item."""
        return "- {}\n".format(text)

    def _generate_fname_md(self, text):
        """generates markdown for a lookup table file path."""
        return "  {}\n".format(text)

    def _generate_document_md(self, document):
        """generates markdown for a document object."""
        md = ''
        text = document.get('text', "")
        entities = sorted(document.get('entities', []),
                          key=lambda k: k['start'])

        pos = 0
        for entity in entities:
            md += text[pos:entity['start']]
            md += self._generate_entity_md(text, entity)
            pos = entity['end']

        md += text[pos:]

        return md

    def _generate_entity_md(self, text, entity):
        """generates markdown for an entity object."""
        entity_text = text[entity['start']:entity['end']]
        entity_type = entity['entity']
        if entity_text != entity['value']:
            # add synonym suffix
            entity_type += ":{}".format(entity['value'])

        return '[{}]({})'.format(entity_text, entity_type)
