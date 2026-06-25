"""Compare V2 right-sizing outputs with the port simulation."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DEFAULT_RIGHT_SIZING = "data/outputs/v2_right_sizing_scenarios.csv"
DEFAULT_PORT_SIMULATION = "data/outputs/v2_port_utilization_simulation.csv"
DEFAULT_OUTPUT = "data/outputs/v2_right_sizing_validation.csv"
DEFAULT_REPORT = "data/outputs/v2_right_sizing_validation_report.md"

OUTPUT_COLUMNS = [
    "model_rank", "site_id", "site_name", "ports_now", "sim_min_ports_current",
    "current_status_at_ports_now", "current_utilization_at_ports_now",
    "current_wait_min_at_ports_now", "current_alignment", "future_ready_capacity",
    "sim_min_ports_2050_high", "future_status_at_future_ready",
    "future_utilization_at_future_ready", "future_wait_min_at_future_ready",
    "future_alignment", "simulation_supported_strategy", "right_sizing_validation_note",
]


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return pd.read_csv(path)


def choose_min_ports(group: pd.DataFrame) -> int | None:
    if group.empty:
        return None
    usable = group[group["capacity_status"] != "underbuilt"]
    if not usable.empty:
        return int(usable.sort_values("port_count").iloc[0]["port_count"])
    return int(group.sort_values(["estimated_wait_min", "port_count"], ascending=[True, False]).iloc[0]["port_count"])


def pick_row(group: pd.DataFrame, flag_col: str) -> pd.Series | None:
    if group.empty:
        return None
    if flag_col in group.columns:
        flagged = group[group[flag_col] == True]
        if not flagged.empty:
            return flagged.iloc[0]
    return group.sort_values("port_count").iloc[0]


def align_now(ports_now: int, sim_min: int | None, status: str, util: float) -> str:
    if sim_min is None:
        return "simulation_missing"
    if ports_now < sim_min:
        return "possibly_low_now"
    if ports_now == sim_min:
        return "aligned_now"
    if status == "likely_overbuilt_or_low_demand" or util < 10:
        return "conservative_under_current_demand"
    return "conservative_now"


def align_future(future_ready: int, sim_min: int | None, status: str) -> str:
    if sim_min is None:
        return "simulation_missing"
    if future_ready < sim_min:
        return "possibly_low_future_capacity"
    if future_ready == sim_min:
        return "aligned_future_capacity"
    if status == "likely_overbuilt_or_low_demand":
        return "conservative_future_capacity"
    return "extra_future_capacity"


def support_label(current: str, future: str) -> str:
    if "possibly_low" in current or "possibly_low" in future:
        return "needs_review"
    if current.startswith("aligned") and future.startswith("aligned"):
        return "simulation_supports_strategy"
    if "conservative" in current or "extra" in future or "conservative" in future:
        return "simulation_supports_conservative_strategy"
    return "simulation_broadly_supports_strategy"


def note_for(current: str, future: str) -> str:
    if "possibly_low" in current:
        return "Near-term port count may need review under simulation assumptions."
    if "possibly_low" in future:
        return "Future-ready capacity may need review under the 2050 high-growth case."
    if "conservative" in current or "extra" in future or "conservative" in future:
        return "Simulation supports this as a conservative planning recommendation."
    return "Simulation supports the right-sizing recommendation under tested assumptions."


def build_validation(right_sizing: pd.DataFrame, simulation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, rs in right_sizing.sort_values("model_rank").iterrows():
        site_id = rs["site_id"]
        site_sim = simulation[simulation["site_id"] == site_id]
        current = site_sim[site_sim["demand_case"] == "current"]
        future = site_sim[site_sim["demand_case"] == "2050_high"]
        current_row = pick_row(current, "is_ports_now")
        future_row = pick_row(future, "is_future_ready_capacity")
        min_current = choose_min_ports(current)
        min_future = choose_min_ports(future)
        ports_now = int(rs["ports_now"])
        future_ready = int(rs["future_ready_capacity"])
        cur_status = str(current_row.get("capacity_status", "simulation_missing")) if current_row is not None else "simulation_missing"
        fut_status = str(future_row.get("capacity_status", "simulation_missing")) if future_row is not None else "simulation_missing"
        cur_util = float(current_row.get("utilization_pct", 0)) if current_row is not None else 0.0
        fut_util = float(future_row.get("utilization_pct", 0)) if future_row is not None else 0.0
        cur_wait = float(current_row.get("estimated_wait_min", 0)) if current_row is not None else 0.0
        fut_wait = float(future_row.get("estimated_wait_min", 0)) if future_row is not None else 0.0
        cur_align = align_now(ports_now, min_current, cur_status, cur_util)
        fut_align = align_future(future_ready, min_future, fut_status)
        rows.append({
            "model_rank": rs["model_rank"], "site_id": site_id, "site_name": rs["site_name"],
            "ports_now": ports_now, "sim_min_ports_current": min_current,
            "current_status_at_ports_now": cur_status, "current_utilization_at_ports_now": cur_util,
            "current_wait_min_at_ports_now": cur_wait, "current_alignment": cur_align,
            "future_ready_capacity": future_ready, "sim_min_ports_2050_high": min_future,
            "future_status_at_future_ready": fut_status, "future_utilization_at_future_ready": fut_util,
            "future_wait_min_at_future_ready": fut_wait, "future_alignment": fut_align,
            "simulation_supported_strategy": support_label(cur_align, fut_align),
            "right_sizing_validation_note": note_for(cur_align, fut_align),
        })
    return pd.DataFrame(rows)[OUTPUT_COLUMNS]


def markdown_table(df: pd.DataFrame, cols: list[str]) -> str:
    view = df[[c for c in cols if c in df.columns]].copy()
    view.columns = [c.replace("_", " ") for c in view.columns]
    lines = ["| " + " | ".join(view.columns) + " |", "| " + " | ".join(["---"] * len(view.columns)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("|", "/") for c in view.columns) + " |")
    return "\n".join(lines)


def build_report(validation: pd.DataFrame) -> str:
    cols = ["model_rank", "site_id", "ports_now", "sim_min_ports_current", "current_alignment", "future_ready_capacity", "sim_min_ports_2050_high", "future_alignment", "simulation_supported_strategy"]
    return f"""# V2 Right-Sizing Validation Report

This report compares right-sizing recommendations with the V2 port simulation.

{markdown_table(validation, cols)}

This is a planning-screen validation layer, not a final engineering result.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--right-sizing", default=DEFAULT_RIGHT_SIZING)
    parser.add_argument("--port-simulation", default=DEFAULT_PORT_SIMULATION)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validation = build_validation(read_csv(Path(args.right_sizing), "right-sizing"), read_csv(Path(args.port_simulation), "port simulation"))
    out = Path(args.output)
    report = Path(args.report)
    ensure_parent(out)
    ensure_parent(report)
    validation.to_csv(out, index=False)
    report.write_text(build_report(validation), encoding="utf-8")
    print("V2 RIGHT-SIZING VALIDATION")
    print("--------------------------")
    print(f"Rows: {len(validation)}")
    print(f"Saved validation: {out}")
    print(f"Saved report: {report}")
    print()
    print(validation[["model_rank", "site_id", "ports_now", "sim_min_ports_current", "current_alignment", "future_ready_capacity", "sim_min_ports_2050_high", "future_alignment"]].to_string(index=False))


if __name__ == "__main__":
    main()
