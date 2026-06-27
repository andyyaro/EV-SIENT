# Active Docs Index

Use this page to find the current, reviewer-facing documentation without scanning every checkpoint file.

## Public visual artifact

The main public-facing visual artifact is the Tableau Public workbook:

[Open the EV Charging Site Readiness Workbook](https://public.tableau.com/views/EV_Charging_Site_Readiness_Workbook/Bar-EVChargingReadinessbySite)

Tableau Public opens the workbook through one starting worksheet URL. Use the visible sheet tabs on the Tableau Public page to navigate the full workbook.

Workbook documentation:

- [../tableau/README.md](../tableau/README.md)

Static PNG charts are still generated for reproducibility, GitHub previews, and the technical deliverable package, but Tableau is the primary public visual layer.

## Read first

- [../README.md](../README.md) — project overview, Tableau link, and preview visuals
- [../START_HERE.md](../START_HERE.md) — shortest project entry point
- [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md) — reviewer-friendly path through the repo
- [../REPRODUCIBILITY_CHECKLIST.md](../REPRODUCIBILITY_CHECKLIST.md) — local reproduction checklist
- [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md) — active V2 workflow guide
- [REPO_MAP.md](REPO_MAP.md) — repository structure and script map
- [../src/README.md](../src/README.md) — script-by-script source index
- [MAINTENANCE_CHECKLIST.md](MAINTENANCE_CHECKLIST.md) — checks before pushing or sharing
- [PROJECT_STATUS.md](PROJECT_STATUS.md) — current project state

## Reproduce the active V2 workflow

```bash
git switch v2-expansion-planning
git pull --rebase origin v2-expansion-planning
make setup
make full-v2-tableau
make links
```

Equivalent all-in review command:

```bash
make review
```

Equivalent raw commands:

```bash
pip install -r requirements.txt
pip install -r requirements-gis.txt
python src/run_v2.py
python src/check_outputs_v2.py
python src/build_tableau_exports.py
python src/check_tableau_exports.py
```

## Open outputs in the right order

For public-facing visual review, start with Tableau Public:

```text
https://public.tableau.com/views/EV_Charging_Site_Readiness_Workbook/Bar-EVChargingReadinessbySite
```

For technical reproducibility review, after running V2, start with:

```text
data/outputs/deliverable_package_v2/README.md
data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md
data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md
data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md
data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png
data/outputs/deliverable_package_v2/charts/v2_port_sizing_scenario_heatmap.png
```

## Technical method docs

- [METHODOLOGY.md](METHODOLOGY.md)
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
- [DATA_SOURCES.md](DATA_SOURCES.md)
- [V2_ELECTRICAL_RISK_SCENARIO_METHOD.md](V2_ELECTRICAL_RISK_SCENARIO_METHOD.md)
- [V2_RIGHT_SIZING_SCENARIO_METHOD.md](V2_RIGHT_SIZING_SCENARIO_METHOD.md)
- [V2_CURRENT_WORKFLOW_GUIDE.md](V2_CURRENT_WORKFLOW_GUIDE.md)

## Planning and reporting docs

- [MODEL_FINDINGS_BRIEF.md](MODEL_FINDINGS_BRIEF.md)
- [MODEL_FINDINGS_REPORT.md](MODEL_FINDINGS_REPORT.md)
- [PRESENTATION_OUTLINE.md](PRESENTATION_OUTLINE.md)
- [RESULTS_INTERPRETATION.md](RESULTS_INTERPRETATION.md)
- [READINESS_MAP_GUIDE.md](READINESS_MAP_GUIDE.md)
- [DATA_CONFIDENCE_SCORE.md](DATA_CONFIDENCE_SCORE.md)
- [RECOMMENDATION_TIERS.md](RECOMMENDATION_TIERS.md)
- [SENSITIVITY_ANALYSIS.md](SENSITIVITY_ANALYSIS.md)

## Expansion and stakeholder docs

- [SITE_SCREENING_CHECKLIST.md](SITE_SCREENING_CHECKLIST.md)
- [ADDING_NEW_SITES_GUIDE.md](ADDING_NEW_SITES_GUIDE.md)
- [STAKEHOLDER_OUTREACH_PLAN.md](STAKEHOLDER_OUTREACH_PLAN.md)
- [SITE_EXPANSION_AND_OUTREACH_TRIAGE.md](SITE_EXPANSION_AND_OUTREACH_TRIAGE.md)
- [V2_PUBLIC_DATA_UPGRADE_WORKFLOW.md](V2_PUBLIC_DATA_UPGRADE_WORKFLOW.md)
- [V2_NEXT_BATCH_PLAN.md](V2_NEXT_BATCH_PLAN.md)
- [V2_BACKLOG_TRIAGE_CHECKLIST.md](V2_BACKLOG_TRIAGE_CHECKLIST.md)

## Checkpoint and history docs

Use [checkpoints/README.md](checkpoints/README.md) for implementation history and milestone notes.

Checkpoint files are useful for auditability, but new reviewers should start with the active docs above.
