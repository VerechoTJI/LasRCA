import numpy as np


LOCALIZATION_METRIC_VERSION = "lasrca-ac-avg5-v1"


def compute_localization_metrics(ranked_indices, truth, max_k=5):
    """Compute AC@1..K and Avg@K from per-case entity rankings.

    Avg@K follows the paper's cumulative definition: the arithmetic mean of
    AC@1 through AC@K, rather than the mean of only the reported odd ranks.
    """
    ranked_indices = np.asarray(ranked_indices)
    truth = np.asarray(truth)

    if ranked_indices.ndim != 2 or truth.ndim != 2:
        raise ValueError("ranked_indices and truth must be two-dimensional")
    if ranked_indices.shape != truth.shape:
        raise ValueError("ranked_indices and truth must have matching shapes")
    if ranked_indices.shape[0] == 0:
        raise ValueError("localization evaluation requires at least one sample")
    if max_k < 1:
        raise ValueError("max_k must be at least 1")

    sample_count, candidate_count = ranked_indices.shape
    metrics = {}
    for k in range(1, max_k + 1):
        effective_k = min(k, candidate_count)
        top_k = ranked_indices[:, :effective_k]
        hits = np.take_along_axis(truth, top_k, axis=1).any(axis=1)
        metrics[f"AC@{k}"] = float(hits.sum() / sample_count)

    metrics[f"Avg@{max_k}"] = float(
        np.mean([metrics[f"AC@{k}"] for k in range(1, max_k + 1)])
    )
    return metrics
