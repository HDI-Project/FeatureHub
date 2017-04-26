import traceback
import sys
import numpy as np
import sklearn.metrics
from sklearn.preprocessing import label_binarize
from sklearn.model_selection import KFold
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from featurefactory.modeling.metrics import Metric, MetricList

class Model(object):
    CLASSIFICATION = "classification"
    REGRESSION     = "regression"

    CLASSIFICATION_SCORING = [
        { "name" : "Accuracy"  , "scoring" : "accuracy" },
        { "name" : "Precision" , "scoring" : "precision" },
        { "name" : "Recall"    , "scoring" : "recall" },
        { "name" : "ROC AUC"   , "scoring" : "roc_auc" },
    ]
    REGRESSION_SCORING = [
        { "name" : "Mean Squared Error" , "scoring" : "mean_squared_error" },
        { "name" : "R-squared"          , "scoring" : "r2" }                     ,
    ]

    BINARY_METRIC_AGGREGATION = "average"
    MULTICLASS_METRIC_AGGREGATION = "micro"

    def __init__(self, problem_type):
        self.problem_type = problem_type

        if self.problem_type == Model.CLASSIFICATION:
            self.model = DecisionTreeClassifier()
        elif self.problem_type == Model.REGRESSION:
            self.model = DecisionTreeRegressor()
        else:
            raise NotImplementedError

    def cv_score_mean(self, X, Y, scoring):
        # 1d arrays are deprecated by sklearn 0.17
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)

        if len(Y.shape) == 1:
            Y = Y.reshape(-1, 1)

        # Determine binary/multiclass classification
        n_classes = len(np.unique(Y))
        if n_classes > 2:
            metric_aggregation = Model.MULTICLASS_METRIC_AGGREGATION
        else:
            metric_aggregation = Model.BINARY_METRIC_AGGREGATION

        # Determine predictor (labels, label probabilities, or values) and
        # scoring function.
        if scoring=="accuracy":
            scorer           = sklearn.metrics.accuracy_score
            predictor        = lambda model, X_test: model.predict(X_test)
            transform_Y_test = lambda Y_test: Y_test
        elif scoring=="precision":
            scorer = lambda y_true, y_pred: sklearn.metrics.precision_score(
                    y_true, y_pred, average=metric_aggregation)
            predictor        = lambda model, X_test: model.predict(X_test)
            transform_Y_test = lambda Y_test: Y_test
        elif scoring=="recall":
            scorer = lambda y_true, y_pred: sklearn.metrics.recall_score(
                    y_true, y_pred, average=metric_aggregation)
            predictor        = lambda model, X_test: model.predict(X_test)
            transform_Y_test = lambda Y_test: Y_test
        elif scoring=="roc_auc":
            scorer = lambda y_true, y_pred: sklearn.metrics.roc_auc_score(
                    y_true, y_pred, average=metric_aggregation)
            predictor        = lambda model, X_test: model.predict_proba(X_test)
            transform_Y_test = lambda Y_test: label_binarize(Y_test,
                    classes=[x for x in range(n_classes)])
        elif scoring=="mean_squared_error":
            scorer           = sklearn.metrics.mean_squared_error
            predictor        = lambda model, X_test: model.predict(X_test)
            transform_Y_test = lambda Y_test: Y_test
        elif scoring=="r2":
            scorer           = sklearn.metrics.r2_score
            predictor        = lambda model, X_test: model.predict(X_test)
            transform_Y_test = lambda Y_test: Y_test

        kf = KFold(shuffle=True)
        scores = []
        for train_inds, test_inds in kf.split(X, Y):
            X_train, X_test = X[train_inds], X[test_inds]
            Y_train, Y_test = Y[train_inds], Y[test_inds]
            self.model.fit(X_train, Y_train)
            Y_test_pred = predictor(self.model, X_test)
            Y_test_tr = transform_Y_test(Y_test)
            score = scorer(Y_test_tr, Y_test_pred)
            scores.append(score)

        return np.mean(scores)

    def compute_metrics(self, X, Y):
        """
        Compute cross-validated metrics from training model on data X with
        labels Y.

        Returns a dictionary that maps metric names ("Accuracy") to values. Note
        that these values may be numpy floating points, and should be
        converted prior to insertion in a database.
        """

        # just ensure that we np for everything
        X = np.array(X)
        Y = np.array(Y)

        # scoring_types maps user-readable name to `scoring`, as argument to
        # cross_val_score
        # See also http://scikit-learn.org/stable/modules/model_evaluation.html#scoring-parameter
        if self._is_classification():
            scoring_list = Model.CLASSIFICATION_SCORING
        elif self._is_regression():
            scoring_list = Model.REGRESSION_SCORING
        else:
            raise NotImplementedError

        metric_list = MetricList()
        for v in scoring_list:
            name    = v["name"]
            scoring = v["scoring"]

            try:
                value = self.cv_score_mean(X, Y, scoring=scoring)
                metric_list.append(Metric(name, scoring, value))
            except Exception:
                metric_list.append(Metric(name, scoring, None))
                raise

        return metric_list

    def _is_classification(self):
        return self.problem_type == "classification"

    def _is_regression(self):
        return self.problem_type == "regression"
