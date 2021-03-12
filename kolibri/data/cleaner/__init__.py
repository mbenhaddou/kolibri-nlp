import re
import logging
from kolibri.data.cleaner.email_ import EmailCleaner
from kolibri.data.cleaner.scripts.cleaning_scripts import clean as clean_user_generated_text
#from .email_ import EmailCleaner
logger = logging.getLogger(__name__)


Punctuations_replacement_patterns = [
    # "()" => " () "
    (r"\)", ") "),
    (r"\(", " ("),
    # "[]" => " [] "
    (r"\]", '] '),
    (r"\[", ' ['),

    (r"[ ]{2,}", ' '),  # space more than one
    (r"\n\n", '\n'), # omit repeated new lines!

    # " , " or "," => ", "
    (r" ، ", ', '),
    (r" ،", ', '),
    (r"\s\.\s", '. '),
    (r"\s\.(?!\.) ", '. '),  # not .. or ... just .
    (r"\s\.\.\.", '... '), # omit space if space exist before ...
    # ( ) => ()
    (r"\s\)", ')'),
    (r"\(\s", '('),
    # [ ] => []
    (r"\s\]", ']'),
    (r"\[\s", '['),

    (r"\s:", ':'),# omit space if space exist before :
    (r":(?!\s)", ': ') # add space if space exist before ...
]


patterns = [(re.compile(regex), repl) for (regex, repl) in Punctuations_replacement_patterns]

def fix_punctuations(text):
    s = text
    if s is None:
        return s

    for (pattern, repl) in patterns:
        (s, count) = re.subn(pattern, repl, s)
    return s

