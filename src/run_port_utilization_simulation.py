"""Run a simple V2 port-utilization simulation.

This module estimates how busy a candidate site may be under different port
counts and planning horizons. It is intentionally beginner-friendly and uses
simple deterministic assumptions instead of complex queueing or machine learning.

Run from the repository root after the V2 model and right-sizing outputs exist:

    python src/run_port_utilization_simulation.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_RESULTS = "data/outputs/v2_site_results.csv"
DEFAULT_RIGHT_SIZING = "data/outputs/v2_right_sizing_scenarios.csv"
DEFAULT_OUTPUT = "data/outputs/v2_port_utilization_simulation.csv"
DEFAULT_REPORT = "data/outputs/v2_port_utilization_simulation_report.md"
DEFAULT_CHART = "data/outputs/charts/v2_port_utilization_simulation.png"

PORT_OPTIONS = [2, 3, 4, 6, 8]
DEMAND_CASES = {
    "current": 1.0,
    "2035_base": 1.8,
    "2035_high": 2.5,
    "2050_base": 3.0,
    "2050_high": 4.5,
}


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_required_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required {label} file not found: {path}")
    return pd.read_csv(path)


def classify_queue_risk(peak_demand_ratio: float) -> str:
    if peak_demand_ratio <= 0.55:
        return "low"
    if peak_demand_ratio <= 0.80:
        return "moderate"
    if peak_demand_ratio <= 1.00:
        return "elevated"
    return "high"


def classify_capacity_status(utilization_pct: float, estimated_wait_min: float) -> str:
    if estimated_wait_min > 20 or utilization_pct > 80:
        return "underbuilt"
    if utilization_pct < 10:
        return "likely_overbuilt_or_low_demand"
    if estimated_wait_min <= 10 and 15 <= utilization_pct <= 65:
        return "right_sized"
    return "acceptable_but_monitor"


def estimate_wait_minutes(peak_demand_ratio: float) -> float:
    if peak_demand_ratio <= 0.55:
        return 0.0
    if peak_demand_ratio <= 0.80:
        return round((peak_demand_ratio - 0.55) * 20, 1)
    if peak_demand_ratio <= 1.00:
        return round(5 + (peak_demand_ratio - 0.80) * 75, 1)
    return round(20 + (peak_demand_ratio - 1.00) * 120, 1)


def simulate_site(
    site: pd.Series,
    right_sizing_row: pd.Series | None,
    avg_charge_hours: float,
    charging_window_hours: float,
    peak_factor: float,
) -> list[dict[str, object]]:
    base_sessions = float(site.get("expected_sessions_day", 0) or 0)
    rows: list[dict[str, object]] = []

    ports_now = None
    future_ready = None
    if right_sizing_row is not None:
        ports_now = int(right_sizing_row.get("ports_now", 0) or 0)
        future_ready = int(right_sizing_row.get("future_ready_capacity", 0) or 0)

    for demand_case, multiplier in DEMAND_CASES.items():
        sessions = base_sessions * multiplier
        for port_count in PORT_OPTIONS:
            utilization_pct = 0.0
            peak_demand_ratio = 0.0
            if port_count > 0 and charging_window_hours > 0:
                utilization_pct = (sessions * avg_charge_hours) / (port_count * charging_window_hours) * 100
                peak_demand_ratio = (sessions * avg_charge_hours * peak_factor) / (port_count * charging_window_hours)

            wait_min = estimate_wait_minutes(peak_demand_ratio)
            rows.append(
                {
                    "site_id": site.get("site_id", ""),
                    "site_name": site.get("site_name", ""),
                    "model_rank": site.get("model_rank", ""),
                    "readiness_score": site.get("readiness_score", ""),
                    "demand_case": demand_case,
                    "session_multiplier": multiplier,
                    "sessions_day": round(sessions, 3),
                    "port_count": port_count,
                    "avg_charge_hours": avg_charge_hours,
                    "charging_window_hours": charging_window_hours,
                    "peak_factor": peak_factor,
                    "utilization_pct": round(utilization_pct, 1),
                    "peak_demand_ratio": round(peak_demand_ratio, 3),
                    "estimated_wait_min": wait_min,
                    "queue_risk_level": classify_queue_risk(peak_demand_ratio),
                    "capacity_status": classify_capacity_status(utilization_pct, wait_min),
                    "is_ports_now": port_count == ports_now,
                    "is_future_ready_capacity": port_count == future_ready,
                }
            )
    return rows


def build_simulation(
    results: pd.DataFrame,
    right_sizing: pd.DataFrame,
    avg_charge_hours: float,
    charging_window_hours: float,
    peak_factor: float,
) -> pd.DataFrame:
    if "site_id" not in results.columns:
        raise ValueError("V2 results must include site_id.")
    if "expected_sessions_day" not in results.columns:
        raise ValueError("V2 results must include expected_sessions_day.")

    right_by_id = right_sizing.set_index("site_id", drop=False) if "site_id" in right_sizing.columns else pd.DataFrame()
    rows: list[dict[str, object]] = []

    ranked = results.copy()
    if "model_rank" in ranked.columns:
        ranked["model_rank"] = pd.to_numeric(ranked["model_rank"], errors="coerce")
        ranked = ranked.sort_values("model_rank")

    for _, site in ranked.iterrows():
        site_id = site.get("site_id", "")
        right_row = right_by_id.loc[site_id] if not right_by_id.empty and site_id in right_by_id.index else None
        rows.extend(simulate_site(site, right_row, avg_charge_hours, charging_window_hours, peak_factor))

    return pd.DataFrame(rows)


def recommended_min_ports(simulation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_cols = ["site_id", "site_name", "model_rank", "demand_case"]
    for keys, group in simulation.groupby(group_cols, dropna=False):
        site_id, site_name, model_rank, demand_case = keys
        acceptable = group[group["capacity_status"].isin(["right_sized", "acceptable_but_monitor"])]
        if acceptable.empty:
            best = group.sort_values(["estimated_wait_min", "utilization_pct"]).iloc[0]
        else:
            best = acceptable.sort_values("port_count").iloc[0]
        rows.append(
            {
                "site_id": site_id,
                "site_name": site_name,
                "model_rank": model_rank,
                "demand_case": demand_case,
                "recommended_min_ports_simulated": int(best["port_count"]),
                "utilization_pct_at_recommended": float(best["utilization_pct"]),
                "estimated_wait_min_at_recommended": float(best["estimated_wait_min"]),
                "queue_risk_at_recommended": best["queue_risk_level"],
                "capacity_status_at_recommended": best["capacity_status"],
            }
        )
    return pd.DataFrame(rows)


def markdown_table(data: pd.DataFrame, columns: list[str]) -> str:
    if data.empty:
        return "_No simulation data available._"
    view = data[[col for col in columns if col in data.columns]].copy()
    view.columns = [col.replace("_", " ") for col in view.columns]
    header = "| " + " | ".join(view.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = []
    for _, row in view.iterrows():
        values = [str(row[col]).replace("|", "/") for col in view.columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator] + rows)


def build_report(simulation: pd.DataFrame, recommended: pd.DataFrame) -> str:
    current = recommended[recommended["demand_case"] == "current"].sort_values("model_rank")
    future_high = recommended[recommended["demand_case"] == "2050_high"].sort_values("model_rank")

    return f"""# V2 Port-Utilization Simulation Report

This report estimates how busy each candidate site may be under different port counts and demand-growth cases.

The simulation is intentionally simple. It is a planning screen, not a detailed queueing model or utility engineering result.

## Assumptions

```text
Port options tested: {PORT_OPTIONS}
Demand cases: {list(DEMAND_CASES.keys())}
Average charging time: {simulation['avg_charge_hours'].iloc[0] if not simulation.empty else 'n/a'} hours
Daily charging window: {simulation['charging_window_hours'].iloc[0] if not simulation.empty else 'n/a'} hours
Peak factor: {simulation['peak_factor'].iloc[0] if not simulation.empty else 'n/a'}
```

## Current-demand recommended minimum ports

{markdown_table(current, ['model_rank', 'site_id', 'recommended_min_ports_simulated', 'utilization_pct_at_recommended', 'estimated_wait_min_at_recommended', 'queue_risk_at_recommended', 'capacity_status_at_recommended'])}

## 2050 high-demand recommended minimum ports

{markdown_table(future_high, ['model_rank', 'site_id', 'recommended_min_ports_simulated', 'utilization_pct_at_recommended', 'estimated_wait_min_at_recommended', 'queue_risk_at_recommended', 'capacity_status_at_recommended'])}

## How to read this

- `right_sized` means utilization and wait time look reasonable for planning-screen purposes.
- `acceptable_but_monitor` means the port count may work, but the site should be watched as demand grows.
- `underbuilt` means simulated wait or utilization is too high.
- `likely_overbuilt_or_low_demand` means the port count may be more capacity than the demand currently supports.

This output should be used with the right-sizing report, electrical-risk report, ADA/AHJ/Fire Marshal review, and local site constraints.
"""


def create_chart(simulation: pd.DataFrame, output_path: Path) -> None:
    current = simulation[simulation["demand_case"] == "current"].copy()
    current["model_rank"] = pd.to_numeric(current["model_rank"], errors="coerce")
    top_sites = current[current["model_rank"] <= 6]

    ensure_parent_dir(output_path)
    plt.figure(figsize=(11, 6))
    for site_id, group in top_sites.groupby("site_id"):
        group = group.sort_values("port_count")
        plt.plot(group["port_count"], group["utilization_pct"], marker="o", label=site_id)
    plt.axhline(65, linestyle="--", linewidth=1, label="Upper planning target")
    plt.axhline(15, linestyle="--", linewidth=1, label="Lower planning target")
    plt.title("V2 Current-Demand Port Utilization Simulation")
    plt.xlabel("Charging ports")
    plt.ylabel("Estimated utilization (%)")
    plt.xticks(PORT_OPTIONS)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a simple V2 port-utilization simulation.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="V2 site results CSV.")
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING, help="V2 right-sizing scenario CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Simulation CSV output.")
    parser.add_argument("--report", default=DEFAULT_REPORT, help="Simulation Markdown report output.")
    parser.add_argument("--chart", default=DEFAULT_CHART, help="Simulation chart output.")
    parser.add_argument("--avg-charge-hours", type=float, default=1.25, help="Average session duration in hours.")
    parser.add_argument("--charging-window-hours", type=float, default=12.0, help="Assumed daily public charging window.")
    parser.add_argument("--peak-factor", type=float, default=1.35, help="Peak demand multiplier used for wait-risk screening.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    right_sizing_path = Path(args.right_sizing)
    output_path = Path(args.output)
    report_path = Path(args.report)
    chart_path = Path(args.chart)

    results = read_required_csv(results_path, "V2 site results")
    right_sizing = read_required_csv(right_sizing_path, "V2 right-sizing")
    simulation = build_simulation(results, right_sizing, args.avg_charge_hours, args.charging_window_hours, args.peak_factor)
    recommended = recommended_min_ports(simulation)

    ensure_parent_dir(output_path)
    ensure_parent_dir(report_path)
    simulation.to_csv(output_path, index=False)
    report_path.write_text(build_report(simulation, recommended), encoding="utf-8")
    create_chart(simulation, chart_path)

    print("V2 PORT-UTILIZATION SIMULATION")
    print("------------------------------")
    print(f"Rows: {len(simulation)}")
    print(f"Saved simulation: {output_path}")
    print(f"Saved report: {report_path}")
    print(f"Saved chart: {chart_path}")
    print()
    print(recommended[recommended["demand_case"] == "current"].sort_values("model_rank").to_string(index=False))


if __name__ == "__main__":
    main()
