"""Check generated model outputs and compare them to the V1 baseline.

This script is the single output-check step for the project. It first runs
sanity checks on the current generated outputs. If those checks pass, it then
creates a baseline comparison report against the committed V1 benchmark snapshot.

Run from the repository root after `python src/run_all.py`, or let run_all.py
call it automatically.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SITE_IDS = {"PWC001", "PWC002", "PWC003", "PWC004", "FFX001", "FFX002"}
EXPECTED_TOP_SITE_ID = "FFX002"

REQUIRED_OUTPUT_FILES = [
    "data/outputs/data_quality_report.csv",
    "data/outputs/site_results.csv",
    "data/outputs/sensitivity_results.csv",
    "data/outputs/sensitivity_summary.csv",
    "data/outputs/profile_results.csv",
    "data/outputs/profile_rank_summary.csv",
    "data/outputs/profile_comparison.md",
    "data/outputs/model_run_summary.md",
    "data/outputs/charts/readiness_score_chart.png",
    "data/outputs/charts/site_readiness_map.png",
]

REQUIRED_SITE_RESULTS_COLUMNS = [
    "model_rank",
    "site_id",
    "site_name",
    "readiness_score",
    "recommendation_tier",
    "recommended_ports_now",
    "recommended_ports_2035",
    "recommended_ports_2050",
]


def output_path(relative_path: str) -> Path:
    return PROJECT_ROOT / relative_path


def add_issue(issues: list[str], message: str) -> None:
    issues.append(message)


def require_file_exists(relative_path: str, issues: list[str]) -> None:
    path = output_path(relative_path)
    if not path.exists():
        add_issue(issues, f"Missing expected output file: {relative_path}")
        return
    if path.stat().st_size == 0:
        add_issue(issues, f"Output file is empty: {relative_path}")


def require_columns(df: pd.DataFrame, columns: list[str], label: str, issues: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        add_issue(issues, f"{label} is missing columns: {missing}")


def check_numeric_range(
    df: pd.DataFrame,
    column: str,
    min_value: float,
    max_value: float,
    label: str,
    issues: list[str],
) -> None:
    if column not in df.columns:
        add_issue(issues, f"{label} is missing required numeric column: {column}")
        return

    values = pd.to_numeric(df[column], errors="coerce")
    if values.isna().any():
        add_issue(issues, f"{label}.{column} contains blank or non-numeric values")
        return

    bad = df[(values < min_value) | (values > max_value)]
    if not bad.empty:
        site_list = bad.get("site_id", pd.Series(["unknown"] * len(bad))).astype(str).tolist()
        add_issue(
            issues,
            f"{label}.{column} has values outside {min_value} to {max_value} for sites: {site_list}",
        )


def check_required_files(issues: list[str]) -> None:
    for relative_path in REQUIRED_OUTPUT_FILES:
        require_file_exists(relative_path, issues)


def check_site_results(issues: list[str]) -> None:
    path = output_path("data/outputs/site_results.csv")
    if not path.exists():
        return

    results = pd.read_csv(path)
    require_columns(results, REQUIRED_SITE_RESULTS_COLUMNS, "site_results.csv", issues)
    if not set(REQUIRED_SITE_RESULTS_COLUMNS).issubset(results.columns):
        return

    actual_site_ids = set(results["site_id"].astype(str))
    if actual_site_ids != EXPECTED_SITE_IDS:
        add_issue(
            issues,
            f"site_results.csv site IDs do not match expected V1 sites. Expected {sorted(EXPECTED_SITE_IDS)}, got {sorted(actual_site_ids)}",
        )

    if results["site_id"].duplicated().any():
        duplicates = results.loc[results["site_id"].duplicated(), "site_id"].astype(str).tolist()
        add_issue(issues, f"site_results.csv has duplicate site_id values: {duplicates}")

    ranks = pd.to_numeric(results["model_rank"], errors="coerce")
    if ranks.isna().any():
        add_issue(issues, "site_results.csv model_rank contains blank or non-numeric values")
    elif ranks.duplicated().any():
        add_issue(issues, "site_results.csv has duplicate model_rank values")
    elif sorted(ranks.astype(int).tolist()) != list(range(1, len(results) + 1)):
        add_issue(issues, "site_results.csv model_rank values should be consecutive starting at 1")

    check_numeric_range(results, "readiness_score", 0, 100, "site_results.csv", issues)
    for column in ["recommended_ports_now", "recommended_ports_2035", "recommended_ports_2050"]:
        check_numeric_range(results, column, 0, 100, "site_results.csv", issues)

    if not ranks.isna().any():
        top_row = results.loc[ranks.idxmin()]
        top_site_id = str(top_row.get("site_id", ""))
        if top_site_id != EXPECTED_TOP_SITE_ID:
            add_issue(
                issues,
                f"Expected current V1 top-ranked site to be {EXPECTED_TOP_SITE_ID}, but got {top_site_id}",
            )


def check_data_quality_report(issues: list[str]) -> None:
    path = output_path("data/outputs/data_quality_report.csv")
    if not path.exists():
        return

    report = pd.read_csv(path)
    require_columns(report, ["severity", "site_id", "field", "issue"], "data_quality_report.csv", issues)
    if "severity" not in report.columns:
        return

    error_count = int((report["severity"] == "ERROR").sum())
    if error_count != 0:
        add_issue(issues, f"data_quality_report.csv has {error_count} ERROR item(s)")


def check_sensitivity_summary(issues: list[str]) -> None:
    path = output_path("data/outputs/sensitivity_summary.csv")
    if not path.exists():
        return

    summary = pd.read_csv(path)
    require_columns(summary, ["site_id", "best_rank", "worst_rank", "rank_range"], "sensitivity_summary.csv", issues)
    if "rank_range" not in summary.columns:
        return

    rank_range = pd.to_numeric(summary["rank_range"], errors="coerce")
    if rank_range.isna().any():
        add_issue(issues, "sensitivity_summary.csv rank_range contains blank or non-numeric values")
    elif (rank_range != 0).any():
        moving_sites = summary.loc[rank_range != 0, "site_id"].astype(str).tolist()
        add_issue(issues, f"Expected V1 sensitivity rank_range to be 0 for every site; changed sites: {moving_sites}")


def run_checks() -> list[str]:
    issues: list[str] = []
    check_required_files(issues)
    check_site_results(issues)
    check_data_quality_report(issues)
    check_sensitivity_summary(issues)
    return issues


def run_baseline_comparison() -> None:
    completed = subprocess.run(
        [sys.executable, "src/compare_to_baseline.py"],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit("Baseline comparison failed.")


def main() -> None:
    issues = run_checks()

    print("MODEL OUTPUT CHECK")
    print("------------------")

    if issues:
        print("Sanity check: FAILED")
        print()
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)

    print("Sanity check: PASSED")
    print()
    run_baseline_comparison()
    print()
    print("Result: PASSED")
    print("Current outputs are valid, and the baseline comparison report was generated.")


if __name__ == "__main__":
    main()
