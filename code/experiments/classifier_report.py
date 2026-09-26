import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path

from experiments.artifacts import collect_artifacts, sha256_file
from experiments.evaluation_output import (
    build_metric_records,
    summarize_metric_records,
)


EXPECTED_SEEDS = list(range(405, 410))
PAPER_DATASETS = {"service": "A", "pod": "B", "node": "C"}


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _read_history(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as input_file:
        rows = list(csv.DictReader(input_file))
    numeric_fields = (
        "total_loss",
        "labeled_loss",
        "iterative_loss",
        "learning_rate",
        "duration_seconds",
    )
    for row in rows:
        row["epoch"] = int(row["epoch"])
        for field in numeric_fields:
            row[field] = float(row[field])
            if not math.isfinite(row[field]):
                raise ValueError(f"non-finite training history value: {field}")
    return rows


def _validate_avg5(localization, seed, entity_type):
    expected = sum(float(localization[f"AC@{rank}"]) for rank in range(1, 6)) / 5
    actual = float(localization["Avg@5"])
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12):
        raise ValueError(f"Avg@5 mismatch for seed {seed} {entity_type}")


def _command_option(command, option):
    try:
        return command[command.index(option) + 1]
    except (ValueError, IndexError) as error:
        raise ValueError(f"missing command option {option}") from error


def _require_consistent(seed_results, field):
    values = {result[field] for result in seed_results}
    if len(values) != 1:
        raise ValueError(f"{field} differs across seeds")


def build_classifier_report(controller_directory):
    controller_directory = Path(controller_directory).resolve()
    completion = _read_json(controller_directory / "completion.json")
    started = _read_json(controller_directory / "started.json")
    if completion.get("status") != "completed":
        raise ValueError("formal controller is not completed")

    runs = completion.get("runs", [])
    seeds = [int(run["seed"]) for run in runs]
    if seeds != EXPECTED_SEEDS or len(set(seeds)) != len(seeds):
        raise ValueError(f"expected seeds {EXPECTED_SEEDS}, got {seeds}")
    if started.get("seeds") != EXPECTED_SEEDS:
        raise ValueError("controller start metadata has unexpected seeds")
    if int(started.get("epochs_per_seed", -1)) != 500:
        raise ValueError("controller start metadata has unexpected epochs")

    seed_results = []
    training_records = []
    checkpoint_records = []
    source_runs = []
    for run in runs:
        seed = int(run["seed"])
        if run.get("status") != "completed" or int(run.get("exit_code", -1)) != 0:
            raise ValueError(f"seed {seed} did not complete successfully")

        run_path = Path(run["run_path"]).resolve()
        summary = _read_json(run_path / "metrics" / "training_summary.json")
        manifest = _read_json(run_path / "manifest.json")
        environment = _read_json(run_path / "environment.json")
        history = _read_history(run_path / "metrics" / "training_history.csv")
        if summary.get("seed") != seed:
            raise ValueError(f"seed identity mismatch for seed {seed}")
        if int(manifest.get("exit_code", -1)) != 0:
            raise ValueError(f"run manifest exit code is nonzero for seed {seed}")
        if summary.get("strategy") != "one-shot-k0":
            raise ValueError(f"unexpected strategy for seed {seed}")
        if int(summary.get("requested_epochs", -1)) != 500:
            raise ValueError(f"unexpected requested epochs for seed {seed}")
        if int(summary.get("completed_epochs", -1)) != 500:
            raise ValueError(f"unexpected completed epochs for seed {seed}")
        if [row["epoch"] for row in history] != list(range(500)):
            raise ValueError(f"incomplete training history for seed {seed}")

        checkpoint_path = Path(summary["checkpoint_path"]).resolve()
        if not checkpoint_path.is_file():
            raise ValueError(f"checkpoint missing for seed {seed}")
        actual_checkpoint_sha = sha256_file(checkpoint_path)
        if actual_checkpoint_sha != summary["checkpoint_sha256"]:
            raise ValueError(f"checkpoint SHA256 mismatch for seed {seed}")

        preprocessing = summary["trace_preprocessing"]
        if preprocessing.get("zero_iqr_fallback") != "std":
            raise ValueError(f"unexpected zero-IQR fallback for seed {seed}")
        if preprocessing.get("percentile_clip") != "stored-1-99":
            raise ValueError(f"unexpected percentile clipping for seed {seed}")
        command = manifest.get("command", [])
        expected_options = {
            "--mode": "train",
            "--k": "0",
            "--seed": str(seed),
            "--epochs": "500",
            "--track": "local-full-trace-stable",
            "--trace_zero_iqr_fallback": "std",
            "--trace_percentile_clip": "stored-1-99",
        }
        for option, expected in expected_options.items():
            if str(_command_option(command, option)) != expected:
                raise ValueError(f"unexpected {option} for seed {seed}")
        for entity_type, localization in summary["localization"].items():
            _validate_avg5(localization, seed, entity_type)

        final_epoch = history[-1]
        training_records.append(
            {
                "seed": seed,
                "run_id": summary["run_id"],
                "run_path": str(run_path),
                "environment_id": summary["environment_id"],
                "gpu": environment.get("gpu"),
                "strategy": summary["strategy"],
                "k": 0,
                "track": summary["track"],
                "requested_epochs": int(summary["requested_epochs"]),
                "completed_epochs": int(summary["completed_epochs"]),
                "zero_iqr_fallback": preprocessing["zero_iqr_fallback"],
                "percentile_clip": preprocessing["percentile_clip"],
                "dataset_path": summary["dataset_path"],
                "dataset_sha256": summary["dataset_sha256"],
                "ground_truth_path": summary["ground_truth_path"],
                "ground_truth_sha256": summary["ground_truth_sha256"],
                "training_duration_seconds": float(summary["duration_seconds"]),
                "wall_clock_duration_seconds": float(manifest["duration_seconds"]),
                "final_total_loss": final_epoch["total_loss"],
                "final_labeled_loss": final_epoch["labeled_loss"],
                "final_iterative_loss": final_epoch["iterative_loss"],
                "peak_gpu_memory_bytes": int(summary["peak_gpu_memory_bytes"]),
                "checkpoint_path": str(checkpoint_path),
                "checkpoint_bytes": checkpoint_path.stat().st_size,
                "checkpoint_sha256": actual_checkpoint_sha,
                "checkpoint_sha256_verified": True,
                "exit_code": int(manifest["exit_code"]),
                "command": manifest["command"],
            }
        )
        checkpoint_records.append(
            {
                "seed": seed,
                "checkpoint_path": str(checkpoint_path),
                "bytes": checkpoint_path.stat().st_size,
                "sha256": actual_checkpoint_sha,
                "verified": True,
            }
        )
        seed_results.append(summary)
        source_runs.append({"seed": seed, "run_path": str(run_path)})

    for field in (
        "dataset",
        "dataset_path",
        "dataset_sha256",
        "ground_truth_path",
        "ground_truth_sha256",
        "environment_id",
        "strategy",
        "track",
    ):
        _require_consistent(seed_results, field)

    first = seed_results[0]
    metric_records = build_metric_records(
        seed_results,
        dataset=first["dataset"],
        track=first["track"],
        method="LasRCA small classifier",
        strategy=first["strategy"],
        environment_id=first["environment_id"],
        run_id=controller_directory.name,
        dataset_path=first["dataset_path"],
        dataset_sha256=first["dataset_sha256"],
        ground_truth_path=first["ground_truth_path"],
        ground_truth_sha256=first["ground_truth_sha256"],
    )
    for record in metric_records:
        record["paper_dataset"] = PAPER_DATASETS[record["entity_type"]]

    return {
        "run_index": {
            "source_controller": str(controller_directory),
            "source_commit": started["commit"],
            "source_runs": source_runs,
            "preprocessing_deviation": {
                "paper_faithful": False,
                "zero_iqr_fallback": started["trace_zero_iqr_fallback"],
                "percentile_clip": started["trace_percentile_clip"],
            },
        },
        "training_records": training_records,
        "checkpoint_records": checkpoint_records,
        "metric_records": metric_records,
        "metric_summary": summarize_metric_records(metric_records),
        "validation": {
            "status": "passed",
            "expected_seeds": EXPECTED_SEEDS,
            "observed_seeds": seeds,
            "checks": {
                "controller_completed": True,
                "all_exit_codes_zero": True,
                "all_histories_have_500_epochs": True,
                "all_checkpoint_hashes_verified": True,
                "all_avg5_values_recomputed": True,
            },
        },
    }


def _write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as output_file:
        json.dump(value, output_file, ensure_ascii=False, indent=2, sort_keys=True)
        output_file.write("\n")


def _write_csv(path, records):
    fieldnames = list(records[0]) if records else []
    with Path(path).open("x", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = {
                key: json.dumps(value, ensure_ascii=False)
                if isinstance(value, (list, dict))
                else value
                for key, value in record.items()
            }
            writer.writerow(row)


def _readme(report):
    run_index = report["run_index"]
    return f"""# LasRCA Classifier reproduction evidence

This package aggregates the completed one-shot (`k=0`) small-classifier runs
for seeds 405–409. It does not retrain or modify the source runs.

## Source

- Controller: `{run_index['source_controller']}`
- Training commit: `{run_index['source_commit']}`
- Environment: primary-windows
- Seeds: 405, 406, 407, 408, 409
- Epochs per seed: 500

## Required results

- `per_seed_training.*`: checkpoint, settings, runtime, loss, and GPU memory
- `per_seed_metrics.*`: localization and fault-type metrics per seed
- `summary.*`: mean and population standard deviation over five seeds
- `checkpoint_manifest.*`: independently verified checkpoint hashes
- `validation.json`: completeness and arithmetic checks

Paper datasets A, B, and C map to service, pod, and node respectively.
`Avg@5` was independently recomputed from AC@1 through AC@5.

## Declared deviation

These are not paper-faithful preprocessing results. The completed runs used a
zero-IQR standard-deviation fallback and stored 1st/99th percentile clipping.
"""


def write_classifier_report(output_directory, report):
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=False)
    paths = {
        "run_index": output_directory / "run_index.json",
        "training_json": output_directory / "per_seed_training.json",
        "training_csv": output_directory / "per_seed_training.csv",
        "metrics_json": output_directory / "per_seed_metrics.json",
        "metrics_csv": output_directory / "per_seed_metrics.csv",
        "summary_json": output_directory / "summary.json",
        "summary_csv": output_directory / "summary.csv",
        "checkpoint_json": output_directory / "checkpoint_manifest.json",
        "checkpoint_csv": output_directory / "checkpoint_manifest.csv",
        "validation": output_directory / "validation.json",
        "readme": output_directory / "README.md",
        "completion": output_directory / "completion.json",
        "artifact_manifest": output_directory / "artifact_manifest.json",
    }

    _write_json(paths["run_index"], report["run_index"])
    _write_json(paths["training_json"], report["training_records"])
    _write_csv(paths["training_csv"], report["training_records"])
    _write_json(paths["metrics_json"], report["metric_records"])
    _write_csv(paths["metrics_csv"], report["metric_records"])
    _write_json(paths["summary_json"], report["metric_summary"])
    _write_csv(paths["summary_csv"], report["metric_summary"])
    _write_json(paths["checkpoint_json"], report["checkpoint_records"])
    _write_csv(paths["checkpoint_csv"], report["checkpoint_records"])
    _write_json(paths["validation"], report["validation"])
    with paths["readme"].open("x", encoding="utf-8") as output_file:
        output_file.write(_readme(report))
    _write_json(
        paths["completion"],
        {
            "status": "completed",
            "completed_at": datetime.now().astimezone().isoformat(),
            "seed_count": len(report["training_records"]),
            "per_seed_metric_records": len(report["metric_records"]),
            "summary_records": len(report["metric_summary"]),
        },
    )
    _write_json(
        paths["artifact_manifest"],
        {
            "artifacts": collect_artifacts(
                output_directory, excluded_names={"artifact_manifest.json"}
            )
        },
    )
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate and aggregate completed LasRCA classifier runs."
    )
    parser.add_argument("--controller", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args(argv)
    report = build_classifier_report(arguments.controller)
    write_classifier_report(arguments.output, report)
    print(arguments.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
