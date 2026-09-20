# LasRCA Experiment Logging Contract

## Purpose

Every experiment must be independently auditable. A console log is not sufficient unless it is tied to the exact code, environment, inputs, checkpoint, command, timing, and exit state that produced it.

## Run directory

Each invocation writes to a new immutable directory:

```text
runs/lasrca/<timestamp>_<stage>_<run-id>/
  manifest.json
  command.txt
  exit_code.txt
  timing.json
  environment.json
  stdout.log
  stderr.log
  config.json
  artifact_manifest.json
  metrics/
  checkpoints/
  data_flow/
  selection/
```

The runner must fail instead of overwriting an existing run directory.

## Required manifest fields

`manifest.json` must contain:

- schema version and run ID
- stage: `train`, `evaluate`, `select`, or `trace`
- environment ID, fixed to `primary-windows` for this workstream
- start and end timestamps with timezone
- wall-clock duration in seconds
- complete argument vector and working directory
- process exit code and completion status
- Git HEAD, dirty flag, and source diff or source snapshot checksum
- Python, PyTorch, CUDA runtime, cuDNN, GPU, driver, and package-lock identity
- dataset, embedding, released-model, input-checkpoint, and output-checkpoint SHA256 values
- seed, dataset split, labeling strategy, k value, and relevant hyperparameters

## Metrics output

Evaluation writes one machine-readable record per environment, strategy, seed, and entity type. Required fields are:

- run ID and checkpoint SHA256
- dataset and split
- strategy, seed, k, and entity type
- sample count
- AC@1, AC@2, AC@3, AC@4, AC@5, and Avg@5
- micro and macro Precision, Recall, and F1
- metric-definition version

Aggregate output contains mean, population or sample standard deviation with the convention stated, number of seeds, paper value when reported, absolute delta, relative delta, and paper evidence locator.

## Training output

Training additionally records epoch-level total, labeled, and iterative-label loss; learning rate; checkpoint path and SHA256; peak GPU memory; final evaluation metrics; and whether deterministic algorithms were requested and achieved.

## Selection output

Selection records the five input checkpoint hashes, ranking policy, tie policy, entropy or confusion score, budget unit, alpha, selected case count, selected entity count, subgraph count, maximum entities per subgraph, dangling-edge count, and output artifact SHA256.

## Failure behavior

On failure, the runner still writes the command, environment, start/end time, exit code, stdout, stderr, and a concise failure record. A failed run is never presented as missing evidence and never overwrites a successful run.

## Logging safety

Logs must not contain API keys, access tokens, credentials, or complete environment-variable dumps. Paths may be recorded, but user secrets and unrelated host information must be excluded.
