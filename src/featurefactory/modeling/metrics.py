from collections import MutableSequence
import featurefactory.modeling.model

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

    def __lt__(self, other):
        return self.name < other.name

    def __gt__(self, other):
        return self.name > other.name

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

        result = find_in_list(featurefactory.modeling.model.Model.CLASSIFICATION_SCORING)
        if result is not None:
            return result
        result = find_in_list(featurefactory.modeling.model.Model.REGRESSION_SCORING)
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

        # Sort the lists based on Metric.name. This is because if we convert
        # the MetricList to a dictionary for returning to the user, the keys
        # are not in any sorted order.
        # TODO The interface of this collection should be a set.
        for x,y in zip(sorted(self._list), sorted(other._list)):
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
