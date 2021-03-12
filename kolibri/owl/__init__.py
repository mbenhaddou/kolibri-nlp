__all__ = [
    'URIRef',
    'BNode',
    'Literal',
    'Ontology',
    'Entity',
    'Class',
    'Individual',
    'Property',
    'ObjectProperty',
    'AnnotationProperty',
    'DataProperty',
    'RDF',
    'RDFS',
    'OWL',
    'XSD'
]

from rdflib import URIRef, BNode, Literal, RDF, RDFS, OWL, XSD

from kolibri.owl.entities import Entity, Class, Individual, Property, ObjectProperty, AnnotationProperty, DataProperty
from kolibri.owl.ontology import Ontology