from sklearn.model_selection import cross_val_predict
from sklearn_crfsuite.metrics import flat_classification_report
from sklearn.base import BaseEstimator
from kolibri.pipeComponent import Component

class Classifier(Component):
    def __init__(self, config):
        super().__init__(config)
        self.clf=None
        self.class_names=None

class KolibriModel(BaseEstimator):
    def __init__(self, sklearn_model):
        self.model=sklearn_model


    def fit(self, X, y):
        y_pred = cross_val_predict(self.model, X, y, cv=5)
        report = flat_classification_report(y_pred=y_pred, y_true=y)
        self.model.fit(X,y)
        return report

    def predict(self, X):
        return self.model._predict(X)

    def predic_proba(self, X):
        return self.model.predict_proba(X)
