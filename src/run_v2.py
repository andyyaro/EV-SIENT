"""Run the V2 expansion-planning workflow."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

V2_INPUT = "data/inputs/real_sites_v2.csv"
V2_RESULTS = "data/outputs/v2_site_results.csv"
V2_READINESS_CHART = "data/outputs/charts/v2_readiness_score_chart.png"
V2_POLISHED_READINESS_CHART = "data/outputs/charts/v2_polished_readiness_score_chart.png"
V2_DATA_CONFIDENCE_CHART = "data/outputs/charts/v2_data_confidence_chart.png"
V2_SITE_READINESS_MAP = "data/outputs/charts/v2_site_readiness_map.png"
V2_SITE_DECISION_MAP = "data/outputs/charts/v2_site_decision_map.png"
V2_SITE_DECISION_MAP_README = "data/outputs/charts/v2_site_decision_map_readme.png"
V2_DOCS_SITE_DECISION_MAP_README = "docs/assets/charts/v2_site_decision_map_readme.png"
V2_UTILIZATION_CHART_DIR = "data/outputs/charts/v2"
V2_ACTION_MATRIX = "data/outputs/v2_action_matrix.md"
V2_QUALITY = "data/outputs/v2_data_quality_report.csv"
V2_SENSITIVITY_RESULTS = "data/outputs/v2_sensitivity_results.csv"
V2_SENSITIVITY_SUMMARY = "data/outputs/v2_sensitivity_summary.csv"
V2_PROFILE_RESULTS = "data/outputs/v2_profile_results.csv"
V2_PROFILE_RANK_SUMMARY = "data/outputs/v2_profile_rank_summary.csv"
V2_PROFILE_REPORT = "data/outputs/v2_profile_comparison.md"
V2_PROFILE_SCORE_HEATMAP = "data/outputs/charts/v2_profile_score_heatmap.png"
V2_PROFILE_RANK_STABILITY_CHART = "data/outputs/charts/v2_profile_rank_stability_chart.png"
V2_ELECTRICAL_SCENARIO_RESULTS = "data/outputs/v2_electrical_scenario_results.csv"
V2_ELECTRICAL_RISK_SUMMARY = "data/outputs/v2_electrical_risk_summary.csv"
V2_ELECTRICAL_REPORT = "data/outputs/v2_electrical_feasibility_report.md"
V2_RIGHT_SIZING = "data/outputs/v2_right_sizing_scenarios.csv"
V2_RIGHT_SIZING_REPORT = "data/outputs/v2_right_sizing_report.md"
V2_PORT_SIM = "data/outputs/v2_port_utilization_simulation.csv"
V2_PORT_SIM_REPORT = "data/outputs/v2_port_utilization_simulation_report.md"
V2_PORT_SIM_CHART = "data/outputs/charts/v2_port_utilization_simulation.png"
V2_PORT_SIZING_SCENARIOS = "data/inputs/v2_port_sizing_scenarios.csv"
V2_PORT_SIZING_SCENARIO_RESULTS = "data/outputs/v2_port_sizing_scenario_results.csv"
V2_PORT_SIZING_SCENARIO_SUMMARY = "data/outputs/v2_port_sizing_scenario_summary.csv"
V2_PORT_SIZING_SCENARIO_REPORT = "data/outputs/v2_port_sizing_scenario_report.md"
V2_PORT_SIZING_SCENARIO_CHART = "data/outputs/charts/v2_port_sizing_scenario_heatmap.png"
V2_RIGHT_SIZING_VALIDATION = "data/outputs/v2_right_sizing_validation.csv"
V2_RIGHT_SIZING_VALIDATION_REPORT = "data/outputs/v2_right_sizing_validation_report.md"
V2_EXECUTIVE_SUMMARY = "data/outputs/v2_executive_site_summary.csv"
V2_EXECUTIVE_SUMMARY_REPORT = "data/outputs/v2_executive_site_summary.md"
V2_INTERPRETATION = "data/outputs/v2_results_interpretation.md"
V2_RUN_SUMMARY = "data/outputs/v2_run_summary.md"
V2_PUBLIC_REPORT = "data/outputs/Public_EV_Charging_Planning_Report.pdf"
V2_WORKFLOW_STATUS = "data/outputs/v2_workflow_success.json"
V2_BASELINE = "data/baselines/v2_baseline_snapshot.json"
V2_BASELINE_COMPARISON_JSON = "data/outputs/v2_baseline_comparison.json"
V2_BASELINE_COMPARISON_MD = "data/outputs/v2_baseline_comparison.md"
V2_DELIVERABLE_PACKAGE_DIR = "data/outputs/deliverable_package_v2"
V2_DELIVERABLE_PACKAGE_README = "data/outputs/deliverable_package_v2/README.md"
V2_DELIVERABLE_PACKAGE_MANIFEST = "data/outputs/deliverable_package_v2/package_manifest.json"


def run_step(title: str, args: list[str]) -> None:
    """Run one workflow command and stop immediately if it fails."""
    print()
    print(title)
    print("-" * len(title))
    print(" ".join(args))
    subprocess.run(args, cwd=PROJECT_ROOT, check=True)


def baseline_comparison_args(include_deliverable_manifest: bool = False) -> list[str]:
    """Build the V2 baseline-comparison command arguments."""
    args = [
        PYTHON, "src/compare_v2_to_baseline.py",
        "--baseline", V2_BASELINE,
        "--results", V2_RESULTS,
        "--quality", V2_QUALITY,
        "--profile-results", V2_PROFILE_RESULTS,
        "--electrical-summary", V2_ELECTRICAL_RISK_SUMMARY,
        "--right-sizing", V2_RIGHT_SIZING,
        "--port-simulation", V2_PORT_SIM,
        "--port-sizing-scenarios", V2_PORT_SIZING_SCENARIO_RESULTS,
        "--port-sizing-summary", V2_PORT_SIZING_SCENARIO_SUMMARY,
        "--right-sizing-validation", V2_RIGHT_SIZING_VALIDATION,
        "--executive-summary", V2_EXECUTIVE_SUMMARY,
        "--json-output", V2_BASELINE_COMPARISON_JSON,
        "--md-output", V2_BASELINE_COMPARISON_MD,
    ]
    if include_deliverable_manifest:
        args.extend(["--deliverable-manifest", V2_DELIVERABLE_PACKAGE_MANIFEST])
    return args


def main() -> None:
    print("V2 EXPANSION-PLANNING WORKFLOW")
    print("------------------------------")
    print(f"Python: {PYTHON}")
    print(f"Input: {V2_INPUT}")

    run_step("1. Run V2 site-readiness model", [PYTHON, "src/ev_charger_model.py", "--input", V2_INPUT, "--output", V2_RESULTS, "--chart", V2_READINESS_CHART, "--utilization-chart-dir", V2_UTILIZATION_CHART_DIR])
    run_step("2. Add V2 readiness-confidence action matrix", [PYTHON, "src/add_action_matrix.py", "--results", V2_RESULTS, "--report", V2_ACTION_MATRIX])
    run_step("3. Create V2 polished readiness score chart", [PYTHON, "src/plot_readiness_score_chart.py", "--results", V2_RESULTS, "--output", V2_POLISHED_READINESS_CHART])
    run_step("4. Create V2 data confidence chart", [PYTHON, "src/plot_data_confidence_chart.py", "--results", V2_RESULTS, "--output", V2_DATA_CONFIDENCE_CHART])
    run_step("5. Validate V2 site input data", [PYTHON, "src/validate_site_data.py", "--input", V2_INPUT, "--output", V2_QUALITY])
    run_step("6. Run V2 sensitivity analysis", [PYTHON, "src/run_sensitivity_analysis.py", "--input", V2_INPUT, "--results-output", V2_SENSITIVITY_RESULTS, "--summary-output", V2_SENSITIVITY_SUMMARY])
    run_step("7. Run V2 scoring-profile analysis", [PYTHON, "src/run_profile_analysis.py", "--site-results", V2_RESULTS, "--input-sites", V2_INPUT, "--output", V2_PROFILE_RESULTS, "--summary-output", V2_PROFILE_RANK_SUMMARY, "--report-output", V2_PROFILE_REPORT])
    run_step("8. Create V2 profile score heatmap", [PYTHON, "src/plot_profile_score_heatmap.py", "--profile-results", V2_PROFILE_RESULTS, "--output", V2_PROFILE_SCORE_HEATMAP])
    run_step("9. Create V2 profile rank stability chart", [PYTHON, "src/plot_profile_rank_stability.py", "--profile-results", V2_PROFILE_RESULTS, "--output", V2_PROFILE_RANK_STABILITY_CHART])
    run_step("10. Create V2 readiness map", [PYTHON, "src/plot_site_map.py", "--input", V2_INPUT, "--results", V2_RESULTS, "--sensitivity", V2_SENSITIVITY_SUMMARY, "--profile-results", V2_PROFILE_RESULTS, "--output", V2_SITE_READINESS_MAP])
    run_step("11. Run V2 electrical-feasibility scenario analysis", [PYTHON, "src/run_electrical_risk_scenarios.py", "--results", V2_RESULTS, "--scenario-output", V2_ELECTRICAL_SCENARIO_RESULTS, "--summary-output", V2_ELECTRICAL_RISK_SUMMARY, "--report-output", V2_ELECTRICAL_REPORT])
    run_step("12. Run V2 right-sizing scenario analysis", [PYTHON, "src/run_right_sizing_scenarios.py", "--results", V2_RESULTS, "--electrical-summary", V2_ELECTRICAL_RISK_SUMMARY, "--output", V2_RIGHT_SIZING, "--report", V2_RIGHT_SIZING_REPORT])
    run_step("13. Run V2 port-use simulation", [PYTHON, "src/run_port_utilization_simulation.py", "--results", V2_RESULTS, "--right-sizing", V2_RIGHT_SIZING, "--output", V2_PORT_SIM, "--report", V2_PORT_SIM_REPORT, "--chart", V2_PORT_SIM_CHART])
    run_step("14. Run V2 port-sizing scenario analysis", [PYTHON, "src/run_port_sizing_scenario_analysis.py", "--results", V2_RESULTS, "--right-sizing", V2_RIGHT_SIZING, "--scenarios", V2_PORT_SIZING_SCENARIOS, "--output", V2_PORT_SIZING_SCENARIO_RESULTS, "--summary-output", V2_PORT_SIZING_SCENARIO_SUMMARY, "--report", V2_PORT_SIZING_SCENARIO_REPORT, "--chart", V2_PORT_SIZING_SCENARIO_CHART])
    run_step("15. Validate V2 right-sizing with simulation", [PYTHON, "src/validate_right_sizing_with_simulation.py", "--right-sizing", V2_RIGHT_SIZING, "--port-simulation", V2_PORT_SIM, "--output", V2_RIGHT_SIZING_VALIDATION, "--report", V2_RIGHT_SIZING_VALIDATION_REPORT])
    run_step("16. Build V2 executive site summary", [PYTHON, "src/build_v2_executive_summary.py", "--results", V2_RESULTS, "--electrical-summary", V2_ELECTRICAL_RISK_SUMMARY, "--right-sizing", V2_RIGHT_SIZING, "--port-simulation", V2_PORT_SIM, "--port-sizing-scenarios", V2_PORT_SIZING_SCENARIO_RESULTS, "--right-sizing-validation", V2_RIGHT_SIZING_VALIDATION, "--output", V2_EXECUTIVE_SUMMARY, "--report", V2_EXECUTIVE_SUMMARY_REPORT])
    run_step("17. Create V2 GIS decision maps", [PYTHON, "src/plot_site_decision_map_all_labels.py", "--input", V2_EXECUTIVE_SUMMARY, "--output", V2_SITE_DECISION_MAP, "--readme-output", V2_SITE_DECISION_MAP_README, "--docs-readme-output", V2_DOCS_SITE_DECISION_MAP_README])
    run_step("18. Generate V2 interpretation report", [PYTHON, "src/generate_results_interpretation.py", "--results", V2_RESULTS, "--quality", V2_QUALITY, "--sensitivity", V2_SENSITIVITY_SUMMARY, "--profile-results", V2_PROFILE_RESULTS, "--action-report", V2_ACTION_MATRIX, "--output", V2_INTERPRETATION])
    run_step("19. Generate V2 run summary", [PYTHON, "src/generate_run_summary_v2.py", "--results", V2_RESULTS, "--quality", V2_QUALITY, "--sensitivity", V2_SENSITIVITY_SUMMARY, "--profile-results", V2_PROFILE_RESULTS, "--electrical-summary", V2_ELECTRICAL_RISK_SUMMARY, "--right-sizing", V2_RIGHT_SIZING, "--output", V2_RUN_SUMMARY])
    run_step("20. Generate public EV planning PDF report", [PYTHON, "src/generate_public_ev_report_pdf.py", "--executive-summary", V2_EXECUTIVE_SUMMARY, "--quality", V2_QUALITY, "--scenarios", V2_PORT_SIZING_SCENARIO_RESULTS, "--output", V2_PUBLIC_REPORT])
    run_step("21. Compare V2 outputs to baseline", baseline_comparison_args())
    run_step("22. Write V2 workflow completion manifest", [PYTHON, "src/write_v2_workflow_success_marker.py", "--input", V2_INPUT, "--results", V2_RESULTS, "--quality", V2_QUALITY, "--electrical-summary", V2_ELECTRICAL_RISK_SUMMARY, "--right-sizing", V2_RIGHT_SIZING, "--output", V2_WORKFLOW_STATUS])
    run_step("23. Build V2 deliverable package", [PYTHON, "src/build_v2_deliverable_package.py", "--output-dir", V2_DELIVERABLE_PACKAGE_DIR])
    run_step("24. Compare V2 deliverable package manifest to baseline", baseline_comparison_args(include_deliverable_manifest=True))
    run_step("25. Rebuild V2 deliverable package with final baseline comparison", [PYTHON, "src/build_v2_deliverable_package.py", "--output-dir", V2_DELIVERABLE_PACKAGE_DIR])

    print()
    print("V2 workflow complete.")
    print("Key outputs:")
    for path in [
        V2_RESULTS, V2_ACTION_MATRIX, V2_QUALITY, V2_SENSITIVITY_RESULTS, V2_SENSITIVITY_SUMMARY,
        V2_PROFILE_RESULTS, V2_PROFILE_REPORT, V2_ELECTRICAL_RISK_SUMMARY,
        V2_ELECTRICAL_REPORT, V2_RIGHT_SIZING, V2_RIGHT_SIZING_REPORT,
        V2_PORT_SIM, V2_PORT_SIM_REPORT, V2_PORT_SIM_CHART,
        V2_PORT_SIZING_SCENARIO_RESULTS, V2_PORT_SIZING_SCENARIO_SUMMARY,
        V2_PORT_SIZING_SCENARIO_REPORT, V2_PORT_SIZING_SCENARIO_CHART,
        V2_RIGHT_SIZING_VALIDATION, V2_RIGHT_SIZING_VALIDATION_REPORT,
        V2_EXECUTIVE_SUMMARY, V2_EXECUTIVE_SUMMARY_REPORT,
        V2_INTERPRETATION, V2_RUN_SUMMARY, V2_PUBLIC_REPORT, V2_WORKFLOW_STATUS,
        V2_BASELINE_COMPARISON_JSON, V2_BASELINE_COMPARISON_MD,
        V2_DELIVERABLE_PACKAGE_README, V2_DELIVERABLE_PACKAGE_MANIFEST,
        V2_READINESS_CHART, V2_POLISHED_READINESS_CHART,
        V2_DATA_CONFIDENCE_CHART, V2_PROFILE_SCORE_HEATMAP,
        V2_PROFILE_RANK_STABILITY_CHART, V2_SITE_READINESS_MAP,
        V2_SITE_DECISION_MAP, V2_SITE_DECISION_MAP_README,
        V2_DOCS_SITE_DECISION_MAP_README,
    ]:
        print(f"- {path}")


if __name__ == "__main__":
    main()
