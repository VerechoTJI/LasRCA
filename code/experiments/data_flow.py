import math

import numpy as np
import torch


def _as_numpy(value):
    if torch.is_tensor(value):
        return value.detach().cpu().numpy()
    return np.asarray(value)


def summarize_tensor(name, value):
    array = _as_numpy(value)
    finite = np.isfinite(array)
    finite_values = array[finite]
    summary = {
        "name": name,
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "element_count": int(array.size),
        "finite_count": int(finite.sum()),
        "nan_count": int(np.isnan(array).sum()),
        "positive_inf_count": int(np.isposinf(array).sum()),
        "negative_inf_count": int(np.isneginf(array).sum()),
    }
    if finite_values.size:
        summary.update(
            {
                "minimum": float(finite_values.min()),
                "maximum": float(finite_values.max()),
                "mean": float(finite_values.mean()),
                "standard_deviation": float(finite_values.std()),
            }
        )
    else:
        summary.update(
            {
                "minimum": None,
                "maximum": None,
                "mean": None,
                "standard_deviation": None,
            }
        )
    return summary


def binary_confusion_score(probabilities):
    probabilities = np.asarray(probabilities, dtype=np.float64)
    clipped = np.clip(probabilities, 1e-10, 1 - 1e-10)
    return -clipped * np.log2(clipped) - (1 - clipped) * np.log2(1 - clipped)


def validate_edge_index(edge_index, entity_count):
    edge_index = _as_numpy(edge_index)
    if edge_index.ndim == 3 and edge_index.shape[0] == 1:
        edge_index = edge_index[0]
    if edge_index.ndim != 2 or edge_index.shape[0] != 2:
        raise ValueError("edge_index must have shape (2, edge_count)")
    if edge_index.size and (edge_index.min() < 0 or edge_index.max() >= entity_count):
        raise ValueError("edge_index contains an index outside entity range")

    edges = [tuple(map(int, edge)) for edge in edge_index.T]
    duplicate_count = len(edges) - len(set(edges))
    return {
        "shape": list(edge_index.shape),
        "edge_count": len(edges),
        "self_loop_count": sum(source == target for source, target in edges),
        "duplicate_edge_count": duplicate_count,
        "dangling_edge_count": 0,
        "minimum_entity_index": int(edge_index.min()) if edge_index.size else None,
        "maximum_entity_index": int(edge_index.max()) if edge_index.size else None,
    }


def _clone_batch(batch):
    return {
        key: value.detach().clone() if torch.is_tensor(value) else value
        for key, value in batch.items()
    }


def _cpu_array(value):
    return value.detach().cpu().numpy().copy()


def trace_sequential_model(model, batch, modal_types):
    if len(model) != 4:
        raise ValueError("expected four-stage LasRCA sequential model")

    was_training = model.training
    model.eval()
    traced_batch = _clone_batch(batch)
    direct_batch = _clone_batch(batch)
    try:
        with torch.no_grad():
            represented = model[0](traced_batch)
            modal_embeddings = {
                modal_type: _cpu_array(represented[f"x_{modal_type}"])
                for modal_type in modal_types
            }
            integrated = model[1](represented)
            entity_pre_graph = _cpu_array(integrated["x_ent"])
            fused = model[2](integrated)
            entity_post_graph = _cpu_array(fused)
            logits_tensors = model[3](fused)
            direct_logits = model(direct_batch)
    finally:
        model.train(was_training)

    logits = {key: _cpu_array(value) for key, value in logits_tensors.items()}
    probabilities = {
        key: _cpu_array(torch.sigmoid(value)) for key, value in logits_tensors.items()
    }
    confusion_scores = {
        key: binary_confusion_score(value) for key, value in probabilities.items()
    }
    differences = [
        float(np.max(np.abs(logits[key] - _cpu_array(direct_logits[key]))))
        for key in logits
    ]
    maximum_difference = max(differences, default=0.0)
    if not math.isfinite(maximum_difference):
        raise ValueError("non-finite forward comparison")

    return {
        "modal_embeddings": modal_embeddings,
        "entity_pre_graph": entity_pre_graph,
        "entity_post_graph": entity_post_graph,
        "logits": logits,
        "probabilities": probabilities,
        "confusion_scores": confusion_scores,
        "max_forward_difference": maximum_difference,
    }
