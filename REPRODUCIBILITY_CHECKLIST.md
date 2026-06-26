# Reproducibility Checklist

Use `START_HERE.md` and `docs/V2_CURRENT_WORKFLOW_GUIDE.md` for the full active V2 run instructions.

Current branch:

```text
v2-expansion-planning
```

Install:

```text
requirements.txt
requirements-gis.txt
```

Run:

```text
python src/run_v2.py
python src/check_outputs_v2.py
```

Expected checker result:

```text
Status: PASSED
```

Expected workflow marker count:

```text
Generated outputs: 36/36
```

Expected deliverable package count:

```text
Copied files: 35/35
Synced files: 35/35
```

The counts differ because the workflow marker tracks `v2_sensitivity_results.csv`, while the clean deliverable package still contains 35 selected review files.
