import pandas as pd
import dill
import urllib.parse
from featurefactory.admin.sqlalchemy_declarative import (
    Base, Feature, Problem, User, Metric, EvaluationAttempt
)

def load_features_df(problem_name, session):
    """Get all features for a specific problem as a DataFrame."""
    problem_id = session.query(Problem.id).filter(Problem.name == problem_name).scalar()
    features = session.query(Feature).filter(Feature.problem_id == problem_id).all()
    features_records = [feature.__dict__ for feature in features]
    features_df = pd.DataFrame.from_records(features_records)
    del features_df["_sa_instance_state"]
    
    return features_df

def recover_function(feature):
    """Recover compiled function from Feature object."""
    f = dill.loads(urllib.parse.unquote_to_bytes(feature["feature_dill_quoted"]))
    return f

def append_feature_functions(features_df):
    """Recover compiled functions and append column to DataFrame."""
    feature_functions = features_df.apply(recover_function, axis=1)
    features_df["feature_function"] = feature_functions
    return features_df

def build_feature_matrix(features_df, dataset):
    """Build feature matrix from human-generated features."""
    feature_functions = features_df["feature_function"]
    feature_matrix = pd.concat([pd.DataFrame(f(dataset)) for f in feature_functions], axis=1)
    feature_names = [f.__code__.co_name for f in feature_functions]
    feature_matrix.columns = feature_names
    return feature_matrix
