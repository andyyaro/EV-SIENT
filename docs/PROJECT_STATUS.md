# Project Status

## Current phase

Phase 2 prototype development for the Public EV Charging Site-Readiness and Right-Sizing Model.

## Current repo structure

```text
src/                  Python scripts
data/inputs/           Input datasets
data/source_extracts/  Small source extracts
data/outputs/          Generated outputs ignored by Git
docs/                  Documentation and reporting
```

## Completed so far

```text
Real candidate sites added.
Official/official-derived coordinates added.
Existing nearby charger supply added from AFDC/NREL.
VDOT AADT traffic signal added.
ACS households and equity index added.
LODES jobs signal added.
Demand assumptions added and documented.
Planning electrical feasibility estimates added.
Local EV adoption proxy added.
Sensitivity analysis added and strengthened.
Recommendation tier layer added.
Findings brief and presentation outline added.
Repository reorganized into cleaner folders.
```

## Current strongest findings

```text
FFX002 and FFX001 are stable top candidates.
PWC004 is the strongest current PWC public-library candidate.
PWC002 remains important but high-review because of garage context.
PWC003 is low public-priority unless its access/use case changes.
```

## Remaining data improvements

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
hours_open
parking_spaces
amenities_count_0_5mi
local EV adoption counts
```

## Current run commands

```bash
python src/validate_site_data.py
python src/ev_charger_model.py
python src/run_sensitivity_analysis.py
```

## Next good improvements

```text
1. Confirm electrical/service capacity with facility or utility contacts.
2. Replace visitor/employee/parking assumptions with stronger site data.
3. Add or improve map/visual outputs.
4. Prepare slides from docs/PRESENTATION_OUTLINE.md.
5. Add more candidate sites if the project scope expands.
```
