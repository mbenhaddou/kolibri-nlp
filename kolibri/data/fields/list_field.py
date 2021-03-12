from overrides import overrides

from kolibri.data.fields.field import DataArray, Field
from kolibri.data.vocabulary import Vocabulary
from kolibri.data.fields.sequence_field import SequenceField



class ListField(SequenceField):
    """
    A ``ListField`` is a list of other fields.  You would use this to represent, e.g., a list of
    answer options that are themselves ``TextFields``.
    """

    def __init__(self, field_list):
        field_class_set = {field.__class__ for field in field_list}
        assert (
            len(field_class_set) == 1
        ), "ListFields must contain a single field type, found " + str(field_class_set)
        # Not sure why mypy has a hard time with this type...
        self.field_lis = field_list

    # Sequence[Field] methods
    def __iter__(self):
        return iter(self.field_list)

    def __getitem__(self, idx: int):
        return self.field_list[idx]

    def __len__(self) -> int:
        return len(self.field_list)

    @overrides
    def count_vocab_items(self, counter):
        for field in self.field_list:
            field.count_vocab_items(counter)

    @overrides
    def index(self, vocab: Vocabulary):
        for field in self.field_list:
            field.index(vocab)

    @overrides
    def get_padding_lengths(self) :
        field_lengths = [field.get_padding_lengths() for field in self.field_list]
        padding_lengths = {"num_fields": len(self.field_list)}

        # We take the set of all possible padding keys for all fields, rather
        # than just a random key, because it is possible for fields to be empty
        # when we pad ListFields.
        possible_padding_keys = [
            key for field_length in field_lengths for key in list(field_length.keys())
        ]

        for key in set(possible_padding_keys):
            # In order to be able to nest ListFields, we need to scope the padding length keys
            # appropriately, so that nested ListFields don't all use the same "num_fields" key.  So
            # when we construct the dictionary from the list of fields, we add something to the
            # name, and we remove it when padding the list of fields.
            padding_lengths["list_" + key] = max(x[key] if key in x else 0 for x in field_lengths)

        # Set minimum padding length to handle empty list fields.
        for padding_key in padding_lengths:
            padding_lengths[padding_key] = max(padding_lengths[padding_key], 1)

        return padding_lengths

    @overrides
    def sequence_length(self) -> int:
        return len(self.field_list)


    @overrides
    def empty_field(self):
        # Our "empty" list field will actually have a single field in the list, so that we can
        # correctly construct nested lists.  For example, if we have a type that is
        # `ListField[ListField[LabelField]]`, we need the top-level `ListField` to know to
        # construct a `ListField[LabelField]` when it's padding, and the nested `ListField` needs
        # to know that it's empty objects are `LabelFields`.  Having an "empty" list actually have
        # length one makes this all work out, and we'll always be padding to at least length 1,
        # anyway.
        return ListField([self.field_list[0].empty_field()])


    def __str__(self) -> str:
        field_class = self.field_list[0].__class__.__name__
        base_string = f"ListField of {len(self.field_list)} {field_class}s : \n"
        return " ".join([base_string] + [f"\t {field} \n" for field in self.field_list])
