from sklearn.cross_validation import cross_val_score
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor


class Model(object):

    def __init__(self, problem_type):
        self.model = None
        if problem_type == 'classification':
            self.model = DecisionTreeClassifier()
        elif problem_type == 'regression':
            self.model = DecisionTreeRegressor()
        else:
            raise NotImplementedError

    def cross_validate(self, X, Y):
        if len(X.shape) == 1:    # 1d arrays are not supported anymore by
            X = X.reshape(-1, 1)
        return cross_val_score(self.model, X, Y, n_jobs=-1).mean()
