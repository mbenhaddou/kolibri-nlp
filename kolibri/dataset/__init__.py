from .lazycorpusloader import LazyCorpusLoader
from .reader import *
from kolibri.dataset.utils import read_line_block
abc = LazyCorpusLoader(
    'abc',
    PlaintextCorpusReader,
    r'(?!\.).*\.txt'
)
ap = LazyCorpusLoader(
    'ap',
    PlaintextCorpusReader,
    r'(?!\.).*\.txt'
)
nips = LazyCorpusLoader(
    'nips',
    PlaintextCorpusReader,
    r'(?!\.).*\.txt'
)
nsf = LazyCorpusLoader(
    'nsf',
    PlaintextCorpusReader,
    r'(?!\.).*\.txt'
)

nyt = LazyCorpusLoader(
    'nyt',
    PlaintextCorpusReader,
    r'(?!\.).*\.txt'
)
machinelearning = LazyCorpusLoader(
    'machinelearning',
    PlaintextCorpusReader,
    r'(?!\.).*\.txt'
)

gutenberg = LazyCorpusLoader(
    'gutenberg', PlaintextCorpusReader, r'(?!\.).*\.txt', encoding='latin1'
)
inaugural = LazyCorpusLoader(
    'inaugural', PlaintextCorpusReader, r'(?!\.).*\.txt', encoding='latin1'
)

movie_reviews = LazyCorpusLoader(
    'movie_reviews',
    CategorizedPlaintextCorpusReader,
    r'(?!\.).*\.txt',
    cat_pattern=r'(neg|pos)/.*',
)



qc = LazyCorpusLoader(
    'qc', ListReader, ['train.txt', 'test.txt'], encoding='ISO-8859-2'
)

reuters = LazyCorpusLoader(
    'reuters',
    CategorizedPlaintextCorpusReader,
    '(training|test).*',
    cat_file='cats.txt',
    encoding='ISO-8859-2',
)
sentence_polarity = LazyCorpusLoader(
    'sentence_polarity',
    CategorizedSentencesCorpusReader,
    r'rt-polarity\.(neg|pos)',
    cat_pattern=r'rt-polarity\.(neg|pos)',
    encoding='utf-8',
)

wikipedia = LazyCorpusLoader(
    'wikipedia',
    PlaintextCorpusReader,
    r'(?!\.).*\.txt',
    para_block_reader= read_line_block,
)


state_union = LazyCorpusLoader(
    'state_union', PlaintextCorpusReader, r'(?!\.).*\.txt', encoding='ISO-8859-2'
)

subjectivity = LazyCorpusLoader(
    'subjectivity',
    CategorizedSentencesCorpusReader,
    r'(quote.tok.gt9|plot.tok.gt9)\.5000',
    cat_map={'quote.tok.gt9.5000': ['subj'], 'plot.tok.gt9.5000': ['obj']},
    encoding='latin-1',
)
treebank_raw = LazyCorpusLoader(
    'treebank/raw', PlaintextCorpusReader, r'wsj_.*', encoding='ISO-8859-2'
)
twitter_samples = LazyCorpusLoader('twitter_samples', TwitterCorpusReader, '.*\.json')
udhr2 = LazyCorpusLoader('udhr2', PlaintextCorpusReader, r'.*\.txt', encoding='utf8')
webtext = LazyCorpusLoader(
    'webtext', PlaintextCorpusReader, r'(?!README|\.).*\.txt', encoding='ISO-8859-2'
)




if __name__ == '__main__':
    # demo()
    pass

# ** this is for nose **
# unload all dataset after tests
def teardown_module(module=None):
    import nltk.corpus

    for name in dir(nltk.corpus):
        obj = getattr(nltk.corpus, name, None)
        if isinstance(obj, CorpusReader) and hasattr(obj, '_unload'):
            obj._unload()