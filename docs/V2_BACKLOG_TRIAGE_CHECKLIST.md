# V2 Backlog Triage Checklist

## Purpose

Use this checklist to decide which rows in `v2_candidate_site_backlog.csv` are closest to graduating into `real_sites_v2.csv`.

The checklist supports the V2 funnel:

```text
backlog candidate
→ public-data cleanup
→ model-ready V2 row
→ model screening
→ outreach shortlist
```

## Scripted triage

Run this command from the repository root:

```bash
python src/triage_v2_candidate_backlog.py
```

Default input:

```text
data/source_extracts/v2_candidate_site_backlog.csv
```

Default outputs:

```text
data/outputs/v2_candidate_site_backlog_triage.csv
data/outputs/v2_candidate_site_backlog_triage.md
```

The generated outputs are local review files. They help decide which backlog rows to clean up first.

## What the script checks

The script looks at:

```text
initial priority
model-ready status
review status
decision field
address completeness
zip completeness
latitude / longitude completeness
public-access status
parking evidence status
nearby EV charging check status
missing public-data list
```

It then creates:

```text
triage_score
triage_group
blocking_gaps
recommended_next_action
```

## Triage groups

The main groups are:

```text
ready_for_model_row
near_ready_collect_targeted_data
useful_but_needs_public_data
early_backlog_candidate
parked_for_later
rejected
already_added_to_v2_model
```

## Manual graduation checklist

Before a backlog candidate moves into `real_sites_v2.csv`, confirm:

```text
site name is known
site type is clear enough
address is known
city/state/zip are known
latitude and longitude are available
public access is at least estimated
parking availability is at least estimated
nearby existing EV charging has been checked
basic hours or dwell-time assumptions are reasonable
notes clearly separate confirmed facts from assumptions
```

## What to clean up first

Start with candidates that are:

```text
High priority
almost_ready
public_data_in_progress
missing only targeted public-data fields
located in a useful comparison area
not blocked by unclear access or ownership
```

Do not start with candidates that have no address, no coordinate path, unclear public access, and unclear parking unless they are strategically very important.

## Best next data to fill

For most current V2 backlog rows, the highest-value missing data is:

```text
coordinates
parking estimate
operating hours
nearby charger counts from AFDC or a similar source
traffic exposure
nearby households / jobs
source notes for each value
```

## Rule for stakeholder outreach

Do not reach out just because a site is in the backlog.

Reach out after the model has screened the site and one of these is true:

```text
the site ranks near the top
the site has high readiness but low data confidence
the site has major public-access uncertainty
the site is a garage or technically complex site
the site could change the top 3–5 shortlist
```

## Recommended next workflow

```bash
python src/triage_v2_candidate_backlog.py
```

Then open:

```text
data/outputs/v2_candidate_site_backlog_triage.md
```

Pick the first 3–5 near-ready rows and fill their missing public data before adding them to:

```text
data/inputs/real_sites_v2.csv
```
