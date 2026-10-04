import csv
import json
import tempfile
import unittest
from pathlib import Path

from experiments.artifacts import sha256_file
from experiments.evaluation_output import (
    build_classification_metric_records,
    build_metric_records,
    resolve_metrics_output_directory,
    summarize_metric_records,
    write_evaluation_outputs,
)


class EvaluationOutputTests(unittest.TestCase):
    def test_sweep_summary_combines_independent_seed_runs(self):
        identities=dict(environment_id='local',dataset='A',track='paired',method='LasRCA',strategy='k0',entity_type='node')
        records=[dict(identities,run_id=f'run-{i}',seed=405+i,**{'AC@1':i/10}) for i in range(5)]
        summary=summarize_metric_records(records,summary_run_id='five-seed-sweep')
        self.assertEqual(len(summary),1)
        self.assertEqual(summary[0]['count'],5)
        self.assertAlmostEqual(summary[0]['mean'],.2)
        self.assertAlmostEqual(summary[0]['std'],(.02)**.5)
        self.assertEqual(records[0]['run_id'],'run-0')

    def setUp(self):
        self.seed_results = [
            {
                "seed": 405,
                "checkpoint_path": "model_seed_405_k_0.pkl",
                "checkpoint_sha256": "a" * 64,
                "localization": {
                    "service": {
                        "AC@1": 0.4,
                        "AC@2": 0.5,
                        "AC@3": 0.6,
                        "AC@4": 0.7,
                        "AC@5": 0.8,
                        "Avg@5": 0.6,
                    }
                },
                "classification": {
                    "service": {
                        "micro_precision_score": ["0.7"],
                        "macro_precision_score": ["0.6"],
                        "micro_recall_score": ["0.5"],
                        "macro_recall_score": ["0.4"],
                        "micro_f1_score": ["0.3"],
                        "macro_f1_score": ["0.2"],
                        "precision_score": ["[0.1 0.2]"],
                    }
                },
            },
            {
                "seed": 406,
                "checkpoint_path": "model_seed_406_k_0.pkl",
                "checkpoint_sha256": "b" * 64,
                "localization": {
                    "service": {
                        "AC@1": 0.6,
                        "AC@2": 0.7,
                        "AC@3": 0.8,
                        "AC@4": 0.9,
                        "AC@5": 1.0,
                        "Avg@5": 0.8,
                    }
                },
                "classification": {
                    "service": {
                        "micro_precision_score": ["0.9"],
                        "macro_precision_score": ["0.8"],
                        "micro_recall_score": ["0.7"],
                        "macro_recall_score": ["0.6"],
                        "micro_f1_score": ["0.5"],
                        "macro_f1_score": ["0.4"],
                    }
                },
            },
        ]

    def test_builds_numeric_per_seed_records(self):
        records = build_metric_records(
            self.seed_results,
            dataset="A/metric_trace_log",
            track="released-artifact",
            method="LasRCA",
            strategy="one-shot-k0",
            environment_id="primary-windows",
            run_id="run-123",
            dataset_path="dataset.pkl",
            dataset_sha256="c" * 64,
            ground_truth_path="ground-truth.pkl",
            ground_truth_sha256="d" * 64,
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["seed"], 405)
        self.assertEqual(records[0]["environment_id"], "primary-windows")
        self.assertEqual(records[0]["run_id"], "run-123")
        self.assertEqual(records[0]["entity_type"], "service")
        self.assertEqual(records[0]["AC@4"], 0.7)
        self.assertEqual(records[0]["micro_precision_score"], 0.7)
        self.assertEqual(records[0]["dataset_sha256"], "c" * 64)
        self.assertNotIn("precision_score", records[0])

    def test_builds_and_summarizes_classification_only_records(self):
        seed_results = [
            {
                "seed": 405,
                "checkpoint_path": "model_seed_405.pkl",
                "checkpoint_sha256": "a" * 64,
                "classification": {
                    "pod": {
                        "micro_precision_score": ["0.7"],
                        "macro_precision_score": ["0.6"],
                        "micro_recall_score": ["0.5"],
                        "macro_recall_score": ["0.4"],
                        "micro_f1_score": ["0.3"],
                        "macro_f1_score": ["0.2"],
                    }
                },
            },
            {
                "seed": 406,
                "checkpoint_path": "model_seed_406.pkl",
                "checkpoint_sha256": "b" * 64,
                "classification": {
                    "pod": {
                        "micro_precision_score": ["0.9"],
                        "macro_precision_score": ["0.8"],
                        "micro_recall_score": ["0.7"],
                        "macro_recall_score": ["0.6"],
                        "micro_f1_score": ["0.5"],
                        "macro_f1_score": ["0.4"],
                    }
                },
            },
        ]

        records = build_classification_metric_records(
            seed_results,
            dataset="A/metric_trace_log",
            track="released-artifact",
            method="Pretrain and Fine-tuning",
            strategy="classification-only",
            environment_id="primary-windows",
            run_id="run-456",
            dataset_path="dataset.pkl",
            dataset_sha256="c" * 64,
            ground_truth_path="ground-truth.pkl",
            ground_truth_sha256="d" * 64,
        )
        summary = summarize_metric_records(records)

        self.assertEqual(len(records), 2)
        self.assertNotIn("AC@1", records[0])
        self.assertEqual(records[0]["micro_f1_score"], 0.3)
        self.assertEqual(
            {item["metric"] for item in summary},
            {
                "micro_precision_score",
                "macro_precision_score",
                "micro_recall_score",
                "macro_recall_score",
                "micro_f1_score",
                "macro_f1_score",
            },
        )
        micro_f1 = next(
            item for item in summary if item["metric"] == "micro_f1_score"
        )
        self.assertAlmostEqual(micro_f1["mean"], 0.4)
        self.assertAlmostEqual(micro_f1["std"], 0.1)

    def test_writes_blank_localization_fields_for_classification_only_records(self):
        records = build_classification_metric_records(
            [
                {
                    "seed": 405,
                    "checkpoint_path": "model_seed_405.pkl",
                    "checkpoint_sha256": "a" * 64,
                    "classification": {
                        "pod": {
                            "micro_precision_score": 0.7,
                            "macro_precision_score": 0.6,
                            "micro_recall_score": 0.5,
                            "macro_recall_score": 0.4,
                            "micro_f1_score": 0.3,
                            "macro_f1_score": 0.2,
                        }
                    },
                }
            ],
            dataset="A/metric_trace_log",
            track="released-artifact",
            method="Pretrain and Fine-tuning",
            strategy="classification-only",
            environment_id="primary-windows",
            run_id="run-789",
            dataset_path="dataset.pkl",
            dataset_sha256="c" * 64,
            ground_truth_path="ground-truth.pkl",
            ground_truth_sha256="d" * 64,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_evaluation_outputs(
                output_directory, records, summarize_metric_records(records)
            )
            with (output_directory / "per_seed_metrics.csv").open(newline="") as f:
                csv_record = next(csv.DictReader(f))

        self.assertEqual(csv_record["AC@1"], "")
        self.assertEqual(csv_record["micro_f1_score"], "0.3")

    def test_summarizes_mean_and_population_standard_deviation(self):
        records = build_metric_records(
            self.seed_results,
            dataset="A/metric_trace_log",
            track="released-artifact",
            method="LasRCA",
            strategy="one-shot-k0",
            environment_id="primary-windows",
            run_id="run-123",
            dataset_path="dataset.pkl",
            dataset_sha256="c" * 64,
            ground_truth_path="ground-truth.pkl",
            ground_truth_sha256="d" * 64,
        )

        summary = summarize_metric_records(records)
        ac1 = next(item for item in summary if item["metric"] == "AC@1")

        self.assertEqual(ac1["count"], 2)
        self.assertAlmostEqual(ac1["mean"], 0.5)
        self.assertAlmostEqual(ac1["std"], 0.1)

    def test_writes_json_and_csv_without_overwriting(self):
        records = build_metric_records(
            self.seed_results,
            dataset="A/metric_trace_log",
            track="released-artifact",
            method="LasRCA",
            strategy="one-shot-k0",
            environment_id="primary-windows",
            run_id="run-123",
            dataset_path="dataset.pkl",
            dataset_sha256="c" * 64,
            ground_truth_path="ground-truth.pkl",
            ground_truth_sha256="d" * 64,
        )
        summary = summarize_metric_records(records)

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_evaluation_outputs(output_directory, records, summary)

            json_records = json.loads(
                (output_directory / "per_seed_metrics.json").read_text()
            )
            with (output_directory / "per_seed_metrics.csv").open(newline="") as f:
                csv_records = list(csv.DictReader(f))

            self.assertEqual(len(json_records), 2)
            self.assertEqual(len(csv_records), 2)
            self.assertTrue((output_directory / "summary.json").is_file())
            self.assertTrue((output_directory / "summary.csv").is_file())

            with self.assertRaises(FileExistsError):
                write_evaluation_outputs(output_directory, records, summary)

    def test_resolves_metrics_directory_from_runner_environment(self):
        output_directory = resolve_metrics_output_directory(
            None, {"LASRCA_RUN_DIR": "C:/runs/example"}
        )

        self.assertEqual(output_directory, Path("C:/runs/example") / "metrics")

    def test_explicit_metrics_directory_takes_precedence(self):
        output_directory = resolve_metrics_output_directory(
            "C:/explicit/metrics", {"LASRCA_RUN_DIR": "C:/runs/example"}
        )

        self.assertEqual(output_directory, Path("C:/explicit/metrics"))

    def test_hashes_input_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact = Path(temporary_directory) / "artifact.bin"
            artifact.write_bytes(b"abc")

            self.assertEqual(
                sha256_file(artifact),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )


if __name__ == "__main__":
    unittest.main()
