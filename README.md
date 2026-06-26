# EV Charger Site-Readiness and Right-Sizing Prototype

![Model Pipeline Check](https://github.com/andyyaro/Future-City-Fellowship-/actions/workflows/model-check.yml/badge.svg)

This repository contains a Python planning-support prototype for comparing public EV charging candidate sites in Fairfax City and Prince William County.

The model evaluates sites using demand, implementation feasibility, site review, equity, data confidence, electrical-risk screening, right-sizing, port-use simulation, and action recommendations. It supports early planning only; it is not a construction, procurement, utility approval, permitting, or final design tool.

## Current active branch

This branch is currently used for V2 expansion-planning work.

```text
v2-expansion-planning
```

Use:

```text
main = stable V1 baseline workflow
v2-expansion-planning = active V2 prototype workflow
```

## Start here

- Current V2 workflow guide: [docs/V2_CURRENT_WORKFLOW_GUIDE.md](docs/V2_CURRENT_WORKFLOW_GUIDE.md)
- Shortest reproduction guide: [START_HERE.md](START_HERE.md)
- Step-by-step reproduction checklist: [REPRODUCIBILITY_CHECKLIST.md](REPRODUCIBILITY_CHECKLIST.md)
- Simple repo map: [docs/REPO_MAP.md](docs/REPO_MAP.md)
- Project status: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)

## Python version

Use Python 3.10 or newer. Python 3.11 is the tested version used by the GitHub Actions workflow.

## V2 quick run

From the repository root on `v2-expansion-planning`:

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
python src/run_v2.py
python src/check_outputs_v2.py
```

A successful V2 run should end with:

```text
V2 OUTPUT CHECK
Status: PASSED
All expected V2 outputs are present, all 12 V2 candidate sites are represented, and the deliverable package is hash-synced with current source outputs.
```

## Stable V1 quick run

From the repository root on `main`:

```bash
git switch main
git pull --rebase origin main
python src/run_all.py
python src/build_deliverable_package.py
git status --short
```

## Current V2 workflow

`src/run_v2.py` runs the full active workflow:

```text
site-readiness model
action matrix
data validation
sensitivity analysis
scoring-profile analysis
charts and readiness map
electrical-risk scenario analysis
right-sizing scenario analysis
port-use simulation
right-sizing validation
executive site summary
GIS decision maps for report and README use
interpretation report
run summary
baseline comparison
workflow manifest
deliverable package
```

## Main V2 outputs to review

Start with the V2 deliverable package:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/tables/v2_executive_site_summary.csv
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
data/outputs/deliverable_package_v2/charts/v2_site_decision_map_readme.png
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_run_summary.md
```

Important direct outputs:

```text
data/outputs/v2_site_results.csv
data/outputs/v2_right_sizing_scenarios.csv
data/outputs/v2_port_utilization_simulation.csv
data/outputs/v2_right_sizing_validation.csv
data/outputs/v2_executive_site_summary.csv
data/outputs/v2_baseline_comparison.md
data/outputs/v2_workflow_success.json
```

Important V2 charts generated locally:

```text
data/outputs/charts/v2_polished_readiness_score_chart.png
data/outputs/charts/v2_data_confidence_chart.png
data/outputs/charts/v2_profile_score_heatmap.png
data/outputs/charts/v2_profile_rank_stability_chart.png
data/outputs/charts/v2_site_readiness_map.png
data/outputs/charts/v2_site_decision_map.png
data/outputs/charts/v2_site_decision_map_readme.png
data/outputs/charts/v2_port_utilization_simulation.png
```

## V2 preview visuals

These committed README visuals are copied from the latest validated V2 model-generated charts so the README reflects the active V2 workflow rather than the older V1 workflow.

### V2 readiness ranking

![V2 readiness ranking preview](docs/assets/charts/v2_polished_readiness_score_chart.png)

### V2 GIS decision map

![V2 GIS decision map preview](docs/assets/charts/v2_site_decision_map_readme.png)

### V2 rank stability across profiles

![V2 profile rank stability preview](docs/assets/charts/v2_profile_rank_stability_chart.png)

### V2 port-use simulation and right-sizing validation

![V2 port simulation preview](docs/assets/charts/v2_port_utilization_simulation.png)

## Main input and output files

| File | Purpose |
|---|---|
| [data/inputs/real_sites_v1.csv](data/inputs/real_sites_v1.csv) | Stable V1 candidate-site input dataset. |
| [data/inputs/real_sites_v2.csv](data/inputs/real_sites_v2.csv) | Active V2 expansion candidate-site input dataset. |
| `data/outputs/v2_executive_site_summary.csv` | Main V2 executive decision table generated locally. |
| `data/outputs/deliverable_package_v2/` | Clean local V2 review package generated by the workflow. |
| [data/outputs/site_results.csv](data/outputs/site_results.csv) | Main V1 model result table. |
| [data/outputs/deliverable_package/](data/outputs/deliverable_package/) | Shareable local V1 package after generation. |

## Main workflow scripts

| File | Purpose |
|---|---|
| [src/run_v2.py](src/run_v2.py) | Run the active V2 workflow. |
| [src/check_outputs_v2.py](src/check_outputs_v2.py) | Check V2 outputs, site coverage, and deliverable-package hash sync. |
| [src/build_v2_deliverable_package.py](src/build_v2_deliverable_package.py) | Build the clean V2 deliverable package. |
| [src/plot_site_decision_map.py](src/plot_site_decision_map.py) | Build the GIS decision maps for report and README use. |
| [src/run_port_utilization_simulation.py](src/run_port_utilization_simulation.py) | Run the V2 port-use simulation. |
| [src/validate_right_sizing_with_simulation.py](src/validate_right_sizing_with_simulation.py) | Compare right-sizing recommendations with simulation results. |
| [src/build_v2_executive_summary.py](src/build_v2_executive_summary.py) | Build the V2 executive decision table. |
| [src/run_all.py](src/run_all.py) | Run the stable V1 workflow. |
| [src/ev_charger_model.py](src/ev_charger_model.py) | Main scoring and right-sizing model. |

See [docs/REPO_MAP.md](docs/REPO_MAP.md) for the fuller script and file map.

## Current planning interpretation

Current V2 result:

```text
FFX002 — City of Fairfax Regional Library is the strongest current public candidate.
FFX004 is the second-ranked Tier 1 candidate.
PWC006 is the strongest current Prince William County library candidate.
PWC002 remains useful but high-review because of garage/fire/AHJ/electrical uncertainty.
PWC003 should not be advanced as a general-public buildout without a clarified use case.
```

## Documentation

- [docs/V2_CURRENT_WORKFLOW_GUIDE.md](docs/V2_CURRENT_WORKFLOW_GUIDE.md)
- [START_HERE.md](START_HERE.md)
- [REPRODUCIBILITY_CHECKLIST.md](REPRODUCIBILITY_CHECKLIST.md)
- [docs/REPO_MAP.md](docs/REPO_MAP.md)
- [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md)
- [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)
- [docs/METHODOLOGY.md](docs/METHODOLOGY.md)
- [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)

## Important limitation

The prototype is useful for transparent early planning, but any real project decision must be checked with the appropriate site owner, technical reviewers, permitting offices, accessibility reviewers, Fire Marshal/AHJ reviewers, utility reviewers, and procurement process.
