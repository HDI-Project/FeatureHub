import sys
import os
import pandas
import requests
import collections
import traceback

from featurefactory.util                         import compute_dataset_hash, run_isolated, get_source
from featurefactory.admin.sqlalchemy_declarative import Problem
from featurefactory.evaluation                   import EvaluationResponse
from featurefactory.user.model                   import Model

class EvaluationClient(object):
    def __init__(self, problem_id, username, orm, dataset=[]):
        self.problem_id = problem_id
        self.username  = username
        self.orm       = orm
        self.dataset   = dataset

        if self.dataset:
            self.__dataset_hash = compute_dataset_hash(self.dataset)
        else:
            self.__dataset_hash = None

    def register_feature(self, feature, description):
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

        if verbose:
            vprint = print
        else:
            def do_nothing(*args, **kwargs): pass
            vprint = do_nothing

        vprint("Obtaining dataset...", end='')
        self._load_dataset()
        vprint("done")


        vprint("Extracting features...", end='')
        X = self._extract_features(feature)
        vprint("done")

        # confirm dataset has not been changed
        vprint("Verifying dataset integrity...", end='')
        self._verify_dataset_integrity()
        vprint("done")

        # validate
        vprint("Validating feature values...", end='')
        result = self._validate_feature_values(X)
        vprint("done")

        # extract label
        vprint("Extracting label...", end='')
        Y = self._extract_label()
        vprint("done")

        # compute metrics
        vprint("Computing metrics...", end='')
        metrics = self._compute_metrics(X, Y)
        vprint("done")

        return metrics

    #
    # The rest of these methods are subroutines within _evaluate, or utility
    # functions of those subroutines.
    #

    def _compute_metrics(self, X, Y):
        with self.orm.session_scope() as session:
            # TODO this may be a sub-transaction
            problem = session.query(Problem).filter(Problem.id == self.problem_id).one()
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
            problem  = session.query(Problem).filter(Problem.id == self.problem_id).one()
            y_index  = problem.y_index
            y_column = problem.y_column
        return self.dataset[y_index][y_column]

    def _load_dataset(self):
        """
        Load dataset if dataset is not present, and compute/re-compute dataset
        hash.
        """

        # TODO check for dtypes file, facilitating lower memory usage

        if not self.dataset:
            with self.orm.session_scope() as session:
                # TODO this may be a sub-transaction
                problem = session.query(Problem).filter(Problem.id == self.problem_id).one()
                problem_files = problem.files
                problem_data_path = problem.data_path

            for filename in problem_files.split(","):
                abs_filename = os.path.join(problem_data_path, filename)
                self.dataset.append(pandas.read_csv(abs_filename, low_memory=False))

            # compute/recompute hash
            self.__dataset_hash = compute_dataset_hash(self.dataset)

        if self.dataset and not self.__dataset_hash:
            self.__dataset_hash = compute_dataset_hash(self.dataset)


        return self.dataset

    def _reload_dataset(self):
        """
        Force reload of dataset.
        """
        self.dataset = []
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
            y_index = problem.y_index

        result = []

        # must be a data frame
        if not isinstance(feature_values, pandas.core.frame.DataFrame):
            result.append("does not return DataFrame")
            return "; ".join(result)

        # must have the right shape
        expected_shape = (self.dataset[y_index].shape[0], 1)
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

class Evaluator(EvaluationClient):
    def __init__(self, problem_id, username, orm, dataset=[]):
        super().__init__(problem_id, username, orm, dataset)

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
