from featurefactory.modeling import Metric, MetricList

def test_metric():
    name    = "Accuracy"
    scoring = "accuracy"
    value   = 0.0

    _test_metric(name, scoring, value)

def _test_metric(name, scoring, value):
    metric = Metric(name, scoring, value)

    print('metric.convert(kind="user")')
    print(metric.convert(kind="user"))
    print('metric.convert(kind="db")')
    print(metric.convert(kind="db"))
    assert metric == Metric.from_dict(metric.convert(kind="user"), kind="user")
    assert metric == Metric.from_dict(metric.convert(kind="db"), kind="db")

def test_metric_list():
    # create list
    metric_list = MetricList()
    assert metric_list == metric_list

    metric_list1 = MetricList()
    assert metric_list1 == metric_list


    # add elements
    metric_list.append(Metric("Accuracy", "accuracy", 0.0))
    metric_list.append(Metric("Precision", "precision", 0.5))

    metric_list2 = MetricList()
    metric_list2.append(Metric("Accuracy", "accuracy", 0.0))
    metric_list2.append(Metric("Precision", "precision", 0.5))

    # check equality operations
    assert metric_list == metric_list
    assert metric_list == metric_list2

    # check non-equality
    metric_list1.append(Metric("Recall", "recall", 0.7))
    assert metric_list1 != metric_list

    print(metric_list)
    print(metric_list2)
    metric_list2[1] = Metric("Precision", "precision", 0.4)
    assert metric_list2 != metric_list

    # check inverses
    assert metric_list == MetricList.from_dict_user(metric_list.convert(kind="user"))
    assert metric_list == MetricList.from_list_db(metric_list.convert(kind="db"))
    assert metric_list == MetricList.from_object(metric_list.convert(kind="user"))
    assert metric_list == MetricList.from_object(metric_list.convert(kind="db"))
