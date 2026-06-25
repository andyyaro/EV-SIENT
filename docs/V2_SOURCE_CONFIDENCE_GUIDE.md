# V2 Source Confidence Guide

## Purpose

This guide keeps V2 scalable by making every data value easier to interpret.

As the project grows from a small six-site V1 dataset to a larger V2 candidate pool, each field should make clear whether it comes from an official source, a public dataset, a public web reference, a planning assumption, or stakeholder confirmation.

The goal is not to make every V2 value perfect immediately.

The goal is to make the uncertainty honest, visible, and easy to improve later.

## Why this matters

V2 will include more candidate sites than V1.

That means the project needs a clean way to say:

```text
This value is confirmed.
This value comes from a public dataset.
This value is a public reference, but not official enough yet.
This value is a planning assumption.
This value still needs stakeholder or technical confirmation.
```

This prevents preliminary screening rows from sounding more certain than they really are.

## Source confidence labels

Use the following labels in source notes, assumption files, and backlog notes.

### 1. official_source

Use this when the value comes directly from an official facility, agency, government, utility, or operator source.

Examples:

```text
Official library branch page confirms address.
Official county facility page confirms hours.
Official parking page confirms parking capacity.
Official GIS layer provides coordinates.
Official transportation dataset provides traffic count.
```

### 2. public_dataset

Use this when the value comes from a structured public dataset.

Examples:

```text
AFDC alternative fuel stations download
ACS demographic extract
LODES jobs extract
VDOT traffic dataset
OpenStreetMap Overpass extract, when documented as OSM-derived
```

This is useful and reproducible, but still should be documented with date/version/source notes when possible.

### 3. public_web_reference

Use this when the value comes from a public webpage or public listing, but not from a strong official dataset or direct facility source.

Examples:

```text
A public page lists the facility address.
A public map or listing provides coordinates.
A general public reference confirms a site exists.
```

This is acceptable for early V2 screening, but should be replaced with official_source or public_dataset when possible.

### 4. planning_assumption

Use this when the value is a reasonable placeholder chosen for first-pass screening.

Examples:

```text
estimated visitors per day
estimated employees per day
estimated parking capacity
estimated nearby households before ACS buffer is added
estimated nearby jobs before LODES buffer is added
estimated traffic before VDOT segment match is added
estimated trenching distance
estimated service upgrade cost
```

Planning assumptions are allowed in V2 screening rows, but they should not be treated as final evidence.

### 5. stakeholder_confirmed

Use this only after a relevant person, office, agency, utility, facility manager, or stakeholder confirms the value.

Examples:

```text
facility manager confirms available panel capacity
county staff confirms parking lot ownership
library staff confirms practical charger placement area
utility confirms service upgrade requirement
fire/AHJ staff confirms review issue
```

This is one of the strongest labels, especially for electrical, ownership, ADA, fire access, and implementation feasibility.

### 6. unconfirmed_placeholder

Use this when the value is unknown, but the model needs a placeholder to run.

Examples:

```text
spare_capacity_kw = 0
emergency_disconnect_visible = 0
elec_service_rating_amp = 0
```

This label should trigger follow-up before a site is treated as a serious implementation candidate.

## Recommended use by file type

### In `real_sites_v2.csv`

Keep the actual numeric value needed by the model.

Use the `notes` column to summarize the source confidence mix.

Example:

```text
V2 preliminary model row. Address and hours from official_source; charger counts from public_dataset; households, jobs, traffic, equity, and electrical capacity remain planning_assumption or unconfirmed_placeholder.
```

### In `v2_candidate_site_backlog.csv`

Use the notes/status fields to show whether a site is still missing basic public data, already added, or waiting for source replacement.

Example:

```text
added_to_v2_model; replace planning assumptions before V2 baseline
```

### In site-specific public data notes

Explain what was collected and where it came from.

Separate stronger evidence from weaker assumptions.

Example structure:

```text
Official/public data collected
Nearby EV charging source
Preliminary model row added
Planning assumptions used
Fields that still need better source replacement
Recommended next action
```

### In site-specific assumption CSVs

Use these columns:

```text
field,value,source_status,notes
```

The `source_status` column should use one of the labels from this guide.

## V2 baseline rule

Do not create a V2 baseline until the top candidate rows have fewer high-impact planning assumptions.

At minimum, before a V2 baseline, try to improve:

```text
nearby_households_1mi
nearby_jobs_1mi
aadt_nearest
amenities_count_0_5mi
equity_gap_index
ev_registrations_local
ev_share_local
parking_spaces
hours_open
visitors_day
employees_day
spare_capacity_kw
elec_service_rating_amp
emergency_disconnect_visible
```

## Interpretation rule

A high readiness score with many `planning_assumption` or `unconfirmed_placeholder` values should be treated as a screening flag, not a final recommendation.

A lower readiness score with strong `official_source`, `public_dataset`, or `stakeholder_confirmed` data may be more trustworthy than a higher score built mostly on assumptions.

## Simple project language

When explaining V2 results, use plain language:

```text
This site looks promising, but much of the score is still assumption-based.
This site has strong public data but still needs electrical confirmation.
This site has many nearby chargers already, so additional need may be lower.
This site should stay in the backlog until address, parking, and access are clearer.
```

## Current V2 source-status principle

V2 is allowed to use assumptions for early screening.

But V2 should always label assumptions clearly.

That is what makes the model scalable and honest.
