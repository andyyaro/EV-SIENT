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
Official FFX002 facility hours and parking added.
Official PWC004 current renovation status documented.
Planning electrical feasibility estimates added.
Local EV adoption proxy added.
Sensitivity analysis added and strengthened.
Recommendation tier layer added.
Findings brief, full findings report, and presentation outline added.
Stakeholder data request pack added.
Repository reorganized into cleaner folders.
```

## Current strongest findings

```text
FFX002 and FFX001 are stable top candidates.
PWC004 is the strongest current PWC public-library candidate under future/reopened planning assumptions.
PWC004's current official renovation closure needs a project scope decision.
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
hours_open for sites except FFX002
parking_spaces for sites except FFX002
amenities_count_0_5mi
local EV adoption counts
```

## Current stakeholder request files

```text
docs/STAKEHOLDER_DATA_REQUEST.md
data/source_extracts/stakeholder_data_request_fields.csv
```

Use these files to ask facility, utility, public works, parking, ADA/accessibility, Fire Marshal/AHJ, GIS, and planning contacts for the data needed to replace assumptions and placeholders.

## Current run commands

```bash
python src/validate_site_data.py
python src/ev_charger_model.py
python src/run_sensitivity_analysis.py
```

## Next good improvements

```text
1. Decide whether PWC004 should be modeled as current closed status or future reopened site conditions.
2. Continue public-data upgrades for facility hours, parking, public access, and amenities.
3. Replace visitor/employee/parking/electrical assumptions with stronger site data when responses arrive.
4. Re-run the validator, model, and sensitivity analysis after each major data update.
5. Add or improve map/visual outputs.
6. Prepare slides from docs/PRESENTATION_OUTLINE.md.
7. Add more candidate sites if the project scope expands.
```
