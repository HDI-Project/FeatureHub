import sys
import os
import pandas
import requests
import collections
import traceback

from featurefactory.util import (
    compute_dataset_hash, run_isolated, get_source, possibly_talking_action,
    myhash

)
from featurefactory.admin.sqlalchemy_declarative import Problem, Feature
from featurefactory.evaluation                   import EvaluationResponse
from featurefactory.modeling                     import Model

class EvaluatorClient(object):
    def __init__(self, problem_id, username, orm, dataset={}):
        self.problem_id = problem_id
        self.username  = username
        self.orm       = orm
        self.dataset   = dataset

        if self.dataset:
            self.__dataset_hash = compute_dataset_hash(self.dataset)
        else:
            self.__dataset_hash = None

    def check_if_registered(self, feature, verbose=False):
        code    = get_source(feature)
        return self._check_if_registered(code, verbose=verbose)

    def _check_if_registered(self, code, verbose=False):
        md5 = myhash(code)

        with self.orm.session_scope() as session:
            filters = (
                Feature.problem_id == self.problem_id,
                Feature.md5        == md5,
            )
            query = session.query(Feature).filter(*filters)
            result = query.scalar()

        if result:
            if verbose:
                print("Feature already registered.")
            return True

        return False

    def register_feature(self, feature, description):
        """
        """
        # request from eval-server directly
        url = "http://{}:{}/services/eval-server/evaluate".format(
            os.environ["EVAL_CONTAINER_NAME"],
            os.environ["EVAL_CONTAINER_PORT"]
        )
        code = get_source(feature)
        data = {
            "database"    : self.orm.database,
            "problem_id"  : self.problem_id,
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
            except Exception as e:
                # TODO
                print("response failed with exception")
                print(traceback.format_exc(), file=sys.stderr)
                try:
                    print(response, file=sys.stderr)
                    print(response.text, file=sys.stderr)
                except Exception:
                    pass
        else:
            # TODO
            print("response failed with bad status code")
            try:
                print(response, file=sys.stderr)
                print(response.text, file=sys.stderr)
            except Exception:
                pass

    def evaluate(self, feature):
        """
        Evaluate feature.

        Prints results and returns a dictionary with (metric => value) entries.
        If the feature is invalid, prints reason and returns empty dictionary.

        Args
        ----
            feature : function
                Feature to evaluate
        """
        try:
            metrics = self._evaluate(feature, verbose=True)
            metrics_str = metrics.to_string(kind="user")
            metrics_user = metrics.convert(kind="user")
            print(metrics_str)
            return metrics_user
        except ValueError as e:
            print("Feature is not valid: {}".format(str(e)), file=sys.stderr)
            return {}

    def _evaluate(self, feature, verbose=False):

        with possibly_talking_action("Obtaining dataset...", verbose):
            self._load_dataset()

        with possibly_talking_action("Extracting features...", verbose):
            X = self._extract_features(feature)

        # confirm dataset has not been changed
        with possibly_talking_action("Verifying dataset integrity...", verbose):
            self._verify_dataset_integrity()

        # validate
        with possibly_talking_action("Validating feature values...", verbose):
            result = self._validate_feature_values(X)

        # extract label
        with possibly_talking_action("Extracting label...", verbose):
            Y = self._extract_label()

        # compute metrics
        with possibly_talking_action("Computing metrics...", verbose):
            metrics = self._compute_metrics(X, Y)

        return metrics

    #
    # The rest of these methods are subroutines within _evaluate, or utility
    # functions of those subroutines.
    #

    def _compute_metrics(self, X, Y):
        with self.orm.session_scope() as session:
            # TODO this may be a sub-transaction
            problem = session.query(Problem)\
                    .filter(Problem.id == self.problem_id).one()
            problem_type = problem.problem_type
        model = Model(problem_type)
        metrics = model.compute_metrics(X, Y)

        return metrics

    def _extract_features(self, feature):
        """
        """
        assert isinstance(feature, collections.Callable), \
                "feature must be a function!"

        return run_isolated(feature, self.dataset)

    def _extract_label(self):
        with self.orm.session_scope() as session:
            problem = session.query(Problem)\
                    .filter(Problem.id == self.problem_id).one()
            target_table_name = problem.target_table_name
            y_column          = problem.y_column
        return self.dataset[target_table_name][y_column]

    def _load_dataset(self):
        """
        Load dataset if dataset is not present, and compute/re-compute dataset
        hash.
        """

        # TODO check for dtypes file, facilitating lower memory usage

        if not self.dataset:
            with self.orm.session_scope() as session:
                # TODO this may be a sub-transaction
                problem = session.query(Problem)\
                        .filter(Problem.id == self.problem_id).one()
                problem_files = problem.files
                problem_table_names = problem.table_names
                problem_data_path = problem.data_path

            for (filename, table_name) in zip(problem_files.split(","),
                    problem_table_names.split(",")):
                abs_filename = os.path.join(problem_data_path, filename)
                self.dataset[table_name] = pandas.read_csv(abs_filename,
                        low_memory=False)

            # compute/recompute hash
            self.__dataset_hash = compute_dataset_hash(self.dataset)

        if self.dataset and not self.__dataset_hash:
            self.__dataset_hash = compute_dataset_hash(self.dataset)


        return self.dataset

    def _reload_dataset(self):
        """
        Force reload of dataset.
        """
        self.dataset = {}
        self._load_dataset()

    def _validate_feature_values(self, feature_values):
        """
        Return validity of feature values.

        Currently checks if the feature is a DataFrame of the correct
        dimensions. If the feature is valid, returns an empty string. Otherwise,
        returns a semicolon-delimited list of reasons that the feature is
        invalid.
        """

        with self.orm.session_scope() as session:
            # TODO this may be a sub-transaction
            problem = session.query(Problem).filter(Problem.id == self.problem_id).one()
            target_table_name = problem.target_table_name

        result = []

        # must be a data frame
        if not isinstance(feature_values, pandas.core.frame.DataFrame):
            result.append("does not return DataFrame")
            return "; ".join(result)

        # must have the right shape
        expected_shape = (self.dataset[target_table_name].shape[0], 1)
        if feature_values.shape != expected_shape:
            result.append(
                "returns DataFrame of invalid shape "
                "(actual {}, expected {})".format(
                    feature_values.shape, expected_shape)
            )

        result = "; ".join(result)

        if bool(result):
            raise ValueError(result)

        return result

    def _verify_dataset_integrity(self):
        """
        """
        new_hash = compute_dataset_hash(self.dataset)
        if self.__dataset_hash != new_hash:
            print("Old hash: {}".format(self.__dataset_hash), file=sys.stderr)
            print("New hash: {}".format(new_hash), file=sys.stderr)
            #TODO exception handling
            self._reload_dataset()

class EvaluatorServer(EvaluatorClient):
    def __init__(self, problem_id, username, orm, dataset={}):
        super().__init__(problem_id, username, orm, dataset)

    def check_if_registered(self, code, verbose=False):
        """
        Check if feature is registered.

        Overwrites client method by expecting code to be passed directly. This
        is because on the server, we are limited to be unable to do code ->
        function -> code.
        """
        return self._check_if_registered(code, verbose=verbose)

    def evaluate(self, feature):
        """
        Evaluate feature.

        Returns a dictionary with (metric => value) entries. If the feature is
        invalid, re-raises the ValueError.
        """
        try:
            metrics = self._evaluate(feature, verbose=False)
            return metrics
        except ValueError as e:
            raise

    def register_feature(self, feature, description):
        """Register_feature is a no-op in this subclass."""
        pass

    def _compute_metrics(self, X, Y, verbose=False):
        # doesn't do anything different
        metrics = super()._compute_metrics(X, Y)
        return metrics

    def _verify_dataset_integrity(self):
        # Don't need to verify dataset integrity on server because we re-load
        # the dataset for every new feature.
        pass
