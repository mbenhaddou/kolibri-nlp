from typing import Dict, Union
import logging
import json
from overrides import overrides
from kolibri.data.dataset_readers.dataset_reader import DatasetReader
from kolibri_dnn.data.fields import LabelField, TextField, Field, ListField
from kolibri.data.document import Document
from kolibri.data.token_indexers import TokenIndexer, SingleIdTokenIndexer
from kolibri_dnn.tokenizers import RegexpTokenizer, SentenceTokenizer

logger = logging.getLogger(__name__)


class TextClassificationJsonReader(DatasetReader):
    """
    Reads tokens and their labels from a labeled text classification dataset.
    Expects a "text" field and a "label" field in JSON format.
    """

    def __init__(
        self,
        token_indexers: Dict[str, TokenIndexer] = None,
        tokenizer = None,
        segment_sentences: bool = False,
        skip_label_indexing: bool = False
    ) -> None:
        super().__init__()
        self._tokenizer = tokenizer or RegexpTokenizer()
        self._segment_sentences = segment_sentences
        self._skip_label_indexing = skip_label_indexing
        self._token_indexers = token_indexers or {"tokens": SingleIdTokenIndexer()}
        if self._segment_sentences:
            self._sentence_segmenter = SentenceTokenizer()

    @overrides
    def _read(self, file_path):
        with open(file_path, "r") as data_file:
            for line in data_file.readlines():
                if not line:
                    continue
                items = json.loads(line)
                text = items["text"]
                label = items.get("label", None)
                if label is not None:
                    if self._skip_label_indexing:
                        try:
                            label = int(label)
                        except ValueError:
                            raise ValueError(
                                "Labels must be integers if skip_label_indexing is True."
                            )
                    else:
                        label = str(label)
                instance = self.text_to_instance(text=text, label=label)
                if instance is not None:
                    yield instance

    @overrides
    def text_to_instance(
        self, text: str, label: Union[str, int] = None
    ):  # type: ignore

        fields: Dict[str, Field] = {}
        if self._segment_sentences:
            sentences = []
            sentence_splits = self._sentence_segmenter.tokenize(text)
            for sentence in sentence_splits:
                word_tokens = self._tokenizer.tokenize(sentence["text"])
                sentences.append(TextField(word_tokens, self._token_indexers))
            fields["sentences"] = ListField(sentences)
        else:
            tokens = self._tokenizer.tokenize(text)
            fields["tokens"] = TextField(tokens, self._token_indexers)
        if label is not None:
            fields["label"] = LabelField(label, skip_indexing=self._skip_label_indexing)
        return Document(fields)
