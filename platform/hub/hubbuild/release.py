"""Writing a release: Parquet files, the manifest, the STAC catalogue and the pointers.

Layout under the output's `hub/` folder, which is exactly the `hub/` prefix in the bucket:

    packs/{county_fips}/{hub_version}/core.parquet          immutable
    data/{dataset}/{vintage}/{build_id}/{name}.parquet       immutable
    releases/{hub_version}/manifest.json, coverage.json, licences.txt    immutable
    stac/catalog.json, stac/{collection}/collection.json     pointers (rewritten each release)
    stac/{collection}/{item}.json                            immutable
    latest.json                                              pointer, written last

A release is built in a staging folder, checked by the gates, and only then copied into place.
A key that already exists is never overwritten with different bytes: releases are new keys and
only the pointers change.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

#: The plan's limits: 1-5 MB a pack, and no release over 2 GB.
PACK_MAX_BYTES = 5 * 1024 * 1024
RELEASE_MAX_BYTES = 2 * 1024 ** 3
#: Larger swings than this against the previous release stop the build unless allowed.
ROW_CHANGE_LIMIT = 0.20

PACK_SCHEMA = [
    ("kind", "string"), ("id", "string"), ("lat", "double"), ("lon", "double"),
    ("households", "double"), ("jobs", "int32"), ("svi", "double"),
    ("l2_ports", "int32"), ("dcfc_ports", "int32"),
]

POINTER_CACHE = "public, max-age=60"
IMMUTABLE_CACHE = "public, max-age=31536000, immutable"


class GateError(RuntimeError):
    """A release failed a quality gate and was not published."""


class ImmutableKeyError(RuntimeError):
    """A release would overwrite an existing key with different bytes."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_parquet(path: Path, columns: dict[str, list], schema: list[tuple[str, str]],
                  metadata: dict[str, str]) -> None:
    """One row group, Snappy (the codec hyparquet reads with no add-on), explicit types.

    Integers are int32 on purpose: hyparquet returns int64 as BigInt, which the app would have
    to convert one value at a time.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    types = {"string": pa.string(), "double": pa.float64(), "int32": pa.int32()}
    arrow_schema = pa.schema([(n, types[t]) for n, t in schema], metadata=metadata)
    table = pa.table({n: pa.array(columns[n], type=types[t]) for n, t in schema}, schema=arrow_schema)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, compression="snappy", row_group_size=max(1, table.num_rows),
                   use_dictionary=["kind"] if "kind" in columns else False, write_statistics=True)


def read_schema(path: Path) -> list[tuple[str, str]]:
    import pyarrow.parquet as pq

    names = {"string": "string", "large_string": "string", "double": "double", "int32": "int32"}
    return [(f.name, names.get(str(f.type), str(f.type))) for f in pq.read_schema(path)]


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=False, ensure_ascii=False) + "\n").encode("utf-8")


@dataclass
class Staged:
    """Files of one release, by key relative to hub/, before they are copied into place."""

    root: Path
    files: dict[str, Path] = field(default_factory=dict)

    def path(self, key: str) -> Path:
        p = self.root / "hub" / key
        p.parent.mkdir(parents=True, exist_ok=True)
        self.files[key] = p
        return p

    def write(self, key: str, data: bytes) -> Path:
        p = self.path(key)
        p.write_bytes(data)
        return p

    def entry(self, key: str) -> dict:
        data = self.files[key].read_bytes()
        return {"key": key, "sha256": sha256_bytes(data), "bytes": len(data)}


@dataclass
class Gate:
    name: str
    passed: bool
    detail: str

    def record(self) -> dict:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


def check_gates(manifest: dict, staged: Staged, previous: dict | None,
                allow_row_change: bool) -> list[Gate]:
    """The plan's five gates: schema, row-count change, coordinates, licence text, size."""
    gates: list[Gate] = []

    wrong = []
    for pack in manifest["packs"]:
        got = read_schema(staged.files[pack["key"]])
        if got != [tuple(c) for c in PACK_SCHEMA]:
            wrong.append(f"{pack['key']}: {got}")
    gates.append(Gate("schema", not wrong, "every pack has the pack schema" if not wrong else "; ".join(wrong)))

    rows_now = sum(p["rows"]["block"] + p["rows"]["station"] for p in manifest["packs"])
    if previous:
        rows_then = sum(p["rows"]["block"] + p["rows"]["station"] for p in previous.get("packs", []))
        change = abs(rows_now - rows_then) / rows_then if rows_then else 1.0
        ok = change <= ROW_CHANGE_LIMIT or allow_row_change
        detail = (f"{rows_now} pack rows against {rows_then} in {previous['hubVersion']} "
                  f"({change:.1%} change; limit {ROW_CHANGE_LIMIT:.0%}"
                  f"{', allowed by --allow-row-change' if allow_row_change and change > ROW_CHANGE_LIMIT else ''})")
    else:
        ok, detail = True, f"{rows_now} pack rows; no previous release to compare"
    gates.append(Gate("row-count change", ok, detail))

    lo0, la0, lo1, la1 = manifest["coverage"]["bbox"]
    pad = manifest["coverage"]["stationMarginMiles"] / 69.0 * 1.5
    outside = [p["county"] for p in manifest["packs"]
               if not (lo0 - pad <= p["bbox"][0] and p["bbox"][2] <= lo1 + pad
                       and la0 - pad <= p["bbox"][1] and p["bbox"][3] <= la1 + pad)]
    counties_ok = all(p["county"].startswith(manifest["coverage"]["stateFips"]) for p in manifest["packs"])
    gates.append(Gate("coordinates", not outside and counties_ok,
                      "every pack's rows are WGS84 longitude and latitude inside the coverage box"
                      if not outside and counties_ok else f"packs outside the coverage box: {outside}"))

    licences = staged.files[manifest["licences"]["key"]].read_text()
    unlicensed = [k for k, d in manifest["datasets"].items() if not d["licence"] or d["licence"] not in licences]
    gates.append(Gate("licence text", not unlicensed,
                      "every dataset's licence is in licences.txt" if not unlicensed else f"missing for {unlicensed}"))

    big = [p["key"] for p in manifest["packs"] if p["bytes"] > PACK_MAX_BYTES]
    total = sum(staged.files[k].stat().st_size for k in staged.files)
    gates.append(Gate("size", not big and total <= RELEASE_MAX_BYTES,
                      f"largest pack {max(p['bytes'] for p in manifest['packs']):,} bytes (limit {PACK_MAX_BYTES:,}); "
                      f"release {total:,} bytes (limit {RELEASE_MAX_BYTES:,})" + (f"; too large: {big}" if big else "")))
    return gates


def publish(staged: Staged, out: Path, pointers: dict[str, bytes]) -> list[str]:
    """Copy staged keys into out/hub/, refusing to change an existing key, then write pointers.

    Returns the keys actually written (unchanged keys already present are skipped)."""
    hub = out / "hub"
    written = []
    for key, src in sorted(staged.files.items()):
        dest = hub / key
        data = src.read_bytes()
        if dest.exists():
            if dest.read_bytes() != data:
                raise ImmutableKeyError(f"hub/{key} already exists with different content; releases never "
                                        f"overwrite a key. Build a new hub version instead.")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        written.append(key)
    # Pointers last, latest.json very last, so a reader never sees a pointer to a missing key.
    for key in sorted(pointers, key=lambda k: k == "latest.json"):
        dest = hub / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(pointers[key])
        written.append(key)
    return written


# ---------- STAC 1.1 ----------

STAC_VERSION = "1.1.0"


def stac_item(item_id: str, collection: str, datetime_utc: str, bbox: list[float] | None,
              assets: dict[str, dict], properties: dict, self_href: str) -> dict:
    geometry = None
    if bbox:
        lo0, la0, lo1, la1 = bbox
        geometry = {"type": "Polygon", "coordinates": [[[lo0, la0], [lo1, la0], [lo1, la1], [lo0, la1], [lo0, la0]]]}
    item = {
        "type": "Feature", "stac_version": STAC_VERSION, "id": item_id, "collection": collection,
        "geometry": geometry, "properties": {"datetime": datetime_utc, **properties},
        "links": [
            {"rel": "root", "href": "../catalog.json", "type": "application/json"},
            {"rel": "parent", "href": "./collection.json", "type": "application/json"},
            {"rel": "collection", "href": "./collection.json", "type": "application/json"},
            {"rel": "self", "href": self_href, "type": "application/geo+json"},
        ],
        "assets": assets,
    }
    if bbox:
        item["bbox"] = bbox
    return item


def stac_collection(collection_id: str, title: str, description: str, licence: str,
                    licence_href: str, bbox: list[float], items: list[str], providers: list[dict]) -> dict:
    return {
        "type": "Collection", "stac_version": STAC_VERSION, "id": collection_id, "title": title,
        "description": description, "license": "other", "providers": providers,
        "extent": {"spatial": {"bbox": [bbox]}, "temporal": {"interval": [[None, None]]}},
        "links": [
            {"rel": "root", "href": "../catalog.json", "type": "application/json"},
            {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
            {"rel": "self", "href": "./collection.json", "type": "application/json"},
            {"rel": "license", "href": licence_href, "type": "text/plain", "title": licence},
        ] + [{"rel": "item", "href": f"./{i}.json", "type": "application/geo+json"} for i in items],
    }


def existing_items(out: Path, collection: str) -> list[str]:
    path = out / "hub" / "stac" / collection / "collection.json"
    if not path.is_file():
        return []
    links = json.loads(path.read_text()).get("links", [])
    return [l["href"][2:-5] for l in links if l.get("rel") == "item"]
