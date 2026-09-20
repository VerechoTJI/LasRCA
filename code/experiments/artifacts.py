import hashlib
from pathlib import Path


def sha256_file(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_artifacts(root_directory, excluded_names=()):
    root_directory = Path(root_directory)
    excluded_names = set(excluded_names)
    artifacts = []
    for path in sorted(root_directory.rglob("*")):
        if not path.is_file() or path.name in excluded_names:
            continue
        artifacts.append(
            {
                "path": path.relative_to(root_directory).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return artifacts
