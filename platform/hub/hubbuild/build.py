"""One hub release, from the registry to published keys. `build()` is the whole pipeline."""

from __future__ import annotations

import json
import platform
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import BUILDER_VERSION, estimates, geo, readers, release, sources

COVERAGE_TOLERANCE_M = 25.0

#: The dataset groups the fields name: one logical source published as one file per state.
#: sources.json describes each group and lists its members; every published state's blocks file
#: must be in `pl94171` and its jobs file in `lodes-wac`.
BLOCKS_GROUP, JOBS_GROUP = "pl94171", "lodes-wac"

#: What each field the hub fills is, in the words the planner sees beside every value. The app
#: computes these in the browser from a site's coordinates and the county packs; the build only
#: describes them. `requiresFullCircle`: offered only when the whole circle lies inside the
#: coverage boundary (every published state together), because the packs hold no blocks beyond it.
FIELDS = {
    "nearby_households_1mi": {
        "column": "households", "rowKind": "block", "aggregate": "sum", "radiusMiles": 1.0,
        "decimals": 0, "requiresFullCircle": True,
        "primary": "acs-b11001", "datasets": ["acs-b11001", BLOCKS_GROUP],
        "sourceLabel": "Census ACS 2020-2024, by 2020 block",
        "method": "Households from the Census Bureau's American Community Survey 2020-2024 for each "
                  "block group, shared among its 2020 census blocks by their occupied homes in the "
                  "2020 Census, then added up over the blocks whose centre is within 1 mile of the site.",
    },
    "nearby_jobs_1mi": {
        "column": "jobs", "rowKind": "block", "aggregate": "sum", "radiusMiles": 1.0,
        "decimals": 0, "requiresFullCircle": True,
        "primary": JOBS_GROUP, "datasets": [JOBS_GROUP, BLOCKS_GROUP],
        "sourceLabel": "Census LODES 8.4, 2023 jobs",
        "method": "Jobs counted at each 2020 census block in the Census Bureau's LODES 8.4 (2023), "
                  "added up over the blocks whose centre is within 1 mile of the site.",
    },
    "equity_gap_index": {
        "column": "svi", "rowKind": "block", "aggregate": "weighted_mean", "weight": "households",
        "radiusMiles": 1.0, "decimals": 3, "requiresFullCircle": True,
        "primary": "svi-2022", "datasets": ["svi-2022", "acs-b11001", BLOCKS_GROUP],
        "sourceLabel": "CDC/ATSDR SVI 2022, national rank",
        "method": "The CDC/ATSDR Social Vulnerability Index 2022 (national percentile, 0 least to 1 most "
                  "vulnerable) of the census tracts within 1 mile, averaged by their households. It is a "
                  "proxy for charging-equity need, not an index built for charging.",
    },
    "existing_l2_ports_1mi": {
        "column": "l2_ports", "rowKind": "station", "aggregate": "sum", "radiusMiles": 1.0,
        "decimals": 0, "requiresFullCircle": False,
        "primary": "afdc-stations", "datasets": ["afdc-stations"],
        "sourceLabel": "AFDC station list",
        "method": "Level 2 charging ports at open, public stations within 1 mile of the site, from the "
                  "Alternative Fuels Data Center's station list.",
    },
    "existing_dcfc_ports_3mi": {
        "column": "dcfc_ports", "rowKind": "station", "aggregate": "sum", "radiusMiles": 3.0,
        "decimals": 0, "requiresFullCircle": False,
        "primary": "afdc-stations", "datasets": ["afdc-stations"],
        "sourceLabel": "AFDC station list",
        "method": "DC fast charging ports at open, public stations within 3 miles of the site, from the "
                  "Alternative Fuels Data Center's station list.",
    },
}

#: Fields the engine scores that the build plan expects from the hub, and why this release does
#: not have them. Shown in the app so a planner knows the gap is the hub's, not their file's.
NOT_YET = {
    "aadt_nearest": "Not in this release. The plan pins road volumes from FHWA's HPMS 2024 (with VDOT "
                    "2025 counts in Virginia), and neither was available as a file to download when it was "
                    "built: VDOT's public traffic layer is a live map service whose counts end in 2022. "
                    "Choosing which road counts as the nearest arterial is also still a methods decision.",
    "amenities_count_0_5mi": "Not in this release. It needs an extract of Overture places for the states "
                             "the hub covers (an 11 GB global release) and an agreed list of which categories "
                             "count as amenities; neither has been built yet.",
    "ev_share_local": "Not in this release. County EV registrations come from Atlas EV Hub under the "
                      "ODbL licence, which the plan keeps in a separate pack that this release does not "
                      "build, and the total vehicles to divide by is still to be chosen.",
}


def _vintage_slug(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-." else "-" for c in text).strip("-").lower()


def _snapshot_date(inp: sources.Input) -> str:
    stamp = inp.last_modified or inp.retrieved_utc
    return stamp[:10] if stamp else datetime.now(timezone.utc).date().isoformat()


def _build_id(*parts: str) -> str:
    return release.sha256_bytes("\n".join([BUILDER_VERSION, *parts]).encode())[:12]


def _bbox(lons, lats) -> list[float]:
    return [round(float(np.min(lons)), 6), round(float(np.min(lats)), 6),
            round(float(np.max(lons)), 6), round(float(np.max(lats)), 6)]


def _none(values, cast):
    return [None if (isinstance(v, float) and np.isnan(v)) else cast(v) for v in values]


def in_prose(names: list[str]) -> str:
    """'Virginia', 'Virginia and Maryland', 'Virginia, Maryland and Illinois'."""
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def published_states(registry: dict) -> list[dict]:
    """The states this release covers, in the registry's order, each checked against its datasets."""
    states = registry.get("states") or []
    if not states:
        raise sources.SourceError("sources.json lists no states to publish")
    groups = registry.get("groups") or {}
    seen = set()
    for st in states:
        missing = [k for k in ("fips", "stusab", "name", "blocks", "jobs") if not st.get(k)]
        if missing:
            raise sources.SourceError(f"sources.json: state {st} has no {missing}")
        if st["fips"] in seen:
            raise sources.SourceError(f"sources.json: state {st['fips']} is listed twice")
        seen.add(st["fips"])
        for role, group in (("blocks", BLOCKS_GROUP), ("jobs", JOBS_GROUP)):
            if st[role] not in registry["datasets"]:
                raise sources.SourceError(f"sources.json: {st['name']} names {st[role]}, which is not a dataset")
            if st[role] not in (groups.get(group) or {}).get("members", []):
                raise sources.SourceError(f"sources.json: {st[role]} is not a member of the {group} group")
    return states


def group_records(registry: dict, inputs: dict, vintages: dict, published: dict) -> dict[str, dict]:
    """One manifest record per dataset group, refused unless its members agree on publisher,
    vintage, publication date and licence (a field names one source, so its parts must match)."""
    out = {}
    for gid, g in (registry.get("groups") or {}).items():
        members = list(g.get("members") or [])
        if not members or any(m not in inputs for m in members):
            raise sources.SourceError(f"sources.json: group {gid} names datasets that are not inputs")
        specs = [inputs[m].spec for m in members]
        agreed = {}
        for key, values in (("publisher", [s["publisher"] for s in specs]), ("licence", [s["licence"] for s in specs]),
                            ("licenceUrl", [s.get("licence_url") for s in specs]),
                            ("vintage", [vintages[m] for m in members]), ("sourceDate", [published[m] for m in members])):
            if len(set(values)) != 1:
                raise sources.SourceError(f"sources.json: the members of {gid} differ in {key}: {sorted(set(map(str, values)))}")
            agreed[key] = values[0]
        out[gid] = {"dataset": gid, "title": g["title"], "publisher": agreed["publisher"], "vintage": agreed["vintage"],
                    "published": agreed["sourceDate"], "licence": agreed["licence"], "licenceUrl": agreed["licenceUrl"],
                    "landing": g.get("landing"), "url": g.get("url"), "members": members,
                    "sourceDate": agreed["sourceDate"], "label": specs[0].get("label", "")}
    return out


def build(registry_path: Path, cache: Path, out: Path, hub_version: str, *, offline: bool = False,
          refresh: bool = False, allow_row_change: bool = False, log=print) -> dict:
    """Fetch, compute, stage, gate and publish one release. Returns its manifest."""
    if (out / "hub" / "releases" / hub_version).exists():
        raise release.ImmutableKeyError(f"hub/releases/{hub_version} already exists; releases are immutable. "
                                        f"Choose a new --hub-version.")
    registry = sources.load_registry(registry_path)
    states = published_states(registry)
    inputs = {k: sources.fetch(k, spec, cache, offline=offline, refresh=refresh)
              for k, spec in registry["datasets"].items()}
    for k, inp in inputs.items():
        log(f"input {k}: {inp.path.name} {inp.bytes:,} bytes sha256 {inp.sha256[:12]}")

    snapshot = _snapshot_date(inputs["afdc-stations"])
    published = {k: (inp.spec.get("published") or snapshot) for k, inp in inputs.items()}
    vintages = {k: (snapshot if inp.spec["vintage"] == "snapshot" else inp.spec["vintage"]) for k, inp in inputs.items()}
    groups = group_records(registry, inputs, vintages, published)
    for name, spec in FIELDS.items():
        unknown = [d for d in spec["datasets"] if d not in inputs and d not in groups]
        if unknown:
            raise sources.SourceError(f"field {name} names datasets that are neither inputs nor groups: {unknown}")

    log("reading national inputs")
    acs = readers.read_acs_households(inputs["acs-b11001"].path)
    svi = readers.read_svi(inputs["svi-2022"].path)
    stations = readers.read_afdc(inputs["afdc-stations"].path)
    tiger = inputs["tiger-state-2026"].path

    # Each state on its own, exactly as a one-state release builds it: its blocks, and the
    # stations inside it or within the margin of its own boundary, carried by its own counties.
    # A station near a shared border is in both states' packs; the app counts it once (by ID).
    per_state = []
    all_rings: list[np.ndarray] = []
    for st in states:
        log(f"computing {st['name']}")
        pl = readers.read_pl_blocks(inputs[st["blocks"]].path, st["stusab"])
        jobs = readers.read_lodes_wac(inputs[st["jobs"]].path)
        rings = readers.read_state_rings(tiger, st["fips"])
        all_rings += rings
        own = estimates.coverage_rings(rings, COVERAGE_TOLERANCE_M)
        blocks = estimates.block_rows(pl, acs, jobs, svi, st["fips"])
        stns = estimates.station_rows(stations, own, blocks)
        pts = np.concatenate(own)
        per_state.append({"state": st, "blocks": blocks, "stations": stns, "names": pl.county_names,
                          "bbox": _bbox(pts[:, 0], pts[:, 1])})
        del pl

    # Coverage: every published state together, with shared borders dissolved, so a site near
    # the line between two published states is measured to the outer edge, not to that line.
    coverage = estimates.coverage_rings(geo.dissolve_rings(all_rings), COVERAGE_TOLERANCE_M)
    coverage_name = in_prose([st.get("prose") or st["name"] for st in states])
    state_records = [{"fips": p["state"]["fips"], "stusab": p["state"]["stusab"], "name": p["state"]["name"],
                      "prose": p["state"].get("prose") or p["state"]["name"], "bbox": p["bbox"], "datasets": {"blocks": p["state"]["blocks"], "jobs": p["state"]["jobs"]}}
                     for p in per_state]

    staging = Path(tempfile.mkdtemp(prefix="evsient-hub-"))
    try:
        staged = release.Staged(staging)
        built = datetime.now(timezone.utc).isoformat(timespec="seconds")

        # Coverage and licences, inside the release folder.
        allpts = np.concatenate(coverage)
        cov_bbox = _bbox(allpts[:, 0], allpts[:, 1])
        cov_key = f"releases/{hub_version}/coverage.json"
        staged.write(cov_key, release.json_bytes({
            "schema": "evsient-hub-coverage/2", "name": coverage_name,
            "states": [{k: s[k] for k in ("fips", "stusab", "name", "bbox")} for s in state_records],
            "source": "tiger-state-2026", "toleranceMetres": COVERAGE_TOLERANCE_M,
            "bbox": cov_bbox, "rings": [r.tolist() for r in coverage],
        }))
        lic_key = f"releases/{hub_version}/licences.txt"
        lic_lines = [f"EV-SIENT public data hub {hub_version}: sources and licences", ""]
        for k, inp in inputs.items():
            s = inp.spec
            lic_lines += [f"{s['title']} ({k})", f"  Publisher: {s['publisher']}", f"  Vintage: {vintages[k]}",
                          f"  Source: {inp.url}", f"  Licence: {s['licence']}", ""]
        lic_lines += ["Derived values in the county packs (households shared to blocks, sums and averages) are",
                      "computed by the EV-SIENT hub builder and are not published or endorsed by any source above.", ""]
        staged.write(lic_key, "\n".join(lic_lines).encode("utf-8"))

        # County packs, one state at a time; listed by county FIPS.
        pack_meta_base = {"evsient.schema": "evsient-hub-pack/1", "evsient.hub_version": hub_version}
        packs = []
        for part in per_state:
            blocks, stns = part["blocks"], part["stations"]
            b_county = np.array(blocks.county)
            s_county = np.array(stns.county) if stns.id else np.array([], dtype=str)
            for fips in sorted(set(blocks.county) | set(stns.county)):
                bi = np.flatnonzero(b_county == fips)
                si = np.flatnonzero(s_county == fips)
                nb, ns = len(bi), len(si)
                columns = {
                    "kind": ["block"] * nb + ["station"] * ns,
                    "id": [blocks.geoid[i] for i in bi] + [stns.id[i] for i in si],
                    "lat": [float(x) for x in blocks.lat[bi]] + [float(x) for x in stns.lat[si]],
                    "lon": [float(x) for x in blocks.lon[bi]] + [float(x) for x in stns.lon[si]],
                    "households": _none(blocks.households[bi], float) + [None] * ns,
                    "jobs": [int(x) for x in blocks.jobs[bi]] + [None] * ns,
                    "svi": _none(blocks.svi[bi], float) + [None] * ns,
                    "l2_ports": [None] * nb + [int(x) for x in stns.l2[si]],
                    "dcfc_ports": [None] * nb + [int(x) for x in stns.dcfc[si]],
                }
                key = f"packs/{fips}/{hub_version}/core.parquet"
                release.write_parquet(staged.path(key), columns, release.PACK_SCHEMA,
                                      {**pack_meta_base, "evsient.county_fips": fips})
                entry = staged.entry(key)
                packs.append({
                    "county": fips, "state": part["state"]["fips"], "name": part["names"].get(fips, fips), **entry,
                    "rows": {"block": nb, "station": ns},
                    "bbox": _bbox(columns["lon"], columns["lat"]),
                })
        packs.sort(key=lambda p: p["county"])

        # National tables, content-addressed by build id.
        tables = []

        def table(dataset: str, vintage: str, name: str, columns: dict, schema: list, description: str,
                  input_ids: list[str]):
            bid = _build_id(name, *[inputs[i].sha256 for i in input_ids])
            key = f"data/{dataset}/{_vintage_slug(vintage)}/{bid}/{name}.parquet"
            release.write_parquet(staged.path(key), columns, schema,
                                  {"evsient.schema": f"evsient-hub-table/{name}/1", "evsient.dataset": dataset})
            tables.append({"dataset": dataset, "name": name, **staged.entry(key),
                           "rows": len(next(iter(columns.values()))), "description": description,
                           "inputs": input_ids})

        acs_ids = sorted(acs)
        table("acs-households", "2020-2024", "households_by_block_group", {
            "geoid": acs_ids, "households": [acs[g][0] for g in acs_ids],
            "households_moe": [acs[g][1] for g in acs_ids],
        }, [("geoid", "string"), ("households", "int32"), ("households_moe", "int32")],
            "ACS 2020-2024 5-year households (B11001) and margin of error for every block group in the United States.",
            ["acs-b11001"])
        svi_ids = sorted(svi)
        table("svi", "2022", "svi_by_tract", {
            "fips": svi_ids, **{c.lower(): [svi[f][c] for f in svi_ids] for c in readers.SVI_COLUMNS[1:]},
        }, [("fips", "string")] + [(c.lower(), "double") for c in readers.SVI_COLUMNS[1:]],
            "CDC/ATSDR SVI 2022 national percentile ranks (overall and four themes) for every census tract.",
            ["svi-2022"])
        st_sorted = sorted(stations, key=lambda s: s["id"])
        table("afdc-stations", snapshot, "stations", {
            "id": [s["id"] for s in st_sorted], "country": [s["country"] for s in st_sorted],
            "state": [s["state"] for s in st_sorted], "lat": [s["lat"] for s in st_sorted],
            "lon": [s["lon"] for s in st_sorted], "ev_level1": [s["l1"] for s in st_sorted],
            "ev_level2": [s["l2"] for s in st_sorted], "ev_dc_fast": [s["dcfc"] for s in st_sorted],
            "ev_network": [s["network"] for s in st_sorted],
            "date_last_confirmed": [s["confirmed"] for s in st_sorted],
        }, [("id", "int32"), ("country", "string"), ("state", "string"), ("lat", "double"), ("lon", "double"),
            ("ev_level1", "int32"), ("ev_level2", "int32"), ("ev_dc_fast", "int32"), ("ev_network", "string"),
            ("date_last_confirmed", "string")],
            "Open, public electric charging stations from the AFDC station list, with port counts by level.",
            ["afdc-stations"])

        datasets = {}
        for k, inp in inputs.items():
            rec = inp.record()
            rec["vintage"] = vintages[k]
            rec["sourceDate"] = published[k]
            datasets[k] = rec
        datasets.update(groups)
        fields = {}
        for name, spec in FIELDS.items():
            primary = datasets[spec["primary"]]
            fields[name] = {**spec, "vintage": primary["vintage"], "sourceDate": primary["sourceDate"],
                            "licence": primary["licence"]}

        manifest = {
            "schema": "evsient-hub-release/1",
            "hubVersion": hub_version,
            "builtUtc": built,
            "builder": {"version": BUILDER_VERSION, "python": platform.python_version(),
                        "pyarrow": __import__("pyarrow").__version__},
            "coverage": {"name": coverage_name, "states": state_records, **staged.entry(cov_key),
                         "bbox": cov_bbox, "stationMarginMiles": estimates.STATION_MARGIN_MI,
                         "rings": len(coverage), "vertices": int(sum(len(r) for r in coverage))},
            "licences": staged.entry(lic_key),
            "datasets": datasets,
            "fields": fields,
            "notYet": NOT_YET,
            "packSchema": [{"name": n, "type": t} for n, t in release.PACK_SCHEMA],
            "packs": packs,
            "tables": tables,
            "notes": {p["state"]["fips"]: {"state": p["state"]["stusab"], "blocks": p["blocks"].notes,
                                           "stations": p["stations"].notes} for p in per_state},
        }

        previous = None
        latest = out / "hub" / "latest.json"
        if latest.is_file():
            pointer = json.loads(latest.read_text())
            prev_path = out / "hub" / pointer["manifest"]
            if prev_path.is_file():
                previous = json.loads(prev_path.read_text())
        gates = release.check_gates(manifest, staged, previous, allow_row_change)
        manifest["gates"] = [g.record() for g in gates]
        for g in gates:
            log(f"gate {g.name}: {'pass' if g.passed else 'FAIL'} ({g.detail})")
        failed = [g for g in gates if not g.passed]
        if failed:
            raise release.GateError("release not published; failed gates: " + "; ".join(f"{g.name}: {g.detail}" for g in failed))

        man_key = f"releases/{hub_version}/manifest.json"
        staged.write(man_key, release.json_bytes(manifest))
        man_entry = staged.entry(man_key)

        # STAC: items are immutable; collections and the catalogue are pointers.
        pointers: dict[str, bytes] = {}
        catalog_children = []
        providers = lambda ids: [{"name": p, "roles": ["producer", "licensor"], "url": u} for p, u in dict.fromkeys(
            (inputs[i].spec["publisher"], inputs[i].spec.get("landing") or inputs[i].url) for i in ids)] + [
            {"name": "EV-SIENT public data hub", "roles": ["processor", "host"]}]
        item_id = f"county-packs-{hub_version}"
        staged.write(f"stac/county-packs/{item_id}.json", release.json_bytes(release.stac_item(
            item_id, "county-packs", built, cov_bbox,
            {p["county"]: {"href": f"../../{p['key']}", "type": "application/vnd.apache.parquet",
                           "title": p["name"], "roles": ["data"], "file:size": p["bytes"],
                           "evsient:sha256": p["sha256"]} for p in packs},
            {"evsient:hub_version": hub_version, "evsient:manifest": f"../../{man_key}",
             "evsient:states": [s["stusab"] for s in state_records]},
            f"./{item_id}.json")))
        pack_inputs = ["acs-b11001", *[st["jobs"] for st in states], "svi-2022", "afdc-stations",
                       *[st["blocks"] for st in states]]
        groups_out = [("county-packs", "County packs", "Per-county Parquet packs the planner reads in the browser: "
                       f"census blocks with households, jobs and an equity rank, and public charging stations, for "
                       f"{coverage_name}.", pack_inputs, [item_id], cov_bbox)]
        for t in tables:
            iid = f"{t['dataset']}-{t['key'].split('/')[2]}-{t['key'].split('/')[3]}"
            item_key = f"stac/{t['dataset']}/{iid}.json"
            # A table with unchanged inputs keeps its key, and its item was published with it: the
            # item is immutable too, so it is not written again with this build's time.
            if not (out / "hub" / item_key).is_file():
                staged.write(item_key, release.json_bytes(release.stac_item(
                    iid, t["dataset"], built, None,
                    {"data": {"href": f"../../{t['key']}", "type": "application/vnd.apache.parquet",
                              "roles": ["data"], "file:size": t["bytes"], "evsient:sha256": t["sha256"]}},
                    {"description": t["description"], "evsient:inputs": t["inputs"]}, f"./{iid}.json")))
            groups_out.append((t["dataset"], t["dataset"], t["description"], t["inputs"], [iid],
                               [-179.2, -14.6, 179.8, 71.4]))
        for cid, title, description, ids, new_items, bbox in groups_out:
            items = list(dict.fromkeys(release.existing_items(out, cid) + new_items))
            lic = "; ".join(dict.fromkeys(inputs[i].spec["licence"].split(".")[0] for i in ids))
            pointers[f"stac/{cid}/collection.json"] = release.json_bytes(release.stac_collection(
                cid, title, description, lic, f"../../{lic_key}", bbox, items, providers(ids)))
            catalog_children.append(cid)
        old_catalog = out / "hub" / "stac" / "catalog.json"
        if old_catalog.is_file():
            for l in json.loads(old_catalog.read_text()).get("links", []):
                if l.get("rel") == "child":
                    catalog_children.append(l["href"].split("/")[1])
        pointers["stac/catalog.json"] = release.json_bytes({
            "type": "Catalog", "stac_version": release.STAC_VERSION, "id": "evsient-hub",
            "title": "EV-SIENT public data hub",
            "description": "Public datasets and per-county packs for the EV-SIENT Planner. Current release: "
                           f"{hub_version} (see ../latest.json).",
            "links": [{"rel": "root", "href": "./catalog.json", "type": "application/json"},
                      {"rel": "self", "href": "./catalog.json", "type": "application/json"}]
                     + [{"rel": "child", "href": f"./{c}/collection.json", "type": "application/json"}
                        for c in dict.fromkeys(catalog_children)],
        })
        pointers["latest.json"] = release.json_bytes({
            "schema": "evsient-hub-latest/1", "hubVersion": hub_version,
            "manifest": man_key, "manifestSha256": man_entry["sha256"], "published": built,
        })
        written = release.publish(staged, out, pointers)
        log(f"published {len(written)} keys under {out / 'hub'}")
        return manifest
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    import argparse

    here = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description="Build one EV-SIENT public data hub release.")
    p.add_argument("--hub-version", default=datetime.now(timezone.utc).strftime("%Y-%m-%d") + ".1",
                   help="new release name, e.g. 2026-10-18.1 (never reused)")
    p.add_argument("--sources", type=Path, default=here / "sources.json")
    p.add_argument("--cache", type=Path, default=here / "cache")
    p.add_argument("--out", type=Path, default=here / "out")
    p.add_argument("--offline", action="store_true", help="use only cached inputs; never download")
    p.add_argument("--refresh", action="store_true", help="take a new snapshot of live inputs (AFDC)")
    p.add_argument("--allow-row-change", action="store_true",
                   help=f"publish even if a state's pack rows change by more than {release.ROW_CHANGE_LIMIT * 100:.0f}%%")
    args = p.parse_args(argv)
    try:
        manifest = build(args.sources, args.cache, args.out, args.hub_version, offline=args.offline,
                         refresh=args.refresh, allow_row_change=args.allow_row_change)
    except (sources.SourceError, readers.SourceFormatError, release.GateError, release.ImmutableKeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    total = sum(p["bytes"] for p in manifest["packs"])
    states = ", ".join(s["stusab"] for s in manifest["coverage"]["states"])
    print(f"hub {manifest['hubVersion']}: {len(manifest['packs'])} county packs for {states}, {total:,} bytes; "
          f"{len(manifest['tables'])} national tables")
    return 0
