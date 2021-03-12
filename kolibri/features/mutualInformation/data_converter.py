from collections import Counter
from kolibri.features.mutualInformation.models import SetDocumentInformation, PersistentDict
from sklearn.feature_extraction import DictVectorizer
from typing import Dict, List, Tuple, Any, Union
import joblib
import itertools



def generate_document_dict(document_key:str,
                           documents:List[Union[List[str], Tuple[Any]]])->Tuple[str,Counter]:
    """This function gets Document-frequency count in given list of documents
    """
    assert isinstance(documents, list)
    feature_frequencies = [Counter(document) for document in documents]
    document_frequencies = Counter()
    for feat_freq in feature_frequencies: document_frequencies.update(feat_freq.keys())

    return (document_key, document_frequencies)


def make_multi_docs2term_freq_info(labeled_documents):
    """* What u can do
    - This function generates information to construct term-frequency matrix
    """

    counted_frequency = [(label, Counter(list(itertools.chain.from_iterable(documents))))
                         for label, documents in labeled_documents.items()]
    feature_documents = [dict(label_freqCounter_tuple[1]) for label_freqCounter_tuple in counted_frequency]



    dict_matrix_index = {}

    # use sklearn feature-extraction
    vec = DictVectorizer()
    dict_matrix_index['matrix_object'] = vec.fit_transform(feature_documents).tocsr()
    dict_matrix_index['feature2id'] = {feat:feat_id for feat_id, feat in enumerate(vec.get_feature_names())}
    dict_matrix_index['label2id'] = {label_freqCounter_tuple[0]:label_id for label_id, label_freqCounter_tuple in  enumerate(counted_frequency)}

    return SetDocumentInformation(dict_matrix_index)



def make_multi_docs2doc_freq_info(labeled_documents, n_jobs:int=-1,)->SetDocumentInformation:
    """* What u can do
    - This function generates information (term-label frequency info) for constructing document-frequency matrix.
    """

    counted_frequency = joblib.Parallel(n_jobs=n_jobs)(
        joblib.delayed(generate_document_dict)(key, docs)
        for key, docs in sorted(labeled_documents.items(), key=lambda key_value_tuple: key_value_tuple[0]))

    ### construct [{}] structure for input of DictVectorizer() ###
    seq_feature_documents = (dict(label_freqCounter_tuple[1]) for label_freqCounter_tuple in counted_frequency)

    ### Save index-string dictionary

    dict_matrix_index: Dict[str, Union[dict, Any]] = {}

    # use sklearn feature-extraction
    vec = DictVectorizer()
    dict_matrix_index['matrix_object'] = vec.fit_transform(seq_feature_documents).tocsr()
    dict_matrix_index['feature2id'] = {feat:feat_id for feat_id, feat in enumerate(vec.get_feature_names())}
    dict_matrix_index['label2id'] = {label_freqCounter_tuple[0]:label_id for label_id, label_freqCounter_tuple in enumerate(counted_frequency)}

    return SetDocumentInformation(dict_matrix_index)

