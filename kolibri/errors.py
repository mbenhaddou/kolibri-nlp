
from typing import Text

class MissingArgumentError(ValueError):
    """Raised when a function is called and not all parameters can be
    filled from the context / config.

    Attributes:
        document -- explanation of which parameter is missing
    """

    def __init__(self, document):
        # type: (Text) -> None
        super(MissingArgumentError, self).__init__(document)
        self.document = document

    def __str__(self):
        return self.document


class UnsupportedLanguageError(Exception):
    """Raised when a component is created but the language is not supported.

    Attributes:
        component -- component name
        language -- language that component doesn't support
    """

    def __init__(self, component, language):
        # type: (Text, Text) -> None
        self.component = component
        self.language = language

        super(UnsupportedLanguageError, self).__init__(component, language)

    def __str__(self):
        return "component {} does not support language {}".format(
            self.component, self.language
        )


class InvalidConfigError(ValueError):
    """Raised if an invalid configuration is encountered."""

    def __init__(self, message):
        # type: (Text) -> None
        super(InvalidConfigError, self).__init__(message)


class InvalidProjectError(Exception):
    """Raised when a model failed to load.

    Attributes:
        document -- explanation of why the model is invalid
    """

    def __init__(self, document):
        self.document = document

    def __str__(self):
        return self.document


class UnsupportedModelError(Exception):
    """Raised when a model is too old to be loaded.

    Attributes:
        document -- explanation of why the model is invalid
    """

    def __init__(self, document):
        self.document = document

    def __str__(self):
        return self.document
