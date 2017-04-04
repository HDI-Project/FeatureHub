from flask import Response
from json import dumps

class EvaluationResponse(Response):
    """
    Wrapper class for response from evaluation server.

    Args
    - `status_code`: Possible values are EvaluationResponse static members.
    - `metrics`: Dictionary mapping names of different metrics to floating
      point values.
    """

    STATUS_CODE_OKAY         = "okay"
    STATUS_CODE_BAD_REQUEST  = "bad_request"
    STATUS_CODE_BAD_FEATURE  = "bad_feature"
    STATUS_CODE_SERVER_ERROR = "server_error"
    STATUS_CODE_DB_ERROR     = "db_error"

    def __init__(self, status_code=0, metrics={}):
        d = {
            "status_code" : status_code,
            "metrics" : metrics,
        }
        response = dumps(d, indent=1, sort_keys=True)
        mimetype = "application/json"

        super().__init__(response=response, mimetype=mimetype)
