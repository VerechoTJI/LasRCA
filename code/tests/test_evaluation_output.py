import csv
import json
import tempfile
import unittest
from pathlib import Path

from experiments.evaluation_output import (
    build_metric_records,
    summarize_metric_records,
    write_evaluation_outputs,
)


class EvaluationOutputTests(unittest.TestCase):
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
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["seed"], 405)
        self.assertEqual(records[0]["entity_type"], "service")
        self.assertEqual(records[0]["AC@4"], 0.7)
        self.assertEqual(records[0]["micro_precision_score"], 0.7)
        self.assertNotIn("precision_score", records[0])

    def test_summarizes_mean_and_population_standard_deviation(self):
        records = build_metric_records(
            self.seed_results,
            dataset="A/metric_trace_log",
            track="released-artifact",
            method="LasRCA",
            strategy="one-shot-k0",
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


if __name__ == "__main__":
    unittest.main()
