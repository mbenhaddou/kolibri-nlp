import regex as re
from kolibri.tokenizer.tokenizer import Tokenizer
from kolibri.tokenizer.token_ import *
from kolibri.stopwords import get_stop_words

class RegexpTokenizer(Tokenizer):
    """
    A tokenizer that splits a string using a regular expression, which
    matches either the tokens or the separators between tokens.
    By default, the following flags are
        used: `re.UNICODE | re.MULTILINE | re.DOTALL`.
    """

    def __init__(self, pattern, config=None, discard_empty=True, flags=re.UNICODE | re.MULTILINE):
        # If they gave us a regexp object, extract the patterns.
        super().__init__(config)
        pattern = getattr(pattern, 'patterns', pattern)

        self._pattern = pattern
        self._discard_empty = discard_empty
        self._flags = flags
        self._regexp = None

        self.stopwords = None
        if "language" in config:
            self.language=config['language']
            self.stopwords=get_stop_words(self.language)
    def _check_regexp(self):
        if self._regexp is None:
            self._regexp = re.compile(self._pattern, self._flags)

    def tokenize(self, text):
        self._check_regexp()
        # If our regexp matches gaps, use re.split:
        words= self._regexp.findall(text)

        running_offset = 0
        tokens = Tokens()
        for i, word in enumerate(words):
            word_offset = text.index(word, running_offset)
            word_len = len(word)
            running_offset = word_offset + word_len
            token=Token(text=word, start=word_offset, index=i)
            if self.stopwords:
                token.is_stopword=word.lower() in self.stopwords
            tokens.append(token)
        return tokens



if __name__=='__main__':
    text=""""Please add the 'Statutory > NL-Sick Leave' => See table below.
    Company
    UPI
    Legal Name - Last Name
    Preferred Name - First Name
    Type of Leave
    Start of Leave
    Estimated Last Day of Leave
    Actual Last Day of Leave
    6079 AbbVie BV Commercial
    10373417
    Bosua
    Rosanna
    Statutory > NL-Sick Leave
    29-APR-2019
    28-APR-2020
    6079 AbbVie BV Commercial
    10355526
    Scholtes
    Monique
    Statutory > NL-Sick Leave
    26-NOV-2018
    25-NOV-2019
    Thanks!
    Met vriendelijke groet"""


    tokenizer=RegexpTokenizer('[\w$£€]+|[\(\)%]', config={'language':'en'})
    tokens=tokenizer.tokenize(text)
    for t in tokens:
        print(t.text)