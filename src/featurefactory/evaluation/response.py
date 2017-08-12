import json
from flask import Response
from featurefactory.modeling import MetricList
from featurefactory.util import TRY_AGAIN_LATER

class EvaluationResponse(Response):
    """Wrapper class for response from evaluation server.

    Parameters
    ----
    status_code : string, optional (default=EvaluationResponse.STATUS_CODE_OKAY)
        Possible values are EvaluationResponse static members.
    metrics : list of Metric, optional (default=None)
        List of Metric objects, which each encode metric name, metric scoring
        method, and value.
    topic_url : str

    Examples
    --------
    >>> EvaluationResponse(status_code=EvaluationResponse.STATUS_CODE_SERVER_ERROR)
    """

    STATUS_CODE_OKAY              = "okay"
    STATUS_CODE_BAD_REQUEST       = "bad_request"
    STATUS_CODE_BAD_AUTH          = "bad_auth"
    STATUS_CODE_BAD_FEATURE       = "bad_feature"
    STATUS_CODE_DUPLICATE_FEATURE = "duplicate_feature"
    STATUS_CODE_SERVER_ERROR      = "server_error"
    STATUS_CODE_DB_ERROR          = "db_error"

    def __init__(self, status_code=STATUS_CODE_OKAY, metrics=None,
            topic_url=""):
        if metrics is not None:
            metrics = MetricList.from_object(metrics).convert(kind="user")

        d = {
            "status_code" : status_code,
            "metrics"     : metrics,
            "topic_url"   : topic_url,
        }
        response = json.dumps(d, indent=1, sort_keys=True)
        mimetype = "application/json"

        super().__init__(response=response, mimetype=mimetype)

        self.status_code1 = status_code
        self.metrics = metrics
        self.topic_url = topic_url


    @classmethod
    def from_string(cls, string):
        """Instantiate EvaluationResponse from a json-dumped string.
        
        This is useful for recreating the instance on the receiving end of the
        web connection.

        Parameters
        ----------
        string : str
            Json-dumped string encoding the response.
        """

        d = json.loads(string)

        status_code = d["status_code"]
        metrics     = d["metrics"]
        topic_url   = d["topic_url"]

        return cls(status_code=status_code, metrics=metrics, topic_url=topic_url)

    def _get_explanation(self):
        """Return an explanation of the response status code."""

        if self.status_code1 == self.STATUS_CODE_OKAY:
            return "Feature registered successfully."
        elif self.status_code1 == self.STATUS_CODE_BAD_REQUEST:
            return "Oops -- failed to communicate with server. " \
                + TRY_AGAIN_LATER
        elif self.status_code1 == self.STATUS_CODE_BAD_AUTH:
            return "Oops -- couldn't verify your identity. " \
                + TRY_AGAIN_LATER
        elif self.status_code1 == self.STATUS_CODE_BAD_FEATURE:
            return ("Feature is invalid and not registered. Try evaluating"
                    " it locally to see your problems.")
        elif self.status_code1 == self.STATUS_CODE_DUPLICATE_FEATURE:
            return "Feature is already registered."
        elif self.status_code1 == self.STATUS_CODE_SERVER_ERROR:
            return "Oops -- server failed to evaluate your feature. " \
                + TRY_AGAIN_LATER
        elif self.status_code1 == self.STATUS_CODE_DB_ERROR:
            return "Oops -- failed to register feature with database. " \
                + TRY_AGAIN_LATER
        else:
            return ""

    def _get_metrics_str(self):
        return MetricList.from_object(self.metrics).to_string(kind="user")

    def _get_topic_url_str(self):
        topic_url = self.topic_url if self.topic_url else "<not available>"
        return "Feature posted to forum => {}".format(topic_url)

    def __str__(self):
        """ Return string representation of response.

        Return a descriptive representation of the response suitable for showing
        FeatureHub users.
        """
        explanation = self._get_explanation()
        metrics_str = self._get_metrics_str()
        result = explanation + "\n\n" + metrics_str 
        if self.topic_url:
            topic_url_str = self._get_topic_url_str()
            result += "\n" + topic_url_str
        return result
