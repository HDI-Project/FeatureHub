import sys
import os
import sklearn.metrics
import pandas as pd
import dill
import urllib.parse
import signal
import json
import traceback
import numpy as np
from contextlib import contextmanager
from featurefactory.admin.sqlalchemy_declarative import *

FEATURE_EXTRACTION_TIME_LIMIT = 40

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

class TimeoutException(Exception):
    pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def build_feature_matrix(features_df, dataset, group_id, group_feature_indices,
        feature_extraction_time_limit=FEATURE_EXTRACTION_TIME_LIMIT):
    """Build feature matrix from human-generated features."""
    feature_functions = features_df["feature_function"]
    num_features = len(feature_functions)

    # extract feature values and names, giving a time limit on execution.
    features = []
    for index, (f, f_id) in enumerate(zip(feature_functions, group_feature_indices)):
        feature_name = "{}_{:04d}".format(group_id, f_id)
        frac = "{n}/{N}".format(n=index, N=num_features-1)
        print("Extracting feature {name:40.40} ({frac:>10.10})".format(
            name=feature_name, frac=frac), end='\r')
        try:
            with time_limit(feature_extraction_time_limit):
                feature = f(dataset)
        except TimeoutException as exc:
            print("Feature extraction (index {index}, name {name}) timed "
                  "out.".format(index=index, name=feature_name),
                  file=sys.stderr)
            # TODO needs entities table
            if features:
                feature = null_feature(features[0][0], name=feature_name)
            else:
                raise ValueError("Couldn't create null feature from empty"
                                 " features list.")
        except Exception as exc:
            print("Feature extraction (index {index}, name {name}) raised "
                  "Exception".format(index=index, name=feature_name),
                  file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            # TODO needs entities table
            if features:
                feature = null_feature(features[0][0], name=feature_name)
            else:
                raise ValueError("Couldn't create null feature from empty"
                                 " features list.")

        features.append((feature, feature_name,))
    print("\ndone")

    feature_matrix = pd.concat([pd.DataFrame(feature[0]) for feature in features], axis=1)
    feature_names = [features[1] for feature in features]
    feature_matrix.columns = feature_names
    return feature_matrix

def null_feature(entities, name='null_feature', fill=0.0):
    """Create null feature of an appropriate length."""
    index = entities.index
    df = pd.DataFrame(index=index)
    df[name] = fill
    return df

def save_feature_matrix(feature_matrix, problem_name, split, suffix):
    name = "output/features/{}_{}_{}.pkl.bz2".format(problem_name, split, suffix)
    save_table(feature_matrix, name) 

def load_feature_matrix(problem_name, split, suffix):
    name = "output/features/{}_{}_{}.pkl.bz2".format(problem_name, split, suffix)
    return load_table(name)

def build_and_save_all_features(commands, session, suffix, splits=[],
        problem_names=[], features_on_disk=False):
    """Build and save feature matrices.

    Examples
    --------
    >>> with orm.session_scope() as session:
            build_and_save_all_features(commands, session, suffix)
    """

    # assumes problem names/orderings constant across extractions
    query = session.query(Problem).filter(Problem.name != "demo")
    if problem_names:
        query = query.filter(Problem.name.in_(problem_names))
    result = query.all()
    problem_names = [r.name for r in result]
    problem_ids   = [r.id for r in result]

    if not splits:
        splits = ["train", "test"]

    for problem_name, problem_id in zip(problem_names, problem_ids):
        for split in splits:
            print("Processing features for problem {}, split {}"
                    .format(problem_name, split))

            # load data
            _, dataset, entities_featurized, target = \
                commands.load_dataset(problem_name=problem_name, split=split)

            # extract features and indices
            if features_on_disk:
                tmp = load_table1("output/tables/features", suffix)
            else:
                tmp = extract_table(session, Feature)
            group_feature_indices = list(np.flatnonzero(tmp["problem_id"] == problem_id))
            features_df = tmp.loc[group_feature_indices, :]
    
            # compute feature functions
            append_feature_functions(features_df, inplace=True)
            feature_matrix = build_feature_matrix(features_df, dataset,
                    suffix, group_feature_indices)

            # save results
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

def prepare_automl_file_name(problem_name, split, suffix):
    name = "automl_{}_{}_{}.pkl".format(problem_name, split, suffix)
    dirname = os.path.join(os.path.expanduser("~"), "notebooks", "output")
    if not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    return os.path.join(dirname, name)

def load_dataset_from_dir(session, data_dir, problem_name):

    # query db for import parameters to load files
    problem = session.query(Problem)\
            .filter(Problem.name == problem_name).one()
    problem_files = json.loads(problem.files)
    problem_table_names = json.loads(problem.table_names)
    problem_entities_featurized_table_name = \
        problem.entities_featurized_table_name
    problem_target_table_name = problem.target_table_name

    problem_data_dir = os.path.join(data_dir, problem_name)

    # load entities and other tables

    # load other tables
    dataset = {}
    for (table_name, filename) in zip (problem_table_names,
            problem_files):
        if table_name == problem_entities_featurized_table_name or \
           table_name == problem_target_table_name:
            continue
        abs_filename = os.path.join(problem_data_dir, filename)
        dataset[table_name] = pd.read_csv(abs_filename,
                low_memory=False, header=0)

    # if empty string, we simply don't have any features to add
    if problem_entities_featurized_table_name:
        cols = list(problem_table_names)
        ind_features = cols.index(problem_entities_featurized_table_name)
        abs_filename = os.path.join(problem_data_dir,
                problem_files[ind_features])
        entities_featurized = pd.read_csv(abs_filename,
                low_memory=False, header=0)

    # load target
    cols = list(problem_table_names)
    ind_target = cols.index(problem_target_table_name)
    abs_filename = os.path.join(problem_data_dir,
            problem_files[ind_target])

    # target might not exist if we are making predictions on unseen
    # test data
    if os.path.exists(abs_filename):
        target = pd.read_csv(abs_filename, low_memory=False, header=0)
    else:
        target = None

    return dataset, entities_featurized, target

def save_submission(df, problem_name, split_train, split_test, suffix):
    underscore = "_" if suffix else ""
    name1 = os.path.join("output", "submissions",
            "submission_{}_{}_{}{}{}.csv".format(problem_name, split_train,
                split_test, underscore, suffix))
    fullname = os.path.join(os.path.expanduser("~"), "notebooks", name1)
    df.to_csv(fullname, index=True, header=True)
    print("Submission saved as {}".format(fullname))
