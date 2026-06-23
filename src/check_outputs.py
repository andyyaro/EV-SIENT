"""Check generated model outputs and compare them to the V1 baseline.

This script is the single output-check step for the project. It first runs
sanity checks on the current generated outputs. If those checks pass, it then
creates a baseline comparison report against the committed V1 benchmark snapshot.

The V1 expectations that are likely to change over time live in
data/config/output_check_rules_v1.json instead of being hard-coded in this
script.

Run from the repository root after `python src/run_all.py`, or let run_all.py
call it automatically.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECK_RULES_FILE = "data/config/output_check_rules_v1.json"

REQUIRED_OUTPUT_FILES = [
    "data/outputs/data_quality_report.csv",
    "data/outputs/site_results.csv",
    "data/outputs/sensitivity_results.csv",
    "data/outputs/sensitivity_summary.csv",
    "data/outputs/profile_results.csv",
    "data/outputs/profile_rank_summary.csv",
    "data/outputs/profile_comparison.md",
    "data/outputs/model_run_summary.md",
    "data/outputs/results_interpretation.md",
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

REQUIRED_PROFILE_RESULTS_COLUMNS = [
    "profile_name",
    "profile_rank",
    "site_id",
    "site_name",
    "profile_readiness_score",
]


def output_path(relative_path: str) -> Path:
    return PROJECT_ROOT / relative_path


def add_issue(issues: list[str], message: str) -> None:
    issues.append(message)


def load_check_rules(issues: list[str]) -> dict[str, Any]:
    path = output_path(CHECK_RULES_FILE)
    if not path.exists():
        add_issue(issues, f"Missing output-check rules config: {CHECK_RULES_FILE}")
        return {}

    try:
        rules = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        add_issue(issues, f"Could not parse {CHECK_RULES_FILE}: {exc}")
        return {}

    if not isinstance(rules, dict):
        add_issue(issues, f"{CHECK_RULES_FILE} must contain a JSON object")
        return {}

    return rules


def get_expected_site_ids(rules: dict[str, Any], issues: list[str]) -> set[str]:
    site_ids = rules.get("expected_site_ids", [])
    if not isinstance(site_ids, list) or not site_ids:
        add_issue(issues, f"{CHECK_RULES_FILE} must define a non-empty expected_site_ids list")
        return set()
    return {str(site_id) for site_id in site_ids}


def get_expected_profile_names(rules: dict[str, Any], issues: list[str]) -> set[str]:
    profile_names = rules.get("expected_profile_names", [])
    if not isinstance(profile_names, list) or not profile_names:
        add_issue(issues, f"{CHECK_RULES_FILE} must define a non-empty expected_profile_names list")
        return set()
    return {str(profile_name) for profile_name in profile_names}


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


def check_site_results(issues: list[str], rules: dict[str, Any]) -> None:
    path = output_path("data/outputs/site_results.csv")
    if not path.exists():
        return

    results = pd.read_csv(path)
    require_columns(results, REQUIRED_SITE_RESULTS_COLUMNS, "site_results.csv", issues)
    if not set(REQUIRED_SITE_RESULTS_COLUMNS).issubset(results.columns):
        return

    expected_site_ids = get_expected_site_ids(rules, issues)
    actual_site_ids = set(results["site_id"].astype(str))
    if expected_site_ids and actual_site_ids != expected_site_ids:
        add_issue(
            issues,
            f"site_results.csv site IDs do not match expected V1 sites. "
            f"Expected {sorted(expected_site_ids)}, got {sorted(actual_site_ids)}",
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

    expected_top_site_id = str(rules.get("expected_top_site_id", ""))
    if not expected_top_site_id:
        add_issue(issues, f"{CHECK_RULES_FILE} must define expected_top_site_id")
    elif not ranks.isna().any():
        top_row = results.loc[ranks.idxmin()]
        top_site_id = str(top_row.get("site_id", ""))
        if top_site_id != expected_top_site_id:
            add_issue(
                issues,
                f"Expected current V1 top-ranked site to be {expected_top_site_id}, but got {top_site_id}",
            )


def check_data_quality_report(issues: list[str], rules: dict[str, Any]) -> None:
    path = output_path("data/outputs/data_quality_report.csv")
    if not path.exists():
        return

    report = pd.read_csv(path)
    require_columns(report, ["severity", "site_id", "field", "issue"], "data_quality_report.csv", issues)
    if "severity" not in report.columns:
        return

    if bool(rules.get("require_zero_data_quality_errors", True)):
        error_count = int((report["severity"] == "ERROR").sum())
        if error_count != 0:
            add_issue(issues, f"data_quality_report.csv has {error_count} ERROR item(s)")


def check_sensitivity_summary(issues: list[str], rules: dict[str, Any]) -> None:
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
    elif bool(rules.get("require_zero_sensitivity_rank_range", True)) and (rank_range != 0).any():
        moving_sites = summary.loc[rank_range != 0, "site_id"].astype(str).tolist()
        add_issue(issues, f"Expected V1 sensitivity rank_range to be 0 for every site; changed sites: {moving_sites}")


def check_profile_results(issues: list[str], rules: dict[str, Any]) -> None:
    path = output_path("data/outputs/profile_results.csv")
    if not path.exists():
        return

    profiles = pd.read_csv(path)
    require_columns(profiles, REQUIRED_PROFILE_RESULTS_COLUMNS, "profile_results.csv", issues)
    if not set(REQUIRED_PROFILE_RESULTS_COLUMNS).issubset(profiles.columns):
        return

    expected_site_ids = get_expected_site_ids(rules, issues)
    expected_profile_names = get_expected_profile_names(rules, issues)

    actual_profile_names = set(profiles["profile_name"].astype(str))
    if expected_profile_names and actual_profile_names != expected_profile_names:
        add_issue(
            issues,
            f"profile_results.csv profile names do not match expected V1 profiles. "
            f"Expected {sorted(expected_profile_names)}, got {sorted(actual_profile_names)}",
        )

    actual_site_ids = set(profiles["site_id"].astype(str))
    if expected_site_ids and actual_site_ids != expected_site_ids:
        add_issue(
            issues,
            f"profile_results.csv site IDs do not match expected V1 sites. "
            f"Expected {sorted(expected_site_ids)}, got {sorted(actual_site_ids)}",
        )

    duplicate_pairs = profiles[profiles[["profile_name", "site_id"]].duplicated()]
    if not duplicate_pairs.empty:
        duplicates = duplicate_pairs[["profile_name", "site_id"]].astype(str).to_dict("records")
        add_issue(issues, f"profile_results.csv has duplicate (profile_name, site_id) rows: {duplicates}")

    expected_profile_count = int(rules.get("expected_profile_count", len(expected_profile_names)))
    actual_profile_count = profiles["profile_name"].nunique()
    if expected_profile_count and actual_profile_count != expected_profile_count:
        add_issue(
            issues,
            f"profile_results.csv should contain {expected_profile_count} profiles, but contains {actual_profile_count}",
        )

    expected_sites_per_profile = int(rules.get("expected_sites_per_profile", len(expected_site_ids)))
    if expected_profile_count and expected_sites_per_profile:
        expected_rows = expected_profile_count * expected_sites_per_profile
        if len(profiles) != expected_rows:
            add_issue(issues, f"profile_results.csv should contain {expected_rows} rows, but contains {len(profiles)}")

    score_min = float(rules.get("profile_readiness_score_min", 0))
    score_max = float(rules.get("profile_readiness_score_max", 100))
    check_numeric_range(
        profiles,
        "profile_readiness_score",
        score_min,
        score_max,
        "profile_results.csv",
        issues,
    )

    for profile_name, group in profiles.groupby("profile_name", sort=False):
        label = f"profile_results.csv profile {profile_name}"

        if expected_sites_per_profile and len(group) != expected_sites_per_profile:
            add_issue(issues, f"{label} should contain {expected_sites_per_profile} sites, but contains {len(group)}")

        if expected_site_ids and set(group["site_id"].astype(str)) != expected_site_ids:
            add_issue(issues, f"{label} does not contain the expected site set")

        ranks = pd.to_numeric(group["profile_rank"], errors="coerce")
        if ranks.isna().any():
            add_issue(issues, f"{label} profile_rank contains blank or non-numeric values")
            continue

        if ranks.duplicated().any():
            add_issue(issues, f"{label} has duplicate profile_rank values")
            continue

        expected_ranks = list(range(1, len(group) + 1))
        actual_ranks = sorted(ranks.astype(int).tolist())
        if actual_ranks != expected_ranks:
            add_issue(issues, f"{label} profile_rank values should be consecutive starting at 1")


def run_checks() -> list[str]:
    issues: list[str] = []
    rules = load_check_rules(issues)

    check_required_files(issues)
    if rules:
        check_site_results(issues, rules)
        check_data_quality_report(issues, rules)
        check_sensitivity_summary(issues, rules)
        check_profile_results(issues, rules)

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
