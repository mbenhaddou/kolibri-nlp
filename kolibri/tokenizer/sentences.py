# pylint: disable=W0212

"""Sentence segmentation for English.

This module implements sentence segmentation in English using simple
machine learning classifiers.

Todo:
  * Standardize model (re-)generation
"""

# Imports
import os
import re
from typing import Tuple, List, Generator, Any, Union
from .SentenceTokenizer import split_multi




# Setup module path
MODULE_PATH = os.path.dirname(os.path.abspath(__file__))

extra_abbreviations = ['no', 'l']

PRE_PROCESS_TEXT_REMOVE = re.compile(
    r'(?:^\s*\d+\s*$)'
    r'|(?:^\s*\<PAGE\>\s*(\d+)?\s*(\n|$))'
    r'|(?:^\s*(^.+)?[Pp][Aa][Gg][Ee]\s+\d+\s+[Oo][Ff]\s+\d+(.+)?$\s*(\n|$))'
    r'|(?:^\s+$)'
    r'|(?:^\s*i+\s*$)',
    re.MULTILINE
)

# '|'-separated templates of the sequences splitting sentences.
SENTENCE_SPLITTERS = re.compile(
    r'(?<=\n)\s*\n'  # Blank line - usually separates one sentence from another
    r'|(?<=\n)\S+.*[ \t.]{5,200}\S.+\S\s*(?=\n)'  # Something:       separated with spaces
)

SENTENCE_SPLITTERS_LOWER_EXCLUDE = re.compile(
    r'(?:\s*and\s*)'
)

STRIP_GROUP = re.compile(r'^\s*(\S.*?)\s*$', re.DOTALL)


def pre_process_document(text: str) -> str:
    """
    Pre-process text of the specified document before splitting it to the sentences.
    Removes obsolete formatting, page-splitting markers, page numbers e.t.c.
    :param text:
    :return:
    """
    if not text:
        return text
    return PRE_PROCESS_TEXT_REMOVE.sub('', text)


def _trim_span(text: str, span: Tuple[int, int]) -> Union[None, Tuple[int, int]]:
    span_text = text[span[0]: span[1]]
    m = STRIP_GROUP.search(span_text)
    if m:
        new_span = m.span(1)
        return span[0] + new_span[0], span[0] + new_span[1]

    return None


def post_process_sentence(sent):

    return sent.replace('\n', ' ')



def get_sentence_list(text):
    """
    Get sentences from text.
    :param text:
    :return:
    """
    processed_sentences=[]
    sentences=split_multi(text)
    for sent in sentences:
        processed_sentences.append(post_process_sentence(sent))
    return processed_sentences


def get_sentence_span(text) -> Generator[Tuple[int, int, str], Any, Any]:
    """
    Given a text, returns a list of the (start, end) spans of sentences
    in the text.
    """
    for span in split_multi(text):
        yield from post_process_sentence(span)


def get_sentence_span_list(text) -> List[Tuple[int, int, str]]:
    """
    Given a text, generates (start, end) spans of sentences
    in the text.
    """
    return list(get_sentence_span(text))


