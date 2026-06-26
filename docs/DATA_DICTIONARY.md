# Data Dictionary

This file defines the main inputs, config files, and generated outputs used by the EV Charger Site-Readiness and Right-Sizing Prototype.

The active Phase 2 workflow is V2 on `v2-expansion-planning`. V1 remains available on `main` as the stable baseline workflow.

## Active V2 input and config files

```text
data/inputs/real_sites_v2.csv                  Active V2 candidate-site input dataset
data/inputs/v2_port_sizing_scenarios.csv       Port-sizing stress-test assumptions
data/config/scoring_profiles.csv               Alternative scoring-priority profiles
data/baselines/v2_baseline_snapshot.json       Saved V2 baseline guardrails
requirements.txt                               Core Python dependencies
requirements-gis.txt                           GIS map dependencies for V2 decision maps
requirements-v2.txt                            Optional public-data upgrade helper dependencies
```

## Active V2 generated outputs

```text
data/outputs/v2_site_results.csv
data/outputs/v2_action_matrix.md
data/outputs/v2_data_quality_report.csv
data/outputs/v2_sensitivity_results.csv
data/outputs/v2_sensitivity_summary.csv
data/outputs/v2_profile_results.csv
data/outputs/v2_profile_rank_summary.csv
data/outputs/v2_profile_comparison.md
data/outputs/v2_electrical_scenario_results.csv
data/outputs/v2_electrical_risk_summary.csv
data/outputs/v2_electrical_feasibility_report.md
data/outputs/v2_right_sizing_scenarios.csv
data/outputs/v2_right_sizing_report.md
data/outputs/v2_port_utilization_simulation.csv
data/outputs/v2_port_utilization_simulation_report.md
data/outputs/v2_port_sizing_scenario_results.csv
data/outputs/v2_port_sizing_scenario_summary.csv
data/outputs/v2_port_sizing_scenario_report.md
data/outputs/v2_right_sizing_validation.csv
data/outputs/v2_right_sizing_validation_report.md
data/outputs/v2_executive_site_summary.csv
data/outputs/v2_executive_site_summary.md
data/outputs/v2_results_interpretation.md
data/outputs/v2_run_summary.md
data/outputs/v2_baseline_comparison.json
data/outputs/v2_baseline_comparison.md
data/outputs/v2_workflow_success.json
data/outputs/deliverable_package_v2/
```

## Active V2 generated charts

```text
data/outputs/charts/v2_readiness_score_chart.png
data/outputs/charts/v2_polished_readiness_score_chart.png
data/outputs/charts/v2_data_confidence_chart.png
data/outputs/charts/v2_profile_score_heatmap.png
data/outputs/charts/v2_profile_rank_stability_chart.png
data/outputs/charts/v2_site_readiness_map.png
data/outputs/charts/v2_site_decision_map.png
data/outputs/charts/v2_site_decision_map_readme.png
data/outputs/charts/v2_port_utilization_simulation.png
data/outputs/charts/v2_port_sizing_scenario_heatmap.png
data/outputs/charts/v2/utilization_vs_ports_<site>.png
```

The committed README map asset is:

```text
docs/assets/charts/v2_site_decision_map_readme.png
```

## Important `real_sites_v2.csv` input columns

| Column | Meaning | Current status |
|---|---|---|
| `site_id` | Stable site identifier such as `FFX002` or `PWC006`. | Project-created. |
| `site_name` | Candidate site name. | Facility/locality name. |
| `site_type` | Model behavior type such as `library`, `office`, `garage`, or `public_safety`. | Project classification. |
| `address`, `city`, `state`, `zip`, `lat`, `lon` | Location fields used for maps and context. | Official or official-derived where available. |
| `public_access` | Whether the site is a normal public charging candidate. | `1` public, `0` limited/non-public. |
| `employees_day`, `visitors_day`, `parking_spaces`, `hours_open`, `avg_dwell_min` | Demand and use assumptions. | Mixed official values and planning assumptions. |
| `nearby_households_1mi` | Estimated households within 1 mile. | ACS/TIGER derived where upgraded. |
| `nearby_jobs_1mi` | Estimated jobs within 1 mile. | LODES/TIGER derived where upgraded. |
| `aadt_nearest` | Nearby traffic exposure. | VDOT nearest-segment screening value. |
| `amenities_count_0_5mi` | Nearby public-use amenity category count. | Reviewed OpenStreetMap/Overpass count. |
| `ev_registrations_local`, `ev_share_local` | Local EV adoption signal. | Planning proxy until better locality EV data is available. |
| `existing_l2_ports_1mi`, `existing_dcfc_ports_3mi` | Existing nearby public charging supply. | AFDC/NREL derived. |
| `equity_gap_index` | Equity signal used in scoring. | ACS/TIGER derived where upgraded. |
| `elec_service_voltage`, `elec_service_rating_amp`, `spare_capacity_kw` | Electrical service/capacity fields. | Placeholders needing confirmation. |
| `distance_to_service_ft`, `trenching_ft`, `trench_cost_per_ft`, `service_upgrade_cost_usd` | Planning feasibility inputs. | Screening-level estimates. |
| `ada_layout_possible`, `fire_access_ok`, `garage_enclosed`, `emergency_disconnect_visible`, `stormwater_risk` | Site review and safety flags. | Screening-level fields needing site review. |
| `notes` | Source and uncertainty explanation. | Required for transparency. |

## Important `v2_site_results.csv` columns

| Column | Meaning |
|---|---|
| `model_rank` | Rank after sorting by readiness score. |
| `readiness_score` | Final weighted readiness score. |
| `data_confidence_score` | Separate 0-100 score showing how complete/confirmed the current input data is. |
| `data_confidence_level` | Plain-English confidence level. |
| `data_confidence_reason` | Short explanation of what raised or lowered confidence. |
| `readiness_band` | Simple readiness category used by the action matrix. |
| `confidence_band` | Simple confidence category used by the action matrix. |
| `readiness_confidence_cell` | Combined readiness/confidence action-matrix cell. |
| `action_label` | Short next-action label for the site. |
| `action_detail` | Longer next-action explanation. |
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

## Important `v2_right_sizing_scenarios.csv` columns

| Column | Meaning |
|---|---|
| `ports_now` | Recommended starter install size. |
| `ports_2035_base`, `ports_2035_high` | 2035 planning sizes under base and high growth. |
| `ports_2050_base`, `ports_2050_high` | 2050 planning sizes under base and high growth. |
| `future_ready_capacity` | Capacity to plan conduit/electrical/site layout around. |
| `expansion_strategy` | Planning strategy, such as starter install, future-ready, monitor, or review before expansion. |

## Important `v2_port_utilization_simulation.csv` columns

| Column | Meaning |
|---|---|
| `demand_case` | Demand case such as `current`, `2035_high`, or `2050_high`. |
| `port_count` | Tested port count. |
| `sessions_day` | Simulated daily charging sessions for the demand case. |
| `utilization_pct` | Estimated utilization percentage. |
| `peak_demand_ratio` | Peak-load screen used to estimate waiting risk. |
| `estimated_wait_min` | Planning-screen wait estimate. |
| `queue_risk_level` | Low, moderate, elevated, or high queue-risk label. |
| `capacity_status` | `right_sized`, `acceptable_but_monitor`, `likely_overbuilt_or_low_demand`, or `underbuilt`. |
| `is_ports_now` | Whether the tested row equals the current recommended install. |
| `is_future_ready_capacity` | Whether the tested row equals the future-ready capacity plan. |

## Important `v2_port_sizing_scenario_results.csv` columns

| Column | Meaning |
|---|---|
| `scenario_name` | Scenario code from `v2_port_sizing_scenarios.csv`. |
| `scenario_label` | Presentation label for the scenario. |
| `scenario_description` | Description of what assumption is being stress-tested. |
| `scenario_min_ports_current` | Smallest tested port count that avoids underbuilt status under current-demand scenario assumptions. |
| `scenario_min_ports_2035_high` | Smallest tested port count under 2035 high-demand assumptions. |
| `scenario_min_ports_2050_high` | Smallest tested port count under 2050 high-demand assumptions. |
| `current_capacity_gap` | Extra current ports needed under the scenario, if any. |
| `future_capacity_gap` | Extra future-ready ports needed under the scenario, if any. |
| `current_alignment` | Whether current ports match, exceed, or fall below the scenario minimum. |
| `future_capacity_alignment` | Whether future-ready capacity matches, covers, or is exceeded by the scenario. |

## Important `v2_executive_site_summary.csv` columns

| Column | Meaning |
|---|---|
| `model_rank`, `site_id`, `site_name`, `readiness_score` | Core ranked site identity and score. |
| `data_confidence_level` | Current input confidence level. |
| `recommendation_tier`, `action_label` | Planning decision labels. |
| `electrical_risk_level`, `expected_electrical_rank`, `expected_electrical_score` | Electrical-risk scenario summary. |
| `ports_now`, `ports_2035_base`, `ports_2035_high`, `ports_2050_base`, `ports_2050_high`, `future_ready_capacity` | Right-sizing and future-ready planning fields. |
| `sim_min_ports_current`, `sim_min_ports_2035_high`, `sim_min_ports_2050_high` | Base port-use simulation minimums. |
| `scenario_max_min_ports_2050_high` | Highest scenario-based 2050 high-demand minimum port count. |
| `scenario_future_capacity_gap` | Largest scenario gap between scenario minimum and planned future-ready capacity. |
| `scenario_sensitivity_level` | Whether the site is robust or sensitive under tested scenarios. |
| `scenario_stress_note` | Plain-English scenario note for the decision table. |
| `current_alignment`, `future_alignment`, `simulation_supported_strategy` | Right-sizing validation labels. |
| `right_sizing_validation_note` | Plain-English validation note. |
| `major_review_flags` | Consolidated review flags for planning follow-up. |

## Stable V1 input and config files

```text
data/inputs/real_sites_v1.csv              Stable V1 candidate-site input dataset
data/inputs/sites_demo.csv                 Small starter/demo dataset
data/inputs/new_sites_template.csv         Template for future candidate-site rows
data/config/output_manifest_v1.json        Expected outputs, checker files, and package contents
data/config/output_check_rules_v1.json     V1 output-check expectations
```

## Stable V1 generated outputs

```text
data/outputs/site_results.csv
data/outputs/action_matrix.md
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

## Data confidence and action-matrix interpretation

```text
readiness_score = how promising the site looks

data_confidence_score = how complete/confirmed the current inputs are

action_label = what to do next
```

The confidence score does not change the ranking. The action matrix turns readiness and confidence into a simple next step.

## Important limitation

The model is a planning-support prototype. Any real decision must be checked with the appropriate project stakeholders and technical reviewers.
