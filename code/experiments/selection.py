import math

import numpy as np


def binary_entropy(probability):
    probability = float(np.clip(probability, 1e-10, 1 - 1e-10))
    return -probability * math.log2(probability) - (
        1 - probability
    ) * math.log2(1 - probability)


def _entity_type(meta_data, entity_index):
    for entity_type in meta_data["ent_types"]:
        start, end = meta_data["ent_type_index"][entity_type]
        if start <= entity_index < end:
            return entity_type
    raise IndexError(f"entity index is outside the metadata ranges: {entity_index}")


def _is_masked(y_mask, sample_index, entity_index, fault_type_index):
    if y_mask.ndim == 2:
        return bool(y_mask[sample_index, entity_index])
    if y_mask.ndim == 3:
        return bool(y_mask[sample_index, entity_index, fault_type_index])
    raise ValueError("y_mask must have shape (cases, entities) or (cases, entities, faults)")


def build_candidate_ranking(
    meta_data,
    mean_probabilities,
    y_mask,
    *,
    seed_probabilities=None,
    seeds=None,
):
    mean_probabilities = np.asarray(mean_probabilities)
    y_mask = np.asarray(y_mask)
    if mean_probabilities.ndim != 3:
        raise ValueError("mean_probabilities must have shape (cases, entities, faults)")
    if y_mask.shape[:2] != mean_probabilities.shape[:2]:
        raise ValueError("y_mask case/entity dimensions must match probabilities")

    seeds = list(seeds or [])
    if seed_probabilities is not None:
        seed_probabilities = np.asarray(seed_probabilities)
        expected = (len(seeds),) + mean_probabilities.shape
        if seed_probabilities.shape != expected:
            raise ValueError(
                f"seed_probabilities has shape {seed_probabilities.shape}, expected {expected}"
            )

    records = []
    case_count, entity_count, _fault_count = mean_probabilities.shape
    fault_type_names = meta_data.get(
        "en_fault_type_list", meta_data["fault_type_list"]
    )
    for sample_index in range(case_count):
        for entity_index in range(entity_count):
            entity_type = _entity_type(meta_data, entity_index)
            fault_start, fault_end = meta_data["ent_fault_type_index"][entity_type]
            for fault_type_index in range(fault_start, fault_end):
                probability = float(
                    mean_probabilities[sample_index, entity_index, fault_type_index]
                )
                masked = _is_masked(
                    y_mask, sample_index, entity_index, fault_type_index
                )
                record = {
                    "rank": None,
                    "sample_index": sample_index,
                    "entity_index": entity_index,
                    "entity_name": meta_data["ent_names"][entity_index],
                    "entity_type": entity_type,
                    "fault_type_index": fault_type_index,
                    "fault_type_name": meta_data["fault_type_list"][fault_type_index],
                    "fault_type_name_en": fault_type_names[fault_type_index],
                    "mean_probability": probability,
                    "confusion_score": binary_entropy(probability),
                    "masked_as_labeled": masked,
                    "selection_eligible": not masked,
                }
                if seed_probabilities is not None:
                    for seed_offset, seed in enumerate(seeds):
                        record[f"probability_seed_{seed}"] = float(
                            seed_probabilities[
                                seed_offset,
                                sample_index,
                                entity_index,
                                fault_type_index,
                            ]
                        )
                records.append(record)

    records.sort(
        key=lambda record: (
            not record["selection_eligible"],
            -record["confusion_score"],
            record["sample_index"],
            record["entity_index"],
            record["fault_type_index"],
        )
    )
    rank = 0
    for record in records:
        if record["selection_eligible"]:
            rank += 1
            record["rank"] = rank
    return records


def select_repository_case_budget(ranking, alpha=100):
    if alpha < 0:
        raise ValueError("alpha must not be negative")
    selected_records = []
    selected_cases = set()
    for record in ranking:
        if not record.get("selection_eligible", True):
            continue
        sample_index = int(record["sample_index"])
        if sample_index not in selected_cases:
            if len(selected_cases) >= alpha:
                break
            selected_cases.add(sample_index)
        selected_records.append(record)
    return selected_records


def paper_literal_entity_ranking(ranking, alpha=100):
    best_by_entity = {}
    for record in ranking:
        if not record.get("selection_eligible", True):
            continue
        key = (int(record["sample_index"]), int(record["entity_index"]))
        current = best_by_entity.get(key)
        if current is None or (
            record["confusion_score"], -int(record["fault_type_index"])
        ) > (current["confusion_score"], -int(current["fault_type_index"])):
            best_by_entity[key] = dict(record)

    records = sorted(
        best_by_entity.values(),
        key=lambda record: (
            -record["confusion_score"],
            record["sample_index"],
            record["entity_index"],
            record["fault_type_index"],
        ),
    )[:alpha]
    for rank, record in enumerate(records, start=1):
        record["paper_entity_rank"] = rank
    return records


def ranking_indices(ranking):
    eligible = [
        record for record in ranking if record.get("selection_eligible", True)
    ]
    return tuple(
        np.asarray([record[field] for record in eligible], dtype=np.int64)
        for field in ("sample_index", "entity_index", "fault_type_index")
    )
