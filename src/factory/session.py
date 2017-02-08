from __future__ import print_function

import collections
import datetime
import gc
import hashlib
import inspect
import os
from multiprocessing import Pool

import pandas as pd
from sqlalchemy.sql import exists
from sqlalchemy.orm.exc import NoResultFound

from factory.model import Model
from orm.sqlalchemy_declarative import Feature, Notebook, Problem, User
from orm.sqlalchemy_main import ORMManager


class Session(object):
    """created per user connected, hidden/inaccessible to user.

    Note: use '__' prefix to make variables private so that users cannot read
    them directly.

    WARNING: The statement above is not completely true.
    Variables prefixed by '__' are "harder" to access, but still accessible!
    For example, __db attribute is still accessible as `session._Session__db`
    """
    def __init__(self, problem, n_jobs=1, database='featurefactory'):
        self.__orm = ORMManager(database)
        self.__user = None
        self.__dataset = None

        try:
            problems = self.__orm.session.query(Problem)
            self.__problem = problems.filter(Problem.name == problem).one()
        except NoResultFound:
            raise ValueError('Invalid problem name: {}'.format(problem))

        self.__model = Model(self.__problem.problem_type)
        self.__files = self.__problem.files.split(',')
        self.__y_index = self.__problem.y_index
        self.__y_column = self.__problem.y_column
        self.__data_path = self.__problem.data_path

    def login(self):
        """log a user into the feature factory system."""

        name = os.getenv('USER')
        try:
            query = self.__orm.session.query(User)
            self.__user = query.filter(User.name == name).one()
        except NoResultFound:
            pass

    def logout(self):
        """log a user out of the feature factory system."""
        if self.__user:
            self.__user = None

    def create_user(self):
        """creates a new user entry in database."""
        name = os.getenv('USER')
        if not self.__orm.session.query(exists().where(User.name == name)).scalar():
            self.__orm.session.add(User(name=name))

    def add_notebook(self, name):
        """creates a new notebook entry in database."""
        assert self.__user, 'you have to be logged in first in order to add a notebook'

        query = (
            Notebook.name == name,
            Notebook.problem == self.__problem,
            Notebook.user == self.__user
        )

        if self.__orm.session.query(Notebook.id).filter(*query).scalar():
            print('Notebook already registered')
            return

        notebook = Notebook(name=name, user=self.__user, problem=self.__problem)
        self.__orm.session.add(notebook)
        self.__orm.session.commit()
        print('Notebook {} successfully registered'.format(name))

    def _load_dataset(self):
        for filename in self.__files:
            yield pd.read_csv(os.path.join(self.__data_path, filename), low_memory=False)

    def get_sample_dataset(self):
        if not self.__dataset:
            self.__dataset = list(self._load_dataset())

        gc.collect()    # make sure that we have enough space for this.
        return [df.copy() for df in self.__dataset]

    def __run_isolated(self, function, *args):
        pool = Pool(processes=1)
        try:
            result = pool.map(function, args)[0]
        finally:
            pool.close()

        return result

    def cross_validate(self, feature_extractor):
        assert isinstance(feature_extractor, collections.Callable), \
                "feature_extractor must be a function!"

        # If running in docker and receive Errno 28: No space left on device
        # import os
        # os.environ["JOBLIB_TEMP_FOLDER"] = "/tmp"
        print("Obtaining dataset")
        dataset = self.get_sample_dataset()

        print("Extracting features")
        X = self.__run_isolated(feature_extractor, dataset)
        Y = dataset[self.__y_index].pop(self.__y_column)

        print("Cross validating")
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
        return '\n'.join(x for x in out if not (x in seen or seen.add(x)))

    def add_feature(self, function):
        """creates a new featurek entry in database."""
        assert self.__user, 'you have to be logged in first in order to add a feature'

        name = function.__name__
        assert name != '<lambda>', 'Adding an anonymous function is not allowed'

        code = self.__get_source(function).encode('utf-8')
        md5 = hashlib.md5(code).hexdigest()

        query = (
            Feature.name == name,
            Feature.problem == self.__problem,
            Feature.user == self.__user,
            Feature.md5 == md5
        )
        score = self.__orm.session.query(Feature.score).filter(*query).scalar()
        if score:
            print('Feature {} already registered with score {}'.format(name, score))
            return

        score = float(self.cross_validate(function))
        print("Your feature {} scored {}".format(name, score))

        now = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S')

        feature = Feature(name=name, score=score, code=code, md5=md5,
                          user=self.__user, problem=self.__problem)
        self.__orm.session.add(feature)
        self.__orm.session.commit()
        print('Feature {} successfully registered'.format(name))
