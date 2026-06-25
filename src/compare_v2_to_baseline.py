"""Compare current V2 outputs against a saved V2 baseline snapshot.

This script is a regression guard for the V2 prototype. It helps detect
unintentional changes to ranking, scores, port recommendations, electrical-risk
scenario outputs, and right-sizing scenario outputs.

Run after the V2 workflow:

    python src/compare_v2_to_baseline.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_BASELINE = "data/baselines/v2_baseline_snapshot.json"
DEFAULT_RESULTS = "data/outputs/v2_site_results.csv"
DEFAULT_QUALITY = "data/outputs/v2_data_quality_report.csv"
DEFAULT_PROFILE_RESULTS = "data/outputs/v2_profile_results.csv"
DEFAULT_ELECTRICAL_SUMMARY = "data/outputs/v2_electrical_risk_summary.csv"
DEFAULT_RIGHT_SIZING = "data/outputs/v2_right_sizing_scenarios.csv"
DEFAULT_JSON_OUTPUT = "data/outputs/v2_baseline_comparison.json"
DEFAULT_MD_OUTPUT = "data/outputs/v2_baseline_comparison.md"


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required output file not found: {path}")
    return pd.read_csv(path)


def load_baseline(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Baseline file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def to_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int | None:
    number = to_float(value)
    if number is None:
        return None
    return int(round(number))


def add_result(results: list[dict[str, Any]], check_name: str, status: str, message: str) -> None:
    results.append({"check": check_name, "status": status, "message": message})


def compare_quality_counts(baseline: dict[str, Any], quality: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    expected = baseline.get("quality_counts", {})
    if quality.empty or "severity" not in quality.columns:
        add_result(checks, "quality_counts", "fail", "Quality report missing or lacks severity column.")
        return

    actual_counts = quality["severity"].value_counts().to_dict()
    actual = {level: int(actual_counts.get(level, 0)) for level in ["ERROR", "WARNING", "REVIEW", "INFO"]}
    if actual == expected:
        add_result(checks, "quality_counts", "pass", f"Quality counts match baseline: {actual}.")
    else:
        add_result(checks, "quality_counts", "fail", f"Quality counts changed. Expected {expected}, got {actual}.")


def compare_profile_top_sites(baseline: dict[str, Any], profile_results: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    expected = baseline.get("profile_top_sites", {})
    required = {"profile_name", "profile_rank", "site_id"}
    if profile_results.empty or not required.issubset(profile_results.columns):
        add_result(checks, "profile_top_sites", "fail", "Profile results missing required columns.")
        return

    top_by_profile = (
        profile_results.sort_values(["profile_name", "profile_rank"])
        .groupby("profile_name", as_index=False)
        .first()
    )
    actual = dict(zip(top_by_profile["profile_name"].astype(str), top_by_profile["site_id"].astype(str)))
    if actual == expected:
        add_result(checks, "profile_top_sites", "pass", f"Profile top sites match baseline: {actual}.")
    else:
        add_result(checks, "profile_top_sites", "fail", f"Profile top sites changed. Expected {expected}, got {actual}.")


def compare_site_results(baseline: dict[str, Any], results: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    expected_rows = baseline.get("site_results", [])
    tolerance = float(baseline.get("score_tolerance", 0.2))
    expected_count = int(baseline.get("expected_site_count", len(expected_rows)))

    if len(results) != expected_count:
        add_result(checks, "site_count", "fail", f"Expected {expected_count} sites, got {len(results)}.")
    else:
        add_result(checks, "site_count", "pass", f"Site count matches baseline: {expected_count}.")

    if "site_id" not in results.columns:
        add_result(checks, "site_results", "fail", "Results file has no site_id column.")
        return

    actual_by_id = results.set_index("site_id", drop=False)
    failed = []
    for expected in expected_rows:
        site_id = expected["site_id"]
        if site_id not in actual_by_id.index:
            failed.append(f"{site_id}: missing from current results")
            continue
        actual = actual_by_id.loc[site_id]
        for field in ["model_rank", "recommended_ports_now", "recommended_ports_2035", "recommended_ports_2050"]:
            if to_int(actual.get(field)) != int(expected[field]):
                failed.append(f"{site_id}: {field} expected {expected[field]}, got {actual.get(field)}")
        score = to_float(actual.get("readiness_score"))
        if score is None or abs(score - float(expected["readiness_score"])) > tolerance:
            failed.append(f"{site_id}: readiness_score expected {expected['readiness_score']}±{tolerance}, got {actual.get('readiness_score')}")
        if str(actual.get("recommendation_tier", "")) != str(expected["recommendation_tier"]):
            failed.append(f"{site_id}: recommendation_tier changed")

    if failed:
        add_result(checks, "site_results", "fail", "; ".join(failed[:12]) + (" ..." if len(failed) > 12 else ""))
    else:
        add_result(checks, "site_results", "pass", "Ranks, readiness scores, tiers, and model port recommendations match baseline.")


def compare_electrical(baseline: dict[str, Any], electrical: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    expected_rows = baseline.get("electrical_expected", [])
    tolerance = float(baseline.get("score_tolerance", 0.2))
    if electrical.empty or "site_id" not in electrical.columns:
        add_result(checks, "electrical_expected", "fail", "Electrical summary missing or lacks site_id.")
        return

    actual_by_id = electrical.set_index("site_id", drop=False)
    failed = []
    for expected in expected_rows:
        site_id = expected["site_id"]
        if site_id not in actual_by_id.index:
            failed.append(f"{site_id}: missing from electrical summary")
            continue
        actual = actual_by_id.loc[site_id]
        if to_int(actual.get("expected_rank")) != int(expected["expected_rank"]):
            failed.append(f"{site_id}: expected_rank expected {expected['expected_rank']}, got {actual.get('expected_rank')}")
        score = to_float(actual.get("expected_score"))
        if score is None or abs(score - float(expected["expected_score"])) > tolerance:
            failed.append(f"{site_id}: expected_score expected {expected['expected_score']}±{tolerance}, got {actual.get('expected_score')}")
        if str(actual.get("electrical_risk_level", "")) != str(expected["electrical_risk_level"]):
            failed.append(f"{site_id}: electrical_risk_level expected {expected['electrical_risk_level']}, got {actual.get('electrical_risk_level')}")

    if failed:
        add_result(checks, "electrical_expected", "fail", "; ".join(failed[:12]) + (" ..." if len(failed) > 12 else ""))
    else:
        add_result(checks, "electrical_expected", "pass", "Expected electrical-case ranks, scores, and risk levels match baseline.")


def compare_right_sizing(baseline: dict[str, Any], right_sizing: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    expected_rows = baseline.get("right_sizing", [])
    if right_sizing.empty or "site_id" not in right_sizing.columns:
        add_result(checks, "right_sizing", "fail", "Right-sizing output missing or lacks site_id.")
        return

    actual_by_id = right_sizing.set_index("site_id", drop=False)
    failed = []
    fields = [
        "ports_now",
        "ports_2035_base",
        "ports_2035_high",
        "ports_2050_base",
        "ports_2050_high",
        "future_ready_capacity",
    ]
    for expected in expected_rows:
        site_id = expected["site_id"]
        if site_id not in actual_by_id.index:
            failed.append(f"{site_id}: missing from right-sizing output")
            continue
        actual = actual_by_id.loc[site_id]
        for field in fields:
            if to_int(actual.get(field)) != int(expected[field]):
                failed.append(f"{site_id}: {field} expected {expected[field]}, got {actual.get(field)}")
        if str(actual.get("expansion_strategy", "")) != str(expected["expansion_strategy"]):
            failed.append(f"{site_id}: expansion_strategy expected {expected['expansion_strategy']}, got {actual.get('expansion_strategy')}")

    if failed:
        add_result(checks, "right_sizing", "fail", "; ".join(failed[:12]) + (" ..." if len(failed) > 12 else ""))
    else:
        add_result(checks, "right_sizing", "pass", "Right-sizing ports, future-ready capacity, and strategies match baseline.")


def build_markdown_report(baseline: dict[str, Any], checks: list[dict[str, Any]], status: str) -> str:
    rows = ["| Check | Status | Message |", "|---|---|---|"]
    for check in checks:
        rows.append(f"| {check['check']} | {check['status']} | {str(check['message']).replace('|', '/')} |")

    return "\n".join(
        [
            "# V2 Baseline Comparison Report",
            "",
            f"Baseline: `{baseline.get('baseline_name', 'unknown')}`",
            f"Status: **{status.upper()}**",
            "",
            "This report compares the current V2 outputs against the saved V2 baseline snapshot.",
            "It is intended to catch accidental model, ranking, scoring, or output-structure changes.",
            "",
            "## Checks",
            "",
            *rows,
            "",
            "## Interpretation",
            "",
            "- `pass` means the current output matches the saved baseline for that check.",
            "- `fail` means a difference was found and should be reviewed before treating the run as stable.",
            "- This does not prove the model is correct; it proves the current run is consistent with the saved baseline.",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare current V2 outputs against a saved V2 baseline snapshot.")
    parser.add_argument("--baseline", default=DEFAULT_BASELINE, help="Baseline JSON snapshot.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Current V2 site results CSV.")
    parser.add_argument("--quality", default=DEFAULT_QUALITY, help="Current V2 data quality CSV.")
    parser.add_argument("--profile-results", default=DEFAULT_PROFILE_RESULTS, help="Current V2 profile results CSV.")
    parser.add_argument("--electrical-summary", default=DEFAULT_ELECTRICAL_SUMMARY, help="Current V2 electrical risk summary CSV.")
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING, help="Current V2 right-sizing CSV.")
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT, help="Baseline comparison JSON output.")
    parser.add_argument("--md-output", default=DEFAULT_MD_OUTPUT, help="Baseline comparison Markdown output.")
    parser.add_argument("--no-fail", action="store_true", help="Write reports but do not exit with failure when differences are found.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline = load_baseline(Path(args.baseline))
    results = read_csv(Path(args.results))
    quality = read_csv(Path(args.quality))
    profile_results = read_csv(Path(args.profile_results))
    electrical = read_csv(Path(args.electrical_summary))
    right_sizing = read_csv(Path(args.right_sizing))

    checks: list[dict[str, Any]] = []
    compare_site_results(baseline, results, checks)
    compare_quality_counts(baseline, quality, checks)
    compare_profile_top_sites(baseline, profile_results, checks)
    compare_electrical(baseline, electrical, checks)
    compare_right_sizing(baseline, right_sizing, checks)

    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    json_payload = {"status": status, "baseline_name": baseline.get("baseline_name"), "checks": checks}

    json_output = Path(args.json_output)
    md_output = Path(args.md_output)
    ensure_parent_dir(json_output)
    ensure_parent_dir(md_output)
    json_output.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    md_output.write_text(build_markdown_report(baseline, checks, status), encoding="utf-8")

    print("V2 BASELINE COMPARISON")
    print("----------------------")
    print(f"Baseline: {args.baseline}")
    print(f"Status: {status.upper()}")
    print(f"JSON report: {json_output}")
    print(f"Markdown report: {md_output}")
    for check in checks:
        print(f"- {check['status'].upper()} {check['check']}: {check['message']}")

    if status != "pass" and not args.no_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
