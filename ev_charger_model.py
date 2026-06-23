"""
EV Charger Site-Readiness and Right-Sizing Starter Model

This script reads candidate public EV charging sites, scores them for demand,
feasibility, safety, and equity, recommends starter port counts, adds planning
recommendation tiers, and exports CSV/chart outputs.

It is a transparent planning-support prototype. It does not replace utility,
engineering, ADA, Fire Marshal, AHJ, stormwater, or permitting review.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

EV_SHARE_HIGH_BENCHMARK = 0.10


def minmax(series: pd.Series) -> pd.Series:
    """Convert a column to a 0-1 scale."""
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    if s.max() == s.min():
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def bounded_signal(series: pd.Series, high_benchmark: float) -> pd.Series:
    """Scale a percentage-like signal against a fixed benchmark.

    This avoids exaggerating tiny EV-share differences when there are only a few
    sites in the dataset. For example, 2% EV share becomes 0.20 when the high
    benchmark is 10%.
    """
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    return (s / high_benchmark).clip(lower=0, upper=1)


def yesno_to_num(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).strip().lower()
    return 1.0 if value in {"1", "y", "yes", "true", "t"} else 0.0


def safe_filename(name: str) -> str:
    cleaned = []
    for character in str(name):
        if character.isalnum():
            cleaned.append(character.lower())
        elif character in {" ", "-", "_"}:
            cleaned.append("_")
    filename = "".join(cleaned).strip("_")
    while "__" in filename:
        filename = filename.replace("__", "_")
    return filename or "site"


def erlang_c(lambda_hr: float, mu_hr: float, ports: int):
    """Simple queueing approximation."""
    if ports <= 0 or mu_hr <= 0:
        return np.nan, np.nan, np.nan

    utilization = lambda_hr / (ports * mu_hr)
    if utilization >= 1:
        return 1.0, np.inf, utilization

    traffic_load = lambda_hr / mu_hr
    sum_terms = sum((traffic_load ** n) / math.factorial(n) for n in range(ports))
    last_term = ((traffic_load ** ports) / math.factorial(ports)) * (1 / (1 - utilization))
    p0 = 1.0 / (sum_terms + last_term)
    probability_wait = last_term * p0
    wait_hours = probability_wait / (ports * mu_hr - lambda_hr)
    return probability_wait, wait_hours, utilization


def choose_ports(
    expected_sessions_day: float,
    avg_session_hr: float,
    hours_open: float,
    max_ports: int = 20,
    target_utilization: float = 0.70,
    max_mean_wait_min: float = 10,
):
    arrivals_per_hour = expected_sessions_day / max(hours_open, 1)
    service_rate_per_hour = 1 / max(avg_session_hr, 0.1)
    fallback = None

    for ports in range(1, max_ports + 1):
        _, wait_hours, utilization = erlang_c(arrivals_per_hour, service_rate_per_hour, ports)
        wait_minutes = wait_hours * 60 if np.isfinite(wait_hours) else np.inf
        if np.isfinite(wait_minutes) and utilization <= target_utilization and wait_minutes <= max_mean_wait_min:
            return ports, utilization, wait_minutes
        fallback = (ports, utilization, wait_minutes)

    return fallback


def build_review_reason(row: pd.Series) -> str:
    reasons = []
    if row["public_access"] == 0:
        reasons.append("Limited or non-public access")
    if row["ada_layout_possible"] == 0:
        reasons.append("ADA-accessible layout unresolved")
    if row["fire_access_ok"] == 0:
        reasons.append("Fire apparatus access concern")
    if row["garage_enclosed"] == 1:
        reasons.append("Enclosed garage or limited ventilation/access")
    if row["emergency_disconnect_visible"] == 0:
        reasons.append("Emergency disconnect visibility not confirmed")
    if row["stormwater_risk"] == 1:
        reasons.append("Stormwater or firefighting runoff concern")
    if row["battery_storage_flag"] == 1:
        reasons.append("Battery storage present or proposed")
    return "; ".join(reasons) if reasons else "No obvious model-level review trigger"


def build_recommendation_tier(row: pd.Series) -> str:
    """Convert scores and review flags into a plain-English planning tier."""
    if row["public_access"] == 0:
        return "Low public-priority / special-use"
    if row["garage_enclosed"] == 1:
        return "High-review candidate"
    if row["model_rank"] <= 2 and row["readiness_score"] >= 50:
        return "Tier 1 — advance to site screening"
    if row["readiness_score"] >= 45:
        return "Tier 2 — promising candidate, refine data"
    return "Tier 3 — lower priority / monitor"


def build_planning_recommendation(row: pd.Series) -> str:
    tier = row["recommendation_tier"]
    if tier.startswith("Tier 1"):
        return "Advance to site screening and stakeholder confirmation before design or procurement."
    if tier.startswith("Tier 2"):
        return "Keep as a promising candidate and improve demand, parking, operating-hours, and electrical assumptions."
    if tier.startswith("High-review"):
        return "Keep in the planning discussion, but require garage, fire/AHJ, access, and electrical review before advancement."
    if tier.startswith("Low public"):
        return "Do not advance as a general-public charging site until the public-access or fleet-only use case is confirmed."
    return "Monitor as a lower-priority candidate and revisit after stronger data is available."


def build_priority_reason(row: pd.Series) -> str:
    if row["public_access"] == 0:
        return "Limited or non-public access and low surrounding public-charging demand keep this site low priority."
    if row["garage_enclosed"] == 1:
        return "Commuter/garage role and equity value are useful, but enclosed-garage review lowers implementation confidence."
    if row["model_rank"] <= 2:
        return "Stable top-ranked public candidate with stronger readiness than the rest of the current candidate set."
    if row["readiness_score"] >= 45:
        return "Public candidate with moderate readiness, but additional data is needed before advancing."
    return "Current score is lower than stronger alternatives, mainly because demand/equity/feasibility signals are weaker in this V1 dataset."


def build_data_needed_next(row: pd.Series) -> str:
    needs = []

    if row["elec_service_rating_amp"] == 0:
        needs.append("confirm electrical service rating")
    if row["spare_capacity_kw"] == 0:
        needs.append("confirm spare capacity or upgrade need")
    if row["emergency_disconnect_visible"] == 0:
        needs.append("confirm emergency disconnect location/visibility")

    needs.append("confirm visitor/employee counts and operating hours")
    needs.append("confirm parking count and likely charger placement")

    if row["garage_enclosed"] == 1:
        needs.append("complete garage fire/AHJ/access review")
    if row["public_access"] == 0:
        needs.append("confirm whether site is public, fleet-only, or should be removed")

    return "; ".join(needs)


def apply_recommendations(results: pd.DataFrame) -> pd.DataFrame:
    """Add rank and plain-English planning recommendation columns."""
    ranked = results.sort_values("readiness_score", ascending=False).reset_index(drop=True)
    ranked["model_rank"] = range(1, len(ranked) + 1)
    ranked["recommendation_tier"] = ranked.apply(build_recommendation_tier, axis=1)
    ranked["planning_recommendation"] = ranked.apply(build_planning_recommendation, axis=1)
    ranked["priority_reason"] = ranked.apply(build_priority_reason, axis=1)
    ranked["data_needed_next"] = ranked.apply(build_data_needed_next, axis=1)
    return ranked


def enrich_and_score(sites: pd.DataFrame) -> pd.DataFrame:
    df = sites.copy()

    yes_no_fields = [
        "public_access",
        "ada_layout_possible",
        "fire_access_ok",
        "garage_enclosed",
        "emergency_disconnect_visible",
        "stormwater_risk",
        "battery_storage_flag",
    ]
    for col in yes_no_fields:
        df[col] = df[col].apply(yesno_to_num).fillna(0)

    numeric_fields = [
        "employees_day",
        "visitors_day",
        "fleet_vehicles",
        "parking_spaces",
        "hours_open",
        "avg_dwell_min",
        "nearby_households_1mi",
        "nearby_jobs_1mi",
        "aadt_nearest",
        "amenities_count_0_5mi",
        "ev_share_local",
        "existing_l2_ports_1mi",
        "existing_dcfc_ports_3mi",
        "equity_gap_index",
        "spare_capacity_kw",
        "distance_to_service_ft",
        "trenching_ft",
        "trench_cost_per_ft",
        "service_upgrade_cost_usd",
        "elec_service_rating_amp",
    ]
    for col in numeric_fields:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["access_adjustment"] = np.where(df["public_access"] >= 1, 1.00, 0.35)
    df["readiness_access_adjustment"] = np.where(df["public_access"] >= 1, 1.00, 0.65)

    df["install_cost_est_usd"] = df["trenching_ft"] * df["trench_cost_per_ft"] + df["service_upgrade_cost_usd"]
    df["existing_ports_total"] = df["existing_l2_ports_1mi"] + df["existing_dcfc_ports_3mi"]

    normalize_cols = [
        "nearby_households_1mi",
        "nearby_jobs_1mi",
        "aadt_nearest",
        "amenities_count_0_5mi",
        "parking_spaces",
        "avg_dwell_min",
        "existing_ports_total",
        "spare_capacity_kw",
        "distance_to_service_ft",
        "install_cost_est_usd",
        "equity_gap_index",
    ]
    for col in normalize_cols:
        df[col + "_n"] = minmax(df[col])

    ev_share_signal = bounded_signal(df["ev_share_local"], EV_SHARE_HIGH_BENCHMARK)

    raw_demand_subscore = 100 * (
        0.25 * ev_share_signal
        + 0.18 * df["nearby_jobs_1mi_n"]
        + 0.18 * df["nearby_households_1mi_n"]
        + 0.10 * df["aadt_nearest_n"]
        + 0.10 * df["amenities_count_0_5mi_n"]
        + 0.09 * df["parking_spaces_n"]
        + 0.10 * df["avg_dwell_min_n"]
        - 0.20 * df["existing_ports_total_n"]
    ).clip(lower=0)
    df["demand_subscore"] = (raw_demand_subscore * df["access_adjustment"]).clip(lower=0)

    df["feasibility_subscore"] = 100 * (
        0.35 * df["spare_capacity_kw_n"]
        + 0.25 * (1 - df["install_cost_est_usd_n"])
        + 0.20 * (1 - df["distance_to_service_ft_n"])
        + 0.20 * df["ada_layout_possible"]
    ).clip(lower=0)

    df["safety_subscore"] = 100 * (
        0.35 * df["fire_access_ok"]
        + 0.20 * (1 - df["garage_enclosed"])
        + 0.20 * df["emergency_disconnect_visible"]
        + 0.15 * (1 - df["stormwater_risk"])
        + 0.10 * (1 - df["battery_storage_flag"])
    ).clip(lower=0)

    df["base_readiness_score"] = (
        0.45 * df["demand_subscore"]
        + 0.30 * df["feasibility_subscore"]
        + 0.15 * df["safety_subscore"]
        + 0.10 * (100 * df["equity_gap_index_n"])
    )
    df["readiness_score"] = (df["base_readiness_score"] * df["readiness_access_adjustment"]).round(1)

    behavior = {
        "library": {"visitor_capture": 0.07, "employee_capture": 0.04, "need_factor": 0.55, "avg_session_hr": 1.5, "target_util": 0.65},
        "office": {"visitor_capture": 0.05, "employee_capture": 0.05, "need_factor": 0.50, "avg_session_hr": 2.0, "target_util": 0.65},
        "clinic": {"visitor_capture": 0.06, "employee_capture": 0.04, "need_factor": 0.50, "avg_session_hr": 2.0, "target_util": 0.65},
        "garage": {"visitor_capture": 0.05, "employee_capture": 0.03, "need_factor": 0.60, "avg_session_hr": 4.0, "target_util": 0.60},
        "public_safety": {"visitor_capture": 0.02, "employee_capture": 0.03, "need_factor": 0.35, "avg_session_hr": 3.0, "target_util": 0.70},
        "fleet": {"visitor_capture": 0.00, "employee_capture": 0.00, "need_factor": 0.00, "avg_session_hr": 3.0, "target_util": 0.70},
    }

    output_rows = []
    for _, row in df.iterrows():
        site_type = str(row["site_type"]).lower()
        b = behavior.get(site_type, {"visitor_capture": 0.06, "employee_capture": 0.04, "need_factor": 0.50, "avg_session_hr": 2.0, "target_util": 0.65})

        public_sessions = (
            row["visitors_day"] * row["ev_share_local"] * b["visitor_capture"] * b["need_factor"]
            + row["employees_day"] * row["ev_share_local"] * b["employee_capture"] * b["need_factor"]
        )
        public_sessions *= (
            row["access_adjustment"]
            * (1 + 0.30 * row["equity_gap_index"])
            * (1 + 0.10 * row["amenities_count_0_5mi_n"])
            * (1 - 0.20 * row["existing_ports_total_n"])
        )

        fleet_sessions = max(0, row["fleet_vehicles"] * 0.5)
        expected_sessions_day = max(0.3, public_sessions + fleet_sessions)

        ports_now, utilization, wait_min = choose_ports(expected_sessions_day, b["avg_session_hr"], row["hours_open"], target_utilization=b["target_util"])
        ports_2035, _, _ = choose_ports(expected_sessions_day * 1.6, b["avg_session_hr"], row["hours_open"], target_utilization=b["target_util"])
        ports_2050, _, _ = choose_ports(expected_sessions_day * 2.4, b["avg_session_hr"], row["hours_open"], target_utilization=b["target_util"])

        row = row.copy()
        row["expected_sessions_day"] = expected_sessions_day
        row["recommended_ports_now"] = ports_now
        row["recommended_ports_2035"] = ports_2035
        row["recommended_ports_2050"] = ports_2050
        row["estimated_utilization"] = utilization
        row["mean_wait_min"] = wait_min
        row["review_reason"] = build_review_reason(row)
        row["ahj_review_flag"] = 0 if row["review_reason"] == "No obvious model-level review trigger" else 1
        output_rows.append(row)

    results = pd.DataFrame(output_rows)
    results = apply_recommendations(results)

    output_cols = [
        "model_rank",
        "site_id",
        "site_name",
        "site_type",
        "public_access",
        "access_adjustment",
        "readiness_score",
        "recommendation_tier",
        "planning_recommendation",
        "priority_reason",
        "data_needed_next",
        "demand_subscore",
        "feasibility_subscore",
        "safety_subscore",
        "expected_sessions_day",
        "recommended_ports_now",
        "recommended_ports_2035",
        "recommended_ports_2050",
        "estimated_utilization",
        "mean_wait_min",
        "install_cost_est_usd",
        "ahj_review_flag",
        "review_reason",
    ]
    return results[output_cols]


def plot_readiness(results: pd.DataFrame, output_file: str = "readiness_score_chart.png") -> None:
    plt.figure(figsize=(10, 6))
    plt.barh(results["site_name"], results["readiness_score"])
    plt.xlabel("Readiness Score")
    plt.ylabel("Site")
    plt.title("EV Charger Site Readiness Scores")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_file, dpi=200)
    plt.close()


def plot_utilization_curves(results: pd.DataFrame) -> list[str]:
    chart_files = []
    for _, row in results.iterrows():
        ports = list(range(1, 9))
        avg_session_hr = 1.5 if row["site_type"] == "library" else 4.0 if row["site_type"] == "garage" else 3.0 if row["site_type"] == "public_safety" else 2.0
        hours_open = 24 if row["site_type"] == "garage" else 8
        utilizations = []
        for port_count in ports:
            _, _, utilization = erlang_c(row["expected_sessions_day"] / max(hours_open, 1), 1 / avg_session_hr, port_count)
            utilizations.append(utilization)

        output_file = f"utilization_vs_ports_{safe_filename(row['site_name'])}.png"
        plt.figure(figsize=(8, 5))
        plt.plot(ports, utilizations, marker="o")
        plt.xlabel("Number of Charging Ports")
        plt.ylabel("Estimated Utilization")
        plt.title(f"Utilization vs Ports — {row['site_name']}")
        plt.ylim(0, max(0.8, max(utilizations) * 1.2 if utilizations else 0.8))
        plt.tight_layout()
        plt.savefig(output_file, dpi=200)
        plt.close()
        chart_files.append(output_file)
    return chart_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run EV charger site-readiness model.")
    parser.add_argument("--input", default="real_sites_v1.csv", help="Input candidate-site CSV.")
    parser.add_argument("--output", default="site_results.csv", help="Output results CSV.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    sites = pd.read_csv(input_path)
    results = enrich_and_score(sites)
    results.to_csv(args.output, index=False)
    plot_readiness(results)
    chart_files = plot_utilization_curves(results)

    print("EV CHARGER SITE-READINESS RESULTS")
    print("----------------------------------")
    print(f"Input file: {args.input}")
    print(results.to_string(index=False))
    print()
    print(f"Saved: {args.output}")
    print("Saved: readiness_score_chart.png")
    print("Saved utilization charts:")
    for chart_file in chart_files:
        print(f"- {chart_file}")
    print()
    print("Done. Open the output CSV and PNG charts in this folder.")


if __name__ == "__main__":
    main()
