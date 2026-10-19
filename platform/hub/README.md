# EV-SIENT public data hub

Public data the planner can use to fill gaps in a site file (DEC-025). The builder here turns
pinned public files into small per-county Parquet packs; the app's Public Data step fetches the
packs around a planner's sites, works out each value in the browser, and shows every value with
its source and vintage for the planner to accept or reject, field by field.

Only public sources go in. Nothing from `data/inputs`, the contract or real provenance
(DEC-016), and nothing a planner uploads ever reaches the hub.

The hub covers Virginia, New York, Maryland, the District of Columbia, Colorado and Illinois
(DEC-028). The states are listed in `sources.json` (`states`); adding one is a registry change:
its P.L. 94-171 and LODES files, each added to its group.

## Build a release

```
venv/bin/python -m pip install -r platform/hub/requirements.txt   # pyarrow, once
venv/bin/python -I platform/hub/build_hub.py --hub-version 2026-10-18.2
```

About a minute on a laptop once the inputs are cached (about 330 MB, downloaded on the first
build). The release is written to `platform/hub/out/hub/`, laid out exactly as it is served.
Build on top of a copy of what is already published (the last release's `out/hub/`), so the
row-count gate has a release to compare with and the STAC collections keep their items.

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
| `pl94171-{st}` | 2020 Census P.L. 94-171, one per state (va, ny, md, dc, co, il), published 2021-08-12 | `{st}2020.pl.zip`: block internal points, housing units, occupied units (H1) | Public domain (U.S. Census Bureau) |
| `lodes-wac-{st}` | LODES 8.4, 2023 jobs, one per state, published 2025-12-18 | `{st}_wac_S000_JT00_2023.csv.gz` | Public domain (U.S. Census Bureau) |
| `svi-2022` | CDC/ATSDR SVI 2022 (ACS 2018-2022) | `SVI_2022_US.csv`, every US tract | Public domain (CDC/ATSDR) |
| `tiger-state-2026` | TIGER/Line 2026 states | `tl_2026_us_state.zip` (coverage boundary only) | Public domain (U.S. Census Bureau) |
| `afdc-stations` | Live list; the snapshot date is the vintage | AFDC CSV of open, public electric stations | U.S. Government data, free to use; no endorsement implied |

Every release records each input's URL, vintage, licence, size and SHA-256 in its manifest, and
the full licence texts in `licences.txt`. No ODbL source is used (DEC-028: the owner has not
decided on ODbL).

`states` names, for each published state, its FIPS code, postal code, name and its two files.
`groups` gathers the per-state files into the one source a field names: `pl94171` (2020 blocks)
and `lodes-wac` (jobs). The build refuses a state whose file is not in its group, and a group
whose files differ in publisher, vintage, publication date or licence; the manifest lists each
group in `datasets` with its `members`.

## What a release contains

```
hub/latest.json                                      pointer: current release and its manifest SHA-256
hub/releases/{hubVersion}/manifest.json              inputs, fields, packs, tables, notes, gates
hub/releases/{hubVersion}/coverage.json              outline of every published state together, the
                                                     borders between them dissolved (25 m
                                                     simplification), and each state's box
hub/releases/{hubVersion}/licences.txt
hub/packs/{countyFips}/{hubVersion}/core.parquet     one per county or county equivalent (386)
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

Blocks with neither households nor jobs are left out. Each state is built on its own: its
blocks, and the stations inside it or within 3.5 miles of its own boundary, each carried by the
county of its nearest block in that state. A station near the border of two published states is
therefore in both states' packs; the app counts each station once, by its ID.

## Fields it fills

The manifest's `fields` says how the app works out each one; the method sentence is shown to the
planner beside every value. Distances are great-circle miles (the same formula in
`hubbuild/geo.py` and `app/src/hub/compute.ts`).

| Field | From | How |
|---|---|---|
| `nearby_households_1mi` | ACS 2020-2024, PL 94-171 | Block group households shared among its blocks by 2020 occupied homes, summed over blocks within 1 mile |
| `nearby_jobs_1mi` | LODES 8.4 (2023), one file per state | Jobs summed over blocks within 1 mile |
| `equity_gap_index` | SVI 2022 | Tract national rank, averaged over blocks within 1 mile by households. A proxy, labelled as one |
| `existing_l2_ports_1mi` | AFDC snapshot | Level 2 ports at open, public stations within 1 mile |
| `existing_dcfc_ports_3mi` | AFDC snapshot | DC fast ports at open, public stations within 3 miles |

The block-based fields are offered only for sites at least 1 mile inside the coverage, the
outline of all published states together. A site near the line between two published states
(Arlington and the District of Columbia, say) gets blocks from both; a site within 1 mile of a
state the hub does not cover gets the reason, because the packs hold no blocks there. Port counts
are offered anywhere inside the coverage. A site outside it, too close to its edge or without
coordinates gets the reason, never a zero. TIGER/Line draws a shared border with the same
vertices in both states, so the builder drops every edge that appears in both directions
(`geo.dissolve_rings`) and keeps the outline.

The app says which covered state each site is in (by its nearest census block) and lists each
state's own files that the values near the sites were worked out from.

Not in this release (the manifest's `notYet`, shown in the app): `aadt_nearest` (no downloadable
HPMS 2024 or VDOT 2025 file; VDOT's live layer ends in 2022), `amenities_count_0_5mi` (needs an
Overture extract for the covered states and an agreed category list) and `ev_share_local` (Atlas
EV Hub is ODbL and belongs in a separate pack, not built yet).

## Gates

A release is published only if all five pass; they are recorded in its manifest.

| Gate | Passes when |
|---|---|
| schema | every pack has exactly the pack schema |
| row-count change | each state's pack rows moved 20% or less since the last release (or `--allow-row-change`); a newly added state is reported as new |
| coordinates | every pack is in a published state, and its extent lies inside that state's box plus the station margin |
| licence text | every dataset's licence appears in `licences.txt` |
| size | no pack over 5 MB and the release under 2 GB |

Release 2026-10-18.1: Virginia only, 133 packs, 3.6 MB in all (median 19 KB, largest Fairfax
County at 205 KB), national tables 6.8 MB, 149 files.

Release 2026-10-18.2 (DEC-028): 386 packs, 22.8 MB in all, plus a 466 KB coverage file (6 rings,
8,482 points) and a 197 KB manifest; 390 new files. The national tables are unchanged and keep
their keys.

| State | Packs | Size | Median pack | Largest pack |
|---|---|---|---|---|
| Virginia | 133 | 3.6 MB | 19 KB | Fairfax County, 205 KB |
| New York | 62 | 6.4 MB | 64 KB | Suffolk County, 582 KB |
| Maryland | 24 | 1.9 MB | 55 KB | Baltimore city, 243 KB |
| District of Columbia | 1 | 0.2 MB | 158 KB | District of Columbia, 158 KB |
| Colorado | 64 | 2.9 MB | 22 KB | El Paso County, 276 KB |
| Illinois | 102 | 7.7 MB | 39 KB | Cook County, 1.99 MB |

Virginia's packs hold the same rows as in 2026-10-18.1: each state is built as before, and only
the coverage file (now all six states) and the manifest's shape changed.

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
pointers and the gates. A second invented state shares a border with the first: the border is
dissolved from the coverage, both states publish under one coverage, the first state's packs do
not change when the neighbour is added, a border station is in both states' packs, the
row-count gate reports the new state as new, and the registry refuses a state outside its group
or a group whose files disagree. The Parquet parts skip where pyarrow is not installed.
