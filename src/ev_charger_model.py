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

DEFAULT_INPUT = "data/inputs/real_sites_v1.csv"
DEFAULT_OUTPUT = "data/outputs/site_results.csv"
DEFAULT_READINESS_CHART = "data/outputs/charts/readiness_score_chart.png"
DEFAULT_UTILIZATION_CHART_DIR = "data/outputs/charts"
EV_SHARE_HIGH_BENCHMARK = 0.10


def ensure_parent_dir(path: str | Path) -> None:
    """Create the parent folder for an output path if it does not exist."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def minmax(series: pd.Series) -> pd.Series:
    """Convert a column to a 0-1 scale."""
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    if s.max() == s.min():
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def bounded_signal(series: pd.Series, high_benchmark: float) -> pd.Series:
    """Scale a percentage-like signal against a fixed benchmark."""
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
    if row["model_rank"] == 1:
        return "Stable top-ranked public candidate with stronger readiness than the rest of the current candidate set."
    if row["model_rank"] == 2:
        return "Second strongest public candidate under the current model; strong, but not the top-ranked site."
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


def data_confidence_level(score: float) -> str:
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def build_data_confidence(row: pd.Series) -> pd.Series:
    """Score how much the model can trust a site's current input data.

    This is separate from readiness_score. A site can look promising while still
    needing stronger input confirmation.
    """
    score = 100.0
    reasons: list[str] = []

    def subtract(points: float, reason: str) -> None:
        nonlocal score
        score -= points
        reasons.append(reason)

    notes = str(row.get("notes", "")).lower()

    if row.get("elec_service_rating_amp", 0) <= 0:
        subtract(15, "electrical service rating unconfirmed")
    if row.get("spare_capacity_kw", 0) <= 0:
        subtract(15, "spare capacity unconfirmed")
    if row.get("emergency_disconnect_visible", 0) == 0:
        subtract(10, "emergency disconnect visibility unconfirmed")
    if row.get("distance_to_service_ft", 0) <= 0 or row.get("trenching_ft", 0) <= 0:
        subtract(8, "routing or trenching estimate incomplete")
    if row.get("parking_spaces", 0) <= 0:
        subtract(8, "parking count missing")
    if row.get("hours_open", 0) <= 0:
        subtract(8, "operating hours missing")
    if row.get("visitors_day", 0) <= 0 and row.get("employees_day", 0) <= 0 and row.get("fleet_vehicles", 0) <= 0:
        subtract(8, "site-use demand inputs are weak")
    if row.get("public_access", 0) == 0:
        subtract(8, "public access or use case needs confirmation")
    if row.get("garage_enclosed", 0) == 1:
        subtract(8, "garage context needs extra confirmation")
    if "planning assumption" in notes or "planning assumptions" in notes:
        subtract(6, "notes identify planning assumptions")
    if "unconfirmed" in notes:
        subtract(6, "notes identify unconfirmed fields")

    if "official" in notes:
        score += 5
        reasons.append("some inputs have official-source support")

    score = round(max(0, min(100, score)), 1)
    if not reasons:
        reasons.append("most key inputs are populated")

    return pd.Series(
        {
            "data_confidence_score": score,
            "data_confidence_level": data_confidence_level(score),
            "data_confidence_reason": "; ".join(reasons),
        }
    )


def apply_recommendations(results: pd.DataFrame) -> pd.DataFrame:
    """Add rank, planning recommendations, and data-confidence columns."""
    ranked = results.sort_values("readiness_score", ascending=False).reset_index(drop=True)
    ranked["model_rank"] = range(1, len(ranked) + 1)
    ranked["recommendation_tier"] = ranked.apply(build_recommendation_tier, axis=1)
    ranked["planning_recommendation"] = ranked.apply(build_planning_recommendation, axis=1)
    ranked["priority_reason"] = ranked.apply(build_priority_reason, axis=1)
    ranked["data_needed_next"] = ranked.apply(build_data_needed_next, axis=1)
    confidence_columns = ranked.apply(build_data_confidence, axis=1)
    ranked = pd.concat([ranked, confidence_columns], axis=1)
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
        "trenching_ft",
        "install_cost_est_usd",
        "equity_gap_index",
    ]
    for col in normalize_cols:
        df[col + "_n"] = minmax(df[col])

    df["ev_share_local_n"] = bounded_signal(df["ev_share_local"], EV_SHARE_HIGH_BENCHMARK)

    df["demand_subscore"] = 100 * (
        0.18 * df["nearby_households_1mi_n"]
        + 0.18 * df["nearby_jobs_1mi_n"]
        + 0.13 * df["aadt_nearest_n"]
        + 0.11 * df["amenities_count_0_5mi_n"]
        + 0.10 * df["parking_spaces_n"]
        + 0.08 * df["hours_open"].clip(lower=0, upper=24) / 24
        + 0.07 * df["avg_dwell_min_n"]
        + 0.08 * df["ev_share_local_n"]
        + 0.07 * (1 - df["existing_ports_total_n"])
    )
    df["demand_subscore"] = df["demand_subscore"] * df["readiness_access_adjustment"]

    df["feasibility_subscore"] = 100 * (
        0.35 * df["spare_capacity_kw_n"]
        + 0.25 * (1 - df["distance_to_service_ft_n"])
        + 0.25 * (1 - df["install_cost_est_usd_n"])
        + 0.15 * (1 - df["trenching_ft_n"])
    )

    df["safety_subscore"] = 100 * (
        0.35 * df["ada_layout_possible"]
        + 0.35 * df["fire_access_ok"]
        + 0.15 * (1 - df["garage_enclosed"])
        + 0.10 * df["emergency_disconnect_visible"]
        + 0.05 * (1 - df["stormwater_risk"])
    )

    df["equity_subscore"] = 100 * df["equity_gap_index_n"]

    df["readiness_score"] = (
        0.45 * df["demand_subscore"]
        + 0.30 * df["feasibility_subscore"]
        + 0.15 * df["safety_subscore"]
        + 0.10 * df["equity_subscore"]
    ).round(1)

    df["expected_sessions_day"] = (
        0.0015 * df["visitors_day"]
        + 0.0006 * df["employees_day"]
        + 0.00002 * df["nearby_jobs_1mi"]
        + 0.00003 * df["nearby_households_1mi"] * (1 + df["ev_share_local"])
    )
    df["expected_sessions_day"] = df["expected_sessions_day"].clip(lower=0.3)

    port_rows = []
    for _, row in df.iterrows():
        avg_session_hr = row["avg_dwell_min"] / 60 if row["avg_dwell_min"] > 0 else 2
        ports_now, util_now, wait_now = choose_ports(row["expected_sessions_day"], avg_session_hr, row["hours_open"])
        ports_2035, _, _ = choose_ports(row["expected_sessions_day"] * 1.8, avg_session_hr, row["hours_open"])
        ports_2050, _, _ = choose_ports(row["expected_sessions_day"] * 3.0, avg_session_hr, row["hours_open"])
        port_rows.append(
            {
                "recommended_ports_now": int(ports_now),
                "recommended_ports_2035": int(ports_2035),
                "recommended_ports_2050": int(ports_2050),
                "estimated_utilization": util_now,
                "mean_wait_min": wait_now,
            }
        )

    port_df = pd.DataFrame(port_rows)
    df = pd.concat([df, port_df], axis=1)
    df["ahj_review_flag"] = df.apply(lambda row: 1 if build_review_reason(row) != "No obvious model-level review trigger" else 0, axis=1)
    df["review_reason"] = df.apply(build_review_reason, axis=1)

    return apply_recommendations(df)


def plot_readiness_chart(results: pd.DataFrame, path: Path) -> None:
    ensure_parent_dir(path)
    ordered = results.sort_values("readiness_score", ascending=True)
    labels = ordered["site_id"] + "\n" + ordered["site_name"]

    plt.figure(figsize=(10, 6))
    plt.barh(labels, ordered["readiness_score"])
    plt.xlabel("Readiness score")
    plt.title("EV Charger Site Readiness Scores")
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def plot_utilization_curves(results: pd.DataFrame, chart_dir: Path) -> list[Path]:
    chart_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []

    for _, row in results.iterrows():
        avg_session_hr = row["avg_dwell_min"] / 60 if row["avg_dwell_min"] > 0 else 2
        hours_open = row["hours_open"]
        arrivals_per_hour = row["expected_sessions_day"] / max(hours_open, 1)
        service_rate_per_hour = 1 / max(avg_session_hr, 0.1)
        ports = list(range(1, 11))
        waits = []
        utils = []

        for port_count in ports:
            _, wait_hours, utilization = erlang_c(arrivals_per_hour, service_rate_per_hour, port_count)
            wait_minutes = wait_hours * 60 if np.isfinite(wait_hours) else np.nan
            waits.append(wait_minutes)
            utils.append(utilization)

        fig, ax1 = plt.subplots(figsize=(8, 5))
        ax1.plot(ports, utils, marker="o", label="Utilization")
        ax1.set_xlabel("Number of charging ports")
        ax1.set_ylabel("Utilization")
        ax1.set_ylim(0, max(1.0, max([value for value in utils if np.isfinite(value)] + [1.0])))

        ax2 = ax1.twinx()
        ax2.plot(ports, waits, marker="s", linestyle="--", label="Mean wait minutes")
        ax2.set_ylabel("Mean wait time (minutes)")

        plt.title(f"Utilization vs Ports: {row['site_id']} — {row['site_name']}")
        fig.tight_layout()
        output = chart_dir / f"utilization_vs_ports_{safe_filename(row['site_id'])}_{safe_filename(row['site_name'])}.png"
        plt.savefig(output, dpi=200)
        plt.close()
        saved_paths.append(output)

    return saved_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the EV charger site-readiness model.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to input CSV file.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to output CSV file.")
    parser.add_argument("--chart", default=DEFAULT_READINESS_CHART, help="Path to readiness chart PNG.")
    parser.add_argument("--utilization-chart-dir", default=DEFAULT_UTILIZATION_CHART_DIR, help="Folder for utilization charts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    chart_path = Path(args.chart)
    utilization_chart_dir = Path(args.utilization_chart_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    sites = pd.read_csv(input_path)
    results = enrich_and_score(sites)
    ensure_parent_dir(output_path)
    results.to_csv(output_path, index=False)
    plot_readiness_chart(results, chart_path)
    utilization_charts = plot_utilization_curves(results, utilization_chart_dir)

    display_columns = [
        "model_rank",
        "site_id",
        "site_name",
        "site_type",
        "public_access",
        "access_adjustment",
        "readiness_score",
        "data_confidence_score",
        "data_confidence_level",
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

    print("EV CHARGER SITE-READINESS RESULTS")
    print("----------------------------------")
    print(f"Input file: {input_path}")
    print(results[display_columns].to_string(index=False))
    print()
    print(f"Saved: {output_path}")
    print(f"Saved: {chart_path}")
    print("Saved utilization charts:")
    for path in utilization_charts:
        print(f"- {path}")
    print()
    print("Done. Open data/outputs/ for CSV outputs and data/outputs/charts/ for charts.")


if __name__ == "__main__":
    main()
