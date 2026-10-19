"""Parsers for the upstream files, each in the format the publisher ships.

Every reader checks the header it expects and raises `SourceFormatError` with the file name when
the layout differs, instead of reading the wrong column. Archives are read in memory; nothing is
extracted to disk.
"""

from __future__ import annotations

import csv
import gzip
import io
import math
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np


class SourceFormatError(ValueError):
    """An upstream file is not in the layout this builder was written for."""


# ---------- ACS 5-year table-based summary file ----------

def read_acs_households(path: Path) -> dict[str, tuple[int, int | None]]:
    """B11001 (households) for every block group in the file: {12-digit GEOID: (estimate, MOE)}.

    The table-based summary file is pipe-delimited with a GEO_ID such as
    `1500000US510010901011`; summary level 150 is the block group.
    """
    out: dict[str, tuple[int, int | None]] = {}
    with open(path, encoding="utf-8", newline="") as f:
        header = f.readline().rstrip("\r\n").split("|")
        if header[:3] != ["GEO_ID", "B11001_E001", "B11001_M001"]:
            raise SourceFormatError(f"{path.name}: expected GEO_ID|B11001_E001|B11001_M001, got {header[:3]}")
        for line in f:
            parts = line.rstrip("\r\n").split("|")
            geo = parts[0]
            if not geo.startswith("1500000US"):
                continue
            geoid = geo[len("1500000US"):]
            if len(geoid) != 12 or not geoid.isdigit():
                raise SourceFormatError(f"{path.name}: unexpected block group id {geo!r}")
            try:
                estimate = int(parts[1])
            except ValueError:
                continue  # a suppressed or blank estimate is left out, never read as 0
            moe = int(parts[2]) if parts[2].lstrip("-").isdigit() else None
            out[geoid] = (estimate, moe)
    return out


# ---------- 2020 Census P.L. 94-171 redistricting file ----------

@dataclass
class PlBlocks:
    geoid: list[str]
    lat: np.ndarray
    lon: np.ndarray
    housing_units: np.ndarray
    occupied: np.ndarray
    county_names: dict[str, str]


GEO_FIELDS = 97          # vageo2020.pl, 2020 P.L. 94-171 technical documentation
SEG2_FIELDS = 152        # file 2: P3, P4 and H1
H1_TOTAL = 149           # H0010001 total housing units; H0010002 occupied follows


def read_pl_blocks(path: Path, stusab: str) -> PlBlocks:
    """Every 2020 census block in a state's P.L. 94-171 zip, with its internal point,
    housing units (H1 total) and occupied housing units (H1 occupied: 2020 households).

    The geoheader (`{st}geo2020.pl`) gives the block code and internal point; segment 2
    (`{st}000022020.pl`) gives H1. The two are joined on LOGRECNO, and the geoheader's own
    HU100 must equal H1's total for every block or the file is refused.
    """
    st = stusab.lower()
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        geo_name, seg_name = f"{st}geo2020.pl", f"{st}000022020.pl"
        if geo_name not in names or seg_name not in names:
            raise SourceFormatError(f"{path.name}: expected {geo_name} and {seg_name}")
        blocks: dict[str, tuple[str, int, float, float]] = {}
        counties: dict[str, str] = {}
        with z.open(geo_name) as raw:
            for line in io.TextIOWrapper(raw, encoding="latin-1"):
                p = line.rstrip("\r\n").split("|")
                if len(p) != GEO_FIELDS:
                    raise SourceFormatError(f"{path.name}: geoheader has {len(p)} fields, expected {GEO_FIELDS}")
                sumlev, logrecno, geocode = p[2], p[7], p[9]
                if sumlev == "050":
                    counties[geocode] = p[-10]
                elif sumlev == "750":
                    if len(geocode) != 15:
                        raise SourceFormatError(f"{path.name}: block code {geocode!r} is not 15 digits")
                    blocks[logrecno] = (geocode, int(p[-6]), float(p[-5]), float(p[-4]))
        hu: dict[str, tuple[int, int]] = {}
        with z.open(seg_name) as raw:
            for line in io.TextIOWrapper(raw, encoding="latin-1"):
                p = line.rstrip("\r\n").split("|")
                if len(p) != SEG2_FIELDS:
                    raise SourceFormatError(f"{path.name}: segment 2 has {len(p)} fields, expected {SEG2_FIELDS}")
                if p[4] in blocks:
                    hu[p[4]] = (int(p[H1_TOTAL]), int(p[H1_TOTAL + 1]))
    geoid, lat, lon, units, occupied = [], [], [], [], []
    for logrecno, (code, hu100, la, lo) in sorted(blocks.items(), key=lambda kv: kv[1][0]):
        if logrecno not in hu:
            raise SourceFormatError(f"{path.name}: block {code} has no H1 row")
        total, occ = hu[logrecno]
        if total != hu100:
            raise SourceFormatError(f"{path.name}: block {code} H1 total {total} != HU100 {hu100}")
        geoid.append(code)
        lat.append(la)
        lon.append(lo)
        units.append(total)
        occupied.append(occ)
    return PlBlocks(geoid, np.array(lat), np.array(lon), np.array(units, dtype=np.int64),
                    np.array(occupied, dtype=np.int64), counties)


# ---------- LODES workplace area characteristics ----------

def read_lodes_wac(path: Path) -> dict[str, int]:
    """Total jobs (C000) by 2020 census block, from a LODES 8 WAC file (csv.gz)."""
    out: dict[str, int] = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        if header[:2] != ["w_geocode", "C000"]:
            raise SourceFormatError(f"{path.name}: expected w_geocode,C000, got {header[:2]}")
        for row in reader:
            code = row[0].zfill(15)
            out[code] = out.get(code, 0) + int(row[1])
    return out


# ---------- CDC/ATSDR Social Vulnerability Index ----------

SVI_COLUMNS = ["FIPS", "RPL_THEMES", "RPL_THEME1", "RPL_THEME2", "RPL_THEME3", "RPL_THEME4"]


def read_svi(path: Path) -> dict[str, dict[str, float | None]]:
    """Tract percentile ranks, {11-digit FIPS: {column: rank or None}}. -999 means no rank."""
    out: dict[str, dict[str, float | None]] = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in SVI_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise SourceFormatError(f"{path.name}: missing columns {missing}")
        for row in reader:
            fips = row["FIPS"].strip().zfill(11)
            ranks: dict[str, float | None] = {}
            for c in SVI_COLUMNS[1:]:
                try:
                    v = float(row[c])
                except ValueError:
                    v = math.nan
                ranks[c] = None if (math.isnan(v) or v < 0) else v
            out[fips] = ranks
    return out


# ---------- AFDC alternative fuel stations ----------

AFDC_COLUMNS = {
    "id": "ID", "state": "State", "lat": "Latitude", "lon": "Longitude",
    "l1": "EV Level1 EVSE Num", "l2": "EV Level2 EVSE Num", "dcfc": "EV DC Fast Count",
    "network": "EV Network", "status": "Status Code", "access": "Access Code",
    "country": "Country", "confirmed": "Date Last Confirmed", "fuel": "Fuel Type Code",
}


def _int_or_zero(text: str) -> int:
    text = text.strip()
    return int(float(text)) if text else 0


def read_afdc(path: Path) -> list[dict]:
    """Open, public electric stations from an AFDC CSV export, one dict per station.

    A blank port count is a station with no ports of that level (AFDC leaves it blank rather than
    writing 0). Rows that are not open (`E`), not public or not electric are refused, because the
    download was asked for exactly those and anything else means the query changed.
    """
    out = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in AFDC_COLUMNS.values() if c not in (reader.fieldnames or [])]
        if missing:
            raise SourceFormatError(f"{path.name}: missing columns {missing}")
        for row in reader:
            if row["Fuel Type Code"] != "ELEC" or row["Status Code"] != "E" or row["Access Code"] != "public":
                raise SourceFormatError(f"{path.name}: station {row['ID']} is not an open, public electric station")
            try:
                lat, lon = float(row["Latitude"]), float(row["Longitude"])
            except ValueError:
                continue
            out.append({
                "id": int(row["ID"]), "state": row["State"], "country": row["Country"],
                "lat": lat, "lon": lon,
                "l1": _int_or_zero(row["EV Level1 EVSE Num"]),
                "l2": _int_or_zero(row["EV Level2 EVSE Num"]),
                "dcfc": _int_or_zero(row["EV DC Fast Count"]),
                "network": row["EV Network"], "confirmed": row["Date Last Confirmed"],
            })
    return out


# ---------- TIGER/Line state boundary (shapefile) ----------

def _dbf_records(data: bytes) -> list[dict[str, str]]:
    count = struct.unpack("<I", data[4:8])[0]
    header_len, record_len = struct.unpack("<HH", data[8:12])
    fields = []
    pos = 32
    while data[pos] != 0x0D:
        name = data[pos:pos + 11].split(b"\x00")[0].decode("ascii")
        fields.append((name, data[pos + 16]))
        pos += 32
    out = []
    for i in range(count):
        start = header_len + i * record_len
        rec = data[start:start + record_len]
        offset = 1  # deletion flag
        row = {}
        for name, length in fields:
            row[name] = rec[offset:offset + length].decode("utf-8", "replace").strip()
            offset += length
        out.append(row)
    return out


def read_state_rings(path: Path, statefp: str) -> list[np.ndarray]:
    """One state's boundary from a TIGER/Line state shapefile zip, as rings of (lon, lat)."""
    with zipfile.ZipFile(path) as z:
        stem = next((n[:-4] for n in z.namelist() if n.endswith(".shp")), None)
        if stem is None:
            raise SourceFormatError(f"{path.name}: no .shp member")
        records = _dbf_records(z.read(stem + ".dbf"))
        index = next((i for i, r in enumerate(records) if r.get("STATEFP") == statefp), None)
        if index is None:
            raise SourceFormatError(f"{path.name}: no state with STATEFP {statefp}")
        shx = z.read(stem + ".shx")
        offset = struct.unpack(">i", shx[100 + 8 * index:104 + 8 * index])[0] * 2
        shp = z.read(stem + ".shp")
    content = offset + 8
    shape_type = struct.unpack("<i", shp[content:content + 4])[0]
    if shape_type != 5:
        raise SourceFormatError(f"{path.name}: state {statefp} is shape type {shape_type}, expected 5 (polygon)")
    num_parts, num_points = struct.unpack("<ii", shp[content + 36:content + 44])
    parts = list(struct.unpack(f"<{num_parts}i", shp[content + 44:content + 44 + 4 * num_parts]))
    start = content + 44 + 4 * num_parts
    pts = np.frombuffer(shp[start:start + 16 * num_points], dtype="<f8").reshape(num_points, 2)
    bounds = parts + [num_points]
    return [pts[bounds[i]:bounds[i + 1]].copy() for i in range(num_parts)]
