# Data Dictionary

This file defines the main inputs, config files, and generated outputs used by the EV Charger Site-Readiness and Right-Sizing Prototype.

## Main input and config files

```text
data/inputs/real_sites_v1.csv              Main candidate-site input dataset
data/inputs/sites_demo.csv                 Small starter/demo dataset
data/inputs/new_sites_template.csv         Template for future candidate-site rows
data/config/scoring_profiles.csv           Alternative scoring-priority profiles
data/config/output_check_rules_v1.json     V1 output-check expectations
```

## Main generated outputs

```text
data/outputs/site_results.csv
data/outputs/data_quality_report.csv
data/outputs/sensitivity_results.csv
data/outputs/sensitivity_summary.csv
data/outputs/profile_results.csv
data/outputs/profile_rank_summary.csv
data/outputs/profile_comparison.md
data/outputs/model_run_summary.md
data/outputs/results_interpretation.md
data/outputs/baseline_comparison.csv
data/outputs/baseline_comparison.md
data/outputs/workflow_success.json
data/outputs/deliverable_package/
```

## Main generated charts

```text
data/outputs/charts/readiness_score_chart.png
data/outputs/charts/site_readiness_map.png
data/outputs/charts/profile_rank_stability_chart.png
data/outputs/charts/profile_score_heatmap.png
data/outputs/charts/utilization_vs_ports_<site>.png
```

Recommended profile-analysis visual:

```text
data/outputs/charts/profile_rank_stability_chart.png
```

The rank-stability chart is the main presentation visual because it shows whether each site's rank changes across scoring-priority profiles. A flat line at `#1` means the site remains the top candidate across all profiles.

Supporting profile-analysis visual:

```text
data/outputs/charts/profile_score_heatmap.png
```

The heatmap remains available when exact score and rank values are helpful.

## Important input columns

| Column | Meaning | Current status |
|---|---|---|
| `site_id` | Stable site identifier. | Project-created. |
| `site_name` | Candidate site name. | Facility/locality name. |
| `site_type` | Model behavior type such as `library`, `office`, `garage`, or `public_safety`. | Project classification. |
| `address`, `city`, `state`, `zip`, `lat`, `lon` | Location fields. | Official or official-derived where available. |
| `public_access` | Whether the site is a normal public charging candidate. | `1` public, `0` limited/non-public. |
| `employees_day`, `visitors_day`, `parking_spaces`, `hours_open`, `avg_dwell_min` | Demand and use assumptions. | V1 assumptions except FFX002 parking/hours. |
| `nearby_households_1mi` | Estimated households within 1 mile. | ACS/TIGER derived. |
| `nearby_jobs_1mi` | Estimated jobs within 1 mile. | LODES/TIGER derived. |
| `aadt_nearest` | Nearest traffic exposure. | VDOT derived. |
| `amenities_count_0_5mi` | Nearby public-use amenity category count. | Reviewed OpenStreetMap/Overpass count. |
| `ev_registrations_local`, `ev_share_local` | Local EV adoption signal. | V1 planning proxy. |
| `existing_l2_ports_1mi`, `existing_dcfc_ports_3mi` | Existing nearby public charging supply. | AFDC/NREL derived. |
| `equity_gap_index` | Equity signal used in scoring. | ACS/TIGER derived. |
| `elec_service_rating_amp`, `spare_capacity_kw` | Electrical service/capacity fields. | Placeholders needing confirmation. |
| `distance_to_service_ft`, `trenching_ft`, `trench_cost_per_ft`, `service_upgrade_cost_usd` | Planning feasibility inputs. | V1 estimates. |
| `notes` | Source and uncertainty explanation. | Required for transparency. |

## Important `site_results.csv` columns

| Column | Meaning |
|---|---|
| `model_rank` | Rank after sorting by readiness score. |
| `readiness_score` | Final weighted readiness score. |
| `data_confidence_score` | Separate 0-100 score showing how complete/confirmed the current input data is. |
| `data_confidence_level` | Plain-English level for the confidence score: High, Medium, or Low. |
| `data_confidence_reason` | Short explanation of what raised or lowered the confidence score. |
| `recommendation_tier` | Plain-English planning tier. |
| `planning_recommendation` | Suggested next planning action. |
| `priority_reason` | Short reason for the recommendation. |
| `data_needed_next` | Important confirmations needed before advancement. |
| `demand_subscore` | Demand score after public-access adjustment. |
| `feasibility_subscore` | Feasibility score. |
| `safety_subscore` | Site-context score. |
| `expected_sessions_day` | Estimated charging sessions per day. |
| `recommended_ports_now` | Starter port recommendation for the current period. |
| `recommended_ports_2035` | Port recommendation under 2035 growth. |
| `recommended_ports_2050` | Port recommendation under 2050 growth. |
| `estimated_utilization` | Utilization for the recommended current port count. |
| `mean_wait_min` | Estimated mean wait time in minutes. |
| `install_cost_est_usd` | Planning install cost estimate. |

## Data confidence interpretation

```text
readiness_score = how promising the site looks

data_confidence_score = how complete/confirmed the current inputs are
```

The confidence score does not change the ranking. It helps explain how carefully each result should be interpreted.

## Important `profile_results.csv` columns

| Column | Meaning |
|---|---|
| `profile_name` | Scoring profile identifier from `data/config/scoring_profiles.csv`. |
| `profile_label` | Human-readable profile label. |
| `profile_description` | Short description of the profile priority. |
| `demand_weight`, `feasibility_weight`, `safety_weight`, `equity_weight` | Weighting used for that profile. |
| `profile_rank` | Rank under the scoring profile. |
| `profile_readiness_score` | Readiness score under the scoring profile. |
| `base_model_rank` | Rank from the main V1 model. |
| `base_readiness_score` | Readiness score from the main V1 model. |
| `rank_change_vs_base` | Difference between profile rank and base model rank. |
| `profile_recommendation_tier` | Tier assigned under the scoring profile. |

## Workflow success marker

`data/outputs/workflow_success.json` is written only after `src/run_all.py` completes successfully. The deliverable package builder checks this file before packaging generated outputs.

## Output-check rule fields

These fields appear in `data/config/output_check_rules_v1.json`.

| Field | Meaning |
|---|---|
| `expected_site_ids` | Candidate site IDs expected in current V1 outputs. |
| `expected_top_site_id` | Site expected to rank first in the current V1 output. |
| `require_zero_data_quality_errors` | Whether `data_quality_report.csv` must contain zero ERROR items. |
| `require_zero_sensitivity_rank_range` | Whether every site must have `rank_range = 0` in sensitivity summary. |
| `expected_profile_names` | Scoring profiles expected in `profile_results.csv`. |
| `expected_profile_count` | Number of scoring profiles expected. |
| `expected_sites_per_profile` | Number of candidate sites expected in each profile. |
| `profile_readiness_score_min`, `profile_readiness_score_max` | Allowed score range for profile readiness scores. |

## Important limitation

The model is a planning-support prototype. Any real decision must be checked with the appropriate project stakeholders and technical reviewers.
