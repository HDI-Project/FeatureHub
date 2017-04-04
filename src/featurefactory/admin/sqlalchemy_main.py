from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from featurefactory.admin.sqlalchemy_declarative import Base
from configparser import ConfigParser, NoSectionError
import os

class ORMManager(object):
    """
    Initialize the sqlalchemy ORM engine and starts a database session.

    Parameters
    ----------
    database : string
        Name of database to connect to
    admin : bool, default False
        Whether to look up credentials in environment variables
        `MYSQL_ROOT_USERNAME` and `MYSQL_ROOT_PASSWORD`. If so, logs in as root
        user with admin permissions.
    """

    def __init__(self, database, admin=False):
        self.__database = database

        # Host information is the same across users
        host = os.getenv("MYSQL_CONTAINER_NAME", "localhost")

        if not admin:
            # User's username/password is user-specific
            try:
                config = ConfigParser()
                user_conf = os.path.join(os.path.expanduser("~"),".my.cnf")
                config.read(user_conf)
                user     = config.get("client","user")
                password = config.get("client","password")
            except (IOError, NoSectionError) as e:
                raise ValueError("Couldn't read database credentials.")
        else:
            # Check for environment variables for root account
            user     = os.environ.get("MYSQL_ROOT_USERNAME", "root")
            password = os.environ.get("MYSQL_ROOT_PASSWORD", "")


        conn_string = "mysql+mysqlconnector://{}:{}@{}/{}".format(user, password, host, database)
        self.engine = create_engine(conn_string)

        # Validate cxn
        try:
            create_engine(conn_string).connect()
        except Exception:
            # couldn't connect
            raise ValueError("Couldn't connect to database.")

        Base.metadata.bind = self.engine
        Session = sessionmaker(bind=self.engine)
        Session.bind = self.engine
        self.session = Session()

        # TODO expose factory Session only, rather than instance session
