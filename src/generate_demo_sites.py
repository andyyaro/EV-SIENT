"""Generate synthetic demo candidate sites for stress-testing the model.

The official V1 input file has six real planning candidates. This script creates
a separate synthetic CSV with the same schema so the model can be tested with
larger candidate sets, such as 25, 50, or 100 sites.

Demo data is not real site data and should not be used for recommendations.
It is only for checking scalability, charts, ranking behavior, and workflow
robustness.

Example:

    python src/generate_demo_sites.py --count 50 --seed 42 --output data/demo/demo_sites_50.csv
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import pandas as pd

DEFAULT_TEMPLATE = "data/inputs/real_sites_v1.csv"
DEFAULT_OUTPUT = "data/demo/demo_sites_50.csv"
DEFAULT_COUNT = 50
DEFAULT_SEED = 42

SITE_TYPES = [
    "library",
    "office",
    "garage",
    "park",
    "community_center",
    "transit",
    "school",
    "public_safety",
]

FAIRFAX_CITIES = ["Fairfax", "Fairfax City"]
PWC_CITIES = ["Woodbridge", "Manassas", "Dale City", "Nokesville", "Gainesville", "Dumfries"]
PWC_ZIPS = ["22191", "22192", "20110", "20112", "20155", "22026"]
FAIRFAX_ZIPS = ["22030", "22031", "22032"]


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def choose_weighted(rng: random.Random, values: list, weights: list[float]):
    return rng.choices(values, weights=weights, k=1)[0]


def numeric_range(rng: random.Random, low: float, high: float, decimals: int = 0):
    value = rng.uniform(low, high)
    if decimals == 0:
        return int(round(value))
    return round(value, decimals)


def demo_row(index: int, count: int, rng: random.Random) -> dict[str, object]:
    """Create one synthetic site row with plausible planning-test values."""
    fairfax_cutoff = max(1, int(round(count * 0.40)))
    is_fairfax = index <= fairfax_cutoff

    if is_fairfax:
        prefix = "DEMOFFX"
        lat = numeric_range(rng, 38.820, 38.870, 6)
        lon = numeric_range(rng, -77.330, -77.280, 6)
        city = rng.choice(FAIRFAX_CITIES)
        zipcode = rng.choice(FAIRFAX_ZIPS)
        ev_registrations = 500
        ev_share = 0.023
        households_range = (500, 7500)
        jobs_range = (300, 24000)
    else:
        prefix = "DEMOPWC"
        lat = numeric_range(rng, 38.600, 38.720, 6)
        lon = numeric_range(rng, -77.620, -77.250, 6)
        city = rng.choice(PWC_CITIES)
        zipcode = rng.choice(PWC_ZIPS)
        ev_registrations = 8000
        ev_share = 0.018
        households_range = (300, 8500)
        jobs_range = (200, 26000)

    site_type = rng.choice(SITE_TYPES)
    public_access = choose_weighted(rng, [1, 0], [0.86, 0.14])
    garage_enclosed = 1 if site_type == "garage" and rng.random() < 0.70 else 0

    stronger_electrical = rng.random() < 0.25
    elec_rating = rng.choice([800, 1200, 1600, 2000]) if stronger_electrical else 0
    spare_capacity = numeric_range(rng, 50, 350) if stronger_electrical else 0
    emergency_disconnect = 1 if stronger_electrical else 0

    site_number = f"{index:03d}"
    return {
        "site_id": f"{prefix}{site_number}",
        "site_name": f"Demo Candidate Site {site_number}",
        "site_type": site_type,
        "address": f"{1000 + index} Demo Planning Ave",
        "city": city,
        "state": "VA",
        "zip": zipcode,
        "lat": lat,
        "lon": lon,
        "public_access": public_access,
        "employees_day": numeric_range(rng, 8, 650),
        "visitors_day": numeric_range(rng, 50, 950),
        "fleet_vehicles": numeric_range(rng, 0, 90),
        "parking_spaces": numeric_range(rng, 35, 1800),
        "hours_open": numeric_range(rng, 7, 24, 2),
        "avg_dwell_min": rng.choice([45, 60, 90, 120, 180, 240]),
        "nearby_households_1mi": numeric_range(rng, *households_range),
        "nearby_jobs_1mi": numeric_range(rng, *jobs_range),
        "aadt_nearest": numeric_range(rng, 500, 55000),
        "amenities_count_0_5mi": numeric_range(rng, 0, 9),
        "ev_registrations_local": ev_registrations,
        "ev_share_local": ev_share,
        "existing_l2_ports_1mi": numeric_range(rng, 0, 70),
        "existing_dcfc_ports_3mi": numeric_range(rng, 0, 70),
        "equity_gap_index": numeric_range(rng, 0.05, 0.85, 3),
        "elec_service_voltage": 480,
        "elec_service_rating_amp": elec_rating,
        "spare_capacity_kw": spare_capacity,
        "distance_to_service_ft": numeric_range(rng, 30, 260),
        "trenching_ft": numeric_range(rng, 20, 230),
        "trench_cost_per_ft": 150,
        "service_upgrade_cost_usd": rng.choice([10000, 15000, 20000, 25000, 45000, 60000]),
        "ada_layout_possible": choose_weighted(rng, [1, 0], [0.84, 0.16]),
        "fire_access_ok": choose_weighted(rng, [1, 0], [0.88, 0.12]),
        "garage_enclosed": garage_enclosed,
        "emergency_disconnect_visible": emergency_disconnect,
        "stormwater_risk": choose_weighted(rng, [0, 1], [0.78, 0.22]),
        "battery_storage_flag": 0,
        "battery_storage_kwh": 0,
        "notes": "Synthetic demo row for scalability testing only; not a real candidate site or planning recommendation.",
    }


def build_demo_sites(template_path: Path, count: int, seed: int) -> pd.DataFrame:
    """Build a demo DataFrame that follows the official input schema."""
    if count < 1:
        raise ValueError("count must be at least 1")
    if not template_path.exists():
        raise FileNotFoundError(f"Template input file not found: {template_path}")

    template = pd.read_csv(template_path, nrows=0)
    columns = list(template.columns)
    rng = random.Random(seed)

    rows = [demo_row(index, count, rng) for index in range(1, count + 1)]
    demo = pd.DataFrame(rows)

    missing_columns = [column for column in columns if column not in demo.columns]
    if missing_columns:
        raise ValueError(f"Demo generator did not create required columns: {missing_columns}")

    return demo[columns]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic demo sites for model stress testing.")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, help="Input CSV whose schema should be copied.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output demo CSV path.")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help="Number of demo candidate sites to create.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed for reproducible demo data.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    template_path = Path(args.template)
    output_path = Path(args.output)

    demo = build_demo_sites(template_path, args.count, args.seed)
    ensure_parent_dir(output_path)
    demo.to_csv(output_path, index=False)

    print("GENERATE DEMO SITES")
    print("-------------------")
    print(f"Template: {template_path}")
    print(f"Output: {output_path}")
    print(f"Rows: {len(demo)}")
    print(f"Seed: {args.seed}")
    print()
    print(demo[["site_id", "site_name", "lat", "lon", "public_access", "parking_spaces"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
