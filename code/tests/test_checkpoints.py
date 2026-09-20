import tempfile
import unittest
from pathlib import Path

from experiments.checkpoints import (
    checkpoint_path,
    ensure_checkpoint_target_available,
    resolve_checkpoint_directory,
)


class CheckpointSafetyTests(unittest.TestCase):
    def test_evaluation_defaults_to_released_checkpoint_directory(self):
        released = Path("C:/released/models")

        resolved = resolve_checkpoint_directory(
            "evaluate", released, explicit_directory=None, environment={}
        )

        self.assertEqual(resolved, released)

    def test_training_defaults_to_run_scoped_checkpoint_directory(self):
        resolved = resolve_checkpoint_directory(
            "train",
            Path("C:/released/models"),
            explicit_directory=None,
            environment={"LASRCA_RUN_DIR": "C:/runs/run-123"},
        )

        self.assertEqual(resolved, Path("C:/runs/run-123/checkpoints"))

    def test_training_without_a_safe_output_directory_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "run-scoped checkpoint"):
            resolve_checkpoint_directory(
                "train", Path("C:/released/models"), None, environment={}
            )

    def test_training_cannot_target_released_checkpoint_directory(self):
        released = Path("C:/released/models")

        with self.assertRaisesRegex(ValueError, "released checkpoint"):
            resolve_checkpoint_directory(
                "train", released, explicit_directory=released, environment={}
            )

    def test_checkpoint_name_distinguishes_k0_and_iterative_models(self):
        directory = Path("C:/runs/run-123/checkpoints")

        self.assertEqual(
            checkpoint_path(directory, seed=405, k=0, labeling_strategy="GPT4").name,
            "model_seed_405_k_0.pkl",
        )
        self.assertEqual(
            checkpoint_path(directory, seed=405, k=1, labeling_strategy="GPT4").name,
            "model_seed_405_k_1_GPT4.pkl",
        )

    def test_existing_checkpoint_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            checkpoint = Path(temporary_directory) / "model.pkl"
            checkpoint.write_bytes(b"released")

            with self.assertRaisesRegex(FileExistsError, "refusing to overwrite"):
                ensure_checkpoint_target_available(checkpoint)


if __name__ == "__main__":
    unittest.main()
