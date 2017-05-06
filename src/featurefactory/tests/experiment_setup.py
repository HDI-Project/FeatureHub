import os

def create_test_problem():
    name = 'test'
    problem_type = 'classification'
    data_path = '/data/test'
    files = ['train.csv', 'info.csv']
    y_index = 0
    y_column = 'label'

    data_path_host = os.path.join(os.environ.get('FF_DATA_DIR'), 'data', 'test')
