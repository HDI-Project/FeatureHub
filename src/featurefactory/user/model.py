from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
import numpy as np

class Model(object):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"

    CLASSIFICATION_SCORING = [
        { "name" : "Accuracy"  , "scoring" : "accuracy" },
        { "name" : "Precision" , "scoring" : "precision" },
        { "name" : "Recall"    , "scoring" : "recall" },
        { "name" : "ROC AUC"   , "scoring" : "roc_auc" },
    ]
    REGRESSION_SCORING = [
        { "name" : "Mean Squared Error" , "scoring" : "neg_mean_squared_error" },
        { "name" : "R-squared"          , "scoring" : "r2" }                     ,
    ]

    def __init__(self, problem_type):
        self.problem_type = problem_type

        if self.problem_type == Model.CLASSIFICATION:
            self.model = DecisionTreeClassifier()
        elif self.problem_type == Model.REGRESSION:
            self.model = DecisionTreeRegressor()
        else:
            raise NotImplementedError

    def cv_score_mean(self, X, Y, scoring="accuracy"):
        if len(X.shape) == 1:    # 1d arrays are not supported anymore by
            X = X.reshape(-1, 1)
        return cross_val_score(self.model, X, Y, scoring=scoring, n_jobs=-1).mean()

    def compute_metrics(self, X, Y):
        """
        Compute cross-validated metrics from training model on data X with
        labels Y.

        Returns a dictionary that maps metric names ("Accuracy") to values. Note
        that these values may be numpy floating points or nan, and should be
        converted prior to insertion in a database.
        """
        # scoring_types maps user-readable name to `scoring`, as argument to
        # cross_val_score
        # See also http://scikit-learn.org/stable/modules/model_evaluation.html#scoring-parameter
        if self._is_classification():
            scoring_list = Model.CLASSIFICATION_SCORING
        elif self._is_regression():
            scoring_list = Model.REGRESSION_SCORING
        else:
            raise NotImplementedError

        metrics = []
        for v in scoring_list:
            name    = v["name"]
            scoring = v["scoring"]
            try:
                value = self.cv_score_mean(X, Y, scoring=scoring)
                metrics.append(Metric(name, scoring, value))
            except Exception:
                metrics.append(Metric(name, scoring, np.nan))

        return metrics

    def _is_classification(self):
        return self.problem_type == "classification"

    def _is_regression(self):
        return self.problem_type == "regression"

class Metric(object):
    def __init__(self, name, scoring, value):
        self.name    = name
        self.scoring = scoring
        self.value   = value

    def to_user_display(self):
        d = {
            self.name : self.value,
        }
        return d

    def to_db_entry(self):
        if isinstance(self.value, np.floating):
            value = float(self.value)
        elif np.isnan(self.value):
            value = None
        else:
            # unexpected
            value = None
        d = {
            "name"    : self.name,
            "scoring" : self.scoring,
            "value"   : value,
        }
        return d
