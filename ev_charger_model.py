"""
EV Charger Site-Readiness and Right-Sizing Starter Model

What this script does:
1. Reads sites.csv
2. Scores each site for demand, feasibility, safety, and equity
3. Estimates charging sessions per day
4. Recommends starter EV charging ports now, 2035, and 2050
5. Flags sites needing AHJ / Fire Marshal / accessibility / stormwater review
6. Explains the review reason in plain language
7. Exports site_results.csv and two charts

Run in PyCharm:
- Put this file and sites.csv in the same folder.
- Install packages:
    pip install pandas numpy matplotlib
- Run:
    python ev_charger_model.py
"""

import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def minmax(series):
    """Convert a column to 0-1 scale so different variables can be compared."""
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    if s.max() == s.min():
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def yesno_to_num(value):
    """Convert yes/no style values to 1 or 0."""
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).strip().lower()
    return 1.0 if value in {"1", "y", "yes", "true", "t"} else 0.0


def erlang_c(lambda_hr, mu_hr, ports):
    """
    Simple queueing approximation.

    lambda_hr = charging arrivals per hour
    mu_hr = service rate per port per hour
    ports = number of charging ports

    Returns:
    probability of waiting, average wait in hours, utilization
    """
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


def choose_ports(expected_sessions_day, avg_session_hr, hours_open,
                 max_ports=20, target_utilization=0.70, max_mean_wait_min=10):
    """
    Try 1 port, 2 ports, 3 ports... until the site meets:
    - utilization target
    - average wait target
    """
    arrivals_per_hour = expected_sessions_day / max(hours_open, 1)
    service_rate_per_hour = 1 / max(avg_session_hr, 0.1)

    fallback = None

    for ports in range(1, max_ports + 1):
        _, wait_hours, utilization = erlang_c(
            arrivals_per_hour,
            service_rate_per_hour,
            ports
        )

        wait_minutes = wait_hours * 60 if np.isfinite(wait_hours) else np.inf

        if np.isfinite(wait_minutes) and utilization <= target_utilization and wait_minutes <= max_mean_wait_min:
            return ports, utilization, wait_minutes

        fallback = (ports, utilization, wait_minutes)

    return fallback


def build_review_reason(row):
    """
    Build a plain-English explanation for why a site needs extra review.

    This does not replace Fire Marshal, AHJ, ADA, utility, or stormwater review.
    It only tells us which issues the model noticed.
    """
    reasons = []

    if row["ada_layout_possible"] == 0:
        reasons.append("ADA-accessible layout unresolved")

    if row["fire_access_ok"] == 0:
        reasons.append("Fire apparatus access concern")

    if row["garage_enclosed"] == 1:
        reasons.append("Enclosed garage or limited ventilation/access")

    if row["emergency_disconnect_visible"] == 0:
        reasons.append("Emergency disconnect not clearly visible")

    if row["stormwater_risk"] == 1:
        reasons.append("Stormwater or firefighting runoff concern")

    if row["battery_storage_flag"] == 1:
        reasons.append("Battery storage present or proposed")

    if len(reasons) == 0:
        return "No obvious model-level review trigger"

    return "; ".join(reasons)


def enrich_and_score(sites):
    df = sites.copy()

    yes_no_fields = [
        "ada_layout_possible",
        "fire_access_ok",
        "garage_enclosed",
        "emergency_disconnect_visible",
        "stormwater_risk",
        "battery_storage_flag"
    ]

    for col in yes_no_fields:
        df[col] = df[col].apply(yesno_to_num).fillna(0)

    numeric_fields = [
        "employees_day", "visitors_day", "fleet_vehicles", "parking_spaces",
        "hours_open", "avg_dwell_min", "nearby_households_1mi",
        "nearby_jobs_1mi", "aadt_nearest", "amenities_count_0_5mi",
        "ev_share_local", "existing_l2_ports_1mi", "existing_dcfc_ports_3mi",
        "equity_gap_index", "spare_capacity_kw", "distance_to_service_ft",
        "trenching_ft", "trench_cost_per_ft", "service_upgrade_cost_usd"
    ]

    for col in numeric_fields:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Estimated installation cost:
    # trenching cost + electrical service upgrade cost
    df["install_cost_est_usd"] = (
        df["trenching_ft"] * df["trench_cost_per_ft"] + df["service_upgrade_cost_usd"]
    )

    df["existing_ports_total"] = df["existing_l2_ports_1mi"] + df["existing_dcfc_ports_3mi"]

    normalize_cols = [
        "nearby_households_1mi", "nearby_jobs_1mi", "aadt_nearest",
        "amenities_count_0_5mi", "avg_dwell_min", "existing_ports_total",
        "spare_capacity_kw", "distance_to_service_ft", "install_cost_est_usd",
        "equity_gap_index"
    ]

    for col in normalize_cols:
        df[col + "_n"] = minmax(df[col])

    # Demand subscore: higher means more likely demand.
    # Existing nearby chargers reduce demand because the area may already be served.
    df["demand_subscore"] = 100 * (
        0.30 * minmax(df["ev_share_local"]) +
        0.20 * df["nearby_jobs_1mi_n"] +
        0.20 * df["nearby_households_1mi_n"] +
        0.10 * df["aadt_nearest_n"] +
        0.10 * df["amenities_count_0_5mi_n"] +
        0.10 * df["avg_dwell_min_n"] -
        0.20 * df["existing_ports_total_n"]
    ).clip(lower=0)

    # Feasibility subscore: higher means easier to build.
    # High spare capacity helps. High installation cost and long service distance hurt.
    df["feasibility_subscore"] = 100 * (
        0.35 * df["spare_capacity_kw_n"] +
        0.25 * (1 - df["install_cost_est_usd_n"]) +
        0.20 * (1 - df["distance_to_service_ft_n"]) +
        0.20 * df["ada_layout_possible"]
    ).clip(lower=0)

    # Safety subscore: higher means fewer safety/site-review concerns.
    df["safety_subscore"] = 100 * (
        0.35 * df["fire_access_ok"] +
        0.20 * (1 - df["garage_enclosed"]) +
        0.20 * df["emergency_disconnect_visible"] +
        0.15 * (1 - df["stormwater_risk"]) +
        0.10 * (1 - df["battery_storage_flag"])
    ).clip(lower=0)

    # Final readiness score:
    # weighted average of demand, feasibility, safety, and equity.
    df["readiness_score"] = (
        0.45 * df["demand_subscore"] +
        0.30 * df["feasibility_subscore"] +
        0.15 * df["safety_subscore"] +
        0.10 * (100 * df["equity_gap_index_n"])
    ).round(1)

    # Site-type assumptions for early prototype.
    # These are adjustable assumptions, not permanent facts.
    behavior = {
        "library": {"visitor_capture": 0.07, "employee_capture": 0.04,
                    "need_factor": 0.55, "avg_session_hr": 1.5, "target_util": 0.65},
        "office": {"visitor_capture": 0.05, "employee_capture": 0.05,
                   "need_factor": 0.50, "avg_session_hr": 2.0, "target_util": 0.65},
        "clinic": {"visitor_capture": 0.06, "employee_capture": 0.04,
                   "need_factor": 0.50, "avg_session_hr": 2.0, "target_util": 0.65},
        "garage": {"visitor_capture": 0.05, "employee_capture": 0.03,
                   "need_factor": 0.60, "avg_session_hr": 4.0, "target_util": 0.60},
        "fleet": {"visitor_capture": 0.00, "employee_capture": 0.00,
                  "need_factor": 0.00, "avg_session_hr": 3.0, "target_util": 0.70},
    }

    output_rows = []

    for _, row in df.iterrows():
        site_type = str(row["site_type"]).lower()
        b = behavior.get(
            site_type,
            {"visitor_capture": 0.06, "employee_capture": 0.04,
             "need_factor": 0.50, "avg_session_hr": 2.0, "target_util": 0.65}
        )

        public_sessions = (
            row["visitors_day"] * row["ev_share_local"] * b["visitor_capture"] * b["need_factor"] +
            row["employees_day"] * row["ev_share_local"] * b["employee_capture"] * b["need_factor"]
        )

        # Equity and amenities can increase public value/demand.
        # Existing ports reduce new need because the area may already be served.
        public_sessions *= (
            (1 + 0.30 * row["equity_gap_index"]) *
            (1 + 0.10 * row["amenities_count_0_5mi_n"]) *
            (1 - 0.20 * row["existing_ports_total_n"])
        )

        # Simple fleet assumption:
        # each two fleet vehicles create about one daily charging session.
        fleet_sessions = max(0, row["fleet_vehicles"] * 0.5)

        expected_sessions_day = max(0.3, public_sessions + fleet_sessions)

        rec_now, util, wait_min = choose_ports(
            expected_sessions_day=expected_sessions_day,
            avg_session_hr=b["avg_session_hr"],
            hours_open=max(row["hours_open"], 1),
            target_utilization=b["target_util"]
        )

        # Future growth assumptions:
        # 2035 = 60% more charging demand.
        # 2050 = 140% more charging demand.
        rec_2035, _, _ = choose_ports(
            expected_sessions_day * 1.6,
            b["avg_session_hr"],
            max(row["hours_open"], 1)
        )

        rec_2050, _, _ = choose_ports(
            expected_sessions_day * 2.4,
            b["avg_session_hr"],
            max(row["hours_open"], 1)
        )

        output_rows.append([
            expected_sessions_day,
            b["avg_session_hr"],
            rec_now,
            rec_2035,
            rec_2050,
            util,
            wait_min
        ])

    df[[
        "expected_sessions_day",
        "avg_session_hr",
        "recommended_ports_now",
        "recommended_ports_2035",
        "recommended_ports_2050",
        "estimated_utilization",
        "mean_wait_min"
    ]] = pd.DataFrame(output_rows, index=df.index)

    # AHJ means Authority Having Jurisdiction.
    # This flag means the site should get extra review before moving forward.
    df["ahj_review_flag"] = (
        (df["garage_enclosed"] == 1) |
        (df["battery_storage_flag"] == 1) |
        (df["fire_access_ok"] == 0) |
        (df["emergency_disconnect_visible"] == 0) |
        (df["stormwater_risk"] == 1) |
        (df["ada_layout_possible"] == 0)
    ).astype(int)

    # New plain-English review explanation.
    df["review_reason"] = df.apply(build_review_reason, axis=1)

    return df


def make_readiness_chart(results):
    plot_df = results.sort_values("readiness_score", ascending=True)

    plt.figure(figsize=(9, 5))
    plt.barh(plot_df["site_name"], plot_df["readiness_score"])
    plt.xlabel("Readiness score")
    plt.title("Public EV Charging Site Readiness")
    plt.tight_layout()
    plt.savefig("readiness_score_chart.png", dpi=200)
    plt.show()


def make_utilization_chart(results):
    first_site = results.iloc[0]

    expected_sessions_day = float(first_site["expected_sessions_day"])
    avg_session_hr = float(first_site["avg_session_hr"])
    hours_open = float(first_site["hours_open"])
    site_name = str(first_site["site_name"])

    ports_list = []
    utilization_list = []

    for ports in range(1, 11):
        arrivals_per_hour = expected_sessions_day / max(hours_open, 1)
        service_rate_per_hour = 1 / max(avg_session_hr, 0.1)
        _, _, utilization = erlang_c(arrivals_per_hour, service_rate_per_hour, ports)

        ports_list.append(ports)
        utilization_list.append(utilization)

    plt.figure(figsize=(7, 4))
    plt.plot(ports_list, utilization_list, marker="o")
    plt.axhline(0.70, linestyle="--", label="70% target")
    plt.xlabel("Ports installed")
    plt.ylabel("Estimated utilization")
    plt.title(f"Utilization vs Ports: {site_name}")
    plt.legend()
    plt.tight_layout()
    plt.savefig("utilization_vs_ports_chart.png", dpi=200)
    plt.show()


def main():
    sites = pd.read_csv("sites.csv")
    results = enrich_and_score(sites)

    display_cols = [
        "site_id",
        "site_name",
        "site_type",
        "readiness_score",
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
        "review_reason"
    ]

    final_results = results[display_cols].sort_values("readiness_score", ascending=False)

    print("\nEV CHARGER SITE-READINESS RESULTS")
    print("----------------------------------")
    print(final_results.to_string(index=False))

    final_results.to_csv("site_results.csv", index=False)
    print("\nSaved: site_results.csv")

    make_readiness_chart(results)
    print("Saved: readiness_score_chart.png")

    make_utilization_chart(results)
    print("Saved: utilization_vs_ports_chart.png")

    print("\nDone. Open site_results.csv and the two PNG charts in this folder.")


if __name__ == "__main__":
    main()
