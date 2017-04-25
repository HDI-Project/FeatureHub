from os.path import abspath, realpath, dirname, join
import sys
sys.path.insert(0, join(dirname(abspath(realpath(__file__))),'..','..'))

import featurefactory.util
import numpy as np

from featurefactory.user.model import Model

# ------------------------------------------------------------------------------ 
# Create fake data
X_classification = np.array([
    [6, 8, 6, 7],
    [1, 1, 1, 4],
    [0, 0.5, -1, 3],
])
X_regression = np.copy(X_classification)
Y_regression = np.array(
    [0.3, 0.7, 1.5]
)
Y_classification  = np.round(np.arctan(Y_regression))

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
