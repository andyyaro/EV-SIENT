"""The public data hub builder (platform/hub/, DEC-025), on small synthetic inputs.

No network: every upstream file is written here in its publisher's layout (ACS table-based
summary file, P.L. 94-171 zip, LODES WAC csv.gz, SVI csv, AFDC csv, TIGER shapefile zip) for an
invented one-degree square "state" with two counties, and the build runs with --offline.
The Parquet parts need pyarrow, which only the hub builder installs; they skip without it.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "platform" / "hub"))

from hubbuild import estimates, geo, readers, sources  # noqa: E402

# The invented state: lon -78..-77, lat 37..38, FIPS 51 (the builder's state), two counties.
RING = [(-78.0, 37.0), (-78.0, 38.0), (-77.0, 38.0), (-77.0, 37.0), (-78.0, 37.0)]

# Blocks: (GEOID15, lat, lon, housing units, occupied)
BLOCKS = [
    ("510010001001000", 37.50, -77.50, 50, 40),
    ("510010001001001", 37.51, -77.50, 30, 20),
    ("510010001001002", 37.52, -77.50, 0, 0),      # no homes; jobs below keep it
    ("510010001001003", 37.80, -77.80, 0, 0),      # no homes, no jobs: dropped
    ("510030002001000", 37.20, -77.20, 100, 80),
]
ACS = {"510010001001": (90, 12), "510030002001": (100, 30)}
JOBS = {"510010001001000": 15, "510010001001002": 400, "510030002001000": 7}
SVI = {"51001000100": 0.75, "51003000200": -999}   # -999: SVI gives no rank
STATIONS = [  # (id, lat, lon, l2, dcfc, state)
    (101, 37.505, -77.505, 4, 0, "VA"),
    (102, 37.20, -77.21, "", 2, "VA"),                  # blank L2 count means none
    (103, 37.50, -76.98, 2, 1, "MD"),                   # about 1.1 miles outside: kept
    (104, 40.00, -75.00, 6, 6, "PA"),                   # far away: dropped
]


# ---------- writers for each publisher's layout ----------

def write_acs(path: Path) -> None:
    lines = ["GEO_ID|B11001_E001|B11001_M001", "0400000US51|190|20"]
    lines += [f"1500000US{g}|{e}|{m}" for g, (e, m) in ACS.items()]
    path.write_text("\n".join(lines) + "\n")


def _geo_line(sumlev: str, logrecno: str, geocode: str, name: str, hu: int, lat: float, lon: float) -> str:
    p = [""] * readers.GEO_FIELDS
    p[0], p[1], p[2], p[7], p[9] = "PLST", "VA", sumlev, logrecno, geocode
    p[-10], p[-6], p[-5], p[-4] = name, str(hu), f"{lat:+.7f}", f"{lon:+.7f}"
    return "|".join(p)


def _seg2_line(logrecno: str, total: int, occupied: int) -> str:
    p = ["0"] * readers.SEG2_FIELDS
    p[4], p[readers.H1_TOTAL], p[readers.H1_TOTAL + 1] = logrecno, str(total), str(occupied)
    return "|".join(p)


def write_pl(path: Path, hu_override: int | None = None) -> None:
    geo_lines = [_geo_line("050", "0000001", "51001", "First County", 0, 37.5, -77.5),
                 _geo_line("050", "0000002", "51003", "Second County", 0, 37.2, -77.2)]
    seg = []
    for i, (g, lat, lon, hu, occ) in enumerate(BLOCKS):
        rec = f"{100 + i:07d}"
        geo_lines.append(_geo_line("750", rec, g, f"Block {g[-4:]}", hu, lat, lon))
        seg.append(_seg2_line(rec, hu if hu_override is None or i else hu_override, occ))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("vageo2020.pl", "\n".join(geo_lines) + "\n")
        z.writestr("va000022020.pl", "\n".join(seg) + "\n")


def write_lodes(path: Path) -> None:
    text = "w_geocode,C000,CA01\n" + "".join(f"{g},{j},0\n" for g, j in JOBS.items())
    path.write_bytes(gzip.compress(text.encode()))


def write_svi(path: Path) -> None:
    cols = readers.SVI_COLUMNS
    lines = [",".join(cols)] + [",".join([f, str(r)] + [str(r)] * 4) for f, r in SVI.items()]
    path.write_text("\n".join(lines) + "\n")


def write_afdc(path: Path, rows=STATIONS, status: str = "E") -> None:
    cols = list(readers.AFDC_COLUMNS.values())
    out = io.StringIO()
    out.write(",".join(cols) + "\n")
    for sid, lat, lon, l2, dcfc, state in rows:
        values = {"ID": sid, "State": state, "Latitude": lat, "Longitude": lon, "EV Level1 EVSE Num": "",
                  "EV Level2 EVSE Num": l2, "EV DC Fast Count": dcfc, "EV Network": "Non-Networked",
                  "Status Code": status, "Access Code": "public", "Country": "US",
                  "Date Last Confirmed": "2026-10-01", "Fuel Type Code": "ELEC"}
        out.write(",".join(str(values[c]) for c in cols) + "\n")
    path.write_text(out.getvalue())


def write_tiger(path: Path) -> None:
    """A one-polygon TIGER-style state shapefile: .shp, .shx and .dbf with STATEFP."""
    pts = np.array(RING, dtype="<f8")
    content = struct.pack("<i", 5) + struct.pack("<4d", -78, 37, -77, 38) + struct.pack("<ii", 1, len(pts))
    content += struct.pack("<i", 0) + pts.tobytes()
    record = struct.pack(">ii", 1, len(content) // 2) + content
    header = lambda length: (struct.pack(">i", 9994) + b"\0" * 20 + struct.pack(">i", length // 2)
                             + struct.pack("<ii", 1000, 5) + struct.pack("<4d", -78, 37, -77, 38) + b"\0" * 32)
    shp = header(100 + len(record)) + record
    shx = header(108) + struct.pack(">ii", 50, len(content) // 2)
    fields = [("STATEFP", 2), ("NAME", 20)]
    dbf = struct.pack("<BBBBIHH", 3, 126, 1, 1, 1, 32 + 32 * len(fields) + 1, 1 + 22) + b"\0" * 20
    for name, length in fields:
        dbf += name.encode().ljust(11, b"\0") + b"C" + b"\0" * 4 + bytes([length]) + b"\0" * 15
    dbf += b"\x0d" + b" " + b"51" + b"Invented".ljust(20) + b"\x1a"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("tl_2026_us_state.shp", shp)
        z.writestr("tl_2026_us_state.shx", shx)
        z.writestr("tl_2026_us_state.dbf", dbf)


SPECS = {
    "acs-b11001": ("acsdt5y2024-b11001.dat", write_acs, "2020-2024"),
    "pl94171-va": ("va2020.pl.zip", write_pl, "2020"),
    "lodes-wac-va": ("va_wac_S000_JT00_2023.csv.gz", write_lodes, "LODES 8.4, 2023 jobs"),
    "svi-2022": ("SVI_2022_US.csv", write_svi, "2022 (ACS 2018-2022)"),
    "tiger-state-2026": ("tl_2026_us_state.zip", write_tiger, "2026"),
    "afdc-stations": ("alt_fuel_stations.csv", write_afdc, "snapshot"),
}


def make_inputs(root: Path) -> tuple[Path, Path]:
    """The cache and a registry pinning every file but the AFDC snapshot, as sources.json does."""
    cache = root / "cache"
    datasets = {}
    for name, (file, writer, vintage) in SPECS.items():
        path = cache / name / file
        path.parent.mkdir(parents=True, exist_ok=True)
        writer(path)
        pinned = name != "afdc-stations"
        if not pinned:
            path.with_name(file + ".meta.json").write_text(json.dumps(
                {"url": "https://example.invalid/afdc.csv", "retrievedUtc": "2026-10-18T12:00:00+00:00",
                 "lastModified": None}))
        datasets[name] = {
            "title": f"Synthetic {name}", "publisher": "Test publisher", "vintage": vintage,
            "published": None if not pinned else "2025-01-01", "licence": f"Public domain ({name}).",
            "url": f"https://example.invalid/{file}" + ("?fuel_type=ELEC" if not pinned else ""),
            "file": file, "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if pinned else None,
            **({"url_needs_api_key": True} if not pinned else {}),
        }
    registry = root / "sources.json"
    registry.write_text(json.dumps({"schema": "evsient-hub-sources/1", "datasets": datasets}))
    return cache, registry


# ---------- geometry ----------

def test_haversine_matches_a_known_distance():
    # One degree of latitude on the mean-radius sphere.
    assert float(geo.haversine_mi(37.0, -77.0, 38.0, -77.0)) == pytest.approx(69.093, abs=0.001)
    assert float(geo.haversine_mi(37.5, -77.5, 37.5, -77.5)) == 0.0


def test_point_in_rings_and_distance_to_edge():
    rings = [np.array(RING)]
    assert geo.point_in_rings(-77.5, 37.5, rings)
    assert not geo.point_in_rings(-76.9, 37.5, rings)
    # 0.02 degrees of longitude east of the edge at 37.5 N is about 1.1 miles.
    d = geo.distance_to_rings_mi(np.array([-76.98]), np.array([37.5]), rings)[0]
    assert d == pytest.approx(0.02 * geo.MI_PER_DEGREE * np.cos(np.radians(37.5)), rel=1e-6)


def test_simplify_keeps_corners_and_drops_collinear_points():
    line = np.array([(-78.0, 37.0), (-78.0, 37.5), (-78.0, 38.0), (-77.0, 38.0), (-77.0, 37.0), (-78.0, 37.0)])
    out = geo.simplify_ring(line, 25.0)
    assert len(out) == 5 and (-78.0, 37.5) not in [tuple(p) for p in out]


# ---------- readers refuse a changed layout ----------

def test_readers_read_each_publishers_layout(tmp_path):
    for name, (file, writer, _) in SPECS.items():
        writer(tmp_path / file)
    assert readers.read_acs_households(tmp_path / SPECS["acs-b11001"][0]) == ACS
    pl = readers.read_pl_blocks(tmp_path / "va2020.pl.zip", "VA")
    assert pl.geoid == [b[0] for b in BLOCKS] and list(pl.occupied) == [b[4] for b in BLOCKS]
    assert pl.county_names == {"51001": "First County", "51003": "Second County"}
    assert readers.read_lodes_wac(tmp_path / SPECS["lodes-wac-va"][0]) == JOBS
    svi = readers.read_svi(tmp_path / "SVI_2022_US.csv")
    assert svi["51001000100"]["RPL_THEMES"] == 0.75 and svi["51003000200"]["RPL_THEMES"] is None
    stations = readers.read_afdc(tmp_path / "alt_fuel_stations.csv")
    assert [(s["id"], s["l2"], s["dcfc"]) for s in stations][:2] == [(101, 4, 0), (102, 0, 2)]
    rings = readers.read_state_rings(tmp_path / "tl_2026_us_state.zip", "51")
    assert [tuple(p) for p in rings[0]] == RING


def test_readers_refuse_a_changed_layout(tmp_path):
    bad = tmp_path / "acs.dat"
    bad.write_text("GEO_ID|B11001_E002|B11001_M002\n")
    with pytest.raises(readers.SourceFormatError, match="expected GEO_ID"):
        readers.read_acs_households(bad)
    write_pl(tmp_path / "pl.zip", hu_override=49)
    with pytest.raises(readers.SourceFormatError, match="HU100"):
        readers.read_pl_blocks(tmp_path / "pl.zip", "VA")
    write_afdc(tmp_path / "afdc.csv", status="P")
    with pytest.raises(readers.SourceFormatError, match="not an open, public electric station"):
        readers.read_afdc(tmp_path / "afdc.csv")


# ---------- estimates ----------

def test_households_are_shared_by_occupied_homes_and_conserved(tmp_path):
    write_pl(tmp_path / "pl.zip")
    pl = readers.read_pl_blocks(tmp_path / "pl.zip", "VA")
    svi = {f: {"RPL_THEMES": (None if r < 0 else r)} for f, r in SVI.items()}
    rows = estimates.block_rows(pl, ACS, JOBS, svi, "51")
    by_id = dict(zip(rows.geoid, rows.households))
    assert by_id["510010001001000"] == pytest.approx(60.0)    # 90 x 40/60
    assert by_id["510010001001001"] == pytest.approx(30.0)
    assert by_id["510010001001002"] == 0.0                     # kept for its jobs
    assert "510010001001003" not in by_id                      # nothing there: dropped
    assert rows.notes["packHouseholdsTotal"] == rows.notes["acsHouseholdsTotal"] == 190
    assert np.isnan(rows.svi[rows.geoid.index("510030002001000")])   # no rank stays empty, never 0


def test_stations_near_the_line_are_kept_and_far_ones_dropped(tmp_path):
    write_pl(tmp_path / "pl.zip")
    pl = readers.read_pl_blocks(tmp_path / "pl.zip", "VA")
    rows = estimates.block_rows(pl, ACS, JOBS, {}, "51")
    stations = [{"id": s[0], "lat": s[1], "lon": s[2], "l2": s[3] or 0, "dcfc": s[4], "country": "US",
                 "state": s[5]} for s in STATIONS]
    st = estimates.station_rows(stations, [np.array(RING)], rows)
    assert st.id == ["afdc:101", "afdc:102", "afdc:103"]
    assert st.county == ["51001", "51003", "51003"]   # by nearest kept block
    assert st.notes["stationsWithinMargin"] == 1


# ---------- sources: pins, cache and keys ----------

def test_api_key_never_reaches_a_recorded_url():
    url = "https://developer.example/api/alt-fuel-stations/v1.csv?fuel_type=ELEC&api_key=SECRET123"
    assert "SECRET123" not in sources.public_url(url) and "fuel_type=ELEC" in sources.public_url(url)


def test_a_changed_upstream_file_stops_the_build(tmp_path):
    cache, registry = make_inputs(tmp_path)
    spec = json.loads(registry.read_text())["datasets"]["acs-b11001"]
    (cache / "acs-b11001" / spec["file"]).write_text("GEO_ID|B11001_E001|B11001_M001\n")
    with pytest.raises(sources.SourceError, match="pins"):
        sources.fetch("acs-b11001", spec, cache, offline=True)


def test_offline_never_downloads(tmp_path):
    spec = {"url": "https://example.invalid/x.csv", "file": "x.csv", "sha256": None}
    with pytest.raises(sources.SourceError, match="--offline"):
        sources.fetch("x", spec, tmp_path, offline=True)


# ---------- a whole release (needs pyarrow) ----------

@pytest.fixture
def built(tmp_path):
    pytest.importorskip("pyarrow")
    from hubbuild import build

    cache, registry = make_inputs(tmp_path)
    out = tmp_path / "out"
    manifest = build.build(registry, cache, out, "2026-10-18.1", offline=True, log=lambda *_: None)
    return build, registry, cache, out, manifest


def test_release_layout_pointers_and_checksums(built):
    _, _, _, out, manifest = built
    hub = out / "hub"
    latest = json.loads((hub / "latest.json").read_text())
    assert latest["hubVersion"] == "2026-10-18.1"
    man_bytes = (hub / latest["manifest"]).read_bytes()
    assert hashlib.sha256(man_bytes).hexdigest() == latest["manifestSha256"]
    assert [g["passed"] for g in manifest["gates"]] == [True] * 5
    assert [p["county"] for p in manifest["packs"]] == ["51001", "51003"]
    for p in manifest["packs"] + manifest["tables"]:
        assert hashlib.sha256((hub / p["key"]).read_bytes()).hexdigest() == p["sha256"]
    assert set(manifest["fields"]) == {"nearby_households_1mi", "nearby_jobs_1mi", "equity_gap_index",
                                       "existing_l2_ports_1mi", "existing_dcfc_ports_3mi"}
    assert set(manifest["notYet"]) == {"aadt_nearest", "amenities_count_0_5mi", "ev_share_local"}
    for spec in manifest["fields"].values():
        assert spec["vintage"] and spec["sourceDate"] and spec["licence"] and spec["method"]
    assert (hub / "stac" / "catalog.json").is_file()
    # The AFDC snapshot is dated by when it was taken, and no api_key is recorded anywhere.
    assert manifest["datasets"]["afdc-stations"]["vintage"] == "2026-10-18"
    assert "api_key" not in man_bytes.decode()


def test_pack_rows(built):
    import pyarrow.parquet as pq

    _, _, _, out, manifest = built
    pack = pq.read_table(out / "hub" / manifest["packs"][0]["key"]).to_pylist()
    blocks = {r["id"]: r for r in pack if r["kind"] == "block"}
    assert blocks["510010001001000"]["households"] == pytest.approx(60.0)
    assert blocks["510010001001002"]["jobs"] == 400
    assert blocks["510010001001000"]["svi"] == 0.75
    assert [r["l2_ports"] for r in pack if r["kind"] == "station"] == [4]
    other = pq.read_table(out / "hub" / manifest["packs"][1]["key"]).to_pylist()
    assert [r["svi"] for r in other if r["kind"] == "block"] == [None]
    stations = {r["id"]: r for r in other if r["kind"] == "station"}
    assert stations["afdc:102"]["l2_ports"] == 0                 # blank in the AFDC file: no ports
    assert stations["afdc:103"]["dcfc_ports"] == 1 and stations["afdc:103"]["households"] is None


def test_releases_are_immutable_and_a_new_one_moves_the_pointer(built):
    build, registry, cache, out, first = built
    from hubbuild import release

    with pytest.raises(release.ImmutableKeyError):
        build.build(registry, cache, out, "2026-10-18.1", offline=True, log=lambda *_: None)
    second = build.build(registry, cache, out, "2026-10-18.2", offline=True, log=lambda *_: None)
    hub = out / "hub"
    assert json.loads((hub / "latest.json").read_text())["hubVersion"] == "2026-10-18.2"
    assert (hub / first["packs"][0]["key"]).is_file()        # the old release stays readable
    assert [t["key"] for t in second["tables"]] == [t["key"] for t in first["tables"]]   # same inputs, same keys
    items = json.loads((hub / "stac" / "county-packs" / "collection.json").read_text())["links"]
    assert {"county-packs-2026-10-18.1", "county-packs-2026-10-18.2"} <= {
        l["href"].split("/")[-1][:-5] for l in items if l["rel"] == "item"}


def test_row_count_gate_stops_a_release_that_shrinks(built, monkeypatch):
    build, registry, cache, out, _ = built
    from hubbuild import release

    real = estimates.block_rows

    def fewer(*args, **kwargs):
        rows = real(*args, **kwargs)
        keep = [0]
        return estimates.BlockRows([rows.geoid[i] for i in keep], [rows.county[i] for i in keep], rows.lat[keep],
                                   rows.lon[keep], rows.households[keep], rows.jobs[keep], rows.svi[keep], rows.notes)

    monkeypatch.setattr(build.estimates, "block_rows", fewer)
    with pytest.raises(release.GateError, match="row-count change"):
        build.build(registry, cache, out, "2026-10-18.3", offline=True, log=lambda *_: None)
    assert json.loads((out / "hub" / "latest.json").read_text())["hubVersion"] == "2026-10-18.1"
    manifest = build.build(registry, cache, out, "2026-10-18.3", offline=True, allow_row_change=True,
                           log=lambda *_: None)
    assert manifest["gates"][1]["passed"]
