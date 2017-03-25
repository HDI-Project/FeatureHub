from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from featurefactory.admin.sqlalchemy_declarative import Base
from configparser import ConfigParser, NoSectionError
import os

class ORMManager:
    """Initialize the sqlalchemy ORM engine and starts a database session."""

    def __init__(self, database):

        # Host information is the same across users
        host = os.getenv('MYSQL_CONTAINER_NAME', 'localhost')

        # User's username/password is user-specific
        try:
            config = ConfigParser()
            user_conf = os.path.join(os.path.expanduser('~'),'.my.cnf')
            config.read(user_conf)
            user     = config.get('client','user')
            password = config.get('client','password')
        except (IOError, NoSectionError) as e:
            # TODO should throw error
            user     = 'root'
            password = ''

        conn_string = 'mysql+mysqlconnector://{}:{}@{}/{}'.format(user, password, host, database)
        self.engine = create_engine(conn_string)
        Base.metadata.bind = self.engine
        dbsession = sessionmaker(bind=self.engine)
        dbsession.bind = self.engine
        self.session = dbsession()
