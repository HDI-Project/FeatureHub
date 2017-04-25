import os
import sys
import gc
import hashlib
import pandas as pd
from textwrap import dedent
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from featurefactory.admin.sqlalchemy_main        import ORMManager
from featurefactory.admin.sqlalchemy_declarative import Problem, Feature, User, Metric
from featurefactory.modeling                     import Model
from featurefactory.util                         import run_isolated, get_source, compute_dataset_hash
from featurefactory.evaluation                   import EvaluationClient

MD5_ABBREV_LEN = 8

class Session(object):
    """
    Represents a user's session within Feature Factory.

    Includes commands for discovering, testing, and registering new features.
    """

    def __init__(self, problem, database="featurefactory"):
        self.__database = database
        self.__orm      = ORMManager(database)
        self.__username = None
        self.__dataset  = []

        with self.__orm.session_scope() as session:
            try:
                problem = session.query(Problem)\
                                 .filter(Problem.name == problem)\
                                 .one()
                self.__problemid = problem.id
                self.__files     = problem.files.split(",")
                self.__y_index   = problem.y_index
                self.__y_column  = problem.y_column
                self.__data_path = problem.data_path
                self.__model     = Model(problem.problem_type)
            except NoResultFound:
                raise ValueError("Invalid problem name: {}".format(problem))


        # "log in" to the system
        self._login()

        # initialize evaluation client
        self.__evaluation_client = EvaluationClient(self.__problemid,
                self.__username, self.__orm, self.__dataset) 

    def _login(self):
        name = os.environ.get("USER")
        if not name:
            raise ValueError("Missing environment variable 'USER'. Feature"
                             " factory session not initialized.")

        with self.__orm.session_scope() as session:
            try:
                user = session.query(User)\
                              .filter(User.name == name)\
                              .one()
                self.__username = user.name
            except NoResultFound:
                session.add(User(name=name))
                self.__username = name
            except MultipleResultsFound as e:
                raise e

    def get_sample_dataset(self):
        """
        Loads sample of problem dataset, returning a list of
        DataFrames.
        """
        if not self.__dataset:
            self._load_dataset()

        gc.collect()    # make sure that we have enough space for this.
        return [df.copy() for df in self.__dataset]

    def discover_features(self, code_fragment=None, metric_name=None):
        """
        Print features written by other users.

        A code fragment can be used to filter search results. For each feature,
        prints feature description, metrics, and source code.

        Args
        ----
            code_fragment : string
                Source code fragment to filter for.
            metric_name : string
                Metric to report. One of "Accuracy", "Precision", "Recall", and
                "ROC AUC" for classification problems, and "Mean Squared Error"
                and "R-squared" for regression problems.
        """
        self._print_some_features(code_fragment, metric_name, User.name != self.__username)

    def print_my_features(self, code_fragment=None, metric_name=None):
        """
        Print features written by me.

        A code fragment can be used to filter search results. For each feature,
        prints feature description, metrics, and source code.

        Args
        ----
            code_fragment : string
                Source code fragment to filter for.
            metric_name : string
                Metric to report. One of "Accuracy", "Precision", "Recall", and
                "ROC AUC" for classification problems, and "Mean Squared Error"
                and "R-squared" for regression problems.
        """
        self._print_some_features(code_fragment, metric_name, User.name == self.__username)

    def _print_some_features(self, code_fragment, metric_name, predicate):
        """
        Driver function for discover_features and print_my_features.
        """
        metric_name_default = "Accuracy"
        if not metric_name:
            metric_name = metric_name_default

        with self.__orm.session_scope() as session:
            query = self._filter_features(session, code_fragment)

            # Filter only users that are not me
            query = query.join(Feature.user).filter(predicate)

            # Join with metrics table
            query = query.join(Metric)\
                         .filter(Metric.name == metric_name)\
                         .add_columns(Metric.name, Metric.value)
            features = query.all()

            if features:
                for feature in features:
                    # each feature is a tuple (<feature>, metric_name, metric_value)
                    self._print_one_feature(feature[0].description, feature[1],
                            feature[2], feature[0].code)
            else:
                print("No features found.")


    def evaluate(self, feature):
        """
        Evaluate feature on training dataset, returning key performance metrics.

        Runs the feature in an isolated environment to extract the feature
        values. Validates the feature values. Then, builds a model on that one
        feature, performs cross validation, and returns key performance metrics.
        """

        return self.__evaluation_client.evaluate(feature)

    def register_feature(self, feature, description=""):
        """
        Creates a new feature entry in database.
        """

        is_registered = self._check_if_registered(feature, description)
        if is_registered:
            return

        if not description:
            description = self._prompt_description()

        self.__evaluation_client.register_feature(feature, description)

    def _load_dataset(self):
        # TODO check for dtypes file, assisting in low memory usage

        if not self.__dataset:
            for filename in self.__files:
                abs_filename = os.path.join(self.__data_path, filename)
                self.__dataset.append( pd.read_csv(abs_filename, low_memory=False))

        return self.__dataset

    def _reload_dataset(self):
        self.__dataset = []
        return self._load_dataset()

    def _filter_features(self, session, code_fragment):
        """
        Return a query object that filters features written for the appropriate
        problem by code snippets.

        This query object can be added to by the caller.
        """
        filter_ = (
            Feature.problem_id == self.__problemid,
        )

        if code_fragment:
            filter_ = filter_ + (
                Feature.code.contains(code_fragment),
            )

        return session.query(Feature).filter(*filter_)

    def _check_if_registered(self, feature, description, verbose=True):
        code    = get_source(feature)
        md5     = hashlib.md5(code).hexdigest()

        with self.__orm.session_scope() as session:
            filters = (
                Feature.problem_id == self.__problemid,
                Feature.md5        == md5,
                User.name          == self.__username,
            )
            query = session.query(Feature, User).filter(*filters)
            result = query.scalar()

        if result:
            if verbose:
                print("Feature already registered.")
            return True

        return False

    def _prompt_description(self):
        print("First, enter feature description. Your feature description "
              "should be clear, concise, and meaningful to non-data scientists."
              " (If your feature fails to register, this description will be "
              "discarded.)")

        description = input("Enter description: ")
        print("")
        return description

    @staticmethod
    def _print_one_feature(feature_description, metric_names, metric_values,
            feature_code):
        result = "------------------\n" + \
                 "*{}*\n".format(feature_description) + \
                 "\n" + \
                 "Feature metrics:\n"

        for metric_name, metric_value in zip(metric_names, metric_values):
            result += "    {}: {}\n".format(metric_name, metric_value)

        result += "\n"
        result += "Feature code:\n"

        for line in feature_code.split("\n"):
            result += "    " + line + "\n"

        print(result)
