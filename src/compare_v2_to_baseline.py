"""Compare current V2 outputs against a saved V2 baseline snapshot."""

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
DEFAULT_PORT_SIMULATION = "data/outputs/v2_port_utilization_simulation.csv"
DEFAULT_RIGHT_SIZING_VALIDATION = "data/outputs/v2_right_sizing_validation.csv"
DEFAULT_EXECUTIVE_SUMMARY = "data/outputs/v2_executive_site_summary.csv"
DEFAULT_JSON_OUTPUT = "data/outputs/v2_baseline_comparison.json"
DEFAULT_MD_OUTPUT = "data/outputs/v2_baseline_comparison.md"


def read_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Required output file not found: {path}")
    return pd.read_csv(path)


def read_json(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Required JSON file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def as_int(value: Any) -> int | None:
    try:
        if pd.isna(value):
            return None
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def as_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def add(checks: list[dict[str, Any]], name: str, status: str, message: str) -> None:
    checks.append({"check": name, "status": status, "message": message})


def missing_columns(table: pd.DataFrame, required: list[str] | set[str]) -> list[str]:
    return sorted(set(required) - set(table.columns))


def choose_min_ports(group: pd.DataFrame) -> int | None:
    if group.empty:
        return None
    usable = group[group["capacity_status"] != "underbuilt"]
    if not usable.empty:
        best = usable.sort_values("port_count").iloc[0]
    else:
        best = group.sort_values(["estimated_wait_min", "port_count"], ascending=[True, False]).iloc[0]
    return int(best["port_count"])


def compare_quality(baseline: dict[str, Any], quality: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    if "severity" not in quality.columns:
        add(checks, "quality_counts", "fail", "Quality report missing severity column.")
        return
    counts = quality["severity"].value_counts().to_dict()
    actual = {level: int(counts.get(level, 0)) for level in ["ERROR", "WARNING", "REVIEW", "INFO"]}
    expected = baseline.get("quality_counts", {})
    add(checks, "quality_counts", "pass" if actual == expected else "fail", f"Expected {expected}, got {actual}.")


def compare_profiles(baseline: dict[str, Any], profiles: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    required = {"profile_name", "profile_rank", "site_id"}
    if missing_columns(profiles, required):
        add(checks, "profile_top_sites", "fail", "Profile results missing required columns.")
        return
    top = profiles.sort_values(["profile_name", "profile_rank"]).groupby("profile_name", as_index=False).first()
    actual = dict(zip(top["profile_name"].astype(str), top["site_id"].astype(str)))
    expected = baseline.get("profile_top_sites", {})
    add(checks, "profile_top_sites", "pass" if actual == expected else "fail", f"Expected {expected}, got {actual}.")


def compare_site_results(baseline: dict[str, Any], results: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    expected_rows = baseline.get("site_results", [])
    expected_count = int(baseline.get("expected_site_count", len(expected_rows)))
    tolerance = float(baseline.get("score_tolerance", 0.2))
    add(checks, "site_count", "pass" if len(results) == expected_count else "fail", f"Expected {expected_count} sites, got {len(results)}.")
    if "site_id" not in results.columns:
        add(checks, "site_results", "fail", "Results missing site_id.")
        return
    by_id = results.set_index("site_id", drop=False)
    failures = []
    for expected in expected_rows:
        site_id = expected["site_id"]
        if site_id not in by_id.index:
            failures.append(f"{site_id}: missing")
            continue
        actual = by_id.loc[site_id]
        for field in ["model_rank", "recommended_ports_now", "recommended_ports_2035", "recommended_ports_2050"]:
            if as_int(actual.get(field)) != int(expected[field]):
                failures.append(f"{site_id}: {field} expected {expected[field]}, got {actual.get(field)}")
        score = as_float(actual.get("readiness_score"))
        if score is None or abs(score - float(expected["readiness_score"])) > tolerance:
            failures.append(f"{site_id}: readiness_score expected {expected['readiness_score']}, got {actual.get('readiness_score')}")
        if str(actual.get("recommendation_tier", "")) != str(expected["recommendation_tier"]):
            failures.append(f"{site_id}: recommendation_tier changed")
    add(checks, "site_results", "fail" if failures else "pass", "; ".join(failures[:12]) if failures else "Site ranks, scores, tiers, and port recommendations match baseline.")


def compare_electrical(baseline: dict[str, Any], electrical: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    expected_rows = baseline.get("electrical_expected", [])
    tolerance = float(baseline.get("score_tolerance", 0.2))
    if "site_id" not in electrical.columns:
        add(checks, "electrical_expected", "fail", "Electrical summary missing site_id.")
        return
    by_id = electrical.set_index("site_id", drop=False)
    failures = []
    for expected in expected_rows:
        site_id = expected["site_id"]
        if site_id not in by_id.index:
            failures.append(f"{site_id}: missing")
            continue
        actual = by_id.loc[site_id]
        if as_int(actual.get("expected_rank")) != int(expected["expected_rank"]):
            failures.append(f"{site_id}: expected_rank changed")
        score = as_float(actual.get("expected_score"))
        if score is None or abs(score - float(expected["expected_score"])) > tolerance:
            failures.append(f"{site_id}: expected_score changed")
        if str(actual.get("electrical_risk_level", "")) != str(expected["electrical_risk_level"]):
            failures.append(f"{site_id}: electrical_risk_level changed")
    add(checks, "electrical_expected", "fail" if failures else "pass", "; ".join(failures[:12]) if failures else "Electrical expected-case outputs match baseline.")


def compare_right_sizing(baseline: dict[str, Any], sizing: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    if "site_id" not in sizing.columns:
        add(checks, "right_sizing", "fail", "Right-sizing output missing site_id.")
        return
    by_id = sizing.set_index("site_id", drop=False)
    fields = ["ports_now", "ports_2035_base", "ports_2035_high", "ports_2050_base", "ports_2050_high", "future_ready_capacity"]
    failures = []
    for expected in baseline.get("right_sizing", []):
        site_id = expected["site_id"]
        if site_id not in by_id.index:
            failures.append(f"{site_id}: missing")
            continue
        actual = by_id.loc[site_id]
        for field in fields:
            if as_int(actual.get(field)) != int(expected[field]):
                failures.append(f"{site_id}: {field} changed")
        if str(actual.get("expansion_strategy", "")) != str(expected["expansion_strategy"]):
            failures.append(f"{site_id}: expansion_strategy changed")
    add(checks, "right_sizing", "fail" if failures else "pass", "; ".join(failures[:12]) if failures else "Right-sizing outputs match baseline.")


def compare_port_simulation(baseline: dict[str, Any], simulation: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    expected = baseline.get("port_simulation", {})
    required = {"site_id", "demand_case", "port_count", "avg_charge_hours", "charging_window_hours", "peak_factor", "capacity_status", "estimated_wait_min"}
    missing = missing_columns(simulation, required)
    if missing:
        add(checks, "port_simulation", "fail", f"Missing columns: {missing}.")
        return
    failures = []
    if expected.get("row_count") is not None and len(simulation) != int(expected["row_count"]):
        failures.append(f"row_count expected {expected['row_count']}, got {len(simulation)}")
    if expected.get("demand_cases") and set(simulation["demand_case"].astype(str)) != set(expected["demand_cases"]):
        failures.append("demand_cases changed")
    if expected.get("port_options"):
        actual_ports = sorted(int(x) for x in pd.to_numeric(simulation["port_count"], errors="coerce").dropna().unique())
        if actual_ports != [int(x) for x in expected["port_options"]]:
            failures.append(f"port_options expected {expected['port_options']}, got {actual_ports}")
    for field in ["avg_charge_hours", "charging_window_hours", "peak_factor"]:
        if field in expected:
            actual_values = sorted(float(x) for x in pd.to_numeric(simulation[field], errors="coerce").dropna().unique())
            if actual_values != [float(expected[field])]:
                failures.append(f"{field} expected {expected[field]}, got {actual_values}")
    current = simulation[simulation["demand_case"] == "current"]
    for site_id, expected_ports in expected.get("current_min_ports_by_site", {}).items():
        actual_ports = choose_min_ports(current[current["site_id"].astype(str) == str(site_id)])
        if actual_ports != int(expected_ports):
            failures.append(f"{site_id}: current min ports expected {expected_ports}, got {actual_ports}")
    add(checks, "port_simulation", "fail" if failures else "pass", "; ".join(failures[:12]) if failures else "Port simulation guardrails match baseline.")


def compare_validation(baseline: dict[str, Any], validation: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    expected = baseline.get("right_sizing_validation", {})
    missing = missing_columns(validation, expected.get("required_columns", []))
    if missing:
        add(checks, "right_sizing_validation", "fail", f"Missing columns: {missing}.")
        return
    failures = []
    if expected.get("row_count") is not None and len(validation) != int(expected["row_count"]):
        failures.append(f"row_count expected {expected['row_count']}, got {len(validation)}")
    by_id = validation.set_index("site_id", drop=False)
    for site_id, expected_value in expected.get("current_alignment_by_site", {}).items():
        actual = str(by_id.loc[site_id].get("current_alignment", "")) if site_id in by_id.index else "missing"
        if actual != str(expected_value):
            failures.append(f"{site_id}: current_alignment expected {expected_value}, got {actual}")
    allowed_future = set(expected.get("future_alignment_allowed_values", []))
    if allowed_future:
        invalid = sorted(set(validation["future_alignment"].dropna().astype(str)) - allowed_future)
        if invalid:
            failures.append(f"future_alignment unexpected values: {invalid}")
    for col in ["current_alignment", "future_alignment"]:
        for prefix in expected.get("forbidden_alignment_prefixes", []):
            bad = sorted({value for value in validation[col].dropna().astype(str) if value.startswith(prefix)})
            if bad:
                failures.append(f"{col} contains forbidden values: {bad}")
    allowed_support = set(expected.get("simulation_supported_strategy_allowed_values", []))
    if allowed_support:
        invalid = sorted(set(validation["simulation_supported_strategy"].dropna().astype(str)) - allowed_support)
        if invalid:
            failures.append(f"simulation_supported_strategy unexpected values: {invalid}")
    add(checks, "right_sizing_validation", "fail" if failures else "pass", "; ".join(failures[:12]) if failures else "Right-sizing validation guardrails match baseline.")


def compare_executive(baseline: dict[str, Any], executive: pd.DataFrame, checks: list[dict[str, Any]]) -> None:
    expected = baseline.get("executive_summary", {})
    missing = missing_columns(executive, expected.get("required_columns", []))
    if missing:
        add(checks, "executive_summary", "fail", f"Missing columns: {missing}.")
        return
    failures = []
    if expected.get("row_count") is not None and len(executive) != int(expected["row_count"]):
        failures.append(f"row_count expected {expected['row_count']}, got {len(executive)}")
    ranked = executive.copy()
    ranked["model_rank"] = pd.to_numeric(ranked["model_rank"], errors="coerce")
    ranked = ranked.sort_values("model_rank")
    if expected.get("top_site_id") and str(ranked.iloc[0]["site_id"]) != str(expected["top_site_id"]):
        failures.append(f"top_site_id expected {expected['top_site_id']}, got {ranked.iloc[0]['site_id']}")
    for field in expected.get("non_empty_columns", []):
        empty_count = int(executive[field].isna().sum() + (executive[field].astype(str).str.strip() == "").sum())
        if empty_count:
            failures.append(f"{field} has {empty_count} empty rows")
    by_id = executive.set_index("site_id", drop=False)
    for site_id, expected_value in expected.get("current_alignment_by_site", {}).items():
        actual = str(by_id.loc[site_id].get("current_alignment", "")) if site_id in by_id.index else "missing"
        if actual != str(expected_value):
            failures.append(f"{site_id}: executive current_alignment expected {expected_value}, got {actual}")
    add(checks, "executive_summary", "fail" if failures else "pass", "; ".join(failures[:12]) if failures else "Executive summary guardrails match baseline.")


def compare_package_manifest(baseline: dict[str, Any], manifest: dict[str, Any] | None, checks: list[dict[str, Any]]) -> None:
    if manifest is None:
        return
    expected = baseline.get("deliverable_package_manifest", {})
    failures = []
    for field in ["package", "status", "expected_count", "copied_count", "synced_count", "clean_rebuild"]:
        if field in expected and manifest.get(field) != expected[field]:
            failures.append(f"{field} expected {expected[field]}, got {manifest.get(field)}")
    if expected.get("missing_or_empty_sources", []) == [] and manifest.get("missing_or_empty_sources"):
        failures.append("missing_or_empty_sources is not empty")
    if expected.get("out_of_sync_destinations", []) == [] and manifest.get("out_of_sync_destinations"):
        failures.append("out_of_sync_destinations is not empty")
    if manifest.get("expected_count") != manifest.get("copied_count"):
        failures.append("copied_count does not equal expected_count")
    if manifest.get("expected_count") != manifest.get("synced_count"):
        failures.append("synced_count does not equal expected_count")
    required_destinations = set(expected.get("required_destinations", []))
    copied_destinations = {str(item.get("destination", "")) for item in manifest.get("files", []) if item.get("copied")}
    missing = sorted(required_destinations - copied_destinations)
    if missing:
        failures.append(f"missing copied destinations: {missing}")
    stale = sorted(str(item.get("destination", "")) for item in manifest.get("files", []) if item.get("copied") and item.get("in_sync") is not True)
    if stale:
        failures.append(f"manifest has copied files not marked in_sync: {stale[:5]}")
    add(checks, "deliverable_package_manifest", "fail" if failures else "pass", "; ".join(failures[:12]) if failures else "Deliverable package manifest matches baseline and all copied files are synced.")


def build_markdown(baseline: dict[str, Any], checks: list[dict[str, Any]], status: str) -> str:
    rows = ["| Check | Status | Message |", "|---|---|---|"]
    rows += [f"| {item['check']} | {item['status']} | {str(item['message']).replace('|', '/')} |" for item in checks]
    return "\n".join([
        "# V2 Baseline Comparison Report",
        "",
        f"Baseline: `{baseline.get('baseline_name', 'unknown')}`",
        f"Status: **{status.upper()}**",
        "",
        "This report compares the current V2 outputs against the saved V2 baseline snapshot.",
        "It catches accidental ranking, scoring, simulation, validation, executive-summary, GIS-map package, and package-manifest changes.",
        "",
        "## Checks",
        "",
        *rows,
        "",
        "## Interpretation",
        "",
        "- `pass` means the current output matches the saved baseline for that check.",
        "- `fail` means a difference was found and should be reviewed before treating the run as stable.",
        "",
    ])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default=DEFAULT_BASELINE)
    parser.add_argument("--results", default=DEFAULT_RESULTS)
    parser.add_argument("--quality", default=DEFAULT_QUALITY)
    parser.add_argument("--profile-results", default=DEFAULT_PROFILE_RESULTS)
    parser.add_argument("--electrical-summary", default=DEFAULT_ELECTRICAL_SUMMARY)
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING)
    parser.add_argument("--port-simulation", default=DEFAULT_PORT_SIMULATION)
    parser.add_argument("--right-sizing-validation", default=DEFAULT_RIGHT_SIZING_VALIDATION)
    parser.add_argument("--executive-summary", default=DEFAULT_EXECUTIVE_SUMMARY)
    parser.add_argument("--deliverable-manifest", default=None)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--md-output", default=DEFAULT_MD_OUTPUT)
    parser.add_argument("--no-fail", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline = read_json(args.baseline)
    checks: list[dict[str, Any]] = []
    compare_site_results(baseline, read_csv(args.results), checks)
    compare_quality(baseline, read_csv(args.quality), checks)
    compare_profiles(baseline, read_csv(args.profile_results), checks)
    compare_electrical(baseline, read_csv(args.electrical_summary), checks)
    compare_right_sizing(baseline, read_csv(args.right_sizing), checks)
    compare_port_simulation(baseline, read_csv(args.port_simulation), checks)
    compare_validation(baseline, read_csv(args.right_sizing_validation), checks)
    compare_executive(baseline, read_csv(args.executive_summary), checks)
    compare_package_manifest(baseline, read_json(args.deliverable_manifest) if args.deliverable_manifest else None, checks)

    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    payload = {"status": status, "baseline_name": baseline.get("baseline_name"), "checks": checks}
    Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.md_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    Path(args.md_output).write_text(build_markdown(baseline, checks, status), encoding="utf-8")

    print("V2 BASELINE COMPARISON")
    print("----------------------")
    print(f"Baseline: {args.baseline}")
    print(f"Status: {status.upper()}")
    print(f"JSON report: {args.json_output}")
    print(f"Markdown report: {args.md_output}")
    for item in checks:
        print(f"- {item['status'].upper()} {item['check']}: {item['message']}")

    if status != "pass" and not args.no_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
