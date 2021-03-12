#! -*- coding: utf-8 -*-
from kolibri.features.mutualInformation.models import DataCsrMatrix, ScoredResultObject, AvailableInputTypes
from kolibri.features.mutualInformation import data_converter, data
from kolibri.features.mutualInformation.pmi import PMI
from kolibri.features.mutualInformation.tf_idf import TFIDF



from typing import Dict
from scipy.sparse.csr import csr_matrix
import logging

METHOD_NAMES = ['pmi', 'tf_idf']
N_FEATURE_SWITCH_STRATEGY = 1000000


def decide_joblib_strategy(feature2id_dict:Dict[str,int])->str:
    if len(feature2id_dict) > N_FEATURE_SWITCH_STRATEGY:
        return 'threading'
    else:
        return 'multiprocessing'


def compute(input_dict:AvailableInputTypes,
                          method:str,
                          matrix_form=None,
                          n_jobs:int=1)->ScoredResultObject:
    """A interface function of DocumentFeatureSelection package.

    * Args
    - input_dict: Dict-object which has category-name as key and list of features as value.
        - You can put dict or sqlitedict.SqliteDict, or DocumentFeatureSelection.models.PersistentDict
    - method: A method name of feature selection metric
    - use_cython: boolean flag to use cython code for computation. It's much faster to use cython than native-python code
    - is_use_cache: boolean flag to use disk-drive for keeping objects which tends to be huge.
    - is_use_memmap: boolean flag to use memmap for keeping matrix object.
    - path_working_dir: str object.
        - The file path to directory where you save cache file or memmap matrix object. If you leave it None, it finds some directory and save files in it.
    - cache_backend
        - Named of cache backend if you put True on is_use_cache. [PersistentDict, SqliteDict]

    """
    if not method in METHOD_NAMES:
        raise Exception('method name must be either of {}. Yours: {}'.format(METHOD_NAMES, method))

    if method == 'tf_idf':
        """You get scored-matrix with term-frequency.
        ATTENTION: the input for TF-IDF MUST be term-frequency matrix. NOT document-frequency matrix
        """
        matrix_data_object = data.DataConverter().convert_multi_docs2term_frequency_matrix(
            labeled_documents=input_dict,
            n_jobs=n_jobs
        )
        assert isinstance(matrix_data_object, DataCsrMatrix)

        scored_sparse_matrix = TFIDF().fit_transform(X=matrix_data_object.csr_matrix_)
        assert isinstance(scored_sparse_matrix, csr_matrix)

    elif method == 'pmi' and matrix_form is None:
        """You get scored-matrix with either of soa or mutualInformation.
        """
        matrix_data_object = data.DataConverter().convert_multi_docs2document_frequency_matrix(
            labeled_documents=input_dict,
            n_jobs=n_jobs
        )
        assert isinstance(matrix_data_object, DataCsrMatrix)
        backend_strategy = decide_joblib_strategy(matrix_data_object.vocabulary)
        scored_sparse_matrix = PMI().fit_transform(X=matrix_data_object.csr_matrix_,
                                                       n_docs_distribution=matrix_data_object.n_docs_distribution,
                                                       n_jobs=n_jobs,
                                                       joblib_backend=backend_strategy)
        assert isinstance(scored_sparse_matrix, csr_matrix)

    else:
        raise Exception()
#todo fix logger
#    logger.info('Done computation.')
    return ScoredResultObject(
        scored_matrix=scored_sparse_matrix,
        label2id_dict=matrix_data_object.label2id_dict,
        feature2id_dict=matrix_data_object.vocabulary,
        method=method,
        matrix_form=matrix_form,
        frequency_matrix=matrix_data_object.csr_matrix_)