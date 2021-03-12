from kolibri.utils import overlap
import logging

logger = logging.getLogger(__name__)


def bio_tags_from_offsets(tokens, entities):
    entities = sorted(entities, key=lambda k: k[0])
    for token in tokens:
        token.data['tag'] = 'O'

    start = 0
    for ent in entities:
        for i in range(start, len(tokens)):
            if overlap(ent[0], ent[1], tokens[i].start, tokens[i].end):
                tokens[i].data['tag'] = "B-{0}".format(ent[2])
                i = i + 1
                start = i
                while i < len(tokens) and overlap(ent[0], ent[1], tokens[i].start, tokens[i].end):
                    tokens[i].data['tag'] = "I-{0}".format(ent[2])
                    i = i + 1
                    start = i
                break

    return [t.data['tag'] for t in tokens]


def from_json_to_bio(message,  entity_offsets):
    """Convert json examples to format of underlying crfsuite."""


    tokens = message.get("tokens")
    ents = bio_tags_from_offsets(tokens, entity_offsets)

    if '-' in ents:
        logger.warning("Misaligned entity annotation in sentence '{}'. "
                           "Make sure the start and end values of the "
                           "annotated training examples end at token "
                           "boundaries (e.g. don't include trailing "
                           "whitespaces or punctuation)."
                           "".format(message.text))

    return from_text_to_entities(message, ents)

def from_text_to_entities(message, entities=None, pos_features=True):
    crf_format = []
    if pos_features:
        tokens = message.nlp_doc.tokens
    else:
        tokens = message.tokens
    for i, token in enumerate(tokens):
        patterns = __pattern_of_token(message, i)
        entity = entities[i] if entities else "N/A"
        tag = __tag_of_token(token) if pos_features else None
        lemma=token.lemma
        data_tuple=(token.text, tag, entity, lemma)+patterns
        crf_format.append(data_tuple)
    return crf_format


def __pattern_of_token(message, i):
    patterns=()
    if message.tokens is not None:
        for key in message.tokens[i].patterns:
            patterns+=(message.tokens[i].patterns[key],)

    return patterns

def __tag_of_token(token):
    return token.pos