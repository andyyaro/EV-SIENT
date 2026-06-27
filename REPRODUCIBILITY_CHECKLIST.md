# Reproducibility Checklist

Use `START_HERE.md`, `docs/V2_CURRENT_WORKFLOW_GUIDE.md`, and `tableau/README.md` for the full active V2 run and Tableau refresh instructions.

Current branch:

```text
v2-expansion-planning
```

Install:

```text
requirements.txt
requirements-gis.txt
```

Run the active V2 model workflow:

```text
python src/run_v2.py
python src/check_outputs_v2.py
```

Equivalent Makefile command:

```text
make full-v2
```

Regenerate and validate Tableau-ready CSV inputs after the model outputs exist:

```text
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

Equivalent Makefile command:

```text
make full-v2-tableau
```

Tableau-only refresh/check commands:

```text
make tableau-exports
make check-tableau
```

Full review command:

```text
make review
```

Expected model checker result:

```text
Status: PASSED
```

Expected Tableau checker result:

```text
TABLEAU EXPORT CHECK
--------------------
Status: PASSED
Checked exports: 15/15
Candidate sites represented: 12/12
Exact export set, required columns, row counts, numeric fields, and site coverage are valid.
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

The counts differ because the workflow marker tracks `v2_sensitivity_results.csv`, while the clean deliverable package contains 35 selected review files.

## Public visual artifact

The main public-facing visual artifact is the Tableau workbook documented in:

```text
tableau/README.md
```

Static PNG charts remain reproducibility and technical package outputs. Tableau is the main public visual layer.
