import tempfile
import pytest
from kolibri.data.dataset_readers.entity_reader_json import JSONEntityReader
from kolibri.utils import ensure_list


class TestJSONDatasetReader:
    def test_default_format(self):
        reader = JSONEntityReader()
        instances = reader.read("../../data/all_sentences_entities.json")
        instances = ensure_list(instances)
        assert len(instances) == 1597
