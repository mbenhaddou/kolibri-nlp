class IStemmer(object):
    """
    A processing interface for removing morphological affixes from
    words.
    """

    def stemWord(self, token):
        """
        :param token: The token to be stemmed.
        :type token: str
        """