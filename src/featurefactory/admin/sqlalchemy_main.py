from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from featurefactory.admin.sqlalchemy_declarative import Base
from configparser import ConfigParser, NoSectionError
import os

class ORMManager:
    """Initialize the sqlalchemy ORM engine and starts a database session."""

    def __init__(self, database, admin=False):
        self.__database = database

        # Host information is the same across users
        host = os.getenv('MYSQL_CONTAINER_NAME', 'localhost')

        if not admin
            # User's username/password is user-specific
            try:
                config = ConfigParser()
                user_conf = os.path.join(os.path.expanduser('~'),'.my.cnf')
                config.read(user_conf)
                user     = config.get('client','user')
                password = config.get('client','password')
            except (IOError, NoSectionError) as e:
                raise ValueError("Couldn't read database credentials.")
        else:
            # Check for environment variables for root account
            user     = os.environ.get("MYSQL_ROOT_USERNAME", "root")
            password = os.environment.get("MYSQL_ROOT_PASSWORD", "")


        conn_string = 'mysql+mysqlconnector://{}:{}@{}/{}'.format(user, password, host, database)
        self.engine = create_engine(conn_string)

        # Validate cxn
        try:
            create_engine(conn_string).connect()
        except (ArgumentError, InterfaceError) as e:
            # couldn't connect
            raise ValueError("Couldn't connect to database.")

        Base.metadata.bind = self.engine
        dbsession = sessionmaker(bind=self.engine)
        dbsession.bind = self.engine
        self.session = dbsession()
