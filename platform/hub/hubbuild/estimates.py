"""The rows a county pack holds: census blocks with households, jobs and an equity rank, and
public charging stations with their port counts. Pure numpy and dicts, no file formats.

Each step says what it does in one sentence, because the planner is shown that sentence beside
every value filled from these rows (DEC-021):

* **Households** are the ACS 2020-2024 count for each block group, shared among the block group's
  2020 census blocks in proportion to their occupied homes in 2020 (P.L. 94-171 H1). A block
  group with no occupied homes in 2020 shares by housing units; one with neither shares
  equally. Each fallback is counted in the release notes. A block group with no ACS estimate
  leaves its blocks' households empty (null), never 0.
* **Jobs** are LODES 8.4 workplace counts (C000, 2023) at each 2020 block. LODES lists only
  blocks with jobs, so a block it does not list has 0 jobs: that is the file's own meaning.
* **Equity** is the CDC/ATSDR SVI 2022 overall national percentile (RPL_THEMES) of the block's
  tract, or null where the SVI gives no rank.
* **Stations** are open, public AFDC electric stations inside the state or within
  `STATION_MARGIN_MI` of its boundary, so a site near the state line still sees the chargers
  across it.

Blocks with neither households nor jobs are dropped: they add nothing to a sum, and an equity
average is weighted by households.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import geo
from .readers import PlBlocks

#: Stations this far outside the state are kept, so the 3-mile DC fast count is complete for
#: any site inside it (the largest radius a field uses, plus half a mile).
STATION_MARGIN_MI = 3.5


@dataclass
class BlockRows:
    geoid: list[str]
    county: list[str]
    lat: np.ndarray
    lon: np.ndarray
    households: np.ndarray      # float, NaN where no ACS estimate
    jobs: np.ndarray            # int
    svi: np.ndarray             # float, NaN where no rank
    notes: dict = field(default_factory=dict)


@dataclass
class StationRows:
    id: list[str]
    county: list[str]
    lat: np.ndarray
    lon: np.ndarray
    l2: np.ndarray
    dcfc: np.ndarray
    notes: dict = field(default_factory=dict)


def block_rows(pl: PlBlocks, acs: dict[str, tuple[int, int | None]], jobs: dict[str, int],
               svi: dict[str, dict[str, float | None]], state_fips: str) -> BlockRows:
    n = len(pl.geoid)
    bg = np.array([g[:12] for g in pl.geoid])
    order = np.argsort(bg, kind="stable")
    households = np.full(n, np.nan)
    fallback = {"housing_units": 0, "equal": 0, "no_acs_estimate": 0}
    starts = np.flatnonzero(np.r_[True, bg[order][1:] != bg[order][:-1]])
    ends = np.r_[starts[1:], n]
    pl_bgs = set()
    for s, e in zip(starts, ends):
        idx = order[s:e]
        code = bg[idx[0]]
        pl_bgs.add(code)
        if code not in acs:
            fallback["no_acs_estimate"] += 1
            continue
        estimate = acs[code][0]
        occ, units = pl.occupied[idx].astype(float), pl.housing_units[idx].astype(float)
        if occ.sum() > 0:
            weights, kind = occ, "occupied"
        elif units.sum() > 0:
            weights, kind = units, "housing_units"
        else:
            weights, kind = np.ones(len(idx)), "equal"
        if estimate > 0 and kind != "occupied":
            fallback[kind] += 1
        households[idx] = estimate * weights / weights.sum()
    state_acs = {k: v for k, v in acs.items() if k.startswith(state_fips)}
    unmatched_acs = sorted(set(state_acs) - pl_bgs)

    block_jobs = np.array([jobs.get(g, 0) for g in pl.geoid], dtype=np.int64)
    known = set(pl.geoid)
    unmatched_jobs = {g: j for g, j in jobs.items() if g not in known}

    tract_rank = np.array([np.nan if (r := (svi.get(g[:11]) or {}).get("RPL_THEMES")) is None else r
                           for g in pl.geoid])

    keep = (np.nan_to_num(households, nan=1.0) > 0) | (block_jobs > 0)
    notes = {
        "blocks": n,
        "blocksKept": int(keep.sum()),
        "blockGroups": len(pl_bgs),
        "householdsShareFallbacks": {k: v for k, v in fallback.items() if k != "no_acs_estimate"},
        "blockGroupsWithoutAcsEstimate": fallback["no_acs_estimate"],
        "acsBlockGroupsNotInBlocks": len(unmatched_acs),
        "acsHouseholdsNotInBlocks": int(sum(state_acs[k][0] for k in unmatched_acs)),
        "acsHouseholdsTotal": int(sum(v[0] for v in state_acs.values())),
        "packHouseholdsTotal": round(float(np.nansum(households[keep])), 1),
        "lodesBlocksNotInBlocks": len(unmatched_jobs),
        "lodesJobsNotInBlocks": int(sum(unmatched_jobs.values())),
        "lodesJobsTotal": int(sum(jobs.values())),
        "blocksWithoutSviRank": int(np.isnan(tract_rank[keep]).sum()),
    }
    idx = np.flatnonzero(keep)
    return BlockRows(
        geoid=[pl.geoid[i] for i in idx], county=[pl.geoid[i][:5] for i in idx],
        lat=pl.lat[idx], lon=pl.lon[idx], households=np.round(households[idx], 3),
        jobs=block_jobs[idx], svi=tract_rank[idx], notes=notes)


def station_rows(stations: list[dict], rings: list[np.ndarray], blocks: BlockRows) -> StationRows:
    """Stations inside the boundary or within STATION_MARGIN_MI of it, each assigned to the
    county of its nearest kept block. Assignment only decides which pack carries a station;
    the app fetches every pack whose extent reaches its sites, so it sees all of them."""
    us = [s for s in stations if s["country"] == "US"]
    allpts = np.concatenate(rings)
    pad = STATION_MARGIN_MI / geo.MI_PER_DEGREE * 1.5
    lo0, la0 = allpts.min(axis=0) - [pad * 1.4, pad]
    lo1, la1 = allpts.max(axis=0) + [pad * 1.4, pad]
    near = [s for s in us if lo0 <= s["lon"] <= lo1 and la0 <= s["lat"] <= la1]
    lons = np.array([s["lon"] for s in near])
    lats = np.array([s["lat"] for s in near])
    inside = np.array([geo.point_in_rings(lo, la, rings) for lo, la in zip(lons, lats)], dtype=bool)
    dist = np.zeros(len(near))
    if (~inside).any():
        dist[~inside] = geo.distance_to_rings_mi(lons[~inside], lats[~inside], rings)
    keep = inside | (dist <= STATION_MARGIN_MI)
    idx = np.flatnonzero(keep)
    nearest = geo.nearest_index(lons[idx], lats[idx], blocks.lon, blocks.lat)
    order = np.argsort([near[i]["id"] for i in idx], kind="stable")
    idx, nearest = idx[order], nearest[order]
    return StationRows(
        id=[f"afdc:{near[i]['id']}" for i in idx],
        county=[blocks.county[j] for j in nearest],
        lat=lats[idx], lon=lons[idx],
        l2=np.array([near[i]["l2"] for i in idx], dtype=np.int64),
        dcfc=np.array([near[i]["dcfc"] for i in idx], dtype=np.int64),
        notes={"stationsUS": len(us), "stationsInside": int(inside.sum()),
               "stationsWithinMargin": int((~inside & keep).sum()),
               "marginMiles": STATION_MARGIN_MI},
    )


def coverage_rings(rings: list[np.ndarray], tolerance_m: float) -> list[np.ndarray]:
    """The boundary simplified for the browser. Rings that collapse are dropped."""
    out = []
    for ring in rings:
        simple = geo.simplify_ring(ring, tolerance_m)
        if len(simple) >= 4:
            out.append(np.round(simple, 6))
    return out
