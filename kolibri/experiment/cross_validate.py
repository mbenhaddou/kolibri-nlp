import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.model_selection import RepeatedStratifiedKFold


def cross_validate_resample(X, y,
                   sampler,
                   classifier,
                   validator=RepeatedStratifiedKFold(n_splits=5, n_repeats=3)):
    class_labels = np.unique(y)


    dataset_orig_target = y.copy()

    label_indices = {}
    for c in class_labels:
        label_indices[c] = np.where(y == c)[0]
    mapping = {}
    for i, c in enumerate(class_labels):
        np.put(y, label_indices[c], i)
        mapping[i] = c

    runtimes = []
    all_preds, all_tests = [], []

    for train, test in validator.split(X, y):
        X_train, y_train = X[train], y[train]
        X_test, y_test = X[test], y[test]

        X_samp, y_samp = sampler.fit_resample(X_train, y_train)


        all_tests.append(y_test)

        classifier.fit(X_samp, y_samp)
        all_preds.append(classifier.predict_proba(X_test))

    if len(all_tests) > 0:
        all_preds = np.vstack(all_preds)
        all_tests = np.hstack(all_tests)

    y = dataset_orig_target

    results = {}
    results['runtime'] = np.mean(runtimes)
    results['sampler'] = sampler.__class__.__name__
    results['classifier'] = classifier.__class__.__name__
    results['sampler_parameters'] = str(sampler.get_params())
    results['classifier_parameters'] = str(classifier.get_params())
    results['db_size'] = len(X)
    results['db_n_attr'] = len(X[0])
    results['db_n_classes'] = len(class_labels)

    all_pred_labels = np.apply_along_axis(lambda x: np.argmax(x), 1, all_preds)

    results['acc'] = accuracy_score(all_tests, all_pred_labels)
    results['confusion_matrix'] = confusion_matrix(all_tests, all_pred_labels)
    results['class_label_mapping'] = mapping
    results['classifcation_report'] = classification_report(all_tests, all_pred_labels)
    results['predicted_vals']=all_pred_labels
    results['real_vals']=all_tests


    return results


def class_label_statistics(y):

    unique, counts = np.unique(y, return_counts=True)
    class_stats = dict(zip(unique, counts))
    minority_label = unique[0] if counts[0] < counts[1] else unique[1]
    majority_label = unique[1] if counts[0] < counts[1] else unique[0]

    return minority_label, majority_label, class_stats
