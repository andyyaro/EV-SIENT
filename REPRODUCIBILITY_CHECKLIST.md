# Reproducibility Checklist

Use this checklist to reproduce the current model outputs from a clean local run.

This guide is written for someone who may be using GitHub for the first time.

## 0. One-time computer setup

Before cloning the repository, make sure these tools are installed:

```text
Git
GitHub CLI, also called gh
Python 3
```

Check whether they are already installed:

macOS, Linux, or Windows terminal:

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

## 1. Choose where the repository should live

Move into the folder where you want to keep the project.

Example for macOS or Linux:

```bash
mkdir -p ~/Documents/GitHub
cd ~/Documents/GitHub
```

Example for Windows PowerShell:

```powershell
mkdir "$HOME\Documents\GitHub"
cd "$HOME\Documents\GitHub"
```

You can choose a different folder. The important thing is to `cd` into the folder **before** cloning.

## 2. Clone the repository

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

## 3. Confirm you are in the repository root

Run:

```bash
pwd
ls
```

You should be inside the project folder:

```text
Future-City-Fellowship-
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

If you do not see those files, you are probably in the wrong folder. Use `cd` to move into the `Future-City-Fellowship-` folder.

## 4. Choose the version to reproduce

To reproduce the frozen V1 review-ready checkpoint exactly, use the tag:

```bash
git checkout v1-review-ready
```

To work from the latest version of `main`, use:

```bash
git switch main
git pull --rebase origin main
```

For normal development, use `main`. For exact V1 review reproduction, use `v1-review-ready`.

## 5. Get the latest version if you are on main

If you are working on `main`, run:

```bash
git pull --rebase origin main
```

If you checked out the frozen `v1-review-ready` tag, skip this step.

## 6. Create and activate a virtual environment

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

## 7. Install dependencies

```bash
pip install -r requirements.txt
```

## 8. Run the full workflow

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

## 9. Build the deliverable package

```bash
python src/build_deliverable_package.py
```

Expected success signs:

```text
Missing files: 0
Done. The deliverable package is ready to review or share.
```

For the V1 review-ready checkpoint, the package should copy 40 files.

## 10. Check local Git status

```bash
git status --short
```

It is normal for generated files under [data/outputs/](data/outputs/) to be ignored by Git.

If the output is empty, there are no uncommitted tracked changes.

## 11. Open the key outputs

Open these files first:

1. [data/outputs/model_run_summary.md](data/outputs/model_run_summary.md)
2. [data/outputs/results_interpretation.md](data/outputs/results_interpretation.md)
3. [data/outputs/action_matrix.md](data/outputs/action_matrix.md)
4. [data/outputs/site_results.csv](data/outputs/site_results.csv)
5. [data/outputs/charts/readiness_score_chart.png](data/outputs/charts/readiness_score_chart.png)
6. [data/outputs/charts/data_confidence_chart.png](data/outputs/charts/data_confidence_chart.png)
7. [data/outputs/charts/profile_rank_stability_chart.png](data/outputs/charts/profile_rank_stability_chart.png)
8. [data/outputs/charts/site_readiness_map.png](data/outputs/charts/site_readiness_map.png)

## 12. Confirm the main result

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

## 13. Confirm the checker output

The checker should confirm:

```text
ERROR: 0
Sanity check: PASSED
```

Remaining `REVIEW` items are expected because some electrical, capacity, emergency-disconnect, access, and stakeholder fields still need confirmation.

## 14. Confirm the deliverable package

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
- [stakeholder_inputs/stakeholder_contact_targets.csv](data/outputs/deliverable_package/stakeholder_inputs/stakeholder_contact_targets.csv)

## 15. What not to edit manually

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

After the repository is cloned, the virtual environment is active, and dependencies are installed, use:

```bash
git pull --rebase origin main && \
python src/run_all.py && \
python src/build_deliverable_package.py && \
git status --short
```

If you are reproducing the frozen V1 tag instead of `main`, do not run `git pull --rebase origin main` after checking out the tag.
