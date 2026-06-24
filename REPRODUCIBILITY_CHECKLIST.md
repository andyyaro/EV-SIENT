# Reproducibility Checklist

Use this checklist to reproduce the current model outputs from a clean local run.

## 1. Start from the repository root

```bash
pwd
```

You should be inside the project folder:

```text
Future-City-Fellowship-
```

## 2. Get the latest version

```bash
git pull --rebase origin main
```

## 3. Create and activate a virtual environment

macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Run the full workflow

```bash
python src/run_all.py
```

Expected success signs:

```text
Sanity check: PASSED
Baseline comparison: COMPLETED
Result: PASSED
```

The output summary should show `OK` for the main generated files.

## 6. Build the deliverable package

```bash
python src/build_deliverable_package.py
```

Expected success signs:

```text
Missing files: 0
Done. The deliverable package is ready to review or share.
```

## 7. Check local Git status

```bash
git status --short
```

It is normal for generated files under [data/outputs/](data/outputs/) to be ignored by Git.

## 8. Open the key outputs

Open these files first:

1. [data/outputs/model_run_summary.md](data/outputs/model_run_summary.md)
2. [data/outputs/results_interpretation.md](data/outputs/results_interpretation.md)
3. [data/outputs/action_matrix.md](data/outputs/action_matrix.md)
4. [data/outputs/site_results.csv](data/outputs/site_results.csv)
5. [data/outputs/charts/readiness_score_chart.png](data/outputs/charts/readiness_score_chart.png)
6. [data/outputs/charts/data_confidence_chart.png](data/outputs/charts/data_confidence_chart.png)
7. [data/outputs/charts/profile_rank_stability_chart.png](data/outputs/charts/profile_rank_stability_chart.png)
8. [data/outputs/charts/site_readiness_map.png](data/outputs/charts/site_readiness_map.png)

## 9. Confirm the main result

The current expected top site is:

```text
FFX002 — City of Fairfax Regional Library
```

Expected ranking:

```text
1. FFX002
2. FFX001
3. PWC002
4. PWC004
5. PWC001
6. PWC003
```

## 10. Confirm the checker output

The checker should confirm:

```text
ERROR: 0
Sanity check: PASSED
```

Remaining `REVIEW` items are expected because some electrical, capacity, emergency-disconnect, access, and stakeholder fields still need confirmation.

## 11. Confirm the deliverable package

The package should be created at [data/outputs/deliverable_package/](data/outputs/deliverable_package/).

The package should include:

- [reports/START_HERE.md](data/outputs/deliverable_package/reports/START_HERE.md)
- [reports/REPRODUCIBILITY_CHECKLIST.md](data/outputs/deliverable_package/reports/REPRODUCIBILITY_CHECKLIST.md)
- [reports/REPO_MAP.md](data/outputs/deliverable_package/reports/REPO_MAP.md)
- [run_outputs/model_run_summary.md](data/outputs/deliverable_package/run_outputs/model_run_summary.md)
- [run_outputs/results_interpretation.md](data/outputs/deliverable_package/run_outputs/results_interpretation.md)
- [run_outputs/action_matrix.md](data/outputs/deliverable_package/run_outputs/action_matrix.md)
- [charts/readiness_score_chart.png](data/outputs/deliverable_package/charts/readiness_score_chart.png)
- [charts/data_confidence_chart.png](data/outputs/deliverable_package/charts/data_confidence_chart.png)
- [charts/profile_rank_stability_chart.png](data/outputs/deliverable_package/charts/profile_rank_stability_chart.png)
- [charts/site_readiness_map.png](data/outputs/deliverable_package/charts/site_readiness_map.png)

## 12. What not to edit manually

Do not manually edit generated outputs:

- [data/outputs/](data/outputs/)
- [data/outputs/charts/](data/outputs/charts/)
- [data/outputs/deliverable_package/](data/outputs/deliverable_package/)

Regenerate them with:

```bash
python src/run_all.py
python src/build_deliverable_package.py
```

## Simple one-command version

After the virtual environment and dependencies are ready, use:

```bash
git pull --rebase origin main && \
python src/run_all.py && \
python src/build_deliverable_package.py && \
git status --short
```
