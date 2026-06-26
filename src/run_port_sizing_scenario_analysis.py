"""Run V2 port-sizing scenario analysis.

This is the port-sizing counterpart to the scoring-profile analysis. It asks:
if charging duration, charging-window, peak-demand, or future-demand assumptions
change, do the recommended port counts still look reasonable?
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

try:
    from chart_style import apply_chart_style

    SELECTED_FONT = apply_chart_style()
except Exception:  # pragma: no cover - chart style should not block analysis
    SELECTED_FONT = None

from run_port_utilization_simulation import (
    PORT_OPTIONS,
    classify_capacity_status,
    classify_queue_risk,
    estimate_wait_minutes,
)

DEFAULT_RESULTS = "data/outputs/v2_site_results.csv"
DEFAULT_RIGHT_SIZING = "data/outputs/v2_right_sizing_scenarios.csv"
DEFAULT_SCENARIOS = "data/inputs/v2_port_sizing_scenarios.csv"
DEFAULT_OUTPUT = "data/outputs/v2_port_sizing_scenario_results.csv"
DEFAULT_SUMMARY = "data/outputs/v2_port_sizing_scenario_summary.csv"
DEFAULT_REPORT = "data/outputs/v2_port_sizing_scenario_report.md"
DEFAULT_CHART = "data/outputs/charts/v2_port_sizing_scenario_heatmap.png"

DEMAND_CASE_COLUMNS = {
    "current": "current_multiplier",
    "2035_high": "2035_high_multiplier",
    "2050_high": "2050_high_multiplier",
}

REQUIRED_SCENARIO_COLUMNS = [
    "scenario_name",
    "scenario_label",
    "scenario_description",
    "avg_charge_hours",
    "charging_window_hours",
    "peak_factor",
    "current_multiplier",
    "2035_high_multiplier",
    "2050_high_multiplier",
]


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_required_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required {label} file not found: {path}")
    return pd.read_csv(path)


def validate_scenarios(scenarios: pd.DataFrame) -> None:
    missing = sorted(set(REQUIRED_SCENARIO_COLUMNS) - set(scenarios.columns))
    if missing:
        raise ValueError(f"Scenario input is missing required columns: {missing}")
    if scenarios["scenario_name"].astype(str).duplicated().any():
        duplicates = scenarios.loc[scenarios["scenario_name"].astype(str).duplicated(), "scenario_name"].tolist()
        raise ValueError(f"Scenario names must be unique. Duplicates: {duplicates}")
    numeric_columns = [
        "avg_charge_hours",
        "charging_window_hours",
        "peak_factor",
        "current_multiplier",
        "2035_high_multiplier",
        "2050_high_multiplier",
    ]
    for column in numeric_columns:
        values = pd.to_numeric(scenarios[column], errors="coerce")
        if values.isna().any() or (values <= 0).any():
            raise ValueError(f"Scenario column must contain positive numeric values: {column}")


def evaluate_port_option(
    sessions_day: float,
    port_count: int,
    avg_charge_hours: float,
    charging_window_hours: float,
    peak_factor: float,
) -> dict[str, Any]:
    utilization_pct = 0.0
    peak_demand_ratio = 0.0
    if port_count > 0 and charging_window_hours > 0:
        utilization_pct = (sessions_day * avg_charge_hours) / (port_count * charging_window_hours) * 100
        peak_demand_ratio = (sessions_day * avg_charge_hours * peak_factor) / (port_count * charging_window_hours)
    wait_min = estimate_wait_minutes(peak_demand_ratio)
    return {
        "port_count": int(port_count),
        "utilization_pct": round(utilization_pct, 1),
        "peak_demand_ratio": round(peak_demand_ratio, 3),
        "estimated_wait_min": float(wait_min),
        "queue_risk_level": classify_queue_risk(peak_demand_ratio),
        "capacity_status": classify_capacity_status(utilization_pct, wait_min),
    }


def choose_min_ports_for_case(
    sessions_day: float,
    avg_charge_hours: float,
    charging_window_hours: float,
    peak_factor: float,
) -> dict[str, Any]:
    options = [evaluate_port_option(sessions_day, ports, avg_charge_hours, charging_window_hours, peak_factor) for ports in PORT_OPTIONS]
    usable = [row for row in options if row["capacity_status"] != "underbuilt"]
    if usable:
        return sorted(usable, key=lambda row: row["port_count"])[0]
    # If every tested option is still underbuilt, use the least-bad tested option:
    # lowest wait first, then largest port count as the tie-breaker.
    return sorted(options, key=lambda row: (row["estimated_wait_min"], -row["port_count"]))[0]


def status_at_port_count(
    sessions_day: float,
    port_count: int,
    avg_charge_hours: float,
    charging_window_hours: float,
    peak_factor: float,
) -> dict[str, Any]:
    return evaluate_port_option(sessions_day, int(port_count), avg_charge_hours, charging_window_hours, peak_factor)


def alignment_label(recommended_min_ports: int, planned_ports: int, low_label: str, match_label: str, conservative_label: str) -> str:
    if planned_ports < recommended_min_ports:
        return low_label
    if planned_ports == recommended_min_ports:
        return match_label
    return conservative_label


def build_results(results: pd.DataFrame, right_sizing: pd.DataFrame, scenarios: pd.DataFrame) -> pd.DataFrame:
    if "site_id" not in results.columns or "expected_sessions_day" not in results.columns:
        raise ValueError("V2 results must include site_id and expected_sessions_day.")
    if "site_id" not in right_sizing.columns:
        raise ValueError("V2 right-sizing output must include site_id.")

    right_by_id = right_sizing.set_index("site_id", drop=False)
    ranked = results.copy()
    ranked["model_rank"] = pd.to_numeric(ranked["model_rank"], errors="coerce")
    ranked = ranked.sort_values("model_rank")

    rows: list[dict[str, Any]] = []
    for _, scenario in scenarios.iterrows():
        scenario_name = str(scenario["scenario_name"])
        scenario_label = str(scenario["scenario_label"])
        scenario_description = str(scenario["scenario_description"])
        avg_charge_hours = float(scenario["avg_charge_hours"])
        charging_window_hours = float(scenario["charging_window_hours"])
        peak_factor = float(scenario["peak_factor"])

        for _, site in ranked.iterrows():
            site_id = str(site["site_id"])
            if site_id not in right_by_id.index:
                raise ValueError(f"Right-sizing output is missing site_id: {site_id}")
            sizing = right_by_id.loc[site_id]
            base_sessions = float(site.get("expected_sessions_day", 0) or 0)
            ports_now = int(sizing.get("ports_now", 0) or 0)
            future_ready = int(sizing.get("future_ready_capacity", 0) or 0)

            case_outputs = {}
            for demand_case, multiplier_column in DEMAND_CASE_COLUMNS.items():
                multiplier = float(scenario[multiplier_column])
                sessions_day = base_sessions * multiplier
                best = choose_min_ports_for_case(sessions_day, avg_charge_hours, charging_window_hours, peak_factor)
                case_outputs[demand_case] = {
                    "sessions_day": round(sessions_day, 3),
                    "min_ports": int(best["port_count"]),
                    "utilization_pct": float(best["utilization_pct"]),
                    "estimated_wait_min": float(best["estimated_wait_min"]),
                    "queue_risk_level": best["queue_risk_level"],
                    "capacity_status": best["capacity_status"],
                }

            current_at_ports_now = status_at_port_count(
                case_outputs["current"]["sessions_day"], ports_now, avg_charge_hours, charging_window_hours, peak_factor
            )
            future_at_ready = status_at_port_count(
                case_outputs["2050_high"]["sessions_day"], future_ready, avg_charge_hours, charging_window_hours, peak_factor
            )
            current_min = case_outputs["current"]["min_ports"]
            min_2035 = case_outputs["2035_high"]["min_ports"]
            min_2050 = case_outputs["2050_high"]["min_ports"]
            future_gap = max(0, min_2050 - future_ready)
            current_gap = max(0, current_min - ports_now)
            future_alignment = alignment_label(
                min_2050,
                future_ready,
                "scenario_exceeds_future_ready_capacity",
                "future_ready_capacity_matches_scenario",
                "future_ready_capacity_covers_scenario",
            )
            current_alignment = alignment_label(
                current_min,
                ports_now,
                "current_ports_may_be_low",
                "current_ports_match_scenario",
                "current_ports_conservative_for_scenario",
            )

            rows.append(
                {
                    "scenario_name": scenario_name,
                    "scenario_label": scenario_label,
                    "scenario_description": scenario_description,
                    "model_rank": int(site["model_rank"]),
                    "site_id": site_id,
                    "site_name": site.get("site_name", ""),
                    "readiness_score": site.get("readiness_score", ""),
                    "base_expected_sessions_day": round(base_sessions, 3),
                    "avg_charge_hours": avg_charge_hours,
                    "charging_window_hours": charging_window_hours,
                    "peak_factor": peak_factor,
                    "current_multiplier": float(scenario["current_multiplier"]),
                    "2035_high_multiplier": float(scenario["2035_high_multiplier"]),
                    "2050_high_multiplier": float(scenario["2050_high_multiplier"]),
                    "ports_now": ports_now,
                    "future_ready_capacity": future_ready,
                    "scenario_min_ports_current": current_min,
                    "scenario_min_ports_2035_high": min_2035,
                    "scenario_min_ports_2050_high": min_2050,
                    "current_capacity_gap": current_gap,
                    "future_capacity_gap": future_gap,
                    "current_alignment": current_alignment,
                    "future_capacity_alignment": future_alignment,
                    "current_status_at_ports_now": current_at_ports_now["capacity_status"],
                    "current_wait_at_ports_now": current_at_ports_now["estimated_wait_min"],
                    "current_utilization_at_ports_now": current_at_ports_now["utilization_pct"],
                    "future_status_at_future_ready": future_at_ready["capacity_status"],
                    "future_wait_at_future_ready": future_at_ready["estimated_wait_min"],
                    "future_utilization_at_future_ready": future_at_ready["utilization_pct"],
                    "future_queue_risk_at_future_ready": future_at_ready["queue_risk_level"],
                }
            )
    return pd.DataFrame(rows)


def summarize_results(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scenario_name, group in results.groupby("scenario_name", sort=False):
        group = group.copy()
        future_exceeded = group[group["future_capacity_alignment"] == "scenario_exceeds_future_ready_capacity"]
        current_low = group[group["current_alignment"] == "current_ports_may_be_low"]
        top_gap_sites = future_exceeded.sort_values(["future_capacity_gap", "model_rank"], ascending=[False, True])["site_id"].head(5).tolist()
        rows.append(
            {
                "scenario_name": scenario_name,
                "scenario_label": group["scenario_label"].iloc[0],
                "site_count": int(group["site_id"].nunique()),
                "sites_current_ports_may_be_low": int(len(current_low)),
                "sites_future_ready_capacity_exceeded": int(len(future_exceeded)),
                "max_scenario_min_ports_2050_high": int(group["scenario_min_ports_2050_high"].max()),
                "average_scenario_min_ports_2050_high": round(float(group["scenario_min_ports_2050_high"].mean()), 2),
                "max_future_capacity_gap": int(group["future_capacity_gap"].max()),
                "top_future_gap_sites": ", ".join(top_gap_sites) if top_gap_sites else "None",
            }
        )
    return pd.DataFrame(rows)


def markdown_table(data: pd.DataFrame, columns: list[str]) -> str:
    if data.empty:
        return "_No data available._"
    view = data[[col for col in columns if col in data.columns]].copy()
    view.columns = [col.replace("_", " ") for col in view.columns]
    header = "| " + " | ".join(view.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = []
    for _, row in view.iterrows():
        rows.append("| " + " | ".join(str(row[col]).replace("|", "/") for col in view.columns) + " |")
    return "\n".join([header, separator] + rows)


def build_headline(summary: pd.DataFrame) -> str:
    if summary.empty:
        return "No scenario summary was generated."
    stable = summary[summary["sites_future_ready_capacity_exceeded"] == 0]
    stress = summary[summary["sites_future_ready_capacity_exceeded"] > 0]
    if stress.empty:
        return "All tested port-sizing scenarios are covered by the current future-ready capacity plan."
    stress_names = ", ".join(stress["scenario_name"].astype(str).tolist())
    max_gap = int(stress["max_future_capacity_gap"].max())
    total_sites = int(stress["sites_future_ready_capacity_exceeded"].max())
    port_word = "port" if max_gap == 1 else "ports"
    return (
        f"The current future-ready plan covers {len(stable)} of {len(summary)} scenarios. "
        f"Capacity gaps appear only in {stress_names}, affecting up to {total_sites} sites with a maximum gap of {max_gap} {port_word}."
    )


def build_report(results: pd.DataFrame, summary: pd.DataFrame, scenarios: pd.DataFrame) -> str:
    stress = results[results["future_capacity_alignment"] == "scenario_exceeds_future_ready_capacity"].copy()
    if not stress.empty:
        stress = stress.sort_values(["scenario_name", "future_capacity_gap", "model_rank"], ascending=[True, False, True]).head(12)
    return f"""# V2 Port-Sizing Scenario Analysis

This report is the port-sizing counterpart to the scoring-profile analysis.

It asks whether the recommended port counts remain reasonable when charging duration, usable daily charging window, peak-demand concentration, and future-demand multipliers change.

## Headline finding

{build_headline(summary)}

## Scenario inputs

{markdown_table(scenarios, ['scenario_name', 'scenario_label', 'avg_charge_hours', 'charging_window_hours', 'peak_factor', 'current_multiplier', '2035_high_multiplier', '2050_high_multiplier'])}

## Scenario summary

{markdown_table(summary, ['scenario_name', 'scenario_label', 'site_count', 'sites_current_ports_may_be_low', 'sites_future_ready_capacity_exceeded', 'max_scenario_min_ports_2050_high', 'average_scenario_min_ports_2050_high', 'max_future_capacity_gap', 'top_future_gap_sites'])}

## Sites where a scenario exceeds future-ready capacity

{markdown_table(stress, ['scenario_name', 'model_rank', 'site_id', 'future_ready_capacity', 'scenario_min_ports_2050_high', 'future_capacity_gap', 'future_capacity_alignment'])}

## How to read this

- `scenario_min_ports_2050_high` is the smallest tested port count that avoids an underbuilt result under that scenario's 2050 high-demand assumptions.
- `future_ready_capacity_covers_scenario` means the current future-ready plan is at least as large as the scenario minimum.
- `scenario_exceeds_future_ready_capacity` means the scenario may require more ports than the current future-ready plan.
- This is a planning stress test, not an engineering design or utility approval.
"""


def create_heatmap(results: pd.DataFrame, output_path: Path) -> None:
    data = results.copy()
    data["site_label"] = data["model_rank"].astype(int).astype(str) + ". " + data["site_id"].astype(str)
    scenario_labels = data[["scenario_name", "scenario_label"]].drop_duplicates().set_index("scenario_name")["scenario_label"].to_dict()
    ordered_sites = data.sort_values("model_rank")["site_label"].drop_duplicates().tolist()
    ordered_scenarios = data["scenario_name"].drop_duplicates().tolist()
    pivot = data.pivot(index="site_label", columns="scenario_name", values="scenario_min_ports_2050_high").reindex(
        index=ordered_sites, columns=ordered_scenarios
    )

    ensure_parent_dir(output_path)
    fig_width = max(11, 1.45 * len(ordered_scenarios) + 4)
    fig_height = max(6.5, 0.42 * len(ordered_sites) + 2.6)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    image = ax.imshow(pivot.values, aspect="auto")
    ax.set_title("V2 Port-Sizing Scenario Stress Test")
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Candidate site")
    ax.set_xticks(range(len(ordered_scenarios)))
    ax.set_xticklabels([scenario_labels.get(name, name).replace(" ", "\n") for name in ordered_scenarios], rotation=0, ha="center")
    ax.set_yticks(range(len(ordered_sites)))
    ax.set_yticklabels(ordered_sites)

    midpoint = (float(pivot.values.min()) + float(pivot.values.max())) / 2
    for y_index, site_label in enumerate(ordered_sites):
        for x_index, scenario_name in enumerate(ordered_scenarios):
            value = pivot.loc[site_label, scenario_name]
            text_color = "black" if float(value) > midpoint else "white"
            ax.text(x_index, y_index, str(int(value)), ha="center", va="center", color=text_color, fontweight="bold")

    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("Minimum ports, 2050 high-demand case")
    fig.text(
        0.5,
        0.01,
        "Numbers show the smallest tested port count that avoids an underbuilt result under each scenario.",
        ha="center",
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run V2 port-sizing scenario analysis.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="V2 site results CSV.")
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING, help="V2 right-sizing scenario CSV.")
    parser.add_argument("--scenarios", default=DEFAULT_SCENARIOS, help="Port-sizing scenario assumptions CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Detailed scenario results CSV output.")
    parser.add_argument("--summary-output", default=DEFAULT_SUMMARY, help="Scenario summary CSV output.")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Scenario Markdown report output.")
    parser.add_argument("--chart", default=DEFAULT_CHART, help="Scenario heatmap chart output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = read_required_csv(Path(args.results), "V2 site results")
    right_sizing = read_required_csv(Path(args.right_sizing), "V2 right-sizing")
    scenarios = read_required_csv(Path(args.scenarios), "V2 port-sizing scenario assumptions")
    validate_scenarios(scenarios)

    scenario_results = build_results(results, right_sizing, scenarios)
    scenario_summary = summarize_results(scenario_results)

    output_path = Path(args.output)
    summary_path = Path(args.summary_output)
    report_path = Path(args.report)
    chart_path = Path(args.chart)
    ensure_parent_dir(output_path)
    ensure_parent_dir(summary_path)
    ensure_parent_dir(report_path)
    ensure_parent_dir(chart_path)

    scenario_results.to_csv(output_path, index=False)
    scenario_summary.to_csv(summary_path, index=False)
    report_path.write_text(build_report(scenario_results, scenario_summary, scenarios), encoding="utf-8")
    create_heatmap(scenario_results, chart_path)

    print("V2 PORT-SIZING SCENARIO ANALYSIS")
    print("--------------------------------")
    print(f"Scenarios: {len(scenarios)}")
    print(f"Sites: {scenario_results['site_id'].nunique()}")
    print(f"Rows: {len(scenario_results)}")
    print(f"Saved results: {output_path}")
    print(f"Saved summary: {summary_path}")
    print(f"Saved report: {report_path}")
    print(f"Saved chart: {chart_path}")
    print()
    print(scenario_summary.to_string(index=False))


if __name__ == "__main__":
    main()
