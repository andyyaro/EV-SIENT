# V2 Next Batch Plan

## Purpose

This file tracks the next V2 expansion batch after the first reviewed public-data upgrade batch for FFX003 and FFX004.

The goal is to expand V2 beyond Fairfax-only additions and create a stronger Prince William County comparison set before treating V2 as a baseline.

## Selected batch

Batch file:

```text
data/source_extracts/v2_next_upgrade_batch.csv
```

Current selected candidates:

```text
V2C011 → PWC005 — Haymarket Gainesville Community Library
V2C008 → PWC006 — Bull Run Regional Library
V2C009 → PWC007 — Central Community Library
V2C010 → PWC008 — Potomac Community Library
V2C015 → PWC009 — Woodbridge VRE Station Parking
```

## Why this batch

This batch was selected because it improves V2 in three ways:

1. It strengthens Prince William County coverage.
2. It adds several public-serving library candidates with similar comparison logic to FFX002, FFX003, and PWC004.
3. It includes one transit/parking candidate to test whether the model handles commuter long-dwell charging differently from libraries and government campuses.

## Do not add directly yet

These candidates should not be copied directly into `data/inputs/real_sites_v2.csv` yet.

Each candidate still needs minimum public-data verification:

```text
official address
zip code
latitude/longitude
parking estimate or parking-capacity evidence
public access / ownership / operating-hours evidence
nearby charger counts
```

The Woodbridge VRE parking candidate also needs ownership and access-rule confirmation before being treated as a general public charging candidate.

## Implementation path

### Step 1 — Verify minimum public location data

For each candidate, verify:

```text
address
city/state/zip
latitude/longitude
site type
public access assumption
operating hours or access hours
parking count or parking-capacity evidence
```

### Step 2 — Create preliminary model rows

Only after the minimum data is verified, add rows to:

```text
data/inputs/real_sites_v2.csv
```

Use future site IDs from the batch file:

```text
PWC005
PWC006
PWC007
PWC008
PWC009
```

### Step 3 — Create/update source confidence rows

For each promoted model row, add source-confidence rows in:

```text
data/source_extracts/v2_source_confidence_tracker.csv
```

At minimum, track:

```text
location
parking
hours/public access
AFDC nearby charging
households
jobs
traffic
amenities
equity
EV adoption
electrical/cost
```

### Step 4 — Create OSM target file and run amenities

After preliminary rows have coordinates, build a target-site file for OSM:

```bash
python - <<'PY'
import pandas as pd
from pathlib import Path

site_ids = ["PWC005", "PWC006", "PWC007", "PWC008", "PWC009"]
sites = pd.read_csv("data/inputs/real_sites_v2.csv")
targets = sites[sites["site_id"].isin(site_ids)].copy()
out = Path("data/source_extracts/v2_batch002_osm_target_sites.csv")
targets.to_csv(out, index=False)
print(f"Saved {len(targets)} target sites to {out}")
PY
```

Then run:

```bash
python src/build_osm_amenities.py \
  --input data/source_extracts/v2_batch002_osm_target_sites.csv \
  --summary-output data/source_extracts/v2_batch002_amenities_osm_summary_0_5mi.csv \
  --poi-output data/source_extracts/v2_batch002_amenities_osm_pois_0_5mi.csv \
  --pause 8 \
  --retries 3
```

### Step 5 — Run public-data upgrade calculator

After the rows are in `real_sites_v2.csv`, run:

```bash
python src/build_v2_public_data_upgrades.py --site-ids PWC005 PWC006 PWC007 PWC008 PWC009
```

Review:

```text
data/source_extracts/v2_public_data_upgrade_recommendations.csv
```

### Step 6 — Apply reviewed values carefully

Only after reviewing the recommendations, update:

```text
data/inputs/real_sites_v2.csv
data/source_extracts/v2_source_confidence_tracker.csv
data/source_extracts/v2_public_data_upgrade_tasks.csv
```

### Step 7 — Rerun V2 workflow

```bash
python src/run_v2.py
python src/check_outputs_v2.py
```

## Expected outcome

After this batch is promoted and upgraded, V2 should have enough candidate diversity to compare:

```text
Fairfax City civic/library sites
Fairfax County library/government sites
Prince William County government/library/transit sites
commuter/garage sites
special-use public-safety site
```

This is the point where a persistent V2 interpretation file in `docs/` will become more useful.
