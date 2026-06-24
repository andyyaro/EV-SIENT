# V2 Expansion Plan

## Purpose

V1 is frozen and should remain stable.

V2 is the next development phase for expanding the Public EV Charging Site-Readiness and Right-Sizing Model from the current six official candidate sites to a larger real candidate-site pool.

The purpose of V2 is to test whether the model remains useful, explainable, and scalable when applied to a broader set of real public or civic locations in Fairfax City, Fairfax County, and Prince William County.

## V1 freeze rule

Do not move, overwrite, or reinterpret the V1 freeze tags.

```text
v1-review-ready
v1-demo-scalability-ready
```

V1 remains the official six-site reviewer-ready checkpoint.

V2 should be built separately so the project can grow without breaking the frozen V1 benchmark.

## Main V2 goal

Expand from:

```text
6 real candidate sites
```

to:

```text
25–50 real candidate sites
```

The target is not to create perfect final recommendations immediately. The target is to create a broader screening dataset that can identify the strongest candidates for deeper stakeholder validation.

## Recommended V2 file structure

Create V2 files instead of replacing V1 files directly.

```text
data/inputs/real_sites_v2.csv
data/config/output_check_rules_v2.json
data/baselines/v2_baseline/
data/outputs_v2/ or data/outputs/v2/   optional, if needed later
docs/V2_EXPANSION_PLAN.md
docs/SITE_EXPANSION_AND_OUTREACH_TRIAGE.md
docs/site_scorecards/
```

The exact output-folder structure can be decided later. The most important rule is that V1 files and V1 tags stay preserved.

## Candidate-site categories to add first

Start with sites that are easy to justify as public, civic, transportation, or community-serving locations.

Good first categories:

```text
public libraries
city or county government buildings
community centers
parks and recreation centers
commuter lots
public garages
transit-adjacent parking areas
public schools or civic campuses, only if public charging access is realistic
public safety or fleet-support sites, only if marked special-use
```

Avoid random private sites at first unless there is a clear public-access or partnership reason.

## V2 screening funnel

V2 should work as a funnel, not as a manual deep-dive into every site.

```text
25–50 real candidate sites
→ public-data screening model
→ top 10–15 serious candidates
→ stakeholder outreach for the strongest or most uncertain candidates
→ top 3–5 technical-review priorities
```

This keeps outreach manageable.

The model should help decide where human follow-up is worth the time.

## Public data first

For the first V2 pass, use public or easily available data before outreach.

Fields to prioritize:

```text
site_id
site_name
site_type
address
city
state
zip
lat
lon
public_access
parking_spaces
hours_open
avg_dwell_min
nearby_households_1mi
nearby_jobs_1mi
aadt_nearest
amenities_count_0_5mi
existing_l2_ports_1mi
existing_dcfc_ports_3mi
equity_gap_index
distance_to_service_ft
trenching_ft
trench_cost_per_ft
service_upgrade_cost_usd
ada_layout_possible
fire_access_ok
garage_enclosed
stormwater_risk
notes
```

Do not wait for perfect electrical data before creating the first V2 candidate pool. Use clearly labeled assumptions, then let the model identify which sites deserve deeper confirmation.

## High-value fields that usually require outreach

These are the fields most likely to need stakeholder, utility, facilities, site-owner, or technical confirmation:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
likely charger placement
panel or transformer constraints
real trenching/routing distance
parking count confirmation
visitor or employee estimates
site operating hours
ADA layout feasibility
fire/AHJ concerns
garage-specific restrictions
future construction or renovation plans
```

These should not block the first V2 screen, but they should drive data-confidence and outreach priority.

## Site ID plan

Keep V2 site IDs short, stable, and locality-based.

Examples:

```text
FFX003
FFX004
FFX005
PWC005
PWC006
PWC007
```

Do not reuse IDs for different sites.

If a site is removed later, retire the ID instead of reassigning it.

## V2 output-check plan

The current V1 checker expects exactly the official six V1 sites. A larger V2 dataset needs its own rules.

Create:

```text
data/config/output_check_rules_v2.json
```

The V2 checker should validate things like:

```text
minimum expected number of sites
required columns present
zero blocking data-quality errors
site IDs are unique
no placeholder NEW001 rows
readiness scores remain within 0–100
recommended ports are positive integers
profile analysis includes all expected profiles
sensitivity analysis completes
required output files are generated
```

Unlike V1, V2 should probably not require one fixed expected top site at first, because the site pool will still be changing.

## V2 baseline plan

After the first stable V2 dataset is created and reviewed, create a V2 baseline:

```text
data/baselines/v2_baseline/
```

Only create the V2 baseline after:

```text
real_sites_v2.csv has a stable first candidate pool
run_all or a V2 workflow completes successfully
major site IDs are no longer changing every run
results have been reviewed for obvious data-entry errors
```

## Outreach triage rule

Do not contact stakeholders for every V2 site.

Prioritize outreach for sites that meet one or more of these conditions:

```text
Top 10 by readiness score
Top 10 by equity need or access gap
High readiness but low data confidence
Garage or enclosed-site complexity
Public-access uncertainty
Strong candidate with electrical assumptions driving the score
Site likely to change because of renovation, construction, or operating-hours uncertainty
```

This keeps V2 scalable.

## Scorecard plan

Create one-page scorecards only for the most important sites.

Suggested first scorecards:

```text
docs/site_scorecards/FFX002_scorecard.md
docs/site_scorecards/FFX001_scorecard.md
docs/site_scorecards/PWC002_scorecard.md
docs/site_scorecards/PWC004_scorecard.md
```

After V2 expansion, create scorecards for new top candidates.

Each scorecard should include:

```text
rank
readiness score
data confidence score
recommendation tier
action label
recommended ports now / 2035 / 2050
why the site ranked well
main risks
missing data
stakeholder questions
next decision
```

## Suggested V2 work order

Use this order:

```text
1. Create this V2 expansion plan.
2. Create a blank real_sites_v2.csv from the V1 schema.
3. Identify 25–50 candidate sites from public/civic categories.
4. Fill the first public-data fields.
5. Create output_check_rules_v2.json.
6. Decide whether to add a separate run_v2.py or parameterize the existing workflow.
7. Run the model on real_sites_v2.csv.
8. Create scalable visuals for the real V2 dataset.
9. Create outreach triage list from the V2 results.
10. Build scorecards for the top candidates.
11. Begin stakeholder outreach only for the shortlist.
12. Re-run with confirmed data.
13. Create a V2 baseline once the first expanded dataset is stable.
```

## What not to do yet

Do not immediately rewrite the scoring model.

Do not immediately build a dashboard.

Do not contact every possible site owner.

Do not replace V1 files or move V1 tags.

Do not treat synthetic demo results as real recommendations.

## Success criteria for V2

V2 is successful when the project can show:

```text
A real expanded candidate-site dataset exists.
The workflow runs without blocking errors.
The model can rank 25–50 real sites.
Scalable visuals remain readable.
The project can explain why a small shortlist deserves outreach.
The top candidates have clear missing-data questions.
V1 remains preserved and reproducible.
```

## Immediate next task

Create a first draft V2 input file:

```text
data/inputs/real_sites_v2.csv
```

Start it by copying the V1 schema and rows, then add new candidate rows only when the site has enough public data to be useful.
