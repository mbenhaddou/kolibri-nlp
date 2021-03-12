__author__ = 'mohamedbenhaddou'

import string


class Token(object):
    def __init__(self, text, start=-1, index=-1, data=None, lemma=None, pos=None, entity=None):
        self.index=index
        self.start = start
        self.text = text
        self.end = start + len(text)
        self.abstract=None
        self.data = data if data else {}
        self.lemma=lemma
        self.pos=pos
        self.tag=None
        self.entity=entity
        self.is_stopword=False
        self.patterns={}

    def set(self, prop, info):
        self.data[prop] = info

    def get(self, prop, default=None):
        return self.data.get(prop, default)

    def tojson(self):
        return {"index": self.index, "text": self.text, "lemma": self.lemma, "pos": self.pos, "entity": self.entity}


class Tokens(list):

    def addToken(self, token):
        list.append(token)


    def get_tokens_as_strings(self, removePunctuations=True):
        if removePunctuations:
            return [t.value for t in self if t.value not in string.punctuation]
        return [t.value for t in self if t.value]
