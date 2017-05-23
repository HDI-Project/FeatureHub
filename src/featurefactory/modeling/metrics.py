from collections import MutableSequence
import featurefactory.modeling.model

import numpy as np
from sklearn.metrics import mean_squared_error

class Metric(object):
    """Metric"""

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

    def __lt__(self, other):
        return self.name < other.name

    def __gt__(self, other):
        return self.name > other.name

    def convert(self, kind="user"):
        """Convert to nice format for returning to user or inserting into db.

        Conversion to user format returns a dictinary with one element mapping
        metric name to metric value. Conversion to db format returns a
        dictionary with keys "name", "scoring", and "value" mapping to their
        respective values. Both formats convert np.floating values to Python
        floats.

        Parameters
        ----------
        kind : str
            One of "user" or "db"
        """

        try:
            value = float(self.value)
        except Exception:
            value = None

        if kind=="user":
            d = {
                self.name : value,
            }
        elif kind=="db":
            d = {
                "name"    : self.name,
                "scoring" : self.scoring,
                "value"   : value,
            }
        else:
            raise ValueError("Bad kind: {} ".format(kind))

        return d

    def to_string(self, kind="user"):
        """Convert to user/db format, then return string representation."""
        if kind=="user":
            return "{}: {}".format(self.name, self.value)
        else:
            raise NotImplementedError

    @classmethod
    def from_dict(cls, d, kind="user"):
        """Instantiate Metric from user/db format."""
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
        """Find the scoring type associated with the metric name."""
        def find_in_list(list_):
            for d in list_:
                if d["name"] == name:
                    return d["scoring"]
            return None

        result = find_in_list(featurefactory.modeling.model.Model.CLASSIFICATION_SCORING)
        if result is not None:
            return result
        result = find_in_list(featurefactory.modeling.model.Model.REGRESSION_SCORING)
        if result is not None:
            return result

        return None

class MetricList(MutableSequence):
    """MetricList"""

    def __init__(self, data=None):
        super().__init__()
        if data is not None:
            self._list = list(data)
        else:
            self._list = list()

    def __repr__(self):
        return repr(self._list)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, ii):
        return self._list[ii]

    def __delitem__(self, ii):
        del self._list[ii]

    def __setitem__(self, ii, val):
        self._list[ii] = val

    def __eq__(self, other):
        if not isinstance(other, MetricList):
            return False

        if len(self._list) != len(other._list):
            return False

        # Sort the lists based on Metric.name. This is because if we convert
        # the MetricList to a dictionary for returning to the user, the keys
        # are not in any sorted order.
        # TODO The interface of this collection should be a set.
        for x,y in zip(sorted(self._list), sorted(other._list)):
            if x != y:
                return False

        return True

    def insert(self, ii, val):
        self._list.insert(ii, val)

    def append(self, val):
        self._list.append(val)

    def to_string(self, kind="user"):
        """Get user-readable output."""
        metrics_str = "Feature evaluation metrics: \n"
        line_prefix = "    "
        line_suffix = "\n"
        if self._list:
            for metric in self._list:
                metrics_str += line_prefix + metric.to_string(kind=kind) + line_suffix
        else:
            metrics_str += line_prefix + "<no metrics returned>" + line_suffix

        return metrics_str

    def convert(self, kind="user"):
        """Convert underlying metric objects.

        Conversion to user format returns a dictionary with each element mapping
        metric name to metric value. Conversion to db format returns a
        list of dictionaries, each with keys "name", "scoring", and "value"
        mapping to their respective values. Both formats convert np.floating
        values to Python floats.

        Parameters
        ----------
        kind : str
            One of "user" or "db"
        """
        if kind=="user":
            metrics = {}
            for m in self._list:
                metrics.update(m.convert(kind="user"))
        elif kind=="db":
            metrics = []
            for m in self._list:
                metrics.append(m.convert(kind="db"))
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
        """Instantiate MetricList from supported format.
        
        Tries to detect the underlying format and deal with that appropriately.

        Parameters
        ----------
        obj: MetricList, dict, list of dict, or list of Metric
        """
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

# Normalized Discounted Cumulative Gain metric
# Source: https://gist.github.com/mblondel/7337391
def _dcg_score(y_true, y_score, k=5, gains="exponential"):
    """Discounted cumulative gain (DCG) at rank k

    Parameters
    ----------
    y_true : array-like, shape = [n_samples]
        Ground truth (true relevance labels).

    y_score : array-like, shape = [n_samples]
        Predicted scores.

    k : int
        Rank.

    gains : str
        Whether gains should be "exponential" (default) or "linear".

    Returns
    -------
    DCG @k : float
    """
    order = np.argsort(y_score)[::-1]
    y_true = np.take(y_true, order[:k])

    if gains == "exponential":
        gains = 2 ** y_true - 1
    elif gains == "linear":
        gains = y_true
    else:
        raise ValueError("Invalid gains option.")

    # highest rank is 1 so +2 instead of +1
    discounts = np.log2(np.arange(len(y_true)) + 2)
    return np.sum(gains / discounts)

def _ndcg_score(y_true, y_score, k=5, gains="exponential"):
    """Normalized discounted cumulative gain (NDCG) at rank k

    Parameters
    ----------
    y_true : array-like, shape = [n_samples]
        Ground truth (true relevance labels).

    y_score : array-like, shape = [n_samples]
        Predicted scores.

    k : int
        Rank.

    gains : str
        Whether gains should be "exponential" (default) or "linear".

    Returns
    -------
    NDCG @k : float
    """
    best = _dcg_score(y_true, y_true, k, gains)
    actual = _dcg_score(y_true, y_score, k, gains)
    return actual / best

_needs_proba=False
ndcg_scorer = sklearn.metrics.make_scorer("ndcg", _ndcg_score,
    greater_is_better=True, needs_proba=_needs_proba)

# RMSLE
def _root_mean_squared_log_error(y_true, y_pred, **kwargs):
    return np.sqrt(mean_squared_error(np.log(y_true + 1),
        np.log(y_pred + 1), **kwargs))

rmsle_scorer = sklearn.metrics.make_scorer("rmsle", _root_mean_squared_log_error,
