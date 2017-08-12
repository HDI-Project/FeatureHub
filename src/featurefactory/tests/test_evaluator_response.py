from featurehub.evaluation import EvaluationResponse

def test_response_status_code_only():
    all_status_codes = [
        EvaluationResponse.STATUS_CODE_BAD_REQUEST,
        EvaluationResponse.STATUS_CODE_OKAY,
        EvaluationResponse.STATUS_CODE_BAD_AUTH,
        EvaluationResponse.STATUS_CODE_BAD_FEATURE,
        EvaluationResponse.STATUS_CODE_SERVER_ERROR,
        EvaluationResponse.STATUS_CODE_DB_ERROR
    ]
    for status_code in all_status_codes:
        _test_response_status_code_only(status_code)

def _test_response_status_code_only(status_code):
    # create response
    response = EvaluationResponse(status_code = status_code)

    # string methods
    metrics_str = response._get_metrics_str()
    explanation_str = response._get_explanation()
    response_str = str(response)


    # re-read response
    text = response.get_data(as_text=True)
    response1 = EvaluationResponse.from_string(text)

    # string methods
    metrics1_str     = response1._get_metrics_str()
    explanation1_str = response1._get_explanation()
    response1_str    = str(response1)

    assert metrics_str     == metrics1_str
    assert explanation_str == explanation1_str
    assert response_str    == response1_str
