"""Write a V2 workflow success marker and output manifest.

This script runs near the end of the V2 workflow. It checks the expected local
outputs and writes a machine-readable JSON file that records what was generated,
when it was generated, and the headline result.

Run from the repository root after the V2 workflow outputs exist:

    python src/write_v2_workflow_success_marker.py
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_INPUT = "data/inputs/real_sites_v2.csv"
DEFAULT_RESULTS = "data/outputs/v2_site_results.csv"
DEFAULT_QUALITY = "data/outputs/v2_data_quality_report.csv"
DEFAULT_ELECTRICAL_SUMMARY = "data/outputs/v2_electrical_risk_summary.csv"
DEFAULT_RIGHT_SIZING = "data/outputs/v2_right_sizing_scenarios.csv"
DEFAULT_OUTPUT = "data/outputs/v2_workflow_success.json"

EXPECTED_OUTPUTS = [
    "data/outputs/v2_site_results.csv",
    "data/outputs/v2_action_matrix.md",
    "data/outputs/v2_data_quality_report.csv",
    "data/outputs/v2_sensitivity_summary.csv",
    "data/outputs/v2_profile_results.csv",
    "data/outputs/v2_profile_comparison.md",
    "data/outputs/v2_electrical_scenario_results.csv",
    "data/outputs/v2_electrical_risk_summary.csv",
    "data/outputs/v2_electrical_feasibility_report.md",
    "data/outputs/v2_right_sizing_scenarios.csv",
    "data/outputs/v2_right_sizing_report.md",
    "data/outputs/v2_port_utilization_simulation.csv",
    "data/outputs/v2_port_utilization_simulation_report.md",
    "data/outputs/v2_right_sizing_validation.csv",
    "data/outputs/v2_right_sizing_validation_report.md",
    "data/outputs/v2_executive_site_summary.csv",
    "data/outputs/v2_executive_site_summary.md",
    "data/outputs/v2_results_interpretation.md",
    "data/outputs/v2_run_summary.md",
    "data/outputs/v2_baseline_comparison.json",
    "data/outputs/v2_baseline_comparison.md",
    "data/outputs/charts/v2_readiness_score_chart.png",
    "data/outputs/charts/v2_polished_readiness_score_chart.png",
    "data/outputs/charts/v2_data_confidence_chart.png",
    "data/outputs/charts/v2_profile_score_heatmap.png",
    "data/outputs/charts/v2_profile_rank_stability_chart.png",
    "data/outputs/charts/v2_site_readiness_map.png",
    "data/outputs/charts/v2_site_decision_map.png",
    "data/outputs/charts/v2_site_decision_map_readme.png",
    "data/outputs/charts/v2_port_utilization_simulation.png",
    "docs/assets/charts/v2_site_decision_map_readme.png",
]


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def file_record(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    exists = path.exists()
    return {
        "path": path_text,
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
    }


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def top_site_summary(results: pd.DataFrame) -> dict[str, Any]:
    if results.empty or "model_rank" not in results.columns:
        return {}
    ranked = results.copy()
    ranked["model_rank"] = pd.to_numeric(ranked["model_rank"], errors="coerce")
    ranked = ranked.sort_values("model_rank")
    if ranked.empty:
        return {}
    top = ranked.iloc[0]
    return {
        "site_id": str(top.get("site_id", "")),
        "site_name": str(top.get("site_name", "")),
        "model_rank": int(top.get("model_rank", 0)) if pd.notna(top.get("model_rank", None)) else None,
        "readiness_score": float(top.get("readiness_score", 0)) if pd.notna(top.get("readiness_score", None)) else None,
        "recommendation_tier": str(top.get("recommendation_tier", "")),
        "action_label": str(top.get("action_label", "")),
    }


def quality_counts(quality: pd.DataFrame) -> dict[str, int]:
    if quality.empty or "severity" not in quality.columns:
        return {}
    counts = quality["severity"].value_counts().to_dict()
    return {level: int(counts.get(level, 0)) for level in ["ERROR", "WARNING", "REVIEW", "INFO"]}


def electrical_counts(electrical: pd.DataFrame) -> dict[str, int]:
    if electrical.empty or "electrical_risk_level" not in electrical.columns:
        return {}
    counts = electrical["electrical_risk_level"].astype(str).value_counts().to_dict()
    return {level: int(counts.get(level, 0)) for level in ["low", "medium", "high"]}


def right_sizing_top_summary(right_sizing: pd.DataFrame) -> dict[str, Any]:
    if right_sizing.empty or "model_rank" not in right_sizing.columns:
        return {}
    ranked = right_sizing.copy()
    ranked["model_rank"] = pd.to_numeric(ranked["model_rank"], errors="coerce")
    ranked = ranked.sort_values("model_rank")
    if ranked.empty:
        return {}
    top = ranked.iloc[0]
    return {
        "site_id": str(top.get("site_id", "")),
        "ports_now": int(top.get("ports_now", 0)) if pd.notna(top.get("ports_now", None)) else None,
        "future_ready_capacity": int(top.get("future_ready_capacity", 0)) if pd.notna(top.get("future_ready_capacity", None)) else None,
        "expansion_strategy": str(top.get("expansion_strategy", "")),
    }


def build_success_marker(input_path: Path, results_path: Path, quality_path: Path, electrical_path: Path, right_sizing_path: Path) -> dict[str, Any]:
    results = read_csv_if_exists(results_path)
    quality = read_csv_if_exists(quality_path)
    electrical = read_csv_if_exists(electrical_path)
    right_sizing = read_csv_if_exists(right_sizing_path)
    outputs = [file_record(path) for path in EXPECTED_OUTPUTS]
    missing_outputs = [record["path"] for record in outputs if not record["exists"] or record["size_bytes"] == 0]
    return {
        "workflow": "v2_expansion_planning",
        "status": "success" if not missing_outputs else "incomplete",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path),
        "input_exists": input_path.exists(),
        "site_count": int(len(results)) if not results.empty else 0,
        "top_site": top_site_summary(results),
        "quality_counts": quality_counts(quality),
        "electrical_risk_counts": electrical_counts(electrical),
        "top_right_sizing": right_sizing_top_summary(right_sizing),
        "expected_outputs_count": len(outputs),
        "generated_outputs_count": len(outputs) - len(missing_outputs),
        "missing_or_empty_outputs": missing_outputs,
        "outputs": outputs,
        "notes": [
            "This marker confirms that the local V2 workflow outputs were generated.",
            "It is a workflow reproducibility artifact, not an engineering or permitting approval.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write a V2 workflow success marker and output manifest.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="V2 input CSV path.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="V2 site results CSV path.")
    parser.add_argument("--quality", default=DEFAULT_QUALITY, help="V2 data quality CSV path.")
    parser.add_argument("--electrical-summary", default=DEFAULT_ELECTRICAL_SUMMARY, help="V2 electrical risk summary CSV path.")
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING, help="V2 right-sizing scenario CSV path.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output success marker JSON path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    results_path = Path(args.results)
    quality_path = Path(args.quality)
    electrical_path = Path(args.electrical_summary)
    right_sizing_path = Path(args.right_sizing)
    output_path = Path(args.output)
    marker = build_success_marker(input_path, results_path, quality_path, electrical_path, right_sizing_path)
    ensure_parent_dir(output_path)
    output_path.write_text(json.dumps(marker, indent=2), encoding="utf-8")
    print("V2 WORKFLOW SUCCESS MARKER")
    print("--------------------------")
    print(f"Status: {marker['status']}")
    print(f"Input file: {input_path}")
    print(f"Site count: {marker['site_count']}")
    print(f"Top site: {marker.get('top_site', {}).get('site_id', 'not available')}")
    print(f"Generated outputs: {marker['generated_outputs_count']}/{marker['expected_outputs_count']}")
    print(f"Saved marker: {output_path}")
    if marker["missing_or_empty_outputs"]:
        print("Missing or empty outputs:")
        for path in marker["missing_or_empty_outputs"]:
            print(f"- {path}")


if __name__ == "__main__":
    main()
