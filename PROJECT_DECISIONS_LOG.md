# Project Decisions Log

This file keeps the major project decisions in one place so assumptions, source quality, model changes, and replacement targets are not lost as the prototype evolves.

The project is a planning-support prototype for public EV charging site readiness and right-sizing in Fairfax City and Prince William County. It does not replace engineering, utility, ADA, Fire Marshal, AHJ, stormwater, or permitting review.

## Source quality labels

```text
Official = direct value from an official source
Official-derived = calculated from official source data
Manual estimate = manual V1 estimate that should be improved later
Planning estimate = project-created estimate used to reduce placeholder zeros
Planning proxy = temporary proxy when official local data is not accessible
Placeholder = unresolved value intentionally left for future confirmation
```

## Current model files

```text
ev_charger_model.py
validate_site_data.py
real_sites_v1.csv
site_results.csv
data_quality_report.csv
```

## Current source/documentation files

```text
METHODOLOGY.md
PROJECT_STATUS.md
RESULTS_INTERPRETATION.md
DATA_DICTIONARY.md
data/source_dataset_log.csv
data/dataset_metadata.csv
data/raw_exports/README.md
data/source_extracts/
```

## Decision 1 — Use real candidate sites as the default input

Decision: `real_sites_v1.csv` is the default model input.

Reason: Phase 2 should use real candidate sites instead of only starter/demo rows.

Affected files:

```text
real_sites_v1.csv
ev_charger_model.py
validate_site_data.py
site_results.csv
```

Source quality: mixed official, official-derived, manual estimate, planning estimate, planning proxy, and placeholder fields.

Replacement target: improve individual fields as stronger data becomes available.

## Decision 2 — Keep large raw exports out of the repo

Decision: The repo stores small model-ready extracts and documentation, not every large raw file.

Reason: Some raw files are large, and the model only needs processed values.

Affected files:

```text
data/raw_exports/README.md
data/source_extracts/
data/source_dataset_log.csv
data/dataset_metadata.csv
```

Source quality: documentation / repo management decision.

Replacement target: keep documenting raw exports used and store only useful small extracts.

## Decision 3 — Address and coordinate verification

Decision: Candidate-site addresses and coordinates are based on official GIS address sources when available.

Sources:

```text
City of Fairfax GeoHub Addresses
Prince William County GIS Premise Addresses
```

Affected fields:

```text
address
city
state
zip
lat
lon
```

Source quality: Official.

Replacement target: update only if the site list changes or better facility-specific coordinates are provided.

## Decision 4 — Existing nearby EV charging supply

Decision: Nearby public active charging ports are counted from AFDC / NREL Alternative Fuel Stations exports.

Rules:

```text
Level 2 ports counted within 1 mile
DC fast ports counted within 3 miles
Only public active electric stations counted
```

Affected fields:

```text
existing_l2_ports_1mi
existing_dcfc_ports_3mi
```

Source quality: Official.

Replacement target: refresh AFDC export later if updated charger supply is needed.

## Decision 5 — Traffic demand signal

Decision: `aadt_nearest` uses the nearest VDOT Bidirectional Traffic Volume 2025 segment.

Affected field:

```text
aadt_nearest
```

Source quality: Official.

Replacement target: refresh with newer VDOT data when available.

## Decision 6 — Nearby households

Decision: `nearby_households_1mi` is estimated from ACS 2024 5-Year B11001 and TIGER 2024 Virginia block group geometry.

Method: area-weighted 1-mile block group intersection.

Affected field:

```text
nearby_households_1mi
```

Source quality: Official-derived.

Replacement target: improve with smaller geography or better allocation method if needed.

## Decision 7 — Nearby jobs

Decision: `nearby_jobs_1mi` is estimated from LODES 2023 Virginia Workplace Area Characteristics.

Method: workplace block jobs aggregated to block groups, then area-weighted to 1-mile site buffers.

Affected field:

```text
nearby_jobs_1mi
```

Source quality: Official-derived.

Replacement target: refresh with newer LODES data when available.

## Decision 8 — Amenities within 0.5 miles

Decision: `amenities_count_0_5mi` is a manual V1 public-use category count.

Reason: It gives the model a public-use context signal before a stronger GIS/POI method is built.

Affected field:

```text
amenities_count_0_5mi
```

Source quality: Manual estimate.

Replacement target: replace with GIS/POI data such as OpenStreetMap, local GIS amenities, or another documented source.

## Decision 9 — Demand assumptions and parking

Decision: `employees_day`, `visitors_day`, `parking_spaces`, `hours_open`, and `avg_dwell_min` are V1 planning assumptions.

Reason: They allow the right-sizing model to run while official facility counts or stakeholder estimates are still unavailable.

Affected fields:

```text
employees_day
visitors_day
parking_spaces
hours_open
avg_dwell_min
```

Source quality: Manual estimate.

Replacement target: replace with official facility counts, observed use, stakeholder estimates, or documented manual counts.

## Decision 10 — Parking has a low demand weight

Decision: Parking is included in the demand subscore, but only with a 0.09 weight.

Reason: Current parking values are manual V1 estimates, not official verified counts.

Affected model area:

```text
demand_subscore
```

Source quality: model weighting decision.

Replacement target: revisit the parking weight once parking counts are official or strongly verified.

## Decision 11 — ACS equity index

Decision: `equity_gap_index` is official-derived from ACS 2024 5-Year block group indicators and TIGER 2024 geometry.

Inputs:

```text
B19013 median household income
B25044 no-vehicle households
B25003 renter occupancy
B25024 multifamily housing
TIGER 2024 Virginia block groups
```

Method: 1-mile area-weighted block group estimate. Median household income is approximated by household-weighted block group medians because medians are not additive.

Affected files:

```text
data/source_extracts/acs_equity_inputs_1mi.csv
data/source_extracts/acs_equity_index_1mi.csv
real_sites_v1.csv
```

Source quality: Official-derived.

Replacement target: improve median-income method later if a stronger small-area method is needed.

## Decision 12 — Use B25044 instead of B08201 for no-vehicle households

Decision: B25044 is used for no-vehicle households.

Reason: The downloaded B08201 block-group export returned blank vehicle fields during the prototype step.

Affected field:

```text
no_vehicle_household_share
```

Source quality: Official Census table used as replacement.

Replacement target: revisit only if B08201 becomes usable or a better official vehicle-access source is found.

## Decision 13 — Electrical feasibility V1 planning estimates

Decision: Distance, trenching, trench cost, and service-upgrade cost now use conservative planning-level estimates instead of zeros.

Affected fields:

```text
distance_to_service_ft
trenching_ft
trench_cost_per_ft
service_upgrade_cost_usd
```

Fields intentionally left unresolved:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
```

Source quality: Planning estimate.

Replacement target: replace with facility, utility, site review, or engineering-confirmed values.

## Decision 14 — Garage context remains high review

Decision: Neabsco-Potomac Commuter Garage remains high-review because garage installations can involve extra ventilation, access, fire-response, conduit-routing, and emergency-disconnect questions.

Affected site:

```text
PWC002 — Neabsco-Potomac Commuter Garage
```

Source quality: planning/safety interpretation.

Replacement target: confirm with Prince William County facilities staff, Fire Marshal/AHJ, and utility review.

## Decision 15 — Local EV adoption V1 proxy

Decision: `ev_registrations_local` and `ev_share_local` now use locality-level proxy values.

Values:

```text
Prince William County sites: ev_registrations_local = 8000; ev_share_local = 0.018
Fairfax City sites: ev_registrations_local = 500; ev_share_local = 0.023
```

Reason: A current statewide Virginia EV benchmark was found, but an accessible official locality-level DMV EV registration CSV for Fairfax City and Prince William County was not found during the prototype step.

Source quality: Planning proxy.

Replacement target: replace with official DMV, locality, Virginia Clean Cities, Atlas Public Policy, or other documented locality-level EV registration data if available.

## Decision 16 — EV share uses benchmark scaling, not min-max scaling

Decision: `ev_share_local` is scaled against a fixed 10 percent high-adoption benchmark.

Formula:

```text
ev_share_signal = min(ev_share_local / 0.10, 1.0)
```

Reason: Min-max scaling would exaggerate small differences in a six-site dataset. For example, 1.8 percent versus 2.3 percent should not become a full 0-to-1 split.

Affected model area:

```text
demand_subscore
```

Source quality: model normalization decision.

Replacement target: recalibrate the benchmark if stronger regional/local EV adoption data becomes available.

## Decision 17 — Public access adjustment

Decision: Limited or non-public sites stay in the dataset but are discounted.

Current logic:

```text
public_access = 1 -> access_adjustment = 1.00
public_access = 0 -> access_adjustment = 0.35
public_access = 1 -> readiness_access_adjustment = 1.00
public_access = 0 -> readiness_access_adjustment = 0.65
```

Affected site:

```text
PWC003 — Prince William County Public Safety Training Center
```

Source quality: model logic decision.

Replacement target: confirm whether the site should be public charging, fleet/support charging, or excluded from the public-charging candidate list.

## Decision 18 — Port recommendations are starter planning estimates

Decision: Recommended ports are based on expected sessions, dwell time, hours open, utilization, and a simple queueing check.

Method: The model chooses the smallest number of ports that keeps utilization and mean wait below targets.

Source quality: model logic decision.

Replacement target: recalibrate with observed charger use, session data, or stakeholder planning targets.

## Current unresolved items

The main unresolved fields are:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
hours_open
parking_spaces
amenities_count_0_5mi
```

The most important next confirmations are:

```text
1. Facility or utility electrical service data
2. Spare capacity or upgrade requirement
3. Emergency disconnect location / visibility
4. Better visitor, employee, parking, and hours support
5. Better local EV adoption counts if official locality data becomes available
6. Better amenities / POI method
```

## Current latest model ranking after local EV adoption proxy

```text
1. FFX002 — City of Fairfax Regional Library: 59.8
2. FFX001 — Fairfax City Hall or municipal building: 53.1
3. PWC004 — Chinn Park Regional Library: 46.5
4. PWC002 — Neabsco-Potomac Commuter Garage: 43.2
5. PWC001 — PWC McCoart Government Center: 40.1
6. PWC003 — Prince William County Public Safety Training Center: 18.6
```

## Maintenance rule

Whenever the project changes a source, assumption, formula, or output interpretation, update this file along with the affected source extract, metadata, methodology, and status documents.
