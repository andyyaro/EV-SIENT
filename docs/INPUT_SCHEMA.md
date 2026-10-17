# Running EV-SIENT on your own sites

[← repository root](../README.md)

The model was built on one study: twelve candidate sites in Fairfax City and Prince William
County. Since 2026-10-17 it also runs on anyone else's sites. You bring a spreadsheet in
whatever shape you have; **intake** reads it, tells you cell by cell what it would do, and
writes a **cohort** directory only after you accept; `run --cohort` scores it, sizes the
ports and writes the same validated contract the reference study gets.

One rule governs all of it: **a value nobody recorded earns no credit, and is never replaced
by a guess** (DEC-011). A file with gaps produces a run with low confidence and lower scores,
not a refusal and not a confident answer.

The machine-readable version of this page is
[`data/schema/input_schema_v1.json`](../data/schema/input_schema_v1.json).

## Quick start

```bash
pip install -e .                                   # once, from the repository root

# 1. Look first. This prints every reading and finding and writes NOTHING.
python -m fcf_m2.workflow intake your_sites.csv --out cohorts/your-city

# 2. If the readings are right, accept them. This writes the cohort directory.
python -m fcf_m2.workflow intake your_sites.csv --out cohorts/your-city --accept \
    --jurisdiction "Your City" --source-date 2026-10-01 --source-org "Your agency"

# 3. Run the model on it, then check the contract it wrote.
python -m fcf_m2.workflow run --cohort cohorts/your-city
python -m fcf_m2.workflow validate-contract cohorts/your-city/outputs/<run>/contract
```

To start from nothing, fill in [`data/intake/template_sites.csv`](../data/intake/template_sites.csv):
one header row with every field the model reads, in the canonical names.

## What intake does to your file

| Step | What happens | How you are told |
|---|---|---|
| Column names | Matched to the canonical names below by name and by a hand-written list of aliases (`staff` is `employees_day`). A match that is a guess is flagged. A name too unlike any field is left unmapped, and that field is absent. | warning per guessed match; note per absent field |
| Units | Converted only where the column name says so, and only for the five fields marked "recognised and converted" below: metres to feet for the two distances (`_m`), hours or seconds to minutes for visit length (`_hr`, `_sec`), minutes to hours for opening hours (`_min`), watts or megawatts to kilowatts for spare capacity (`_w`, `_mw`). Each is one multiplication. | warning per conversion |
| Cells | `1,400` and `$45,000` are read as numbers. A blank, `n/a`, `unknown`, `-` or `tbd` is absent, never 0 and never "no". Anything else that is not a value (`about 50`, `partial`) is absent too. | note or warning per field, naming the file rows |
| Refused | No site identifier, a repeated or blank one, or coordinates that are not latitude and longitude (projected coordinates are never converted). | refusal; nothing is written |

Every change is written to `intake_ledger.csv` in the cohort, every finding to
`intake_findings.json`, and the file's SHA-256 to `cohort.json`, so a run can always be traced
back to the exact file it came from.

## A cohort directory

| File | Required | What it holds | If it is missing |
|---|---|---|---|
| `sites.csv` | **yes** | One row per site: the fields in the next section | the cohort cannot run |
| `electrical_risk.csv` | no | `site_id`, `electrical_risk_level` (`low`, `medium` or `high`). `high` holds a site to 2 starter ports and smaller expansion targets until an electrical review | every site is `medium`, the right-sizing default |
| `site_meta.csv` | no | `site_id`, `arrival_start_hr`, `arrival_end_hr`, `base_load_mean_kw`, `base_load_peak_kw` | arrivals run from 08:00 for each site's opening hours (8 h where not recorded); the base load is left unknown, not invented |
| `provenance.csv` | no | Where each group of figures came from (`source_class`, `verification_status`, ...), the shape of `data/provenance/field_provenance_v1.csv` | every group is `unconfirmed`, so data confidence is Low. Intake writes one for you |
| `cohort.json` | no | `cohort_id`, `jurisdiction`, `source_date` (YYYY-MM-DD), `source_org` | named after the directory; source date `unstated`, which costs confidence |

Every default a run used is written as a sentence in its `run_summary.json` and in the
contract manifest's `cohort.defaults`.

## The fields of `sites.csv`

Only `site_id` is required. Leave a cell blank when nobody knows; the yes/no fields take
`yes`/`no`, `1`/`0` or `true`/`false`.

| Field | Unit | In the score | What it is | If blank or absent |
|---|---|---|---|---|
| `site_id` | identifier | no | A unique, stable identifier for the site. Letters, digits, '.', '_' and '-'. | the file is refused |
| `site_name` | text | no | Display name. Not a model input. | the site_id is shown instead |
| `site_type` | text | no | What the building is, e.g. library, office, recreation, garage. A type containing 'garage' is routed to fire/AHJ review before any normal buildout. | 'unspecified' |
| `lat` | degrees | no | Latitude, WGS84 decimal degrees. Projected coordinates are refused, never converted. | the map surfaces are unavailable; nothing else changes |
| `lon` | degrees | no | Longitude, WGS84 decimal degrees. | the map surfaces are unavailable; nothing else changes |
| `employees_day` | people/day | no | Staff on site on a typical day. Drives expected charging sessions, not the score. | counts as 0 expected sessions from staff |
| `visitors_day` | people/day | no | Visitors on a typical day. Drives expected charging sessions, not the score. | counts as 0 expected sessions from visitors |
| `fleet_vehicles` | vehicles | no | Fleet vehicles based at the site. Read and carried, not used. | nothing changes |
| `parking_spaces` | spaces | yes | Parking spaces at the site. Also caps the port plan at 5% of spaces (2 to 12). | earns no credit, and the port plan is capped at 2 |
| `hours_open` | hours/day | yes | Hours the site is open on a typical day. A '_min' column is recognised and converted. | earns no credit; port sizing assumes 8 hours |
| `avg_dwell_min` | minutes | yes | Average length of a visit. An '_hr' or '_sec' column is recognised and converted. | earns no credit; port sizing assumes 120 minutes |
| `nearby_households_1mi` | households | yes | Households within 1 mile. | earns no credit in the score |
| `nearby_jobs_1mi` | jobs | yes | Jobs within 1 mile. | earns no credit in the score |
| `aadt_nearest` | vehicles/day | yes | Annual average daily traffic on the nearest arterial. | earns no credit in the score |
| `amenities_count_0_5mi` | count | yes | Amenities (shops, services) within half a mile. | earns no credit in the score |
| `ev_share_local` | fraction | yes | Share of locally registered vehicles that are electric, as a fraction: 0.03 means 3%. | earns no credit in the score |
| `existing_l2_ports_1mi` | ports | yes | Public Level 2 charging ports already within 1 mile. Lower is better. | earns no credit in the score |
| `existing_dcfc_ports_3mi` | ports | yes | Public DC fast charging ports already within 3 miles. Lower is better. | earns no credit in the score |
| `equity_gap_index` | index 0-1 | yes | Charging-equity need, 0 (least) to 1 (most underserved). | earns no credit; the contract's equity_indicator is left empty |
| `spare_capacity_kw` | kW | yes | Spare electrical capacity at the service. Used in the score, but the contract reports capacity as a placeholder until a utility or facility confirms it. Watts and megawatts are recognised and converted. | earns no credit in the score |
| `distance_to_service_ft` | feet | yes | Distance from the parking area to the electrical service. Lower is better. Metres are recognised and converted. | earns no credit in the score |
| `trenching_ft` | feet | yes | Trenching needed. Lower is better. Metres are recognised and converted. | earns no credit, and the site gets no cost figures |
| `trench_cost_per_ft` | USD/foot | yes | Trenching cost per foot. | the install-cost term earns no credit, and the site gets no cost figures |
| `service_upgrade_cost_usd` | USD | yes | Cost of upgrading the electrical service. Lower is better. | earns no credit, and the site gets no cost figures |
| `elec_service_rating_amp` | amps | no | Rating of the electrical service. Read and carried, not used. | nothing changes |
| `public_access` | yes/no | yes | Is the site open to the public? | treated as not public: demand counts at 65%, the 'Low public-priority' tier, and every port target held to 2 |
| `ada_layout_possible` | yes/no | yes | Can an ADA-accessible charging layout be built? | earns no credit in the score |
| `fire_access_ok` | yes/no | yes | Is fire-service access adequate? | earns no credit in the score |
| `garage_enclosed` | yes/no | yes | Is the parking an enclosed garage? Yes lowers the safety score. | earns no safety credit, and the site is a 'High-review candidate' |
| `emergency_disconnect_visible` | yes/no | yes | Is an emergency disconnect visible from the charging area? | earns no credit in the score |
| `stormwater_risk` | yes/no | yes | Is there a stormwater or flooding risk? Yes lowers the safety score. | earns no safety credit |
| `battery_storage_flag` | yes/no | no | Is battery storage on site? Read and carried, not used. | nothing changes |

## When a value is missing

| What is missing | What the model does |
|---|---|
| Any field in the score | The term earns 0. For the six "lower is better" terms (existing ports, service distance, install cost, trenching, enclosed garage, stormwater risk) that is the change: an absent value used to earn their **maximum** |
| `public_access` | Treated as not public, as a recorded "no" is: demand counts at 65%, the tier is "Low public-priority", every port target is held to 2 and the plan is not to advance a general public buildout |
| `garage_enclosed` | No safety credit, and the site is a "High-review candidate" until someone checks |
| `parking_spaces` | The port plan is capped at 2, the smallest cap. A counted 40-space lot also gets 2 |
| `hours_open`, `avg_dwell_min` | No score credit; port sizing assumes 8 hours a day and 120-minute visits |
| `trenching_ft`, `trench_cost_per_ft` or `service_upgrade_cost_usd` | The site gets **no cost figures**: costed with the gap as 0 it would look cheaper than a site that was measured |
| `equity_gap_index` | No equity credit; the contract's `equity_indicator` is empty |
| `employees_day`, `visitors_day` | Not in the score; the site's expected charging sessions count none from staff or visitors, so its port plan can only shrink |

Both site results files (`site_results_*.csv`) carry an `absent_fields` column naming each
site's gaps.

## What the results mean, and what they do not

- **Scores** use fixed anchors, so a site gets the same score whichever other sites are in
  the run, and scores can be compared across cohorts. The anchors were set for the reference
  study's region; they were not calibrated to yours.
- **Tiers are relative to the cohort.** Tier 1 needs rank 2 or better, so at most two sites
  in any run can hold it (`config.TIER1_MAX_RANK`). Compare scores across cohorts, never tiers.
- **Port plans follow the ranking your results show**: the fixed-anchor one, the same ranks
  and tiers as `site_results_milestone2_v3.csv`. The reference study is the one exception.
  Its plans follow its accepted cohort-relative (legacy) ranking, deliberately, so the totals
  it presented reconcile; on the fixed-anchor ranking the same rules give 25 / 47 instead of
  25 / 48 (F-05). The manifest's `cohort.plan_ranking` says which one a run used.
- **Every site gets at least 2 starter ports**, including one the plan says not to advance
  (a non-public site). Read those 2 as a placeholder for a decision, not a recommendation.
- **Electrical capacity is a placeholder at every site.** The score uses the
  `spare_capacity_kw` you supplied, but the contract's capacity fields stay empty and marked
  `placeholder` on every row until a utility or facility confirms them.
- **Data confidence is Low** until the jurisdiction supplies provenance for its own figures.
  Accepting intake's mapping confirms what the columns mean, not that the figures are right.
- **Some constants belong to the reference study's region.** The standards register lists
  the editions Virginia has adopted; CO2e uses the EPA eGRID factor for its grid subregion
  (SRVC); costs use its screening tariff and cost classes. Confirm or replace each before
  quoting it. A cohort's manifest repeats this in `cohort.notes`.
- **RT-04's 25 starter / 48 pathway totals belong to the reference study.** They are asserted
  only when a run reads the reference study's own inputs (`contract.REFERENCE_INPUTS`), and
  never against another cohort.

## Worked example

[`data/intake/example/example_city_facilities.csv`](../data/intake/example/example_city_facilities.csv)
is six **invented** sites in an "Example City" that does not exist, written with the faults
real files have: spaced and capitalised column names, distances in metres, visit length in
hours, `1,400` visitors, a `$45,000` cost, an `n/a`, a blank parking count, a garage marked
`partial`, a stormwater risk marked `unknown`, and no amenities column at all.

```bash
python -m fcf_m2.workflow intake data/intake/example/example_city_facilities.csv \
    --out cohorts/example-city --accept --jurisdiction "Example City" \
    --source-date 2026-10-01 --source-org "Example City (invented)"
python -m fcf_m2.workflow run --cohort cohorts/example-city
```

Intake reports `31 of 32 fields mapped, 1 absent, 0 refusal(s), 4 warning(s), 6 note(s)`:
three unit conversions and the unreadable `partial` as warnings; the absent amenities column,
the `n/a`, the blank parking count, the `unknown` and the two formatted numbers as notes, the
cell-level ones naming their file row. The run then scores six sites with **12 starter ports
and a 15-port pathway**, every site at Low confidence. Example City Recreation Center
(`EXC-04`), whose parking count was blank, gets the minimum cap of 2; the Transit Garage
(`EXC-05`), recorded as not open to the public, is "Low public-priority" with a plan not to
advance a public buildout, and its `partial` garage answer is listed in its `absent_fields`.
`tests/test_input_schema.py` reruns this example and fails if any number on this page stops
being true.
