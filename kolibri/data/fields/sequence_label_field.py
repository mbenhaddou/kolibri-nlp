from typing import Dict, List, Union, Set, Iterator
import logging
import textwrap

from overrides import overrides
import torch

from kolibri.data.fields.field import Field
from kolibri.data.fields.sequence_field import SequenceField
from kolibri.data.vocabulary import Vocabulary

logger = logging.getLogger(__name__)


class SequenceLabelField(Field):
    """
    A ``SequenceLabelField`` assigns a categorical label to each element.
    """

    _already_warned_namespaces: Set[str] = set()

    def __init__(
        self,
        labels,
        sequence_field,
        label_namespace: str = "labels",
    ) -> None:
        self.labels = labels
        self.sequence_field = sequence_field
        self._label_namespace = label_namespace
        self._indexed_labels = None
        if len(labels) != sequence_field.sequence_length():
            raise Exception(
                "Label length and sequence length "
                "don't match: %d and %d" % (len(labels), sequence_field.sequence_length())
            )

        self._skip_indexing = False
        if all([isinstance(x, int) for x in labels]):
            self._indexed_labels = labels
            self._skip_indexing = True

        elif not all([isinstance(x, str) for x in labels]):
            raise Exception(
                "SequenceLabelFields must be passed either all "
                "strings or all ints. Found labels {} with "
                "types: {}.".format(labels, [type(x) for x in labels])
            )

    # Sequence methods
    def __iter__(self) -> Iterator[Union[str, int]]:
        return iter(self.labels)

    def __getitem__(self, idx: int) -> Union[str, int]:
        return self.labels[idx]

    def __len__(self) -> int:
        return len(self.labels)

    def get_padding_lengths(self) -> Dict[str, int]:
        return self.sequence_field.sequence_length()


    @overrides
    def count_vocab_items(self, counter: Dict[str, Dict[str, int]]):
        if self._indexed_labels is None:
            for label in self.labels:
                counter[self._label_namespace][label] += 1  # type: ignore

    @overrides
    def index(self, vocab: Vocabulary):
        if not self._skip_indexing:
            self._indexed_labels = [
                vocab.get_token_index(label, self._label_namespace)  # type: ignore
                for label in self.labels
            ]

    @overrides
    def empty_field(self) -> "SequenceLabelField":

        # The empty_list here is needed for mypy
        empty_list: List[str] = []
        sequence_label_field = SequenceLabelField(empty_list, self.sequence_field.empty_field())
        sequence_label_field._indexed_labels = empty_list
        return sequence_label_field

    def __str__(self) -> str:
        length = self.sequence_field.sequence_length()
        formatted_labels = "".join(
            ["\t\t" + labels + "\n" for labels in textwrap.wrap(repr(self.labels), 100)]
        )
        return (
            f"SequenceLabelField of length {length} with "
            f"labels:\n {formatted_labels} \t\tin namespace: '{self._label_namespace}'."
        )
