import numpy as np
from sklearn.ensemble import AdaBoostClassifier
from collections import Counter


class AdaCostClassifier(AdaBoostClassifier):

    def __init__(self, base_estimator=None, n_estimators=20, learning_rate=0.5,
                 FNcost='auto', FPcost=1, algorithm='SAMME.R', random_state=None):
        super(AdaBoostClassifier, self).__init__(
            base_estimator=base_estimator, n_estimators=n_estimators,
            learning_rate=learning_rate, random_state=random_state)

        self.FPcost = FPcost
        self.FNcost = FNcost
        self.algorithm = algorithm

    def _boost_real(self, iboost, X, y, sample_weight, random_state):
        """Implement a single boost using the SAMME.R real algorithm."""
        estimator = self._make_estimator(random_state=random_state)
        estimator.fit(X, y, sample_weight=sample_weight)
        y_predict_proba = estimator.predict_proba(X)

        if iboost == 0:
            self.classes_ = getattr(estimator, 'classes_', None)
            self.n_classes_ = len(self.classes_)
        y_predict = self.classes_.take(np.argmax(y_predict_proba, axis=1), axis=0)
        incorrect = y_predict != y
        estimator_error = np.mean(np.average(incorrect, weights=sample_weight, axis=0))
        if estimator_error <= 0:
            return sample_weight, 1., 0.

        n_classes = self.n_classes_
        classes = self.classes_
        y_codes = np.array([-1. / (n_classes - 1), 1.])
        y_coding = y_codes.take(classes == y[:, np.newaxis])
        proba = y_predict_proba  # alias for readability

        # Truncate proba
        # Is equivalent to proba [proba <np.finfo (proba.dtype) .eps] = np.finfo (proba.dtype) .eps
        np.clip(proba, np.finfo(proba.dtype).eps, None, out=proba)

        estimator_weight = (-1. * self.learning_rate * ((n_classes - 1.) / n_classes)
                            * (y_coding * np.log(y_predict_proba)).sum(axis=1))

        # Sample updated formula, just rewrite here
        if not iboost == self.n_estimators - 1:
            criteria = ((sample_weight > 0) | (estimator_weight < 0))
            # Multiply self._beta (y, y_predict) on the original basis, that is, the cost adjustment function
            sample_weight *= np.exp(estimator_weight * criteria * self._beta(y, y_predict))
        return sample_weight, 1., estimator_error

    # Newly defined cost adjustment function

    def _beta(self, y, y_hat):
        res = []
        ratio = Counter(y)
        ratio={cl:1+(cnt/len(y)) for cl, cnt in ratio.items()}
        if self.FNcost == 'auto':
            self.FNcost = ratio

        for i in zip(y, y_hat):
            # FN error: Misjudged risky customers as normal users
            if i[0] != i[1]:
                res.append(self.FNcost[i[0]])
                # FP error: Misjudge normal customers as risky users
            else:
                res.append(self.FPcost)
        return np.array(res)