# EV Charger Site-Readiness and Right-Sizing Prototype

![Model Pipeline Check](https://github.com/andyyaro/Future-City-Fellowship-/actions/workflows/model-check.yml/badge.svg)

This repository contains a Python planning-support prototype for comparing public EV charging candidate sites in Fairfax City and Prince William County.

The model evaluates sites using demand, feasibility, safety/AHJ review, equity, and right-sizing signals. It does **not** replace utility review, engineering design, Fire Marshal/AHJ review, ADA/accessibility review, stormwater review, permitting, procurement, or stakeholder approval.

## Clean repository structure

```text
src/                  Python scripts
src/run_all.py
src/check_outputs.py
src/compare_to_baseline.py
src/create_baseline_snapshot.py
src/generate_run_summary.py
src/generate_results_interpretation.py
src/build_deliverable_package.py
src/ev_charger_model.py
src/validate_site_data.py
src/run_sensitivity_analysis.py
src/run_profile_analysis.py
src/build_osm_amenities.py
src/plot_site_map.py

data/inputs/           Main input datasets
data/inputs/real_sites_v1.csv
data/inputs/sites_demo.csv

data/config/           Small model configuration and output-check rule files
data/config/scoring_profiles.csv
data/config/output_check_rules_v1.json

data/baselines/        Curated committed benchmark snapshots
data/source_extracts/  Small model-ready source extracts
data/raw_exports/      Notes about large raw exports not committed to the repo
data/outputs/          Generated local outputs; ignored by Git
data/run_history/      Optional local run archive; ignored by Git

docs/                  Project documentation and reporting files
requirements.txt       Python package list for reproducible local runs
README.md              Start here
```

## Install requirements

```bash
pip install -r requirements.txt
```

The project currently uses:

```text
pandas
numpy
matplotlib
```

## Main workflow

Run the full local workflow from the repository root:

```bash
git pull --rebase origin main
python src/run_all.py
python src/build_deliverable_package.py
git status --short
```

`src/run_all.py` runs the validator, readiness/right-sizing model, sensitivity analysis, scoring profile analysis, readiness map, Markdown run summary, generated results interpretation, and one combined output-check step.

The output-check step also generates a baseline comparison report against the committed V1 baseline.

You can also run the steps manually:

```bash
python src/validate_site_data.py
python src/ev_charger_model.py
python src/run_sensitivity_analysis.py
python src/run_profile_analysis.py
python src/plot_site_map.py
python src/generate_run_summary.py
python src/generate_results_interpretation.py
python src/check_outputs.py
python src/build_deliverable_package.py
```

Optional amenities POI workflow:

```bash
python src/build_osm_amenities.py
```

Default input:

```text
data/inputs/real_sites_v1.csv
```

Default generated outputs:

```text
data/outputs/data_quality_report.csv
data/outputs/site_results.csv
data/outputs/sensitivity_results.csv
data/outputs/sensitivity_summary.csv
data/outputs/profile_results.csv
data/outputs/profile_rank_summary.csv
data/outputs/profile_comparison.md
data/outputs/model_run_summary.md
data/outputs/results_interpretation.md
data/outputs/baseline_comparison.csv
data/outputs/baseline_comparison.md
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/site_readiness_map.png
data/outputs/charts/utilization_vs_ports_<site>.png
data/outputs/amenities_osm_summary_0_5mi.csv
data/outputs/amenities_osm_pois_0_5mi.csv
data/outputs/deliverable_package/
```

## Scoring profile analysis

`src/run_profile_analysis.py` tests how rankings change when different planning priorities are emphasized.

The profile definitions live in:

```text
data/config/scoring_profiles.csv
```

Current profiles include:

```text
base
demand_priority
equity_priority
feasibility_priority
safety_priority
```

This does not replace the main model ranking. It is a planning-sensitivity layer that shows whether the same sites stay strong when demand, equity, feasibility, or safety is weighted more heavily.

Generated profile outputs:

```text
data/outputs/profile_results.csv
data/outputs/profile_rank_summary.csv
data/outputs/profile_comparison.md
```

## Generated interpretation

`src/generate_results_interpretation.py` creates a dynamic plain-English interpretation from the latest local outputs.

Generated output:

```text
data/outputs/results_interpretation.md
```

This generated file adapts when rankings, recommendation tiers, sensitivity results, profile results, or review triggers change. It should be preferred over static docs when sharing the latest run result.

## Combined output check

`src/check_outputs.py` is the single final output-check command.

It does two things:

```text
1. Sanity-checks current generated outputs.
2. Generates a baseline comparison report against data/baselines/v1_baseline/.
```

The V1 sanity-check expectations live in:

```text
data/config/output_check_rules_v1.json
```

The sanity check currently verifies that required outputs exist, the expected six candidate site IDs appear, model ranks are valid, readiness scores and profile scores are in range, port counts are non-negative, sensitivity rankings remain stable, profile outputs have the expected profiles and row counts, the generated interpretation exists, and the data-quality report has no ERROR items.

The baseline comparison writes local reports to:

```text
data/outputs/baseline_comparison.csv
data/outputs/baseline_comparison.md
```

This makes it easy to see whether rankings, readiness scores, recommendation tiers, or port recommendations changed after model/data updates.

To intentionally create a future baseline:

```bash
python src/run_all.py
python src/create_baseline_snapshot.py --label v2_baseline
```

Only commit a new baseline after reviewing that it should become an official benchmark.

## Deliverable package

`src/build_deliverable_package.py` collects the main generated outputs and reporting files into one local shareable folder.

Run:

```bash
python src/run_all.py
python src/build_deliverable_package.py
```

Default package folder:

```text
data/outputs/deliverable_package/
```

The package includes charts, dynamic run outputs, key CSV tables, reporting documents, a package README, and a package manifest. It is ignored by Git because it is generated locally.

## Generated outputs stay local

Files in `data/outputs/` are generated by local model runs. They are intentionally ignored by Git and should stay local by default.

This keeps the repository focused on source code, input data, source extracts, baseline snapshots, and documentation instead of committing a new set of output files every time the model is rerun.

Only commit a generated output if the project intentionally decides to publish a specific static artifact.

## Optional examples

Run the model on the demo dataset:

```bash
python src/ev_charger_model.py --input data/inputs/sites_demo.csv --output data/outputs/demo_site_results.csv
```

Run the validator on the demo dataset:

```bash
python src/validate_site_data.py --input data/inputs/sites_demo.csv --output data/outputs/demo_data_quality_report.csv
```

Run the profile analysis after generating site results:

```bash
python src/run_profile_analysis.py
```

Generate the dynamic results interpretation after generating outputs:

```bash
python src/generate_results_interpretation.py
```

Run the OSM amenities workflow with a longer pause between API requests:

```bash
python src/build_osm_amenities.py --pause 5
```

Create the readiness map after running the model:

```bash
python src/plot_site_map.py
```

Create the Markdown run summary after running the model:

```bash
python src/generate_run_summary.py
```

Run the combined output check after generating outputs:

```bash
python src/check_outputs.py
```

Build the shareable deliverable package:

```bash
python src/build_deliverable_package.py
```

## What the model does

1. Reads a candidate-site CSV.
2. Cleans numeric and yes/no fields.
3. Applies a public-access adjustment so limited-access sites do not rank like normal public sites.
4. Scores each site for demand, feasibility, safety, and equity.
5. Estimates charging sessions per day.
6. Recommends starter ports for now, 2035, and 2050.
7. Adds plain-English recommendation tiers and next data needs.
8. Runs sensitivity scenarios to test whether rankings stay stable under uncertainty.
9. Tests alternative scoring profiles for different planning priorities.
10. Exports CSV outputs, charts, and Markdown summaries.
11. Generates an adaptive results interpretation from the latest outputs.
12. Runs one combined output check that validates current outputs and compares them against the committed V1 baseline snapshot.
13. Can build a local deliverable package for sharing or presentation.

## Current candidate sites

```text
PWC001 — PWC McCoart Government Center
PWC002 — Neabsco-Potomac Commuter Garage
PWC003 — Prince William County Public Safety Training Center
PWC004 — Chinn Park Regional Library
FFX001 — Fairfax City Hall or municipal building
FFX002 — City of Fairfax Regional Library
```

## Current planning interpretation

```text
FFX002 — Tier 1 / stable top candidate
FFX001 — Tier 1 / stable second candidate
PWC004 — Tier 2 / strongest current PWC public-library candidate under future/reopened planning assumptions
PWC002 — High-review candidate because of garage context
PWC001 — Tier 3 / lower priority under current assumptions
PWC003 — Low public-priority / special-use because public access is limited
```

## Documentation guide

Use these docs depending on what you need:

```text
docs/METHODOLOGY.md                         How scoring and port recommendations work
docs/DATA_DICTIONARY.md                     Input/output column definitions
docs/DATA_SOURCES.md                        Source plan and source quality notes
docs/RESULTS_INTERPRETATION.md              Static plain-English result guide
docs/READINESS_MAP_GUIDE.md                 How to interpret the generated readiness map
docs/OSM_AMENITIES_WORKFLOW.md              How to download and review OSM amenity POIs
docs/RECOMMENDATION_TIERS.md                Recommendation tier logic
docs/SENSITIVITY_ANALYSIS.md                Sensitivity scenario setup
docs/SENSITIVITY_RESULTS_INTERPRETATION.md  Sensitivity result interpretation
docs/MODEL_FINDINGS_BRIEF.md                Concise report-style findings brief
docs/MODEL_FINDINGS_REPORT.md               Fuller report-style write-up
docs/PRESENTATION_OUTLINE.md                Slide-style presentation outline
docs/STAKEHOLDER_DATA_REQUEST.md            Stakeholder questions for replacing assumptions
docs/PROJECT_STATUS.md                      Project status and next steps
docs/PROJECT_DECISIONS_LOG.md               Central project decision log
```

Latest generated interpretation:

```text
data/outputs/results_interpretation.md
```

## Important limitations

The current model still needs stronger confirmation for:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
hours_open for sites except FFX002
parking_spaces for sites except FFX002
local EV adoption counts
```

The prototype is useful for transparent early planning, but any real project decision must be checked with the appropriate site owner, utility, engineers, ADA/accessibility reviewers, Fire Marshal/AHJ, stormwater staff, permitting offices, and procurement process.
