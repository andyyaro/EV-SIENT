# Tableau Workbook

This folder contains the main interactive Tableau visual artifact for the Future City Fellowship Phase 2 EV charging prototype.

## Workbook

- Workbook: `EV_Charging_Site_Readiness_Workbook.twbx`
- Type: Packaged Tableau workbook
- Purpose: Public-facing visual artifact for the EV Charging Site-Readiness and Right-Sizing Model

The workbook is intended to replace the earlier static/model-generated PNG charts with a polished, interactive visual set.

## Visuals included

1. **EV Charging Site Readiness Ranking**  
   Ranks candidate public sites by readiness score.

2. **Candidate EV Charging Site Map**  
   Shows candidate charging locations and nearby reference points.

3. **Charging Port Growth by Planning Year**  
   Compares current installation needs with future-ready planning targets for 2035 and 2050.

4. **Review Burden by Site**  
   Summarizes review complexity by candidate site.

5. **Review Burden Map by Candidate Site**  
   Shows where higher-review candidate sites are located geographically.

6. **Profile Readiness by Scoring Profile**  
   Compares each site’s readiness score and rank under different scoring priorities.

7. **Site Subscores by Model Dimension**  
   Shows how demand, electrical feasibility, safety/review, and equity contribute to each site’s readiness.

8. **Profile Rank Stability by Site**  
   Shows how much each site’s rank changes across alternative scoring profiles.

9. **Data Confidence and Review Issues by Site**  
   Shows which site recommendations need additional data confirmation.

10. **Port Sizing Scenario Gaps**  
    Shows where future-ready capacity may fall short under high-growth or stress assumptions.

11. **Port Utilization Simulation**  
    Shows how estimated port utilization changes as charger count increases under different demand cases.

12. **Action Decision Quadrant**  
    Compares readiness and implementation complexity to support next-step planning decisions.

## Generated Tableau input files

Tableau-ready CSV inputs are generated under `data/outputs/tableau/`.

These files are generated outputs and are not committed by default.

Current Tableau export files include:

- `tableau_site_readiness.csv`
- `tableau_site_map.csv`
- `tableau_map_points.csv`
- `tableau_port_growth.csv`
- `tableau_review_burden.csv`
- `tableau_review_burden_map.csv`
- `tableau_profile_score_heatmap.csv`
- `tableau_profile_subscore_heatmap.csv`
- `tableau_profile_rank_stability.csv`
- `tableau_data_confidence.csv`
- `tableau_data_quality_issues.csv`
- `tableau_port_sizing_scenario_heatmap.csv`
- `tableau_port_utilization_simulation.csv`
- `tableau_action_recommendation_matrix.csv`
- `tableau_action_decision_quadrant_clean.csv`

## How to regenerate Tableau CSV inputs

From the repo root:

`python src/build_tableau_exports.py`

If source model outputs are missing or stale, run:

`make full-v2`

Then regenerate Tableau exports:

`python src/build_tableau_exports.py`

## How to refresh the workbook

1. Regenerate Tableau CSV inputs.
2. Open `tableau/EV_Charging_Site_Readiness_Workbook.twbx`.
3. Refresh or repoint data sources if Tableau prompts for file locations.
4. Review worksheet titles, legends, filters, and tooltips.
5. Save the packaged workbook.
6. Commit the workbook and source script changes, but do not commit generated CSVs unless intentionally changing that policy.

## Planning-support disclaimer

This workbook is a planning-support artifact only. It is not final engineering, permitting, utility, procurement, fire, ADA, stormwater, or construction approval.

Review burden scores, decision quadrants, and scenario outputs are prototype planning indicators. They should support screening, prioritization, and discussion, not official determinations.
