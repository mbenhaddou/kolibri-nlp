import copy
import numpy as np
from kolibri.utils.distance import *



def get_data_from_col(data, label, col, index):
    """
    to get data subset form a col, where the value is not zero
    :param data: data set
    :param label: label corresponding to data
    :param col: the col we want to get data subset
    :param index: the index for matrix
    :return: data subset and corresponding labels
    """
    data_result = None
    cla_result = None
    for i in range(len(col)):
        if col[i] != 0:
            d = np.array([data[k] for k in range(len(label)) if label[k] == get_key_for_value(index, i)])
            c = np.ones(len(d)) * col[i]
            if d.shape[0] > 0 and d.shape[1] > 0:
                if data_result is None:
                    data_result = copy.copy(d)
                    cla_result = copy.copy(c)
                else:
                    data_result = np.vstack((data_result, d))
                    cla_result = np.hstack((cla_result, c))
    return data_result, cla_result


def get_key_for_value(dictionary, value):
    for i in dictionary:
        if dictionary[i] == value:
            return i




def get_class_probabilities(vector, matrix, distance=euclidean_distance, weights=None):
    """
    find the closet coding vector in matrix
    :param vector: a predicted vector
    :param matrix: coding matrix
    :param distance: a callable object to calculate distance
    :param weights: the weights for each feature
    :return: the index corresponding to closet coding vector
    """
    proabilities={i:1-distance(vector, mat, weights)/matrix.shape[1] for i, mat in enumerate(matrix)}

    proabilitie_sorted = sorted(proabilities.items(), key=lambda kv: kv[1], reverse=True)
    return proabilitie_sorted


def exist_same_row(matrix):
    """
    to checkout whether there are same rows in a matrix
    :param matrix: coding matrix
    :return: true or false
    """
    row_count = matrix.shape[0]
    for i in range(row_count):
        for j in range(i+1, row_count):
            if np.all([matrix[i] == matrix[j]]) or np.all([matrix[i] == -matrix[j]]):
                 return True
    return False


def exist_same_col(matrix):
    """
    to checkout whether there are same cols in a matrix
    :param matrix: coding matrix
    :return: true or false
    """
    col_count = matrix.shape[1]
    for i in range(col_count):
        for j in range(i+1, col_count):
            if np.all([matrix[:, i] == matrix[:, j]]) or np.all([matrix[:, i] == -matrix[:, j]]):
                 return True
    return False


def exist_two_class(matrix):
    """
    to ensure all cols in coding matrix have 1 and -1
    :param matrix: coding matrix
    :return: true or false
    """
    col_count = matrix.shape[1]
    for i in range(col_count):
        col_unique = np.unique(matrix[:, i])
        if (1 not in col_unique) or (-1 not in col_unique):
            # print('dont have two classes:', matrix[:, i])
            return False
    return True
