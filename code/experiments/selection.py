import csv
import json
import math
import pickle
from pathlib import Path

import numpy as np

from experiments.artifacts import collect_artifacts, sha256_file


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


def audit_selected_samples(samples, direct_entities_by_case=None, max_entities=10):
    direct_entities_by_case = direct_entities_by_case or {}
    subgraphs = []
    entities = []
    edges = []
    for sample in samples:
        sample_index = int(sample["sample_index"])
        entity_indices = [int(value) for value in sample["ent_indices"]]
        entity_names = list(sample["ent_names"])
        entity_types = list(sample["ent_types"])
        if not (
            len(entity_indices) == len(entity_names) == len(entity_types)
        ):
            raise ValueError("selected entity indices, names, and types must align")

        direct_entities = {
            int(value) for value in direct_entities_by_case.get(sample_index, set())
        }
        selected_names = set(entity_names)
        for position, (entity_index, entity_name, entity_type) in enumerate(
            zip(entity_indices, entity_names, entity_types)
        ):
            entities.append(
                {
                    "sample_index": sample_index,
                    "subgraph_position": position,
                    "entity_index": entity_index,
                    "entity_name": entity_name,
                    "entity_type": entity_type,
                    "selection_origin": (
                        "direct_confusion"
                        if entity_index in direct_entities
                        else "topology_neighbor"
                    ),
                }
            )

        edge_sources, edge_targets = sample["ent_edges"]
        if len(edge_sources) != len(edge_targets):
            raise ValueError("selected edge source and target arrays must align")
        seen_edges = set()
        dangling_count = 0
        duplicate_count = 0
        self_loop_count = 0
        for edge_position, (source, target) in enumerate(
            zip(edge_sources, edge_targets)
        ):
            dangling = source not in selected_names or target not in selected_names
            duplicate = (source, target) in seen_edges
            self_loop = source == target
            seen_edges.add((source, target))
            dangling_count += int(dangling)
            duplicate_count += int(duplicate)
            self_loop_count += int(self_loop)
            edges.append(
                {
                    "sample_index": sample_index,
                    "edge_position": edge_position,
                    "source": source,
                    "target": target,
                    "dangling": dangling,
                    "duplicate": duplicate,
                    "self_loop": self_loop,
                }
            )

        subgraphs.append(
            {
                "sample_index": sample_index,
                "entity_count": len(entity_names),
                "direct_entity_count": len(direct_entities.intersection(entity_indices)),
                "edge_count": len(edge_sources),
                "over_max_entities": len(entity_names) > max_entities,
                "dangling_edge_count": dangling_count,
                "duplicate_edge_count": duplicate_count,
                "self_loop_count": self_loop_count,
            }
        )

    entity_counts = [record["entity_count"] for record in subgraphs]
    summary = {
        "selected_case_count": len({record["sample_index"] for record in subgraphs}),
        "subgraph_count": len(subgraphs),
        "selected_entity_count": len(entities),
        "direct_entity_count": sum(
            record["selection_origin"] == "direct_confusion" for record in entities
        ),
        "topology_neighbor_count": sum(
            record["selection_origin"] == "topology_neighbor" for record in entities
        ),
        "minimum_entities_per_subgraph": min(entity_counts, default=0),
        "maximum_entities_per_subgraph": max(entity_counts, default=0),
        "over_max_entities_count": sum(
            record["over_max_entities"] for record in subgraphs
        ),
        "edge_count": len(edges),
        "dangling_edge_count": sum(record["dangling"] for record in edges),
        "duplicate_edge_count": sum(record["duplicate"] for record in edges),
        "self_loop_count": sum(record["self_loop"] for record in edges),
    }
    return {
        "summary": summary,
        "subgraphs": subgraphs,
        "entities": entities,
        "edges": edges,
    }


def _write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(path, records):
    fieldnames = []
    for record in records:
        for field in record:
            if field not in fieldnames:
                fieldnames.append(field)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        if not fieldnames:
            return
        writer = csv.DictWriter(output_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def write_selection_outputs(
    output_directory,
    *,
    selected_samples,
    candidate_ranking,
    paper_literal_ranking,
    direct_entities_by_case,
    checkpoint_records,
    seed_probabilities,
    mean_probabilities,
    preprocessing,
    validation,
    completion,
    max_entities=10,
):
    output_directory = Path(output_directory)
    if output_directory.exists() and any(output_directory.iterdir()):
        raise FileExistsError(f"selection output directory is not empty: {output_directory}")
    output_directory.mkdir(parents=True, exist_ok=True)

    audit = audit_selected_samples(
        selected_samples,
        direct_entities_by_case,
        max_entities=max_entities,
    )
    summary = dict(audit["summary"])
    summary.update(
        {
            "candidate_record_count": len(candidate_ranking),
            "eligible_candidate_record_count": sum(
                record.get("selection_eligible", True)
                for record in candidate_ranking
            ),
            "paper_literal_entity_count": len(paper_literal_ranking),
            "alpha": completion.get("alpha", 100),
            "repository_budget_unit": "unique_case_index",
            "paper_budget_unit": "case_entity",
            "candidate_unit": "case_entity_fault_type",
            "maximum_entities_permitted": max_entities,
        }
    )

    selected_samples_path = output_directory / "selected_samples_k_0.pkl"
    with selected_samples_path.open("wb") as output_file:
        pickle.dump(selected_samples, output_file)

    _write_json(output_directory / "candidate_ranking.json", candidate_ranking)
    _write_csv(output_directory / "candidate_ranking.csv", candidate_ranking)
    _write_json(
        output_directory / "paper_literal_top_100_entities.json",
        paper_literal_ranking,
    )
    _write_csv(
        output_directory / "paper_literal_top_100_entities.csv",
        paper_literal_ranking,
    )
    _write_json(output_directory / "subgraphs.json", audit["subgraphs"])
    _write_csv(output_directory / "selected_cases.csv", audit["subgraphs"])
    _write_csv(output_directory / "selected_entities.csv", audit["entities"])
    _write_csv(output_directory / "edges.csv", audit["edges"])
    _write_json(output_directory / "checkpoint_manifest.json", checkpoint_records)
    _write_csv(output_directory / "checkpoint_manifest.csv", checkpoint_records)
    np.savez_compressed(
        output_directory / "selection_probabilities.npz",
        seed_probabilities=np.asarray(seed_probabilities),
        mean_probabilities=np.asarray(mean_probabilities),
    )
    _write_json(output_directory / "preprocessing.json", preprocessing)

    summary["selected_samples_sha256"] = sha256_file(selected_samples_path)
    summary["selected_samples_bytes"] = selected_samples_path.stat().st_size
    _write_json(output_directory / "selection_summary.json", summary)
    _write_json(output_directory / "validation.json", validation)
    completion = dict(completion)
    completion.update(summary)
    _write_json(output_directory / "completion.json", completion)
    (output_directory / "README.md").write_text(
        "# LasRCA Selection Evidence\n\n"
        "This directory contains the complete five-checkpoint high-confusion "
        "ranking, the repository-compatible 100-case selection artifact, a "
        "literal top-100 entity diagnostic, and subgraph integrity checks.\n\n"
        "`selected_samples_k_0.pkl` is run-scoped and does not replace the "
        "released artifact under `temp_data`.\n",
        encoding="utf-8",
    )
    _write_json(
        output_directory / "artifact_manifest.json",
        {
            "artifacts": collect_artifacts(
                output_directory, excluded_names={"artifact_manifest.json"}
            )
        },
    )
    return audit | {"summary": summary}
