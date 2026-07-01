# Reproducibility Checklist

This checklist explains how to reproduce the active V2 Future City Fellowship EV charging site-readiness and right-sizing workflow locally from a fresh laptop or a fresh clone.

It covers both:

```text
macOS Terminal
Windows PowerShell
```

Use this checklist when you want to confirm that the repository can be cloned, installed, run, checked, and reviewed from the terminal.

For project context, also read:

```text
START_HERE.md
docs/ACTIVE_DOCS_INDEX.md
docs/V2_CURRENT_WORKFLOW_GUIDE.md
docs/REPO_MAP.md
src/README.md
tableau/README.md
```

---

## 1. Target branch

The active V2 workflow lives on:

```text
v2-expansion-planning
```

Branch meaning:

```text
main = stable V1 baseline workflow
v2-expansion-planning = active V2 prototype workflow
```

The steps below assume you are reproducing the active V2 workflow.

---

## 2. Required tools

You need:

```text
Git
GitHub CLI
Python 3.10 or newer
pip
```

Python 3.11 is recommended.

Optional but useful:

```text
make
lychee
Tableau Desktop or Tableau Public
```

`make` is convenient on macOS and Git Bash, but the raw Python commands are provided so the project can also be reproduced from Windows PowerShell.

---

## 3. Check installed tools

### macOS Terminal

```bash
git --version
gh --version
python3 --version
pip3 --version
```

Optional:

```bash
make --version
```

### Windows PowerShell

```powershell
git --version
gh --version
py --version
python --version
pip --version
```

On Windows, either `py` or `python` may work depending on how Python was installed.

If `py --version` works, use `py -3` in the Windows commands below.

If `python --version` works, you may use `python` instead.

---

## 4. Sign in to GitHub from the terminal

This repository is private, so the terminal must be authenticated before cloning or pulling.

This command is the same on macOS and Windows:

```bash
gh auth login
```

Recommended choices:

```text
GitHub.com
HTTPS
Authenticate Git with your GitHub credentials: Yes
Login with a web browser
```

GitHub CLI will show a one-time code. Copy the code, press Enter, and complete the browser login.

Verify login:

```bash
gh auth status
```

A healthy result should show that you are logged in and that Git operations are configured.

Do not paste personal access tokens, passwords, API keys, or credentials into project files.

---

## 5. Clone the repository

### macOS Terminal

Choose a working folder:

```bash
cd ~/Documents
```

Clone the repository:

```bash
git clone https://github.com/andyyaro/Future-City-Fellowship-.git
```

Enter the repo:

```bash
cd Future-City-Fellowship-
```

### Windows PowerShell

Choose a working folder:

```powershell
cd "$HOME\Documents"
```

Clone the repository:

```powershell
git clone https://github.com/andyyaro/Future-City-Fellowship-.git
```

Enter the repo:

```powershell
cd Future-City-Fellowship-
```

### Confirm the remote

macOS Terminal or Windows PowerShell:

```bash
git remote -v
```

Expected remote:

```text
https://github.com/andyyaro/Future-City-Fellowship-.git
```

---

## 6. Switch to the active V2 branch

macOS Terminal or Windows PowerShell:

```bash
git fetch origin
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
```

Confirm the branch:

```bash
git branch --show-current
```

Expected output:

```text
v2-expansion-planning
```

Confirm the repo is clean:

```bash
git status --short
```

A clean repo shows no output.

---

## 7. Create a virtual environment

### macOS Terminal

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Confirm the virtual environment is active:

```bash
which python
python --version
```

The path should include `.venv`.

### Windows PowerShell

Create the virtual environment:

```powershell
py -3 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Confirm the virtual environment is active:

```powershell
where python
python --version
```

The path should include `.venv`.

---

## 8. Install dependencies

The core model dependencies are in:

```text
requirements.txt
```

Optional GIS/map dependencies are in:

```text
requirements-gis.txt
```

Optional public-data upgrade dependencies are in:

```text
requirements-v2.txt
```

For normal V2 reproduction, install core and GIS dependencies.

### macOS Terminal

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-gis.txt
```

Optional V2 public-data helper dependencies:

```bash
python -m pip install -r requirements-v2.txt
```

### Windows PowerShell

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-gis.txt
```

Optional V2 public-data helper dependencies:

```powershell
python -m pip install -r requirements-v2.txt
```

---

## 9. Run the full active V2 workflow

The raw Python commands work on both macOS and Windows.

### macOS Terminal

```bash
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

### Windows PowerShell

```powershell
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

This sequence runs the model, checks outputs, regenerates Tableau-ready CSV files, and validates the Tableau export folder.

---

## 10. Optional Makefile commands

The Makefile is convenient on macOS and on Windows if using Git Bash or another Unix-like shell.

### macOS Terminal

Full model and Tableau reproduction:

```bash
make full-v2-tableau
```

Full review:

```bash
make review
```

Show Git status:

```bash
make status
```

### Windows Git Bash

If you are using Git Bash and `make` is installed:

```bash
make full-v2-tableau
make review
make status
```

### Windows PowerShell

Use the raw Python commands instead of `make`:

```powershell
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
git status --short
```

This avoids Windows shell differences with commands such as `rm`, `mkdir`, and `find`.

---

## 11. Expected successful model output

A healthy V2 model check should include:

```text
V2 OUTPUT CHECK
---------------
Status: PASSED
```

Expected workflow marker count:

```text
Generated outputs: 36/36
```

Expected deliverable package result:

```text
Copied files: 35/35
Synced files: 35/35
```

The counts differ because the workflow marker tracks `v2_sensitivity_results.csv`, while the clean deliverable package contains 35 selected review files.

---

## 12. Expected successful Tableau export output

A healthy Tableau export check should include:

```text
TABLEAU EXPORT CHECK
--------------------
Status: PASSED
Checked exports: 15/15
Candidate sites represented: 12/12
Exact export set, required columns, row counts, numeric fields, and site coverage are valid.
```

Tableau-ready CSV outputs are generated under:

```text
data/outputs/tableau/
```

The local packaged Tableau workbook is:

```text
tableau/EV_Charging_Site_Readiness_Workbook.twbx
```

The Tableau workflow is documented in:

```text
tableau/README.md
```

---

## 13. Main outputs to inspect after reproduction

After a successful run, inspect these outputs first:

```text
data/outputs/v2_executive_site_summary.csv
data/outputs/v2_run_summary.md
data/outputs/v2_interpretation_report.md
data/outputs/v2_right_sizing_validation_report.md
data/outputs/v2_port_sizing_scenario_report.md
data/outputs/v2_workflow_completion_manifest.json
```

The clean technical review package is:

```text
data/outputs/deliverable_package_v2/
```

Important package files include:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/tables/v2_executive_site_summary.csv
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
data/outputs/deliverable_package_v2/tables/v2_port_sizing_scenario_summary.csv
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
data/outputs/deliverable_package_v2/charts/v2_port_sizing_scenario_heatmap.png
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
```

---

## 14. Main V2 input files

The active V2 candidate-site dataset is:

```text
data/inputs/real_sites_v2.csv
```

The active port-sizing scenario assumptions file is:

```text
data/inputs/v2_port_sizing_scenarios.csv
```

Other assumption and metadata files are documented in:

```text
docs/DATA_SOURCES.md
docs/DATA_DICTIONARY.md
data/dataset_metadata.csv
data/source_dataset_log.csv
```

---

## 15. Optional clean rebuild

### macOS Terminal

If using Make:

```bash
make clean-local
make full-v2-tableau
```

If not using Make:

```bash
rm -rf data/source_extracts/gis/
rm -rf data/run_history/
find . -type d -name __pycache__ -prune -exec rm -rf {} +
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

### Windows PowerShell

Remove local generated caches:

```powershell
if (Test-Path data/source_extracts/gis) { Remove-Item -Recurse -Force data/source_extracts/gis }
if (Test-Path data/run_history) { Remove-Item -Recurse -Force data/run_history }
Get-ChildItem -Path . -Directory -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
```

Then rerun:

```powershell
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

Always check repo status before deleting or committing anything:

```bash
git status --short
```

---

## 16. Optional Markdown link check

The link checker uses `lychee`.

### macOS Terminal or Git Bash

If `lychee` is installed:

```bash
make links
```

Or run directly:

```bash
lychee --verbose --no-progress \
  --accept 200,204,206,301,302,303,307,308 \
  --include-fragments \
  --exclude-path data/outputs \
  --exclude-path data/run_history \
  './**/*.md'
```

### Windows PowerShell

If `lychee` is installed, use:

```powershell
lychee --verbose --no-progress --accept 200,204,206,301,302,303,307,308 --include-fragments --exclude-path data/outputs --exclude-path data/run_history "./**/*.md"
```

If `lychee` is not installed, skip this step for local model reproduction. The model and Tableau output checks are the required technical reproduction checks.

---

## 17. Troubleshooting

### Problem: `gh` command not found

Install GitHub CLI, close and reopen the terminal, then check:

```bash
gh --version
```

Then sign in:

```bash
gh auth login
```

### Problem: clone fails with authentication error

Check login:

```bash
gh auth status
```

Then rerun:

```bash
gh auth login
```

Make sure your GitHub account has access to the private repository.

### Problem: wrong branch

Check:

```bash
git branch --show-current
```

Switch back to V2:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
```

### Problem: PowerShell blocks virtual environment activation

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Problem: dependencies fail to install

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Then reinstall:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-gis.txt
```

### Problem: `make` command not found

Use the raw Python commands instead:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

### Problem: output checker fails

Run the model again from the repository root:

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

Read the checker output carefully. It usually identifies the missing file, missing column, row-count issue, or package-sync issue.

### Problem: Tableau export checker fails

Regenerate Tableau exports:

```bash
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

### Problem: repo has unexpected modified files after running

Check:

```bash
git status --short
```

Review file-level changes:

```bash
git diff --stat
```

To discard accidental local edits to a tracked file, use caution:

```bash
git restore path/to/file
```

Do not run broad restore commands unless you are certain you want to discard local work.

---

## 18. Final reproducibility pass

A complete local reproduction should end with the following checks.

### macOS Terminal

```bash
git branch --show-current
git status --short
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
git status --short
```

### Windows PowerShell

```powershell
git branch --show-current
git status --short
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
git status --short
```

Expected branch:

```text
v2-expansion-planning
```

Expected model result:

```text
V2 OUTPUT CHECK
Status: PASSED
```

Expected Tableau result:

```text
TABLEAU EXPORT CHECK
Status: PASSED
Checked exports: 15/15
Candidate sites represented: 12/12
```

Expected package result:

```text
Copied files: 35/35
Synced files: 35/35
```

If `git status --short` shows changes after the run, review them before committing. Do not commit generated files unless the project intentionally requires those output changes to be versioned.

---

## 19. Public visual artifact

The main public-facing visual artifact is the Tableau workbook documented in:

```text
tableau/README.md
```

Static PNG charts remain reproducibility and technical package outputs. Tableau is the main public visual layer.

Use the local packaged workbook here:

```text
tableau/EV_Charging_Site_Readiness_Workbook.twbx
```

and the generated Tableau CSV inputs here:

```text
data/outputs/tableau/
```

---

## 20. Reproducibility summary

A successful local reproduction means:

```text
GitHub authentication works
The private repository clones successfully
The v2-expansion-planning branch is checked out
Python dependencies install in a virtual environment
The V2 model workflow runs successfully
The V2 output checker passes
The Tableau export builder runs successfully
The Tableau export checker passes
The deliverable package is generated and synced
The main review outputs can be opened locally
```

This confirms that the active V2 prototype can be reproduced locally from the repository on either macOS or Windows.
