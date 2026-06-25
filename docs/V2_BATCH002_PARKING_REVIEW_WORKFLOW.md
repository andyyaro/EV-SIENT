# V2 Batch 002 Parking Review Workflow

## Purpose

This workflow documents how to replace placeholder parking-space values for the V2 Batch 002 library candidates.

Target sites:

```text
PWC005 — Haymarket Gainesville Library
PWC006 — Bull Run Library
PWC007 — Central Library
PWC008 — Potomac Library
```

## Current status

The current `parking_spaces` values are placeholders used to keep the preliminary V2 model runnable. They should not be described as official parking counts.

## Preferred evidence order

1. Official facility page, site plan, county planning document, or property record with a parking count.
2. If no official count is available, documented map/aerial review with a conservative parking-stall estimate.
3. Stakeholder confirmation from county/library/facilities staff.

## Manual map-review method

For each site:

1. Open the site in an aerial/satellite map view.
2. Identify only parking areas that clearly serve the library site.
3. Count visible marked stalls when possible.
4. If counting is difficult, use a conservative estimate and mark the confidence as `draft`.
5. Record the reviewed value in:

```text
data/source_extracts/v2_batch002_parking_review_template.csv
```

## Required fields to fill

```text
reviewed_parking_spaces
evidence_type
evidence_note
confidence
apply_ready
notes
```

Use `apply_ready=yes` only after the parking estimate has been reviewed enough to apply to `data/inputs/real_sites_v2.csv`.

## Interpretation rule

Parking affects feasibility and right-sizing, so do not treat Batch 002 rankings as final until parking is reviewed.
