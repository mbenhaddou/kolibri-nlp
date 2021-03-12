"""
A Vocabulary maps strings to integers, allowing for strings to be mapped to an
out-of-vocabulary token.
"""

import codecs
import copy
import logging
import os
from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Union
import tqdm
from kolibri.utils import namespace_match
from kolibri.config import ModelConfig
logger = logging.getLogger(__name__)


DEFAULT_NON_PADDED_NAMESPACES = ("*tags", "*labels")
DEFAULT_PADDING_TOKEN = "__PADDING__"
DEFAULT_OOV_TOKEN = "__UNKNOWN__"
NAMESPACE_PADDING_FILE = "non_padded_namespaces.txt"


class _NamespaceDict(defaultdict):
    """
    This is a `defaultdict where we use "namespaces" in the to keep track of several different
    mappings from strings to integers, so that we have a consistent API for mapping words, tags,
    labels, characters, or whatever else you want, into integers.  The issue is that some of those
    namespaces (words and characters) should have integers reserved for padding and
    out-of-vocabulary tokens, while others (labels and tags) shouldn't.
    """

    def __init__(
        self,
        non_padded_namespaces: Iterable[str],
        padded_function: Callable[[], Any],
        non_padded_function: Callable[[], Any],
    ) -> None:
        self._non_padded_namespaces = set(non_padded_namespaces)
        self._padded_function = padded_function
        self._non_padded_function = non_padded_function
        super().__init__()

    def __missing__(self, key: str):
        if any(namespace_match(pattern, key) for pattern in self._non_padded_namespaces):
            value = self._non_padded_function()
        else:
            value = self._padded_function()
        dict.__setitem__(self, key, value)
        return value

    def add_non_padded_namespaces(self, non_padded_namespaces: Set[str]):
        # add non_padded_namespaces which weren't already present
        self._non_padded_namespaces.update(non_padded_namespaces)


class _Token2IndexDict(_NamespaceDict):
    def __init__(self, non_padded_namespaces: Set[str], padding_token: str, oov_token: str) -> None:
        super().__init__(
            non_padded_namespaces, lambda: {padding_token: 0, oov_token: 1}, lambda: {}
        )


class _Index2TokenDict(_NamespaceDict):
    def __init__(self, non_padded_namespaces: Set[str], padding_token: str, oov_token: str) -> None:
        super().__init__(
            non_padded_namespaces, lambda: {0: padding_token, 1: oov_token}, lambda: {}
        )



def pop_max_vocab_size(params: ModelConfig):
    """
    max_vocab_size: maximum size of the vocabulary, not including the __UNKNOWN__ token..
    """
    size = params.get("max_vocab_size", None)

    if isinstance(size, dict):
        # This is the Dict[str, int] case.
        return size
    elif size is not None:
        # This is the int / str case.
        return int(size)
    else:
        return None


class Vocabulary():
    """
    Maps strings to integers and integrers to strings, allowing for strings to be mapped to an
    out-of-vocabulary token..
    """

    default_implementation = "default"

    def __init__(
        self,
        counter: Dict[str, Dict[str, int]] = None,
        min_count: Dict[str, int] = None,
        max_vocab_size: Union[int, Dict[str, int]] = None,
        non_padded_namespaces: Iterable[str] = DEFAULT_NON_PADDED_NAMESPACES,
        tokens_to_add: Dict[str, List[str]] = None,
        padding_token: Optional[str] = DEFAULT_PADDING_TOKEN,
        oov_token: Optional[str] = DEFAULT_OOV_TOKEN,
        recemmended_padding: int=None
    ) -> None:

        self._padding_token = padding_token if padding_token is not None else DEFAULT_PADDING_TOKEN
        self._oov_token = oov_token if oov_token is not None else DEFAULT_OOV_TOKEN

        self._non_padded_namespaces = set(non_padded_namespaces)

        self._token_to_index = _Token2IndexDict(
            self._non_padded_namespaces, self._padding_token, self._oov_token
        )
        self._index_to_token = _Index2TokenDict(
            self._non_padded_namespaces, self._padding_token, self._oov_token
        )

        self.recommended_padding_lengths=recemmended_padding
        self._retained_counter: Optional[Dict[str, Dict[str, int]]] = None
        # Made an empty vocabulary, now extend it.
        self._extend(
            counter,
            min_count,
            max_vocab_size,
            non_padded_namespaces,
            tokens_to_add,
        )

    def __getstate__(self):
        """
        Need to sanitize defaultdict and defaultdict-like objects
        by converting them to vanilla dicts when we pickle the vocabulary.
        """
        state = copy.copy(self.__dict__)
        state["_token_to_index"] = dict(state["_token_to_index"])
        state["_index_to_token"] = dict(state["_index_to_token"])

        if "_retained_counter" in state:
            state["_retained_counter"] = {
                key: dict(value) for key, value in state["_retained_counter"].items()
            }

        return state

    def __setstate__(self, state):
        """
        Conversely, when we unpickle, we need to reload the plain dicts
        into our special DefaultDict subclasses.
        """

        self.__dict__ = copy.copy(state)
        self._token_to_index = _Token2IndexDict(
            self._non_padded_namespaces, self._padding_token, self._oov_token
        )
        self._token_to_index.update(state["_token_to_index"])
        self._index_to_token = _Index2TokenDict(
            self._non_padded_namespaces, self._padding_token, self._oov_token
        )
        self._index_to_token.update(state["_index_to_token"])

    def save_to_files(self, directory: str) -> None:
        """
        Persist this Vocabulary to files so it can be reloaded later.
        Each namespace corresponds to one file.

        Parameters
        ----------
        directory : ``str``
            The directory where we save the serialized vocabulary.
        """
        os.makedirs(directory, exist_ok=True)
        if os.listdir(directory):
            logging.warning("vocabulary serialization directory %s is not empty", directory)

        with codecs.open(
            os.path.join(directory, NAMESPACE_PADDING_FILE), "w", "utf-8"
        ) as namespace_file:
            for namespace_str in self._non_padded_namespaces:
                print(namespace_str, file=namespace_file)

        for namespace, mapping in self._index_to_token.items():
            # Each namespace gets written to its own file, in index order.
            with codecs.open(
                os.path.join(directory, namespace + ".txt"), "w", "utf-8"
            ) as token_file:
                num_tokens = len(mapping)
                start_index = 1 if mapping[0] == self._padding_token else 0
                for i in range(start_index, num_tokens):
                    print(mapping[i].replace("\n", "__NEWLINE__"), file=token_file)

    @classmethod
    def from_files(
        cls,
        directory: str,
        padding_token: Optional[str] = DEFAULT_PADDING_TOKEN,
        oov_token: Optional[str] = DEFAULT_OOV_TOKEN,
    ) -> "Vocabulary":
        """
        Loads a ``Vocabulary`` that was serialized using ``save_to_files``.

        Parameters
        ----------
        directory : ``str``
            The directory containing the serialized vocabulary.
        """
        logger.info("Loading token dictionary from %s.", directory)
        padding_token = padding_token if padding_token is not None else DEFAULT_PADDING_TOKEN
        oov_token = oov_token if oov_token is not None else DEFAULT_OOV_TOKEN
        with codecs.open(
            os.path.join(directory, NAMESPACE_PADDING_FILE), "r", "utf-8"
        ) as namespace_file:
            non_padded_namespaces = [namespace_str.strip() for namespace_str in namespace_file]

        vocab = cls(
            non_padded_namespaces=non_padded_namespaces,
            padding_token=padding_token,
            oov_token=oov_token,
        )

        # Check every file in the directory.
        for namespace_filename in os.listdir(directory):
            if namespace_filename == NAMESPACE_PADDING_FILE:
                continue
            if namespace_filename.startswith("."):
                continue
            namespace = namespace_filename.replace(".txt", "")
            if any(namespace_match(pattern, namespace) for pattern in non_padded_namespaces):
                is_padded = False
            else:
                is_padded = True
            filename = os.path.join(directory, namespace_filename)
            vocab.set_from_file(filename, is_padded, namespace=namespace, oov_token=oov_token)

        return vocab

    def set_from_file(
        self,
        filename: str,
        is_padded: bool = True,
        oov_token: str = DEFAULT_OOV_TOKEN,
        namespace: str = "tokens",
    ):
        """
        If you already have a vocabulary file for a trained model somewhere, and you really want to
        use that vocabulary file instead of just setting the vocabulary from a dataset, for
        whatever reason, you can do that with this method.  You must specify the namespace to use,
        and we assume that you want to use padding and OOV tokens for this.

        Parameters
        ----------
        filename : ``str``
            The file containing the vocabulary to load.  It should be formatted as one token per
            line, with nothing else in the line.  The index we assign to the token is the line
            number in the file (1-indexed if ``is_padded``, 0-indexed otherwise).  Note that this
            file should contain the OOV token string!
        is_padded : ``bool``, optional (default=True)
            Is this vocabulary padded?  For token / word / character vocabularies, this should be
            ``True``; while for tag or label vocabularies, this should typically be ``False``.  If
            ``True``, we add a padding token with index 0, and we enforce that the ``oov_token`` is
            present in the file.
        oov_token : ``str``, optional (default=DEFAULT_OOV_TOKEN)
            What token does this vocabulary use to represent out-of-vocabulary characters?  This
            must show up as a line in the vocabulary file.  When we find it, we replace
            ``oov_token`` with ``self._oov_token``, because we only use one OOV token across
            namespaces.
        namespace : ``str``, optional (default="tokens")
            What namespace should we overwrite with this vocab file?
        """
        if is_padded:
            self._token_to_index[namespace] = {self._padding_token: 0}
            self._index_to_token[namespace] = {0: self._padding_token}
        else:
            self._token_to_index[namespace] = {}
            self._index_to_token[namespace] = {}
        with codecs.open(filename, "r", "utf-8") as input_file:
            lines = input_file.read().split("\n")
            # Be flexible about having final newline or not
            if lines and lines[-1] == "":
                lines = lines[:-1]
            for i, line in enumerate(lines):
                index = i + 1 if is_padded else i
                token = line.replace("@@NEWLINE@@", "\n")
                if token == oov_token:
                    token = self._oov_token
                self._token_to_index[namespace][token] = index
                self._index_to_token[namespace][index] = token
        if is_padded:
            assert self._oov_token in self._token_to_index[namespace], "OOV token not found!"

    @classmethod
    def from_instances(
        cls,
        instances: Iterable["adi.Instance"],
        min_count: Dict[str, int] = None,
        max_vocab_size: Union[int, Dict[str, int]] = None,
        non_padded_namespaces: Iterable[str] = DEFAULT_NON_PADDED_NAMESPACES,
        tokens_to_add: Dict[str, List[str]] = None,
        padding_token: Optional[str] = DEFAULT_PADDING_TOKEN,
        oov_token: Optional[str] = DEFAULT_OOV_TOKEN,
    ) -> "Vocabulary":
        """
        Constructs a vocabulary given a collection of `Instances` and some parameters.
        We count all of the vocabulary items in the instances, then pass those counts
        and the other parameters, to :func:`__init__`.  See that method for a description
        of what the other parameters do.
        """
        logger.info("Fitting token dictionary from dataset.")
        padding_token = padding_token if padding_token is not None else DEFAULT_PADDING_TOKEN
        oov_token = oov_token if oov_token is not None else DEFAULT_OOV_TOKEN
        namespace_token_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        all_instance_lengths: List[Dict[str, Dict[str, int]]] = []
        padding_lengths: Dict[str, Dict[str, int]] = defaultdict(dict)
        for instance in tqdm.tqdm(instances):
            instance.count_vocab_items(namespace_token_counts)
            all_instance_lengths.append(instance.get_padding_lengths())

        if not all_instance_lengths:
            _recommended_padding ={**padding_lengths}
        else:
            all_field_lengths: Dict[str, List[Dict[str, int]]] = defaultdict(list)
            for instance_lengths in all_instance_lengths:
                for field_name, instance_field_lengths in instance_lengths.items():
                    all_field_lengths[field_name].append(instance_field_lengths)

            for field_name, field_lengths in all_field_lengths.items():
                padding_lengths[field_name] = sorted(field_lengths)[int(0.90 * len(field_lengths))]
            _recommended_padding= {**padding_lengths}
        return cls(
            counter=namespace_token_counts,
            min_count=min_count,
            max_vocab_size=max_vocab_size,
            non_padded_namespaces=non_padded_namespaces,
            tokens_to_add=tokens_to_add,
            padding_token=padding_token,
            oov_token=oov_token,
            recemmended_padding=_recommended_padding
        )

    def _extend(
        self,
        counter: Dict[str, Dict[str, int]] = None,
        min_count: Dict[str, int] = None,
        max_vocab_size: Union[int, Dict[str, int]] = None,
        non_padded_namespaces: Iterable[str] = DEFAULT_NON_PADDED_NAMESPACES,
        pretrained_files: Optional[Dict[str, str]] = None,
        only_include_pretrained_words: bool = False,
        tokens_to_add: Dict[str, List[str]] = None,
        min_pretrained_embeddings: Dict[str, int] = None,
    ) -> None:
        """
        This method is used for extend an already generated vocabulary.
        """
        if not isinstance(max_vocab_size, dict):
            int_max_vocab_size = max_vocab_size
            max_vocab_size = defaultdict(lambda: int_max_vocab_size)  # type: ignore
        min_count = min_count or {}
        pretrained_files = pretrained_files or {}
        min_pretrained_embeddings = min_pretrained_embeddings or {}
        non_padded_namespaces = set(non_padded_namespaces)
        counter = counter or {}
        tokens_to_add = tokens_to_add or {}

        self._retained_counter = counter
        # Make sure vocabulary extension is safe.
        current_namespaces = {*self._token_to_index}
        extension_namespaces = {*counter, *tokens_to_add}

        for namespace in current_namespaces & extension_namespaces:
            # if new namespace was already present
            # Either both should be padded or none should be.
            original_padded = not any(
                namespace_match(pattern, namespace) for pattern in self._non_padded_namespaces
            )
            extension_padded = not any(
                namespace_match(pattern, namespace) for pattern in non_padded_namespaces
            )
            if original_padded != extension_padded:
                raise Exception(
                    "Common namespace {} has conflicting ".format(namespace)
                    + "setting of padded = True/False. "
                    + "Hence extension cannot be done."
                )

        # Add new non-padded namespaces for extension
        self._token_to_index.add_non_padded_namespaces(non_padded_namespaces)
        self._index_to_token.add_non_padded_namespaces(non_padded_namespaces)
        self._non_padded_namespaces.update(non_padded_namespaces)

        for namespace in counter:
            pretrained_set = None
            token_counts = list(counter[namespace].items())
            token_counts.sort(key=lambda x: x[1], reverse=True)
            try:
                max_vocab = max_vocab_size[namespace]
            except KeyError:
                max_vocab = None
            if max_vocab:
                token_counts = token_counts[:max_vocab]
            for token, count in token_counts:
                if pretrained_set is not None:
                    if only_include_pretrained_words:
                        if token in pretrained_set and count >= min_count.get(namespace, 1):
                            self.add_token_to_namespace(token, namespace)
                    elif token in pretrained_set or count >= min_count.get(namespace, 1):
                        self.add_token_to_namespace(token, namespace)
                elif count >= min_count.get(namespace, 1):
                    self.add_token_to_namespace(token, namespace)

        for namespace, tokens in tokens_to_add.items():
            for token in tokens:
                self.add_token_to_namespace(token, namespace)

    def extend_from_instances(
        self, params: ModelConfig, instances: Iterable["adi.Instance"] = ()
    ) -> None:
        """
        Extends an already generated vocabulary using a collection of instances.
        """
        min_count = params.get("min_count", None)
        max_vocab_size = pop_max_vocab_size(params)
        non_padded_namespaces = params.get("non_padded_namespaces", DEFAULT_NON_PADDED_NAMESPACES)
        pretrained_files = params.get("pretrained_files", {})
        min_pretrained_embeddings = params.get("min_pretrained_embeddings", None)
        only_include_pretrained_words = params.get("only_include_pretrained_words", False)
        tokens_to_add = params.get("tokens_to_add", None)


        logger.info("Fitting token dictionary from dataset.")
        namespace_token_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for instance in tqdm.tqdm(instances):
            instance.count_vocab_items(namespace_token_counts)
        self._extend(
            counter=namespace_token_counts,
            min_count=min_count,
            max_vocab_size=max_vocab_size,
            non_padded_namespaces=non_padded_namespaces,
            pretrained_files=pretrained_files,
            only_include_pretrained_words=only_include_pretrained_words,
            tokens_to_add=tokens_to_add,
            min_pretrained_embeddings=min_pretrained_embeddings,
        )

    def is_padded(self, namespace: str) -> bool:
        """
        Returns whether or not there are padding and OOV tokens added to the given namespace.
        """
        return self._index_to_token[namespace][0] == self._padding_token

    def add_token_to_namespace(self, token: str, namespace: str = "tokens") -> int:
        """
        Adds ``token`` to the index, if it is not already present.  Either way, we return the index of
        the token.
        """
        if not isinstance(token, str):
            raise ValueError(
                "Vocabulary tokens must be strings, or saving and loading will break."
                "  Got %s (with type %s)" % (repr(token), type(token))
            )
        if token not in self._token_to_index[namespace]:
            index = len(self._token_to_index[namespace])
            self._token_to_index[namespace][token] = index
            self._index_to_token[namespace][index] = token
            return index
        else:
            return self._token_to_index[namespace][token]

    def add_tokens_to_namespace(self, tokens: List[str], namespace: str = "tokens") -> List[int]:
        """
        Adds ``tokens`` to the index, if they are not already present.
        """
        return [self.add_token_to_namespace(token, namespace) for token in tokens]

    def get_index_to_token_vocabulary(self, namespace: str = "tokens") -> Dict[int, str]:
        return self._index_to_token[namespace]

    def get_token_to_index_vocabulary(self, namespace: str = "tokens") -> Dict[str, int]:
        return self._token_to_index[namespace]

    def get_token_index(self, token: str, namespace: str = "tokens") -> int:
        if token in self._token_to_index[namespace]:
            return self._token_to_index[namespace][token]
        else:
            try:
                return self._token_to_index[namespace][self._oov_token]
            except KeyError:
                logger.error("Namespace: %s", namespace)
                logger.error("Token: %s", token)
                raise

    def get_token_from_index(self, index: int, namespace: str = "tokens") -> str:
        return self._index_to_token[namespace][index]

    def get_vocab_size(self, namespace: str = "tokens") -> int:
        return len(self._token_to_index[namespace])

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return False

    def print_statistics(self) -> None:
        if self._retained_counter:
            logger.info(
                "Printed vocabulary statistics are only for the part of the vocabulary generated from instances. "
            )
            print("\n\n----Vocabulary Statistics----\n")
            # Since we don't saved counter info, it is impossible to consider pre-saved portion.
            for namespace in self._retained_counter:
                tokens_with_counts = list(self._retained_counter[namespace].items())
                tokens_with_counts.sort(key=lambda x: x[1], reverse=True)
                print(f"\nTop 10 most frequent tokens in namespace '{namespace}':")
                for token, freq in tokens_with_counts[:10]:
                    print(f"\tToken: {token}\t\tFrequency: {freq}")
                # Now sort by token length, not frequency
                tokens_with_counts.sort(key=lambda x: len(x[0]), reverse=True)

                print(f"\nTop 10 longest tokens in namespace '{namespace}':")
                for token, freq in tokens_with_counts[:10]:
                    print(f"\tToken: {token}\t\tlength: {len(token)}\tFrequency: {freq}")

                print(f"\nTop 10 shortest tokens in namespace '{namespace}':")
                for token, freq in reversed(tokens_with_counts[-10:]):
                    print(f"\tToken: {token}\t\tlength: {len(token)}\tFrequency: {freq}")
        else:
            # _retained_counter would be set only if instances were used for vocabulary construction.
            logger.info(
                "Vocabulary statistics cannot be printed since dataset instances were not used for its construction."
            )