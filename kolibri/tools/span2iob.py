from kolibri.tokenizer.structured_tokenizer import StructuredTokenizer
import json, operator
from kolibri.utils import overlap

file="/Users/mbenhaddou/Documents/Mentis/Developement/Python/Kolibri/applications/EntityExtraction/data/all_sentences_entities.json"
tokenizer=StructuredTokenizer()
data=json.load(open(file))





for d in data['kolibri_nlu_data']['common_examples']:
    tokens=tokenizer.tokenize(d['text'])
    entities=sorted(d['entities'], key=lambda k: k['start'])
    for token in tokens:
        token.data['tag']='O'

    start=0
    for ent in entities:
        for i in range(start, len(tokens)):
            if overlap(ent['start'], ent['end'], tokens[i].start, tokens[i].end):
                tokens[i].data['tag']= "B-{0}".format(ent['entity'])
                i=i+1
                start=i
                while overlap(ent['start'], ent['end'], tokens[i].start, tokens[i].end):
                    tokens[i].data['tag'] = "I-{0}".format(ent['entity'])
                    i=i+1
                    start=i
                break