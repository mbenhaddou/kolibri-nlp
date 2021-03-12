
from string import ascii_lowercase

from rdflib import Literal
from rdflib.namespace import  RDFS, RDF, OWL, XSD
from six import string_types
from six.moves.urllib.parse import urlparse
from rdflib import Literal
from six import string_types
import rdflib


NAMESPACES_DEFAULT = [
    ("rdf", rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#")),
    ("rdfs", rdflib.URIRef("http://www.w3.org/2000/01/rdf-schema#")),
    ("xml", rdflib.URIRef("http://www.w3.org/XML/1998/namespace")),
    ("xsd", rdflib.URIRef("http://www.w3.org/2001/XMLSchema#")),
    ('foaf', rdflib.URIRef("http://xmlns.com/foaf/0.1/")),
    ("skos", rdflib.URIRef( "http://www.w3.org/2004/02/skos/core#")),
    ("owl", rdflib.URIRef("http://www.w3.org/2002/07/owl#")),
]


# Default tag to use as a language tag for literal assigments of text strings
DEFAULT_LANGUAGE_TAG = "en"

# These are all the Python types which are considered valid to be used directly
# as assigments on Literal properties (of type rdfs:Literal)
LITERAL_PRIMITIVE_TYPES = string_types + (
    Literal,
    int,
    float,
    bool,
)

COMMON_PROPERTY_URIS = (
    OWL.AnnotationProperty,
    OWL.AsymmetricProperty,
    OWL.DatatypeProperty,
    OWL.DeprecatedProperty,
    OWL.FunctionalProperty,
    OWL.InverseFunctionalProperty,
    OWL.IrreflexiveProperty,
    OWL.ObjectProperty,
    OWL.OntologyProperty,
    OWL.ReflexiveProperty,
    OWL.SymmetricProperty,
    OWL.TransitiveProperty,
    RDF.Property,
)



def is_in_namespace(uri, base_uri):
    """
    Check if given URI is in the "namespace" of the given base URI

    """
    if any((
        base_uri.endswith("#"),
        base_uri.endswith("/")
    )):
        # We chop off last character of base uri as that typically can include a
        # backslash (/) or a fragment (#) character.
        base_uri = base_uri[:-1]
    return uri.startswith(base_uri)


def is_a_class(uri):
    return uri in (
        RDFS.Class,
        OWL.Class,
    )


def is_a_property(uri):
    return uri in COMMON_PROPERTY_URIS


def is_a_property_subtype(uri, type_graph=None):
    return any((
        type_graph and is_a_property(type_graph.get(uri)),
        could_be_a_property_uri(uri),
    ))


def is_a_list(uri):
    return uri in (
        RDFS.List,
    )


def is_a_literal(uri):
    return (uri in (RDFS.Literal,) or
            uri.startswith(XSD))


def is_literal_value(value):
    return (
        isinstance(value, Literal) or
        isinstance(value, string_types)
    )



def is_comment_predicate(predicate):
    return predicate in (
        RDFS.comment,
    )


def is_domain_predicate(predicate):
    return predicate in (
        RDFS.domain,
    )


def is_label_predicate(predicate):
    return predicate in (
        RDFS.label,
    )


def is_range_predicate(predicate):
    return predicate in (
        RDFS.range,
    )


def is_type_predicate(predicate):
    return predicate in (
        RDFS.type,
    )


def is_sub_class_predicate(predicate):
    return predicate in (
        RDFS.subClassOf, OWL.subClassOf
    )


def is_sub_property_predicate(predicate):
    return predicate in (
        RDFS.subPropertyOf, OWL.subPropertyOf
    )


def could_be_a_property_uri(uri):
    """
    Heuristic for checking if a given URI "looks like" a Property type or an Class type.
    by cheking if first letter is lower case (This is a Convention)

    """
    name = urlparse(uri).path
    return name[0] in ascii_lowercase


def uri2niceString(aUri, namespaces=None):
    """
    From a URI, returns a nice string representation that uses also the namespace symbols
    Cuts the uri of the namespace, and replaces it with its shortcut (for base, attempts to infer it or leaves it blank)

    Namespaces are a list

    [('xml', rdflib.URIRef('http://www.w3.org/XML/1998/namespace'))
    ('', rdflib.URIRef('http://cohereweb.net/ontology/cohere.owl#'))
    (u'owl', rdflib.URIRef('http://www.w3.org/2002/07/owl#'))
    ('rdfs', rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#'))
    ('rdf', rdflib.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#'))
    (u'xsd', rdflib.URIRef('http://www.w3.org/2001/XMLSchema#'))]

    """
    if not namespaces:
        namespaces = NAMESPACES_DEFAULT

    if not aUri:
        stringa = ""
    elif type(aUri) == rdflib.term.URIRef:
        # we have a URI: try to create a qName
        stringa = aUri.toPython()
        for aNamespaceTuple in namespaces:
            try:  # check if it matches the available NS
                if stringa.find(aNamespaceTuple[1].__str__()) == 0:
                    if aNamespaceTuple[0]:  # for base NS, it's empty
                        stringa = aNamespaceTuple[0] + ":" + stringa[len(
                            aNamespaceTuple[1].__str__()):]
                    else:
                        prefix = inferNamespacePrefix(aNamespaceTuple[1])
                        if prefix:
                            stringa = prefix + ":" + stringa[len(
                                aNamespaceTuple[1].__str__()):]
                        else:
                            stringa = ":" + stringa[len(aNamespaceTuple[1].
                                                        __str__()):]
            except:
                stringa = "error"

    elif type(aUri) == rdflib.term.Literal:
        stringa = "\"%s\"" % aUri  # no string casting so to prevent encoding errors
    else:
        # print(type(aUri))
        if type(aUri) == type(u''):
            stringa = aUri
        else:
            stringa = aUri.toPython()
    return stringa



def uri2niceString(aUri, namespaces=None):
    """
    From a URI, returns a nice string representation that uses also the namespace symbols
    Cuts the uri of the namespace, and replaces it with its shortcut (for base, attempts to infer it or leaves it blank)

    Namespaces are a list

    [('xml', rdflib.URIRef('http://www.w3.org/XML/1998/namespace'))
    ('', rdflib.URIRef('http://cohereweb.net/ontology/cohere.owl#'))
    (u'owl', rdflib.URIRef('http://www.w3.org/2002/07/owl#'))
    ('rdfs', rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#'))
    ('rdf', rdflib.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#'))
    (u'xsd', rdflib.URIRef('http://www.w3.org/2001/XMLSchema#'))]

    """
    if not namespaces:
        namespaces = NAMESPACES_DEFAULT

    if not aUri:
        stringa = ""
    elif type(aUri) == rdflib.term.URIRef:
        # we have a URI: try to create a qName
        stringa = aUri.toPython()
        for aNamespaceTuple in namespaces:
            try:  # check if it matches the available NS
                if stringa.find(aNamespaceTuple[1].__str__()) == 0:
                    if aNamespaceTuple[0]:  # for base NS, it's empty
                        stringa = aNamespaceTuple[0] + ":" + stringa[len(
                            aNamespaceTuple[1].__str__()):]
                    else:
                        prefix = inferNamespacePrefix(aNamespaceTuple[1])
                        if prefix:
                            stringa = prefix + ":" + stringa[len(
                                aNamespaceTuple[1].__str__()):]
                        else:
                            stringa = ":" + stringa[len(aNamespaceTuple[1].
                                                        __str__()):]
            except:
                stringa = "error"

    elif type(aUri) == rdflib.term.Literal:
        stringa = "\"%s\"" % aUri  # no string casting so to prevent encoding errors
    else:
        # print(type(aUri))
        if type(aUri) == type(u''):
            stringa = aUri
        else:
            stringa = aUri.toPython()
    return stringa


def niceString2uri(aUriString, namespaces=None):
    """
    From a string representing a URI possibly with the namespace qname, returns a URI instance.

    gold:Citation  ==> rdflib.term.URIRef(u'http://purl.org/linguistics/gold/Citation')

    Namespaces are a list

    [('xml', rdflib.URIRef('http://www.w3.org/XML/1998/namespace'))
    ('', rdflib.URIRef('http://cohereweb.net/ontology/cohere.owl#'))
    (u'owl', rdflib.URIRef('http://www.w3.org/2002/07/owl#'))
    ('rdfs', rdflib.URIRef('http://www.w3.org/2000/01/rdf-schema#'))
    ('rdf', rdflib.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#'))
    (u'xsd', rdflib.URIRef('http://www.w3.org/2001/XMLSchema#'))]

    """

    if not namespaces:
        namespaces = []

    for aNamespaceTuple in namespaces:
        if aNamespaceTuple[0] and aUriString.find(
                aNamespaceTuple[0].__str__() + ":") == 0:
            aUriString_name = aUriString.split(":")[1]
            return rdflib.term.URIRef(aNamespaceTuple[1] + aUriString_name)

    # we dont handle the 'base' URI case
    return rdflib.term.URIRef(aUriString)

def inferNamespacePrefix(aUri):
    """
    From a URI returns the last bit and simulates a namespace prefix when rendering the ontology.

    eg from <'http://www.w3.org/2008/05/skos#'>
        it returns the 'skos' string
    """
    stringa = aUri.__str__()
    try:
        prefix = stringa.replace("#", "").split("/")[-1]
    except:
        prefix = ""
    return prefix
