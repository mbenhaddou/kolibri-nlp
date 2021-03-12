"""
Tokenizer Interface
"""

from kolibri.pipeComponent import Component

class Tokenizer(Component):
    def __init__(self, config):
        super().__init__(config)
        self.tokenizer=None

