
"""
Corpus readers.  The modules in this package provide functions
that can be used to read dataset fileids in a variety of formats.  These
functions can be used to read both the dataset fileids that are
distributed in the Corpus package, and dataset fileids that are part
of external corpora.
Corpus Reader Functions
=======================
Each dataset module defines one or more "dataset reader functions",
which can be used to read documents from that dataset.  These functions
take an argument, ``item``, which is used to indicate which document
should be read from the dataset:
- If ``item`` is one of the unique identifiers listed in the dataset
  module's ``items`` variable, then the corresponding document will
  be loaded from the Corpus package.
- If ``item`` is a fileid, then that file will be read.
Additionally, dataset reader functions can be given lists of item
names; in which case, they will return a concatenation of the
corresponding documents.
Corpus reader functions are named based on the type of information
they return.  Some common examples, and their return types, are:
- words(): list of str
- sents(): list of (list of str)
- paras(): list of (list of (list of str))
- tagged_words(): list of (str,str) tuple
- tagged_sents(): list of (list of (str,str))
- tagged_paras(): list of (list of (list of (str,str)))
- chunked_sents(): list of (Tree w/ (str,str) leaves)
- parsed_sents(): list of (Tree with str leaves)
- parsed_paras(): list of (list of (Tree with str leaves))
- xml(): A single xml ElementTree
- raw(): unprocessed dataset contents
For example, to read a list of the words in the Brown Corpus, use
``Corpus.brown.words()``:

    The, Fulton, County, Grand, Jury, said, ...
"""

from kolibri.dataset.reader.plaintext import *
from kolibri.dataset.reader.sentiwordnet import *
from kolibri.dataset.reader.twitter import *

from kolibri.dataset.reader.categorized_sents import *
from kolibri.dataset.reader.string_category import *

# Make sure that Corpus.reader.bracket_parse gives the module, not


__all__ = [
    'CorpusReader',
    'CategorizedCorpusReader',
    'PlaintextCorpusReader',
    'SyntaxCorpusReader',
    'EuroparlCorpusReader',
    'CategorizedPlaintextCorpusReader',
    'SentiWordNetCorpusReader',
    'SentiSynset',
    'ListReader',
    'TwitterCorpusReader',
    'CategorizedSentencesCorpusReader'
]