from kolibri.data.fields.field import Field


class SequenceField(Field):
    """
    A ``SequenceField`` represents a sequence of things.
    """

    def sequence_length(self) -> int:
        """
        How many elements are there in this sequence?
        """
        raise NotImplementedError

    def empty_field(self):
        raise NotImplementedError
