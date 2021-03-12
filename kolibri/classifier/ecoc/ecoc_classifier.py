from sklearn.svm import SVC
from kolibri.utils.distance import *
from kolibri.pipeComponent import Component
from kolibri.classifier.ecoc import matrix as MT
import logging
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from itertools import combinations
from scipy.special import comb
from kolibri.classifier.models import get_model
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import StratifiedKFold
import os, joblib
import copy
logger = logging.getLogger(__name__)

ECOC_MODEL_FILE_NAME = "classifier_ecoc.pkl"
ECOC_PREDICTORS_FILE_NAME = "predictor_{0}.pkl"

class ECOC(Component):
    """
    the base class for all to inherit
    """
    name = "classifier_ecoc"

    provides = ["classification", "target_ranking"]

    requires = ["text_features"]

    defaults = {

        # the models used in the classifier if several models are given they will be combined
        "ecoc_model": "svm",
        "ecoc_type": "dense"
    }
    def __init__(self, config, distance_measure=euclidean_distance, base_estimator='svm', le=None):

        super().__init__(config)
        self.estimator = get_model(base_estimator)
        self.predictors = []
        self.matrix = None
        self.index = None
        self.distance_measure = distance_measure
        self.predicted_vector = []
        self.train_data = []
        self.train_label = []
        self.ecoc_type=self.component_config["ecoc_type"]
        if le is not None:
            self.le = le
        else:
            self.le = LabelEncoder()


    def create_matrix(self, data, label):

        """
        create the matrix for codes for each class
        :param data: the data used in ecoc
        :param label: the corresponding label to data
        :return: coding matrix
        """
        if self.ecoc_type=="dense":
            while True:
                index = {l: i for i, l in enumerate(np.unique(label))}
                matrix_row = len(index)
                if matrix_row > 3:
                    matrix_col = np.int(np.floor(10 * np.log10(matrix_row)))
                else:
                    matrix_col = matrix_row
                matrix = np.random.random((matrix_row, matrix_col))
                class_1_index = matrix > 0.5
                class_2_index = matrix < 0.5
                matrix[class_1_index] = 1
                matrix[class_2_index] = -1
                if (not MT.exist_same_col(matrix)) and (not MT.exist_same_row(matrix)) and MT.exist_two_class(matrix):
                    return matrix, index
        elif self.ecoc_type=="ovo":
            index = {l: i for i, l in enumerate(np.unique(label))}
            groups = combinations(range(len(index)), 2)
            matrix_row = len(index)
            # combinations of number of classes  taken 2 at a time
            matrix_col = np.int(comb(len(index), 2))
            col_count = 0
            matrix = np.zeros((matrix_row, matrix_col))
            for group in groups:
                class_1_index = group[0]
                class_2_index = group[1]
                matrix[class_1_index, col_count] = 1
                matrix[class_2_index, col_count] = -1
                col_count += 1
            return matrix, index
        elif self.ecoc_type=="ova":
            index = {l: i for i, l in enumerate(np.unique(label))}
            matrix = np.eye(len(index)) * 2 - 1
            return matrix, index

    def train(self, training_data, cfg, **kwargs):  # type (TrainingData, ModelConfig, **Any) -> None(self, data, label, **estimator_param):
        """
        a method to train base estimator based on given data and label
        :param data: data used to train base estimator
        :param label: label corresponding to the data
        :param estimator_param: some param used by base estimator
        :return: None
        """
        labels = [e.target
                  for e in training_data.training_examples]
        y = self.transform_labels_str2num(labels)

        if len(set(labels)) < 2:
            logger.warn("Can not train a classifier. "
                        "Need at least 2 different classes. "
                        "Skipping training of classifier.")
        else:
            data = np.stack([example.text_features
                          for example in training_data.training_examples])

        self.predictors = []
        self.matrix, self.index = self.create_matrix(data, y)
#        self.evaluate_model(data, y)
        for i in range(self.matrix.shape[1]):
            dat, cla = MT.get_data_from_col(data, y, self.matrix[:, i], self.index)
            estimator = self.estimator.fit(dat, cla)
            self.predictors.append(copy.copy(estimator))

    def evaluate_model(self, data, y, cv=5):
        kf = StratifiedKFold(n_splits=cv, shuffle=False)
        predicted=[0]*len(y)
        for train_index, test_index in kf.split(data, y):
            predictors=[]
            for i in range(self.matrix.shape[1]):
                dat, cla = MT.get_data_from_col(data[train_index], y[train_index], self.matrix[:, i], self.index)
                estimator = self.estimator.fit(dat, cla)
                predictors.append(copy.copy(estimator))
            res = []
            for test in test_index:
                predicted[test]=self.predict(predictors, data[test])["name"]
        print(accuracy_score(y, predicted))
        print(classification_report(y, predicted, target_names=self.le.classes_))
        print(confusion_matrix(y, predicted))

    def predict(self, predictors, data):
        """Return the most likely class and its probability for a document."""

        if not self.estimator:
            # component is either not trained or didn't
            # receive enough training data
            target = None
            target_ranking = []
        else:
            if len(predictors) == 0:
                logging.debug('The Model has not been fitted!')
            if len(data.shape) == 1:
                data = np.reshape(data, [1, -1])

            predicted_vector = self._use_predictors_bis(predictors, data)  # one row

            predicted_vector=list(predicted_vector)
            probabilities = MT.get_class_probabilities(predicted_vector, self.matrix, self.distance_measure)

            if len(probabilities) > 0:

                target = {"name": probabilities[0][0], "confidence": probabilities[0][1]}
            else:
                target = {"name": None, "confidence": 0.0}
            return target


    def process(self, document, **kwargs):

        """Return the most likely class and its probability for a document."""

        if not self.estimator:
            # component is either not trained or didn't
            # receive enough training data
            target = None
            target_ranking = []
        else:
            data = document.text_features.reshape(1, -1)
            res = []
            if len(self.predictors) == 0:
                logging.debug('The Model has not been fitted!')
            if len(data.shape) == 1:
                data = np.reshape(data, [1, -1])

            predicted_vector = self._use_predictors(data)  # one row

            self.predicted_vector.append(list(predicted_vector))
            probabilities = MT.get_class_probabilities(predicted_vector, self.matrix, self.distance_measure)

            if len(probabilities) > 0:

                target = {"name": self.transform_labels_num2str([probabilities[0][0]]), "confidence": probabilities[0][1]}

                target_ranking = [{"name": self.transform_labels_num2str([p[0]]), "confidence": p[1]}
                                  for p in  probabilities]
            else:
                target = {"name": None, "confidence": 0.0}
                target_ranking = []

            document.target = target
            document.set_output_property("target")
            document.target_ranking = target_ranking
            document.set_output_property("target_ranking")


    def _use_predictors(self, data):
        """
        :param data: data to predict
        :return: predicted vector
        """
        res = []
        for i in self.predictors:
            pred=i._predict(np.array(data))
            res.append(pred[0])
        return np.array(res)

    def _use_predictors_bis(self, predictors, data):
        res = []
        for i in predictors:
            pred=i._predict(np.array(data))

            res.append(pred[0])
        return np.array(res)

    def transform_labels_str2num(self, labels):
        # type: (List[Text]) -> np.ndarray
        """Transforms a list of strings into numeric label representation.

        :param labels: List of labels to convert to numeric representation"""

        return self.le.fit_transform(labels)

    def transform_labels_num2str(self, y):
        # type: (np.ndarray) -> np.ndarray
        """Transforms a list of strings into numeric label representation.

        :param y: List of labels to convert to numeric representation"""
        str=self.le.inverse_transform(y)
        return str

    @classmethod
    def load(cls,
             model_dir=None,  # type: Optional[Text]
             model_metadata=None,  # type: Optional[Metadata]
             cached_component=None,  # type: Optional[Component]
             **kwargs  # type: Any
             ):


        meta = model_metadata.for_component(cls.name)
        file_name = meta.get("classifier_file", ECOC_MODEL_FILE_NAME)
        classifier_file = os.path.join(model_dir, file_name)

        if os.path.exists(classifier_file):
            model = joblib.load(classifier_file)
            for i, predictor in enumerate(model.predictors):
                predictor=joblib.load(os.path.join(model_dir, ECOC_PREDICTORS_FILE_NAME.format(i)))
                model.predictors[i]=joblib.load(os.path.join(model_dir, ECOC_PREDICTORS_FILE_NAME.format(i)))
            return model
        else:
            return cls(meta)


    def persist(self, model_dir):
        """Persist this model into the passed directory."""

        classifier_file = os.path.join(model_dir, ECOC_MODEL_FILE_NAME)

        joblib.dump(self, classifier_file)
        for i, predictor in enumerate(self.predictors):
            joblib.dump(predictor, os.path.join(model_dir, ECOC_PREDICTORS_FILE_NAME.format(i)))
        return {"classifier_file": ECOC_MODEL_FILE_NAME}
