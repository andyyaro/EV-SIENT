"""Check generated outputs and create the baseline comparison report."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULES_FILE = "data/config/output_check_rules_v1.json"

REQUIRED_FILES = [
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
    "data/outputs/charts/profile_rank_stability_chart.png",
    "data/outputs/charts/site_readiness_map.png",
]

SITE_COLUMNS = [
    "model_rank",
    "site_id",
    "site_name",
    "readiness_score",
    "recommendation_tier",
    "recommended_ports_now",
    "recommended_ports_2035",
    "recommended_ports_2050",
]

PROFILE_COLUMNS = [
    "profile_name",
    "profile_rank",
    "site_id",
    "site_name",
    "profile_readiness_score",
]


def p(relative_path: str) -> Path:
    return PROJECT_ROOT / relative_path


def add(issues: list[str], message: str) -> None:
    issues.append(message)


def load_rules(issues: list[str]) -> dict[str, Any]:
    path = p(RULES_FILE)
    if not path.exists():
        add(issues, f"Missing rules file: {RULES_FILE}")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        add(issues, f"Could not parse {RULES_FILE}: {exc}")
        return {}
    if not isinstance(data, dict):
        add(issues, f"{RULES_FILE} must contain a JSON object")
        return {}
    return data


def require_files(issues: list[str]) -> None:
    for relative_path in REQUIRED_FILES:
        path = p(relative_path)
        if not path.exists():
            add(issues, f"Missing expected output file: {relative_path}")
        elif path.stat().st_size == 0:
            add(issues, f"Output file is empty: {relative_path}")


def require_columns(df: pd.DataFrame, columns: list[str], label: str, issues: list[str]) -> bool:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        add(issues, f"{label} is missing columns: {missing}")
        return False
    return True


def numeric_series(df: pd.DataFrame, column: str, label: str, issues: list[str]) -> pd.Series | None:
    values = pd.to_numeric(df[column], errors="coerce")
    if values.isna().any():
        add(issues, f"{label}.{column} contains blank or non-numeric values")
        return None
    return values


def require_range(df: pd.DataFrame, column: str, low: float, high: float, label: str, issues: list[str]) -> None:
    values = numeric_series(df, column, label, issues)
    if values is None:
        return
    bad = df[(values < low) | (values > high)]
    if not bad.empty:
        sites = bad.get("site_id", pd.Series(["unknown"] * len(bad))).astype(str).tolist()
        add(issues, f"{label}.{column} outside {low} to {high}: {sites}")


def expected_set(rules: dict[str, Any], key: str, issues: list[str]) -> set[str]:
    values = rules.get(key, [])
    if not isinstance(values, list) or not values:
        add(issues, f"{RULES_FILE} must define non-empty {key}")
        return set()
    return {str(value) for value in values}


def check_site_results(issues: list[str], rules: dict[str, Any]) -> None:
    path = p("data/outputs/site_results.csv")
    if not path.exists():
        return
    df = pd.read_csv(path)
    if not require_columns(df, SITE_COLUMNS, "site_results.csv", issues):
        return

    expected_sites = expected_set(rules, "expected_site_ids", issues)
    actual_sites = set(df["site_id"].astype(str))
    if expected_sites and actual_sites != expected_sites:
        add(issues, f"site_results.csv site IDs differ. Expected {sorted(expected_sites)}, got {sorted(actual_sites)}")

    if df["site_id"].duplicated().any():
        add(issues, "site_results.csv has duplicate site_id values")

    ranks = numeric_series(df, "model_rank", "site_results.csv", issues)
    if ranks is not None:
        actual = sorted(ranks.astype(int).tolist())
        expected = list(range(1, len(df) + 1))
        if actual != expected:
            add(issues, "site_results.csv model_rank values should be consecutive starting at 1")
        top_site = str(df.loc[ranks.idxmin(), "site_id"])
        expected_top = str(rules.get("expected_top_site_id", ""))
        if expected_top and top_site != expected_top:
            add(issues, f"Expected top site {expected_top}, got {top_site}")

    require_range(df, "readiness_score", 0, 100, "site_results.csv", issues)
    for column in ["recommended_ports_now", "recommended_ports_2035", "recommended_ports_2050"]:
        require_range(df, column, 0, 100, "site_results.csv", issues)


def check_quality_report(issues: list[str], rules: dict[str, Any]) -> None:
    path = p("data/outputs/data_quality_report.csv")
    if not path.exists():
        return
    df = pd.read_csv(path)
    if not require_columns(df, ["severity", "site_id", "field", "issue"], "data_quality_report.csv", issues):
        return
    if bool(rules.get("require_zero_data_quality_errors", True)):
        count = int((df["severity"] == "ERROR").sum())
        if count:
            add(issues, f"data_quality_report.csv has {count} ERROR item(s)")


def check_sensitivity(issues: list[str], rules: dict[str, Any]) -> None:
    path = p("data/outputs/sensitivity_summary.csv")
    if not path.exists():
        return
    df = pd.read_csv(path)
    if not require_columns(df, ["site_id", "best_rank", "worst_rank", "rank_range"], "sensitivity_summary.csv", issues):
        return
    rank_range = numeric_series(df, "rank_range", "sensitivity_summary.csv", issues)
    if rank_range is not None and bool(rules.get("require_zero_sensitivity_rank_range", True)) and (rank_range != 0).any():
        sites = df.loc[rank_range != 0, "site_id"].astype(str).tolist()
        add(issues, f"Expected sensitivity rank_range 0 for every site; changed sites: {sites}")


def check_profiles(issues: list[str], rules: dict[str, Any]) -> None:
    path = p("data/outputs/profile_results.csv")
    if not path.exists():
        return
    df = pd.read_csv(path)
    if not require_columns(df, PROFILE_COLUMNS, "profile_results.csv", issues):
        return

    expected_sites = expected_set(rules, "expected_site_ids", issues)
    expected_profiles = expected_set(rules, "expected_profile_names", issues)
    actual_sites = set(df["site_id"].astype(str))
    actual_profiles = set(df["profile_name"].astype(str))

    if expected_sites and actual_sites != expected_sites:
        add(issues, f"profile_results.csv site IDs differ. Expected {sorted(expected_sites)}, got {sorted(actual_sites)}")
    if expected_profiles and actual_profiles != expected_profiles:
        add(issues, f"profile_results.csv profile names differ. Expected {sorted(expected_profiles)}, got {sorted(actual_profiles)}")
    if df[["profile_name", "site_id"]].duplicated().any():
        add(issues, "profile_results.csv has duplicate profile/site rows")

    expected_profile_count = int(rules.get("expected_profile_count", len(expected_profiles)))
    expected_sites_per_profile = int(rules.get("expected_sites_per_profile", len(expected_sites)))
    if expected_profile_count and df["profile_name"].nunique() != expected_profile_count:
        add(issues, f"profile_results.csv should contain {expected_profile_count} profiles")
    if expected_profile_count and expected_sites_per_profile and len(df) != expected_profile_count * expected_sites_per_profile:
        add(issues, f"profile_results.csv should contain {expected_profile_count * expected_sites_per_profile} rows")

    require_range(
        df,
        "profile_readiness_score",
        float(rules.get("profile_readiness_score_min", 0)),
        float(rules.get("profile_readiness_score_max", 100)),
        "profile_results.csv",
        issues,
    )

    for profile_name, group in df.groupby("profile_name", sort=False):
        ranks = numeric_series(group, "profile_rank", f"profile_results.csv profile {profile_name}", issues)
        if ranks is None:
            continue
        if sorted(ranks.astype(int).tolist()) != list(range(1, len(group) + 1)):
            add(issues, f"profile_results.csv profile {profile_name} ranks should be consecutive starting at 1")


def run_checks() -> list[str]:
    issues: list[str] = []
    rules = load_rules(issues)
    require_files(issues)
    if rules:
        check_site_results(issues, rules)
        check_quality_report(issues, rules)
        check_sensitivity(issues, rules)
        check_profiles(issues, rules)
    return issues


def run_baseline_comparison() -> None:
    completed = subprocess.run([sys.executable, "src/compare_to_baseline.py"], cwd=PROJECT_ROOT, check=False)
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
