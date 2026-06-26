# Baseline snapshots

This folder stores small, curated model-output snapshots that are intentionally committed to the repository.

These files are different from `data/outputs/`:

- `data/outputs/` contains normal generated local outputs and is ignored by Git.
- `data/baselines/` contains selected benchmark snapshots for comparison and reproducibility.

## Stable V1 baseline

```text
v1_baseline/
```

The stable V1 workflow uses this baseline through the V1 output-check step:

```bash
python src/run_all.py
python src/check_outputs.py
```

## Active V2 baseline snapshot

```text
v2_baseline_snapshot.json
```

The active V2 workflow uses this snapshot through:

```bash
python src/compare_v2_to_baseline.py
```

The current V2 snapshot covers:

```text
12 candidate sites
site ranking and readiness scores
data-quality counts
profile top sites
electrical expected-case outputs
right-sizing outputs
port-use simulation guardrails
port-sizing scenario guardrails
right-sizing validation guardrails
executive summary guardrails
deliverable-package manifest guardrails
```

The current V2 package expectation is:

```text
Copied files: 35/35
Synced files: 35/35
```

## Manual checks

You can run the V2 baseline comparison through the full workflow:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

You can run the V1 check manually after generating V1 outputs:

```bash
python src/check_outputs.py
```

## Baseline maintenance rule

Only commit a new baseline after reviewing that the model run should become an official benchmark. Generated local outputs under `data/outputs/` should stay ignored unless a file is intentionally promoted into `data/baselines/` or `docs/assets/`.
