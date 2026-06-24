"""Run the full EV charger model workflow in one command.

This script calls the main project scripts in the correct order so the validator,
model outputs, sensitivity analysis, profile analysis, map/chart outputs,
Markdown summaries, generated interpretation, and combined output checks stay
synchronized.

Run from the repository root:

    python src/run_all.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUCCESS_MARKER = "data/outputs/workflow_success.json"

STEPS = [
    {"name": "Validate input data", "command": [sys.executable, "src/validate_site_data.py"]},
    {"name": "Run readiness and right-sizing model", "command": [sys.executable, "src/ev_charger_model.py"]},
    {"name": "Create polished readiness score chart", "command": [sys.executable, "src/plot_readiness_score_chart.py"]},
    {"name": "Create data confidence chart", "command": [sys.executable, "src/plot_data_confidence_chart.py"]},
    {"name": "Run sensitivity analysis", "command": [sys.executable, "src/run_sensitivity_analysis.py"]},
    {"name": "Run scoring profile analysis", "command": [sys.executable, "src/run_profile_analysis.py"]},
    {"name": "Create profile score heatmap", "command": [sys.executable, "src/plot_profile_score_heatmap.py"]},
    {"name": "Create profile rank stability chart", "command": [sys.executable, "src/plot_profile_rank_stability.py"]},
    {"name": "Create readiness map", "command": [sys.executable, "src/plot_site_map.py"]},
    {"name": "Generate Markdown run summary", "command": [sys.executable, "src/generate_run_summary.py"]},
    {"name": "Generate results interpretation", "command": [sys.executable, "src/generate_results_interpretation.py"]},
    {"name": "Check outputs and compare to V1 baseline", "command": [sys.executable, "src/check_outputs.py"]},
]

EXPECTED_OUTPUTS = [
    "data/outputs/data_quality_report.csv",
    "data/outputs/site_results.csv",
    "data/outputs/sensitivity_results.csv",
    "data/outputs/sensitivity_summary.csv",
    "data/outputs/profile_results.csv",
    "data/outputs/profile_rank_summary.csv",
    "data/outputs/profile_comparison.md",
    "data/outputs/charts/readiness_score_chart.png",
    "data/outputs/charts/data_confidence_chart.png",
    "data/outputs/charts/profile_score_heatmap.png",
    "data/outputs/charts/profile_rank_stability_chart.png",
    "data/outputs/charts/site_readiness_map.png",
    "data/outputs/model_run_summary.md",
    "data/outputs/results_interpretation.md",
    "data/outputs/baseline_comparison.csv",
    "data/outputs/baseline_comparison.md",
    SUCCESS_MARKER,
]


def run_step(step: dict[str, object]) -> None:
    """Run one pipeline step and stop if it fails."""
    name = str(step["name"])
    command = list(step["command"])

    print()
    print("=" * 72)
    print(name)
    print("=" * 72)
    print("Command:", " ".join(command))
    print()

    completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"Pipeline stopped because this step failed: {name}")


def write_success_marker() -> None:
    marker_path = PROJECT_ROOT / SUCCESS_MARKER
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "status": "passed",
        "steps": [step["name"] for step in STEPS],
    }
    marker_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def print_output_summary() -> None:
    """Print which expected outputs exist after the run."""
    print()
    print("=" * 72)
    print("Output summary")
    print("=" * 72)

    for relative_path in EXPECTED_OUTPUTS:
        path = PROJECT_ROOT / relative_path
        status = "OK" if path.exists() else "MISSING"
        print(f"{status:7} {relative_path}")

    print()
    print("Done. Generated outputs are local files under data/outputs/ and are ignored by Git.")


def main() -> None:
    print("FULL EV CHARGER MODEL WORKFLOW")
    print("Repository root:", PROJECT_ROOT)

    for step in STEPS:
        run_step(step)

    write_success_marker()
    print_output_summary()


if __name__ == "__main__":
    main()
