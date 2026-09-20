import os
from pathlib import Path


def checkpoint_path(directory, *, seed, k, labeling_strategy):
    suffix = f"_k_{k}_{labeling_strategy}" if k != 0 else f"_k_{k}"
    return Path(directory) / f"model_seed_{seed}{suffix}.pkl"


def _same_path(first, second):
    first = os.path.normcase(str(Path(first).resolve()))
    second = os.path.normcase(str(Path(second).resolve()))
    return first == second


def resolve_checkpoint_directory(
    mode, released_directory, explicit_directory, environment
):
    released_directory = Path(released_directory)
    if mode == "evaluate":
        return Path(explicit_directory) if explicit_directory else released_directory
    if mode != "train":
        raise ValueError(f"unsupported checkpoint mode: {mode}")

    if explicit_directory:
        target_directory = Path(explicit_directory)
    else:
        run_directory = environment.get("LASRCA_RUN_DIR")
        if not run_directory:
            raise ValueError(
                "training requires a run-scoped checkpoint directory; use the "
                "stage runner or --checkpoint_dir"
            )
        target_directory = Path(run_directory) / "checkpoints"

    if _same_path(target_directory, released_directory):
        raise ValueError("training cannot write into the released checkpoint directory")
    return target_directory


def ensure_checkpoint_target_available(path):
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite checkpoint: {path}")
    return path
