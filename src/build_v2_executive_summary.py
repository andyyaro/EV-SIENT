"""Build a consolidated V2 executive site summary table."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_RESULTS = "data/outputs/v2_site_results.csv"
DEFAULT_ELECTRICAL_SUMMARY = "data/outputs/v2_electrical_risk_summary.csv"
DEFAULT_RIGHT_SIZING = "data/outputs/v2_right_sizing_scenarios.csv"
DEFAULT_PORT_SIMULATION = "data/outputs/v2_port_utilization_simulation.csv"
DEFAULT_PORT_SIZING_SCENARIOS = "data/outputs/v2_port_sizing_scenario_results.csv"
DEFAULT_RIGHT_SIZING_VALIDATION = "data/outputs/v2_right_sizing_validation.csv"
DEFAULT_OUTPUT = "data/outputs/v2_executive_site_summary.csv"
DEFAULT_REPORT = "data/outputs/v2_executive_site_summary.md"

OUTPUT_COLUMNS = [
    "model_rank", "site_id", "site_name", "readiness_score", "data_confidence_level",
    "recommendation_tier", "action_label", "electrical_risk_level", "expected_electrical_rank",
    "expected_electrical_score", "ports_now", "ports_2035_base", "ports_2035_high",
    "ports_2050_base", "ports_2050_high", "future_ready_capacity", "expansion_strategy",
    "sim_min_ports_current", "sim_utilization_current_at_ports_now", "sim_wait_current_at_ports_now",
    "sim_queue_risk_current_at_ports_now", "sim_min_ports_2035_high", "sim_min_ports_2050_high",
    "sim_status_2050_high_at_future_ready", "scenario_max_min_ports_2050_high",
    "scenario_future_capacity_gap", "scenario_sensitivity_level", "scenario_stress_note",
    "current_alignment", "future_alignment", "simulation_supported_strategy",
    "right_sizing_validation_note", "major_review_flags", "planning_recommendation",
    "data_needed_next",
]


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_required_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required {label} file not found: {path}")
    return pd.read_csv(path)


def read_optional_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def normalize_electrical_columns(electrical: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    if "electrical_adjusted_rank" in electrical.columns and "expected_rank" not in electrical.columns:
        rename_map["electrical_adjusted_rank"] = "expected_rank"
    if "electrical_adjusted_score" in electrical.columns and "expected_score" not in electrical.columns:
        rename_map["electrical_adjusted_score"] = "expected_score"
    return electrical.rename(columns=rename_map) if rename_map else electrical


def semicolon_join(items: list[str]) -> str:
    cleaned, seen = [], set()
    for item in items:
        text = str(item).strip()
        if text and text.lower() != "nan" and text not in seen:
            cleaned.append(text)
            seen.add(text)
    return "; ".join(cleaned)


def build_review_flags(row: pd.Series) -> str:
    flags: list[str] = []
    review_reason = str(row.get("review_reason", "")).strip()
    if review_reason and review_reason.lower() != "nan":
        flags.extend([part.strip() for part in review_reason.split(";") if part.strip()])

    risk = str(row.get("electrical_risk_level", "")).lower()
    if risk == "high":
        flags.append("High electrical-risk screen")
    elif risk == "medium":
        flags.append("Electrical assumptions need confirmation")

    strategy = str(row.get("expansion_strategy", "")).lower()
    tier = str(row.get("recommendation_tier", "")).lower()
    if "high-review" in tier:
        flags.append("High-review candidate")
    if "garage" in tier or "garage" in strategy:
        flags.append("Garage / Fire Marshal / AHJ review likely")
    if "electrical_review" in strategy:
        flags.append("Electrical review before expansion")
    if "monitor_due_to_nearby_supply" in strategy:
        flags.append("Nearby charging supply may reduce priority")
    if "do_not_advance" in strategy:
        flags.append("Do not advance as general-public buildout")

    if str(row.get("simulation_supported_strategy", "")).lower() == "needs_review":
        flags.append("Right-sizing and simulation need review")
    if str(row.get("future_alignment", "")).lower() == "possibly_low_future_capacity":
        flags.append("Future-ready capacity may be low in 2050 high case")
    if str(row.get("scenario_sensitivity_level", "")).lower() == "combined_stress_sensitive":
        flags.append("Combined-stress scenario may require extra future-ready capacity")
    elif str(row.get("scenario_sensitivity_level", "")).lower() == "scenario_sensitive":
        flags.append("Scenario stress test may require extra future-ready capacity")

    try:
        if float(row.get("public_access", 1)) < 1:
            flags.append("Public access/use case needs confirmation")
    except (TypeError, ValueError):
        pass
    return semicolon_join(flags or ["Standard site screening needed"])


def pick_min_ports(group: pd.DataFrame) -> object:
    if group.empty:
        return ""
    usable = group[group["capacity_status"] != "underbuilt"]
    if not usable.empty:
        return int(usable.sort_values("port_count").iloc[0]["port_count"])
    return int(group.sort_values(["estimated_wait_min", "port_count"], ascending=[True, False]).iloc[0]["port_count"])


def summarize_port_simulation(simulation: pd.DataFrame) -> pd.DataFrame:
    if simulation.empty or "site_id" not in simulation.columns:
        return pd.DataFrame(columns=["site_id"])
    rows = []
    for site_id, site_rows in simulation.groupby("site_id", dropna=False):
        current = site_rows[site_rows["demand_case"] == "current"].copy()
        high_2035 = site_rows[site_rows["demand_case"] == "2035_high"].copy()
        high_2050 = site_rows[site_rows["demand_case"] == "2050_high"].copy()
        current_ports_now = current[current["is_ports_now"] == True] if "is_ports_now" in current.columns else pd.DataFrame()
        future_ready = high_2050[high_2050["is_future_ready_capacity"] == True] if "is_future_ready_capacity" in high_2050.columns else pd.DataFrame()
        if current_ports_now.empty and not current.empty:
            current_ports_now = current.sort_values("port_count").head(1)
        if future_ready.empty and not high_2050.empty:
            future_ready = high_2050.sort_values("port_count").tail(1)
        current_row = current_ports_now.iloc[0] if not current_ports_now.empty else None
        future_row = future_ready.iloc[0] if not future_ready.empty else None
        rows.append({
            "site_id": site_id,
            "sim_min_ports_current": pick_min_ports(current),
            "sim_utilization_current_at_ports_now": current_row.get("utilization_pct", "") if current_row is not None else "",
            "sim_wait_current_at_ports_now": current_row.get("estimated_wait_min", "") if current_row is not None else "",
            "sim_queue_risk_current_at_ports_now": current_row.get("queue_risk_level", "") if current_row is not None else "",
            "sim_min_ports_2035_high": pick_min_ports(high_2035),
            "sim_min_ports_2050_high": pick_min_ports(high_2050),
            "sim_status_2050_high_at_future_ready": future_row.get("capacity_status", "") if future_row is not None else "",
        })
    return pd.DataFrame(rows)


def sentence_join(items: list[str]) -> str:
    cleaned = [item for item in items if item]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return ", ".join(cleaned[:-1]) + f", and {cleaned[-1]}"


def lower_first(text: str) -> str:
    if not text:
        return text
    return text[:1].lower() + text[1:]


def summarize_port_sizing_scenarios(scenarios: pd.DataFrame) -> pd.DataFrame:
    """Summarize the scenario stress-test results at one row per site."""
    output_columns = [
        "site_id", "scenario_max_min_ports_2050_high", "scenario_future_capacity_gap",
        "scenario_sensitivity_level", "scenario_stress_note",
    ]
    required = {"site_id", "scenario_name", "scenario_min_ports_2050_high", "future_capacity_gap"}
    missing = sorted(required - set(scenarios.columns))
    if scenarios.empty or missing:
        return pd.DataFrame(columns=output_columns)

    data = scenarios.copy()
    data["scenario_min_ports_2050_high"] = pd.to_numeric(data["scenario_min_ports_2050_high"], errors="coerce").fillna(0)
    data["future_capacity_gap"] = pd.to_numeric(data["future_capacity_gap"], errors="coerce").fillna(0)

    rows = []
    for site_id, site_rows in data.groupby("site_id", dropna=False):
        max_min_ports = int(site_rows["scenario_min_ports_2050_high"].max())
        max_gap = int(site_rows["future_capacity_gap"].max())
        gap_rows = site_rows[site_rows["future_capacity_gap"] > 0].copy()

        if gap_rows.empty:
            sensitivity = "robust"
            note = "Future-ready capacity covers all tested port-sizing scenarios."
        else:
            scenario_names = set(gap_rows["scenario_name"].astype(str))
            sensitivity = "combined_stress_sensitive" if scenario_names == {"combined_stress"} else "scenario_sensitive"
            label_column = "scenario_label" if "scenario_label" in gap_rows.columns else "scenario_name"
            labels = gap_rows[label_column].astype(str).drop_duplicates().tolist()
            scenario_text = lower_first(sentence_join(labels))
            port_word = "port" if max_gap == 1 else "ports"
            if sensitivity == "combined_stress_sensitive":
                note = f"Stable under normal scenarios, but {scenario_text} may require {max_gap} additional future-ready {port_word}."
            else:
                note = f"{sentence_join(labels)} may require up to {max_gap} additional future-ready {port_word}."

        rows.append({
            "site_id": site_id,
            "scenario_max_min_ports_2050_high": max_min_ports,
            "scenario_future_capacity_gap": max_gap,
            "scenario_sensitivity_level": sensitivity,
            "scenario_stress_note": note,
        })
    return pd.DataFrame(rows, columns=output_columns)


def build_executive_summary(
    results: pd.DataFrame,
    electrical: pd.DataFrame,
    right_sizing: pd.DataFrame,
    port_simulation: pd.DataFrame,
    port_sizing_scenarios: pd.DataFrame,
    validation: pd.DataFrame,
) -> pd.DataFrame:
    required_results = {"site_id", "model_rank", "site_name", "readiness_score"}
    missing = required_results - set(results.columns)
    if missing:
        raise ValueError(f"V2 site results are missing required columns: {sorted(missing)}")

    electrical = normalize_electrical_columns(electrical)
    electrical_keep = [c for c in ["site_id", "electrical_risk_level", "expected_rank", "expected_score"] if c in electrical.columns]
    right_keep = [c for c in ["site_id", "ports_now", "ports_2035_base", "ports_2035_high", "ports_2050_base", "ports_2050_high", "future_ready_capacity", "expansion_strategy"] if c in right_sizing.columns]
    if "site_id" not in electrical_keep:
        raise ValueError("Electrical summary is missing site_id.")
    if "site_id" not in right_keep:
        raise ValueError("Right-sizing output is missing site_id.")

    merged = results.merge(electrical[electrical_keep], on="site_id", how="left")
    merged = merged.merge(right_sizing[right_keep], on="site_id", how="left")
    port_summary = summarize_port_simulation(port_simulation)
    if not port_summary.empty:
        merged = merged.merge(port_summary, on="site_id", how="left")
    scenario_summary = summarize_port_sizing_scenarios(port_sizing_scenarios)
    if not scenario_summary.empty:
        merged = merged.merge(scenario_summary, on="site_id", how="left")
    if not validation.empty and "site_id" in validation.columns:
        validation_keep = [c for c in ["site_id", "current_alignment", "future_alignment", "simulation_supported_strategy", "right_sizing_validation_note"] if c in validation.columns]
        merged = merged.merge(validation[validation_keep], on="site_id", how="left")
    merged = merged.rename(columns={"expected_rank": "expected_electrical_rank", "expected_score": "expected_electrical_score"})
    for col in OUTPUT_COLUMNS:
        if col not in merged.columns:
            merged[col] = ""
    merged["major_review_flags"] = merged.apply(build_review_flags, axis=1)
    merged["model_rank"] = pd.to_numeric(merged["model_rank"], errors="coerce")
    return merged.sort_values("model_rank")[OUTPUT_COLUMNS]


def markdown_table(data: pd.DataFrame, columns: list[str]) -> str:
    if data.empty:
        return "_No executive summary data available._"
    view = data[[col for col in columns if col in data.columns]].copy()
    view.columns = [col.replace("_", " ") for col in view.columns]
    lines = ["| " + " | ".join(view.columns) + " |", "| " + " | ".join(["---"] * len(view.columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("|", "/") for c in view.columns) + " |")
    return "\n".join(lines)


def build_markdown_report(summary: pd.DataFrame) -> str:
    top = summary.iloc[0] if not summary.empty else None
    top_text = "No top site available."
    if top is not None:
        top_text = f"Top candidate: **{top['site_id']} — {top['site_name']}** with readiness score **{top['readiness_score']}**."
    cols = [
        "model_rank", "site_id", "ports_now", "sim_min_ports_current",
        "current_alignment", "future_ready_capacity", "sim_min_ports_2050_high",
        "scenario_max_min_ports_2050_high", "scenario_future_capacity_gap",
        "scenario_sensitivity_level", "future_alignment", "simulation_supported_strategy",
        "major_review_flags",
    ]
    scenario_cols = ["model_rank", "site_id", "future_ready_capacity", "scenario_max_min_ports_2050_high", "scenario_future_capacity_gap", "scenario_sensitivity_level", "scenario_stress_note"]
    return f"""# V2 Executive Site Summary

{top_text}

This table combines ranking, electrical risk, right-sizing, port-utilization simulation, port-sizing scenario stress testing, and right-sizing validation outputs.

## Executive decision table

{markdown_table(summary, cols)}

## Port-sizing scenario notes

{markdown_table(summary, scenario_cols)}

## Notes

- `current_alignment` compares `ports_now` with simulated current-demand need.
- `future_alignment` compares `future_ready_capacity` with simulated 2050 high-growth need.
- `scenario_sensitivity_level` summarizes whether alternate port-sizing scenarios expose a future-ready capacity gap.
- `scenario_future_capacity_gap` is the largest extra future-ready port count identified across tested scenarios.
- These fields are planning-screen signals, not final design or permitting results.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a consolidated V2 executive site summary table.")
    parser.add_argument("--results", default=DEFAULT_RESULTS)
    parser.add_argument("--electrical-summary", default=DEFAULT_ELECTRICAL_SUMMARY)
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING)
    parser.add_argument("--port-simulation", default=DEFAULT_PORT_SIMULATION)
    parser.add_argument("--port-sizing-scenarios", default=DEFAULT_PORT_SIZING_SCENARIOS)
    parser.add_argument("--right-sizing-validation", default=DEFAULT_RIGHT_SIZING_VALIDATION)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_executive_summary(
        read_required_csv(Path(args.results), "V2 site results"),
        read_required_csv(Path(args.electrical_summary), "V2 electrical summary"),
        read_required_csv(Path(args.right_sizing), "V2 right-sizing"),
        read_optional_csv(Path(args.port_simulation)),
        read_optional_csv(Path(args.port_sizing_scenarios)),
        read_optional_csv(Path(args.right_sizing_validation)),
    )
    output_path = Path(args.output)
    report_path = Path(args.report)
    ensure_parent_dir(output_path)
    ensure_parent_dir(report_path)
    summary.to_csv(output_path, index=False)
    report_path.write_text(build_markdown_report(summary), encoding="utf-8")
    print("V2 EXECUTIVE SITE SUMMARY")
    print("-------------------------")
    print(f"Rows: {len(summary)}")
    print(f"Saved CSV: {output_path}")
    print(f"Saved report: {report_path}")
    print()
    preview_cols = [
        "model_rank", "site_id", "ports_now", "sim_min_ports_current", "current_alignment",
        "future_ready_capacity", "sim_min_ports_2050_high", "scenario_max_min_ports_2050_high",
        "scenario_future_capacity_gap", "scenario_sensitivity_level",
    ]
    print(summary[preview_cols].to_string(index=False))


if __name__ == "__main__":
    main()
