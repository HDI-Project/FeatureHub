from __future__ import print_function

import sys
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils import database_exists, create_database, drop_database

from featurefactory.admin.sqlalchemy_declarative import Base, Feature, Problem, User, Metric
from featurefactory.admin.sqlalchemy_main import ORMManager


class Commands(object):
    """
    Admin interface for the database.

    Create the schema, add or remove problems, and view problems, users, and
    features.
    """

    def __init__(self, problem=None, database="featurefactory"):
        """Create the ORMManager and connect to DB.

        if problem name is given, load it.
        """

        self.__orm = ORMManager(database)

        if not database_exists(self.__orm.engine.url):
            print("database {} does not seem to exist.".format(database))
            print("You might want to create it by calling set_up method")
        elif  problem:
            try:
                with self.__orm.session_scope() as session:
                    problem = session.query(Problem).filter(Problem.name == problem).one()
                    self.__problemid = problem.id
            except NoResultFound:
                print("WARNING: Problem {} does not exist!".format(problem))
                print("You might want to create it by calling create_problem method")

    def set_up(self, drop=False):
        """Create a new DB and create the initial scheme.

        If the DB already exists, it will be dropped if the drop argument is True.
        """
        url = self.__orm.engine.url
        if database_exists(url):
            if drop:
                print("Dropping old database {}".format(url))
                drop_database(url)
            else:
                print("WARNING! Database {} already exists.\n"
                      "Set drop=True if you want to drop it.".format(url),
                      file=sys.stderr)
                return

        create_database(url)
        Base.metadata.create_all(self.__orm.engine)

        print("Database {} created successfully".format(url))

    def create_problem(self, name, problem_type, data_path, files, y_index, y_column):
        """Creates a new problem entry in database."""

        with self.__orm.session_scope() as session:
            try:
                problem = session.query(Problem).filter(Problem.name == name).one()
                self.__problemid = problem.id
                print("Problem {} already exists".format(name))
                return
            except NoResultFound:
                pass    # we will create it

            problem = Problem(
                name         = name,
                problem_type = problem_type,
                data_path    = data_path,
                files        = ",".join(files),
                y_index      = y_index,
                y_column     = y_column
            )
            session.add(problem)
            self.__problemid = problem.id
            print("Problem {} successfully created".format(name))

    def get_problems(self):
        """Return a list of problems in the database."""

        with self.__orm.session_scope() as session:
            try:
                problems = session.query(Problem.name).all()
                return [problem[0] for problem in problems]
            except NoResultFound:
                return []

    def _get_features(self, session, user_name=None):
        """Get an SQLAlchemy cursor pointing at the requested features."""

        #TODO pivot metrics tables
        query = session.query(Feature, User.name, Metric)

        if user_name:
            query = query.filter(User.name == user_name)

        query = query.filter(Feature.problem.id == self.__problemid)

        return query

    def get_features(self, user_name=None):
        """Get a DataFrame with the details about all registered features."""
        with self.__orm.session_scope() as session:
            features = self._get_features(session, user_name).all()
            feature_dicts = [{
                "user"        : feature.user.name,
                "description" : feature.description,
                "md5"         : feature.md5,
                "created_at"  : feature.created_at,
                metric.name   : metric.value,
            } for feature, metric in features]

            if not feature_dicts:
                print("No features found")
            else:
                return pd.DataFrame(feature_dicts)

    def print_feature(self, user_name, md5=None):
        """
        Print the code of the requested feature.

        If there is more than one feature with the same name, only the
        latest version is printed.
        Alternatively, the feature md5 can be passed to select a particular feature.
        """
        with self.__orm.session_scope() as session:
            query = self._get_features(session, user_name)

            if md5:
                query = query.filter(Feature.md5 == md5)

            query = query.order_by(Feature.created_at.desc())

            feature = query.first()
            if feature:
                print("Description: {}".format(feature.description))
                print("md5: {}".format(feature.md5))
                print("created_at: {}".format(feature.created_at))
                print("\n")
                print(feature.code)
            else:
                print("No matching features found.")
