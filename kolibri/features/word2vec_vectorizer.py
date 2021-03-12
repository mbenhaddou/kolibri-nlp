from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np



class Transform2WordVectors (BaseEstimator, TransformerMixin):

    wvObject = None

    def __init__(self, wvObject = None, vocabulary=None):
        self.wvObject = wvObject
        self.vocabulary=vocabulary

    def transform(self, X, y=None, **fit_params):

        return self

    def fit(self, sparseX):


        if (not self.wvObject):         # No transformation
            return sparseX
        else:

            wordVectors = np.array([self.wvObject.encode(v) for v in self.vocabulary])
            reducedMatrix = sparseX.dot(wordVectors)
        return reducedMatrix

    def sparseMultiply (self,sparseX, wordVectors):
        wvLength = len(wordVectors[0])
        reducedMatrix = []
        for row in sparseX:
            newRow = np.zeros(wvLength)
            for nonzeroLocation, value in list(zip(row.indices, row.data)):
                newRow = newRow + value * wordVectors[nonzeroLocation]
            reducedMatrix.append(newRow)
        reducedMatrix=np.array([np.array(xi) for xi in reducedMatrix])
        return reducedMatrix
