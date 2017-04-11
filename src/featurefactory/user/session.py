from __future__ import print_function

import gc
import hashlib
import os
import sys
from textwrap import dedent
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from featurefactory.admin.sqlalchemy_main        import ORMManager
from featurefactory.admin.sqlalchemy_declarative import Problem, Feature, User
from featurefactory.user.model                   import Model
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
        self.__orm     = ORMManager(database)
        self.__user    = None
        self.__dataset = []

        try:
            problems = self.__orm.session.query(Problem)
            self.__problem = problems.filter(Problem.name == problem).one()
        except NoResultFound:
            raise ValueError("Invalid problem name: {}".format(problem))

        self.__model     = Model(self.__problem.problem_type)
        self.__files     = self.__problem.files.split(",")
        self.__y_index   = self.__problem.y_index
        self.__y_column  = self.__problem.y_column
        self.__data_path = self.__problem.data_path

        # "log in" to the system
        name = os.getenv("USER")
        try:
            self.__user = self.__orm.session.query(User)\
                                            .filter(User.name == name)\
                                            .one()
        except NoResultFound:
            self.__user = User(name=name)
            self.__orm.session.add(self.__user)
            self.__orm.session.commit()
        except MultipleResultsFound:
            # shouldn"t happen after bug fix
            self.__user = self.__orm.session.query(User)\
                                            .filter(User.name == name)\
                                            .first()

        # initialize evaluation client
        self.__evaluation_client = EvaluationClient(self.__problem, self.__user,
            self.__orm, self.__dataset) 

    def get_sample_dataset(self):
        """
        Loads sample of problem dataset, returning a list of
        DataFrames.
        """
        if not self.__dataset:
            self._load_dataset()

        gc.collect()    # make sure that we have enough space for this.
        return [df.copy() for df in self.__dataset]

    def discover_features(self, code_fragment=None):
        """
        Discover features written by other users.

        Print features written by other users, enabling collaboration.
        A code fragment can be used to filter search results. For each feature,
        prints feature score and feature code.
        """
        query = self._filter_features(code_fragment)
        query = query.filter(Feature.user != self.__user)

        features = query.all()

        if features:
            for feature in features:
                self._print_one_feature(feature)
        else:
            print("No features found.")

    def print_my_features(self):
        """Print all features written by this user."""
        query = self._filter_features(None)
        features = query.all()

        if features:
            for feature in features:
                self._print_one_feature(feature)
        else:
            print("No features found.")

    def evaluate(self, feature):
        """
        Return score of feature run on dataset sample.

        Runs the feature in an isolated environment to extract the feature
        values. Validates the feature values. Then, builds a model on that one
        feature, performs cross validation, and returns the score.
        """

        return self.__evaluation_client.evaluate(feature)

    def register_feature(self, feature, description=""):
        """
        Creates a new feature entry in database.
        """

        assert self.__user, "User not initialized properly."

        is_registered = self._check_if_registered(feature, description)
        if is_registered:
            return

        if not description:
            description = self._prompt_description()

        self.__evaluation_client.register_feature(feature, description)

    def _abbrev_md5(self, md5):
        """Return first MD5_ABBREV_LEN characters of md5"""
        return md5[:MD5_ABBREV_LEN]

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

    def _filter_features(self, code_fragment):
        """
        Return a query object that filters features written for the appropriate
        problem by code snippets.

        This query object can be added to by the caller.
        """
        assert self.__user, "user not initialized properly"

        filter_ = (
            Feature.problem == self.__problem,
        )

        if code_fragment:
            filter_ = filter_ + (
                Feature.code.contains(code_fragment),
            )

        return (
            self.__orm.session.query(Feature)
                .filter(*filter_)
                .order_by(Feature.score)
        )

    def _check_if_registered(self, feature, description, verbose=True):
        code    = get_source(feature)
        problem = self.__problem
        md5     = hashlib.md5(code).hexdigest()

        query = (
            Feature.problem == self.__problem,
            Feature.user    == self.__user,
            Feature.md5     == md5,
        )
        score = self.__orm.session.query(Feature.score).filter(*query).scalar()
        if score:
            if verbose:
                print("Feature already registered with score {}".format(score))
            return True

        return False

    def _prompt_description(self):
        print("First, enter feature description. Your feature description "
              "should be clear, concise, and meaningful to non-data scientists."
              " (If your feature fails to register, this description will be "
              "discarded.)")

        try:
            raw_input
        except NameError:
            raw_input = input

        description = raw_input("Enter description: ")
        return description

    @staticmethod
    def _print_one_feature(feature):
        print(dedent("""
        ------------------
        Feature score: {0}

        Feature code:
        {1}
        \n
        """.format(feature.score, feature.code)))
