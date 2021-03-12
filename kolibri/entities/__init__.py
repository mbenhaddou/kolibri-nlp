from typing import Any
from typing import Dict
from typing import List
from typing import Text

from kolibri.pipeComponent import Component
from kolibri.document import Document
from seqeval.metrics.sequence_labeling import get_entities
import numpy as np


class EntityExtractor(Component):
    def add_extractor_name(self, entities):
        for entity in entities:
            entity["extractor"] = self.name
        return entities

    def add_processor_name(self, entity):
        # type: (Dict[Text, Any]) -> Dict[Text, Any]
        if "processors" in entity:
            entity["processors"].append(self.name)
        else:
            entity["processors"] = [self.name]

        return entity

    @staticmethod
    def find_entity(ent, text, tokens):
        offsets = [token.offset for token in tokens]
        ends = [token.end for token in tokens]

        if ent["start"] not in offsets:
            message = ("Invalid entity {} in example '{}': "
                       "entities must span whole tokens. "
                       "Wrong entity start.".format(ent, text))
            raise ValueError(message)

        if ent["end"] not in ends:
            message = ("Invalid entity {} in example '{}': "
                       "entities must span whole tokens. "
                       "Wrong entity end.".format(ent, text))
            raise ValueError(message)

        start = offsets.index(ent["start"])
        end = ends.index(ent["end"]) + 1
        return start, end

    def filter_trainable_entities(self, entity_examples):
        # type: (List[Document]) -> List[Document]
        """Filters out untrainable entity annotations.

        Creates a copy of entity_examples in which entities that have
        `extractor` set to something other than self.name (e.g. 'ner_crf')
        are removed."""

        filtered = []
        for message in entity_examples:
            entities = []
            for ent in message.get("entities", []):
                extractor = ent.get("extractor")
                if not extractor or extractor == self.name:
                    entities.append(ent)
            data = message.copy()
            data['entities'] = entities
            filtered.append(
                Document(text=message.text,
                        data=data,
                        output_properties=message.output_properties,
                        time=message.time))

        return filtered
    def _build_response(self, sent, tags, prob):
        res = []
        words=[t.text for t in sent.tokens]
        chunks = get_entities(tags)

        for chunk_type, chunk_start, chunk_end in chunks:
            chunk_end += 1
            entity = {
                'value': ' '.join(words[chunk_start: chunk_end]),
                'type': chunk_type,
                'score': float(np.average(prob[chunk_start: chunk_end])),
                'beginOffset': chunk_start,
                'endOffset': chunk_end,
                'start': sent.tokens[chunk_start].start,
                'end': sent.tokens[chunk_end-1].end
            }
            res.append(entity)

        return res
