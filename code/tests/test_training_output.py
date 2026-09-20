import json
import tempfile
import unittest
from pathlib import Path

from experiments.training_output import make_epoch_record, write_training_outputs


class TrainingOutputTests(unittest.TestCase):
    def test_epoch_record_contains_finite_numeric_values(self):
        record = make_epoch_record(
            epoch=1,
            total_loss=3.5,
            labeled_loss=2.0,
            iterative_loss=1.5,
            learning_rate=0.0001,
            duration_seconds=4.25,
        )

        self.assertEqual(record["epoch"], 1)
        self.assertEqual(record["total_loss"], 3.5)
        self.assertEqual(record["labeled_loss"], 2.0)
        self.assertEqual(record["iterative_loss"], 1.5)
        self.assertEqual(record["learning_rate"], 0.0001)
        self.assertEqual(record["duration_seconds"], 4.25)

    def test_epoch_record_rejects_non_finite_loss(self):
        with self.assertRaisesRegex(ValueError, "total_loss=nan"):
            make_epoch_record(
                epoch=0,
                total_loss=float("nan"),
                labeled_loss=1.0,
                iterative_loss=0.0,
                learning_rate=0.0001,
                duration_seconds=1.0,
            )

    def test_epoch_record_names_every_non_finite_metric(self):
        with self.assertRaisesRegex(
            ValueError, "labeled_loss=inf, learning_rate=-inf"
        ):
            make_epoch_record(
                epoch=3,
                total_loss=1.0,
                labeled_loss=float("inf"),
                iterative_loss=0.0,
                learning_rate=float("-inf"),
                duration_seconds=1.0,
            )

    def test_writes_training_history_and_summary_without_overwriting(self):
        records = [
            make_epoch_record(
                epoch=0,
                total_loss=3.5,
                labeled_loss=3.5,
                iterative_loss=0.0,
                learning_rate=0.0001,
                duration_seconds=4.25,
            )
        ]
        summary = {
            "seed": 405,
            "completed_epochs": 1,
            "checkpoint_sha256": "a" * 64,
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            write_training_outputs(output_directory, records, summary)

            history = json.loads(
                (output_directory / "training_history.json").read_text()
            )
            saved_summary = json.loads(
                (output_directory / "training_summary.json").read_text()
            )
            self.assertEqual(history, records)
            self.assertEqual(saved_summary["seed"], 405)
            self.assertTrue((output_directory / "training_history.csv").is_file())

            with self.assertRaises(FileExistsError):
                write_training_outputs(output_directory, records, summary)


if __name__ == "__main__":
    unittest.main()
