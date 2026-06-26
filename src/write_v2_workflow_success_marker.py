from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

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
    "data/outputs/v2_sensitivity_results.csv",
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
    "data/outputs/v2_port_sizing_scenario_results.csv",
    "data/outputs/v2_port_sizing_scenario_summary.csv",
    "data/outputs/v2_port_sizing_scenario_report.md",
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
    "data/outputs/charts/v2_port_sizing_scenario_heatmap.png",
    "docs/assets/charts/v2_site_decision_map_readme.png",
]


def ensure_parent_dir(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def file_record(path_text):
    path = Path(path_text)
    exists = path.exists()
    return {"path": path_text, "exists": exists, "size_bytes": path.stat().st_size if exists else 0}


def read_csv_if_exists(path):
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def top_site_summary(results):
    if results.empty or "model_rank" not in results.columns:
        return {}
    ranked = results.copy()
    ranked["model_rank"] = pd.to_numeric(ranked["model_rank"], errors="coerce")
    ranked = ranked.sort_values("model_rank")
    top = ranked.iloc[0]
    return {
        "site_id": str(top.get("site_id", "")),
        "site_name": str(top.get("site_name", "")),
        "model_rank": int(top.get("model_rank", 0)) if pd.notna(top.get("model_rank", None)) else None,
        "readiness_score": float(top.get("readiness_score", 0)) if pd.notna(top.get("readiness_score", None)) else None,
        "recommendation_tier": str(top.get("recommendation_tier", "")),
        "action_label": str(top.get("action_label", "")),
    }


def value_counts(table, column, levels):
    if table.empty or column not in table.columns:
        return {}
    counts = table[column].astype(str).value_counts().to_dict()
    return {level: int(counts.get(level, 0)) for level in levels}


def right_sizing_top_summary(right_sizing):
    if right_sizing.empty or "model_rank" not in right_sizing.columns:
        return {}
    ranked = right_sizing.copy()
    ranked["model_rank"] = pd.to_numeric(ranked["model_rank"], errors="coerce")
    ranked = ranked.sort_values("model_rank")
    top = ranked.iloc[0]
    return {
        "site_id": str(top.get("site_id", "")),
        "ports_now": int(top.get("ports_now", 0)) if pd.notna(top.get("ports_now", None)) else None,
        "future_ready_capacity": int(top.get("future_ready_capacity", 0)) if pd.notna(top.get("future_ready_capacity", None)) else None,
        "expansion_strategy": str(top.get("expansion_strategy", "")),
    }


def build_success_marker(input_path, results_path, quality_path, electrical_path, right_sizing_path):
    input_path = Path(input_path)
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
        "quality_counts": value_counts(quality, "severity", ["ERROR", "WARNING", "REVIEW", "INFO"]),
        "electrical_risk_counts": value_counts(electrical, "electrical_risk_level", ["low", "medium", "high"]),
        "top_right_sizing": right_sizing_top_summary(right_sizing),
        "workflow_step_count": 24,
        "expected_outputs_count": len(outputs),
        "generated_outputs_count": len(outputs) - len(missing_outputs),
        "missing_or_empty_outputs": missing_outputs,
        "outputs": outputs,
        "notes": [
            "Includes the detailed sensitivity output.",
            "Includes the port-sizing scenario analysis layer.",
            "Planning artifact only; not an approval document.",
        ],
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Write a V2 workflow output manifest.")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--results", default=DEFAULT_RESULTS)
    parser.add_argument("--quality", default=DEFAULT_QUALITY)
    parser.add_argument("--electrical-summary", default=DEFAULT_ELECTRICAL_SUMMARY)
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output)
    marker = build_success_marker(args.input, args.results, args.quality, args.electrical_summary, args.right_sizing)
    ensure_parent_dir(output_path)
    output_path.write_text(json.dumps(marker, indent=2), encoding="utf-8")
    print("V2 WORKFLOW SUCCESS MARKER")
    print("--------------------------")
    print(f"Status: {marker['status']}")
    print(f"Input file: {args.input}")
    print(f"Workflow steps: {marker['workflow_step_count']}")
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
