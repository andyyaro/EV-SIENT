"""Build nearby EV charging supply counts from an AFDC/NREL export.

This script counts public active electric charging supply around candidate sites.

Default method used by the Future City Fellowship prototype:
- Level 2 ports within 1 mile
- DC fast ports within 3 miles

The script is intentionally lightweight and beginner-friendly. It uses pandas plus
simple distance math so it works in PyCharm without GIS dependencies.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable

import pandas as pd


DEFAULT_AFDC_PATH = Path("data/raw_exports/alt_fuel_stations (Jun 23 2026).csv")
DEFAULT_SITE_INPUT = Path("data/inputs/real_sites_v2.csv")
DEFAULT_COUNTS_OUTPUT = Path("data/source_extracts/afdc_ev_supply_counts_v2_batch002.csv")
DEFAULT_MATCHES_OUTPUT = Path("data/source_extracts/afdc_ev_supply_matches_v2_batch002.csv")

TARGET_SITE_IDS = ["PWC005", "PWC006", "PWC007", "PWC008"]


def normalize_column_name(name: str) -> str:
    """Return a loose column key for matching AFDC columns with small variations."""

    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )


def find_column(columns: Iterable[str], candidates: Iterable[str], required: bool = True) -> str | None:
    """Find the first matching column from a list of possible names."""

    normalized = {normalize_column_name(column): column for column in columns}
    for candidate in candidates:
        key = normalize_column_name(candidate)
        if key in normalized:
            return normalized[key]

    if required:
        raise ValueError(
            "Could not find required column. Tried: "
            + ", ".join(candidates)
            + "\nAvailable columns: "
            + ", ".join(map(str, columns))
        )
    return None


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate approximate distance between two lat/lon points in miles."""

    earth_radius_miles = 3958.7613
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_miles * c


def numeric_series(series: pd.Series) -> pd.Series:
    """Convert a possibly text-based numeric column into non-null numeric values."""

    return pd.to_numeric(series, errors="coerce").fillna(0)


def load_sites(site_path: Path, site_ids: list[str]) -> pd.DataFrame:
    sites = pd.read_csv(site_path)
    required_columns = {"site_id", "site_name", "lat", "lon"}
    missing = required_columns - set(sites.columns)
    if missing:
        raise ValueError(f"Site file is missing required columns: {sorted(missing)}")

    sites = sites[sites["site_id"].isin(site_ids)].copy()
    if sites.empty:
        raise ValueError(f"No requested site IDs were found in {site_path}: {site_ids}")

    sites["lat"] = pd.to_numeric(sites["lat"], errors="raise")
    sites["lon"] = pd.to_numeric(sites["lon"], errors="raise")
    return sites


def load_afdc(afdc_path: Path) -> tuple[pd.DataFrame, dict[str, str | None]]:
    if not afdc_path.exists():
        raise FileNotFoundError(
            f"AFDC file not found: {afdc_path}\n"
            "Download/export the AFDC Alternative Fuel Stations CSV into data/raw_exports/ "
            "or pass --afdc with the correct path."
        )

    afdc = pd.read_csv(afdc_path, low_memory=False)

    columns = {
        "station_name": find_column(afdc.columns, ["Station Name", "station_name"], required=False),
        "street_address": find_column(afdc.columns, ["Street Address", "street_address"], required=False),
        "city": find_column(afdc.columns, ["City"], required=False),
        "state": find_column(afdc.columns, ["State"], required=False),
        "zip": find_column(afdc.columns, ["ZIP", "Zip", "zip"], required=False),
        "fuel_type": find_column(afdc.columns, ["Fuel Type Code", "fuel_type_code", "Fuel Type"], required=False),
        "access": find_column(afdc.columns, ["Access Code", "access_code", "Groups With Access Code"], required=False),
        "status": find_column(afdc.columns, ["Status Code", "status_code", "Status"], required=False),
        "lat": find_column(afdc.columns, ["Latitude", "lat"], required=True),
        "lon": find_column(afdc.columns, ["Longitude", "lon", "lng"], required=True),
        "l2_ports": find_column(
            afdc.columns,
            ["EV Level2 EVSE Num", "EV Level2 EVSE Number", "ev_level2_evse_num"],
            required=False,
        ),
        "dcfc_ports": find_column(
            afdc.columns,
            ["EV DC Fast Count", "EV DC Fast Num", "ev_dc_fast_count"],
            required=False,
        ),
    }

    afdc[columns["lat"]] = pd.to_numeric(afdc[columns["lat"]], errors="coerce")
    afdc[columns["lon"]] = pd.to_numeric(afdc[columns["lon"]], errors="coerce")
    afdc = afdc.dropna(subset=[columns["lat"], columns["lon"]]).copy()

    if columns["l2_ports"] is not None:
        afdc["_l2_ports"] = numeric_series(afdc[columns["l2_ports"]])
    else:
        afdc["_l2_ports"] = 0

    if columns["dcfc_ports"] is not None:
        afdc["_dcfc_ports"] = numeric_series(afdc[columns["dcfc_ports"]])
    else:
        afdc["_dcfc_ports"] = 0

    if columns["fuel_type"] is not None:
        fuel = afdc[columns["fuel_type"]].astype(str).str.upper().str.strip()
        afdc = afdc[fuel.eq("ELEC") | fuel.str.contains("ELECTRIC", na=False)].copy()

    if columns["access"] is not None:
        access = afdc[columns["access"]].astype(str).str.lower()
        afdc = afdc[access.str.contains("public", na=False)].copy()

    if columns["status"] is not None:
        status = afdc[columns["status"]].astype(str).str.upper().str.strip()
        active_status = status.isin(["E", "OPEN", "ACTIVE", "EXISTING"]) | status.str.contains(
            "EXISTING|ACTIVE|OPEN", na=False
        )
        afdc = afdc[active_status].copy()

    return afdc, columns


def build_counts(
    sites: pd.DataFrame,
    afdc: pd.DataFrame,
    columns: dict[str, str | None],
    l2_radius_miles: float,
    dcfc_radius_miles: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    count_rows = []
    match_rows = []

    for _, site in sites.iterrows():
        site_id = site["site_id"]
        site_name = site["site_name"]
        site_lat = float(site["lat"])
        site_lon = float(site["lon"])

        nearby_l2_ports = 0
        nearby_dcfc_ports = 0

        for _, station in afdc.iterrows():
            station_lat = float(station[columns["lat"]])
            station_lon = float(station[columns["lon"]])
            distance = haversine_miles(site_lat, site_lon, station_lat, station_lon)
            l2_ports = int(station["_l2_ports"])
            dcfc_ports = int(station["_dcfc_ports"])

            within_l2 = distance <= l2_radius_miles and l2_ports > 0
            within_dcfc = distance <= dcfc_radius_miles and dcfc_ports > 0

            if within_l2:
                nearby_l2_ports += l2_ports
            if within_dcfc:
                nearby_dcfc_ports += dcfc_ports

            if within_l2 or within_dcfc:
                match_rows.append(
                    {
                        "site_id": site_id,
                        "site_name": site_name,
                        "station_name": station.get(columns["station_name"], "") if columns["station_name"] else "",
                        "station_address": station.get(columns["street_address"], "")
                        if columns["street_address"]
                        else "",
                        "station_city": station.get(columns["city"], "") if columns["city"] else "",
                        "station_state": station.get(columns["state"], "") if columns["state"] else "",
                        "station_zip": station.get(columns["zip"], "") if columns["zip"] else "",
                        "station_lat": station_lat,
                        "station_lon": station_lon,
                        "distance_miles": round(distance, 3),
                        "l2_ports": l2_ports,
                        "dcfc_ports": dcfc_ports,
                        "counted_for_l2_1mi": int(within_l2),
                        "counted_for_dcfc_3mi": int(within_dcfc),
                    }
                )

        count_rows.append(
            {
                "site_id": site_id,
                "site_name": site_name,
                "lat": site_lat,
                "lon": site_lon,
                "existing_l2_ports_1mi": nearby_l2_ports,
                "existing_dcfc_ports_3mi": nearby_dcfc_ports,
                "source_dataset": "AFDC Alternative Fuel Stations",
                "source_owner": "NREL / U.S. Department of Energy",
                "source_quality": "Official",
                "filter_summary": (
                    "public; active/existing; electric; "
                    f"Level 2 within {l2_radius_miles:g} mile; "
                    f"DC fast within {dcfc_radius_miles:g} miles"
                ),
                "notes": "nearby public active EV charging supply count",
            }
        )

    return pd.DataFrame(count_rows), pd.DataFrame(match_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AFDC/NREL EV supply counts near candidate sites.")
    parser.add_argument("--sites", default=DEFAULT_SITE_INPUT, type=Path)
    parser.add_argument("--afdc", default=DEFAULT_AFDC_PATH, type=Path)
    parser.add_argument("--site-ids", nargs="+", default=TARGET_SITE_IDS)
    parser.add_argument("--l2-radius", default=1.0, type=float)
    parser.add_argument("--dcfc-radius", default=3.0, type=float)
    parser.add_argument("--counts-output", default=DEFAULT_COUNTS_OUTPUT, type=Path)
    parser.add_argument("--matches-output", default=DEFAULT_MATCHES_OUTPUT, type=Path)
    args = parser.parse_args()

    print("AFDC / NREL EV SUPPLY COUNT BUILDER")
    print("------------------------------------")
    print(f"Site input: {args.sites}")
    print(f"AFDC input: {args.afdc}")
    print(f"Target site IDs: {', '.join(args.site_ids)}")

    sites = load_sites(args.sites, args.site_ids)
    afdc, columns = load_afdc(args.afdc)
    counts, matches = build_counts(sites, afdc, columns, args.l2_radius, args.dcfc_radius)

    args.counts_output.parent.mkdir(parents=True, exist_ok=True)
    args.matches_output.parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(args.counts_output, index=False)
    matches.to_csv(args.matches_output, index=False)

    print("\nRecommended EV supply counts to review:")
    print(counts[["site_id", "site_name", "existing_l2_ports_1mi", "existing_dcfc_ports_3mi"]].to_string(index=False))
    print(f"\nSaved counts: {args.counts_output}")
    print(f"Saved station matches: {args.matches_output}")
    print("Done. Review counts and matches before applying to data/inputs/real_sites_v2.csv.")


if __name__ == "__main__":
    main()
