from featurehub.tests.util import EPSILON
from featurehub.modeling.scorers import ndcg_score, rmsle_score
from featurehub.modeling.scorers import ndcg_scorer, rmsle_scorer
from featurehub.modeling.scorers import ndcg_autoscorer, rmsle_autoscorer
import numpy as np

def test_ndcg():
    y_true = np.array([1,0,2])

    y_pred1 = np.array([[0.15, 0.55, 0.2], [0.7, 0.2, 0.1], [0.06, 0.04, 0.9]])
    score1 = ndcg_score(y_true, y_pred1, k=2)
    assert score1 == 1.0

    y_pred2 = np.array([[.9, 0.5, 0.8], [0.7, 0.2, 0.1], [0.06, 0.04, 0.9]])
    score2 = ndcg_score(y_true, y_pred2, k=2)
    assert np.abs(score2 - 0.666666) < EPSILON

    #                   0.5             0.5              1./np.log2(3)
    y_pred3 = np.array([[.9, 0.5, 0.8], [0.1, 0.7, 0.2], [0.04, 0.9, 0.06]])
    score3  = ndcg_score(y_true, y_pred3, k=3)
    assert np.abs(score3 - 0.543643) < EPSILON

def test_rmsle():
    pass
