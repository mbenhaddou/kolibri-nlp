
from kolibri.data.fields.field import Field
from kolibri.data.vocabulary import Vocabulary


class Document():
    """
    An ``Instance`` is a collection of 'Field` objects specifying the inputs and outputs to
    a model.
    """

    def __init__(self, fields):
        self.fields = fields
        self.indexed = False

    def __getitem__(self, key: str) -> Field:
        return self.fields[key]

    def __iter__(self):
        return iter(self.fields)

    def __len__(self) -> int:
        return len(self.fields)

    def add_field(self, field_name: str, field: Field, vocab: Vocabulary = None) -> None:
        """
        Add the field to the existing fields mapping.
        """
        self.fields[field_name] = field
        if self.indexed:
            field.index(vocab)

    def get_padding_lengths(self):
        """
        Returns a dictionary of padding lengths, keyed by field name.  Each ``Field`` returns a
        mapping from padding keys to actual lengths, and we just key that dictionary by field name.
        """
        lengths = {}
        for field_name, field in self.fields.items():
            lengths[field_name] = field.get_padding_lengths()
        return lengths

    def count_vocab_items(self, counter):
        """
        Increments counts in the given ``counter`` for all of the vocabulary items in all of the
        ``Fields`` in this ``Instance``.
        """
        for field in self.fields.values():
            field.count_vocab_items(counter)

    def index_fields(self, vocab: Vocabulary) -> None:
        """
        Indexes all fields in this ``Instance`` using the provided ``Vocabulary``.
        """
        if not self.indexed:
            self.indexed = True
            for field in self.fields.values():
                field.index(vocab)

    def __str__(self) -> str:
        base_string = f"Instance with fields:\n"
        return " ".join(
            [base_string] + [f"\t {name}: {field} \n" for name, field in self.fields.items()]
        )
