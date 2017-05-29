import os
import sklearn.metrics
import pandas as pd
import dill
import urllib.parse
from featurefactory.admin.sqlalchemy_declarative import *

def load_features_df(session, problem_name):
    """Get all features for a specific problem as a DataFrame."""
    problem_id = session.query(Problem.id).filter(Problem.name ==
            problem_name).scalar()
    df = extract_table(session, Feature)
    return df.loc[df["problem_id"] == problem_id, :]

def recover_function(feature):
    """Recover compiled function from Feature object."""
    f = dill.loads(urllib.parse.unquote_to_bytes(feature["feature_dill_quoted"]))
    return f

def append_feature_functions(features_df, inplace=False):
    """Recover compiled functions and append column to DataFrame."""
    feature_functions = features_df.apply(recover_function, axis=1)
    if inplace:
        features_df["feature_function"] = feature_functions
        return None
    else:
        features_df = features_df.copy()
        features_df["feature_function"] = feature_functions
        return features_df

def build_feature_matrix(features_df, dataset):
    """Build feature matrix from human-generated features."""
    feature_functions = features_df["feature_function"]
    feature_matrix = pd.concat([pd.DataFrame(f(dataset)) for f in feature_functions], axis=1)
    feature_names = [f.__code__.co_name for f in feature_functions]
    feature_matrix.columns = feature_names
    return feature_matrix

def save_feature_matrix(feature_matrix, problem_name, split, suffix):
    name = "{}_{}_{}.pkl.bz2".format(problem_name, split, suffix)
    save_table(feature_matrix, name) 

def load_feature_matrix(problem_name, split, suffix):
    name = "{}_{}_{}.pkl.bz2".format(problem_name, split, suffix)
    return load_table(name)

def build_and_save_all_features(commands, session, suffix):
    """Build and save feature matrices.

    Examples
    --------
    >>> with orm.session_scope() as session:
            build_and_save_all_features(commands, session, suffix)
    """
    result = session.query(Problem).filter(Problem.name != "demo").all()
    problem_names = [r.name for r in result]

    for problem_name in problem_names:
        for split in ["train", "test"]:
            print("Processing features for problem {}, split {}"
                    .format(problem_name, split))
            _, dataset, entities_featurized, target = \
                commands.load_dataset(problem_name=problem_name, split=split)
            features_df = load_features_df(session, problem_name)
            append_feature_functions(features_df, inplace=True)
            feature_matrix = build_feature_matrix(features_df, dataset)
            save_feature_matrix(feature_matrix, problem_name, split, suffix)

def extract_and_save_all_tables(session, suffix):
    for mapper in [Feature, Problem, User, EvaluationAttempt, Metric]:
        df = extract_table(session, mapper)
        save_table1(df, mapper.__tablename__, suffix)

def extract_table(session, mapper):
    result = session.query(mapper).all()
    result_records = [r.__dict__ for r in result]
    result_df = pd.DataFrame.from_records(result_records)
    tablename = mapper.__tablename__
    if "_sa_instance_state" in result_df.columns:
        del result_df["_sa_instance_state"]
    return result_df

def save_table1(df, name, suffix):
    underscore = "_" if suffix else ""
    name1 = name + underscore + suffix + ".pkl.bz2"
    save_table(df, name1)

def save_table(df, name):
    fullname = os.path.join(os.path.expanduser("~"), "notebooks", name)
    df.to_pickle(fullname)

def load_table1(name, suffix):
    underscore = "_" if suffix else ""
    name1 = name + underscore + suffix + ".pkl.bz2"
    return load_table(name1)

def load_table(name):
    fullname = os.path.join(os.path.expanduser("~"), "notebooks", name)
    return pd.read_pickle(fullname)
