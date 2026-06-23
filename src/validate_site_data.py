"""Validate candidate-site input data for the EV charging prototype.

This script is a planning checklist, not an engineering approval tool.
It helps identify missing values, placeholder assumptions, and review flags in
candidate-site CSV files such as data/inputs/real_sites_v1.csv.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_INPUT = "data/inputs/real_sites_v1.csv"
DEFAULT_OUTPUT = "data/outputs/data_quality_report.csv"

REQUIRED_COLUMNS = [
    "site_id", "site_name", "site_type", "address", "city", "state", "zip",
    "lat", "lon", "public_access", "employees_day", "visitors_day",
    "fleet_vehicles", "parking_spaces", "hours_open", "avg_dwell_min",
    "nearby_households_1mi", "nearby_jobs_1mi", "aadt_nearest",
    "amenities_count_0_5mi", "ev_registrations_local", "ev_share_local",
    "existing_l2_ports_1mi", "existing_dcfc_ports_3mi", "equity_gap_index",
    "elec_service_voltage", "elec_service_rating_amp", "spare_capacity_kw",
    "distance_to_service_ft", "trenching_ft", "trench_cost_per_ft",
    "service_upgrade_cost_usd", "ada_layout_possible", "fire_access_ok",
    "garage_enclosed", "emergency_disconnect_visible", "stormwater_risk",
    "battery_storage_flag", "battery_storage_kwh", "notes",
]

NUMERIC_COLUMNS = [
    "lat", "lon", "public_access", "employees_day", "visitors_day",
    "fleet_vehicles", "parking_spaces", "hours_open", "avg_dwell_min",
    "nearby_households_1mi", "nearby_jobs_1mi", "aadt_nearest",
    "amenities_count_0_5mi", "ev_registrations_local", "ev_share_local",
    "existing_l2_ports_1mi", "existing_dcfc_ports_3mi", "equity_gap_index",
    "elec_service_voltage", "elec_service_rating_amp", "spare_capacity_kw",
    "distance_to_service_ft", "trenching_ft", "trench_cost_per_ft",
    "service_upgrade_cost_usd", "ada_layout_possible", "fire_access_ok",
    "garage_enclosed", "emergency_disconnect_visible", "stormwater_risk",
    "battery_storage_flag", "battery_storage_kwh",
]

BINARY_COLUMNS = [
    "public_access", "ada_layout_possible", "fire_access_ok", "garage_enclosed",
    "emergency_disconnect_visible", "stormwater_risk", "battery_storage_flag",
]

PLACEHOLDER_ZERO_FIELDS = {
    "ev_registrations_local": "Replace zero with a local EV registration count or document why unavailable.",
    "parking_spaces": "Confirm parking-space count from site records, GIS, or stakeholder input.",
    "elec_service_rating_amp": "Replace placeholder with service rating if available from facility/utility review.",
    "spare_capacity_kw": "Replace placeholder with estimated or confirmed spare electrical capacity.",
    "distance_to_service_ft": "Estimate distance from likely charger area to electrical service.",
    "trenching_ft": "Estimate trenching length or document why trenching is not expected.",
    "service_upgrade_cost_usd": "Add a planning-level service-upgrade estimate or explain why none is expected.",
}

SAFETY_REVIEW_RULES = {
    "public_access": (0, "Limited or non-public access", "Treat as special-use/fleet-support unless public access is confirmed."),
    "ada_layout_possible": (0, "ADA-accessible layout unresolved", "Review charger location, accessible route, slopes, aisle width, and signage needs."),
    "fire_access_ok": (0, "Fire apparatus access concern", "Request AHJ or Fire Marshal review before treating site as ready."),
    "garage_enclosed": (1, "Enclosed garage or limited ventilation/access", "Review ventilation, fire response access, charger placement, and emergency procedures."),
    "emergency_disconnect_visible": (0, "Emergency disconnect visibility not confirmed", "Confirm emergency disconnect location and visibility during site review."),
    "stormwater_risk": (1, "Stormwater or firefighting runoff concern", "Review drainage, runoff path, and firefighting-water management with site staff."),
    "battery_storage_flag": (1, "Battery storage present/proposed", "Add battery-storage-specific AHJ, fire, and code review."),
}

ASSUMPTION_FIELDS = ["employees_day", "visitors_day", "hours_open", "avg_dwell_min"]
SEVERITY_ORDER = ["ERROR", "WARNING", "REVIEW", "INFO"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate EV charging candidate-site input data.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Candidate-site CSV to validate.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="CSV report to create.")
    return parser.parse_args()


def clean_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    return text if len(text) <= 160 else text[:157] + "..."


def normalized_note(row: pd.Series) -> str:
    return str(row.get("notes", "") or "").lower()


def note_documents_field(row: pd.Series, field: str) -> bool:
    """Return True when notes show that a field has stronger source support."""
    note = normalized_note(row)
    if field == "hours_open":
        return "hours_open" in note and any(word in note for word in ["official", "supports", "supported"])
    if field == "amenities_count_0_5mi":
        return "amenities_count" in note and any(word in note for word in ["osm", "overpass", "reviewed"])
    return False


def add_issue(issues: list[dict[str, str]], severity: str, site_id: str, site_name: str,
              field: str, issue: str, current_value: Any, recommended_next_step: str) -> None:
    issues.append({
        "severity": severity,
        "site_id": site_id,
        "site_name": site_name,
        "field": field,
        "issue": issue,
        "current_value": clean_value(current_value),
        "recommended_next_step": recommended_next_step,
    })


def site_label(row: pd.Series) -> tuple[str, str]:
    site_id = clean_value(row.get("site_id", "UNKNOWN")) or "UNKNOWN"
    return site_id, clean_value(row.get("site_name", ""))


def validate_required_columns(df: pd.DataFrame, issues: list[dict[str, str]]) -> None:
    for column in [col for col in REQUIRED_COLUMNS if col not in df.columns]:
        add_issue(issues, "ERROR", "GLOBAL", "Dataset", column, "Missing required column",
                  "missing", "Add this column to the input CSV or update the model/schema if intentionally removed.")


def validate_blank_required_values(df: pd.DataFrame, issues: list[dict[str, str]]) -> None:
    for column in ["site_id", "site_name", "site_type", "address", "city", "state"]:
        if column not in df.columns:
            continue
        blank_mask = df[column].isna() | (df[column].astype(str).str.strip() == "")
        for _, row in df[blank_mask].iterrows():
            site_id, site_name = site_label(row)
            add_issue(issues, "ERROR", site_id, site_name, column, "Blank required text value",
                      row.get(column, ""), "Fill this value so the site can be clearly identified and mapped.")


def validate_duplicate_site_ids(df: pd.DataFrame, issues: list[dict[str, str]]) -> None:
    if "site_id" not in df.columns:
        return
    for _, row in df[df["site_id"].duplicated(keep=False)].iterrows():
        site_id, site_name = site_label(row)
        add_issue(issues, "ERROR", site_id, site_name, "site_id", "Duplicate site_id",
                  row.get("site_id", ""), "Make every site_id unique so outputs and charts do not merge sites.")


def validate_numeric_columns(df: pd.DataFrame, issues: list[dict[str, str]]) -> pd.DataFrame:
    numeric_df = df.copy()
    for column in NUMERIC_COLUMNS:
        if column not in df.columns:
            continue
        converted = pd.to_numeric(df[column], errors="coerce")
        bad_mask = converted.isna() & df[column].notna() & (df[column].astype(str).str.strip() != "")
        for _, row in df[bad_mask].iterrows():
            site_id, site_name = site_label(row)
            add_issue(issues, "ERROR", site_id, site_name, column, "Value should be numeric",
                      row.get(column, ""), "Replace with a number or update the model to handle blanks.")
        numeric_df[column] = converted
    return numeric_df


def validate_binary_columns(df: pd.DataFrame, issues: list[dict[str, str]]) -> None:
    for column in BINARY_COLUMNS:
        if column not in df.columns:
            continue
        invalid_mask = ~df[column].isin([0, 1]) & df[column].notna()
        for _, row in df[invalid_mask].iterrows():
            site_id, site_name = site_label(row)
            add_issue(issues, "ERROR", site_id, site_name, column, "Binary field should be 0 or 1",
                      row.get(column, ""), "Use 1 for yes/true and 0 for no/false.")


def validate_coordinates(df: pd.DataFrame, issues: list[dict[str, str]]) -> None:
    if "lat" in df.columns:
        for _, row in df[df["lat"].isna() | (df["lat"] < -90) | (df["lat"] > 90)].iterrows():
            site_id, site_name = site_label(row)
            add_issue(issues, "ERROR", site_id, site_name, "lat", "Latitude is missing or outside valid range",
                      row.get("lat", ""), "Confirm site coordinates from GIS or another documented source.")
    if "lon" in df.columns:
        for _, row in df[df["lon"].isna() | (df["lon"] < -180) | (df["lon"] > 180)].iterrows():
            site_id, site_name = site_label(row)
            add_issue(issues, "ERROR", site_id, site_name, "lon", "Longitude is missing or outside valid range",
                      row.get("lon", ""), "Confirm site coordinates from GIS or another documented source.")


def validate_placeholder_values(df: pd.DataFrame, issues: list[dict[str, str]]) -> None:
    for column, next_step in PLACEHOLDER_ZERO_FIELDS.items():
        if column not in df.columns:
            continue
        for _, row in df[df[column] == 0].iterrows():
            site_id, site_name = site_label(row)
            add_issue(issues, "REVIEW", site_id, site_name, column,
                      "Zero value may be a placeholder or unconfirmed assumption", row.get(column, ""), next_step)


def validate_safety_review_flags(df: pd.DataFrame, issues: list[dict[str, str]]) -> None:
    for column, (bad_value, issue, next_step) in SAFETY_REVIEW_RULES.items():
        if column not in df.columns:
            continue
        for _, row in df[df[column] == bad_value].iterrows():
            site_id, site_name = site_label(row)
            add_issue(issues, "REVIEW", site_id, site_name, column, issue, row.get(column, ""), next_step)


def validate_assumption_notes(df: pd.DataFrame, issues: list[dict[str, str]]) -> None:
    if "notes" not in df.columns:
        return
    notes = df["notes"].fillna("").astype(str).str.lower()
    assumption_mask = notes.str.contains("assumption|placeholder", regex=True)

    for _, row in df[assumption_mask].iterrows():
        site_id, site_name = site_label(row)
        add_issue(issues, "INFO", site_id, site_name, "notes",
                  "Row notes mention assumptions or placeholders", row.get("notes", ""),
                  "Use this row as a reminder to replace assumptions with official data, stakeholder estimates, or documented reasoning.")

    for column in ASSUMPTION_FIELDS:
        if column not in df.columns:
            continue
        field_mask = assumption_mask & notes.str.contains(column.lower(), regex=False)
        for _, row in df[field_mask].iterrows():
            if note_documents_field(row, column):
                continue
            site_id, site_name = site_label(row)
            add_issue(issues, "REVIEW", site_id, site_name, column, "Field appears to be assumption-based",
                      row.get(column, ""), "Replace with official data, stakeholder estimate, or a clearly documented assumption.")


def validate_equity_source(df: pd.DataFrame, issues: list[dict[str, str]]) -> None:
    if "equity_gap_index" not in df.columns:
        return
    for _, row in df.iterrows():
        site_id, site_name = site_label(row)
        value = row.get("equity_gap_index")
        if pd.notna(value) and (value < 0 or value > 1):
            add_issue(issues, "ERROR", site_id, site_name, "equity_gap_index",
                      "Equity index should be between 0 and 1", value,
                      "Review the equity extract and keep the normalized index in the 0 to 1 range.")

    if "notes" not in df.columns:
        add_issue(issues, "REVIEW", "GLOBAL", "Dataset", "equity_gap_index",
                  "Equity values need source documentation", "notes column missing",
                  "Document whether equity values are placeholders or official-derived ACS estimates.")
        return

    notes = df["notes"].fillna("").astype(str).str.lower()
    documented = notes.str.contains("equity", regex=False) & notes.str.contains(
        "source extract|source extracts|acs|official-derived|acs_equity_index", regex=True
    )
    for _, row in df[~documented].iterrows():
        site_id, site_name = site_label(row)
        add_issue(issues, "REVIEW", site_id, site_name, "equity_gap_index",
                  "Equity source not clearly documented in notes", row.get("equity_gap_index", ""),
                  "Add a note explaining whether equity_gap_index is from acs_equity_index_1mi.csv or still a placeholder.")


def validate_dataset_level_patterns(df: pd.DataFrame, issues: list[dict[str, str]]) -> None:
    if "ev_share_local" in df.columns:
        unique_ev_shares = sorted(df["ev_share_local"].dropna().unique().tolist())
        if len(unique_ev_shares) == 1:
            add_issue(issues, "REVIEW", "GLOBAL", "Dataset", "ev_share_local",
                      "Same EV-share value is used for every site", unique_ev_shares[0],
                      "Replace with locality-specific EV adoption estimates or document why one shared assumption is acceptable for V1.")

    if "amenities_count_0_5mi" in df.columns and (df["amenities_count_0_5mi"] == 0).all():
        add_issue(issues, "REVIEW", "GLOBAL", "Dataset", "amenities_count_0_5mi",
                  "Amenities are zero for every site", "all zero",
                  "Add a real amenities/POI method or remove this factor from scoring until it is supported.")

    if "service_upgrade_cost_usd" in df.columns and (df["service_upgrade_cost_usd"] == 0).all():
        add_issue(issues, "REVIEW", "GLOBAL", "Dataset", "service_upgrade_cost_usd",
                  "Service-upgrade cost is zero for every site", "all zero",
                  "Add planning-level electrical cost assumptions or document why costs are not yet estimated.")


def build_report(input_path: Path) -> pd.DataFrame:
    issues: list[dict[str, str]] = []
    if not input_path.exists():
        add_issue(issues, "ERROR", "GLOBAL", "Dataset", "input", "Input file not found",
                  str(input_path), "Check the file path and run the command from the repository root.")
        return pd.DataFrame(issues)

    df = pd.read_csv(input_path)
    validate_required_columns(df, issues)
    validate_blank_required_values(df, issues)
    validate_duplicate_site_ids(df, issues)
    numeric_df = validate_numeric_columns(df, issues)
    validate_binary_columns(numeric_df, issues)
    validate_coordinates(numeric_df, issues)
    validate_placeholder_values(numeric_df, issues)
    validate_safety_review_flags(numeric_df, issues)
    validate_assumption_notes(df, issues)
    validate_equity_source(numeric_df, issues)
    validate_dataset_level_patterns(numeric_df, issues)

    if not issues:
        add_issue(issues, "INFO", "GLOBAL", "Dataset", "all", "No validation issues found", "",
                  "The input passed the current checklist. Keep documenting source quality as the model improves.")

    report = pd.DataFrame(issues)
    report["severity"] = pd.Categorical(report["severity"], categories=SEVERITY_ORDER, ordered=True)
    report = report.sort_values(by=["severity", "site_id", "field", "issue"], kind="stable")
    report["severity"] = report["severity"].astype(str)
    return report


def print_summary(report: pd.DataFrame, input_path: Path, output_path: Path) -> None:
    print("EV CHARGER SITE DATA QUALITY CHECK")
    print("----------------------------------")
    print(f"Input file: {input_path}")
    print(f"Output report: {output_path}")
    print()
    counts = report["severity"].value_counts().to_dict()
    for severity in SEVERITY_ORDER:
        print(f"{severity}: {counts.get(severity, 0)}")
    print()
    if counts.get("ERROR", 0) > 0:
        print("Result: Fix ERROR items before relying on model outputs.")
    elif counts.get("REVIEW", 0) > 0 or counts.get("WARNING", 0) > 0:
        print("Result: No blocking errors, but several fields still need review or better support.")
    else:
        print("Result: No blocking issues found by the current checklist.")
    print()
    print("Top items to review:")
    preview = report[report["severity"].isin(["ERROR", "WARNING", "REVIEW"])].head(10)
    if preview.empty:
        print("- None")
    else:
        for _, row in preview.iterrows():
            print(f"- [{row['severity']}] {row['site_id']} | {row['field']}: {row['issue']}")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    report = build_report(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output_path, index=False)
    print_summary(report, input_path, output_path)


if __name__ == "__main__":
    main()
