import numpy as np
from sklearn.metrics import mean_squared_error
import sklearn.metrics
import autosklearn.metrics

#
# Normalized Discounted Cumulative Gain metric
#
def ndcg_score(y_true, y_pred, k=5):
    """Normalized discounted cumulative gain (NDCG) at rank k

    This specific score function operates under the assumption that the
    relevance for the correct label is 1 and the relevance for all other labels
    is 0.

    Parameters
    ----------
    y_true : array-like, shape = [n_samples,]
        Ground truth (true relevance labels). These must be encoded to integer
        values, by using LabelEncoder, for example.

    y_pred : array-like, shape = [n_samples, n_classes]
        Probability predictions for each class.

    k : int
        Rank.

    Returns
    -------
    NDCG @k : float
    """
    y_pred_topk = np.fliplr(np.argsort(y_pred))[:,:k]
    pos = np.where(np.sum(y_pred_topk==y_true[:,None],1) > 0,
                 np.argmax(y_pred_topk==y_true[:,None],1),
                 np.nan)
    scores = [1.0/np.log2((i+1)+1) if not np.isnan(i) else 0 for i in pos]
    return np.mean(scores)

ndcg_scorer = sklearn.metrics.make_scorer(ndcg_score,
    greater_is_better=True, needs_proba=True)

ndcg_autoscorer = autosklearn.metrics.make_scorer("ndcg", ndcg_score,
    greater_is_better=True, needs_proba=True)

#
# Root mean squared log error
#

def rmsle_score(y_true, y_pred, **kwargs):
    return np.sqrt(mean_squared_error(np.log(y_pred + 1), np.log(y_true + 1),
        **kwargs))

rmsle_scorer = sklearn.metrics.make_scorer(rmsle_score,
    greater_is_better=False, needs_proba=False)

rmsle_autoscorer = autosklearn.metrics.make_scorer("rmsle", rmsle_score,
    greater_is_better=False, needs_proba=False)
