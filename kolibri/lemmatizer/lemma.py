from kolibri.lemmatizer.fr.french_lefff_lemmatizer import FrenchLefffLemmatizer
from kolibri.lemmatizer.en.formlemmatizer import FormWordNetLematizer

french_lemmatizer = FrenchLefffLemmatizer()
english_lemmatizer = FormWordNetLematizer()


def get_lemmatizer_for_language(language):
    lemmatizer = None
    if language == "fr":
        lemmatizer = french_lemmatizer
    if language == "en":
        lemmatizer = english_lemmatizer

    return lemmatizer
