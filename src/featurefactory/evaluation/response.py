class EvaluationResponse:
    """
    Wrapper class for response from evaluation server.
    """
    STATUS_CODE_OKAY = "okay"
    STATUS_CODE_BAD_REQUEST = "bad_request"
    STATUS_CODE_BAD_FEATURE = "bad_feature"
    STATUS_CODE_SERVER_ERROR = "server_error"
    STATUS_CODE_DB_ERROR = "db_error"

    def __init__(self, status_code=0, metrics={}):
        """
        Args
        - `status_code`: Possible values are EvaluationResponse static members.
        - `metrics`: Dictionary mapping names of different metrics to floating
          point values.
        """
        self.status_code = status_code
        self.metrics = metrics

    def to_response(self):
        """
        Return Response object encoding status code and metrics.
        """
        d = {
            "status_code" : self.status_code,
            "metrics" : metrics,
        }
        return Response(
            json.dumps(d, indent=1, sort_keys=True),
            mimetype="application/json",
            )
