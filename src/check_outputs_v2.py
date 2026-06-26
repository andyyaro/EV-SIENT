"""Check generated V2 model outputs.

The checker verifies that expected V2 artifacts exist, all 12 candidate sites are
represented, the README decision-map asset is synchronized, the port-sizing
scenario layer is present, the baseline comparison passed, and the deliverable
package is hash-synced with current source outputs.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REQUIRED_SITE_IDS = {
    "FFX001", "FFX002", "FFX003", "FFX004",
    "PWC001", "PWC002", "PWC003", "PWC004",
    "PWC005", "PWC006", "PWC007", "PWC008",
}
EXPECTED_SITE_COUNT = len(REQUIRED_SITE_IDS)
EXPECTED_PORT_SCENARIOS = {"base", "high_growth", "long_sessions", "short_daily_window", "peakier_demand", "combined_stress"}
EXPECTED_PACKAGE_PAYLOAD_COUNT = 35

CORE_OUTPUT_FILES = [
    Path("data/outputs/v2_site_results.csv"),
    Path("data/outputs/v2_action_matrix.md"),
    Path("data/outputs/v2_data_quality_report.csv"),
    Path("data/outputs/v2_sensitivity_summary.csv"),
    Path("data/outputs/v2_profile_results.csv"),
    Path("data/outputs/v2_profile_rank_summary.csv"),
    Path("data/outputs/v2_profile_comparison.md"),
    Path("data/outputs/v2_electrical_scenario_results.csv"),
    Path("data/outputs/v2_electrical_risk_summary.csv"),
    Path("data/outputs/v2_electrical_feasibility_report.md"),
    Path("data/outputs/v2_right_sizing_scenarios.csv"),
    Path("data/outputs/v2_right_sizing_report.md"),
    Path("data/outputs/v2_port_utilization_simulation.csv"),
    Path("data/outputs/v2_port_utilization_simulation_report.md"),
    Path("data/outputs/v2_port_sizing_scenario_results.csv"),
    Path("data/outputs/v2_port_sizing_scenario_summary.csv"),
    Path("data/outputs/v2_port_sizing_scenario_report.md"),
    Path("data/outputs/v2_right_sizing_validation.csv"),
    Path("data/outputs/v2_right_sizing_validation_report.md"),
    Path("data/outputs/v2_executive_site_summary.csv"),
    Path("data/outputs/v2_executive_site_summary.md"),
    Path("data/outputs/v2_results_interpretation.md"),
    Path("data/outputs/v2_run_summary.md"),
    Path("data/outputs/v2_workflow_success.json"),
    Path("data/outputs/v2_baseline_comparison.json"),
    Path("data/outputs/v2_baseline_comparison.md"),
    Path("data/outputs/charts/v2_readiness_score_chart.png"),
    Path("data/outputs/charts/v2_polished_readiness_score_chart.png"),
    Path("data/outputs/charts/v2_data_confidence_chart.png"),
    Path("data/outputs/charts/v2_profile_score_heatmap.png"),
    Path("data/outputs/charts/v2_profile_rank_stability_chart.png"),
    Path("data/outputs/charts/v2_site_readiness_map.png"),
    Path("data/outputs/charts/v2_site_decision_map.png"),
    Path("data/outputs/charts/v2_site_decision_map_readme.png"),
    Path("data/outputs/charts/v2_port_utilization_simulation.png"),
    Path("data/outputs/charts/v2_port_sizing_scenario_heatmap.png"),
    Path("docs/assets/charts/v2_site_decision_map_readme.png"),
]

PACKAGE_PAYLOAD_FILES = [
    Path("data/outputs/deliverable_package_v2/tables/v2_executive_site_summary.csv"),
    Path("data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md"),
    Path("data/outputs/deliverable_package_v2/tables/v2_right_sizing_validation.csv"),
    Path("data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md"),
    Path("data/outputs/deliverable_package_v2/inputs/v2_port_sizing_scenarios.csv"),
    Path("data/outputs/deliverable_package_v2/tables/v2_port_sizing_scenario_results.csv"),
    Path("data/outputs/deliverable_package_v2/tables/v2_port_sizing_scenario_summary.csv"),
    Path("data/outputs/deliverable_package_v2/reports/v2_port_sizing_scenario_report.md"),
    Path("data/outputs/deliverable_package_v2/tables/v2_site_results.csv"),
    Path("data/outputs/deliverable_package_v2/reports/v2_action_matrix.md"),
    Path("data/outputs/deliverable_package_v2/tables/v2_sensitivity_summary.csv"),
    Path("data/outputs/deliverable_package_v2/tables/v2_profile_results.csv"),
    Path("data/outputs/deliverable_package_v2/tables/v2_profile_rank_summary.csv"),
    Path("data/outputs/deliverable_package_v2/reports/v2_profile_comparison.md"),
    Path("data/outputs/deliverable_package_v2/tables/v2_right_sizing_scenarios.csv"),
    Path("data/outputs/deliverable_package_v2/reports/v2_right_sizing_report.md"),
    Path("data/outputs/deliverable_package_v2/tables/v2_port_utilization_simulation.csv"),
    Path("data/outputs/deliverable_package_v2/reports/v2_port_utilization_simulation_report.md"),
    Path("data/outputs/deliverable_package_v2/tables/v2_electrical_risk_summary.csv"),
    Path("data/outputs/deliverable_package_v2/reports/v2_electrical_feasibility_report.md"),
    Path("data/outputs/deliverable_package_v2/tables/v2_data_quality_report.csv"),
    Path("data/outputs/deliverable_package_v2/reports/v2_results_interpretation.md"),
    Path("data/outputs/deliverable_package_v2/reports/v2_run_summary.md"),
    Path("data/outputs/deliverable_package_v2/manifests/v2_baseline_comparison.json"),
    Path("data/outputs/deliverable_package_v2/reports/v2_baseline_comparison.md"),
    Path("data/outputs/deliverable_package_v2/manifests/v2_workflow_success.json"),
    Path("data/outputs/deliverable_package_v2/charts/v2_polished_readiness_score_chart.png"),
    Path("data/outputs/deliverable_package_v2/charts/v2_data_confidence_chart.png"),
    Path("data/outputs/deliverable_package_v2/charts/v2_profile_score_heatmap.png"),
    Path("data/outputs/deliverable_package_v2/charts/v2_profile_rank_stability_chart.png"),
    Path("data/outputs/deliverable_package_v2/charts/v2_site_readiness_map.png"),
    Path("data/outputs/deliverable_package_v2/charts/v2_site_decision_map.png"),
    Path("data/outputs/deliverable_package_v2/charts/v2_site_decision_map_readme.png"),
    Path("data/outputs/deliverable_package_v2/charts/v2_port_utilization_simulation.png"),
    Path("data/outputs/deliverable_package_v2/charts/v2_port_sizing_scenario_heatmap.png"),
]

PACKAGE_FILES = [
    Path("data/outputs/deliverable_package_v2/README.md"),
    Path("data/outputs/deliverable_package_v2/package_manifest.json"),
    *PACKAGE_PAYLOAD_FILES,
]

REQUIRED_BASELINE_CHECKS = {
    "site_count",
    "site_results",
    "quality_counts",
    "profile_top_sites",
    "electrical_expected",
    "right_sizing",
    "port_simulation",
    "port_sizing_scenarios",
    "right_sizing_validation",
    "executive_summary",
    "deliverable_package_manifest",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_errors(paths: list[Path]) -> list[str]:
    errors = []
    for path in paths:
        if not path.exists():
            errors.append(f"Missing expected V2 output: {path}")
        elif path.stat().st_size == 0:
            errors.append(f"Expected V2 output is empty: {path}")
    return errors


def read_csv(path: Path, label: str) -> tuple[pd.DataFrame | None, list[str]]:
    if not path.exists():
        return None, [f"Cannot check {label} because {path} is missing."]
    try:
        return pd.read_csv(path), []
    except Exception as exc:
        return None, [f"Cannot read {label}: {exc}"]


def read_json(path: Path, label: str) -> tuple[dict | None, list[str]]:
    if not path.exists():
        return None, [f"Cannot check {label} because {path} is missing."]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except Exception as exc:
        return None, [f"Cannot read {label}: {exc}"]


def check_site_table(path: Path, label: str, exact_rows: int | None = None) -> list[str]:
    table, errors = read_csv(path, label)
    if table is None:
        return errors
    if "site_id" not in table.columns:
        return [f"{label} is missing site_id."]
    found = set(table["site_id"].astype(str))
    missing = sorted(REQUIRED_SITE_IDS - found)
    if missing:
        errors.append(f"{label} is missing expected site IDs: {missing}")
    if exact_rows is not None and len(table) != exact_rows:
        errors.append(f"{label} has {len(table)} rows; expected {exact_rows} rows.")
    elif len(table) < EXPECTED_SITE_COUNT:
        errors.append(f"{label} has {len(table)} rows; expected at least {EXPECTED_SITE_COUNT} rows.")
    return errors


def check_chart_sync() -> list[str]:
    source = Path("data/outputs/charts/v2_site_decision_map_readme.png")
    destination = Path("docs/assets/charts/v2_site_decision_map_readme.png")
    if not source.exists() or not destination.exists():
        return [f"Cannot check README GIS decision map asset sync because one path is missing: {source} -> {destination}"]
    if sha256_file(source) != sha256_file(destination):
        return [f"README GIS decision map asset is stale: {destination} does not match {source}"]
    return []


def check_port_sizing_scenarios() -> list[str]:
    results, errors = read_csv(Path("data/outputs/v2_port_sizing_scenario_results.csv"), "V2 port-sizing scenario results")
    summary, summary_errors = read_csv(Path("data/outputs/v2_port_sizing_scenario_summary.csv"), "V2 port-sizing scenario summary")
    errors.extend(summary_errors)
    if results is None or summary is None:
        return errors
    required = {
        "scenario_name", "site_id", "model_rank", "ports_now", "future_ready_capacity",
        "scenario_min_ports_current", "scenario_min_ports_2035_high",
        "scenario_min_ports_2050_high", "current_alignment", "future_capacity_alignment",
        "future_capacity_gap",
    }
    missing_columns = sorted(required - set(results.columns))
    if missing_columns:
        errors.append(f"v2_port_sizing_scenario_results.csv is missing columns: {missing_columns}")
    found_scenarios = set(results["scenario_name"].astype(str)) if "scenario_name" in results.columns else set()
    if found_scenarios != EXPECTED_PORT_SCENARIOS:
        errors.append(f"v2_port_sizing_scenario_results.csv scenario set changed: {sorted(found_scenarios)}")
    expected_rows = EXPECTED_SITE_COUNT * len(EXPECTED_PORT_SCENARIOS)
    if len(results) != expected_rows:
        errors.append(f"v2_port_sizing_scenario_results.csv has {len(results)} rows; expected {expected_rows} rows.")
    if len(summary) != len(EXPECTED_PORT_SCENARIOS):
        errors.append(f"v2_port_sizing_scenario_summary.csv has {len(summary)} rows; expected {len(EXPECTED_PORT_SCENARIOS)} rows.")
    errors.extend(check_site_table(Path("data/outputs/v2_port_sizing_scenario_results.csv"), "v2_port_sizing_scenario_results.csv"))
    return errors


def check_baseline_comparison() -> list[str]:
    data, errors = read_json(Path("data/outputs/v2_baseline_comparison.json"), "V2 baseline comparison")
    if data is None:
        return errors
    if data.get("status") != "pass":
        errors.append(f"v2_baseline_comparison.json status is not pass: {data.get('status')}")
    checks = data.get("checks", [])
    failed = [check.get("check") for check in checks if check.get("status") != "pass"]
    if failed:
        errors.append(f"v2_baseline_comparison.json has failed checks: {failed}")
    found = {str(check.get("check", "")) for check in checks}
    missing = sorted(REQUIRED_BASELINE_CHECKS - found)
    if missing:
        errors.append(f"v2_baseline_comparison.json is missing required checks: {missing}")
    return errors


def check_workflow_manifest() -> list[str]:
    data, errors = read_json(Path("data/outputs/v2_workflow_success.json"), "V2 workflow manifest")
    if data is None:
        return errors
    if data.get("workflow") != "v2_expansion_planning":
        errors.append("v2_workflow_success.json has the wrong workflow name.")
    if data.get("status") != "success":
        errors.append(f"v2_workflow_success.json status is not success: {data.get('status')}")
    if int(data.get("site_count", 0)) < EXPECTED_SITE_COUNT:
        errors.append(f"v2_workflow_success.json site_count is lower than expected: {data.get('site_count')}")
    if data.get("missing_or_empty_outputs"):
        errors.append("v2_workflow_success.json reports missing or empty outputs.")
    return errors


def check_package_manifest() -> list[str]:
    manifest_path = Path("data/outputs/deliverable_package_v2/package_manifest.json")
    data, errors = read_json(manifest_path, "deliverable package manifest")
    if data is None:
        return errors
    if data.get("package") != "v2_deliverable_package":
        errors.append("deliverable package manifest has the wrong package name.")
    if data.get("status") != "complete":
        errors.append(f"deliverable package manifest status is not complete: {data.get('status')}")
    if data.get("clean_rebuild") is not True:
        errors.append("deliverable package was not created as a clean rebuild.")
    if data.get("previous_package_removed") is not True:
        errors.append("deliverable package manifest does not confirm the previous package was removed.")
    for field in ["expected_count", "copied_count", "synced_count"]:
        if int(data.get(field, -1)) != EXPECTED_PACKAGE_PAYLOAD_COUNT:
            errors.append(f"deliverable package {field} is {data.get(field)}; expected {EXPECTED_PACKAGE_PAYLOAD_COUNT}.")
    if data.get("missing_or_empty_sources"):
        errors.append("deliverable package manifest reports missing or empty sources.")
    if data.get("out_of_sync_destinations"):
        errors.append("deliverable package manifest reports out-of-sync copied files.")

    expected_destinations = {str(path) for path in PACKAGE_PAYLOAD_FILES}
    records = data.get("files", [])
    copied_destinations = {str(record.get("destination", "")) for record in records if record.get("copied")}
    missing_destinations = sorted(expected_destinations - copied_destinations)
    if missing_destinations:
        errors.append(f"deliverable package manifest is missing copied destinations: {missing_destinations}")

    for record in records:
        if not record.get("copied"):
            continue
        source = Path(str(record.get("source", "")))
        destination = Path(str(record.get("destination", "")))
        if not source.exists() or not destination.exists():
            errors.append(f"deliverable package sync check missing path: {source} -> {destination}")
            continue
        source_hash = sha256_file(source)
        destination_hash = sha256_file(destination)
        if source_hash != destination_hash:
            errors.append(f"deliverable package copy is stale: {destination} does not match {source}")
        if record.get("source_sha256") and record.get("source_sha256") != source_hash:
            errors.append(f"deliverable package manifest source hash is stale for {source}")
        if record.get("destination_sha256") and record.get("destination_sha256") != destination_hash:
            errors.append(f"deliverable package manifest destination hash is stale for {destination}")
        if record.get("in_sync") is not True:
            errors.append(f"deliverable package manifest marks file out of sync: {destination}")
    return errors


def main() -> None:
    print("V2 OUTPUT CHECK")
    print("---------------")
    errors: list[str] = []
    errors.extend(file_errors(CORE_OUTPUT_FILES + PACKAGE_FILES))
    errors.extend(check_site_table(Path("data/outputs/v2_site_results.csv"), "v2_site_results.csv", exact_rows=EXPECTED_SITE_COUNT))
    errors.extend(check_site_table(Path("data/outputs/v2_right_sizing_scenarios.csv"), "v2_right_sizing_scenarios.csv", exact_rows=EXPECTED_SITE_COUNT))
    errors.extend(check_site_table(Path("data/outputs/v2_right_sizing_validation.csv"), "v2_right_sizing_validation.csv", exact_rows=EXPECTED_SITE_COUNT))
    errors.extend(check_site_table(Path("data/outputs/v2_executive_site_summary.csv"), "v2_executive_site_summary.csv", exact_rows=EXPECTED_SITE_COUNT))
    errors.extend(check_port_sizing_scenarios())
    errors.extend(check_chart_sync())
    errors.extend(check_baseline_comparison())
    errors.extend(check_workflow_manifest())
    errors.extend(check_package_manifest())

    if errors:
        print("Status: FAILED")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    print("Status: PASSED")
    print("All expected V2 outputs are present, all 12 V2 candidate sites are represented, the port-sizing scenario analysis is present, the README decision-map asset is synced, baseline checks cover the new V2 layers, and the deliverable package is hash-synced with current source outputs.")


if __name__ == "__main__":
    main()
