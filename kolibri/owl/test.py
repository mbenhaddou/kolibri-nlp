__author__ = 'joshhanna'

from kolibri.owl.ontology import Ontology
from rdflib import URIRef

#TODO: convert to actual tests

ont = Ontology()
print("loading bfo")
ont.load(location="/Users/mohamedmentis/Documents/Mentis/Development/Python/NGA/nga_entities_api/extractor/intents.ttl")

cl=ont.get_class(match='Date')

for cls in ont.classes:
    if cls.is_named():
        print("cls:", cls.uri)
        for s, p, o in cls.triples:
            print(s, p, o)

        print("parents")
        for child in cls.parents:
            print(child.uri)


