from __future__ import print_function

import pandas as pd
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils import database_exists, create_database, drop_database

from orm.sqlalchemy_declarative import Base, Feature, Problem, User
from orm.sqlalchemy_main import ORMManager


class Commands(object):

    def __init__(self, problem=None, database='featurefactory'):
        """Create the ORMManager and connect to DB.

        if problem name is given, load it.
        """

        self.__orm = ORMManager(database)

        if not database_exists(self.__orm.engine.url):
            print('database {} does not seem to exist.'.format(database))
            print('You might want to create it by calling set_up method')
        elif  problem:
            try:
                problems = self.__orm.session.query(Problem)
                self.__problem = problems.filter(Problem.name == problem).one()
            except NoResultFound:
                print('WARNING: Problem {} does not exist!'.format(problem))
                print('You might want to create it by calling create_problem method')

    def set_up(self, drop=False):
        """Create a new DB and create the initial scheme.

        If the DB already exists, it will be dropped if the drop argument is True.
        """
        url = self.__orm.engine.url
        if database_exists(url):
            if drop:
                print('Dropping old database {}'.format(url))
                drop_database(url)
            else:
                print('WARNING! database {} already exists.'.format(url))
                print('Set drop=True if you want me to drop it')
                return

        create_database(url)
        Base.metadata.create_all(self.__orm.engine)

        print('Database {} created successfully'.format(url))

    def create_problem(self, name, problem_type, data_path, files, y_index, y_column):
        """Creates a new problem entry in database."""

        try:
            self.__orm.session.commit()    # forces a refresh
            self.__problem = self.__orm.session.query(Problem).filter(Problem.name == name).one()
            print('Problem already exists: {}'.format(name))
        except NoResultFound:
            pass    # we will create it

        self.__problem = Problem(name=name, problem_type=problem_type, data_path=data_path,
                                 files=','.join(files), y_index=y_index, y_column=y_column)
        self.__orm.session.add(self.__problem)
        self.__orm.session.commit()
        print('Problem {} successfully created'.format(name))

    def get_problems(self):
        try:
            self.__orm.session.commit()    # forces a refresh
            problems = self.__orm.session.query(Problem.name).all()
            return [problem[0] for problem in problems]
        except NoResultFound:
            return []

    def _get_features(self, user_name=None, feature_name=None):
        """Get an SQLAlchemy cursor pointing at the requested features."""
        self.__orm.session.commit()    # forces a refresh

        filter_ = [
            Feature.problem == self.__problem,
        ]

        if user_name:
            user = self.__orm.session.query(User).filter(User.name == user_name).one()
            filter_.append(Feature.user == user)

        if feature_name:
            filter_.append(Feature.name == feature_name)

        return self.__orm.session.query(Feature).filter(*filter_)

    def get_features(self, user_name=None):
        """Get a pandas.DataFrame with the details about all registered features."""
        features = self._get_features(user_name).all()
        feature_dicts = [{
            'user': feature.user.name,
            'name': feature.name,
            'md5': feature.md5,
            'score': feature.score,
            'created_at': feature.created_at
            } for feature in features]

        if not feature_dicts:
            print('No features found')
        else:
            return pd.DataFrame(feature_dicts)

    def print_feature(self, user_name, feature_name, md5=None):
        """Print the code of the requested feature.

        If there is more than one feature with the same name, only the
        latest version is printed.
        Alternatively, the feature md5 can be passed to select a particular feature.
        """
        features = self._get_features(user_name, feature_name)
        if md5:
            features = features.filter(Feature.md5 == md5)

        feature = features.order_by(Feature.created_at.desc()).first()

        print('Name: {}'.format(feature.name))
        print('Score: {}'.format(feature.score))
        print('md5: {}'.format(feature.md5))
        print('created_at: {}'.format(feature.created_at))
        print('\n')
        print(feature.code)
