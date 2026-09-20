# LasRCA Paper Faithful Environment Blocker

## Status

`paper-faithful` is blocked and reference-only for the current experiment series. The project owner confirmed that this environment does not run, which is why the Windows port is used.

## Reference environment

- Ubuntu 20.04.6
- Python 3.10
- Docker 19.03.12
- PyTorch 2.0.1
- CUDA 11.7
- cuDNN 8

## Evidence boundary

The exact historical command, failure log, and lowest-level error are not present in the supplied workspace. The blocker is therefore recorded as a project decision supported by the owner's prior execution attempt, not as a newly reproduced failure in this work session.

## Consequence

- Do not spend the first-five-item experiment budget rebuilding this environment.
- Do not block Setup, Evaluation, Classifier, Data flow, or Selection on this environment.
- Do not label primary-windows results as paper-faithful.
- Preserve the paper environment specification in reports so readers can judge comparability.

Revisiting this blocker requires a separate explicit task and must not silently replace the current primary-windows experiment line.
