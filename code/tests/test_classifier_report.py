import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from experiments.classifier_report import (
    build_classifier_report,
    main,
    write_classifier_report,
)


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


class ClassifierReportTests(unittest.TestCase):
    def make_controller(
        self, root, *, corrupt_checkpoint=False, mismatched_dataset=False
    ):
        runs = []
        for seed in range(405, 410):
            run = root / f"seed-{seed}"
            (run / "checkpoints").mkdir(parents=True)
            (run / "metrics").mkdir()
            checkpoint = run / "checkpoints" / f"model_seed_{seed}_k_0.pkl"
            checkpoint.write_bytes(f"checkpoint-{seed}".encode())
            checkpoint_sha = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
            if corrupt_checkpoint and seed == 405:
                checkpoint_sha = "0" * 64

            localization = {
                entity: {
                    "AC@1": 0.1,
                    "AC@2": 0.2,
                    "AC@3": 0.3,
                    "AC@4": 0.4,
                    "AC@5": 0.5,
                    "Avg@5": 0.3,
                }
                for entity in ("service", "pod", "node")
            }
            classification = {
                entity: {
                    "micro_precision_score": ["0.6"],
                    "macro_precision_score": ["0.5"],
                    "micro_recall_score": ["0.4"],
                    "macro_recall_score": ["0.3"],
                    "micro_f1_score": ["0.2"],
                    "macro_f1_score": ["0.1"],
                }
                for entity in ("service", "pod", "node")
            }
            summary = {
                "seed": seed,
                "run_id": f"run-{seed}",
                "strategy": "one-shot-k0",
                "track": "local-full-trace-stable",
                "requested_epochs": 500,
                "completed_epochs": 500,
                "duration_seconds": 100.0 + seed,
                "peak_gpu_memory_bytes": 1024,
                "dataset": "A/metric_trace_log",
                "dataset_path": "dataset.pkl",
                "dataset_sha256": (
                    "c" * 64 if mismatched_dataset and seed == 409 else "a" * 64
                ),
                "ground_truth_path": "ground_truth.pkl",
                "ground_truth_sha256": "b" * 64,
                "environment_id": "primary-windows",
                "checkpoint_path": str(checkpoint),
                "checkpoint_sha256": checkpoint_sha,
                "localization": localization,
                "classification": classification,
                "trace_preprocessing": {
                    "zero_iqr_fallback": "std",
                    "percentile_clip": "stored-1-99",
                },
            }
            write_json(run / "metrics" / "training_summary.json", summary)
            with (run / "metrics" / "training_history.csv").open(
                "w", newline="", encoding="utf-8"
            ) as output:
                writer = csv.DictWriter(
                    output,
                    fieldnames=[
                        "epoch",
                        "total_loss",
                        "labeled_loss",
                        "iterative_loss",
                        "learning_rate",
                        "duration_seconds",
                    ],
                )
                writer.writeheader()
                for epoch in range(500):
                    writer.writerow(
                        {
                            "epoch": epoch,
                            "total_loss": 1.0 / (epoch + 1),
                            "labeled_loss": 1.0 / (epoch + 1),
                            "iterative_loss": 0.0,
                            "learning_rate": 0.001,
                            "duration_seconds": 0.1,
                        }
                    )
            write_json(
                run / "manifest.json",
                {
                    "run_id": f"run-{seed}",
                    "environment_id": "primary-windows",
                    "exit_code": 0,
                    "duration_seconds": 110.0 + seed,
                    "command": [
                        "python",
                        "las_rca.py",
                        "--mode",
                        "train",
                        "--k",
                        "0",
                        "--seed",
                        str(seed),
                        "--epochs",
                        "500",
                        "--track",
                        "local-full-trace-stable",
                        "--trace_zero_iqr_fallback",
                        "std",
                        "--trace_percentile_clip",
                        "stored-1-99",
                    ],
                },
            )
            write_json(run / "environment.json", {"gpu": "test GPU"})
            runs.append(
                {
                    "seed": seed,
                    "status": "completed",
                    "exit_code": 0,
                    "run_path": str(run),
                }
            )

        controller = root / "controller"
        controller.mkdir()
        write_json(controller / "completion.json", {"status": "completed", "runs": runs})
        write_json(
            controller / "started.json",
            {
                "commit": "e528089",
                "seeds": list(range(405, 410)),
                "epochs_per_seed": 500,
                "trace_zero_iqr_fallback": "std",
                "trace_percentile_clip": "stored-1-99",
            },
        )
        return controller

    def test_builds_complete_five_seed_report(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = self.make_controller(Path(temporary_directory))
            report = build_classifier_report(controller)

        self.assertEqual(len(report["training_records"]), 5)
        self.assertEqual(len(report["metric_records"]), 15)
        self.assertEqual(len(report["metric_summary"]), 36)
        self.assertEqual(report["validation"]["status"], "passed")
        self.assertEqual(
            {record["paper_dataset"] for record in report["metric_records"]},
            {"A", "B", "C"},
        )
        first = report["training_records"][0]
        self.assertEqual(first["seed"], 405)
        self.assertEqual(first["completed_epochs"], 500)
        self.assertEqual(first["final_total_loss"], 0.002)
        self.assertTrue(first["checkpoint_sha256_verified"])

    def test_rejects_checkpoint_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = self.make_controller(
                Path(temporary_directory), corrupt_checkpoint=True
            )
            with self.assertRaisesRegex(ValueError, "checkpoint SHA256 mismatch"):
                build_classifier_report(controller)

    def test_writes_complete_package_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = self.make_controller(root)
            report = build_classifier_report(controller)
            output_directory = root / "classifier-report"

            paths = write_classifier_report(output_directory, report)

            expected_names = {
                "run_index.json",
                "per_seed_training.json",
                "per_seed_training.csv",
                "per_seed_metrics.json",
                "per_seed_metrics.csv",
                "summary.json",
                "summary.csv",
                "checkpoint_manifest.json",
                "checkpoint_manifest.csv",
                "validation.json",
                "README.md",
                "completion.json",
                "artifact_manifest.json",
            }
            self.assertEqual({path.name for path in paths.values()}, expected_names)
            completion = json.loads(
                (output_directory / "completion.json").read_text(encoding="utf-8")
            )
            self.assertEqual(completion["status"], "completed")
            self.assertEqual(completion["per_seed_metric_records"], 15)
            artifacts = json.loads(
                (output_directory / "artifact_manifest.json").read_text(
                    encoding="utf-8"
                )
            )["artifacts"]
            self.assertEqual(len(artifacts), 12)

            with self.assertRaises(FileExistsError):
                write_classifier_report(output_directory, report)

    def test_rejects_cross_seed_dataset_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            controller = self.make_controller(
                Path(temporary_directory), mismatched_dataset=True
            )
            with self.assertRaisesRegex(ValueError, "dataset_sha256 differs"):
                build_classifier_report(controller)

    def test_cli_generates_report_at_explicit_new_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            controller = self.make_controller(root)
            output_directory = root / "classifier-cli"

            exit_code = main(
                [
                    "--controller",
                    str(controller),
                    "--output",
                    str(output_directory),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((output_directory / "completion.json").is_file())


if __name__ == "__main__":
    unittest.main()
