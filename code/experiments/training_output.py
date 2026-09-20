import csv
import json
import math
from pathlib import Path


EPOCH_FIELDS = [
    "epoch",
    "total_loss",
    "labeled_loss",
    "iterative_loss",
    "learning_rate",
    "duration_seconds",
]


def make_epoch_record(
    *,
    epoch,
    total_loss,
    labeled_loss,
    iterative_loss,
    learning_rate,
    duration_seconds,
):
    record = {
        "epoch": int(epoch),
        "total_loss": float(total_loss),
        "labeled_loss": float(labeled_loss),
        "iterative_loss": float(iterative_loss),
        "learning_rate": float(learning_rate),
        "duration_seconds": float(duration_seconds),
    }
    if record["epoch"] < 0:
        raise ValueError("epoch must be non-negative")
    non_finite = [
        f"{field}={record[field]}"
        for field in EPOCH_FIELDS[1:]
        if not math.isfinite(record[field])
    ]
    if non_finite:
        raise ValueError(f"non-finite training metrics: {', '.join(non_finite)}")
    return record


def _write_json_exclusive(path, value):
    with path.open("x", encoding="utf-8") as output_file:
        json.dump(value, output_file, ensure_ascii=False, indent=2, sort_keys=True)
        output_file.write("\n")


def training_output_paths(output_directory):
    output_directory = Path(output_directory)
    return {
        "history_json": output_directory / "training_history.json",
        "history_csv": output_directory / "training_history.csv",
        "summary_json": output_directory / "training_summary.json",
    }


def ensure_training_output_available(output_directory):
    paths = training_output_paths(output_directory)
    existing = [path for path in paths.values() if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite training output: {existing[0]}")
    return paths


def write_training_outputs(output_directory, epoch_records, summary):
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    paths = ensure_training_output_available(output_directory)

    _write_json_exclusive(paths["history_json"], epoch_records)
    with paths["history_csv"].open(
        "x", encoding="utf-8", newline=""
    ) as output_file:
        writer = csv.DictWriter(output_file, fieldnames=EPOCH_FIELDS)
        writer.writeheader()
        writer.writerows(epoch_records)
    _write_json_exclusive(paths["summary_json"], summary)
    return paths
