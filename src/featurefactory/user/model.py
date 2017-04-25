from collections import MutableSequence
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

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

class Metric(object):
    def __init__(self, name, scoring, value):
        self.name    = name
        self.scoring = scoring
        self.value   = value

    def __eq__(self, other):
        if not isinstance(other, Metric):
            return False

        return self.name == other.name \
                and self.scoring == other.scoring \
                and self.value == other.value

    def __str__(self):
        return "<{} object with fields {}>".format(type(self), self.__dict__)

    def __repr__(self):
        return str(self)

    def to_user_display(self):
        d = {
            self.name : self.value,
        }
        return d

    def to_db_entry(self):
        try:
            value = float(self.value)
        except Exception:
            value = None
        d = {
            "name"    : self.name,
            "scoring" : self.scoring,
            "value"   : value,
        }
        return d

    def to_string(self, kind="user"):
        if kind=="user":
            return "{}: {}".format(self.name, self.value)
        else:
            raise NotImplementedError()

    @classmethod
    def from_dict(cls, d, kind="user"):
        if kind=="user":
            assert len(d) == 1
            keys = [k for k in d.keys()]
            name    = keys[0]
            scoring = Metric.name_to_scoring(name)
            value   = d[name]
            return cls(name, scoring, value)
        elif kind=="db":
            return cls(**d)
        else:
            raise ValueError("Bad kind: {} ".format(kind))

    @staticmethod
    def name_to_scoring(name):
        def find_in_list(list_):
            for d in list_:
                if d["name"] == name:
                    return d["scoring"]
            return None

        result = find_in_list(Model.CLASSIFICATION_SCORING)
        if result is not None:
            return result
        result = find_in_list(Model.REGRESSION_SCORING)
        if result is not None:
            return result

        return None

class MetricList(MutableSequence):
    def __init__(self, data=None):
        """Initialize the class"""
        super().__init__()
        if data is not None:
            self._list = list(data)
        else:
            self._list = list()

    def __repr__(self):
        return repr(self._list)

    def __len__(self):
        """List length"""
        return len(self._list)

    def __getitem__(self, ii):
        """Get a list item"""
        return self._list[ii]

    def __delitem__(self, ii):
        """Delete an item"""
        del self._list[ii]

    def __setitem__(self, ii, val):
        self._list[ii] = val

    def to_string(self, kind="user"):
        """
        Get user-readable output from metrics, a dict of metrics
        """
        metrics_str = "Feature evaluation metrics: \n"
        line_prefix = "    "
        line_suffix = "\n"
        if self._list:
            for metric in self._list:
                metrics_str += line_prefix + metric.to_string(kind=kind) + line_suffix
        else:
            metrics_str += line_prefix + "<no metrics returned>" + line_suffix

        return metrics_str

    def __eq__(self, other):
        if not isinstance(other, MetricList):
            return False

        if len(self._list) != len(other._list):
            return False

        for x,y in zip(self._list, other._list):
            if x != y:
                return False

        return True

    def insert(self, ii, val):
        # optional: self._acl_check(val)
        self._list.insert(ii, val)

    def append(self, val):
        self.insert(len(self._list), val)

    def convert(self, kind="user"):
        if kind=="user":
            metrics = {}
            for m in self._list:
                    metrics.update(m.to_user_display())
        elif kind=="db":
            metrics = []
            for m in self._list:
                metrics.append(m.to_db_entry())
        else:
            ValueError("Bad kind: {}".format(kind))

        return metrics

    @classmethod
    def from_dict_user(cls, d):
        metrics = cls()
        for key in d:
            metrics.append(Metric.from_dict({key:d[key]},kind="user"))

        return metrics

    @classmethod
    def from_list_db(cls, l):
        metrics = cls()
        for item in l:
            metrics.append(Metric.from_dict(item,kind="db"))

        return metrics

    @classmethod
    def from_object(cls, obj):
        if isinstance(obj, MetricList):
            return obj
        elif isinstance(obj, dict):
            return MetricList.from_dict_user(obj)
        elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
            return MetricList.from_list_db(obj)
        elif isinstance(obj, list) and obj and isinstance(obj[0], Metric):
            result = MetricList()
            for metric in obj:
                result.append(metric)
            return result
        else:
            return cls()
