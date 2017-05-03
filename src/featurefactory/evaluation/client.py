import sys
import os
import json
import pandas as pd
import requests
import collections
import dill
import traceback
from urllib.parse import quote_from_bytes

from featurefactory.util import (
    compute_dataset_hash, run_isolated, get_source, possibly_talking_action,
    myhash, concat_datasets
)
from featurefactory.admin.sqlalchemy_declarative import Problem, Feature
from featurefactory.evaluation                   import EvaluationResponse
from featurefactory.modeling                     import Model

class EvaluatorClient(object):
    def __init__(self, problem_id, username, orm, dataset={}, target=None,
            entities_featurized=None):
        self.problem_id          = problem_id
        self.username            = username
        self.orm                 = orm
        self.dataset             = dataset
        self.target              = target
        self.entities_featurized = entities_featurized

        if self.dataset:
            self.__dataset_hash = compute_dataset_hash(self.dataset)
        else:
            self.__dataset_hash = None

    def check_if_registered(self, feature, verbose=False):
        """Check if feature is registered.

        Extracts source code, then looks for the identical source code in the
        feature database.

        Parameters
        ----------
        feature : function
        verbose : bool
            Whether to print output.
        """
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

    def submit(self, feature, description):
        """Submit feature to server for evaluation on test data.
        
        If successful, registers feature in feature database and returns key
        performance metrics.

        Runs the feature in an isolated environment to extract the feature
        values. Validates the feature values. Then, builds a model on that one
        feature, performs cross validation, and returns key performance
        metrics.

        Parameters
        ----------
        feature : function
            Feature to evaluate
        description : str
            Feature description
        """
        # request from eval-server directly
        url = "http://{}:{}/services/eval-server/evaluate".format(
            os.environ.get("EVAL_CONTAINER_NAME"),
            os.environ.get("EVAL_CONTAINER_PORT")
        )
        feature_dill = quote_from_bytes(dill.dumps(feature))
        code = get_source(feature)
        data = {
            "database"    : self.orm.database,
            "problem_id"  : self.problem_id,
            "feature_dill": feature_dill,
            "code"        : code,
            "description" : description,
        }
        headers = {
            "Authorization" : "token {}".format(
                os.environ.get("JUPYTERHUB_API_TOKEN")),
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
        """Evaluate feature on training dataset and return key performance metrics.

        Runs the feature in an isolated environment to extract the feature
        values. Validates the feature values. Then, builds a model on that one
        feature and computes key cross-validated metrics. Prints results and
        returns a dictionary with (metric => value) entries. If the feature is
        invalid, prints reason and returns empty dictionary.

        Parameters
        ----------
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
            print(traceback.format_exc(), file=sys.stderr)
            return {}

    def _evaluate(self, feature, verbose=False):

        with possibly_talking_action("Obtaining dataset...", verbose):
            self._load_dataset()

        with possibly_talking_action("Extracting features...", verbose):
            feature_values = self._extract_features(feature)

        # confirm dataset has not been changed
        with possibly_talking_action("Verifying dataset integrity...", verbose):
            self._verify_dataset_integrity()

        # validate
        with possibly_talking_action("Validating feature values...", verbose):
            result = self._validate_feature_values(feature_values)

        # full feature matrix
        with possibly_talking_action("Building full feature matrix...",
                verbose):
            X = self._build_feature_matrix(feature_values)

        # target values
        # with possibly_talking_action("Extracting target values...", verbose):
        Y = self._extract_label()

        # compute metrics
        with possibly_talking_action("Fitting model and computing metrics...", verbose):
            metrics = self._compute_metrics(X, Y)

        return metrics

    #
    # The rest of these methods are subroutines within _evaluate, or utility
    # functions of those subroutines.
    #

    def _create_model(self):
        with self.orm.session_scope() as session:
            problem = session.query(Problem)\
                    .filter(Problem.id == self.problem_id).one()
            problem_type = problem.problem_type
        return Model(problem_type)

    def _compute_metrics(self, X, Y):
        model = self._create_model()
        metrics = model.compute_metrics_cv(X, Y)

        return metrics

    def _extract_features(self, feature):
        assert isinstance(feature, collections.Callable), \
                "feature must be a function!"

        return run_isolated(feature, self.dataset)

    def _extract_label(self):
        if pd.DataFrame(self.target).empty:
            self._load_dataset()

        return self.target

    def _load_dataset_split(self, split, dataset, entities_featurized, target,
            dataset_hash=None, compute_hash=True):
        # query db for import parameters to load files
        is_present_dataset = bool(dataset)
        is_present_entities_featurized = not pd.DataFrame(entities_featurized).empty
        is_present_target = not pd.DataFrame(target).empty
        is_anything_missing = not all(
                [is_present_dataset, is_present_entities_featurized, is_present_target])

        if is_anything_missing:
            with self.orm.session_scope() as session:
                problem = session.query(Problem)\
                        .filter(Problem.id == self.problem_id).one()
                problem_data_dir = getattr(problem,
                        "data_dir_{}".format(split))
                problem_files = json.loads(problem.files)
                problem_table_names = json.loads(problem.table_names)
                problem_entities_featurized_table_name = \
                    problem.entities_featurized_table_name
                problem_target_table_name = problem.target_table_name

        # load entities and other tables
        if not is_present_dataset:
            # load other tables
            for (table_name, filename) in zip (problem_table_names,
                    problem_files):
                if table_name == problem_entities_featurized_table_name or \
                   table_name == problem_target_table_name:
                    continue
                abs_filename = os.path.join(problem_data_dir, filename)
                dataset[table_name] = pd.read_csv(abs_filename,
                        low_memory=False)

                # compute/recompute hash
                if compute_hash:
                    dataset_hash = compute_dataset_hash(dataset)
                else:
                    dataset_hash = None

        # recompute dataset hash. condition only met if we dataset has already
        # loaded, but dataset hash had not been computed. (because we just
        # computed hash several lines above!)
        if compute_hash:
            if not dataset_hash:
                dataset_hash = compute_dataset_hash(dataset)

        # load entities featurized
        if not is_present_entities_featurized:
            # if empty string, we simply don't have any features to add
            if problem_entities_featurized_table_name:
                cols = list(problem_table_names)
                ind_features = cols.index(problem_entities_featurized_table_name)
                abs_filename = os.path.join(problem_data_dir,
                        problem_files[ind_features])
                entities_featurized = pd.read_csv(abs_filename,
                        low_memory=False)

        # load target
        if not is_present_target:
            cols = list(problem_table_names)
            ind_target = cols.index(problem_target_table_name)
            abs_filename = os.path.join(problem_data_dir,
                    problem_files[ind_target]) 
            target = pd.read_csv(abs_filename, low_memory=False)

        return dataset, entities_featurized, target, dataset_hash

    def _load_dataset(self):
        """Load dataset if not present.
        
        Also computes/re-computes dataset hash.
        """

        # TODO check for dtypes file, facilitating lower memory usage

        self.dataset, self.entities_featurized, self.target, \
            self.__dataset_hash = self._load_dataset_split("train",
            self.dataset, self.entities_featurized, self.target,
            self.__dataset_hash)

    def _reload_dataset(self):
        """Force reload of dataset.

        Doesn't reload entities_featurized or target, because we only call this
        routine when the dataset hash has changed.
        """
        self.dataset = {}
        self._load_dataset()

    def _validate_feature_values(self, feature_values):
        """Check whether feature values are valid.

        Currently checks if the feature is a DataFrame of the correct
        dimensions. If the feature is valid, returns an empty string. Otherwise,
        raises ValueError with message of a str containing a semicolon-delimited
        list of reasons that the feature is invalid.

        Parameters
        ----------
        feature_values : np array-like

        Returns
        -------
        Empty string if feature values are valid.

        Raises
        ------
        ValueError with message of a str containing semicolon-delimited list of
        reasons that the feature is invalid.
        """

        problems = []

        # must be coerced to DataFrame
        try:
            feature_values_df = pd.DataFrame(feature_values)
        except Exception:
            problems.append("cannot be coerced to DataFrame")
            problems = "; ".join(problems)
            raise ValueError(problems)

        if pd.DataFrame(self.target).empty:
            self._load_dataset()

        # must have the right shape
        expected_shape = (self.target.shape[0], 1) # pylint: disable=no-member
        if feature_values_df.shape != expected_shape:
            problems.append(
                "returns DataFrame of invalid shape "
                "(actual {}, expected {})".format(
                    feature_values_df.shape, expected_shape)
            )

        problems = "; ".join(problems)

        if problems:
            raise ValueError(problems)

        # problems must be an empty string
        return problems

    def _verify_dataset_integrity(self):
        new_hash = compute_dataset_hash(self.dataset)
        if self.__dataset_hash != new_hash:
            print("Old hash: {}".format(self.__dataset_hash), file=sys.stderr)
            print("New hash: {}".format(new_hash), file=sys.stderr)
            #TODO exception handling
            self._reload_dataset()

    def _build_feature_matrix(self, feature_values):
        values_df = pd.DataFrame(feature_values)
        if not pd.DataFrame(self.entities_featurized).empty:
            X = pd.concat([self.entities_featurized, values_df], axis=1) 
        else:
            X = values_df
        return X

class EvaluatorServer(EvaluatorClient):
    def __init__(self, problem_id, username, orm):
        super().__init__(problem_id, username, orm)

        # separate training and testing datasets
        self.dataset_train             = {}
        self.target_train              = None
        self.entities_featurized_train = None
        self.dataset_test              = {}
        self.target_test               = None
        self.entities_featurized_test  = None

    def check_if_registered(self, code, verbose=False):
        """Check if feature is registered.

        Overwrites client method by expecting code to be passed directly. This
        is because on the server, we are limited to be unable to do code ->
        function -> code.

        Parameters
        ----------
        code : str
        verbose : bool, optional (default=False)
            Whether to print output.
        """
        return self._check_if_registered(code, verbose=verbose)

    def evaluate(self, feature):
        """Evaluate feature.

        Returns a dictionary with (metric => value) entries. If the feature is
        invalid, re-raises the ValueError.

        Parameters
        ----------
        feature : function
            Feature to evaluate
        """
        try:
            metrics = self._evaluate(feature, verbose=False)
            return metrics
        except ValueError as e:
            raise

    def submit(self, feature, description):
        """Does nothing.

        This class is instantiated at the server, thus we are already
        registering the feature.
        """
        pass

    def _compute_metrics(self, X, Y):
        model = self._create_model()

        # split X and Y into train and test
        n = len(self.target_train)
        metrics = model.compute_metrics_train_test(X, Y, n)

        return metrics

    def _verify_dataset_integrity(self):
        """Does nothing.

        Don't need to verify dataset integrity on server because we re-load
        the dataset for every new feature.
        """
        pass

    def _load_dataset(self):
        # load dataset for train data
        self.dataset_train, self.entities_featurized_train, \
                self.target_train, _ = self._load_dataset_split("train",
                self.dataset_train, self.entities_featurized_train,
                self.target_train, compute_hash=False)

        # load dataset for test data
        self.dataset_test, self.entities_featurized_test, \
                self.target_test, _ = self._load_dataset_split("test",
                self.dataset_test, self.entities_featurized_test,
                self.target_test, compute_hash=False)

        # concatenate as applicable
        self.dataset = concat_datasets(self.dataset_train, self.dataset_test)
        try:
            self.entities_featurized = pd.concat([self.entities_featurized_train,
                self.entities_featurized_test], axis=0)
        except ValueError:
            # if there are no preprocessed features in the first place, all
            # will be None, and pd.concat fails
            self.entities_featurized = None
        self.target = pd.concat([self.target_train, self.target_test], axis=0)

    def _evaluate(self, feature, verbose=False):
        metrics = super()._evaluate(feature, verbose)
        return metrics
