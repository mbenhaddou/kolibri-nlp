from kolibri.pos_tagger import POSTagger
from kolibri.tokenizer.structured_tokenizer import StructuredTokenizer

tagger =POSTagger()
tokeniser=StructuredTokenizer()

tokens=tokeniser.tokenize('Comment allez vous?')
class Doc:
    def __init__(self):
        self.tokens=[]
        self.vector=None


doc=Doc()

doc.tokens=tokens

tags=tagger(doc)


print(tags)