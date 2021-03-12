from typing import Dict, List
import itertools

from overrides import overrides

from kolibri.data.vocabulary import Vocabulary
from kolibri.tokenizer.token_ import Token
from kolibri.data.token_indexers.token_indexer import TokenIndexer


class SingleIdTokenIndexer(TokenIndexer):
    """
    This :class:`TokenIndexer` represents tokens as single integers..
    """

    def __init__(
        self,
        namespace: str = "tokens",
        lowercase_tokens: bool = False,
        start_tokens = None,
        end_tokens = None
    ) -> None:
        self.namespace = namespace
        self.lowercase_tokens = lowercase_tokens

        self._start_tokens = [Token(st) for st in (start_tokens or [])]
        self._end_tokens = [Token(et) for et in (end_tokens or [])]

    @overrides
    def count_vocab_items(self, token: Token, counter: Dict[str, Dict[str, int]]):
        # If `text_id` is set on the token (e.g., if we're using some kind of hash-based word
        # encoding), we will not be using the vocab for this token.
        if getattr(token, "text_id", None) is None:
            text = token.text
            if self.lowercase_tokens:
                text = text.lower()
            counter[self.namespace][text] += 1

    @overrides
    def tokens_to_indices(
        self, tokens: List[Token], vocabulary: Vocabulary, index_name: str
    ) -> Dict[str, List[int]]:
        indices: List[int] = []

        for token in itertools.chain(self._start_tokens, tokens, self._end_tokens):
            if getattr(token, "text_id", None) is not None:
                # `text_id` being set on the token means that we aren't using the vocab, we just use
                # this id instead.
                indices.append(token.text_id)
            else:
                text = token.text
                if self.lowercase_tokens:
                    text = text.lower()
                indices.append(vocabulary.get_token_index(text, self.namespace))

        return {index_name: indices}

