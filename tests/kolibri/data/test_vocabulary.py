import codecs
import pickle
import gzip
import zipfile
from copy import deepcopy
import copy
import shutil
import pytest
from kolibri.data.token_indexers import SingleIdTokenIndexer
from kolibri.data.fields import TextField
from kolibri.tokenizer.token_ import Token
from kolibri.data.document import Document
from kolibri.data.vocabulary import Vocabulary
from kolibri.data.dataset import Dataset
from kolibri.test_case import KolibriTestCase

TEST_DIR="/Users/mohamedmentis/Documents/Mentis/Development/Python/Kolibri/tests"

class TestVocabulary (KolibriTestCase):

    def setUp(self):
        token_indexer = SingleIdTokenIndexer("tokens")
        text_field = TextField(
            [Token(t) for t in ["a", "a", "a", "a", "b", "b", "c", "c", "c"]],
            {"tokens": token_indexer},
        )
        self.instance = Document({"text": text_field})
        self.dataset = Dataset([self.instance])
        super().setUp()

    def test_pickling(self):
        vocab = Vocabulary.from_instances(self.dataset)

        pickled = pickle.dumps(vocab)
        unpickled = pickle.loads(pickled)

        assert dict(unpickled._index_to_token) == dict(vocab._index_to_token)
        assert dict(unpickled._token_to_index) == dict(vocab._token_to_index)
        assert unpickled._non_padded_namespaces == vocab._non_padded_namespaces
        assert unpickled._oov_token == vocab._oov_token
        assert unpickled._padding_token == vocab._padding_token
        assert unpickled._retained_counter == vocab._retained_counter


    def test_saving_and_loading(self):

        vocab_dir = self.TEST_DIR / "vocab_save"

        vocab = Vocabulary(non_padded_namespaces=["a", "c"])
        vocab.add_tokens_to_namespace(
            ["a0", "a1", "a2"], namespace="a"
        )  # non-padded, should start at 0
        vocab.add_tokens_to_namespace(["b2", "b3"], namespace="b")  # padded, should start at 2

        vocab.save_to_files(vocab_dir)
        vocab2 = Vocabulary.from_files(vocab_dir)

        assert vocab2._non_padded_namespaces == {"a", "c"}

        # Check namespace a.
        assert vocab2.get_vocab_size(namespace="a") == 3
        assert vocab2.get_token_from_index(0, namespace="a") == "a0"
        assert vocab2.get_token_from_index(1, namespace="a") == "a1"
        assert vocab2.get_token_from_index(2, namespace="a") == "a2"
        assert vocab2.get_token_index("a0", namespace="a") == 0
        assert vocab2.get_token_index("a1", namespace="a") == 1
        assert vocab2.get_token_index("a2", namespace="a") == 2

        # Check namespace b.
        assert vocab2.get_vocab_size(namespace="b") == 4  # (unk + padding + two tokens)
        assert vocab2.get_token_from_index(0, namespace="b") == vocab._padding_token
        assert vocab2.get_token_from_index(1, namespace="b") == vocab._oov_token
        assert vocab2.get_token_from_index(2, namespace="b") == "b2"
        assert vocab2.get_token_from_index(3, namespace="b") == "b3"
        assert vocab2.get_token_index(vocab._padding_token, namespace="b") == 0
        assert vocab2.get_token_index(vocab._oov_token, namespace="b") == 1
        assert vocab2.get_token_index("b2", namespace="b") == 2
        assert vocab2.get_token_index("b3", namespace="b") == 3

        # Check the dictionaries containing the reverse mapping are identical.
        assert vocab.get_index_to_token_vocabulary("a") == vocab2.get_index_to_token_vocabulary("a")
        assert vocab.get_index_to_token_vocabulary("b") == vocab2.get_index_to_token_vocabulary("b")

    # def test_from_params(self):
    #     # Save a vocab to check we can load it from_params.
    #     vocab_dir = self.TEST_DIR / "vocab_save"
    #     vocab = Vocabulary(non_padded_namespaces=["a", "c"])
    #     vocab.add_tokens_to_namespace(
    #         ["a0", "a1", "a2"], namespace="a"
    #     )  # non-padded, should start at 0
    #     vocab.add_tokens_to_namespace(["b2", "b3"], namespace="b")  # padded, should start at 2
    #     vocab.save_to_files(vocab_dir)
    #
    #     params = Params({"directory_path": vocab_dir})
    #     vocab2 = Vocabulary.from_params(params)
    #     assert vocab.get_index_to_token_vocabulary("a") == vocab2.get_index_to_token_vocabulary("a")
    #     assert vocab.get_index_to_token_vocabulary("b") == vocab2.get_index_to_token_vocabulary("b")
    #
    #     # Test case where we build a vocab from a dataset.
    #     vocab2 = Vocabulary.from_params(Params({}), self.dataset)
    #     assert vocab2.get_index_to_token_vocabulary("tokens") == {
    #         0: "@@PADDING@@",
    #         1: "@@UNKNOWN@@",
    #         2: "a",
    #         3: "c",
    #         4: "b",
    #     }
    #     # Test from_params raises when we have neither a dataset and a vocab_directory.
    #     with pytest.raises(ConfigurationError):
    #         _ = Vocabulary.from_params(Params({}))
    #
    #     # Test from_params raises when there are any other dict keys
    #     # present apart from 'directory_path' and we aren't calling from_dataset.
    #     with pytest.raises(ConfigurationError):
    #         _ = Vocabulary.from_params(
    #             Params({"directory_path": vocab_dir, "min_count": {"tokens": 2}})
    #         )
    #
    # def test_from_params_adds_tokens_to_vocab(self):
    #     vocab = Vocabulary.from_params(
    #         Params({"tokens_to_add": {"tokens": ["q", "x", "z"]}}), self.dataset
    #     )
    #     assert vocab.get_index_to_token_vocabulary("tokens") == {
    #         0: "@@PADDING@@",
    #         1: "@@UNKNOWN@@",
    #         2: "a",
    #         3: "c",
    #         4: "b",
    #         5: "q",
    #         6: "x",
    #         7: "z",
    #     }

