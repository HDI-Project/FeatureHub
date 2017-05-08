from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class Problem(Base):
    __tablename__ = "problems"

    id                             = Column(Integer, primary_key=True, autoincrement=True)
    name                           = Column(String(100), nullable=False)
    problem_type                   = Column(String(100), nullable=False)
    problem_type_details           = Column(String(1000), nullable=True)
    data_dir_train                 = Column(String(200), nullable=False)
    data_dir_test                  = Column(String(200), nullable=False)
    files                          = Column(String(1000), nullable=False)
    table_names                    = Column(String(1000), nullable=False)
    entities_table_name            = Column(String(100), nullable=False)
    entities_featurized_table_name = Column(String(100), nullable=True)
    target_table_name              = Column(String(100), nullable=False)
    created_at                     = Column(DateTime, default=datetime.now)

class Feature(Base):
    __tablename__ = "features"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    user_id             = Column(Integer, ForeignKey("users.id"))
    user                = relationship("User")
    problem_id          = Column(Integer, ForeignKey("problems.id"))
    problem             = relationship("Problem")
    code                = Column(Text, nullable=False)
    feature_dill_quoted = Column(Text, nullable=True)
    md5                 = Column(String(32), nullable=False)
    description         = Column(String(1000), nullable=False)
    created_at          = Column(DateTime, default=datetime.now)

class Metric(Base):
    __tablename__ = "metrics"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    feature_id = Column(Integer, ForeignKey("features.id"))
    feature    = relationship("Feature", back_populates="metrics")
    name       = Column(String(100), nullable=False)
    scoring    = Column(String(100), nullable=False)
    value      = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class EvaluationAttempt(Base):
    __tablename__ = "evaluationattempts"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    user       = relationship("User")
    problem_id = Column(Integer, ForeignKey("problems.id"))
    problem    = relationship("Problem")
    code       = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

# backwards relationships
Feature.metrics = relationship(
    "Metric", order_by=Metric.name, back_populates="feature")
User.features = relationship("Feature", back_populates="user")
Problem.features = relationship("Feature", back_populates="problem")
User.evaluationattempts = relationship("EvaluationAttempt",
        back_populates="user")
Problem.evaluationattempts = relationship("EvaluatioAttempt",
        back_populates="problem")
