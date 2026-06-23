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
Official and official-derived coordinates added.
Existing nearby charger supply added from AFDC/NREL.
VDOT AADT traffic signal added.
ACS households and equity index added.
LODES jobs signal added.
Demand assumptions added and documented.
Official FFX002 facility hours and parking added.
Official PWC004 current renovation status documented.
PWC004 future/reopened planning assumption confirmed.
Reviewed OSM/Overpass amenities count added and applied.
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
PWC002 remains important but high-review because of garage context.
PWC001 improved from the reviewed OSM amenities update but remains below stronger candidates.
PWC003 is low public-priority unless its access or use case changes.
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

Optional OSM amenities workflow:

```bash
python src/build_osm_amenities.py --pause 15 --retries 4 --retry-wait 30
```

## Next good improvements

```text
1. Re-run the validator, model, and sensitivity analysis after the reviewed amenities update.
2. Replace visitor, employee, parking, and electrical assumptions with stronger site data when available.
3. Improve facility hours and parking for sites other than FFX002.
4. Add or improve map and visual outputs.
5. Prepare slides from docs/PRESENTATION_OUTLINE.md.
6. Add more candidate sites if the project scope expands.
```
