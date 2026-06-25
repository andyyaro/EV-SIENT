# Reproducibility Checklist

Use this checklist to reproduce the current model outputs from a clean local run.

This guide is written for someone who may be using GitHub for the first time.

## Current recommendation

For active Phase 2 work, reproduce the V2 workflow on:

```text
v2-expansion-planning
```

The main V2 guide is:

```text
docs/V2_CURRENT_WORKFLOW_GUIDE.md
```

Use `main` only when reproducing the stable V1 workflow.

## 0. One-time computer setup

Before cloning the repository, make sure these tools are installed:

```text
Git
GitHub CLI, also called gh
Python 3.10 or newer
```

Python 3.11 is the tested version used by the GitHub Actions workflow. Python 3.10+ is recommended because the scripts use modern Python type syntax.

Check whether they are already installed:

```bash
git --version
gh --version
python --version
```

On some macOS or Linux machines, Python may be called `python3` instead of `python`:

```bash
python3 --version
```

If `gh` is installed but not signed in, sign in once:

```bash
gh auth login
```

Recommended choices for a beginner:

```text
GitHub.com
HTTPS
Login with a web browser
```

## 1. Clone the repository

Recommended method using GitHub CLI:

```bash
gh repo clone andyyaro/Future-City-Fellowship-
```

Alternative method using regular Git:

```bash
git clone https://github.com/andyyaro/Future-City-Fellowship-.git
```

Then enter the repository folder:

```bash
cd Future-City-Fellowship-
```

## 2. Confirm you are in the repository root

Run:

```bash
pwd
ls
```

You should see files and folders such as:

```text
START_HERE.md
REPRODUCIBILITY_CHECKLIST.md
requirements.txt
src
data
docs
```

## 3. Create and activate a virtual environment

macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

If your computer uses `python3` instead of `python`, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

After activation, your terminal prompt may show:

```text
(.venv)
```

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Reproduce the active V2 workflow

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
python src/run_v2.py
python src/check_outputs_v2.py
```

Expected success signs:

```text
V2 workflow complete.
V2 OUTPUT CHECK
Status: PASSED
All expected V2 outputs are present and all 12 V2 candidate sites are represented in the main output tables.
```

The deliverable package step should show:

```text
Status: complete
Clean rebuild: True
Copied files: 28/28
```

## 6. Open the key V2 outputs

Open these files first:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/tables/v2_executive_site_summary.csv
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
```

Then review the main charts:

```text
data/outputs/deliverable_package_v2/charts/v2_polished_readiness_score_chart.png
data/outputs/deliverable_package_v2/charts/v2_site_readiness_map.png
data/outputs/deliverable_package_v2/charts/v2_profile_rank_stability_chart.png
data/outputs/deliverable_package_v2/charts/v2_port_utilization_simulation.png
```

## 7. Confirm the current V2 result

The current expected top site is:

```text
FFX002 — City of Fairfax Regional Library
```

Current V2 expected ranking:

```text
1. FFX002
2. FFX004
3. PWC006
4. FFX001
5. PWC002
6. PWC007
7. PWC004
8. FFX003
9. PWC008
10. PWC001
11. PWC005
12. PWC003
```

## 8. Confirm the V2 checker output

The checker should confirm:

```text
Status: PASSED
```

Remaining `REVIEW` items are expected because some electrical, capacity, emergency-disconnect, access, operating-hours, parking, and stakeholder fields still need confirmation.

## 9. Confirm the V2 deliverable package

The package should be created at:

```text
data/outputs/deliverable_package_v2/
```

The package should include:

```text
README.md
package_manifest.json
reports/
tables/
charts/
manifests/
```

The package is rebuilt cleanly by default so stale copied files do not remain.

## 10. Check local Git status

```bash
git status --short
```

It is normal for generated files under `data/outputs/` to be ignored by Git.

If the output is empty, there are no uncommitted tracked changes.

## 11. Stable V1 reproduction

To reproduce the stable V1 workflow on `main`:

```bash
git switch main
git pull --rebase origin main
python src/run_all.py
python src/build_deliverable_package.py
git status --short
```

A successful V1 run should show signs like:

```text
Sanity check: PASSED
Baseline comparison: COMPLETED
Missing files: 0
```

## 12. Optional: run demo mode

Demo mode stress-tests the workflow with synthetic larger candidate pools.

```bash
python src/run_demo.py --count 50 --seed 42 --top-n 15 --clean
```

Demo outputs are local-only and ignored by Git under `data/demo/`.

## 13. What not to edit manually

Do not manually edit generated outputs:

```text
data/outputs/
data/outputs/charts/
data/outputs/deliverable_package/
data/outputs/deliverable_package_v2/
data/demo/
```

Regenerate V2 outputs with:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Regenerate V1 outputs with:

```bash
python src/run_all.py
python src/build_deliverable_package.py
```
