import joblib
import os.path

import numpy as np
from sklearn.preprocessing import label_binarize, LabelEncoder

from featurefactory.modeling.scorers import ndcg_score, rmsle_score
from featurefactory.modeling.model import Model
from featurefactory.util import RANDOM_STATE

# automl
try:
    from autosklearn.classification import AutoSklearnClassifier
    from autosklearn.regression import AutoSklearnRegressor
    import autosklearn.metrics
    ndcg_autoscorer = autosklearn.metrics.make_scorer("ndcg", ndcg_score,
        greater_is_better=True, needs_proba=True)
    rmsle_autoscorer = autosklearn.metrics.make_scorer("rmsle", rmsle_score,
        greater_is_better=False, needs_proba=False)
except ImportError:
    AutoSklearnClassifier = Model._get_default_classifier()
    AutoSklearnRegressor =  Model._get_default_regressor()
    ndcg_autoscorer = ndcg_score
    rmsle_autoscorer = rmsle_score

class AutoModel(Model):
    SEED = RANDOM_STATE+1
    TIME_LEFT_FOR_THIS_TASK=90
    PER_RUN_TIME_LIMIT=10
    ML_MEMORY_LIMIT=7900
    INITIAL_CONFIGURATIONS_VIA_METALEARNING=0

    def __init__(self, problem_type, **kwargs):
        super().__init__(problem_type)

        if self._is_classification():
            AutoMLModel = AutoSklearnClassifier
        elif self._is_regression():
            AutoMLModel = AutoSklearnRegressor
        else:
            raise NotImplementedError

        # ~hack~
        # set custom scorers. really, we should include this in the database
        if "metric" in kwargs:
            self.metric = kwargs["metric"]
        else:
            if self._is_classification():
                self.metric = ndcg_autoscorer
            elif self._is_regression():
                self.metric = rmsle_autoscorer
            else:
                raise NotImplementedError

        automl_param_names = AutoMLModel._get_param_names()
        params = {}
        for param in automl_param_names:
            if param in kwargs:
                params[param] = kwargs.pop(param)
            elif hasattr(self, param.upper()):
                params[param] = getattr(self, param.upper())

        self.model = AutoMLModel(**params)

    def fit(self, X_train, Y_train, **kwargs):
        if "metric" in kwargs:
            self.metric = kwargs.pop("metric")

        X_train = Model._formatX(X_train)
        
        if self._is_classification() and \
            len(np.unique(Y_train)) > 2:
            self.le = LabelEncoder()
            self.le.fit(Y_train)
            Y_train = self.le.transform(Y_train)
        Y_train = Model._formatY(Y_train)

        # If AutoSklearn has failed to load, this object is a sklearn estimator
        # that doesn't accept a 'metric' kwarg.
        try:
            self.model.fit(X_train, Y_train, metric=self.metric, **kwargs)
        except TypeError as e:
            if e.args and "metric" in e.args[0]:
                self.model.fit(X_train, Y_train, **kwargs)
            else:
                raise

    def predict(self, X_test):
        X_test = Model._formatX(X_test)
        Y_test_pred = self.model.predict(X_test)
        if self._is_classification() and \
            len(np.unique(Y_test_pred)) > 2:
            # TODO this fails if <=2 classes are actually predicted. Should
            # store whether it is multiclass classification as class member.
            return self.le.inverse_transform(Y_test_pred)
        else:
            return Y_test_pred

    def predict_proba(self, X_test):
        X_test = Model._formatX(X_test)
        Y_test_pred_proba = self.model.predict_proba(X_test)
        return Y_test_pred_proba

    def score(self, X_test, Y_test):
        # todo not nearly robust enough
        X_test = Model._formatX(X_test)

        Y_test = Model._formatY(Y_test)
        Y_test_pred = self.predict(X_test)
        score = self.metric(Y_test, Y_test_pred)
        return score

    def dump(self, absname):
        joblib.dump(self.model, absname)
        print("Model dumped to {}".format(absname))

    def load(self, absname):
        if not os.path.exists(absname):
            raise ValueError("Couldn't find model at {}".format(absname))
        self.model = joblib.load(absname)
        print("Model loaded successfully.")
