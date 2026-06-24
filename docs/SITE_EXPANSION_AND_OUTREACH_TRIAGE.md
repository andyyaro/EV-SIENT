# Site Expansion and Outreach Triage Guide

## Purpose

This guide explains how a possible V2 candidate site moves through the project pipeline.

The goal is to keep expansion scalable.

V2 should not turn into manual outreach for every possible location. The model should first screen a larger public-data candidate pool, then the team should reach out only for the sites where confirmation would meaningfully improve the decision.

## Core idea

Use a funnel.

```text
Potential site idea
→ backlog candidate
→ public-data review
→ model-ready candidate
→ real_sites_v2.csv row
→ model ranking
→ outreach shortlist
→ stakeholder confirmation
→ updated model row
→ possible scorecard / technical review
```

This keeps the process organized as the project grows from 6 official V1 sites to 25–50 real V2 candidate sites.

## Files used in this workflow

```text
data/source_extracts/v2_candidate_site_backlog.csv
data/inputs/real_sites_v2.csv
docs/V2_EXPANSION_PLAN.md
docs/SITE_EXPANSION_AND_OUTREACH_TRIAGE.md
docs/site_scorecards/
```

The backlog is where uncertain site ideas go first.

The model input file is only for sites that are clean enough to be scored.

## Step 1: Add site ideas to the backlog first

Do not add every idea directly to `real_sites_v2.csv`.

Add possible sites first to:

```text
data/source_extracts/v2_candidate_site_backlog.csv
```

Use the backlog for sites that are interesting but still need basic public-data review.

A backlog row can be incomplete.

A model input row should not be incomplete.

## Step 2: Use clear backlog statuses

Use simple status values so the backlog stays readable.

Recommended `review_status` values:

```text
new
public_data_in_progress
needs_more_public_data
ready_for_model
added_to_v2_model
rejected
parked_for_later
```

Recommended `decision` values:

```text
collect_more_data
add_to_real_sites_v2
reject_for_now
park_for_future
needs_stakeholder_before_model
```

Recommended `model_ready_status` values:

```text
not_ready
almost_ready
ready
added
```

## Step 3: Minimum requirements before moving into real_sites_v2.csv

A site should usually meet these minimum conditions before it becomes a V2 model row:

```text
site name is known
site type is clear enough
address is known
city/state/zip are known
latitude and longitude are available or can be estimated reliably
public-access status is at least estimated
parking availability is at least estimated
site category makes sense for public/civic EV charging
notes explain what is confirmed and what is assumed
```

The model can handle assumptions, but the assumptions must be visible in the notes.

## Step 4: Public-data fields to collect first

Before outreach, try to collect or estimate these fields:

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

These are enough for a first-pass planning screen.

## Step 5: Fields that can remain assumptions in the first V2 screen

Some fields are hard to confirm without facilities, utility, site-owner, or permitting information.

These can remain assumptions for the first V2 screen if they are clearly documented:

```text
elec_service_rating_amp
spare_capacity_kw
emergency_disconnect_visible
employees_day
visitors_day
fleet_vehicles
```

These fields should lower data confidence when unknown.

They should not automatically block a first-pass model run.

## Step 6: When to reject or park a candidate

Reject or park a candidate if most of these are true:

```text
no clear parking area
no realistic public access
site is fully private with no partnership reason
location duplicates a stronger nearby candidate
site use case is too hard to explain
coordinates or address cannot be verified
site would require deep stakeholder work before even basic screening
```

Use `parked_for_later` when a site may become useful later but is not worth V2 effort right now.

Use `rejected` when the site clearly does not fit the project.

## Step 7: When a backlog site graduates into real_sites_v2.csv

A backlog site graduates when it is good enough to be scored.

Set:

```text
review_status = ready_for_model
decision = add_to_real_sites_v2
model_ready_status = ready
```

Then add a full row to:

```text
data/inputs/real_sites_v2.csv
```

After the row is added, update the backlog:

```text
review_status = added_to_v2_model
model_ready_status = added
next_step = run V2 model and review output
```

## Step 8: Outreach should happen after model screening

Do not reach out for every V2 site immediately.

First, run the model on the expanded V2 dataset.

Then prioritize outreach for sites that meet one or more of these conditions:

```text
Top 10 by readiness score
Top 10 by equity or access-gap importance
High readiness but low data confidence
Garage or enclosed-site complexity
Public-access uncertainty
Strong candidate where electrical assumptions drive the score
Site likely affected by renovation, construction, or operating-status uncertainty
Site that could change the final top 3–5 recommendation list
```

This is what makes the project scalable.

## Step 9: Outreach priority levels

Use three priority levels.

```text
High
Medium
Low
```

High priority means:

```text
The site is likely to affect the top shortlist, and one or two missing facts could change the recommendation.
```

Medium priority means:

```text
The site is promising or uncertain, but not urgent enough to contact before stronger candidates.
```

Low priority means:

```text
The site can stay in the model as a screening candidate, but outreach is not worth doing yet.
```

## Step 10: Who to contact by question type

Use the question type to decide the likely stakeholder.

```text
Parking count or parking operations → parking agency, site owner, facilities, or transportation office
EV charging operations → parking/transportation office, ChargePoint/network owner, or site operator
Electrical service / spare capacity → facilities, electrical supervisor, utility, or site engineer
ADA layout → facilities, accessibility office, civil/site design reviewer, or local accessibility reviewer
Fire/AHJ concerns → Fire Marshal, AHJ reviewer, facilities, or site engineer
Operating hours / visitor activity → site manager or public facility page
Future renovation / closure → site owner, facilities planning, capital projects, or public announcements
```

## Step 11: Standard outreach questions

Use short, targeted questions. Do not send every possible question to every stakeholder.

Core questions:

```text
1. Is public EV charging realistic at this location?
2. Where could chargers physically be placed without disrupting operations?
3. How many parking spaces are available near the likely charger area?
4. Are there ADA-accessible parking/layout constraints?
5. Are there known fire access, emergency disconnect, or safety constraints?
6. Is the electrical service likely to support Level 2 chargers without a major upgrade?
7. Is spare electrical capacity known or estimated?
8. Are there planned renovations, closures, or site changes that affect timing?
9. Who is the right follow-up contact for technical details?
```

## Step 12: How to update the model after outreach

After a stakeholder response, update the model carefully.

For each changed field, record:

```text
old value
new value
source/contact
response date
confidence level
notes explaining the change
```

Do not overwrite assumptions silently.

The notes field should make clear what became confirmed.

Example note language:

```text
Parking count confirmed by site contact on YYYY-MM-DD; electrical service rating remains unconfirmed; likely charger area identified near main public parking lot; ADA layout still needs review.
```

## Step 13: When to create a scorecard

Create a one-page scorecard only for important sites.

Scorecards should be created for:

```text
Top 3–5 model candidates
High-readiness but low-confidence candidates
Garage/high-review candidates
Sites being prepared for stakeholder discussion
Sites being discussed in a presentation or report
```

Scorecards should go in:

```text
docs/site_scorecards/
```

## Step 14: Scorecard template fields

Each scorecard should include:

```text
site ID
site name
locality
site type
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

## Step 15: V2 acceptance checklist

Before treating a V2 expansion as meaningful, confirm:

```text
real_sites_v2.csv has unique site IDs
no placeholder NEW001 row remains
all required columns are present
basic validation has zero blocking errors
model output has readiness scores for every site
recommended ports are positive integers
scalable charts are readable
outreach shortlist is small enough to be realistic
V1 files and V1 tags are untouched
```

## Simple rule of thumb

A site should move forward only when it answers one of these questions well:

```text
Could this site be one of the best public charging candidates?
Could this site serve an underserved or high-need area?
Could this site reveal an important infrastructure constraint?
Could this site help compare different site types fairly?
```

If the answer is no, keep it in the backlog or reject it for now.
