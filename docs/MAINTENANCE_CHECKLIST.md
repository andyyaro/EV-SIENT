# Maintenance Checklist

Use this checklist before pushing major repo changes, handing the repo to a reviewer, publishing Tableau updates, or merging V2 work later.

## 1. Pull the active branch

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
```

## 2. Install dependencies

Preferred command:

```bash
make setup
```

Equivalent raw commands:

```bash
pip install -r requirements.txt
pip install -r requirements-gis.txt
```

## 3. Run the active V2 workflow

Preferred commands:

```bash
make run-v2
make check-v2
```

Equivalent raw commands:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Expected checker result:

```text
Status: PASSED
Copied files: 35/35
Synced files: 35/35
```

## 4. Regenerate and validate Tableau exports

The Tableau workbook is the main public-facing visual artifact. After V2 outputs change, regenerate and validate Tableau CSV inputs:

```bash
make tableau-exports
make check-tableau
```

Equivalent raw commands:

```bash
python src/build_tableau_exports.py
python src/check_tableau_exports.py
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

Generated Tableau CSVs live under:

```text
data/outputs/tableau/
```

These generated files are ignored by Git by default. Do not manually edit them; regenerate them from current model outputs.

## 5. Refresh the Tableau workbook when needed

Use this when the model outputs or Tableau export logic have changed:

```text
1. Run make full-v2-tableau.
2. Open tableau/EV_Charging_Site_Readiness_Workbook.twbx.
3. Refresh or repoint data sources if Tableau asks.
4. Verify visible sheet tabs in Tableau Public after publishing.
5. Save the packaged workbook.
6. Commit the workbook only when the visual artifact intentionally changed.
```

Public link and workbook notes are in:

```text
tableau/README.md
```

## 6. Check Markdown links

Preferred command:

```bash
make links
```

Equivalent raw command:

```bash
lychee --verbose --no-progress \
  --accept 200,204,206,301,302,303,307,308 \
  --include-fragments \
  --exclude-path data/outputs \
  --exclude-path data/run_history \
  './**/*.md'
```

Expected result:

```text
0 Errors
```

## 7. Run the short health check

```bash
make health
```

This runs the V2 output checker, Tableau export checker, and Markdown link checker. It assumes current Tableau exports already exist.

## 8. Run the full review check

```bash
make review
```

This runs the V2 workflow, V2 checker, Tableau export generation, Tableau export checker, Markdown link check, and git status.

## 9. Check Git status

```bash
make status
```

Equivalent raw command:

```bash
git status --short
```

Generated files under `data/outputs/` should normally be ignored by Git.

The committed README preview images under `docs/assets/charts/` should only change when you intentionally update the README visuals.

The packaged Tableau workbook under `tableau/` should only change when you intentionally save a workbook update.

## 10. Review the main outputs

Public visual review:

```text
tableau/README.md
tableau/EV_Charging_Site_Readiness_Workbook.twbx
```

Technical package review:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
data/outputs/deliverable_package_v2/charts/v2_port_sizing_scenario_heatmap.png
```

## 11. Do not commit local generated caches

Do not commit local generated/downloaded helper folders unless there is a clear reason.

Examples to avoid:

```text
data/source_extracts/gis/
data/outputs/
data/outputs/tableau/
data/run_history/
```

To remove local generated caches:

```bash
make clean-local
```

## 12. Before changing code structure

Before moving or renaming scripts, check:

```text
src/run_v2.py
src/check_outputs_v2.py
src/build_tableau_exports.py
src/check_tableau_exports.py
.github/workflows/v2-model-check.yml
.github/workflows/link-check.yml
Makefile
tableau/README.md
docs/REPO_MAP.md
src/README.md
README.md
START_HERE.md
```

Moving scripts is more risky than adding navigation docs because imports, GitHub Actions, Tableau refresh steps, and reproducibility commands may depend on existing paths.

## 13. Before merging to main later

Do not merge V2 into `main` until:

```text
V2 model check passes locally
Tableau exports regenerate from current outputs
Tableau export checker passes locally
Markdown link check passes locally
GitHub Actions pass
README images render
Tableau Public workbook tabs are visible
reviewer guide and source index are current
main-vs-V2 branch purpose is intentionally resolved
```
