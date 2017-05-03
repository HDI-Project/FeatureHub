import os
import json
import gc
import pandas as pd

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from featurefactory.admin.sqlalchemy_main import ORMManager
from featurefactory.admin.sqlalchemy_declarative import (
    Problem, Feature, User, Metric
)
from featurefactory.modeling import Model
from featurefactory.util import run_isolated, get_source, TRY_AGAIN_LATER
from featurefactory.evaluation import EvaluatorClient

class Session(object):
    """Represents a user's session within Feature Factory.

    Includes commands for discovering, testing, and registering new features.
    """

    def __init__(self, problem, database = "featurefactory"):
        self.__database            = database
        self.__orm                 = ORMManager(database)
        self.__username            = None
        self.__dataset             = {}
        self.__target              = None
        self.__entities_featurized = None

        with self.__orm.session_scope() as session:
            try:
                problem = session.query(Problem)\
                                 .filter(Problem.name == problem)\
                                 .one()
                self.__problem_id                             = problem.id
                self.__problem_data_dir                       = problem.data_dir_train
                self.__problem_files                          = json.loads(problem.files)
                self.__problem_table_names                    = json.loads(problem.table_names)
                self.__problem_entities_table_name            = problem.entities_table_name
                self.__problem_entities_featurized_table_name = problem.entities_featurized_table_name
                self.__problem_target_table_name              = problem.target_table_name
            except NoResultFound:
                raise ValueError("Invalid problem name: {}".format(problem))
            except MultipleResultsFound:
                raise ValueError("Unexpected issue talking to database. " +
                                 TRY_AGAIN_LATER)

        # "log in" to the system
        self._login()

        # initialize evaluation client
        self.__evaluation_client = EvaluatorClient(
            self.__problem_id,
            self.__username,
            self.__orm,
            self.__dataset,
            self.__target,
            self.__entities_featurized
        )

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
        """Loads sample of problem training dataset.

        Returns the dataset a dict mapping table names to pandas DataFrames.

        Returns
        -------
        dataset : dict (str => pd.DataFrame)
            A dict mapping table names to pandas DataFrames.
        target : pd.DataFrame
            A DataFrame that holds a single column: the target variable (label).

        Examples
        --------
        >>> dataset = commands.get_sample_dataset()
        >>> dataset["users"] # -> returns DataFrame
        >>> dataset["stores"] # -> returns DataFrame
        """
        if not self.__dataset or pd.DataFrame(self.__target).empty:
            self._load_dataset()

        # Return a *copy* of the dataset, ensuring we have enough memory.
        gc.collect()    
        dataset = {
            table_name : self.__dataset[table_name].copy() for 
                table_name in self.__dataset
        }
        target = self.__target.copy() # pylint: disable=no-member

        return (dataset, target)

    def discover_features(self, code_fragment=None, metric_name=None):
        """Print features written by other users.

        A code fragment can be used to filter search results. For each feature,
        prints feature id, feature description, metrics, and source code.

        Parameters
        ----------
        code_fragment : string, default=None
            Source code fragment to filter for.
        metric_name : string, default=None
            Metric to report. One of "Accuracy", "Precision", "Recall", and
            "ROC AUC" for classification problems, and "Mean Squared Error"
            and "R-squared" for regression problems.
        """
        self._print_some_features(code_fragment, metric_name, User.name != self.__username)

    def print_my_features(self, code_fragment=None, metric_name=None):
        """Print features written by me.

        A code fragment can be used to filter search results. For each feature,
        prints feature id, feature description, metrics, and source code.

        Parameters
        ----------
        code_fragment : string, default=None
            Source code fragment to filter for.
        metric_name : string, default=None
            Metric to report. One of "Accuracy", "Precision", "Recall", and
            "ROC AUC" for classification problems, and "Mean Squared Error"
            and "R-squared" for regression problems.
        """
        self._print_some_features(code_fragment, metric_name, User.name == self.__username)

    def _print_some_features(self, code_fragment, metric_name, predicate):
        """Driver function for discover_features and print_my_features."""
        metric_name_default = "Accuracy"
        if not metric_name:
            metric_name = metric_name_default

        with self.__orm.session_scope() as session:
            query = self._filter_features(session, code_fragment)

            # Filter only users that are not me
            query = query.join(Feature.user).filter(predicate)
            features = query.all()

            if features:
                for feature in features:
                    # Join with metrics table
                    query = session.query(Metric.name, Metric.value)\
                                .filter(Metric.feature_id == feature.id)
                    metrics = query.all()
                    metric_list = [(metric.name, metric.value) for metric in
                            metrics]
                    self._print_one_feature(feature.description, feature.id,
                            feature.code, metric_list)
            else:
                print("No features found.")


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

        if self.__evaluation_client.check_if_registered(feature, verbose=True):
            return

        return self.__evaluation_client.evaluate(feature)

    def submit(self, feature, description=""):
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
            Feature description. If left empty, will prompt for user imput.
        """

        if not description:
            description = self._prompt_description()

        self.__evaluation_client.submit(feature, description)

    def _load_dataset(self):
        # query db for import parameters to load files
        is_present_dataset = bool(self.__dataset)
        is_present_entities_featurized = not pd.DataFrame(self.__entities_featurized).empty
        is_present_target = not pd.DataFrame(self.__target).empty
        is_anything_missing = not all(
                [is_present_dataset, is_present_entities_featurized, is_present_target])

        if is_anything_missing:
            problem_data_dir = self.__problem_data_dir
            problem_files = self.__problem_files
            problem_table_names = self.__problem_table_names
            problem_entities_featurized_table_name = \
                self.__problem_entities_featurized_table_name
            problem_target_table_name = self.__problem_target_table_name

        # load entities and other tables
        if not self.__dataset:
            # load other tables
            for (table_name, filename) in zip (problem_table_names,
                    problem_files):
                if table_name == problem_entities_featurized_table_name or \
                   table_name == problem_target_table_name:
                    continue
                abs_filename = os.path.join(problem_data_dir, filename)
                self.__dataset[table_name] = pd.read_csv(abs_filename,
                        low_memory=False)

        # load entities featurized
        if pd.DataFrame(self.__entities_featurized).empty:
            # if empty string, we simply don't have any features to add
            if problem_entities_featurized_table_name:
                cols = list(problem_table_names)
                ind_features = cols.index(problem_entities_featurized_table_name)
                abs_filename = os.path.join(problem_data_dir,
                        problem_files[ind_features])
                self.__entities_featurized = pd.read_csv(abs_filename,
                        low_memory=False)

        # load target
        if pd.DataFrame(self.__target).empty:
            cols = list(problem_table_names)
            ind_target = cols.index(problem_target_table_name)
            abs_filename = os.path.join(problem_data_dir,
                    problem_files[ind_target]) 
            self.__target = pd.read_csv(abs_filename, low_memory=False)

    def _filter_features(self, session, code_fragment):
        """Return query that filters this problem and given code fragment.
        
        Return a query object that filters features written for the appropriate
        problem by code snippets. This query object can be added to by the
        caller.
        """
        filter_ = (
            Feature.problem_id == self.__problem_id,
        )

        if code_fragment:
            filter_ = filter_ + (
                Feature.code.contains(code_fragment),
            )

        return session.query(Feature).filter(*filter_)

    def _prompt_description(self):
        """Prompt user for description of feature"""
        print("First, enter feature description. Your feature description "
              "should be clear, concise, and meaningful to non-data scientists."
              " (If your feature fails to register, this description will be "
              "discarded.)")

        description = input("Enter description: ")
        print("")
        return description

    @staticmethod
    def _print_one_feature(feature_description, feature_id, feature_code,
            metric_list):
        """Print one feature in user-readable format.
        
        Parameters
        ----------
        feature_description : str
        feature_id : int
        feature_code : str
        metric_list : MetricList

        Examples
        --------
        >>> Session._print_one_feature("Age", 1, "def age(dataset):    pass\n",
                metric_list_)
        -------------------
        Feature id: 1
        Feature description: Age

        Feature code:
            def age(dataset):    pass

        Feature metrics:
            Accuracy: 0.5
            ROC AUC: 0.35
        """
        result = "------------------\n" + \
                 "Feature id: {}\n".format(feature_id) + \
                 "Feature description: {}\n".format(feature_description)

        result += "\n" + \
                  "Feature code:\n"

        for line in feature_code.split("\n"):
            result += "    " + line + "\n"

        result += "\n" + \
                  "Feature metrics:\n"

        for metric_name, metric_value in metric_list:
            result += "    {}: {}\n".format(metric_name, metric_value)

        print(result)
