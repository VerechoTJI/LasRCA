import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from experiments.artifacts import sha256_file
from tasks.selection_run import load_checkpoint_records, resolve_output_directory


class SelectionRunTests(unittest.TestCase):
    def test_loads_and_verifies_exact_formal_seed_set(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            records = []
            for seed in range(405, 410):
                checkpoint = root / f"model_seed_{seed}_k_0.pkl"
                checkpoint.write_bytes(f"checkpoint-{seed}".encode("ascii"))
                records.append(
                    {
                        "seed": seed,
                        "checkpoint_path": str(checkpoint),
                        "sha256": sha256_file(checkpoint),
                    }
                )
            manifest = root / "checkpoint_manifest.json"
            manifest.write_text(json.dumps(records), encoding="utf-8")

            loaded = load_checkpoint_records(manifest)

            self.assertEqual([record["seed"] for record in loaded], list(range(405, 410)))
            self.assertTrue(all(record["verified"] for record in loaded))
            self.assertTrue(all("checkpoint_sha256" in record for record in loaded))

    def test_rejects_incomplete_checkpoint_seed_set(self):
        with TemporaryDirectory() as temporary_directory:
            manifest = Path(temporary_directory) / "checkpoint_manifest.json"
            manifest.write_text("[]", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_checkpoint_records(manifest)

    def test_uses_run_scoped_selection_directory(self):
        with TemporaryDirectory() as temporary_directory:
            with patch.dict(
                os.environ,
                {"LASRCA_RUN_DIR": temporary_directory},
                clear=False,
            ):
                output = resolve_output_directory(None)

            self.assertEqual(output, Path(temporary_directory) / "selection")


if __name__ == "__main__":
    unittest.main()
