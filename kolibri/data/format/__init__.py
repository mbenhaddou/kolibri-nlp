import os, logging
import csv

UNK="unknown"
KOLIBRI= "kolibri" #advanced processing of text
MARKDOWN="ms"
JSON="json"
CSV="csv"
logger = logging.getLogger(__name__)


def _guess_format(filename):
    # type: (Text) -> Text
    """Applies heuristics to guess the data format of a file."""
    guess = UNK
    extension = os.path.splitext(filename)[1]

    if extension==".md":
        guess=MARKDOWN
    if extension==".klb":
        guess=KOLIBRI
    if extension==".csv":
        guess=CSV

    return guess



def loadlargefile(filename, file_type='csv', separator=',', chunk_size=1,  encoding='utf-8'):
    if file_type in ['csv', 'txt', 'tsv']:
        with open(filename, encoding=encoding) as file:
            reader=csv.DictReader(file, delimiter=separator)
            chunk=[]
            for i, line in enumerate(reader):
                if (i % chunk_size==0 and i>0):
                    yield chunk
                    chunk = []
                chunk.append(line)

    else:
        raise NotImplementedError("file type not yet supported")