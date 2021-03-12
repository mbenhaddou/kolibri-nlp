import numpy as np
#from scipy.special import chdtrc
from scipy.sparse import spdiags
from scipy import sparse
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import LabelBinarizer


def _chisquare(f_obs, f_exp, reduce):
    """Replacement for scipy.stats.chisquare with custom reduction.
    Version from https://github.com/scipy/scipy/pull/2525 with additional
    optimizations.
    """
    f_obs = np.asarray(f_obs, dtype=np.float64)

    k = len(f_obs)
    # Reuse f_obs for chi-squared statistics
    chisq = f_obs
    chisq -= f_exp
    chisq **= 2
    chisq /= f_exp
    chisq = reduce(chisq, axis=0)
    return chisq  #, chdtrc(k - 1, chisq)


def _chi2(X, y, alpha, reduce):
    Y = LabelBinarizer().fit_transform(y)
    if Y.shape[1] == 1:
        Y = np.append(1 - Y, Y, axis=1)

    observed = Y.T.dot(X)

    feature_count = X.sum(axis=0).reshape(-1, 1)
    class_prob = Y.mean(axis=0).reshape(-1, 1)
    expected = np.dot(class_prob,feature_count.T)

    observed += alpha
    expected += alpha

    return _chisquare(observed, expected, reduce)


def _rf(X, y, alpha, reduce):
    """Relevance frequency. Ignores alpha."""

    Y = LabelBinarizer().fit_transform(y)
    if Y.shape[1] == 1:
        Y = np.append(1 - Y, Y, axis=1)


    # Per class "document frequencies" (# of samples containing each feature).
    rf = ((Y.T.dot(X)) > 0).astype(np.float64)

    for i in range(Y.shape[1]):
        # rf.sum(axis=0) - rf[i] is the sum of all rows except i
        rf[i] /= np.maximum(1., rf.sum(axis=0) - rf[i])

    # XXX original uses log2(2 + rf)
    return reduce(np.log1p(rf, out=rf), axis=0)

def _cbtw(X, y, alpha, reduce):
    """category based term weighting."""
    Y = LabelBinarizer().fit_transform(y)
    if Y.shape[1] == 1:
        Y = np.append(1 - Y, Y, axis=1)


    # Per class "document frequencies" (# of samples containing each feature).
    rf = np.square(Y.T.dot(X)).astype(np.float64)
    # Per class "document occurence" (# of samples containing each feature at least once).
    rf_O_1 = ((Y.T.dot(X)) > 0).astype(np.float64)

    for i in range(Y.shape[1]):
        # rf.sum(axis=0) - rf[i] is the sum of all rows except i
        rf[i] /= np.maximum(1., rf_O_1.sum(axis=0) - rf_O_1[i])

    for i in range(rf.T.shape[0]):
        rf.T[i]/=np.maximum(1., rf_O_1.sum(axis=1) - rf_O_1.T[i])


    # XXX original uses log2(2 + rf)
    return reduce(np.log1p(1+ rf, out=rf), axis=0)


class SupervisedTermWeights(BaseEstimator, TransformerMixin):
    """Supervised term weighting transformer.
    This estimator learns term weights in a supervised way, taking into account
    the frequency with which features occur in the distinct classes of a
    classification problem. It produces weighted frequencies by multiplying
    term frequencies by the learned weights, to get combinations such as
    tf-chi2, i.e., term frequency times chi2 test statistic.
    Such weightings have been found to outperform the unsupervised tf-idf
    weighting on a variety of text classification tasks (using linear
    classifiers).
    Parameters
    ----------
    weighting : {'chi2', 'rf'}, default = 'chi2'
        Weighting scheme. 'chi2' is the chi^2 test statistic; 'rf' is the
        relevance frequency of Lan et al.
    reduce : {'max', 'mean', 'sum'}, default = 'max'
        How to reduce per-class scores for each feature into a single score:
        take the max, mean or sum over the classes.
    References
    ----------
    Man Lan, Chew Lim Tan and Jian Su (2007). Supervised and Traditional Term
        Weighting Methods for Automatic Text Categorization. PAMI.
    """

    _WEIGHTING = {'chi2': _chi2, 'rf': _rf, 'cbtw':_cbtw}
    _REDUCE = {'max': np.max, 'mean': np.mean, 'sum': np.sum}

    def __init__(self, weighting="chi2", reduce="max", alpha=1):
        self.reduce = reduce
        self.alpha = alpha
        self.weighting = weighting

    def fit(self, X, y):
        """Learn supervised term weights from training set X, y."""
        reduce_ = self._REDUCE[self.reduce]
        weighting = self._WEIGHTING[self.weighting]

        self.weights_ = weighting(X, y, self.alpha, reduce_)
        return self

    def transform(self, X, y=None):
        """Transform term frequency matrix X into a weighted frequency matrix.
        """
        n_features = self.weights_.shape[0]
        return X * spdiags(self.weights_, 0, n_features, n_features)