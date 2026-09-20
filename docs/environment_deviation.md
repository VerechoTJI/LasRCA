# LasRCA Environment Deviation

## Decision

All experiments in the current LasRCA workstream use the runnable `primary-windows` environment. The environment documented by the paper and official README remains a reference for interpreting differences; it is not an execution gate.

## Environment comparison

| Component | Paper reference | Primary Windows environment | Reporting consequence |
| --- | --- | --- | --- |
| Operating system | Ubuntu 20.04.6 | Windows 10.0.19045 | Report path, process, and shell differences. |
| Python | 3.10 | 3.12.13 | Preserve the exact lockfile and runtime version for every run. |
| PyTorch | 2.0.1 | 2.11.0+cu128 | Numerical or operator behavior may differ; do not attribute all metric deltas to the model. |
| CUDA runtime | 11.7 | 12.8 | Record runtime, driver, GPU, and deterministic settings. |
| cuDNN | 8 | Provided through the installed PyTorch stack; exact runtime value must be captured by the run wrapper | Do not claim an identical deep-learning stack. |
| GPU | RTX 4090 | NVIDIA GeForce RTX 5070 Ti, 16303 MiB | Measure runtime and peak memory locally instead of copying the paper's hardware expectation. |
| Dependency source | `requirements.txt` versions in the official package | `pyproject.toml` and `uv.lock` | Treat `uv.lock` SHA256 as part of the environment identity. |

## Current identity

- Environment ID: `primary-windows`
- `uv.lock` SHA256: `C42CF6C4CB3A0B03F04B5D870000DECBA6A3A864F87CAF3C6B332A7EC1665069`
- Python: 3.12.13
- PyTorch: 2.11.0+cu128
- CUDA available: true
- CUDA runtime: 12.8
- GPU: NVIDIA GeForce RTX 5070 Ti
- NVIDIA driver: 616.86
- GPU memory: 16303 MiB

## Interpretation rule

Released and locally trained checkpoints must be evaluated with the same primary-windows evaluator when making a local comparison. Paper values remain an external reference. If a result differs from the paper, first check dataset identity, split, seed, checkpoint, metric definition, and implementation. Any residual difference that could be caused by the runtime stack is reported as an environment limitation rather than assigned to a single cause.
