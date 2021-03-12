from typing import Any
from kolibri.data.cleaner.scripts.email2text import EmailMessage
from kolibri.document import Document
from kolibri.pipeComponent import Component


class EmailCleaner(Component):
    name = "email_cleaner"

    provides = ["clean"]

    def __init__(self, config):
        super().__init__(config)
        split_pattern = None
        if "split_pattern" in config:
            split_pattern = config["split_pattern"]
        self.email_parser = EmailMessage(config["language"], split_pattern)

    def train(self, training_data, config, **kwargs):

        for example in training_data.training_examples:
            example.clean = self.clean(example.raw_text)

    def process(self, document, **kwargs):
        # type: (Document, **Any) -> None

        document.clean = self.clean(document.raw_text)

    def clean(self, text):
        cleaned = self.email_parser.read(text)
        cleaned = [fragment.body for fragment in cleaned.fragments]
        text = '. '.join(cleaned)
        return text
