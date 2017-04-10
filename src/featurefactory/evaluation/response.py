from flask import Response
import json

class EvaluationResponse(Response):
    """
    Wrapper class for response from evaluation server.

    Args
    ----
        status_code : string
            Possible values are EvaluationResponse static members.
        metrics : dict
            Dictionary mapping names of different metrics to floating point
            values.
    """

    STATUS_CODE_OKAY         = "okay"
    STATUS_CODE_BAD_REQUEST  = "bad_request"
    STATUS_CODE_BAD_AUTH     = "bad_auth"
    STATUS_CODE_BAD_FEATURE  = "bad_feature"
    STATUS_CODE_SERVER_ERROR = "server_error"
    STATUS_CODE_DB_ERROR     = "db_error"

    try_again = "Please try again later or contact administrator."

    def __init__(self, status_code=STATUS_CODE_OKAY, metrics={}):
        d = {
            "status_code" : status_code,
            "metrics"     : metrics,
        }
        response = json.dumps(d, indent=1, sort_keys=True)
        mimetype = "application/json"

        super().__init__(response=response, mimetype=mimetype)

        self.status_code1 = status_code
        self.metrics = metrics

    @classmethod
    def from_string(cls, string):
        """
        Create a new instance from a json-dumped string. This is useful for
        recreating the instance on the receiving end of the web connection.

        Args
        ----
            string : str
                Json-dumped string encoding the response.
        """

        d = json.loads(string)

        status_code = d["status_code"]
        metrics     = d["metrics"]

        return cls(status_code=status_code, metrics=metrics)

    def _get_explanation(self):
        """
        Return an explanation of the response status code.
        """

        if self.status_code1 == self.STATUS_CODE_OKAY:
            return "Feature registered successfully."
        elif self.status_code1 == self.STATUS_CODE_BAD_REQUEST:
            return "Oops -- failed to communicate with server. " + self.try_again
        elif self.status_code1 == self.STATUS_CODE_BAD_AUTH:
            return "Oops -- couldn't verify your identity. " + self.try_again
        elif self.status_code1 == self.STATUS_CODE_BAD_FEATURE:
            return "Feature is invalid and not registered. Try cross " + \
                    "validating it locally to see your problems."
        elif self.status_code1 == self.STATUS_CODE_SERVER_ERROR:
            return "Oops -- server failed to evaluate your feature. " + \
                self.try_again
        elif self.status_code1 == self.STATUS_CODE_DB_ERROR:
            return "Oops -- failed to register feature with database. " + \
                self.try_again 
        else:
            return ""

    def __str__(self):
        """
        Return a descriptive representation of the response suitable for showing
        Feature Factory users.
        """

        explanation = self._get_explanation()

        metrics_str = "Feature evaluation metrics: "
        line_prefix = "\n    "
        if self.metrics:
            for key in self.metrics:
                metrics_str += line_prefix + "{}: {}".format(key, self.metrics[key])
        else:
            metrics_str += line_prefix + "<no metrics returned>"

        return explanation + "\n\n" + metrics_str
