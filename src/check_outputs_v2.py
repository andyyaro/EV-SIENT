"""Check generated V2 model outputs.

This checker is intentionally stricter than a simple file-exists test. It verifies
that the core V2 outputs contain all 12 candidate sites, that the newer
simulation / validation / executive-summary layers are present, that GIS decision
map copies stay synchronized, and that the deliverable package manifest matches
current source outputs by SHA-256 hash.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

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
    Path("docs/assets/charts/v2_site_decision_map_readme.png"),
]

PACKAGE_FILES = [
    Path("data/outputs/deliverable_package_v2/README.md"),
    Path("data/outputs/deliverable_package_v2/package_manifest.json"),
    Path("data/outputs/deliverable_package_v2/tables/v2_executive_site_summary.csv"),
    Path("data/outputs/deliverable_package_v2/reports/v2_executive_site_summary.md"),
    Path("data/outputs/deliverable_package_v2/tables/v2_right_sizing_validation.csv"),
    Path("data/outputs/deliverable_package_v2/reports/v2_right_sizing_validation_report.md"),
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
]

EXPECTED_FILES = CORE_OUTPUT_FILES + PACKAGE_FILES
EXPECTED_PACKAGE_PAYLOAD_COUNT = len(PACKAGE_FILES) - 2  # Excludes package README and manifest generated by the builder.

REQUIRED_RESULT_COLUMNS = [
    "model_rank", "site_id", "site_name", "readiness_score", "data_confidence_score",
    "data_confidence_level", "recommendation_tier", "recommended_ports_now",
    "recommended_ports_2035", "recommended_ports_2050", "action_label",
]

REQUIRED_ELECTRICAL_COLUMNS = [
    "site_id", "site_name", "base_rank", "electrical_risk_level", "expected_rank",
    "conservative_rank", "expected_score", "conservative_score",
]

REQUIRED_RIGHT_SIZING_COLUMNS = [
    "site_id", "site_name", "model_rank", "ports_now", "ports_2035_base",
    "ports_2035_high", "ports_2050_base", "ports_2050_high",
    "future_ready_capacity", "expansion_strategy",
]

REQUIRED_PORT_SIM_COLUMNS = [
    "site_id", "site_name", "model_rank", "demand_case", "sessions_day",
    "port_count", "utilization_pct", "peak_demand_ratio", "estimated_wait_min",
    "queue_risk_level", "capacity_status",
]

REQUIRED_RIGHT_SIZING_VALIDATION_COLUMNS = [
    "site_id", "site_name", "ports_now", "sim_min_ports_current", "current_alignment",
    "future_ready_capacity", "sim_min_ports_2050_high", "future_alignment",
    "simulation_supported_strategy", "right_sizing_validation_note",
]

REQUIRED_EXECUTIVE_COLUMNS = [
    "model_rank", "site_id", "site_name", "readiness_score", "data_confidence_level",
    "recommendation_tier", "action_label", "electrical_risk_level",
    "expected_electrical_rank", "expected_electrical_score", "ports_now",
    "future_ready_capacity", "expansion_strategy", "sim_min_ports_current",
    "sim_utilization_current_at_ports_now", "sim_wait_current_at_ports_now",
    "sim_queue_risk_current_at_ports_now", "sim_min_ports_2035_high",
    "sim_min_ports_2050_high", "sim_status_2050_high_at_future_ready",
    "current_alignment", "future_alignment", "simulation_supported_strategy",
    "right_sizing_validation_note", "major_review_flags",
]

REQUIRED_BASELINE_CHECKS = {
    "site_count",
    "site_results",
    "quality_counts",
    "profile_top_sites",
    "electrical_expected",
    "right_sizing",
    "port_simulation",
    "right_sizing_validation",
    "executive_summary",
    "deliverable_package_manifest",
}

REQUIRED_SITE_IDS = {
    "FFX001", "FFX002", "FFX003", "FFX004",
    "PWC001", "PWC002", "PWC003", "PWC004",
    "PWC005", "PWC006", "PWC007", "PWC008",
}
EXPECTED_SITE_COUNT = len(REQUIRED_SITE_IDS)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_expected_files() -> list[str]:
    errors = []
    for path in EXPECTED_FILES:
        if not path.exists():
            errors.append(f"Missing expected V2 output: {path}")
        elif path.stat().st_size == 0:
            errors.append(f"Expected V2 output is empty: {path}")
    return errors


def check_file_pair_sync(source: Path, destination: Path, label: str) -> list[str]:
    if not source.exists() or not destination.exists():
        return [f"Cannot check {label} sync because one path is missing: {source} -> {destination}"]
    if source.stat().st_size == 0 or destination.stat().st_size == 0:
        return [f"Cannot check {label} sync because one path is empty: {source} -> {destination}"]
    if sha256_file(source) != sha256_file(destination):
        return [f"{label} is stale: {destination} does not match {source}"]
    return []


def check_chart_sync() -> list[str]:
    return check_file_pair_sync(
        Path("data/outputs/charts/v2_site_decision_map_readme.png"),
        Path("docs/assets/charts/v2_site_decision_map_readme.png"),
        "README GIS decision map asset",
    )


def check_columns(table: pd.DataFrame, table_name: str, required_columns: list[str]) -> list[str]:
    missing = [col for col in required_columns if col not in table.columns]
    return [f"{table_name} is missing required columns: {missing}"] if missing else []


def check_site_ids(table: pd.DataFrame, table_name: str) -> list[str]:
    errors = []
    if "site_id" not in table.columns:
        return [f"{table_name} is missing site_id."]
    found_site_ids = set(table["site_id"].astype(str))
    missing_site_ids = sorted(REQUIRED_SITE_IDS - found_site_ids)
    if missing_site_ids:
        errors.append(f"{table_name} is missing expected V2 site IDs: {missing_site_ids}")
    if len(table) < EXPECTED_SITE_COUNT:
        errors.append(f"{table_name} has {len(table)} rows; expected at least {EXPECTED_SITE_COUNT} rows.")
    return errors


def read_table(path: Path, label: str) -> tuple[pd.DataFrame | None, list[str]]:
    if not path.exists():
        return None, [f"Cannot check {label} because {path} is missing."]
    return pd.read_csv(path), []


def check_results_table() -> list[str]:
    results, errors = read_table(Path("data/outputs/v2_site_results.csv"), "V2 results table")
    if results is None:
        return errors
    errors.extend(check_columns(results, "v2_site_results.csv", REQUIRED_RESULT_COLUMNS))
    errors.extend(check_site_ids(results, "v2_site_results.csv"))
    if "readiness_score" in results.columns:
        readiness = pd.to_numeric(results["readiness_score"], errors="coerce")
        if readiness.isna().any() or ((readiness < 0) | (readiness > 100)).any():
            errors.append("v2_site_results.csv has invalid readiness_score values.")
    if "model_rank" in results.columns:
        ranks = pd.to_numeric(results["model_rank"], errors="coerce")
        if ranks.isna().any() or sorted(ranks.astype(int).tolist()) != list(range(1, len(results) + 1)):
            errors.append("v2_site_results.csv model_rank values are not a clean 1..N ranking.")
    return errors


def check_electrical_summary() -> list[str]:
    summary, errors = read_table(Path("data/outputs/v2_electrical_risk_summary.csv"), "electrical risk summary")
    if summary is None:
        return errors
    errors.extend(check_columns(summary, "v2_electrical_risk_summary.csv", REQUIRED_ELECTRICAL_COLUMNS))
    errors.extend(check_site_ids(summary, "v2_electrical_risk_summary.csv"))
    if "electrical_risk_level" in summary.columns:
        invalid = sorted(set(summary["electrical_risk_level"].dropna().astype(str)) - {"low", "medium", "high"})
        if invalid:
            errors.append(f"v2_electrical_risk_summary.csv has invalid risk levels: {invalid}")
    return errors


def check_right_sizing() -> list[str]:
    right_sizing, errors = read_table(Path("data/outputs/v2_right_sizing_scenarios.csv"), "right-sizing output")
    if right_sizing is None:
        return errors
    errors.extend(check_columns(right_sizing, "v2_right_sizing_scenarios.csv", REQUIRED_RIGHT_SIZING_COLUMNS))
    errors.extend(check_site_ids(right_sizing, "v2_right_sizing_scenarios.csv"))
    for col in ["ports_now", "ports_2035_base", "ports_2035_high", "ports_2050_base", "ports_2050_high", "future_ready_capacity"]:
        if col in right_sizing.columns:
            values = pd.to_numeric(right_sizing[col], errors="coerce")
            if values.isna().any() or (values < 0).any():
                errors.append(f"v2_right_sizing_scenarios.csv has invalid values in {col}.")
    return errors


def check_port_simulation() -> list[str]:
    simulation, errors = read_table(Path("data/outputs/v2_port_utilization_simulation.csv"), "V2 port simulation")
    if simulation is None:
        return errors
    errors.extend(check_columns(simulation, "v2_port_utilization_simulation.csv", REQUIRED_PORT_SIM_COLUMNS))
    errors.extend(check_site_ids(simulation, "v2_port_utilization_simulation.csv"))
    expected_min_rows = EXPECTED_SITE_COUNT * 5
    if len(simulation) < expected_min_rows:
        errors.append(f"v2_port_utilization_simulation.csv has {len(simulation)} rows; expected at least {expected_min_rows} rows.")
    return errors


def check_right_sizing_validation() -> list[str]:
    validation, errors = read_table(Path("data/outputs/v2_right_sizing_validation.csv"), "right-sizing validation")
    if validation is None:
        return errors
    errors.extend(check_columns(validation, "v2_right_sizing_validation.csv", REQUIRED_RIGHT_SIZING_VALIDATION_COLUMNS))
    errors.extend(check_site_ids(validation, "v2_right_sizing_validation.csv"))
    return errors


def check_executive_summary() -> list[str]:
    summary, errors = read_table(Path("data/outputs/v2_executive_site_summary.csv"), "V2 executive summary")
    if summary is None:
        return errors
    errors.extend(check_columns(summary, "v2_executive_site_summary.csv", REQUIRED_EXECUTIVE_COLUMNS))
    errors.extend(check_site_ids(summary, "v2_executive_site_summary.csv"))
    return errors


def check_deliverable_package() -> list[str]:
    path = Path("data/outputs/deliverable_package_v2/package_manifest.json")
    if not path.exists():
        return [f"Cannot check deliverable package because {path} is missing."]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"deliverable package manifest is not valid JSON: {exc}"]

    errors = []
    if data.get("package") != "v2_deliverable_package":
        errors.append("deliverable package manifest has the wrong package name.")
    if data.get("status") != "complete":
        errors.append(f"deliverable package manifest status is not complete: {data.get('status')}")
    if data.get("clean_rebuild") is not True:
        errors.append("deliverable package was not created as a clean rebuild.")
    if data.get("previous_package_removed") is not True:
        errors.append("deliverable package manifest does not confirm the previous package was removed.")
    if data.get("missing_or_empty_sources"):
        errors.append("deliverable package manifest reports missing or empty sources.")
    if data.get("out_of_sync_destinations"):
        errors.append("deliverable package manifest reports out-of-sync copied files.")

    expected_count = int(data.get("expected_count", 0))
    copied_count = int(data.get("copied_count", -1))
    synced_count = int(data.get("synced_count", -1))
    if expected_count != EXPECTED_PACKAGE_PAYLOAD_COUNT:
        errors.append(f"deliverable package expected_count is {expected_count}; expected {EXPECTED_PACKAGE_PAYLOAD_COUNT}.")
    if copied_count != EXPECTED_PACKAGE_PAYLOAD_COUNT:
        errors.append(f"deliverable package copied_count is {copied_count}; expected {EXPECTED_PACKAGE_PAYLOAD_COUNT}.")
    if synced_count != EXPECTED_PACKAGE_PAYLOAD_COUNT:
        errors.append(f"deliverable package synced_count is {synced_count}; expected {EXPECTED_PACKAGE_PAYLOAD_COUNT}.")

    expected_manifest_destinations = {str(path) for path in PACKAGE_FILES if path.name not in {"README.md", "package_manifest.json"}}
    manifest_records = data.get("files", [])
    copied_destinations = {str(record.get("destination", "")) for record in manifest_records if record.get("copied")}
    missing_destinations = sorted(expected_manifest_destinations - copied_destinations)
    if missing_destinations:
        errors.append(f"deliverable package manifest is missing copied destinations: {missing_destinations}")

    for record in manifest_records:
        source = Path(str(record.get("source", "")))
        destination = Path(str(record.get("destination", "")))
        if not record.get("copied"):
            continue
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


def check_run_summary() -> list[str]:
    path = Path("data/outputs/v2_run_summary.md")
    if not path.exists():
        return [f"Cannot check V2 run summary because {path} is missing."]
    text = path.read_text(encoding="utf-8")
    required = ["# V2 Model Run Summary", "## Electrical-risk scenario summary", "## Right-sizing scenario summary", "## Generated visual outputs"]
    missing = [phrase for phrase in required if phrase not in text]
    return [f"v2_run_summary.md is missing expected sections: {missing}"] if missing else []


def check_workflow_manifest() -> list[str]:
    path = Path("data/outputs/v2_workflow_success.json")
    if not path.exists():
        return [f"Cannot check V2 workflow manifest because {path} is missing."]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"v2_workflow_success.json is not valid JSON: {exc}"]
    errors = []
    if data.get("workflow") != "v2_expansion_planning":
        errors.append("v2_workflow_success.json has the wrong workflow name.")
    if data.get("status") != "success":
        errors.append(f"v2_workflow_success.json status is not success: {data.get('status')}")
    if int(data.get("site_count", 0)) < EXPECTED_SITE_COUNT:
        errors.append(f"v2_workflow_success.json site_count is lower than expected: expected at least {EXPECTED_SITE_COUNT}.")
    if data.get("missing_or_empty_outputs"):
        errors.append("v2_workflow_success.json reports missing or empty outputs.")
    return errors


def check_baseline_comparison() -> list[str]:
    path = Path("data/outputs/v2_baseline_comparison.json")
    if not path.exists():
        return [f"Cannot check V2 baseline comparison because {path} is missing."]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"v2_baseline_comparison.json is not valid JSON: {exc}"]
    errors = []
    if data.get("status") != "pass":
        errors.append(f"v2_baseline_comparison.json status is not pass: {data.get('status')}")
    checks = data.get("checks", [])
    failed_checks = [check for check in checks if check.get("status") != "pass"]
    if failed_checks:
        errors.append(f"v2_baseline_comparison.json has failed checks: {[check.get('check') for check in failed_checks]}")
    found_checks = {str(check.get("check", "")) for check in checks}
    missing_checks = sorted(REQUIRED_BASELINE_CHECKS - found_checks)
    if missing_checks:
        errors.append(f"v2_baseline_comparison.json is missing required checks: {missing_checks}")
    return errors


def main() -> None:
    print("V2 OUTPUT CHECK")
    print("---------------")
    errors = []
    errors.extend(check_expected_files())
    errors.extend(check_chart_sync())
    errors.extend(check_results_table())
    errors.extend(check_electrical_summary())
    errors.extend(check_right_sizing())
    errors.extend(check_port_simulation())
    errors.extend(check_right_sizing_validation())
    errors.extend(check_executive_summary())
    errors.extend(check_deliverable_package())
    errors.extend(check_run_summary())
    errors.extend(check_workflow_manifest())
    errors.extend(check_baseline_comparison())
    if errors:
        print("Status: FAILED")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    print("Status: PASSED")
    print("All expected V2 outputs are present, all 12 V2 candidate sites are represented, the README decision-map asset is synced, baseline checks cover the new V2 layers, and the deliverable package is hash-synced with current source outputs.")


if __name__ == "__main__":
    main()
