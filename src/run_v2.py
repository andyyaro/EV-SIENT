"""Run the V2 expansion-planning workflow.

This script is intentionally separate from src/run_all.py, which preserves the
stable V1 workflow on main. V2 uses the expanded input file and V2-specific
local output paths so the generated outputs do not overwrite the V1 run.

Run from the repository root:

    python src/run_v2.py

The script writes generated outputs under data/outputs/. Those files are local
artifacts and are ignored by Git unless a polished summary is intentionally
copied into docs/.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

V2_INPUT = "data/inputs/real_sites_v2.csv"
V2_RESULTS = "data/outputs/v2_site_results.csv"
V2_READINESS_CHART = "data/outputs/charts/v2_readiness_score_chart.png"
V2_UTILIZATION_CHART_DIR = "data/outputs/charts/v2"
V2_ACTION_MATRIX = "data/outputs/v2_action_matrix.md"
V2_QUALITY = "data/outputs/v2_data_quality_report.csv"
V2_SENSITIVITY_RESULTS = "data/outputs/v2_sensitivity_results.csv"
V2_SENSITIVITY_SUMMARY = "data/outputs/v2_sensitivity_summary.csv"
V2_PROFILE_RESULTS = "data/outputs/v2_profile_results.csv"
V2_PROFILE_RANK_SUMMARY = "data/outputs/v2_profile_rank_summary.csv"
V2_PROFILE_REPORT = "data/outputs/v2_profile_comparison.md"
V2_ELECTRICAL_SCENARIO_RESULTS = "data/outputs/v2_electrical_scenario_results.csv"
V2_ELECTRICAL_RISK_SUMMARY = "data/outputs/v2_electrical_risk_summary.csv"
V2_ELECTRICAL_REPORT = "data/outputs/v2_electrical_feasibility_report.md"
V2_INTERPRETATION = "data/outputs/v2_results_interpretation.md"


def run_step(title: str, args: list[str]) -> None:
    """Run one workflow command and stop immediately if it fails."""
    print()
    print(title)
    print("-" * len(title))
    print(" ".join(args))
    subprocess.run(args, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    print("V2 EXPANSION-PLANNING WORKFLOW")
    print("------------------------------")
    print(f"Python: {PYTHON}")
    print(f"Input: {V2_INPUT}")

    run_step(
        "1. Run V2 site-readiness model",
        [
            PYTHON,
            "src/ev_charger_model.py",
            "--input",
            V2_INPUT,
            "--output",
            V2_RESULTS,
            "--chart",
            V2_READINESS_CHART,
            "--utilization-chart-dir",
            V2_UTILIZATION_CHART_DIR,
        ],
    )

    run_step(
        "2. Add V2 readiness-confidence action matrix",
        [
            PYTHON,
            "src/add_action_matrix.py",
            "--results",
            V2_RESULTS,
            "--report",
            V2_ACTION_MATRIX,
        ],
    )

    run_step(
        "3. Validate V2 site input data",
        [
            PYTHON,
            "src/validate_site_data.py",
            "--input",
            V2_INPUT,
            "--output",
            V2_QUALITY,
        ],
    )

    run_step(
        "4. Run V2 sensitivity analysis",
        [
            PYTHON,
            "src/run_sensitivity_analysis.py",
            "--input",
            V2_INPUT,
            "--results-output",
            V2_SENSITIVITY_RESULTS,
            "--summary-output",
            V2_SENSITIVITY_SUMMARY,
        ],
    )

    run_step(
        "5. Run V2 scoring-profile analysis",
        [
            PYTHON,
            "src/run_profile_analysis.py",
            "--site-results",
            V2_RESULTS,
            "--input-sites",
            V2_INPUT,
            "--output",
            V2_PROFILE_RESULTS,
            "--summary-output",
            V2_PROFILE_RANK_SUMMARY,
            "--report-output",
            V2_PROFILE_REPORT,
        ],
    )

    run_step(
        "6. Run V2 electrical-feasibility scenario analysis",
        [
            PYTHON,
            "src/run_electrical_risk_scenarios.py",
            "--results",
            V2_RESULTS,
            "--scenario-output",
            V2_ELECTRICAL_SCENARIO_RESULTS,
            "--summary-output",
            V2_ELECTRICAL_RISK_SUMMARY,
            "--report-output",
            V2_ELECTRICAL_REPORT,
        ],
    )

    run_step(
        "7. Generate V2 interpretation report",
        [
            PYTHON,
            "src/generate_results_interpretation.py",
            "--results",
            V2_RESULTS,
            "--quality",
            V2_QUALITY,
            "--sensitivity",
            V2_SENSITIVITY_SUMMARY,
            "--profile-results",
            V2_PROFILE_RESULTS,
            "--action-report",
            V2_ACTION_MATRIX,
            "--output",
            V2_INTERPRETATION,
        ],
    )

    print()
    print("V2 workflow complete.")
    print("Key outputs:")
    for path in [
        V2_RESULTS,
        V2_ACTION_MATRIX,
        V2_QUALITY,
        V2_SENSITIVITY_SUMMARY,
        V2_PROFILE_RESULTS,
        V2_PROFILE_REPORT,
        V2_ELECTRICAL_RISK_SUMMARY,
        V2_ELECTRICAL_REPORT,
        V2_INTERPRETATION,
        V2_READINESS_CHART,
    ]:
        print(f"- {path}")


if __name__ == "__main__":
    main()
