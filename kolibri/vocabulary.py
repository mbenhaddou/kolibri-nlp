import os
from collections import Counter, defaultdict
from six import string_types, iteritems, itervalues

class Vocabulary(object):
    """A vocabulary that maps tokens to ints (storing a vocabulary).

    Attributes:
        _token_count: A collections.Counter object holding the frequencies of tokens
            in the data used to build the Vocabulary.
        token2id: A collections.defaultdict instance mapping token strings to
            numerical identifiers.
        _id2token: A list of token strings indexed by their numerical identifiers.
    """

    def __init__(self, max_size=None, lower=True, unk_token=True, remove_stopwords=False, specials=('<pad>',)):
        """Create a Vocabulary object.

        Args:
            max_size: The maximum size of the vocabulary, or None for no
                maximum. Default: None.
            lower: boolean. Whether to convert the texts to lowercase.
            unk_token: boolean. Whether to add unknown token.
            specials: The list of special tokens (e.g., padding or eos) that
                will be prepended to the vocabulary. Default: ('<pad>',)
        """
        self._max_size = max_size
        self._lower = lower
        self._unk = unk_token
        self.token2id = {token: i for i, token in enumerate(specials)}
        self._id2token = list(specials)
        self._token_count = Counter()
        self.can_remove_stopwords=remove_stopwords
        self.num_docs = 0
        self.num_pos = 0
        self.num_nnz = 0
        self.corpus=None
    def __len__(self):
        return len(self.token2id)

    def add_token(self, token):
        """Add token to vocabulary.

        Args:
            token (str): token to add.
        """
        token = self.process_token(token)
        self._token_count.update([token])


    def add_documents(self, docs):
        """Update dictionary from a collection of documents. Each document is a list
        of tokens.

        Args:
            docs (list): documents to add.
        """
        if 'sentences' in docs:
            for sent in docs.sentences:
                sent = map(self.process_token, [t for t in sent.tokens if not t.is_stopword])
                self._token_count.update(sent)

        else:
            sent = list(map(self.process_token,  [t for t in docs.tokens if not t.is_stopword]))
            self._token_count.update(sent)

    def add_document_lists(self, docs):
        """Update dictionary from a collection of documents. Each document is a list
        of tokens.

        Args:
            docs (list): documents to add.
        """
        for sent in docs:
            sent = map(self.process_token, sent)
            self._token_count.update(sent)

    def add_training_data(self, data):
        for example in data.training_examples:
            self.add_documents(example)

        return
    def doc2id(self, doc):
        """Get the list of token_id given doc.

        Args:
            doc (list): document.

        Returns:
            list: int id of doc.
        """
        if isinstance(doc, string_types):
            raise TypeError("doc2idx expects an array of unicode tokens on input, not a single string")
        doc = map(self.process_token, doc)
        return [self.token_to_id(token) for token in doc]

    def id2doc(self, ids):
        """Get the token list.

        Args:
            ids (list): token ids.

        Returns:
            list: token list.
        """
        return [self.id_to_token(idx) for idx in ids]


    def doc2bow(self, document, allow_update=False, return_missing=False):
        """Convert `document` into the bag-of-words (BoW) format = list of `(token_id, token_count)` tuples.

        Parameters
        ----------
        doc : list of str
            Input document.
        allow_update : bool, optional
            Update self, by adding new tokens from `document` and updating internal corpus statistics.
        return_missing : bool, optional
            Return missing tokens (tokens present in `document` but not in self) with frequencies?

        Return
        ------
        list of (int, int)
            BoW representation of `document`.
        list of (int, int), dict of (str, int)
            If `return_missing` is True, return BoW representation of `document` + dictionary with missing
            tokens and their frequencies.

        """

        doc=[t.text for t in document.tokens]

        if isinstance(doc, string_types):
            raise TypeError("doc2bow expects an array of unicode tokens on input, not a single string")

        # Construct (word, frequency) mapping.
        counter = defaultdict(int)
        for w in doc:
            counter[w if isinstance(w, str) else str(w, 'utf-8')] += 1

        token2id = self.token2id
        if allow_update or return_missing:
            missing = sorted(x for x in iteritems(counter) if x[0] not in token2id)
            if allow_update:
                for w, _ in missing:
                    # new id = number of ids made so far;
                    # NOTE this assumes there are no gaps in the id sequence!
                    token2id[w] = len(token2id)
        result = {token2id[w]: freq for w, freq in iteritems(counter) if w in token2id}

        if allow_update:
            self.num_docs += 1
            self.num_pos += sum(itervalues(counter))
            self.num_nnz += len(result)
            # keep track of document and collection frequencies
            for tokenid, freq in iteritems(result):
                self.cfs[tokenid] = self.cfs.get(tokenid, 0) + freq
                self.dfs[tokenid] = self.dfs.get(tokenid, 0) + 1

        # return tokenids, in ascending id order
        result = sorted(iteritems(result))
        if return_missing:
            return result, dict(missing)
        else:
            return result


    def build(self):
        """
        Build vocabulary.
        """
        token_freq = self._token_count.most_common(self._max_size)
        idx = len(self.vocab)
        for token, _ in token_freq:
            self.token2id[token] = idx
            self._id2token.append(token)
            idx += 1
        if self._unk:
            unk = '<unk>'
            self.token2id[unk] = idx
            self._id2token.append(unk)

        self.id2token={v:k for k, v in self.token2id.items()}

    def process_token(self, token):
        """Process token before following methods:
        * add_token
        * add_documents
        * doc2id
        * token_to_id

        Args:
            token (str): token to process.

        Returns:
            str: processed token string.
        """

        if isinstance(token, str):
            token_text=token
        else:
            token_text = token.text
        if self._lower:
            token_text = token_text.lower()

        return token_text

    def token_to_id(self, token):
        """Get the token_id of given token.

        Args:
            token (str): token from vocabulary.

        Returns:
            int: int id of token.
        """
        token = self.process_token(token)
        return self.token2id.get(token, len(self.token2id) - 1)

    def id_to_token(self, idx):
        """token-id to token (string).

        Args:
            idx (int): token id.

        Returns:
            str: string of given token id.
        """
        return self._id2token[idx]

    @property
    def vocab(self):
        """Return the vocabulary.

        Returns:
            dict: get the dict object of the vocabulary.
        """
        return self.token2id

    @property
    def count(self):
        return len(self.token2id)
    @property
    def reverse_vocab(self):
        """Return the vocabulary as a reversed dict object.

        Returns:
            dict: reversed vocabulary object.
        """
        return self._id2token


