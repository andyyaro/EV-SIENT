# Data Dictionary

This file defines the main columns used by the EV Charger Site-Readiness and Right-Sizing Prototype.

It covers two files:

```text
real_sites_v1.csv
site_results.csv
```

`real_sites_v1.csv` is the main input dataset. `site_results.csv` is the main output produced after running the model.

## General notes

Many fields are planning estimates, not official engineering values.

Official or official-derived fields should still be checked before a real project moves forward. The model is a planning-support prototype and does not replace AHJ, Fire Marshal, ADA, utility, stormwater, engineering, or permitting review.

## real_sites_v1.csv input columns

| Column | Type | Meaning | Current source / status |
|---|---:|---|---|
| `site_id` | text | Short stable ID for the candidate site. | Project-created ID. |
| `site_name` | text | Candidate site name. | Local government/facility source or project label. |
| `site_type` | text | Site category used by the model behavior assumptions. Examples: `library`, `office`, `garage`, `public_safety`, `clinic`, `fleet`. | Project classification. |
| `address` | text | Street address. | Official GIS/facility source where available. |
| `city` | text | City or locality name. | Official GIS/facility source where available. |
| `state` | text | State abbreviation. | Usually `VA`. |
| `zip` | text | ZIP code. Stored as text so extended ZIPs are preserved. | Official GIS/facility source where available. |
| `lat` | number | Latitude coordinate. | Official GIS address point where available. |
| `lon` | number | Longitude coordinate. | Official GIS address point where available. |
| `public_access` | yes/no number | Whether the general public can reasonably access charging at the site. `1` means public access. `0` means limited or non-public access. | Project/stakeholder/site assumption. |
| `employees_day` | number | Estimated daily employees or staff associated with the site. | V1 planning assumption. Needs better facility data. |
| `visitors_day` | number | Estimated daily visitors, patrons, users, or parking users. | V1 planning assumption. Needs better facility data. |
| `fleet_vehicles` | number | Number of fleet vehicles associated with the site. | Placeholder unless stakeholder data is available. |
| `parking_spaces` | number | Estimated or known parking spaces at the site. | Placeholder/manual estimate unless confirmed. |
| `hours_open` | number | Approximate daily hours available for charging. | Planning assumption unless official hours are added. |
| `avg_dwell_min` | number | Average time a typical visitor/user stays at the site, in minutes. | Site-type planning assumption. |
| `nearby_households_1mi` | number | Estimated households within 1 mile of the site. | Official-derived from ACS 2024 5-Year B11001 and TIGER 2024 block group geometry. |
| `nearby_jobs_1mi` | number | Estimated jobs within 1 mile of the site. | Official-derived from LODES 2023 Virginia WAC and TIGER 2024 block group geometry. |
| `aadt_nearest` | number | Annual Average Daily Traffic from the nearest VDOT traffic segment. | Official-derived from VDOT Bidirectional Traffic Volume 2025. |
| `amenities_count_0_5mi` | number | Manual V1 count of nearby public-use amenity categories within roughly 0.5 miles. It is a category count, not an exact business count. | Manual V1 planning estimate from `data/source_extracts/amenities_0_5mi.csv`. Replace later with GIS/POI data. |
| `ev_registrations_local` | number | Local EV registration count, if available. | Placeholder. |
| `ev_share_local` | number | Estimated local EV share. Example: `0.07` means 7 percent. | Planning assumption for V1. |
| `existing_l2_ports_1mi` | number | Public active Level 2 charging ports within 1 mile. | Official-derived from AFDC / NREL Alternative Fuel Stations export. |
| `existing_dcfc_ports_3mi` | number | Public active DC fast charging ports within 3 miles. | Official-derived from AFDC / NREL Alternative Fuel Stations export. |
| `equity_gap_index` | number | Project-created equity gap score. Higher means the model treats the site as having more equity value. | Placeholder/project-created. Needs ACS-based improvement. |
| `elec_service_voltage` | number | Electrical service voltage at or near the site. | Placeholder unless facility/utility data is available. |
| `elec_service_rating_amp` | number | Electrical service rating in amps. | Placeholder unless facility/utility data is available. |
| `spare_capacity_kw` | number | Estimated spare electrical capacity in kilowatts. Higher values improve feasibility. | Placeholder/manual assumption. Needs utility or facility data. |
| `distance_to_service_ft` | number | Estimated distance from charger location to electrical service, in feet. Lower values improve feasibility. | Placeholder/manual assumption. |
| `trenching_ft` | number | Estimated trenching length in feet. Used in install cost estimate. | Placeholder/manual assumption. |
| `trench_cost_per_ft` | number | Estimated trenching cost per foot. | Cost assumption. |
| `service_upgrade_cost_usd` | number | Estimated service upgrade cost in U.S. dollars. | Placeholder/manual assumption. |
| `ada_layout_possible` | yes/no number | Whether ADA-accessible layout appears possible. `1` means likely possible. `0` means unresolved or problematic. | Planning/site-review assumption. |
| `fire_access_ok` | yes/no number | Whether fire apparatus access appears acceptable at model level. `1` means no obvious issue. `0` means concern. | Planning/site-review assumption. |
| `garage_enclosed` | yes/no number | Whether the site is an enclosed garage or has garage-like limitations. `1` means garage/enclosed. | Site type/facility assumption. |
| `emergency_disconnect_visible` | yes/no number | Whether emergency disconnect visibility has been confirmed. `1` means confirmed. `0` means not confirmed. | Usually unknown in V1. |
| `stormwater_risk` | yes/no number | Whether stormwater or firefighting runoff concern is flagged. `1` means concern. | Planning/site-review assumption. |
| `battery_storage_flag` | yes/no number | Whether battery storage is present or proposed. `1` means yes. | Project design input or placeholder. |
| `battery_storage_kwh` | number | Battery storage size in kilowatt-hours, if present. | Project design input or placeholder. |
| `notes` | text | Plain-language notes explaining data sources, assumptions, uncertainty, or stakeholder context. | Project notes. |

## site_results.csv output columns

`site_results.csv` is created when the script runs.

| Column | Type | Meaning |
|---|---:|---|
| `site_id` | text | Site ID copied from the input dataset. |
| `site_name` | text | Site name copied from the input dataset. |
| `site_type` | text | Site type copied from the input dataset. |
| `public_access` | number | Cleaned public-access value used by the model. `1` means public access; `0` means limited/non-public. |
| `access_adjustment` | number | Public-access multiplier used to discount limited-access sites as public charging priorities. Current values: `1.00` for public sites and `0.35` for limited-access sites. |
| `readiness_score` | number | Final weighted site-readiness score after public-access adjustment. Higher means stronger public charging priority. |
| `demand_subscore` | number | Demand score after public-access adjustment. Higher means stronger demand indicators. |
| `feasibility_subscore` | number | Feasibility score. Higher means easier to build based on current assumptions. |
| `safety_subscore` | number | Safety/site-review score. Higher means fewer model-level concerns. |
| `expected_sessions_day` | number | Estimated charging sessions per day. This is separate from readiness score. |
| `recommended_ports_now` | number | Recommended starter number of charging ports for the current period. |
| `recommended_ports_2035` | number | Recommended ports under the 2035 growth scenario. |
| `recommended_ports_2050` | number | Recommended ports under the 2050 growth scenario. |
| `estimated_utilization` | number | Estimated utilization for the recommended current port count. |
| `mean_wait_min` | number | Estimated mean wait time in minutes for the recommended current port count. |
| `install_cost_est_usd` | number | Estimated install cost from trenching plus service upgrade cost. |
| `ahj_review_flag` | yes/no number | `1` means the site has at least one model-level review trigger. `0` means no obvious trigger from the current fields. |
| `review_reason` | text | Plain-English explanation of why review was triggered. |

## Derived/internal model fields

Some fields are created inside the Python script but may not appear in the final output table.

| Field | Meaning |
|---|---|
| `existing_ports_total` | Sum of Level 2 ports within 1 mile and DC fast ports within 3 miles. Used as a competition/saturation signal. |
| `install_cost_est_usd` | `trenching_ft * trench_cost_per_ft + service_upgrade_cost_usd`. This field is included in the output. |
| `readiness_access_adjustment` | Final readiness multiplier for limited-access sites. Current values: `1.00` for public sites and `0.65` for limited-access sites. |
| `base_readiness_score` | Readiness score before the final public-access discount. |
| `_n` columns | Normalized 0-to-1 versions of selected numeric columns, created internally for scoring. |
| `avg_session_hr` | Average charging session duration in hours, selected from site-type behavior assumptions. |
| `target_utilization` | Utilization threshold selected from site-type behavior assumptions. |

## Score interpretation

Use the scores as planning signals, not final decisions.

```text
Higher readiness_score = stronger public charging priority.
Higher demand_subscore = stronger demand indicators.
Higher feasibility_subscore = easier to build based on current assumptions.
Higher safety_subscore = fewer model-level review concerns.
```

A site can have a good readiness score and still require review. For example, a public library may be a strong demand location but still have `Emergency disconnect visibility not confirmed` because that design detail has not been verified.

## Important limitations

The current model still has placeholder or early-assumption fields. The most important ones to improve are:

```text
employees_day
visitors_day
parking_spaces
hours_open
amenities_count_0_5mi
ev_share_local
equity_gap_index
spare_capacity_kw
distance_to_service_ft
trenching_ft
service_upgrade_cost_usd
ada_layout_possible
fire_access_ok
emergency_disconnect_visible
stormwater_risk
battery_storage_flag
battery_storage_kwh
```

`amenities_count_0_5mi` is now populated with manual V1 category estimates, but it should still be improved later with GIS/POI data.

Any real site decision should be checked with the appropriate AHJ, Fire Marshal, ADA/accessibility reviewers, utility, stormwater staff, engineers, and permitting offices.
