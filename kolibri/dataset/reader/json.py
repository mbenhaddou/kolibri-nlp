"""
Read tuples from a dataset consisting of categorized strings.
For example, from the question classification dataset:
NUM:dist How far is it from Denver to Aspen ?
LOC:city What county is Modesto , California in ?
HUM:desc Who was Galileo ?
DESC:def What is an atom ?
NUM:date When did Hawaii become a state ?
"""

from kolibri.dataset.corpusreader import CorpusReader, concat, StreamBackedCorpusView
from kolibri.dataset.utils import read_csv_line_block

# [xx] Should the order of the tuple be reversed -- in most other places
# in nltk, we use the form (data, tag) -- e.g., tagged words and
# labeled texts for classifiers.
class JSonReader(CorpusReader):
    def __init__(self, root,
                 fileids,
                 delimiter=' ',
                 encoding='utf8'
                 ):
        """
        :param root: The root directory for this dataset.
        :param fileids: A list or regexp specifying the fileids in this dataset.
        :param delimiter: Field delimiter
        """

        CorpusReader.__init__(self, root, fileids, encoding)
        self._delimiter = delimiter
        self._para_block_reader = read_csv_line_block

    def tuples(self, fileids=None):
        if fileids is None:
            fileids = self._fileids
        elif isinstance(fileids, str):
            fileids = [fileids]
        return concat(
            [
                StreamBackedCorpusView(fileid, self._para_block_reader, encoding=enc)
                for (fileid, enc) in self.abspaths(fileids, True)
            ]
        )

    def raw(self, fileids=None):
        """
        :return: the text contents of the given fileids, as a single string.
        """
        if fileids is None:
            fileids = self._fileids
        elif isinstance(fileids, str):
            fileids = [fileids]
        return concat([self.open(f).read() for f in fileids])

