from kolibri.data.dataset_readers.dataset_reader import DatasetReader
from kolibri.data.token_indexers import SingleIdTokenIndexer
from overrides import overrides
from kolibri.data.document import Document
from kolibri.tokenizer.token_ import Token
from kolibri.data.fields import TextField, SequenceLabelField
import json
from kolibri.utils.file import read_file
from kolibri.tokenizer.regex_tokenizer import RegexpTokenizer
from kolibri.entities.entity import Entity

class JSONEntityReader(DatasetReader):

    def __init__(self, token_indexers=None):

        super().__init__(token_indexers or {'tokens': SingleIdTokenIndexer()})

        self.tokenizer=RegexpTokenizer('[0-9]+[\.,]?[0-9]+|[A-Z]\'\w+|[\w]+|[\(\)%$£€&,:\'\.-]')

    @overrides
    def _read(self, file_path: str):
        js = json.loads(read_file(file_path))

        data = js['kolibri_nlu_data']
        instances = data.get("instances", [])
        for ex in instances:
            tokens=self.tokenizer.tokenize(ex["text"])
            entities=[Entity(e["entity"],e["value"],  e["start"], e["end"]) for e in ex["entities"]]
            ner_tags=self._bilou_tags_from_offsets(ex["text"], tokens, entities)
            yield self.text_to_document([t.text for t in tokens], ner_tags)

    def _bilou_tags_from_offsets(self, text, tokens, entities, missing: str = "O") :
        # From spacy.spacy.GoldParse, under MIT License
        starts = {token.start: i for i, token in enumerate(tokens)}
        ends = {token.end: i for i, token in enumerate(tokens)}
        bilou = ["-" for _ in tokens]
        # Handle entity cases
 #       for start_char, end_char, label in entities:
        for entity in entities:
            start_char=entity.start
            end_char=entity.end
            label=entity.type
            start_token = starts.get(start_char)
            end_token = ends.get(end_char)
            # Only interested if the tokenization is correct
            if start_token is not None and end_token is not None:
                if start_token == end_token:
                    bilou[start_token] = "B-%s" % label
                else:
                    bilou[start_token] = "B-%s" % label
                    for i in range(start_token + 1, end_token+1):
                        bilou[i] = "I-%s" % label

        # Now distinguish the O cases from ones where we miss the tokenization
        entity_chars = set()
        for entity in entities:
            start_char=entity.start
            end_char=entity.end
            for i in range(start_char, end_char):
                entity_chars.add(i)
        for n, token in enumerate(tokens):
            for i in range(token.start, token.end):
                if i in entity_chars:
                    break
            else:
                bilou[n] = missing
        if '-' in bilou:
            print(bilou)
        return bilou

    @overrides
    def text_to_document(self, words, ner_tags):
        fields = {}
        # wrap each token in the file with a token object
        tokens = TextField([Token(w) for w in words], self._token_indexers)

        # Instances in AllenNLP are created using Python dictionaries,
        # which map the token key to the Field type
        fields["tokens"] = tokens
        fields["label"] = SequenceLabelField(ner_tags, tokens)

        return Document(fields)

