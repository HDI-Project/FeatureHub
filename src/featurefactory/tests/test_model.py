import sys
import featurefactory.util
import numpy as np
import sklearn.datasets

from featurefactory.modeling import Model

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

def test_classification():
    _test_problem_type(Model.CLASSIFICATION)

def test_regression():
    _test_problem_type(Model.REGRESSION)

def _test_problem_type(problem_type):
    model = Model(problem_type)
    metrics = model.compute_metrics(data[problem_type]["X"],
                                    data[problem_type]["Y"])
