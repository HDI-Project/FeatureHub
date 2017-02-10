from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, BigInteger, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)

class Feature(Base):
    __tablename__ = 'features'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User')
    problem_id = Column(Integer, ForeignKey('problems.id'))
    problem = relationship('Problem')
    code = Column(Text, nullable=False)
    md5 = Column(String(32), nullable=True)
    score = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

class Problem(Base):
    __tablename__ = 'problems'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    problem_type = Column(String(100), nullable=False)
    data_path = Column(String(100), nullable=False)
    files = Column(String(100), nullable=False)
    y_index = Column(Integer, nullable=False)
    y_column = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
