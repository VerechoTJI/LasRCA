# LasRCA Working Reproduction Environment

This directory contains the runnable Windows port used for the current LasRCA reproduction work. It is intentionally treated as a compatibility reproduction environment, not as the paper-faithful Ubuntu environment.

## Verified environment

- Operating system: Windows 10.0.19045
- Python: 3.12.13
- PyTorch: 2.11.0+cu128
- CUDA runtime reported by PyTorch: 12.8
- GPU: NVIDIA GeForce RTX 5070 Ti, 16303 MiB
- NVIDIA driver: 616.86
- NumPy: 1.26.4
- pandas: 2.3.3
- scikit-learn: 1.9.0
- Dependency lock: `uv.lock`

The paper/official README environment is Ubuntu 20.04.6, Python 3.10, PyTorch 2.0.1, CUDA 11.7, and cuDNN 8. That environment is currently blocked and is not a prerequisite for this experiment series. See `../docs/environment_deviation.md` and `../docs/paper_faithful_blocker.md`.

## Current entry points

The existing `reproduce.sh` runs all released-checkpoint evaluation strategies. The present `tasks/las_rca.py` main block runs `final_test()` for seeds 405–409; classifier training is not currently selected by the entry point.

From PowerShell, the current k=0 evaluation entry point is:

```powershell
.\.venv\Scripts\python.exe .\tasks\las_rca.py --k 0
```

The full historical evaluation sequence is defined in `reproduce.sh`. Until the new run wrapper is implemented, redirecting output alone does not satisfy the experiment logging contract because the exact command, exit code, runtime, environment ID, and artifact hashes are not captured together.

Use the logged stage runner for new invocations:

```powershell
.\.venv\Scripts\python.exe -m experiments.run_stage `
  --stage evaluate `
  --runs-dir ..\runs\lasrca `
  --cwd . `
  -- .\.venv\Scripts\python.exe .\tasks\las_rca.py --k 0
```

The runner creates a unique immutable directory and preserves command metadata, stdout, stderr, exit code, timing, runtime environment, and manifest files. Sensitive command and configuration fields such as API keys and tokens are redacted from recorded metadata.

## Existing evidence

- `../out/20260606.log`
- `../out/20260606-1.log`
- `../temp_data/A/selected_samples/selected_samples_k_0.pkl`

Both 2026-06-06 logs reach the final aggregate output without a recorded Traceback, ERROR, or Exception. They are historical baselines, not yet complete reproducible runs under the new logging contract.

## Next implementation boundary

Code changes after the baseline commit will be split into small verified increments:

1. Add explicit `train`, `evaluate`, `select`, and `trace` modes without changing default evaluation results.
2. Add immutable run directories and structured logging described in `../docs/logging_contract.md`.
3. Add metric tests and structured per-seed exports.
4. Reproduce and fix the selection dangling-edge bug with a failing test first.
5. Run seed 405 smoke training before starting the five-seed full training series.
