"""Check generated V2 model outputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

EXPECTED_FILES = [
    Path("data/outputs/v2_site_results.csv"),
    Path("data/outputs/v2_action_matrix.md"),
    Path("data/outputs/v2_data_quality_report.csv"),
    Path("data/outputs/v2_sensitivity_summary.csv"),
    Path("data/outputs/v2_profile_results.csv"),
    Path("data/outputs/v2_profile_comparison.md"),
    Path("data/outputs/v2_electrical_scenario_results.csv"),
    Path("data/outputs/v2_electrical_risk_summary.csv"),
    Path("data/outputs/v2_electrical_feasibility_report.md"),
    Path("data/outputs/v2_right_sizing_scenarios.csv"),
    Path("data/outputs/v2_right_sizing_report.md"),
    Path("data/outputs/v2_port_utilization_simulation.csv"),
    Path("data/outputs/v2_port_utilization_simulation_report.md"),
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
    Path("data/outputs/charts/v2_port_utilization_simulation.png"),
]

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

REQUIRED_EXECUTIVE_COLUMNS = [
    "model_rank", "site_id", "site_name", "readiness_score", "data_confidence_level",
    "recommendation_tier", "action_label", "electrical_risk_level",
    "expected_electrical_rank", "expected_electrical_score", "ports_now",
    "future_ready_capacity", "expansion_strategy", "major_review_flags",
]

REQUIRED_SITE_IDS = {"FFX001", "FFX002", "FFX003", "FFX004", "PWC001", "PWC002", "PWC003", "PWC004"}


def check_expected_files() -> list[str]:
    errors = []
    for path in EXPECTED_FILES:
        if not path.exists():
            errors.append(f"Missing expected V2 output: {path}")
        elif path.stat().st_size == 0:
            errors.append(f"Expected V2 output is empty: {path}")
    return errors


def check_results_table() -> list[str]:
    errors = []
    path = Path("data/outputs/v2_site_results.csv")
    if not path.exists():
        return [f"Cannot check V2 results table because {path} is missing."]
    results = pd.read_csv(path)
    missing_columns = [col for col in REQUIRED_RESULT_COLUMNS if col not in results.columns]
    if missing_columns:
        errors.append(f"v2_site_results.csv is missing required columns: {missing_columns}")
    if len(results) < len(REQUIRED_SITE_IDS):
        errors.append(f"v2_site_results.csv has {len(results)} rows; expected at least {len(REQUIRED_SITE_IDS)} rows.")
    found_site_ids = set(results.get("site_id", pd.Series(dtype=str)).astype(str))
    missing_site_ids = sorted(REQUIRED_SITE_IDS - found_site_ids)
    if missing_site_ids:
        errors.append(f"v2_site_results.csv is missing expected site IDs: {missing_site_ids}")
    if "readiness_score" in results.columns:
        readiness = pd.to_numeric(results["readiness_score"], errors="coerce")
        if readiness.isna().any():
            errors.append("v2_site_results.csv has nonnumeric readiness_score values.")
        if ((readiness < 0) | (readiness > 100)).any():
            errors.append("v2_site_results.csv has readiness_score values outside 0-100.")
    if "model_rank" in results.columns:
        ranks = pd.to_numeric(results["model_rank"], errors="coerce")
        if ranks.isna().any() or sorted(ranks.astype(int).tolist()) != list(range(1, len(results) + 1)):
            errors.append("v2_site_results.csv model_rank values are not a clean 1..N ranking.")
    return errors


def check_electrical_summary() -> list[str]:
    errors = []
    path = Path("data/outputs/v2_electrical_risk_summary.csv")
    if not path.exists():
        return [f"Cannot check electrical risk summary because {path} is missing."]
    summary = pd.read_csv(path)
    missing_columns = [col for col in REQUIRED_ELECTRICAL_COLUMNS if col not in summary.columns]
    if missing_columns:
        errors.append(f"v2_electrical_risk_summary.csv is missing required columns: {missing_columns}")
    if "electrical_risk_level" in summary.columns:
        valid_levels = {"low", "medium", "high"}
        found_levels = set(summary["electrical_risk_level"].dropna().astype(str))
        invalid_levels = sorted(found_levels - valid_levels)
        if invalid_levels:
            errors.append(f"v2_electrical_risk_summary.csv has invalid risk levels: {invalid_levels}")
    return errors


def check_right_sizing() -> list[str]:
    errors = []
    path = Path("data/outputs/v2_right_sizing_scenarios.csv")
    if not path.exists():
        return [f"Cannot check right-sizing output because {path} is missing."]
    right_sizing = pd.read_csv(path)
    missing_columns = [col for col in REQUIRED_RIGHT_SIZING_COLUMNS if col not in right_sizing.columns]
    if missing_columns:
        errors.append(f"v2_right_sizing_scenarios.csv is missing required columns: {missing_columns}")
    for col in ["ports_now", "ports_2035_base", "ports_2035_high", "ports_2050_base", "ports_2050_high", "future_ready_capacity"]:
        if col in right_sizing.columns:
            values = pd.to_numeric(right_sizing[col], errors="coerce")
            if values.isna().any() or (values < 0).any():
                errors.append(f"v2_right_sizing_scenarios.csv has invalid values in {col}.")
    return errors


def check_port_simulation() -> list[str]:
    errors = []
    path = Path("data/outputs/v2_port_utilization_simulation.csv")
    if not path.exists():
        return [f"Cannot check V2 port simulation because {path} is missing."]
    simulation = pd.read_csv(path)
    missing_columns = [col for col in REQUIRED_PORT_SIM_COLUMNS if col not in simulation.columns]
    if missing_columns:
        errors.append(f"v2_port_utilization_simulation.csv is missing required columns: {missing_columns}")
    if len(simulation) < len(REQUIRED_SITE_IDS) * 5:
        errors.append("v2_port_utilization_simulation.csv has fewer rows than expected.")
    return errors


def check_executive_summary() -> list[str]:
    errors = []
    path = Path("data/outputs/v2_executive_site_summary.csv")
    if not path.exists():
        return [f"Cannot check V2 executive summary because {path} is missing."]
    summary = pd.read_csv(path)
    missing_columns = [col for col in REQUIRED_EXECUTIVE_COLUMNS if col not in summary.columns]
    if missing_columns:
        errors.append(f"v2_executive_site_summary.csv is missing required columns: {missing_columns}")
    if len(summary) < len(REQUIRED_SITE_IDS):
        errors.append("v2_executive_site_summary.csv has fewer rows than expected.")
    return errors


def check_run_summary() -> list[str]:
    path = Path("data/outputs/v2_run_summary.md")
    if not path.exists():
        return [f"Cannot check V2 run summary because {path} is missing."]
    text = path.read_text(encoding="utf-8")
    required_phrases = ["# V2 Model Run Summary", "## Electrical-risk scenario summary", "## Right-sizing scenario summary", "## Generated visual outputs"]
    missing = [phrase for phrase in required_phrases if phrase not in text]
    if missing:
        return [f"v2_run_summary.md is missing expected sections: {missing}"]
    return []


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
    if int(data.get("site_count", 0)) < len(REQUIRED_SITE_IDS):
        errors.append("v2_workflow_success.json site_count is lower than expected.")
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
    failed_checks = [check for check in data.get("checks", []) if check.get("status") != "pass"]
    if failed_checks:
        errors.append(f"v2_baseline_comparison.json has failed checks: {[check.get('check') for check in failed_checks]}")
    return errors


def main() -> None:
    print("V2 OUTPUT CHECK")
    print("---------------")
    errors = []
    errors.extend(check_expected_files())
    errors.extend(check_results_table())
    errors.extend(check_electrical_summary())
    errors.extend(check_right_sizing())
    errors.extend(check_port_simulation())
    errors.extend(check_executive_summary())
    errors.extend(check_run_summary())
    errors.extend(check_workflow_manifest())
    errors.extend(check_baseline_comparison())
    if errors:
        print("Status: FAILED")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    print("Status: PASSED")
    print("All expected V2 outputs are present and the main V2 results table has the required structure.")


if __name__ == "__main__":
    main()
