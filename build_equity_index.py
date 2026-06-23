"""
Build ACS-based equity gap index for candidate EV charging sites.

This script is intentionally separate from ev_charger_model.py.
It takes an ACS equity input extract and converts it into a 0-to-1
site-level equity_gap_index that can later be copied into real_sites_v1.csv.

Current V1 equity concept:
- lower income = higher equity gap
- higher no-vehicle household share = higher equity gap
- higher renter household share = higher equity gap
- higher multifamily housing share = higher equity gap

Important:
This script should be run only after the input values are filled from
ACS/Census-derived data. Do not treat blank template values as official data.

Run:
    python build_equity_index.py

Optional:
    python build_equity_index.py --input data/source_extracts/acs_equity_inputs_1mi.csv --output data/source_extracts/acs_equity_index_1mi.csv
"""

import argparse
import numpy as np
import pandas as pd


DEFAULT_INPUT = "data/source_extracts/acs_equity_inputs_1mi.csv"
DEFAULT_OUTPUT = "data/source_extracts/acs_equity_index_1mi.csv"

REQUIRED_COLUMNS = [
    "site_id",
    "site_name",
    "median_household_income",
    "total_households",
    "no_vehicle_households",
    "occupied_housing_units",
    "renter_occupied_households",
    "total_housing_units",
    "multifamily_units"
]


def minmax(series):
    """Normalize a numeric series from 0 to 1."""
    s = pd.to_numeric(series, errors="coerce")

    if s.isna().all():
        return pd.Series(np.nan, index=s.index)

    s_min = s.min(skipna=True)
    s_max = s.max(skipna=True)

    if s_max == s_min:
        return pd.Series(0.0, index=s.index)

    return (s - s_min) / (s_max - s_min)


def safe_divide(numerator, denominator):
    """Divide safely and return NaN where denominator is zero or missing."""
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    return np.where(denominator > 0, numerator / denominator, np.nan)


def validate_columns(df):
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def build_equity_index(df):
    """Calculate equity components and final equity_gap_index."""
    validate_columns(df)
    result = df.copy()

    numeric_cols = [
        "median_household_income",
        "total_households",
        "no_vehicle_households",
        "occupied_housing_units",
        "renter_occupied_households",
        "total_housing_units",
        "multifamily_units"
    ]

    for col in numeric_cols:
        result[col] = pd.to_numeric(result[col], errors="coerce")

    result["no_vehicle_household_share"] = safe_divide(
        result["no_vehicle_households"],
        result["total_households"]
    )

    result["renter_household_share"] = safe_divide(
        result["renter_occupied_households"],
        result["occupied_housing_units"]
    )

    result["multifamily_unit_share"] = safe_divide(
        result["multifamily_units"],
        result["total_housing_units"]
    )

    # Lower income should produce a higher equity component.
    result["lower_income_component"] = 1 - minmax(result["median_household_income"])

    # Higher no-vehicle, renter, and multifamily shares should produce higher equity components.
    result["no_vehicle_component"] = minmax(result["no_vehicle_household_share"])
    result["renter_component"] = minmax(result["renter_household_share"])
    result["multifamily_component"] = minmax(result["multifamily_unit_share"])

    component_cols = [
        "lower_income_component",
        "no_vehicle_component",
        "renter_component",
        "multifamily_component"
    ]

    if result[component_cols].isna().any(axis=None):
        print("WARNING: Some equity inputs are missing or invalid. Output rows with missing components should not be treated as final.")

    result["equity_gap_index"] = (
        0.35 * result["lower_income_component"] +
        0.30 * result["no_vehicle_component"] +
        0.20 * result["renter_component"] +
        0.15 * result["multifamily_component"]
    ).round(3)

    output_cols = [
        "site_id",
        "site_name",
        "median_household_income",
        "no_vehicle_household_share",
        "renter_household_share",
        "multifamily_unit_share",
        "lower_income_component",
        "no_vehicle_component",
        "renter_component",
        "multifamily_component",
        "equity_gap_index",
        "method",
        "source_tables",
        "notes"
    ]

    for optional_col in ["method", "source_tables", "notes"]:
        if optional_col not in result.columns:
            result[optional_col] = ""

    return result[output_cols]


def main():
    parser = argparse.ArgumentParser(description="Build ACS-derived equity_gap_index values for EV charging candidate sites.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help=f"Input CSV. Default: {DEFAULT_INPUT}")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help=f"Output CSV. Default: {DEFAULT_OUTPUT}")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    result = build_equity_index(df)
    result.to_csv(args.output, index=False)

    print("ACS EQUITY INDEX BUILD")
    print("----------------------")
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")
    print(result[["site_id", "site_name", "equity_gap_index"]].to_string(index=False))
    print("\nDone. Review the output before copying equity_gap_index into real_sites_v1.csv.")


if __name__ == "__main__":
    main()
