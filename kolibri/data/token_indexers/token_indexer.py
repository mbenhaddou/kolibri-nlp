from typing import Dict, List, TypeVar

import numpy

from kolibri.tokenizer.token_ import Token

TokenType = TypeVar("TokenType", int, List[int], numpy.ndarray)


class TokenIndexer():
    """
    Determines how string tokens get represented as arrays of indices in a model.
    This class both converts strings into numerical values and it produces actual arrays.

    Tokens can be represented as single IDs (e.g., the word "cat" gets represented by the number
    34), or as lists of character IDs (e.g., "cat" gets represented by the numbers [23, 10, 18]).

      """

    default_implementation = "single_id"

    def count_vocab_items(self, token: Token, counter: Dict[str, Dict[str, int]]):
         raise NotImplementedError

    def tokens_to_indices( self, tokens, vocabulary, index_name: str):
        """
        Takes a list of tokens and converts them to one or more sets of indices.
        """
        raise NotImplementedError

    def get_keys(self, index_name: str) -> List[str]:
        """
        Return a list of the keys this indexer return from ``tokens_to_indices``.
        """

        return [index_name]

    def __eq__(self, other) -> bool:
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented
