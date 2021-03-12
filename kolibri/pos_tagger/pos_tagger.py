from kolibri.pos_tagger import POSTagger
from nltk import pos_tag as nltk_pos_tag


french_tagger=POSTagger()
english_tagger=nltk_pos_tag



def pos_tag(doc, language):
    if language=='fr':
        return french_tagger(doc)
    elif language=='en':
        tags=nltk_pos_tag([t.text for t in doc.tokens])
        for i, t in enumerate(tags):
            doc.tokens[i].pos=t[1]
        return doc

    return doc

