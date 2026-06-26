# Maintenance Checklist

Use this checklist before pushing major repo changes, handing the repo to a reviewer, or merging V2 work later.

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

## 4. Check Markdown links

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

## 5. Run the short health check

```bash
make health
```

This runs the V2 output checker and Markdown link checker.

## 6. Check Git status

```bash
make status
```

Equivalent raw command:

```bash
git status --short
```

Generated files under `data/outputs/` should normally be ignored by Git.

The committed README preview images under `docs/assets/charts/` should only change when you intentionally update the README visuals.

## 7. Review the main outputs

Open the clean package:

```text
data/outputs/deliverable_package_v2/README.md
```

Then inspect:

```text
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
data/outputs/deliverable_package_v2/charts/v2_port_sizing_scenario_heatmap.png
```

## 8. Do not commit local generated caches

Do not commit local generated/downloaded helper folders unless there is a clear reason.

Examples to avoid:

```text
data/source_extracts/gis/
data/outputs/
data/run_history/
```

To remove local generated caches:

```bash
make clean-local
```

## 9. Before changing code structure

Before moving or renaming scripts, check:

```text
src/run_v2.py
src/check_outputs_v2.py
.github/workflows/v2-model-check.yml
.github/workflows/link-check.yml
Makefile
docs/REPO_MAP.md
src/README.md
README.md
START_HERE.md
```

Moving scripts is more risky than adding navigation docs because imports, GitHub Actions, and reproducibility commands may depend on existing paths.

## 10. Before merging to main later

Do not merge V2 into `main` until:

```text
V2 model check passes locally
Markdown link check passes locally
GitHub Actions pass
README images render
reviewer guide and source index are current
main-vs-V2 branch purpose is intentionally resolved
```
