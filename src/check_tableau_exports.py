from __future__ import annotations

from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path("data/outputs")
TABLEAU_DIR = OUTPUT_DIR / "tableau"

EXPECTED_EXPORTS = {
    "tableau_site_readiness.csv": [
        "Rank", "Site ID", "Site Name", "Readiness Score", "Tier",
        "Install Now Ports", "Future Ready Ports", "Expansion Strategy",
        "Electrical Risk Level", "Site Label",
    ],
    "tableau_site_map.csv": [
        "Rank", "Site ID", "Site Name", "County", "Address", "Latitude", "Longitude",
        "Readiness Score", "Tier", "Install Now Ports", "Future Ready Ports", "Site Label",
    ],
    "tableau_map_points.csv": [
        "Rank", "Site ID", "Site Name", "Latitude", "Longitude", "Point Type",
        "Point Name", "Map Label", "Map Size", "Tooltip Text",
    ],
    "tableau_port_growth.csv": [
        "Rank", "Site ID", "Site Name", "Site Label", "Planning Horizon",
        "Planning Horizon Order", "Recommended Ports", "Tooltip Text",
    ],
    "tableau_review_burden.csv": [
        "Rank", "Site ID", "Site Name", "Site Label", "Review Burden Score",
        "Review Burden Level", "Review Flags", "Tooltip Text",
    ],
    "tableau_review_burden_map.csv": [
        "Rank", "Site ID", "Site Name", "Latitude", "Longitude", "Review Burden Score",
        "Map Label", "Map Size", "Map Color Group", "Tooltip Text",
    ],
    "tableau_profile_score_heatmap.csv": [
        "Site ID", "Site Name", "Site Label", "Profile Name", "Profile Label",
        "Profile Sort", "Profile Rank", "Profile Readiness Score", "Base Model Rank",
        "Tooltip Text",
    ],
    "tableau_profile_subscore_heatmap.csv": [
        "Site ID", "Site Name", "Site Label", "Profile Name", "Profile Label",
        "Score Dimension", "Dimension Sort", "Dimension Score", "Tooltip Text",
    ],
    "tableau_profile_rank_stability.csv": [
        "Site ID", "Site Name", "Site Label", "Base Model Rank", "Best Profile Rank",
        "Worst Profile Rank", "Average Profile Rank", "Profile Rank Range", "Stability Level",
        "Tooltip Text",
    ],
    "tableau_data_confidence.csv": [
        "Model Rank", "Site ID", "Site Name", "Site Label", "Readiness Score",
        "Data Confidence Level", "Data Review Issue Count", "Tooltip Text",
    ],
    "tableau_data_quality_issues.csv": [
        "Severity", "Site ID", "Site Name", "Site Label", "Field", "Issue",
        "Current Value", "Recommended Next Step", "Tooltip Text",
    ],
    "tableau_port_sizing_scenario_heatmap.csv": [
        "Scenario Name", "Scenario Label", "Scenario Sort", "Site ID", "Site Name",
        "Site Label", "Future Capacity Gap", "Future Gap Category", "Tooltip Text",
    ],
    "tableau_port_utilization_simulation.csv": [
        "Site ID", "Site Name", "Site Label", "Demand Case", "Demand Case Sort",
        "Port Count", "Utilization Percent", "Queue Risk Level", "Recommended Port Marker",
        "Tooltip Text",
    ],
    "tableau_action_recommendation_matrix.csv": [
        "Model Rank", "Action Priority", "Action Group", "Site ID", "Site Name",
        "Site Label", "Readiness Score", "Recommendation Tier", "Action Label", "Tooltip Text",
    ],
    "tableau_action_decision_quadrant_clean.csv": [
        "Model Rank", "Site ID", "Site Name", "Site Label", "Readiness Score",
        "Implementation Complexity Score", "Decision Quadrant", "Future Ready Capacity",
        "Tooltip Text",
    ],
}

SITE_COVERAGE_FILES = [
    "tableau_site_readiness.csv",
    "tableau_site_map.csv",
    "tableau_map_points.csv",
    "tableau_port_growth.csv",
    "tableau_review_burden.csv",
    "tableau_review_burden_map.csv",
    "tableau_profile_score_heatmap.csv",
    "tableau_profile_subscore_heatmap.csv",
    "tableau_profile_rank_stability.csv",
    "tableau_data_confidence.csv",
    "tableau_port_sizing_scenario_heatmap.csv",
    "tableau_port_utilization_simulation.csv",
    "tableau_action_recommendation_matrix.csv",
    "tableau_action_decision_quadrant_clean.csv",
]


def fail(message: str) -> None:
    raise SystemExit(f"Status: FAILED\n{message}")


def read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001 - checker should report any CSV read failure clearly.
        fail(f"Could not read {path}: {exc}")


def require_columns(df: pd.DataFrame, filename: str, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        fail(f"{filename} is missing required columns: {missing}")
    unnamed = [column for column in df.columns if str(column).startswith("Unnamed:")]
    if unnamed:
        fail(f"{filename} contains unnamed index-like columns: {unnamed}")


def check_exact_export_set() -> None:
    actual = sorted(path.name for path in TABLEAU_DIR.glob("tableau_*.csv"))
    expected = sorted(EXPECTED_EXPORTS)
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing:
        fail(f"Missing Tableau exports: {missing}")
    if extra:
        fail(f"Unexpected stale Tableau exports: {extra}")


def load_expected_site_ids() -> list[str]:
    summary_path = OUTPUT_DIR / "v2_executive_site_summary.csv"
    if not summary_path.exists():
        fail(f"Missing executive summary required for site coverage check: {summary_path}")
    summary = read_csv(summary_path)
    if "site_id" not in summary.columns:
        fail("v2_executive_site_summary.csv is missing site_id.")
    site_ids = sorted(summary["site_id"].dropna().astype(str).unique())
    if len(site_ids) != 12:
        fail(f"Expected 12 V2 candidate sites in executive summary, found {len(site_ids)}: {site_ids}")
    return site_ids


def check_site_coverage(filename: str, df: pd.DataFrame, expected_site_ids: list[str]) -> None:
    if "Site ID" not in df.columns:
        fail(f"{filename} cannot be checked for site coverage because it is missing Site ID.")
    actual = sorted(df["Site ID"].dropna().astype(str).unique())
    if actual != expected_site_ids:
        fail(f"{filename} site coverage mismatch. Expected {expected_site_ids}, found {actual}")


def check_row_counts(frames: dict[str, pd.DataFrame], site_count: int) -> None:
    if len(frames["tableau_site_readiness.csv"]) != site_count:
        fail("tableau_site_readiness.csv should have one row per site.")
    if len(frames["tableau_site_map.csv"]) != site_count:
        fail("tableau_site_map.csv should have one row per site.")
    if len(frames["tableau_map_points.csv"]) != site_count:
        fail("tableau_map_points.csv should have one row per site.")
    if len(frames["tableau_review_burden.csv"]) != site_count:
        fail("tableau_review_burden.csv should have one row per site.")
    if len(frames["tableau_review_burden_map.csv"]) != site_count:
        fail("tableau_review_burden_map.csv should have one row per site.")
    if len(frames["tableau_data_confidence.csv"]) != site_count:
        fail("tableau_data_confidence.csv should have one row per site.")
    if len(frames["tableau_action_recommendation_matrix.csv"]) != site_count:
        fail("tableau_action_recommendation_matrix.csv should have one row per site.")
    if len(frames["tableau_action_decision_quadrant_clean.csv"]) != site_count:
        fail("tableau_action_decision_quadrant_clean.csv should have one row per site.")

    port_growth = frames["tableau_port_growth.csv"]
    expected_growth_rows = site_count * 3
    if len(port_growth) != expected_growth_rows:
        fail(f"tableau_port_growth.csv should have {expected_growth_rows} rows, found {len(port_growth)}.")

    profile_heatmap = frames["tableau_profile_score_heatmap.csv"]
    profile_count = profile_heatmap["Profile Name"].nunique()
    if profile_count < 1:
        fail("tableau_profile_score_heatmap.csv has no scoring profiles.")
    expected_profile_rows = site_count * profile_count
    if len(profile_heatmap) != expected_profile_rows:
        fail(f"tableau_profile_score_heatmap.csv should have {expected_profile_rows} rows, found {len(profile_heatmap)}.")

    subscore = frames["tableau_profile_subscore_heatmap.csv"]
    dimension_count = subscore["Score Dimension"].nunique()
    expected_subscore_rows = site_count * profile_count * dimension_count
    if dimension_count != 4:
        fail(f"tableau_profile_subscore_heatmap.csv should contain 4 score dimensions, found {dimension_count}.")
    if len(subscore) != expected_subscore_rows:
        fail(f"tableau_profile_subscore_heatmap.csv should have {expected_subscore_rows} rows, found {len(subscore)}.")

    scenario_heatmap = frames["tableau_port_sizing_scenario_heatmap.csv"]
    scenario_count = scenario_heatmap["Scenario Name"].nunique()
    if scenario_count < 1:
        fail("tableau_port_sizing_scenario_heatmap.csv has no scenarios.")
    expected_scenario_rows = site_count * scenario_count
    if len(scenario_heatmap) != expected_scenario_rows:
        fail(f"tableau_port_sizing_scenario_heatmap.csv should have {expected_scenario_rows} rows, found {len(scenario_heatmap)}.")


def check_numeric_fields(frames: dict[str, pd.DataFrame]) -> None:
    numeric_checks = {
        "tableau_site_readiness.csv": ["Rank", "Readiness Score", "Install Now Ports", "Future Ready Ports"],
        "tableau_site_map.csv": ["Latitude", "Longitude", "Readiness Score"],
        "tableau_review_burden.csv": ["Review Burden Score"],
        "tableau_port_growth.csv": ["Planning Horizon Order", "Recommended Ports"],
        "tableau_action_decision_quadrant_clean.csv": ["Readiness Score", "Implementation Complexity Score", "Future Ready Capacity"],
    }
    for filename, columns in numeric_checks.items():
        df = frames[filename]
        for column in columns:
            converted = pd.to_numeric(df[column], errors="coerce")
            if converted.isna().any():
                fail(f"{filename} has non-numeric or missing values in {column}.")


def check_quadrant_schema(df: pd.DataFrame) -> None:
    if "Decision Quadrant Adjusted" in df.columns:
        fail("tableau_action_decision_quadrant_clean.csv still contains old Decision Quadrant Adjusted column.")
    values = set(df["Decision Quadrant"].dropna().astype(str))
    if not values:
        fail("tableau_action_decision_quadrant_clean.csv has no Decision Quadrant values.")


def main() -> None:
    if not TABLEAU_DIR.exists():
        fail(f"Missing Tableau export directory: {TABLEAU_DIR}")

    check_exact_export_set()
    expected_site_ids = load_expected_site_ids()
    frames: dict[str, pd.DataFrame] = {}

    for filename, required_columns in EXPECTED_EXPORTS.items():
        path = TABLEAU_DIR / filename
        if not path.exists():
            fail(f"Missing Tableau export: {path}")
        if path.stat().st_size == 0:
            fail(f"Tableau export is empty: {path}")
        df = read_csv(path)
        if df.empty:
            fail(f"Tableau export has no rows: {path}")
        require_columns(df, filename, required_columns)
        frames[filename] = df

    for filename in SITE_COVERAGE_FILES:
        check_site_coverage(filename, frames[filename], expected_site_ids)

    check_row_counts(frames, len(expected_site_ids))
    check_numeric_fields(frames)
    check_quadrant_schema(frames["tableau_action_decision_quadrant_clean.csv"])

    print("TABLEAU EXPORT CHECK")
    print("--------------------")
    print("Status: PASSED")
    print(f"Checked exports: {len(EXPECTED_EXPORTS)}/{len(EXPECTED_EXPORTS)}")
    print(f"Candidate sites represented: {len(expected_site_ids)}/12")
    print("Exact export set, required columns, row counts, numeric fields, and site coverage are valid.")


if __name__ == "__main__":
    main()
