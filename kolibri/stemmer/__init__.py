from kolibri.stemmer.nl import DutchStemmer
from nltk.stem import SnowballStemmer
from kolibri.utils import iso_language

class WordStemer:
    def __init__(self, language='english'):
        language=iso_language.language_name(language).lower()
        if language=='dutch':
            self.stemmer=DutchStemmer()
        else:
            self.stemmer=SnowballStemmer(language)


    def stem(self, word):
         return self.stemmer.stemWord(word)


    def stemDoc(self, doc):
        for tok in doc.tokens:
            tok.stem=self.stemmer.stem(tok.text)

        return doc
