import argparse
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path


VALID_STAGES = ("train", "evaluate", "select", "trace")
REDACTED = "[REDACTED]"
SENSITIVE_KEYS = {
    "apikey",
    "accesstoken",
    "token",
    "password",
    "passwd",
    "secret",
    "credential",
    "credentials",
}


def _write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _is_sensitive_key(value):
    normalized = "".join(character for character in value.lower() if character.isalnum())
    return normalized in SENSITIVE_KEYS or normalized.endswith(("apikey", "accesstoken"))


def _redact_mapping(value):
    if isinstance(value, dict):
        return {
            key: REDACTED if _is_sensitive_key(str(key)) else _redact_mapping(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_mapping(item) for item in value]
    return value


def _redact_command(command):
    redacted_command = []
    redact_next_argument = False
    for argument in command:
        if redact_next_argument:
            redacted_command.append(REDACTED)
            redact_next_argument = False
            continue

        if argument.startswith(("-", "/")) and "=" in argument:
            key, _value = argument.split("=", 1)
            if _is_sensitive_key(key.lstrip("-/")):
                redacted_command.append(f"{key}={REDACTED}")
                continue

        redacted_command.append(argument)
        if argument.startswith(("-", "/")) and _is_sensitive_key(
            argument.lstrip("-/")
        ):
            redact_next_argument = True
    return redacted_command


def capture_runtime_environment(environment_id="primary-windows"):
    environment = {
        "environment_id": environment_id,
        "operating_system": platform.platform(),
        "python": platform.python_version(),
        "python_executable": sys.executable,
    }

    try:
        import torch

        environment.update(
            {
                "pytorch": torch.__version__,
                "cuda_runtime": torch.version.cuda,
                "cuda_available": torch.cuda.is_available(),
                "cudnn": torch.backends.cudnn.version(),
            }
        )
        if torch.cuda.is_available():
            environment["gpu"] = torch.cuda.get_device_name(0)
    except ImportError:
        environment["pytorch"] = "not installed"

    return environment


def execute_logged_command(
    base_directory,
    stage,
    command,
    environment,
    *,
    working_directory=None,
    config=None,
):
    if stage not in VALID_STAGES:
        raise ValueError(f"Unsupported stage: {stage}")
    if not command:
        raise ValueError("command must not be empty")

    base_directory = Path(base_directory)
    base_directory.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now().astimezone()
    run_id = uuid.uuid4().hex[:12]
    timestamp = started_at.strftime("%Y%m%d-%H%M%S%z")
    run_directory = base_directory / f"{timestamp}_{stage}_{run_id}"
    run_directory.mkdir(parents=False, exist_ok=False)

    for directory_name in ("metrics", "checkpoints", "data_flow", "selection"):
        (run_directory / directory_name).mkdir()

    normalized_command = [str(argument) for argument in command]
    recorded_command = _redact_command(normalized_command)
    command_text = subprocess.list2cmdline(recorded_command)
    (run_directory / "command.txt").write_text(command_text + "\n", encoding="utf-8")
    _write_json(run_directory / "environment.json", environment)
    _write_json(run_directory / "config.json", _redact_mapping(config or {}))
    _write_json(run_directory / "artifact_manifest.json", {"artifacts": []})

    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "stage": stage,
        "environment_id": environment["environment_id"],
        "working_directory": str(Path(working_directory or os.getcwd()).resolve()),
        "command": recorded_command,
        "started_at": started_at.isoformat(),
        "status": "running",
        "exit_code": None,
    }
    _write_json(run_directory / "manifest.json", manifest)

    monotonic_start = time.monotonic()
    stdout_path = run_directory / "stdout.log"
    stderr_path = run_directory / "stderr.log"
    try:
        child_environment = os.environ.copy()
        child_environment.update(
            {
                "LASRCA_RUN_DIR": str(run_directory.resolve()),
                "LASRCA_STAGE": stage,
            }
        )
        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_file:
            completed_process = subprocess.run(
                normalized_command,
                cwd=working_directory,
                env=child_environment,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                check=False,
            )
        exit_code = completed_process.returncode
    except OSError as error:
        stdout_path.touch(exist_ok=True)
        stderr_path.write_text(f"{type(error).__name__}: {error}\n", encoding="utf-8")
        exit_code = 127

    ended_at = datetime.now().astimezone()
    duration_seconds = time.monotonic() - monotonic_start
    (run_directory / "exit_code.txt").write_text(f"{exit_code}\n", encoding="utf-8")
    _write_json(
        run_directory / "timing.json",
        {
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "duration_seconds": duration_seconds,
        },
    )

    manifest.update(
        {
            "ended_at": ended_at.isoformat(),
            "duration_seconds": duration_seconds,
            "status": "completed" if exit_code == 0 else "failed",
            "exit_code": exit_code,
        }
    )
    _write_json(run_directory / "manifest.json", manifest)
    return run_directory


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="Run one LasRCA stage and preserve its execution evidence."
    )
    parser.add_argument("--stage", required=True, choices=VALID_STAGES)
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "runs" / "lasrca",
    )
    parser.add_argument("--environment-id", default="primary-windows")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv=None):
    arguments = build_argument_parser().parse_args(argv)
    command = arguments.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("A command is required after --")

    run_directory = execute_logged_command(
        base_directory=arguments.runs_dir,
        stage=arguments.stage,
        command=command,
        environment=capture_runtime_environment(arguments.environment_id),
        working_directory=arguments.cwd,
    )
    exit_code = int((run_directory / "exit_code.txt").read_text(encoding="utf-8"))
    print(run_directory)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
