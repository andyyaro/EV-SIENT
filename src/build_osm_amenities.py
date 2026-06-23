"""Build a GIS/POI amenity extract from OpenStreetMap/Overpass.

This script downloads nearby points of interest within 0.5 miles of each candidate
site and summarizes them into amenity categories. It is intentionally separate
from the main model so the results can be reviewed before replacing the current
manual amenities_count_0_5mi values.

Default outputs:
- data/outputs/amenities_osm_summary_0_5mi.csv
- data/outputs/amenities_osm_pois_0_5mi.csv
"""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

DEFAULT_INPUT = "data/inputs/real_sites_v1.csv"
DEFAULT_SUMMARY_OUTPUT = "data/outputs/amenities_osm_summary_0_5mi.csv"
DEFAULT_POI_OUTPUT = "data/outputs/amenities_osm_pois_0_5mi.csv"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
RADIUS_METERS = 805  # approximately 0.5 miles
REQUEST_PAUSE_SECONDS = 2

CATEGORY_RULES = {
    "food": {
        "amenity": {"restaurant", "cafe", "fast_food", "pub", "bar"},
    },
    "retail": {
        "shop": {
            "supermarket", "convenience", "grocery", "department_store", "mall",
            "clothes", "hardware", "pharmacy", "books", "bakery", "general", "yes",
        },
    },
    "entertainment_culture": {
        "amenity": {"cinema", "theatre", "arts_centre"},
        "tourism": {"museum", "attraction", "gallery"},
    },
    "recreation": {
        "leisure": {"park", "recreation_ground", "sports_centre", "fitness_centre", "playground", "water_park", "pitch"},
    },
    "transit": {
        "highway": {"bus_stop"},
        "public_transport": {"station", "platform", "stop_position"},
        "railway": {"station", "halt", "tram_stop"},
    },
    "civic_public": {
        "amenity": {"library", "townhall", "courthouse", "police", "fire_station", "post_office", "community_centre"},
        "office": {"government"},
    },
}

QUERY_TAGS = [
    ("amenity", "restaurant|cafe|fast_food|pub|bar|cinema|theatre|arts_centre|library|townhall|courthouse|police|fire_station|post_office|community_centre"),
    ("tourism", "museum|attraction|gallery"),
    ("leisure", "park|recreation_ground|sports_centre|fitness_centre|playground|water_park|pitch"),
    ("highway", "bus_stop"),
    ("public_transport", "station|platform|stop_position"),
    ("railway", "station|halt|tram_stop"),
    ("office", "government"),
    ("shop", "supermarket|convenience|grocery|department_store|mall|clothes|hardware|pharmacy|books|bakery|general|yes"),
]


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in meters."""
    radius = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_overpass_query(lat: float, lon: float, radius_m: int = RADIUS_METERS) -> str:
    """Create an Overpass QL query for the POI tags used by this script."""
    selectors = []
    for key, value_regex in QUERY_TAGS:
        selectors.append(f'node(around:{radius_m},{lat},{lon})["{key}"~"^({value_regex})$"];')
        selectors.append(f'way(around:{radius_m},{lat},{lon})["{key}"~"^({value_regex})$"];')
        selectors.append(f'relation(around:{radius_m},{lat},{lon})["{key}"~"^({value_regex})$"];')

    return "\n".join([
        "[out:json][timeout:60];",
        "(",
        *selectors,
        ");",
        "out center tags;",
    ])


def fetch_overpass(query: str) -> dict:
    """POST a query to the public Overpass API."""
    payload = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(
        OVERPASS_URL,
        data=payload,
        headers={"User-Agent": "future-city-fellowship-ev-amenity-prototype/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def element_lat_lon(element: dict) -> tuple[float | None, float | None]:
    """Return element coordinate, using center for ways/relations."""
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]
    if "center" in element:
        return element["center"].get("lat"), element["center"].get("lon")
    return None, None


def classify_tags(tags: dict) -> list[str]:
    """Return all amenity categories matched by an OSM tag dictionary."""
    categories = []
    for category, key_values in CATEGORY_RULES.items():
        for key, allowed_values in key_values.items():
            if tags.get(key) in allowed_values:
                categories.append(category)
                break
    return categories


def build_site_pois(site: pd.Series) -> list[dict]:
    """Download and classify POIs for one site."""
    site_lat = float(site["lat"])
    site_lon = float(site["lon"])
    query = build_overpass_query(site_lat, site_lon)
    data = fetch_overpass(query)

    rows = []
    seen = set()
    for element in data.get("elements", []):
        lat, lon = element_lat_lon(element)
        if lat is None or lon is None:
            continue

        distance_m = haversine_m(site_lat, site_lon, lat, lon)
        if distance_m > RADIUS_METERS:
            continue

        tags = element.get("tags", {})
        categories = classify_tags(tags)
        if not categories:
            continue

        osm_type = element.get("type", "")
        osm_id = element.get("id", "")
        unique_key = (osm_type, osm_id)
        if unique_key in seen:
            continue
        seen.add(unique_key)

        rows.append({
            "site_id": site["site_id"],
            "site_name": site["site_name"],
            "osm_type": osm_type,
            "osm_id": osm_id,
            "poi_name": tags.get("name", ""),
            "lat": lat,
            "lon": lon,
            "distance_m": round(distance_m, 1),
            "categories": ";".join(categories),
            "amenity": tags.get("amenity", ""),
            "shop": tags.get("shop", ""),
            "tourism": tags.get("tourism", ""),
            "leisure": tags.get("leisure", ""),
            "public_transport": tags.get("public_transport", ""),
            "railway": tags.get("railway", ""),
            "highway": tags.get("highway", ""),
            "office": tags.get("office", ""),
        })
    return rows


def summarize_pois(sites: pd.DataFrame, pois: pd.DataFrame) -> pd.DataFrame:
    """Create one summary row per site."""
    summary_rows = []
    for _, site in sites.iterrows():
        site_pois = pois[pois["site_id"] == site["site_id"]] if not pois.empty else pd.DataFrame()
        categories_found = set()
        for category_text in site_pois.get("categories", pd.Series(dtype=str)).fillna(""):
            for category in category_text.split(";"):
                if category:
                    categories_found.add(category)

        row = {
            "site_id": site["site_id"],
            "site_name": site["site_name"],
            "current_model_amenities_count_0_5mi": site.get("amenities_count_0_5mi", ""),
            "osm_poi_total_0_5mi": int(len(site_pois)),
            "osm_category_count_0_5mi": int(len(categories_found)),
            "osm_categories_found": ";".join(sorted(categories_found)),
            "source_quality": "OpenStreetMap/Overpass POI extract; not official local government data",
            "applied_to_model": "no",
            "notes": "Review before replacing amenities_count_0_5mi. OSM completeness varies by area and category.",
        }

        for category in sorted(CATEGORY_RULES):
            row[f"has_{category}"] = 1 if category in categories_found else 0
            if site_pois.empty:
                row[f"{category}_poi_count"] = 0
            else:
                row[f"{category}_poi_count"] = int(site_pois["categories"].fillna("").str.contains(category, regex=False).sum())

        summary_rows.append(row)
    return pd.DataFrame(summary_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and summarize OSM POIs within 0.5 miles of candidate sites.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Candidate-site input CSV.")
    parser.add_argument("--summary-output", default=DEFAULT_SUMMARY_OUTPUT, help="Summary CSV output path.")
    parser.add_argument("--poi-output", default=DEFAULT_POI_OUTPUT, help="Detailed POI CSV output path.")
    parser.add_argument("--pause", type=float, default=REQUEST_PAUSE_SECONDS, help="Pause in seconds between Overpass requests.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    sites = pd.read_csv(input_path)
    all_poi_rows = []

    print("OSM / OVERPASS AMENITY EXTRACT")
    print("------------------------------")
    print(f"Input file: {input_path}")
    print(f"Radius: {RADIUS_METERS} meters (~0.5 miles)")
    print()

    for index, site in sites.iterrows():
        print(f"Downloading POIs for {site['site_id']} — {site['site_name']}...")
        try:
            all_poi_rows.extend(build_site_pois(site))
        except Exception as exc:  # keep one failed site from stopping the whole run
            print(f"  WARNING: failed to fetch {site['site_id']}: {exc}")
        if index < len(sites) - 1:
            time.sleep(max(args.pause, 0))

    pois = pd.DataFrame(all_poi_rows)
    summary = summarize_pois(sites, pois)

    summary_output = Path(args.summary_output)
    poi_output = Path(args.poi_output)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    poi_output.parent.mkdir(parents=True, exist_ok=True)

    summary.to_csv(summary_output, index=False)
    pois.to_csv(poi_output, index=False)

    print()
    print("Summary:")
    print(summary[["site_id", "site_name", "current_model_amenities_count_0_5mi", "osm_poi_total_0_5mi", "osm_category_count_0_5mi", "osm_categories_found"]].to_string(index=False))
    print()
    print(f"Saved summary: {summary_output}")
    print(f"Saved detailed POIs: {poi_output}")
    print("Done. Review these outputs before changing data/inputs/real_sites_v1.csv.")


if __name__ == "__main__":
    main()
