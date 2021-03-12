import logging
import os
import typing
from builtins import zip
from typing import Any, Optional
from typing import Dict
from typing import List
from typing import Text
from typing import Tuple

import joblib
import numpy as np
from lime.lime_text import LimeTextExplainer
from mlxtend.classifier import EnsembleVoteClassifier, StackingClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import cross_val_predict
from kolibri.classifier.cost_sensitive import AdaCostClassifier
from kolibri import settings
from kolibri.classifier import models
from kolibri.classifier.model import Classifier
from kolibri.pipeComponent import Component

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    import sklearn

SKLEARN_MODEL_FILE_NAME = "classifier_sklearn.pkl"


def _sklearn_numpy_warning_fix():
    """Fixes unecessary warnings emitted by sklearns use of numpy.

    Sklearn will fix the warnings in their next release in ~ August 2018.

    based on https://stackoverflow.com/questions/49545947/sklearn-deprecationwarning-truth-text-of-an-array"""
    import warnings

    warnings.filterwarnings(module='sklearn*', action='ignore',
                            category=DeprecationWarning)


class SkLearnClassifier(Classifier):
    """classifier using the sklearn framework"""

    name = "classifier_sklearn"

    provides = ["classification", "target_ranking"]

    requires = ["text_features"]

    defaults = {

        # the models used in the classifier if several models are given they will be combined
        "models": ["logistic_regression"],

        # We try to find a good number of cross folds to use during
        # class training, this specifies the max number of folds
        "cross_validation_folds": 5,

        # Scoring function used for evaluating the hyper parameters
        # This can be a name or a function (cfr GridSearchCV doc for more info)
        "scoring_function": "f1_weighted",

        "balance_data": None,
        "balance_data_min_freq":None,
        "balance_data_max_freq": None,
        "cost_sensitive": False,
        "explain":False,
        "ouput_folder": None
    }

    def __init__(self,
                 component_config=None,  # type: Dict[Text, Any]
                 clf=None,  # type: sklearn.model_selection.GridSearchCV
                 le=None  # type: sklearn.preprocessing.LabelEncoder
                 ):
        # type: (...) -> None
        """Construct a new class classifier using the sklearn framework."""
        from sklearn.preprocessing import LabelEncoder

        super(SkLearnClassifier, self).__init__(component_config)

        if le is not None:
            self.le = le
        else:
            self.le = LabelEncoder()
        self.clf = clf

        if self.component_config["explain"]:
            if self.clf:
                class_names = self.clf.classes_
                self.explainer = LimeTextExplainer(class_names=class_names)

        _sklearn_numpy_warning_fix()

    @classmethod
    def required_packages(cls):
        # type: () -> List[Text]
        return ["sklearn"]

    def transform_labels_str2num(self, labels):
        # type: (List[Text]) -> np.ndarray
        """Transforms a list of strings into numeric label representation.

        :param labels: List of labels to convert to numeric representation"""

        return self.le.fit_transform(labels)

    def transform_labels_num2str(self, y):
        # type: (np.ndarray) -> np.ndarray
        """Transforms a list of strings into numeric label representation.

        :param y: List of labels to convert to numeric representation"""

        return self.le.inverse_transform(y)

    def train(self, training_data, cfg, **kwargs):
        """Train the class classifier on a data set."""

        DATA=training_data.training_examples
        if "models" in cfg:
            self.component_config["models"]=cfg["models"]
        labels = [e.target
                  for e in DATA]

        if len(set(labels)) < 2:
            logger.warn("Can not train a classifier. "
                        "Need at least 2 different classes. "
                        "Skipping training of classifier.")
        else:
            y = self.transform_labels_str2num(labels)
            X = np.stack([example.text_features
                          for example in DATA])
            ensemble_strategy=cfg.get("ensemble_strategy", 'voting')
            self.clf = self._create_classifier(self.component_config["models"], ensemble_strategy)
            self.class_names = self.le.classes_

            if self.component_config["cost_sensitive"]:
                self.clf=AdaCostClassifier(self.clf)

            kf=StratifiedKFold(n_splits=self.component_config["cross_validation_folds"], shuffle=False)

            predicted = cross_val_predict(self.clf, X, y, cv=kf)

            self.score=("Accuracy: %0.2f" % (accuracy_score(y, predicted)))
            print(classification_report(y, predicted, target_names=self.le.classes_))
            print(confusion_matrix(y, predicted))
            print(accuracy_score(predicted, y))
            self.component_config["Avg_cross_val_score"]=self.score
            print('building final model')
            self.clf.fit(X, y)

        self.component_config["Avg_cross_val_score"] = self.score

    def _create_classifier(self, model_type, ensemble_strategy='voting'):
        clf=None
        if len(model_type)==1:
            clf=models.get_kolibri_model(model_type[0])[1]
#            clf=clf.model
        elif len(model_type)>1:
            classifiers=[models.get_kolibri_model(m_type)[1] for m_type in model_type]
            clf=self._get_multiple_classifiers([clf for clf in classifiers], ensemble_strategy)

        return clf

    def _get_multiple_classifiers(self, classifiers, esemble_strategy):

        if esemble_strategy == 'voting':
            w=[1 for c in classifiers]
            model = EnsembleVoteClassifier(clfs=classifiers, weights=w, voting='soft', verbose=2)

        elif esemble_strategy == 'stacking':
            lr = LogisticRegression()
            model = StackingClassifier(classifiers=classifiers,
                                       use_probas=True,
                                       average_probas=False,
                                       meta_classifier=lr)
        elif esemble_strategy == 'boosting':
            model = AdaBoostClassifier(n_estimators=100)

        return model


    def process(self, document, **kwargs):
        # type: (Document, **Any) -> None
        """Return the most likely class and its probability for a document."""

        if not self.clf:
            # component is either not trained or didn't
            # receive enough training data
            target = None
            target_ranking = []
        else:
            X = document.text_features.reshape(1, -1)
            raw_results, class_ids, probabilities = self.predict(X)
            classes = self.transform_labels_num2str(np.ravel(class_ids))
            # `predict` returns a matrix as it is supposed
            # to work for multiple examples as well, hence we need to flatten
            classes, probabilities = classes.flatten(), probabilities.flatten()

            if classes.size > 0 and probabilities.size > 0:
                ranking = list(zip(list(classes),
                                   list(probabilities)))[:settings.modeling['TARGET_RANKING_LENGTH']]

                target = {"name": classes[0], "confidence": probabilities[0]}

                target_ranking = [{"name": class_name, "confidence": score}
                                  for class_name, score in ranking]
            else:
                target = {"name": None, "confidence": 0.0}
                target_ranking = []
            self.clf.classes_ = self.le.classes_


        document.target=target
        document.raw_prediction_results=raw_results
        document.set_output_property("raw_prediction_results")
        document.set_output_property("target")
        document.target_ranking= target_ranking
        document.set_output_property("target_ranking")

    def predict_prob(self, X):
        # type: (np.ndarray) -> np.ndarray
        """Given a bow vector of an input text, predict the class label.

        Return probabilities for all labels.

        :param X: bow of input text
        :return: vector of probabilities containing one entry for each label"""

        return self.clf.predict_proba(X)

    def predict(self, X):
        # type: (np.ndarray) -> Tuple[np.ndarray, np.ndarray]
        """Given a bow vector of an input text, predict most probable label.

        Return only the most likely label.

        :param X: bow of input text
        :return: tuple of first, the most probable label and second,
                 its probability."""

        pred_result = self.predict_prob(X)
        # sort the probabilities retrieving the indices of
        # the elements in sorted order
        sorted_indices = np.fliplr(np.argsort(pred_result, axis=1))


        return pred_result, sorted_indices, pred_result[:, sorted_indices]

    @classmethod
    def load(cls,
             model_dir=None,  # type: Optional[Text]
             model_metadata=None,  # type: Optional[Metadata]
             cached_component=None,  # type: Optional[Component]
             **kwargs  # type: Any
             ):


        meta = model_metadata.for_component(cls.name)
        file_name = meta.get("classifier_file", SKLEARN_MODEL_FILE_NAME)
        classifier_file = os.path.join(model_dir, file_name)

        if os.path.exists(classifier_file):
            model = joblib.load(classifier_file)
            if model.clf:
                class_names = model.clf.classes_
                model.explainer = LimeTextExplainer(class_names=class_names)

            return model
        else:
            return cls(meta)


    def persist(self, model_dir):
        """Persist this model into the passed directory."""

        classifier_file = os.path.join(model_dir, SKLEARN_MODEL_FILE_NAME)
        joblib.dump(self, classifier_file)

        return {"classifier_file": SKLEARN_MODEL_FILE_NAME}
