# Data Sources and Field Plan

This file tracks where each input in `sites.csv` should come from.

The goal is to keep the EV charging site-readiness model transparent and defensible. Some fields can come from official datasets, while other fields require manual review, stakeholder input, or site assumptions.

## Source quality levels

| Level | Meaning | Use in model |
|---|---|---|
| Official | Comes from a government, DOE/NLR, Census, VDOT, or local government source | Best source for model inputs |
| Stakeholder evidence | Comes from interviews or project notes | Useful for known site constraints and calibration |
| Manual estimate | Estimated from maps, site review, assumptions, or early planning judgment | Acceptable for prototype, but should be labeled |
| Unknown | Not available yet | Keep blank or use conservative placeholder |

## Priority official sources

### 1. DOE / AFDC / NLR Alternative Fuel Stations

Use for existing EV charger supply near each candidate site.

Official pages:
- https://afdc.energy.gov/stations
- https://developer.nlr.gov/docs/transportation/alt-fuel-stations-v1/

Model fields supported:
- `existing_l2_ports_1mi`
- `existing_dcfc_ports_3mi`
- station names near the site
- station latitude and longitude
- access type
- EV network
- connector / charging information

Notes:
- This should be the first official dataset added because it directly supports EV charging competition/supply around each candidate site.
- The API includes station searches, nearest station searches, and EV charging port CSV output.

### 2. U.S. Census ACS 5-Year

Use for demographic and equity context.

Official page:
- https://www.census.gov/data/developers/data-sets/acs-5year.html

Model fields supported:
- `nearby_households_1mi`
- population context
- renter share
- median income
- vehicle access
- possible future equity-gap variables

Notes:
- ACS 5-year estimates are available down to census tracts and block groups.
- Census API requests require an API key.
- For the first prototype, use ACS as an official source for equity and household context.

### 3. U.S. Census LEHD LODES

Use for workplace/job density around candidate sites.

Official page:
- https://lehd.ces.census.gov/data/

Model fields supported:
- `nearby_jobs_1mi`
- employment density near the site
- workplace activity around public buildings, garages, and community facilities

Notes:
- LODES files are state-based.
- The useful file type for this model is Workplace Area Characteristics.

### 4. VDOT / Virginia Roads Traffic Volume

Use for traffic exposure near candidate sites.

Official page:
- https://www.virginiaroads.org/datasets/VDOT::traffic-volume/about

Model fields supported:
- `aadt_nearest`

Notes:
- AADT means Annual Average Daily Traffic.
- This is useful because traffic volume near a site can be a demand proxy.

### 5. Local government facility pages and GIS

Use for candidate site names and addresses.

Possible sources:
- Prince William County official facility pages
- Fairfax City official facility pages
- library system pages
- public works / public safety / government center pages
- local GIS open data if available

Model fields supported:
- `site_name`
- `site_type`
- `address`
- `city`
- `state`
- `zip`
- `lat`
- `lon`
- `public_access`
- `hours_open`
- `parking_spaces` if published

Notes:
- If parking or hours are not published, mark them as manual estimates in the `notes` field.

## Fields that likely need manual or stakeholder inputs

These fields are important but are usually not available in open public datasets:

- `spare_capacity_kw`
- `distance_to_service_ft`
- `trenching_ft`
- `trench_cost_per_ft`
- `service_upgrade_cost_usd`
- `ada_layout_possible`
- `fire_access_ok`
- `garage_enclosed`
- `emergency_disconnect_visible`
- `stormwater_risk`
- `battery_storage_flag`
- `battery_storage_kwh`

How to handle them in the prototype:
- Use stakeholder interview evidence when available.
- Use conservative manual assumptions when necessary.
- Explain uncertain inputs clearly in the `notes` column.
- Do not present these fields as official engineering determinations unless verified by the appropriate office.

## Field-by-field plan for `sites.csv`

| Field | Planned source | Source quality | Notes |
|---|---|---|---|
| `site_id` | Project-created ID | Manual estimate | Use short stable IDs like PWC001 or FFX001 |
| `site_name` | Local government / facility page | Official | Public facility name |
| `site_type` | Project classification | Manual estimate | library, office, garage, clinic, fleet, community center, public safety |
| `address` | Local government / facility page | Official | Use official address where possible |
| `city` | Local government / facility page | Official |  |
| `state` | Local government / facility page | Official | Usually VA |
| `zip` | Local government / facility page | Official |  |
| `lat` | Geocoded from official address | Manual estimate / official if GIS | Can improve later with GIS coordinates |
| `lon` | Geocoded from official address | Manual estimate / official if GIS | Can improve later with GIS coordinates |
| `public_access` | Facility page / site knowledge | Official or manual estimate | 1 if public can access site |
| `employees_day` | Facility estimate / stakeholder input | Manual estimate | Hard to get officially |
| `visitors_day` | Facility estimate / stakeholder input | Manual estimate | Hard to get officially |
| `fleet_vehicles` | Stakeholder input / fleet plan | Stakeholder evidence or manual estimate | Use 0 if not a fleet site |
| `parking_spaces` | Site page, GIS, or manual count | Official or manual estimate |  |
| `hours_open` | Facility page | Official | If unknown, estimate and mark notes |
| `avg_dwell_min` | Site-type assumption | Manual estimate | Based on library, garage, office, clinic, etc. |
| `nearby_households_1mi` | Census ACS | Official | Later automate by tract/block-group approximation |
| `nearby_jobs_1mi` | Census LEHD LODES | Official | Later automate by block aggregation |
| `aadt_nearest` | VDOT / Virginia Roads | Official | Nearest traffic segment |
| `amenities_count_0_5mi` | OpenStreetMap / manual map count | Public/open data or manual estimate | Not government official unless using local GIS |
| `ev_registrations_local` | State/local registration source if available | Official if found | Optional for later |
| `ev_share_local` | State/local registration source or regional assumption | Official or manual estimate | Use same assumption for v1 if needed |
| `existing_l2_ports_1mi` | AFDC / NLR Alternative Fuel Stations | Official | Count public L2 ports within 1 mile |
| `existing_dcfc_ports_3mi` | AFDC / NLR Alternative Fuel Stations | Official | Count public DC fast ports within 3 miles |
| `equity_gap_index` | ACS-derived index | Official-derived / project-created | Project-created score using official ACS variables |
| `elec_service_voltage` | Facility/utility data | Manual estimate | Often unknown publicly |
| `elec_service_rating_amp` | Facility/utility data | Manual estimate | Often unknown publicly |
| `spare_capacity_kw` | Facility/utility/stakeholder input | Stakeholder evidence or manual estimate | Important uncertainty field |
| `distance_to_service_ft` | Site map / facility input | Manual estimate | Distance from charger location to electrical service |
| `trenching_ft` | Site map / facility input | Manual estimate | Important cost driver |
| `trench_cost_per_ft` | Cost assumption | Manual estimate | Keep constant for prototype unless better data found |
| `service_upgrade_cost_usd` | Facility/utility/stakeholder input | Stakeholder evidence or manual estimate | Important cost driver |
| `ada_layout_possible` | Site review / ADA review | Manual estimate | 1 if likely possible, 0 if unresolved/problematic |
| `fire_access_ok` | Fire/AHJ/site review | Manual estimate | Do not treat as official without review |
| `garage_enclosed` | Site type / facility page | Official or manual estimate | Garages require extra review |
| `emergency_disconnect_visible` | Site review | Manual estimate | Often unknown until design stage |
| `stormwater_risk` | Site review / local stormwater context | Manual estimate | Especially important for runoff concerns |
| `battery_storage_flag` | Project design input | Manual estimate | 1 if storage is proposed/present |
| `battery_storage_kwh` | Project design input | Manual estimate | 0 if none |
| `notes` | Project notes | Manual / stakeholder evidence | Explain uncertain assumptions and interview evidence |

## Near-term dataset plan

Start with 6 to 8 candidate sites:

1. PWC McCoart Building
2. Neabsco Commuter Garage
3. Crisis Receiving Center or similar public health facility
4. Fairfax City public building
5. Public library
6. Community center
7. Public works or fleet facility
8. Public safety facility

For version 1, the most important rule is honesty:
- Official values should be marked as official.
- Estimated values should be clearly marked as estimates.
- Unknown safety/electrical values should not be presented as verified.

## Next implementation step

Create a `real_sites_v1.csv` or update `sites.csv` with real candidate sites, using this data-source plan as the guide.
