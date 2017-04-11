import sys
import os
import pandas
import requests
import collections

from featurefactory.util                         import compute_dataset_hash, run_isolated, get_source
from featurefactory.admin.sqlalchemy_declarative import Feature
from featurefactory.evaluation                   import EvaluationResponse
from featurefactory.user.model                   import Model

class EvaluationClient(object):
    def __init__(self, problem, user, orm, dataset=[]):
        self.problem = problem
        self.user    = user
        self.orm     = orm
        self.dataset = dataset

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
            metrics_str = EvaluationResponse._get_metrics_str(metrics)
            print(metrics_str)
            return metrics
        except ValueError as e:
            print("Feature is not valid: {}".format(str(e)), file=sys.stderr)
            return {}

    def _evaluate(self, feature, verbose=False):

        if verbose:
            vprint = print
        else:
            def do_nothing(*args, **kwargs): pass
            vprint = do_nothing

        assert isinstance(feature, collections.Callable), \
                "feature must be a function!"

        vprint("Obtaining dataset...", end='')
        self._load_dataset()
        vprint("done")


        vprint("Extracting features...", end='')
        X = run_isolated(feature, self.dataset)
        vprint("done")

        # confirm dataset has not been changed
        vprint("Verifying dataset integrity...", end='')
        new_hash = compute_dataset_hash(self.dataset)
        if self.__dataset_hash != new_hash:
            print("Old hash: {}".format(self.__dataset_hash))
            print("New hash: {}".format(new_hash))
            #TODO exception handling
            self._reload_dataset()
        vprint("done")

        # validate
        vprint("Validating feature values...", end='')
        result = self._validate_feature_values(X, self.dataset)
        if bool(result):
            raise ValueError(result)
        vprint("done")

        # extract label
        vprint("Extracting label...", end='')
        Y = self.dataset[self.problem.y_index][self.problem.y_column]
        vprint("done")

        # compute metrics
        metrics = self._compute_metrics(X, Y)
        return metrics

    def _compute_metrics(self, X, Y, verbose=False):
        if verbose:
            vprint = print
        else:
            def do_nothing(*args, **kwargs): pass
            vprint = do_nothing

        vprint("Computing cross validated score...", end='')
        model = Model(self.problem.problem_type)
        score_cv = model.cross_validate(X, Y)
        vprint("done")

        metrics = {
            "score_cv" : float(score_cv),
        }

        return metrics


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

        # must have the right shape
        expected_shape = (dataset[y_index].shape[0], 1)
        if feature_values.shape != expected_shape:
            result.append(
                "returns DataFrame of invalid shape "
                "(actual {}, expected {})".format(
                    feature_values.shape, expected_shape)
            )

        return "; ".join(result)

    def _load_dataset(self):
        """
        Load dataset if dataset is not present, and compute/re-compute dataset
        hash.
        """

        # TODO check for dtypes file, facilitating lower memory usage

        if not self.dataset:
            for filename in self.problem.files.split(","):
                abs_filename = os.path.join(self.problem.data_path, filename)
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

class Evaluator(EvaluationClient):
    def __init__(self, problem, user, orm, dataset=[]):
        super().__init__(problem, user, orm, dataset)

    def evaluate(self, feature):
        """
        Evaluate feature.

        Returns a dictionary with (metric => value) entries. If the feature is
        invalid, re-raises the ValueError.
        """
        try:
            return self._evaluate(feature, verbose=False)
        except ValueError as e:
            raise

    def register_feature(self, feature, description):
        """Register_feature is a no-op in this subclass."""
        pass
