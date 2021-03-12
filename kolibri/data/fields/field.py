from typing import Dict, Generic, List, TypeVar


class Field():
    """
    A ``Field`` is some piece of a tokenizers instance.
    """

    def count_vocab_items(self, counter):

        pass

    def index(self, vocabulary):
        """
        converts all strings in this field into integers.
        """
        pass
    def get_padding_lengths(self) -> Dict[str, int]:
        """
        In order to pad a  batch of instance, we get all of the lengths from the batch, take the max, and pad
        everything to that length. we can also use a predefined length
        """
        return 1

    def empty_field(self):
        """

        """
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented
