import sys
import random
import featurefactory.util
import numpy as np
import pandas as pd
import sklearn.datasets

#from featurefactory.modeling.model_old import Model
from featurefactory.modeling.model import Model
from featurefactory.tests.util import EPSILON

# ------------------------------------------------------------------------------
# Create fake data
(X_classification, Y_classification) = sklearn.datasets.load_iris(return_X_y=True)
(X_regression, Y_regression)         = sklearn.datasets.load_boston(return_X_y=True)

data = {
    Model.CLASSIFICATION : {
        "X" : X_classification,
        "Y" : Y_classification,
    },
    Model.REGRESSION : {
        "X" : X_regression,
        "Y" : Y_regression,
    },
}

data_pd = {
    Model.CLASSIFICATION : {
        "X" : pd.DataFrame(X_classification),
        "Y" : pd.DataFrame(Y_classification),
    },
    Model.REGRESSION : {
        "X" : pd.DataFrame(X_regression),
        "Y" : pd.DataFrame(Y_regression),
    },
}

def test_classification():
    metrics = _test_problem_type_cv(Model.CLASSIFICATION, data)
    metrics_pd = _test_problem_type_cv(Model.CLASSIFICATION, data_pd)

    assert metrics==metrics_pd

    metrics_user = metrics.convert(kind="user")
    assert abs(metrics_user["Accuracy"]  - 0.9468954) < EPSILON
    assert abs(metrics_user["Precision"] - 0.9468954) < EPSILON
    assert abs(metrics_user["Recall"]    - 0.9468954) < EPSILON
    assert abs(metrics_user["ROC AUC"]   - 0.9601715) < EPSILON

def test_classification_train_test():
    metrics = _test_problem_type_train_test(Model.CLASSIFICATION, data)
    metrics_pd = _test_problem_type_train_test(Model.CLASSIFICATION, data_pd)

    assert metrics==metrics_pd

    metrics_user = metrics.convert(kind="user")
    assert abs(metrics_user["Accuracy"]  - 0.7777777) < EPSILON
    assert abs(metrics_user["Precision"] - 0.7777777) < EPSILON
    assert abs(metrics_user["Recall"]    - 0.7777777) < EPSILON
    assert abs(metrics_user["ROC AUC"]   - 0.8333333) < EPSILON

def test_regression():
    metrics = _test_problem_type_cv(Model.REGRESSION, data)
    metrics_pd = _test_problem_type_cv(Model.REGRESSION, data_pd)

    assert metrics==metrics_pd

    metrics_user = metrics.convert(kind="user")
    assert abs(metrics_user["Mean Squared Error"] - 20.7262935) < EPSILON
    assert abs(metrics_user["R-squared"]          -  0.7393219) < EPSILON

def test_regression_train_test():
    metrics = _test_problem_type_train_test(Model.REGRESSION, data)
    metrics_pd = _test_problem_type_train_test(Model.REGRESSION, data_pd)

    assert metrics==metrics_pd

    metrics_user = metrics.convert(kind="user")
    assert abs(metrics_user["Mean Squared Error"] - 48.7246710) < EPSILON
    assert abs(metrics_user["R-squared"]          -  0.2656004) < EPSILON

def _test_problem_type_cv(problem_type, data):
    model = Model(problem_type)
    X = data[problem_type]["X"]
    Y = data[problem_type]["Y"]
    metrics = model.compute_metrics(X, Y)

    return metrics

def _test_problem_type_train_test(problem_type, data):
    model = Model(problem_type)
    X = data[problem_type]["X"]
    Y = data[problem_type]["Y"]
    n = round(0.7 * len(X))
    metrics = model.compute_metrics(X, Y, kind="train_test", n=n)
                                    
    return metrics
