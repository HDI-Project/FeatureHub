from __future__ import print_function

import collections
import gc
import hashlib
import inspect
import os
import sys
from textwrap import dedent
import pandas as pd
from sqlalchemy.sql import exists
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from featurefactory.user.util import run_isolated
from featurefactory.user.model import Model
from featurefactory.admin.sqlalchemy_main import ORMManager
from featurefactory.admin.sqlalchemy_declarative import *


class Session(object):
    """created per user connected, hidden/inaccessible to user.

    Note: use "__" prefix to make variables private so that users cannot read
    them directly.

    WARNING: The statement above is not completely true.
    Variables prefixed by "__" are "harder" to access, but still accessible!
    For example, __db attribute is still accessible as `session._Session__db`
    """
    def __init__(self, problem, n_jobs=1, database="featurefactory"):
        self.__orm = ORMManager(database)
        self.__user = None
        self.__dataset = None

        try:
            problems = self.__orm.session.query(Problem)
            self.__problem = problems.filter(Problem.name == problem).one()
        except NoResultFound:
            raise ValueError("Invalid problem name: {}".format(problem))

        self.__model = Model(self.__problem.problem_type)
        self.__files = self.__problem.files.split(",")
        self.__y_index = self.__problem.y_index
        self.__y_column = self.__problem.y_column
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
    def get_sample_dataset(self):
        """
        Loads sample of problem dataset into memory.

        Returns a list of DataFrames.
        """
        if not self.__dataset:
            self.__dataset = list(self._load_dataset())

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

    def cross_validate(self, feature):
        """
        Return score of feature run on dataset sample.

        Runs the feature in an isolated environment to extract the feature
        values. Validates the feature values. Then, builds a model on that one
        feature, performs cross validation, and returns the score.
        """

        # confirm that dimensions of feature are appropriate.
        invalid = self._validate_feature(feature)
        if invalid:
            print("Feature is not valid: {}".format(invalid), file=sys.stderr)
            score = 0
        else:
            score = self._cross_validate(feature)

        return score

    def register_feature(self, feature):
        """
        Creates a new feature entry in database.
        """

        assert self.__user, "user not initialized properly"

        name = feature.__name__
        assert name != "<lambda>", "Adding an anonymous function is not allowed"

        code = self.__get_source(feature).encode("utf-8")
        md5 = hashlib.md5(code).hexdigest()

        query = (
            Feature.name == name,
            Feature.problem == self.__problem,
            Feature.user == self.__user,
            Feature.md5 == md5,
        )
        score = self.__orm.session.query(Feature.score).filter(*query).scalar()
        if score:
            print("Feature {} already registered with score {}".format(
                name, score))
            return

        if self._is_valid_feature(feature):
            score = float(self._cross_validate(feature))
            print("Your feature {} scored {}".format(name, score))

            feature = Feature(name=name, score=score, code=code, md5=md5,
                              user=self.__user, problem=self.__problem)
            self.__orm.session.add(feature)
            self.__orm.session.commit()
            print("Feature {} successfully registered".format(name))
        else:
            print("Feature {} is invalid and not registered.", file=sys.stderr)

    def _load_dataset(self):
        for filename in self.__files:
            yield pd.read_csv(os.path.join(self.__data_path, filename), 
                    low_memory=False)

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

    @staticmethod
    def _print_one_feature(feature):
        print(dedent("""\
        ----------
        Feature score: {0}

        Feature code:
        {1}
        \n
        """.format(feature.score, feature.code)))

    def _is_valid_feature(self, feature):
        """
        Return whether feature values are valid.
        """

        # _validate_feature returns empty string on success
        return not bool(self._validate_feature(feature))

    def _validate_feature(self, feature):
        """
        Extract feature values from feature function, then validate values.
        """
        dataset = self.get_sample_dataset()
        feature_values = run_isolated(feature, dataset)
        return self._validate_feature_values(feature_values)

    def _validate_feature_values(self, feature_values):
        """
        Return validity of feature values.

        Currently checks if the feature is a DataFrame of the correct
        dimensions. If the feature is valid, returns an empty string. Otherwise,
        returns a semicolon-delimited list of reasons that the feature is
        invalid.
        """

        result = []

        # must be a data frame
        if not isinstance(feature_values, pd.core.frame.DataFrame):
            result.append("does not return DataFrame")
            return "; ".join(result)

        dataset = self.get_sample_dataset()
        expected_shape = (dataset[self.__y_index].shape[0], 1)
        if feature_values.shape != expected_shape:
            result.append(
                "returns DataFrame of invalid shape "
                "(actual {}, expected {})".format(
                    feature_values.shape, expected_shape)
            )

        return "; ".join(result)

    def _cross_validate(self, feature):
        """
        Return score of feature run on dataset sample, without validating
        feature values.
        """
        assert isinstance(feature, collections.Callable), \
                "feature must be a function!"

        # If running in docker and receive Errno 28: No space left on device
        # import os
        # os.environ["JOBLIB_TEMP_FOLDER"] = "/tmp"
        print("Obtaining dataset...")
        dataset = self.get_sample_dataset()

        print("Extracting features...")
        X = run_isolated(feature, dataset)
        Y = dataset[self.__y_index].pop(self.__y_column)

        print("Cross validating...")
        score = self.__model.cross_validate(X, Y)

        # clean up to avoid filling up the memory
        del X
        del Y
        del dataset
        gc.collect()

        return score

    def __get_source(self, function):
        out = []
        try:
            func_code, func_globals = function.func_code, function.func_globals
        except AttributeError:    # Python 3
            func_code, func_globals = function.__code__, function.__globals__

        for name in func_code.co_names:
            obj = func_globals.get(name)
            if obj and inspect.isfunction(obj):
                out.append(self.__get_source(obj))

        out.append(inspect.getsource(function))

        seen = set()
        return "\n".join(x for x in out if not (x in seen or seen.add(x)))
