from featurefactory.user.session import Session
from featurefactory.modeling import Metric, MetricList

def test_print_one_feature():
    feature_description = "Age"
    feature_id = 1
    feature_code = "def age(dataset):" + \
                   "    pass"
    metric_list = MetricList()
    metric_list.append(Metric("Accuracy", "accuracy", 0.1))
    metric_list.append(Metric("Precision", "precision", 0.5))
    metric_list_user = [(metric.name, metric.value) for metric in metric_list]

    Session._print_one_feature(feature_description, feature_id, feature_code,
            metric_list_user)
