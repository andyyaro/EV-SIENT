# EV-SIENT public data hub

Public data the planner can use to fill gaps in a site file (DEC-025). The builder here turns
pinned public files into small per-county Parquet packs; the app's Public Data step fetches the
packs around a planner's sites, works out each value in the browser, and shows every value with
its source and vintage for the planner to accept or reject, field by field.

Only public sources go in. Nothing from `data/inputs`, the contract or real provenance
(DEC-016), and nothing a planner uploads ever reaches the hub.

## Build a release

```
venv/bin/python -m pip install -r platform/hub/requirements.txt   # pyarrow, once
venv/bin/python -I platform/hub/build_hub.py --hub-version 2026-10-18.1
```

About a minute on a laptop once the inputs are cached (about 150 MB, downloaded on the first
build). The release is written to `platform/hub/out/hub/`, laid out exactly as it is served.

| Option | What it does |
|---|---|
| `--hub-version` | The release name. Never reused: a build into an existing release stops |
| `--offline` | Use only the cache; never download |
| `--refresh` | Take a new AFDC snapshot (pinned files never change) |
| `--allow-row-change` | Publish even if the packs' row count moves more than 20% from the last release |

Run it with `-I`. Downloads are untrusted data: they land in `cache/<dataset>/` (ignored by git)
with a `.meta.json` recording the URL and time, are only parsed, never executed, and a pinned
file whose SHA-256 differs from `sources.json` stops the build. The AFDC download needs an API key
in `NLR_API_KEY` (`DEMO_KEY` otherwise, limited to a few requests an hour); the key is stripped
from every recorded URL.

`npm run dev` and `npm run preview` in `platform/app` serve `out/hub/` at `/hub/`, so the Public
Data step works locally against the release you built.

## Inputs (`sources.json`)

| Dataset | Vintage | File | Licence |
|---|---|---|---|
| `acs-b11001` | ACS 2020-2024 5-year, table B11001 (households), published 2026-01-29 | `acsdt5y2024-b11001.dat`, every US block group | Public domain (U.S. Census Bureau) |
| `pl94171-va` | 2020 Census P.L. 94-171, Virginia | `va2020.pl.zip`: block internal points, housing units, occupied units (H1) | Public domain (U.S. Census Bureau) |
| `lodes-wac-va` | LODES 8.4, 2023 jobs, published 2025-12-18 | `va_wac_S000_JT00_2023.csv.gz` | Public domain (U.S. Census Bureau) |
| `svi-2022` | CDC/ATSDR SVI 2022 (ACS 2018-2022) | `SVI_2022_US.csv`, every US tract | Public domain (CDC/ATSDR) |
| `tiger-state-2026` | TIGER/Line 2026 states | `tl_2026_us_state.zip` (coverage boundary only) | Public domain (U.S. Census Bureau) |
| `afdc-stations` | Live list; the snapshot date is the vintage | AFDC CSV of open, public electric stations | U.S. Government data, free to use; no endorsement implied |

Every release records each input's URL, vintage, licence, size and SHA-256 in its manifest, and
the full licence texts in `licences.txt`.

## What a release contains

```
hub/latest.json                                      pointer: current release and its manifest SHA-256
hub/releases/{hubVersion}/manifest.json              inputs, fields, packs, tables, notes, gates
hub/releases/{hubVersion}/coverage.json              Virginia boundary (25 m simplification, 3,999 points)
hub/releases/{hubVersion}/licences.txt
hub/packs/{countyFips}/{hubVersion}/core.parquet     one per county or independent city (133)
hub/data/{dataset}/{vintage}/{buildId}/{name}.parquet  national tables (households by block group,
                                                     SVI by tract, AFDC stations)
hub/stac/catalog.json, hub/stac/{collection}/collection.json   pointers
hub/stac/{collection}/{item}.json                    one STAC item per release or table build
```

Every key except the pointers is new for each release and never rewritten; the builder refuses
to change an existing key. Pointers are written last, `latest.json` very last, so a reader never
follows a pointer to a file that is not there yet. National tables are keyed by a hash of their
inputs, so a release with unchanged inputs reuses the same keys.

### Pack schema

One row group, Snappy compression (which hyparquet reads without add-ons), int32 counts.

| Column | Type | Block rows | Station rows |
|---|---|---|---|
| `kind` | string | `block` | `station` |
| `id` | string | 2020 block GEOID (15 digits) | `afdc:{ID}` |
| `lat`, `lon` | double | block internal point (WGS84) | station location |
| `households` | double | ACS households shared to the block (null if the block group has no estimate) | null |
| `jobs` | int32 | LODES jobs (a block LODES does not list has 0) | null |
| `svi` | double | SVI 2022 overall national percentile of the block's tract (null where SVI gives no rank) | null |
| `l2_ports`, `dcfc_ports` | int32 | null | Level 2 and DC fast ports (a blank AFDC count is 0) |

Blocks with neither households nor jobs are left out. Stations are those inside Virginia or
within 3.5 miles of its boundary, each carried by the county of its nearest block.

## Fields it fills

The manifest's `fields` says how the app works out each one; the method sentence is shown to the
planner beside every value. Distances are great-circle miles (the same formula in
`hubbuild/geo.py` and `app/src/hub/compute.ts`).

| Field | From | How |
|---|---|---|
| `nearby_households_1mi` | ACS 2020-2024, PL 94-171 | Block group households shared among its blocks by 2020 occupied homes, summed over blocks within 1 mile |
| `nearby_jobs_1mi` | LODES 8.4 (2023) | Jobs summed over blocks within 1 mile |
| `equity_gap_index` | SVI 2022 | Tract national rank, averaged over blocks within 1 mile by households. A proxy, labelled as one |
| `existing_l2_ports_1mi` | AFDC snapshot | Level 2 ports at open, public stations within 1 mile |
| `existing_dcfc_ports_3mi` | AFDC snapshot | DC fast ports at open, public stations within 3 miles |

The block-based fields are offered only for sites at least 1 mile inside Virginia, because the
packs hold no blocks across the line; port counts are offered anywhere inside Virginia. A site
outside, too close to the line or without coordinates gets the reason, never a zero.

Not in this release (the manifest's `notYet`, shown in the app): `aadt_nearest` (no downloadable
HPMS 2024 or VDOT 2025 file; VDOT's live layer ends in 2022), `amenities_count_0_5mi` (needs a
Virginia Overture extract and an agreed category list) and `ev_share_local` (Atlas EV Hub is ODbL
and belongs in a separate pack, not built yet).

## Gates

A release is published only if all five pass; they are recorded in its manifest.

| Gate | Passes when |
|---|---|
| schema | every pack has exactly the pack schema |
| row-count change | pack rows moved 20% or less since the last release (or `--allow-row-change`) |
| coordinates | every pack's extent lies inside the coverage box plus the station margin, and every county is in the state |
| licence text | every dataset's licence appears in `licences.txt` |
| size | no pack over 5 MB and the release under 2 GB |

Release 2026-10-18.1: 133 packs, 3.6 MB in all (median 19 KB, largest Fairfax County at 205 KB),
national tables 6.8 MB, 149 files.

## Publishing

The hub is served from the app's own bucket and origin under `/hub/`, so the app's
`connect-src 'self'` covers it. `platform/tools/deploy.sh` never prunes `hub/`. Publish the
immutable keys first, the pointers after, `latest.json` last:

```
aws s3 cp platform/hub/out/hub/packs    s3://future-city-app/hub/packs    --recursive --profile future-city \
  --cache-control "public, max-age=31536000, immutable" --content-type application/vnd.apache.parquet
aws s3 cp platform/hub/out/hub/data     s3://future-city-app/hub/data     --recursive --profile future-city \
  --cache-control "public, max-age=31536000, immutable" --content-type application/vnd.apache.parquet
aws s3 cp platform/hub/out/hub/releases s3://future-city-app/hub/releases --recursive --profile future-city \
  --cache-control "public, max-age=31536000, immutable"
aws s3 cp platform/hub/out/hub/stac     s3://future-city-app/hub/stac     --recursive --profile future-city \
  --cache-control "public, max-age=31536000, immutable" --content-type application/json \
  --exclude "catalog.json" --exclude "*/collection.json"
aws s3 cp platform/hub/out/hub/stac     s3://future-city-app/hub/stac     --recursive --profile future-city \
  --cache-control "public, max-age=60" --content-type application/json \
  --exclude "*" --include "catalog.json" --include "*/collection.json"
aws s3 cp platform/hub/out/hub/latest.json s3://future-city-app/hub/latest.json --profile future-city \
  --cache-control "public, max-age=60" --content-type application/json
aws cloudfront create-invalidation --distribution-id E1JXKS26TDP3Z2 --profile future-city \
  --paths "/hub/latest.json" "/hub/stac/*"
```

The app reads `latest.json` with `cache: 'no-cache'` and every other file by a key that names
its release, checked against the manifest's SHA-256 before it is read.

## Tests

`tests/test_hub_builder.py` builds a whole release offline from small synthetic files in each
publisher's layout: readers, pins, households conservation, station margin, immutable keys,
pointers and the gates. The Parquet parts skip where pyarrow is not installed.
