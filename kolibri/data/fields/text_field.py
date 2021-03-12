"""
A ``TextField`` represents a string of text, the kind that you might want to represent with
standard word vectors, or pass through an LSTM.
"""
from typing import Dict, List, Iterator
import textwrap

from overrides import overrides

from kolibri.tokenizer.token_ import Token
from kolibri.data.token_indexers.token_indexer import TokenType
from kolibri.data.vocabulary import Vocabulary
from kolibri.data.fields.sequence_label_field import Field

TokenList = List[TokenType]


class TextField(Field):
    """
    This ``Field`` represents a list of string tokens.  Before constructing this object, you need
    to tokenize raw strings.
    """

    def __init__(self, tokens, token_indexers) -> None:

        self.tokens = tokens
        self._token_indexers = token_indexers
        self._indexed_tokens = None
        self._indexer_name_to_indexed_token = None
        self._token_index_to_indexer_name = None


    # Sequence[Token] methods
    def __iter__(self) -> Iterator[Token]:
        return iter(self.tokens)

    def __getitem__(self, idx: int) -> Token:
        return self.tokens[idx]

    def __len__(self) -> int:
        return len(self.tokens)


    def count_vocab_items(self, counter):
        for indexer in self._token_indexers.values():
            for token in self.tokens:
                indexer.count_vocab_items(token, counter)

    @overrides
    def index(self, vocab: Vocabulary):
        token_arrays: Dict[str, TokenList] = {}
        indexer_name_to_indexed_token: Dict[str, List[str]] = {}
        token_index_to_indexer_name: Dict[str, str] = {}
        for indexer_name, indexer in self._token_indexers.items():
            token_indices = indexer.tokens_to_indices(self.tokens, vocab, indexer_name)
            token_arrays.update(token_indices)
            indexer_name_to_indexed_token[indexer_name] = list(token_indices.keys())
            for token_index in token_indices:
                token_index_to_indexer_name[token_index] = indexer_name
        self._indexed_tokens = token_arrays
        self._indexer_name_to_indexed_token = indexer_name_to_indexed_token
        self._token_index_to_indexer_name = token_index_to_indexer_name


    def sequence_length(self) -> int:
        return len(self.tokens)


    def empty_field(self):

        text_field = TextField([], self._token_indexers)
        text_field._indexed_tokens = {}
        text_field._indexer_name_to_indexed_token = {}
        for indexer_name, indexer in self._token_indexers.items():
            array_keys = indexer.get_keys(indexer_name)
            for key in array_keys:
                text_field._indexed_tokens[key] = []
            text_field._indexer_name_to_indexed_token[indexer_name] = array_keys
        return text_field

    @overrides
    def get_padding_lengths(self):
        """
       This method gets the max length (over tokens)
        associated with each of these arrays.
        """

        return len(self.tokens)



    def __str__(self) -> str:
        indexers = {
            name: indexer.__class__.__name__ for name, indexer in self._token_indexers.items()
        }

        # Double tab to indent under the header.
        formatted_text = "".join(
            ["\t\t" + text + "\n" for text in textwrap.wrap(repr(self.tokens), 100)]
        )
        return (
            f"TextField of length {self.sequence_length()} with "
            f"text: \n {formatted_text} \t\tand TokenIndexers : {indexers}"
        )
