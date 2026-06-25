"""Check whether local raw exports are present for the V2 public-data upgrade.

This script does not calculate new public-data values by itself.
It checks whether the local machine appears to have the raw exports needed to upgrade
new V2 sites from planning assumptions to official-derived/public-dataset values.

Run from the repository root:

    python src/check_v2_public_data_upgrade_inputs.py

The project intentionally does not commit all large raw exports, so missing files do not
mean the repo is broken. They mean the next step is to download, recreate, or locate the
raw export locally before recomputing the V2 values.
"""

from __future__ import annotations

from pathlib import Path


RAW_DIR = Path("data/raw_exports")

REQUIRED_OR_EXPECTED = [
    {
        "group": "ACS households/equity geometry",
        "filename_contains": "tl_2024_51_bg",
        "why_needed": "TIGER 2024 Virginia block group geometry for 1-mile households and equity buffers.",
    },
    {
        "group": "LODES workplace jobs",
        "filename_contains": "va_wac_S000_JT00_2023",
        "why_needed": "LODES 2023 workplace jobs for nearby_jobs_1mi.",
    },
    {
        "group": "VDOT traffic",
        "filename_contains": "VDOT_Bidirectional_Traffic_Volume_2025",
        "why_needed": "VDOT nearest traffic segment for aadt_nearest.",
    },
    {
        "group": "ACS households",
        "filename_contains": "B11001",
        "why_needed": "ACS household table for nearby_households_1mi.",
    },
    {
        "group": "ACS equity income",
        "filename_contains": "B19013",
        "why_needed": "ACS median household income for equity_gap_index.",
    },
    {
        "group": "ACS equity vehicles",
        "filename_contains": "B25044",
        "why_needed": "ACS vehicles-available table for equity_gap_index.",
    },
    {
        "group": "ACS equity tenure",
        "filename_contains": "B25003",
        "why_needed": "ACS renter/tenure table for equity_gap_index.",
    },
    {
        "group": "ACS equity structure type",
        "filename_contains": "B25024",
        "why_needed": "ACS multifamily/units-in-structure table for equity_gap_index.",
    },
]

OPTIONAL_OR_EXTERNAL = [
    {
        "group": "OSM amenities",
        "filename_contains": "amenities",
        "why_needed": "Reviewed OSM/Overpass extract for amenities_count_0_5mi.",
    },
    {
        "group": "EV adoption",
        "filename_contains": "EV",
        "why_needed": "Current DMV/state/local EV registration extract, if accessible.",
    },
]


def find_matches(raw_dir: Path, pattern_text: str) -> list[Path]:
    """Find local files whose name contains the requested text."""
    if not raw_dir.exists():
        return []

    needle = pattern_text.lower()
    return sorted(path for path in raw_dir.rglob("*") if needle in path.name.lower())


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def main() -> None:
    print("V2 PUBLIC-DATA UPGRADE INPUT CHECK")
    print("-----------------------------------")
    print(f"Raw export folder checked: {RAW_DIR}")

    if not RAW_DIR.exists():
        print()
        print("Status: data/raw_exports/ does not exist locally.")
        print("Create it or point the workflow to the folder where the raw exports are stored.")
        return

    all_required_found = True

    print_section("Required / expected public-data inputs")
    for item in REQUIRED_OR_EXPECTED:
        matches = find_matches(RAW_DIR, item["filename_contains"])
        status = "FOUND" if matches else "MISSING"
        if not matches:
            all_required_found = False
        print(f"{status}: {item['group']} — looking for '{item['filename_contains']}'")
        print(f"  Why: {item['why_needed']}")
        for match in matches[:5]:
            print(f"  - {match}")
        if len(matches) > 5:
            print(f"  ... plus {len(matches) - 5} more match(es)")

    print_section("Optional / may need separate download")
    for item in OPTIONAL_OR_EXTERNAL:
        matches = find_matches(RAW_DIR, item["filename_contains"])
        status = "FOUND" if matches else "NOT FOUND HERE"
        print(f"{status}: {item['group']} — looking for '{item['filename_contains']}'")
        print(f"  Why: {item['why_needed']}")
        for match in matches[:5]:
            print(f"  - {match}")
        if len(matches) > 5:
            print(f"  ... plus {len(matches) - 5} more match(es)")

    print_section("Next step")
    if all_required_found:
        print("The core raw inputs appear to be present.")
        print("Next: compute updated values for FFX003 and FFX004, then update real_sites_v2.csv and the source confidence tracker.")
    else:
        print("Some core raw inputs are missing or not in data/raw_exports/.")
        print("Next: locate/download the missing exports, then rerun this checker.")


if __name__ == "__main__":
    main()
