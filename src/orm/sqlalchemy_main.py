from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from orm.sqlalchemy_declarative import Base
from configparser import RawConfigParser
import os.path

class ORMManager:
    """Initialize the sqlalchemy ORM engine and starts a database session."""

    def __init__(self, database, user='root', password='', host=None):
        if not host:
             try:
                config = RawConfigParser()
                config.read('/etc/featurefactory/featurefactory.conf')
                host = config.get('mysql','host')
             except IOError:
                host = 'localhost'
        conn_string = 'mysql+mysqlconnector://{}:{}@{}/{}'.format(user, password, host, database)
        # print("Opening a new db connection: {}".format(conn_string))
        self.engine = create_engine(conn_string)
        Base.metadata.bind = self.engine
        dbsession = sessionmaker(bind=self.engine)
        dbsession.bind = self.engine
        self.session = dbsession()
