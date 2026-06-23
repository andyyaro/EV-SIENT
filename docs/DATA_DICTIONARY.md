# Data Dictionary

This file defines the main inputs, configs, and outputs used by the EV Charger Site-Readiness and Right-Sizing Prototype.

## Main files

```text
data/inputs/real_sites_v1.csv              Main candidate-site input dataset
data/inputs/sites_demo.csv                 Small starter/demo dataset
data/config/scoring_profiles.csv           Alternative scoring-priority profiles
data/config/output_check_rules_v1.json     V1 output-check expectations
data/outputs/site_results.csv              Main model output, generated locally
data/outputs/data_quality_report.csv       Validation checklist output, generated locally
data/outputs/sensitivity_results.csv       Detailed sensitivity output, generated locally
data/outputs/sensitivity_summary.csv       Sensitivity summary output, generated locally
data/outputs/profile_results.csv           Detailed scoring-profile output, generated locally
data/outputs/profile_rank_summary.csv      Scoring-profile rank stability summary, generated locally
data/outputs/profile_comparison.md         Scoring-profile plain-English report, generated locally
data/outputs/model_run_summary.md          Dynamic run summary, generated locally
data/outputs/results_interpretation.md     Dynamic results interpretation, generated locally
data/outputs/baseline_comparison.csv       Baseline comparison table, generated locally
data/outputs/baseline_comparison.md        Baseline comparison report, generated locally
data/outputs/deliverable_package/          Local shareable output package, generated locally
```

## Important input columns

| Column | Meaning | Current status |
|---|---|---|
| `site_id` | Stable site identifier. | Project-created. |
| `site_name` | Candidate site name. | Facility/locality name. |
| `site_type` | Model behavior type such as `library`, `office`, `garage`, `public_safety`. | Project classification. |
| `address`, `city`, `state`, `zip`, `lat`, `lon` | Location fields. | Official GIS/facility sources where available. |
| `public_access` | Whether the site is a normal public charging candidate. | `1` public, `0` limited/non-public. |
| `employees_day`, `visitors_day`, `parking_spaces`, `hours_open`, `avg_dwell_min` | Demand and use assumptions. | V1 planning assumptions except FFX002 parking/hours. |
| `nearby_households_1mi` | Estimated households within 1 mile. | Official-derived from ACS/TIGER. |
| `nearby_jobs_1mi` | Estimated jobs within 1 mile. | Official-derived from LODES/TIGER. |
| `aadt_nearest` | Nearest traffic exposure. | Official-derived from VDOT. |
| `amenities_count_0_5mi` | Nearby public-use amenity category count. | Reviewed OpenStreetMap/Overpass six-category count. |
| `ev_registrations_local`, `ev_share_local` | Local EV adoption signal. | V1 planning proxy. |
| `existing_l2_ports_1mi`, `existing_dcfc_ports_3mi` | Existing nearby public charging supply. | Official-derived from AFDC/NREL. |
| `equity_gap_index` | Equity signal used in scoring. | Official-derived ACS/TIGER model extract. |
| `elec_service_rating_amp`, `spare_capacity_kw` | Electrical service/capacity fields. | Still placeholders needing confirmation. |
| `distance_to_service_ft`, `trenching_ft`, `trench_cost_per_ft`, `service_upgrade_cost_usd` | Electrical/cost feasibility inputs. | Planning-level V1 estimates. |
| `ada_layout_possible`, `fire_access_ok`, `garage_enclosed`, `emergency_disconnect_visible`, `stormwater_risk`, `battery_storage_flag` | Review and safety flags. | Planning/site-review assumptions. |
| `notes` | Source and uncertainty explanation. | Required for transparency. |

## Important main output columns

These columns appear in `data/outputs/site_results.csv`.

| Column | Meaning |
|---|---|
| `model_rank` | Rank after sorting by readiness score. |
| `readiness_score` | Final weighted readiness score. |
| `recommendation_tier` | Plain-English planning tier. |
| `planning_recommendation` | Suggested next planning action. |
| `priority_reason` | Short reason for the recommendation. |
| `data_needed_next` | Important confirmations needed before advancement. |
| `demand_subscore` | Demand score after public-access adjustment. |
| `feasibility_subscore` | Feasibility score. |
| `safety_subscore` | Safety/site-review score. |
| `expected_sessions_day` | Estimated charging sessions per day. |
| `recommended_ports_now` | Starter port recommendation for the current period. |
| `recommended_ports_2035` | Port recommendation under 2035 growth. |
| `recommended_ports_2050` | Port recommendation under 2050 growth. |
| `estimated_utilization` | Utilization for the recommended current port count. |
| `mean_wait_min` | Estimated mean wait time in minutes. |
| `install_cost_est_usd` | Planning install cost estimate. |
| `ahj_review_flag` | `1` if model-level review trigger exists. |
| `review_reason` | Plain-English review trigger explanation. |

## Important scoring-profile output columns

These columns appear in `data/outputs/profile_results.csv`.

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

## Important output-check rule fields

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

## Recommendation interpretation

```text
Tier 1 — advance to site screening = strong current candidate.
Tier 2 — promising candidate, refine data = promising but needs stronger support.
High-review candidate = has value, but review complexity must be resolved first.
Low public-priority / special-use = not ready as a general-public charging candidate.
Tier 3 — lower priority / monitor = lower current priority than stronger alternatives.
```

## Important limitation

The model is a planning-support prototype. Any real decision must be checked with site owners, utilities, engineers, ADA/accessibility reviewers, Fire Marshal/AHJ, stormwater staff, permitting offices, and procurement processes.
