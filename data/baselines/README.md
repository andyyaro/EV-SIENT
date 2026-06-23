# Baseline snapshots

This folder stores small, curated model-output snapshots that are intentionally committed to the repository.

These files are different from `data/outputs/`:

- `data/outputs/` contains normal generated local outputs and is ignored by Git.
- `data/baselines/` contains selected benchmark snapshots for comparison and reproducibility.

The first baseline is:

```text
v1_baseline/
```

The main workflow uses this baseline automatically through the combined output-check step:

```bash
python src/run_all.py
```

You can also run the combined output check manually after generating outputs:

```bash
python src/check_outputs.py
```

To create a future baseline intentionally:

```bash
python src/run_all.py
python src/create_baseline_snapshot.py --label v2_baseline
```

Only commit a new baseline after reviewing that the model run should become an official benchmark.
