from kolibri.pipeComponent import Component
import numpy as np
class Features(Component):

    def __init__(self, config):
        super().__init__(config)
        self.vectorizer=None

    @staticmethod
    def _combine_with_existing_features(document,
                                             additional_features):
        if document.get("text_features") is not None:
            return np.hstack((document.get("text_features"),
                              additional_features))
        else:
            return additional_features