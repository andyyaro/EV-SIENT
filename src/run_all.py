"""Run the full EV charger model workflow in one command.

This script is a beginner-friendly pipeline runner. It calls the main project
scripts in the correct order so the validator, model outputs, sensitivity
analysis, map/chart outputs, and Markdown run summary stay synchronized.

Run from the repository root:

    python src/run_all.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    {
        "name": "Validate input data",
        "command": [sys.executable, "src/validate_site_data.py"],
    },
    {
        "name": "Run readiness and right-sizing model",
        "command": [sys.executable, "src/ev_charger_model.py"],
    },
    {
        "name": "Run sensitivity analysis",
        "command": [sys.executable, "src/run_sensitivity_analysis.py"],
    },
    {
        "name": "Create readiness map",
        "command": [sys.executable, "src/plot_site_map.py"],
    },
    {
        "name": "Generate Markdown run summary",
        "command": [sys.executable, "src/generate_run_summary.py"],
    },
]

EXPECTED_OUTPUTS = [
    "data/outputs/data_quality_report.csv",
    "data/outputs/site_results.csv",
    "data/outputs/sensitivity_results.csv",
    "data/outputs/sensitivity_summary.csv",
    "data/outputs/charts/readiness_score_chart.png",
    "data/outputs/charts/site_readiness_map.png",
    "data/outputs/model_run_summary.md",
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

    print_output_summary()


if __name__ == "__main__":
    main()
