from typing import Dict, Union, Set
import logging

from overrides import overrides
import torch

from kolibri.data.fields.field import Field
from kolibri.data.vocabulary import Vocabulary


logger = logging.getLogger(__name__)


class LabelField(Field):
    """
    A ``LabelField`` is a categorical label of some kind, where the labels are either strings of
    text or 0-indexed integers (if you wish to skip indexing by passing skip_indexing=True).
    """

    # Most often, you probably don't want to have OOV/PAD tokens with a LabelField, so we warn you
    # about it when you pick a namespace that will getting these tokens by default.  It is
    # possible, however, that you _do_ actually want OOV/PAD tokens with this Field.  This class
    # variable is used to make sure that we only log a single warning for this per namespace, and
    # not every time you create one of these Field objects.
    _already_warned_namespaces: Set[str] = set()

    def __init__(
        self, label: Union[str, int], label_namespace: str = "labels", skip_indexing: bool = False
    ) -> None:
        self.label = label
        self._label_namespace = label_namespace
        self._label_id = None
#        self._already_warned_namespaces(label_namespace)
        self._skip_indexing = skip_indexing

        if skip_indexing:
            if not isinstance(label, int):
                raise Exception(
                    "In order to skip indexing, your labels must be integers. "
                    "Found label = {}".format(label)
                )
            self._label_id = label
        elif not isinstance(label, str):
            raise Exception(
                "LabelFields must be passed a string label if skip_indexing=False. "
                "Found label: {} with type: {}.".format(label, type(label))
            )
    @overrides
    def count_vocab_items(self, counter: Dict[str, Dict[str, int]]):
        if self._label_id is None:
            counter[self._label_namespace][self.label] += 1  # type: ignore

    @overrides
    def index(self, vocab: Vocabulary):
        if not self._skip_indexing:
            self._label_id = vocab.get_token_index(
                self.label, self._label_namespace  # type: ignore
            )

    @overrides
    def empty_field(self):
        return LabelField(-1, self._label_namespace, skip_indexing=True)

    def __str__(self) -> str:
        return f"LabelField with label: {self.label} in namespace: '{self._label_namespace}'.'"
