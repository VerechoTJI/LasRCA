import csv
import json
import statistics
from pathlib import Path

from experiments.artifacts import sha256_file
from experiments.metrics import LOCALIZATION_METRIC_VERSION


LOCALIZATION_FIELDS = [f"AC@{k}" for k in range(1, 6)] + ["Avg@5"]
CLASSIFICATION_FIELDS = [
    f"{scope}_{metric}_score"
    for metric in ("precision", "recall", "f1")
    for scope in ("micro", "macro")
]
METRIC_FIELDS = LOCALIZATION_FIELDS + CLASSIFICATION_FIELDS
IDENTITY_FIELDS = [
    "environment_id",
    "run_id",
    "dataset",
    "track",
    "method",
    "strategy",
    "seed",
    "entity_type",
    "metric_definition_version",
    "dataset_path",
    "dataset_sha256",
    "ground_truth_path",
    "ground_truth_sha256",
    "checkpoint_path",
    "checkpoint_sha256",
]


def _scalar(value):
    while isinstance(value, list):
        if not value:
            raise ValueError("metric values must not contain empty lists")
        value = value[0]
    return float(value)


def resolve_metrics_output_directory(explicit_output, environment):
    if explicit_output:
        return Path(explicit_output)
    run_directory = environment.get("LASRCA_RUN_DIR")
    return Path(run_directory) / "metrics" if run_directory else None


def build_metric_records(
    seed_results,
    *,
    dataset,
    track,
    method,
    strategy,
    environment_id,
    run_id,
    dataset_path,
    dataset_sha256,
    ground_truth_path,
    ground_truth_sha256,
):
    records = []
    for seed_result in seed_results:
        localization = seed_result["localization"]
        classification = seed_result["classification"]
        for entity_type in localization:
            record = {
                "environment_id": environment_id,
                "run_id": run_id,
                "dataset": dataset,
                "track": track,
                "method": method,
                "strategy": strategy,
                "seed": int(seed_result["seed"]),
                "entity_type": entity_type,
                "metric_definition_version": LOCALIZATION_METRIC_VERSION,
                "dataset_path": str(dataset_path),
                "dataset_sha256": dataset_sha256,
                "ground_truth_path": str(ground_truth_path),
                "ground_truth_sha256": ground_truth_sha256,
                "checkpoint_path": str(seed_result["checkpoint_path"]),
                "checkpoint_sha256": seed_result["checkpoint_sha256"],
            }
            record.update(
                {
                    field: _scalar(localization[entity_type][field])
                    for field in LOCALIZATION_FIELDS
                }
            )
            entity_classification = classification[entity_type]
            record.update(
                {
                    field: _scalar(entity_classification[field])
                    for field in CLASSIFICATION_FIELDS
                }
            )
            records.append(record)
    return records


def build_classification_metric_records(
    seed_results,
    *,
    dataset,
    track,
    method,
    strategy,
    environment_id,
    run_id,
    dataset_path,
    dataset_sha256,
    ground_truth_path,
    ground_truth_sha256,
):
    """Build per-seed records when a method has no localization output."""
    records = []
    for seed_result in seed_results:
        for entity_type, classification in seed_result["classification"].items():
            record = {
                "environment_id": environment_id,
                "run_id": run_id,
                "dataset": dataset,
                "track": track,
                "method": method,
                "strategy": strategy,
                "seed": int(seed_result["seed"]),
                "entity_type": entity_type,
                "metric_definition_version": LOCALIZATION_METRIC_VERSION,
                "dataset_path": str(dataset_path),
                "dataset_sha256": dataset_sha256,
                "ground_truth_path": str(ground_truth_path),
                "ground_truth_sha256": ground_truth_sha256,
                "checkpoint_path": str(seed_result["checkpoint_path"]),
                "checkpoint_sha256": seed_result["checkpoint_sha256"],
            }
            record.update(
                {
                    field: _scalar(classification[field])
                    for field in CLASSIFICATION_FIELDS
                }
            )
            records.append(record)
    return records


def summarize_metric_records(records):
    groups = {}
    group_fields = [
        "environment_id",
        "run_id",
        "dataset",
        "track",
        "method",
        "strategy",
        "entity_type",
    ]
    for record in records:
        group_key = tuple(record[field] for field in group_fields)
        for metric in METRIC_FIELDS:
            if metric in record:
                groups.setdefault((group_key, metric), []).append(
                    float(record[metric])
                )

    summary = []
    for (group_key, metric), values in sorted(groups.items()):
        item = dict(zip(group_fields, group_key))
        item.update(
            {
                "metric": metric,
                "count": len(values),
                "mean": statistics.fmean(values),
                "std": statistics.pstdev(values),
                "metric_definition_version": LOCALIZATION_METRIC_VERSION,
            }
        )
        summary.append(item)
    return summary


def _write_json_exclusive(path, value):
    with path.open("x", encoding="utf-8") as output_file:
        json.dump(value, output_file, ensure_ascii=False, indent=2, sort_keys=True)
        output_file.write("\n")


def _write_csv_exclusive(path, records, fieldnames):
    with path.open("x", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def write_evaluation_outputs(output_directory, records, summary):
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "records_json": output_directory / "per_seed_metrics.json",
        "records_csv": output_directory / "per_seed_metrics.csv",
        "summary_json": output_directory / "summary.json",
        "summary_csv": output_directory / "summary.csv",
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite evaluation output: {existing[0]}")

    _write_json_exclusive(paths["records_json"], records)
    _write_csv_exclusive(
        paths["records_csv"], records, IDENTITY_FIELDS + METRIC_FIELDS
    )
    _write_json_exclusive(paths["summary_json"], summary)
    summary_fields = [
        "environment_id",
        "run_id",
        "dataset",
        "track",
        "method",
        "strategy",
        "entity_type",
        "metric",
        "count",
        "mean",
        "std",
        "metric_definition_version",
    ]
    _write_csv_exclusive(paths["summary_csv"], summary, summary_fields)
    return paths
