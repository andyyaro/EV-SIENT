"""Build public-data upgrade extracts for newly added V2 sites.

This script upgrades selected V2 rows from planning assumptions toward stronger
public-data-supported values.

It calculates, when local raw exports are available:
- nearby_households_1mi from ACS household inputs when available
- nearby_jobs_1mi from LODES WAC + TIGER block groups
- aadt_nearest from VDOT traffic GeoJSON
- equity_gap_index from ACS equity tables + TIGER block groups
- amenities_count_0_5mi from an existing OSM reviewed extract when available

Run from the repository root:

    python src/build_v2_public_data_upgrades.py

Optional dependency:
    pyshp is used to read the TIGER block-group shapefile inside the ZIP.
    Install only if needed:

    python -m pip install pyshp

This script writes reviewable extracts under data/source_extracts/.
It does NOT automatically overwrite data/inputs/real_sites_v2.csv.
Review the outputs first, then decide whether to apply the values.
"""

from __future__ import annotations

import json
import math
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    import shapefile  # type: ignore
except ImportError:  # pragma: no cover
    shapefile = None

SITES_PATH = Path("data/inputs/real_sites_v2.csv")
RAW_DIR = Path("data/raw_exports")
OUT_DIR = Path("data/source_extracts")
TARGET_SITE_IDS = ["FFX003", "FFX004"]

TIGER_PATTERN = "tl_2024_51_bg"
ACS_HOUSEHOLDS_PATTERN = "B11001"
LODES_PATTERN = "va_wac_S000_JT00_2023"
VDOT_PATTERN = "VDOT_Bidirectional_Traffic_Volume_2025.geojson"
MILES_RADIUS = 1.0
METERS_PER_MILE = 1609.344

VA_COUNTY_FIPS = {
    "Fairfax County": "059",
    "Prince William County": "153",
    "Fairfax city": "600",
    "Manassas city": "683",
    "Manassas Park city": "685",
}

EQUITY_WEIGHTS = {
    "lower_income_component": 0.35,
    "no_vehicle_component": 0.30,
    "renter_component": 0.20,
    "multifamily_component": 0.15,
}


def find_first(pattern: str, folder: Path = RAW_DIR) -> Path | None:
    if not folder.exists():
        return None
    matches = sorted(p for p in folder.rglob("*") if pattern.lower() in p.name.lower())
    return matches[0] if matches else None


def clean_label(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text).replace("\ufeff", "").strip())


def to_number(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("-", "", regex=False)
        .str.replace("—", "", regex=False)
        .str.replace("(X)", "", regex=False)
        .str.replace("N", "", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce").fillna(0)


def tract_to_code(tract_text: str) -> str:
    tract_text = str(tract_text).strip()
    if "." in tract_text:
        left, right = tract_text.split(".", 1)
        return left.zfill(4) + right.ljust(2, "0")[:2]
    return tract_text.zfill(4) + "00"


def geography_text_to_geoid(text: Any) -> str | None:
    """Convert Census table-display geography text into a 12-digit block-group GEOID."""
    base = clean_label(text)
    base = base.split("!!", 1)[0].strip()

    match = re.match(
        r"Block Group\s+(\d+);\s+Census Tract\s+([0-9.]+);\s+(.+?);\s+Virginia$",
        base,
    )
    if not match:
        return None

    block_group, tract, county_name = match.groups()
    county_fips = VA_COUNTY_FIPS.get(county_name)
    if not county_fips:
        return None

    return "51" + county_fips + tract_to_code(tract) + block_group


def column_to_geoid(column_name: str) -> str | None:
    return geography_text_to_geoid(column_name)


def read_census_geo_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, low_memory=False)
    df.columns = [str(col).replace("\ufeff", "") for col in df.columns]

    if "GEO_ID" not in df.columns:
        raise ValueError(f"{path} does not contain GEO_ID")

    df = df[df["GEO_ID"].astype(str).str.contains("US", na=False)].copy()
    df["geoid"] = df["GEO_ID"].astype(str).str.extract(r"US(\d+)$", expand=False)
    return df


def find_col(df: pd.DataFrame, candidates: list[str]) -> str:
    for col in candidates:
        if col in df.columns:
            return col
    raise ValueError(f"None of these columns were found: {candidates}")


def estimate_column_candidates(df: pd.DataFrame) -> list[str]:
    cols = []
    for col in df.columns[1:]:
        key = label_key(str(col))
        if "margin" in key or "error" in key:
            continue
        if "estimate" in key:
            cols.append(col)
    return cols


def table_display_values(path: Path, col_candidates: list[str], row_matcher=None) -> pd.DataFrame:
    """Read Census table-display exports in either orientation.

    Supported shapes:
    1. rows are variables and columns are block groups, like B11001 from data.census.gov
    2. rows are block groups and columns are variables/estimates, like some equity exports
    """
    df = pd.read_csv(path, dtype=str, low_memory=False)
    df.columns = [str(col).replace("\ufeff", "") for col in df.columns]
    label_col = df.columns[0]
    labels = df[label_col].map(clean_label)

    # Shape 1: block groups are spread across columns.
    col_geoids = {col: column_to_geoid(col) for col in df.columns[1:]}
    if any(geoid is not None for geoid in col_geoids.values()):
        if row_matcher is None:
            raise ValueError(f"{path} is table-display style, but no row matcher was provided.")

        matched = df[labels.map(row_matcher)].copy()
        if matched.empty:
            available_labels = [label for label in labels.tolist() if label and label.lower() != "nan"]
            raise ValueError(
                f"No matching row labels found in {path}. "
                f"First labels seen: {available_labels[:10]}"
            )

        value_by_geoid: dict[str, float] = {}
        for col, geoid in col_geoids.items():
            if geoid is None:
                continue
            total = float(to_number(matched[col]).sum())
            value_by_geoid[geoid] = value_by_geoid.get(geoid, 0.0) + total

        return pd.DataFrame({"geoid": list(value_by_geoid.keys()), "value": list(value_by_geoid.values())})

    # Shape 2: block groups are listed down the first column.
    row_geoids = labels.map(geography_text_to_geoid)
    if row_geoids.notna().sum() > 0:
        value_col = None

        # First try official/API-style column IDs.
        for candidate in col_candidates:
            if candidate in df.columns:
                value_col = candidate
                break

        # Then try columns that contain the candidate ID.
        if value_col is None:
            for col in df.columns[1:]:
                upper_col = str(col).upper()
                if any(candidate.upper() in upper_col for candidate in col_candidates):
                    value_col = col
                    break

        # Then try table-display estimate columns.
        if value_col is None:
            estimate_cols = estimate_column_candidates(df)

            if len(estimate_cols) == 1:
                value_col = estimate_cols[0]
            elif "B19013" in path.name.upper() and estimate_cols:
                # B19013 is a single-variable median-income table.
                value_col = estimate_cols[0]
            elif row_matcher is not None:
                for col in estimate_cols:
                    if row_matcher(clean_label(col)):
                        value_col = col
                        break

        if value_col is None:
            print(f"NOTICE: Could not identify value column in {path.name}.")
            print("NOTICE: Columns seen:", list(df.columns[:12]))
            raise ValueError(f"No usable estimate/value column found in {path}")

        out = pd.DataFrame({
            "geoid": row_geoids,
            "value": to_number(df[value_col]),
        })
        out = out[out["geoid"].notna()].copy()
        return out

    raise ValueError(f"Could not detect Census table-display geography shape in {path}")


def geo_values(path: Path, col_candidates: list[str], row_matcher=None) -> pd.DataFrame:
    try:
        df = read_census_geo_csv(path)
        col = find_col(df, col_candidates)
        return pd.DataFrame({"geoid": df["geoid"], "value": to_number(df[col])})
    except Exception as exc:
        print(f"NOTICE: {path.name} is not GEO_ID-style ({exc}). Reading it as Census table-display export.")
        return table_display_values(path, col_candidates, row_matcher)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def polygon_centroid(points: list[tuple[float, float]]) -> tuple[float, float]:
    if not points:
        return 0.0, 0.0
    area = 0.0
    cx = 0.0
    cy = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    area *= 0.5
    if abs(area) < 1e-12:
        return float(np.mean([p[1] for p in points])), float(np.mean([p[0] for p in points]))
    return cy / (6 * area), cx / (6 * area)


def load_block_group_centroids(tiger_zip: Path) -> pd.DataFrame:
    if shapefile is None:
        raise ImportError("Missing optional package 'pyshp'. Install it with: python -m pip install pyshp")
    reader = shapefile.Reader(str(tiger_zip))
    field_names = [field[0] for field in reader.fields[1:]]
    rows = []
    for shape_rec in reader.iterShapeRecords():
        attrs = dict(zip(field_names, shape_rec.record))
        geoid = str(attrs.get("GEOID", ""))
        if not geoid:
            geoid = "".join(str(attrs.get(key, "")) for key in ["STATEFP", "COUNTYFP", "TRACTCE", "BLKGRPCE"])
        pts = shape_rec.shape.points
        parts = list(shape_rec.shape.parts) + [len(pts)]
        best_part: list[tuple[float, float]] = []
        for start, end in zip(parts[:-1], parts[1:]):
            candidate = pts[start:end]
            if len(candidate) > len(best_part):
                best_part = candidate
        lat, lon = polygon_centroid(best_part)
        rows.append({"geoid": geoid, "bg_lat": lat, "bg_lon": lon})
    return pd.DataFrame(rows)


def site_bg_membership(sites: pd.DataFrame, bg: pd.DataFrame) -> pd.DataFrame:
    rows = []
    radius_m = MILES_RADIUS * METERS_PER_MILE
    for _, site in sites.iterrows():
        site_lat = float(site["lat"])
        site_lon = float(site["lon"])
        for _, block_group in bg.iterrows():
            dist_m = haversine_m(site_lat, site_lon, float(block_group["bg_lat"]), float(block_group["bg_lon"]))
            if dist_m <= radius_m:
                rows.append({
                    "site_id": site["site_id"],
                    "site_name": site["site_name"],
                    "geoid": block_group["geoid"],
                    "bg_centroid_distance_m": round(dist_m, 1),
                })
    return pd.DataFrame(rows)


def label_key(label: str) -> str:
    """Normalize Census table-display row labels for safer matching."""
    text = clean_label(label).lower()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r":+$", "", text).strip()
    text = text.replace("-occupied", " occupied")
    text = re.sub(r"\\s+", " ", text)
    return text


def b11001_household_match(label: str) -> bool:
    key = label_key(label)
    return key in {"households", "total households", "total"}


def b25044_total_households_match(label: str) -> bool:
    key = label_key(label)
    return key in {"occupied housing units", "total"}


def b25044_no_vehicle_match(label: str) -> bool:
    key = label_key(label)
    return key == "no vehicle available" or key.endswith(" no vehicle available")


def b25003_occupied_match(label: str) -> bool:
    key = label_key(label)
    return key in {"occupied housing units", "total"}


def b25003_renter_match(label: str) -> bool:
    key = label_key(label)
    return key in {"renter occupied", "renter occupied housing units"}


def b19013_income_match(label: str) -> bool:
    # In Census table-display exports, B19013 median income values are usually
    # on the "Households" row because the whole table is already median income.
    key = label_key(label)
    return key in {"households", "total households", "total"}


def b25024_total_units_match(label: str) -> bool:
    key = label_key(label)
    return key in {"total housing units", "total"}


def b25024_multifamily_match(label: str) -> bool:
    key = label_key(label)
    return key in {
        "3 or 4 units",
        "5 to 9 units",
        "10 to 19 units",
        "20 to 49 units",
        "50 or more units",
    }


def build_households(membership: pd.DataFrame, b11001_path: Path, b25044_path: Path) -> pd.DataFrame:
    try:
        values = geo_values(b11001_path, ["B11001_001E"], b11001_household_match)
        source_table = "ACS B11001"
    except Exception as exc:
        print(f"NOTICE: Could not use B11001 directly: {exc}")
        print("NOTICE: Falling back to ACS B25044 total occupied households for nearby_households_1mi.")
        values = geo_values(b25044_path, ["B25044_001E"], b25044_total_households_match)
        source_table = "ACS B25044 occupied households fallback"
    values = values.rename(columns={"value": "households"})
    merged = membership.merge(values, on="geoid", how="left")
    summary = merged.groupby(["site_id", "site_name"], as_index=False).agg(
        nearby_households_1mi=("households", "sum"),
        block_groups_used=("geoid", "nunique"),
    )
    summary["nearby_households_1mi"] = summary["nearby_households_1mi"].round().astype(int)
    summary["method"] = f"1-mile centroid-in-buffer estimate from {source_table} + TIGER block groups"
    summary["source_status"] = "official_derived"
    return summary


def build_jobs(membership: pd.DataFrame, lodes_path: Path) -> pd.DataFrame:
    compression = "gzip" if lodes_path.suffix == ".gz" else None
    lodes = pd.read_csv(lodes_path, dtype={"w_geocode": str}, usecols=["w_geocode", "C000"], compression=compression)
    lodes["geoid"] = lodes["w_geocode"].astype(str).str[:12]
    lodes["jobs"] = pd.to_numeric(lodes["C000"], errors="coerce").fillna(0)
    bg_jobs = lodes.groupby("geoid", as_index=False).agg(jobs=("jobs", "sum"))
    merged = membership.merge(bg_jobs, on="geoid", how="left")
    summary = merged.groupby(["site_id", "site_name"], as_index=False).agg(
        nearby_jobs_1mi=("jobs", "sum"),
        block_groups_used=("geoid", "nunique"),
    )
    summary["nearby_jobs_1mi"] = summary["nearby_jobs_1mi"].round().astype(int)
    summary["method"] = "1-mile centroid-in-buffer estimate from LODES WAC + TIGER block groups"
    summary["source_status"] = "official_derived"
    return summary


def load_geojson_from_zip(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            geojson_names = [name for name in zf.namelist() if name.lower().endswith(".geojson") or name.lower().endswith(".json")]
            if not geojson_names:
                raise ValueError(f"No GeoJSON file found in {path}")
            with zf.open(geojson_names[0]) as fp:
                return json.loads(fp.read().decode("utf-8"))
    return json.loads(path.read_text(encoding="utf-8"))


def iter_line_segments(coords: Any):
    if not coords:
        return
    if isinstance(coords[0][0], (int, float)):
        for a, b in zip(coords[:-1], coords[1:]):
            yield (float(a[1]), float(a[0])), (float(b[1]), float(b[0]))
    else:
        for line in coords:
            for a, b in zip(line[:-1], line[1:]):
                yield (float(a[1]), float(a[0])), (float(b[1]), float(b[0]))


def equirect_xy(lat: float, lon: float, ref_lat: float, ref_lon: float) -> tuple[float, float]:
    r = 6_371_000
    x = math.radians(lon - ref_lon) * math.cos(math.radians(ref_lat)) * r
    y = math.radians(lat - ref_lat) * r
    return x, y


def point_segment_distance_m(point: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    lat, lon = point
    ax, ay = equirect_xy(a[0], a[1], lat, lon)
    bx, by = equirect_xy(b[0], b[1], lat, lon)
    dx = bx - ax
    dy = by - ay
    denom = dx * dx + dy * dy
    if denom == 0:
        return math.hypot(ax, ay)
    t = max(0.0, min(1.0, (-(ax * dx + ay * dy)) / denom))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(proj_x, proj_y)


def get_prop(props: dict[str, Any], names: list[str]) -> Any:
    lower = {str(k).lower(): v for k, v in props.items()}
    for name in names:
        if name.lower() in lower:
            return lower[name.lower()]
    return ""


def parse_int_like(value: Any) -> int:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except ValueError:
        return 0


def build_traffic(sites: pd.DataFrame, vdot_path: Path) -> pd.DataFrame:
    data = load_geojson_from_zip(vdot_path)
    features = data.get("features", [])
    rows = []
    for _, site in sites.iterrows():
        site_point = (float(site["lat"]), float(site["lon"]))
        best_props: dict[str, Any] | None = None
        best_distance = float("inf")
        for feature in features:
            geom = feature.get("geometry") or {}
            props = feature.get("properties") or {}
            if geom.get("type") not in {"LineString", "MultiLineString"}:
                continue
            for a, b in iter_line_segments(geom.get("coordinates")):
                distance = point_segment_distance_m(site_point, a, b)
                if distance < best_distance:
                    best_distance = distance
                    best_props = props
        rows.append({
            "site_id": site["site_id"],
            "site_name": site["site_name"],
            "aadt_nearest": parse_int_like(get_prop(best_props or {}, ["ADT", "AADT", "AADT_NBR", "TRAFFIC", "ANNUAL_AVG_DAILY_TRAFFIC"])),
            "nearest_segment_distance_m": round(best_distance, 1) if best_props is not None else "",
            "route_name": get_prop(best_props or {}, ["ROUTE_NAME", "ROUTE_COMM", "RTE_NM", "STREET_NAME"]),
            "segment_label": f"{get_prop(best_props or {}, ['START_LABE', 'START_LABEL', 'FROM_DESC'])} to {get_prop(best_props or {}, ['END_LABEL', 'END_LABE', 'TO_DESC'])}".strip(),
            "method": "Nearest VDOT Bidirectional Traffic Volume segment from GeoJSON" if best_props is not None else "No VDOT segment found",
            "source_status": "official_derived" if best_props is not None else "missing",
        })
    return pd.DataFrame(rows)


def build_equity_inputs(membership: pd.DataFrame, b19013_path: Path, b25044_path: Path, b25003_path: Path, b25024_path: Path) -> pd.DataFrame:
    income = geo_values(b19013_path, ["B19013_001E"], b19013_income_match).rename(columns={"value": "median_household_income"})
    total_households = geo_values(b25044_path, ["B25044_001E"], b25044_total_households_match).rename(columns={"value": "total_households"})
    no_vehicle = geo_values(b25044_path, ["B25044_003E", "B25044_010E"], b25044_no_vehicle_match).rename(columns={"value": "no_vehicle_households"})
    occupied = geo_values(b25003_path, ["B25003_001E"], b25003_occupied_match).rename(columns={"value": "occupied_housing_units"})
    renter = geo_values(b25003_path, ["B25003_003E"], b25003_renter_match).rename(columns={"value": "renter_occupied_households"})
    total_units = geo_values(b25024_path, ["B25024_001E"], b25024_total_units_match).rename(columns={"value": "total_housing_units"})
    multifamily = geo_values(
        b25024_path,
        ["B25024_004E", "B25024_005E", "B25024_006E", "B25024_007E", "B25024_008E"],
        b25024_multifamily_match,
    ).rename(columns={"value": "multifamily_units"})
    bg = income.merge(total_households, on="geoid", how="outer")
    bg = bg.merge(no_vehicle, on="geoid", how="outer")
    bg = bg.merge(occupied, on="geoid", how="outer")
    bg = bg.merge(renter, on="geoid", how="outer")
    bg = bg.merge(total_units, on="geoid", how="outer")
    bg = bg.merge(multifamily, on="geoid", how="outer")
    merged = membership.merge(bg, on="geoid", how="left").fillna(0)
    rows = []
    for (site_id, site_name), group in merged.groupby(["site_id", "site_name"]):
        weights = group["occupied_housing_units"].replace(0, np.nan)
        if weights.notna().sum() == 0:
            median_income = float(group["median_household_income"].mean()) if len(group) else 0.0
        else:
            median_income = float(np.average(group["median_household_income"], weights=weights.fillna(0)))
        rows.append({
            "site_id": site_id,
            "site_name": site_name,
            "median_household_income": round(median_income),
            "total_households": round(float(group["total_households"].sum())),
            "no_vehicle_households": round(float(group["no_vehicle_households"].sum())),
            "occupied_housing_units": round(float(group["occupied_housing_units"].sum())),
            "renter_occupied_households": round(float(group["renter_occupied_households"].sum())),
            "total_housing_units": round(float(group["total_housing_units"].sum())),
            "multifamily_units": round(float(group["multifamily_units"].sum())),
            "block_groups_intersected": int(group["geoid"].nunique()),
            "method": "1-mile centroid-in-buffer block-group estimate; median income approximated by occupied-unit-weighted block-group medians",
            "source_tables": "ACS 2024 5-year B19013, B25044, B25003, B25024; TIGER Line 2024 Virginia block groups",
            "source_status": "official_derived",
        })
    return pd.DataFrame(rows)


def minmax(series: pd.Series, inverse: bool = False) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0)
    lo = float(values.min())
    hi = float(values.max())
    if abs(hi - lo) < 1e-12:
        result = pd.Series([0.0] * len(values), index=values.index)
    else:
        result = (values - lo) / (hi - lo)
    return (1 - result if inverse else result).clip(0, 1)


def build_equity_index(new_inputs: pd.DataFrame) -> pd.DataFrame:
    existing_path = OUT_DIR / "acs_equity_inputs_1mi.csv"
    combined = pd.concat([pd.read_csv(existing_path), new_inputs], ignore_index=True, sort=False) if existing_path.exists() else new_inputs.copy()
    combined["no_vehicle_household_share"] = combined["no_vehicle_households"] / combined["occupied_housing_units"].replace(0, np.nan)
    combined["renter_household_share"] = combined["renter_occupied_households"] / combined["occupied_housing_units"].replace(0, np.nan)
    combined["multifamily_unit_share"] = combined["multifamily_units"] / combined["total_housing_units"].replace(0, np.nan)
    combined["lower_income_component"] = minmax(combined["median_household_income"], inverse=True)
    combined["no_vehicle_component"] = minmax(combined["no_vehicle_household_share"])
    combined["renter_component"] = minmax(combined["renter_household_share"])
    combined["multifamily_component"] = minmax(combined["multifamily_unit_share"])
    combined["equity_gap_index"] = (
        combined["lower_income_component"] * EQUITY_WEIGHTS["lower_income_component"]
        + combined["no_vehicle_component"] * EQUITY_WEIGHTS["no_vehicle_component"]
        + combined["renter_component"] * EQUITY_WEIGHTS["renter_component"]
        + combined["multifamily_component"] * EQUITY_WEIGHTS["multifamily_component"]
    ).round(3)
    return combined[combined["site_id"].isin(TARGET_SITE_IDS)].copy()


def build_amenities(sites: pd.DataFrame) -> pd.DataFrame:
    summary_path = OUT_DIR / "amenities_0_5mi_v4_osm_reviewed.csv"
    if not summary_path.exists():
        return pd.DataFrame({
            "site_id": sites["site_id"], "site_name": sites["site_name"],
            "amenities_count_0_5mi": [""] * len(sites),
            "source_status": ["missing"] * len(sites),
            "method": ["Run src/build_osm_amenities.py for V2 sites and review output"] * len(sites),
        })
    source = pd.read_csv(summary_path)
    subset = source[source["site_id"].isin(TARGET_SITE_IDS)].copy()
    if subset.empty:
        return pd.DataFrame({
            "site_id": sites["site_id"], "site_name": sites["site_name"],
            "amenities_count_0_5mi": [""] * len(sites),
            "source_status": ["needs_v2_osm_run"] * len(sites),
            "method": ["Existing OSM reviewed extract does not include these V2 sites yet"] * len(sites),
        })
    out = subset[["site_id", "site_name", "reviewed_amenities_count_0_5mi", "source_quality", "notes"]].copy()
    out = out.rename(columns={"reviewed_amenities_count_0_5mi": "amenities_count_0_5mi"})
    out["source_status"] = "open_gis_support"
    out["method"] = "Reviewed OSM/Overpass six-category POI extract"
    return out


def write_outputs(outputs: dict[str, pd.DataFrame]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in outputs.items():
        path = OUT_DIR / name
        df.to_csv(path, index=False)
        print(f"Saved: {path}")


def main() -> None:
    print("V2 PUBLIC-DATA UPGRADE CALCULATOR")
    print("----------------------------------")
    if not SITES_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {SITES_PATH}")
    tiger_path = find_first(TIGER_PATTERN)
    b11001_path = find_first(ACS_HOUSEHOLDS_PATTERN)
    lodes_path = find_first(LODES_PATTERN)
    vdot_path = find_first(VDOT_PATTERN)
    b19013_path = find_first("B19013")
    b25044_path = find_first("B25044")
    b25003_path = find_first("B25003")
    b25024_path = find_first("B25024")
    required = {
        "TIGER block groups": tiger_path,
        "ACS B11001 households": b11001_path,
        "LODES WAC jobs": lodes_path,
        "VDOT GeoJSON traffic": vdot_path,
        "ACS B19013 income": b19013_path,
        "ACS B25044 vehicles/households": b25044_path,
        "ACS B25003 tenure": b25003_path,
        "ACS B25024 units": b25024_path,
    }
    missing = [name for name, path in required.items() if path is None]
    if missing:
        print("Missing required inputs:")
        for item in missing:
            print(f"- {item}")
        sys.exit(1)
    sites_all = pd.read_csv(SITES_PATH)
    sites = sites_all[sites_all["site_id"].isin(TARGET_SITE_IDS)].copy()
    if sites.empty:
        raise ValueError(f"No target sites found in {SITES_PATH}: {TARGET_SITE_IDS}")
    print("Target sites:")
    for _, site in sites.iterrows():
        print(f"- {site['site_id']} — {site['site_name']}")
    print()
    print("Loading TIGER block-group centroids...")
    bg = load_block_group_centroids(tiger_path)  # type: ignore[arg-type]
    print(f"Block groups loaded: {len(bg):,}")
    print("Finding block groups within 1 mile of target sites...")
    membership = site_bg_membership(sites, bg)
    if membership.empty:
        raise RuntimeError("No block groups were found within 1 mile of the target sites.")
    households = build_households(membership, b11001_path, b25044_path)  # type: ignore[arg-type]
    jobs = build_jobs(membership, lodes_path)  # type: ignore[arg-type]
    traffic = build_traffic(sites, vdot_path)  # type: ignore[arg-type]
    equity_inputs = build_equity_inputs(membership, b19013_path, b25044_path, b25003_path, b25024_path)  # type: ignore[arg-type]
    equity_index = build_equity_index(equity_inputs)
    amenities = build_amenities(sites)
    combined = sites[["site_id", "site_name", "nearby_households_1mi", "nearby_jobs_1mi", "aadt_nearest", "amenities_count_0_5mi", "equity_gap_index", "ev_registrations_local", "ev_share_local"]].copy()
    combined = combined.rename(columns={
        "nearby_households_1mi": "current_nearby_households_1mi",
        "nearby_jobs_1mi": "current_nearby_jobs_1mi",
        "aadt_nearest": "current_aadt_nearest",
        "amenities_count_0_5mi": "current_amenities_count_0_5mi",
        "equity_gap_index": "current_equity_gap_index",
        "ev_registrations_local": "current_ev_registrations_local",
        "ev_share_local": "current_ev_share_local",
    })
    combined = combined.merge(households[["site_id", "nearby_households_1mi", "method"]].rename(columns={"method": "households_method"}), on="site_id", how="left")
    combined = combined.merge(jobs[["site_id", "nearby_jobs_1mi"]], on="site_id", how="left")
    combined = combined.merge(traffic[["site_id", "aadt_nearest", "route_name", "nearest_segment_distance_m"]], on="site_id", how="left")
    combined = combined.merge(amenities[["site_id", "amenities_count_0_5mi", "source_status"]].rename(columns={"source_status": "amenities_source_status"}), on="site_id", how="left")
    combined = combined.merge(equity_index[["site_id", "equity_gap_index"]], on="site_id", how="left")
    combined["ev_adoption_status"] = "not_upgraded_no_current_official_locality_source_found"
    combined["method_note"] = "Review before applying. Household/jobs/equity use centroid-in-buffer approximation, not final engineering/site validation."
    outputs = {
        "v2_bg_membership_1mi.csv": membership,
        "v2_acs_households_1mi.csv": households,
        "v2_lodes_jobs_1mi.csv": jobs,
        "v2_vdot_nearest_traffic_segments.csv": traffic,
        "v2_acs_equity_inputs_1mi.csv": equity_inputs,
        "v2_acs_equity_index_1mi.csv": equity_index,
        "v2_amenities_0_5mi_status.csv": amenities,
        "v2_public_data_upgrade_recommendations.csv": combined,
    }
    write_outputs(outputs)
    print()
    print("Recommended upgraded values to review:")
    display_cols = ["site_id", "site_name", "nearby_households_1mi", "nearby_jobs_1mi", "aadt_nearest", "amenities_count_0_5mi", "equity_gap_index", "ev_adoption_status"]
    print(combined[display_cols].to_string(index=False))
    print()
    print("Done. Review data/source_extracts/v2_public_data_upgrade_recommendations.csv before applying values to real_sites_v2.csv.")


if __name__ == "__main__":
    main()
