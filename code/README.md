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

The full historical evaluation sequence is defined in `reproduce.sh`. Redirecting output alone does not satisfy the experiment logging contract because the exact command, exit code, runtime, environment ID, and artifact hashes must be captured together.

Use the logged stage runner for new invocations:

```powershell
.\.venv\Scripts\python.exe -m experiments.run_stage `
  --stage evaluate `
  --runs-dir ..\runs\lasrca `
  --cwd . `
  -- .\.venv\Scripts\python.exe .\tasks\las_rca.py --k 0
```

The runner creates a unique immutable directory and preserves command metadata, stdout, stderr, exit code, timing, runtime environment, and manifest files. Sensitive command and configuration fields such as API keys and tokens are redacted from recorded metadata. It passes the immutable run ID and environment ID to the evaluation process, which writes the following files without overwriting existing output:

- `metrics/per_seed_metrics.json` and `.csv`
- `metrics/summary.json` and `.csv`
- `artifact_manifest.json` with size and SHA256 for every run artifact

Each per-seed row includes AC@1 through AC@5, Avg@5, micro/macro Precision/Recall/F1, checkpoint identity, dataset identity, environment ID, and run ID. Avg@5 is the arithmetic mean of AC@1 through AC@5.

The canonical released one-shot evaluation run is:

```text
../runs/lasrca/20260921-033023+0800_evaluate_3090cfbfad7f/
```

It completed seeds 405–409 with exit code 0. The released checkpoint modification times remained unchanged.

Run-scoped smoke training uses the same wrapper and cannot target the released model directory:

```powershell
.\.venv\Scripts\python.exe -m experiments.run_stage `
  --stage train `
  --runs-dir ..\runs\lasrca `
  --cwd . `
  -- .\.venv\Scripts\python.exe .\tasks\las_rca.py `
     --mode train --k 0 --seed 405 --epochs 1 --track local-smoke
```

Training writes its checkpoint under the immutable run's `checkpoints/` directory and records epoch loss, learning rate, epoch/runtime duration, peak GPU memory, checkpoint SHA256, input hashes, and final metrics under `metrics/`. Existing checkpoint and metrics targets are rejected rather than overwritten.

The verified smoke and reload runs are:

- `../runs/lasrca/20260921-033650+0800_train_2edae6766149/`
- `../runs/lasrca/20260921-033753+0800_evaluate_b1eeb4087cf3/`

The one-epoch smoke loss was finite, and the reloaded checkpoint reproduced every saved localization/classification metric with a maximum absolute difference of zero.

## Existing evidence

- `../out/20260606.log`
- `../out/20260606-1.log`
- `../temp_data/A/selected_samples/selected_samples_k_0.pkl`

Both 2026-06-06 logs reach the final aggregate output without a recorded Traceback, ERROR, or Exception. They are historical baselines, not yet complete reproducible runs under the new logging contract.

## Next implementation boundary

The immutable runner, complete localization metrics, structured per-seed exports, safe `train`/`evaluate` modes, run-scoped checkpoints, training evidence, and dangling-edge regression fix are implemented. The next code increment is safe run-scoped `select` and `trace` modes, followed by the five-seed full training series.
