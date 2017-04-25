from sklearn.model_selection import cross_val_score
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
        that these values may be numpy floating points, and should be
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

        metric_list = MetricList()
        for v in scoring_list:
            name    = v["name"]
            scoring = v["scoring"]
            try:
                value = self.cv_score_mean(X, Y, scoring=scoring)
                metric_list.append(Metric(name, scoring, value))
            except Exception:
                metric_list.append(Metric(name, scoring, None))

        return metric_list

    def _is_classification(self):
        return self.problem_type == "classification"

    def _is_regression(self):
        return self.problem_type == "regression"
