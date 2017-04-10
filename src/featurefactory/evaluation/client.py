from __future__ import print_function

import sys
import os
import hashlib
import pandas
import requests

from featurefactory.util import compute_dataset_hash, run_isolated, get_source
from featurefactory.admin.sqlalchemy_declarative import Feature
from featurefactory.evaluation import EvaluationResponse

class EvaluationClient(object):
    def __init__(self, problem, user, orm):
        self.problem = problem
        self.user = user
        self.orm = orm

        self.dataset = [] # TODO

    def register_feature(self, feature, description):
        # request from eval-server directly
        url = "http://{}:{}/services/eval-server/evaluate".format(
            os.environ["EVAL_CONTAINER_NAME"],
            os.environ["EVAL_CONTAINER_PORT"]
        )
        code = get_source(feature)
        data = {
            "database"    : self.orm.database,
            "problem_id"  : self.problem.id,
            "code"        : code,
            "description" : description,
        }
        headers = { 
            "Authorization" : "token {}".format(
                os.environ["JUPYTERHUB_API_TOKEN"]),
        }

        response = requests.post(url=url, data=data, headers=headers)

        if response.ok:
            try:
                eval_response = EvaluationResponse.from_string(response.text)
                print(eval_response)
            except Exception:
                # TODO
                print("response failed")
                try:
                    print(response.text, file=sys.stderr)
                except Exception:
                    pass
        else:
            # TODO
            print("response failed")
            try:
                print(response.text, file=sys.stderr)
            except Exception:
                pass


    def _is_valid_feature(self, feature, dataset):
        """
        Return whether feature values are valid.
        """

        # _validate_feature returns empty string on success
        return not bool(self._validate_feature(feature, dataset))

    def _validate_feature(self, feature, dataset):
        """
        Extract feature values from feature function, then validate values.
        """

        # Run feature in isolated env, but reload dataset if changed.
        dataset_hash = compute_dataset_hash(dataset)
        feature_values = run_isolated(feature, dataset)
        if dataset_hash != compute_dataset_hash(dataset):
            # TODO
            raise Exception

        return self._validate_feature_values(feature_values, dataset)

    def _validate_feature_values(self, feature_values, dataset):
        """
        Return validity of feature values.

        Currently checks if the feature is a DataFrame of the correct
        dimensions. If the feature is valid, returns an empty string. Otherwise,
        returns a semicolon-delimited list of reasons that the feature is
        invalid.
        """

        y_index = self.problem.y_index

        result = []

        # must be a data frame
        if not isinstance(feature_values, pandas.core.frame.DataFrame):
            result.append("does not return DataFrame")
            return "; ".join(result)

        expected_shape = (dataset[y_index].shape[0], 1)
        if feature_values.shape != expected_shape:
            result.append(
                "returns DataFrame of invalid shape "
                "(actual {}, expected {})".format(
                    feature_values.shape, expected_shape)
            )

        return "; ".join(result)

    def _load_dataset(self):
        # TODO check for dtypes file, assisting in low memory usage

        if not self.dataset:
            for filename in self.problem.files.split(","):
                abs_filename = os.path.join(self.problem.data_path, filename)
                self.dataset.append(pandas.read_csv(abs_filename, low_memory=False))

        return self.dataset

    def _cross_validate(self, feature):
        return -1.0

class Evaluator(EvaluationClient):
    def __init__(self, problem, user, orm):
        super().__init__(problem, user, orm)

    def evaluate(self, feature):
        """
        Evaluate feature. Returns a dictionary with (metric => value) entries.

        Args
        ----
            feature : function
                Feature to evaluate
        """
        dataset = self._load_dataset()

        if self._is_valid_feature(feature, dataset):
            score_cv = float(self._cross_validate(feature))
        else:
            raise ValueError

        metrics = {
            "score_cv" : score_cv,
        }

        return metrics

    def register_feature(self, feature, description):
        """
        Register_feature is a no-op in this subclass.
        """

        pass
