from lemminflect import getLemma
from kolibri.lemmatizer.lemmatizer import Lemmatizer

TOGSET_DIC={
    'JJ':'ADJ',
    'JJR':'ADJ',
    'JJS':'ADJ',
    'RB':'ADV',
    'RBR':'ADV',
    'RBS':'ADV',
    'NN':'NOUN',
    'NNS':'NOUN',
    'NNP':'PROPN',
    'NNPS':'PROPN',
'VB':'VERB',
'VBD':'VERB',
'VBG':'VERB',
'VBN':'VERB',
'VBP':'VERB',
'VBZ':'VERB',
'MD':'VERB'
}



def pos_code(tag):
    if tag in TOGSET_DIC:
        return TOGSET_DIC[tag]

class FormWordNetLematizer(Lemmatizer):


    def lemmatize(self, doc):

        for tok in doc.tokens:
            word=tok.text
            tok.lemma = word
            pos=pos_code(tok.pos)
            if pos:
                lemma=getLemma(word, upos=pos)
                if len(lemma)>0:
                    tok.lemma=lemma[0]


        return doc


