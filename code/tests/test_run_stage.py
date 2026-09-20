import json
import sys
import tempfile
import unittest
from pathlib import Path

from experiments.run_stage import execute_logged_command


class ExecuteLoggedCommandTests(unittest.TestCase):
    def test_successful_command_writes_complete_run_evidence(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_directory = execute_logged_command(
                base_directory=Path(temporary_directory),
                stage="evaluate",
                command=[sys.executable, "-c", "print('completed')"],
                environment={"environment_id": "primary-windows"},
            )

            self.assertEqual((run_directory / "exit_code.txt").read_text(), "0\n")
            self.assertIn("completed", (run_directory / "stdout.log").read_text())
            self.assertEqual((run_directory / "stderr.log").read_text(), "")
            self.assertTrue((run_directory / "command.txt").is_file())
            self.assertTrue((run_directory / "timing.json").is_file())
            self.assertTrue((run_directory / "environment.json").is_file())

            artifact_manifest = json.loads(
                (run_directory / "artifact_manifest.json").read_text()
            )
            artifact_paths = {
                artifact["path"] for artifact in artifact_manifest["artifacts"]
            }
            self.assertIn("stdout.log", artifact_paths)
            self.assertIn("manifest.json", artifact_paths)
            self.assertTrue(
                all(
                    len(artifact["sha256"]) == 64
                    for artifact in artifact_manifest["artifacts"]
                )
            )

            manifest = json.loads((run_directory / "manifest.json").read_text())
            self.assertEqual(manifest["stage"], "evaluate")
            self.assertEqual(manifest["environment_id"], "primary-windows")
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["exit_code"], 0)

    def test_failed_command_preserves_stderr_and_exit_code(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_directory = execute_logged_command(
                base_directory=Path(temporary_directory),
                stage="evaluate",
                command=[
                    sys.executable,
                    "-c",
                    "import sys; print('broken', file=sys.stderr); sys.exit(7)",
                ],
                environment={"environment_id": "primary-windows"},
            )

            self.assertEqual((run_directory / "exit_code.txt").read_text(), "7\n")
            self.assertIn("broken", (run_directory / "stderr.log").read_text())

            manifest = json.loads((run_directory / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["exit_code"], 7)

    def test_repeated_invocations_create_distinct_run_directories(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            arguments = {
                "base_directory": Path(temporary_directory),
                "stage": "evaluate",
                "command": [sys.executable, "-c", "pass"],
                "environment": {"environment_id": "primary-windows"},
            }

            first_run = execute_logged_command(**arguments)
            second_run = execute_logged_command(**arguments)

            self.assertNotEqual(first_run, second_run)
            self.assertTrue(first_run.is_dir())
            self.assertTrue(second_run.is_dir())

    def test_command_and_config_secrets_are_redacted_from_run_evidence(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_directory = execute_logged_command(
                base_directory=Path(temporary_directory),
                stage="evaluate",
                command=[
                    sys.executable,
                    "-c",
                    "pass",
                    "--api-key=do-not-record-this",
                    "--token",
                    "also-do-not-record-this",
                ],
                environment={"environment_id": "primary-windows"},
                config={"api_key": "configuration-secret", "seed": 405},
            )

            command_text = (run_directory / "command.txt").read_text()
            manifest_text = (run_directory / "manifest.json").read_text()
            config_text = (run_directory / "config.json").read_text()
            combined_evidence = command_text + manifest_text + config_text

            self.assertNotIn("do-not-record-this", combined_evidence)
            self.assertNotIn("also-do-not-record-this", combined_evidence)
            self.assertNotIn("configuration-secret", combined_evidence)
            self.assertIn("[REDACTED]", combined_evidence)

    def test_child_process_receives_immutable_run_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_directory = execute_logged_command(
                base_directory=Path(temporary_directory),
                stage="evaluate",
                command=[
                    sys.executable,
                    "-c",
                    (
                        "import os, pathlib; "
                        "p = pathlib.Path(os.environ['LASRCA_RUN_DIR']); "
                        "(p / 'metrics' / 'child.txt').write_text(str(p))"
                    ),
                ],
                environment={"environment_id": "primary-windows"},
            )

            child_value = (run_directory / "metrics" / "child.txt").read_text()
            self.assertEqual(Path(child_value), run_directory)


if __name__ == "__main__":
    unittest.main()
