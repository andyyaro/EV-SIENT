from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_DIR = Path("data/outputs")
INPUT_DIR = Path("data/inputs")
TABLEAU_DIR = OUTPUT_DIR / "tableau"
DISCLAIMER = "Planning-support artifact only. Confirm site details before project decisions."

EXPECTED_EXPORTS = [
    "tableau_site_readiness.csv",
    "tableau_site_map.csv",
    "tableau_map_points.csv",
    "tableau_port_growth.csv",
    "tableau_review_burden.csv",
    "tableau_review_burden_map.csv",
    "tableau_profile_score_heatmap.csv",
    "tableau_profile_subscore_heatmap.csv",
    "tableau_profile_rank_stability.csv",
    "tableau_data_confidence.csv",
    "tableau_data_quality_issues.csv",
    "tableau_port_sizing_scenario_heatmap.csv",
    "tableau_port_utilization_simulation.csv",
    "tableau_action_recommendation_matrix.csv",
    "tableau_action_decision_quadrant_clean.csv",
]


def required_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required {label} file not found: {path}")
    return pd.read_csv(path)


def clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace("\n", " ").replace("\r", " ").strip()


def numeric(series: pd.Series, default: float = 0) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default)


def label(site_id: object, site_name: object) -> str:
    return f"{clean(site_id)} — {clean(site_name)}"


def row_label(row: pd.Series) -> str:
    left = "Site ID" if "Site ID" in row else "site_id"
    right = "Site Name" if "Site Name" in row else "site_name"
    return label(row[left], row[right])


def write_csv(df: pd.DataFrame, name: str, quote_all: bool = False) -> None:
    TABLEAU_DIR.mkdir(parents=True, exist_ok=True)
    quoting = csv.QUOTE_ALL if quote_all else csv.QUOTE_MINIMAL
    path = TABLEAU_DIR / name
    df.to_csv(path, index=False, quoting=quoting)
    print(f"Wrote {path} ({len(df)} rows)")


def county(site_id: object) -> str:
    text = clean(site_id).upper()
    if text.startswith("FFX"):
        return "Fairfax"
    if text.startswith("PWC"):
        return "Prince William"
    return "Review"


def tier_short(value: object) -> str:
    text = clean(value)
    lower = text.lower()
    if "tier 1" in lower:
        return "Tier 1"
    if "tier 2" in lower:
        return "Tier 2"
    if "tier 3" in lower:
        return "Tier 3"
    if "high-review" in lower or "high review" in lower:
        return "High-review"
    if "special" in lower or "low public" in lower:
        return "Special-use"
    return text or "Review"


def count_flags(value: object) -> int:
    text = clean(value)
    if not text or text.lower() in {"none", "nan"}:
        return 0
    return len([part for part in text.split(";") if part.strip()])


def risk_points(value: object) -> int:
    text = clean(value).lower()
    if "high" in text:
        return 3
    if "medium" in text:
        return 2
    if "low" in text:
        return 1
    return 2


def confidence_points(value: object) -> int:
    text = clean(value).lower()
    if "low" in text:
        return 2
    if "medium" in text:
        return 1
    if "high" in text:
        return 0
    return 1


def burden_level(score: object) -> str:
    value = float(score) if str(score) not in {"", "nan"} else 0
    if value <= 3:
        return "Lower review burden"
    if value <= 5:
        return "Moderate review burden"
    return "Higher review burden"


def load_base() -> pd.DataFrame:
    summary = required_csv(OUTPUT_DIR / "v2_executive_site_summary.csv", "executive summary")
    inputs = required_csv(INPUT_DIR / "real_sites_v2.csv", "site input")
    needed = ["site_id", "address", "city", "state", "zip", "lat", "lon"]
    missing = sorted(set(needed) - set(inputs.columns))
    if missing:
        raise ValueError(f"real_sites_v2.csv missing columns: {missing}")
    base = summary.merge(inputs[needed], on="site_id", how="left")
    base["Site Label"] = base.apply(lambda r: label(r["site_id"], r["site_name"]), axis=1)
    base["County"] = base["site_id"].map(county)
    base["Tier"] = base["recommendation_tier"].map(tier_short)
    base["Review Flag Count"] = base["major_review_flags"].map(count_flags)
    base["Review Burden Score"] = (
        base["Review Flag Count"]
        + base["electrical_risk_level"].map(risk_points)
        + base["data_confidence_level"].map(confidence_points)
        + numeric(base["scenario_future_capacity_gap"])
    ).round(0).astype(int)
    base["Review Burden Level"] = base["Review Burden Score"].map(burden_level)
    base["Address"] = base.apply(
        lambda r: ", ".join(part for part in [clean(r.address), clean(r.city), clean(r.state), clean(r.zip)] if part),
        axis=1,
    )
    return base.sort_values("model_rank")


def build_core(base: pd.DataFrame) -> None:
    readiness = pd.DataFrame({
        "Rank": numeric(base["model_rank"]).astype(int),
        "Site ID": base["site_id"].map(clean),
        "Site Name": base["site_name"].map(clean),
        "Readiness Score": numeric(base["readiness_score"]),
        "Tier": base["Tier"].map(clean),
        "Install Now Ports": numeric(base["ports_now"]).astype(int),
        "Future Ready Ports": numeric(base["future_ready_capacity"]).astype(int),
        "Expansion Strategy": base["expansion_strategy"].map(clean),
        "Electrical Risk Level": base["electrical_risk_level"].map(clean),
        "Site Label": base["Site Label"].map(clean),
    })
    write_csv(readiness, "tableau_site_readiness.csv")

    site_map = pd.DataFrame({
        "Rank": readiness["Rank"],
        "Site ID": readiness["Site ID"],
        "Site Name": readiness["Site Name"],
        "County": base["County"].map(clean),
        "Address": base["Address"].map(clean),
        "Latitude": numeric(base["lat"]),
        "Longitude": numeric(base["lon"]),
        "Readiness Score": readiness["Readiness Score"],
        "Tier": readiness["Tier"],
        "Install Now Ports": readiness["Install Now Ports"],
        "Future Ready Ports": readiness["Future Ready Ports"],
        "Electrical Risk Level": readiness["Electrical Risk Level"],
        "Expansion Strategy": readiness["Expansion Strategy"],
        "Site Label": readiness["Site Label"],
    })
    write_csv(site_map, "tableau_site_map.csv")

    points = site_map.copy()
    points["Point Type"] = "Candidate site"
    points["Point Name"] = points["Site Name"]
    points["Map Label"] = points["Site ID"]
    points["Map Size"] = (numeric(points["Future Ready Ports"]) * 10 + 40).astype(int)
    points["Reference Category"] = "Candidate EV charging site"
    points["Tooltip Text"] = points.apply(
        lambda r: f"{r['Site Label']}\nRank: {r['Rank']}\nReadiness Score: {r['Readiness Score']}\n{DISCLAIMER}", axis=1
    )
    write_csv(points[[
        "Rank", "Site ID", "Site Name", "County", "Address", "Latitude", "Longitude", "Readiness Score",
        "Tier", "Install Now Ports", "Future Ready Ports", "Electrical Risk Level", "Expansion Strategy",
        "Site Label", "Point Type", "Point Name", "Map Label", "Map Size", "Reference Category", "Tooltip Text",
    ]], "tableau_map_points.csv")


def build_growth(base: pd.DataFrame) -> None:
    rows = []
    horizons = [("Install now", 1, "ports_now"), ("2035 high planning", 2, "ports_2035_high"), ("Future-ready capacity", 3, "future_ready_capacity")]
    for _, row in base.iterrows():
        for horizon, order, col in horizons:
            ports = int(pd.to_numeric(pd.Series([row.get(col, 0)]), errors="coerce").fillna(0).iloc[0])
            rows.append({
                "Rank": int(row["model_rank"]),
                "Site ID": clean(row["site_id"]),
                "Site Name": clean(row["site_name"]),
                "Site Label": clean(row["Site Label"]),
                "Planning Horizon": horizon,
                "Planning Horizon Order": order,
                "Recommended Ports": ports,
                "Install Now Ports": int(row.get("ports_now", 0)),
                "Estimated 2035 Ports": int(row.get("ports_2035_high", 0)),
                "Future Ready Ports": int(row.get("future_ready_capacity", 0)),
                "Readiness Score": float(row.get("readiness_score", 0)),
                "Tier": clean(row["Tier"]),
                "Electrical Risk Level": clean(row.get("electrical_risk_level", "")),
                "Expansion Strategy": clean(row.get("expansion_strategy", "")),
                "Tooltip Text": f"{row['Site Label']}\nPlanning Horizon: {horizon}\nRecommended Ports: {ports}\n{DISCLAIMER}",
            })
    write_csv(pd.DataFrame(rows), "tableau_port_growth.csv")


def build_review(base: pd.DataFrame) -> None:
    review = pd.DataFrame({
        "Rank": numeric(base["model_rank"]).astype(int),
        "Site ID": base["site_id"].map(clean),
        "Site Name": base["site_name"].map(clean),
        "Site Label": base["Site Label"].map(clean),
        "County": base["County"].map(clean),
        "Readiness Score": numeric(base["readiness_score"]),
        "Tier": base["Tier"].map(clean),
        "Install Now Ports": numeric(base["ports_now"]).astype(int),
        "Future Ready Ports": numeric(base["future_ready_capacity"]).astype(int),
        "Electrical Risk Level": base["electrical_risk_level"].map(clean),
        "Expansion Strategy": base["expansion_strategy"].map(clean),
        "Review Burden Score": base["Review Burden Score"].astype(int),
        "Review Burden Level": base["Review Burden Level"].map(clean),
        "Review Flags": base["major_review_flags"].map(clean),
    })
    review["Tooltip Text"] = review.apply(
        lambda r: f"{r['Site Label']}\nReview Burden Score: {r['Review Burden Score']}\nReview Burden Level: {r['Review Burden Level']}\nReview Flags: {r['Review Flags']}\n{DISCLAIMER}", axis=1
    )
    write_csv(review[[
        "Rank", "Site ID", "Site Name", "Site Label", "County", "Readiness Score", "Tier", "Install Now Ports",
        "Future Ready Ports", "Electrical Risk Level", "Expansion Strategy", "Review Burden Score", "Review Burden Level",
        "Review Flags", "Tooltip Text",
    ]], "tableau_review_burden.csv")

    review_map = review.copy()
    review_map["Address"] = base["Address"].map(clean)
    review_map["Latitude"] = numeric(base["lat"])
    review_map["Longitude"] = numeric(base["lon"])
    review_map["Point Type"] = "Candidate site"
    review_map["Map Label"] = review_map["Site ID"]
    review_map["Map Size"] = (numeric(review_map["Review Burden Score"]) * 8 + 35).astype(int)
    review_map["Map Color Group"] = review_map["Review Burden Level"]
    review_map["Reference Category"] = "Review burden candidate site"
    write_csv(review_map[[
        "Rank", "Site ID", "Site Name", "Site Label", "County", "Readiness Score", "Tier", "Install Now Ports",
        "Future Ready Ports", "Electrical Risk Level", "Expansion Strategy", "Review Burden Score", "Review Burden Level",
        "Review Flags", "Tooltip Text", "Address", "Latitude", "Longitude", "Point Type", "Map Label", "Map Size",
        "Map Color Group", "Reference Category",
    ]], "tableau_review_burden_map.csv")


def build_profile_exports() -> None:
    profiles = required_csv(OUTPUT_DIR / "v2_profile_results.csv", "profile results")
    profiles["Site Label"] = profiles.apply(row_label, axis=1)
    order = profiles[["profile_name", "profile_label"]].drop_duplicates().reset_index(drop=True)
    order["Profile Sort"] = order.index + 1
    profiles = profiles.merge(order, on=["profile_name", "profile_label"], how="left")
    profile_heatmap = profiles.rename(columns={
        "site_id": "Site ID", "site_name": "Site Name", "site_type": "Site Type", "profile_name": "Profile Name",
        "profile_label": "Profile Label", "profile_description": "Profile Description", "profile_rank": "Profile Rank",
        "profile_readiness_score": "Profile Readiness Score", "base_model_rank": "Base Model Rank",
        "base_readiness_score": "Base Readiness Score", "rank_change_vs_base": "Rank Change vs Base",
        "base_recommendation_tier": "Base Recommendation Tier", "profile_recommendation_tier": "Profile Recommendation Tier",
        "demand_weight": "Demand Weight", "feasibility_weight": "Feasibility Weight", "safety_weight": "Safety Weight", "equity_weight": "Equity Weight",
    })
    profile_heatmap["Tooltip Text"] = profile_heatmap.apply(lambda r: f"{r['Site Label']}\nProfile: {r['Profile Label']}\nProfile Rank: {r['Profile Rank']}\n{DISCLAIMER}", axis=1)
    write_csv(profile_heatmap[[
        "Site ID", "Site Name", "Site Label", "Site Type", "Profile Name", "Profile Label", "Profile Sort", "Profile Description",
        "Profile Rank", "Profile Readiness Score", "Base Model Rank", "Base Readiness Score", "Rank Change vs Base",
        "Base Recommendation Tier", "Profile Recommendation Tier", "Demand Weight", "Feasibility Weight", "Safety Weight", "Equity Weight", "Tooltip Text",
    ]], "tableau_profile_score_heatmap.csv")

    dim_map = {"demand_subscore": "Demand", "feasibility_subscore": "Electrical / Feasibility", "safety_subscore": "Safety / Review", "equity_score": "Equity"}
    dim_order = {"Demand": 1, "Electrical / Feasibility": 2, "Safety / Review": 3, "Equity": 4}
    sub = profiles.melt(
        id_vars=["site_id", "site_name", "site_type", "Site Label", "profile_name", "profile_label", "profile_description", "profile_rank", "profile_readiness_score", "base_model_rank", "base_readiness_score"],
        value_vars=list(dim_map), var_name="Score Dimension Raw", value_name="Dimension Score"
    )
    sub["Score Dimension"] = sub["Score Dimension Raw"].map(dim_map)
    sub["Dimension Sort"] = sub["Score Dimension"].map(dim_order)
    sub = sub.rename(columns={
        "site_id": "Site ID", "site_name": "Site Name", "site_type": "Site Type", "profile_name": "Profile Name",
        "profile_label": "Profile Label", "profile_description": "Profile Description", "profile_rank": "Profile Rank",
        "profile_readiness_score": "Profile Readiness Score", "base_model_rank": "Base Model Rank", "base_readiness_score": "Base Readiness Score",
    })
    sub["Tooltip Text"] = sub.apply(lambda r: f"{r['Site Label']}\nProfile: {r['Profile Label']}\nDimension: {r['Score Dimension']}\nScore: {r['Dimension Score']:.1f}\n{DISCLAIMER}", axis=1)
    write_csv(sub[[
        "Site ID", "Site Name", "Site Label", "Site Type", "Profile Name", "Profile Label", "Profile Description", "Profile Rank",
        "Profile Readiness Score", "Base Model Rank", "Base Readiness Score", "Score Dimension", "Dimension Sort", "Dimension Score", "Tooltip Text",
    ]], "tableau_profile_subscore_heatmap.csv")

    rank = required_csv(OUTPUT_DIR / "v2_profile_rank_summary.csv", "profile rank summary")
    rank["Site Label"] = rank.apply(row_label, axis=1)
    rank["Stability Level"] = np.select([rank["profile_rank_range"] <= 1, rank["profile_rank_range"] <= 3, rank["profile_rank_range"] <= 5], ["Very stable", "Moderately stable", "Sensitive"], default="Highly sensitive")
    rank = rank.rename(columns={
        "site_id": "Site ID", "site_name": "Site Name", "best_profile_rank": "Best Profile Rank", "worst_profile_rank": "Worst Profile Rank",
        "average_profile_rank": "Average Profile Rank", "min_profile_score": "Minimum Profile Score", "max_profile_score": "Maximum Profile Score",
        "average_profile_score": "Average Profile Score", "base_model_rank": "Base Model Rank", "base_readiness_score": "Base Readiness Score",
        "profile_rank_range": "Profile Rank Range", "profile_score_range": "Profile Score Range",
    })
    rank["Tooltip Text"] = rank.apply(lambda r: f"{r['Site Label']}\nBase Rank: {r['Base Model Rank']}\nRank Range: {r['Profile Rank Range']}\n{DISCLAIMER}", axis=1)
    write_csv(rank[[
        "Site ID", "Site Name", "Site Label", "Base Model Rank", "Base Readiness Score", "Best Profile Rank", "Worst Profile Rank",
        "Average Profile Rank", "Minimum Profile Score", "Maximum Profile Score", "Average Profile Score", "Profile Rank Range",
        "Profile Score Range", "Stability Level", "Tooltip Text",
    ]], "tableau_profile_rank_stability.csv")


def build_confidence_exports() -> None:
    summary = required_csv(OUTPUT_DIR / "v2_executive_site_summary.csv", "executive summary")
    quality = required_csv(OUTPUT_DIR / "v2_data_quality_report.csv", "data quality report")
    summary["Site Label"] = summary.apply(row_label, axis=1)
    issues = quality.groupby(["site_id", "site_name"]).agg(
        Data_Review_Issue_Count=("issue", "count"),
        Fields_To_Review=("field", lambda x: "; ".join(sorted(set(map(str, x))))),
        Recommended_Next_Steps=("recommended_next_step", lambda x: "; ".join(list(dict.fromkeys(map(str, x)))[:3])),
    ).reset_index()
    severity = pd.crosstab(quality["site_id"], quality["severity"]).reset_index()
    for col in ["INFO", "REVIEW"]:
        if col not in severity.columns:
            severity[col] = 0
    data = summary.merge(issues, on=["site_id", "site_name"], how="left").merge(severity, on="site_id", how="left")
    data["Data_Review_Issue_Count"] = data["Data_Review_Issue_Count"].fillna(0).astype(int)
    for col in [c for c in data.columns if c.isupper()]:
        data[col] = data[col].fillna(0).astype(int)
    data["Fields_To_Review"] = data["Fields_To_Review"].fillna("No flagged fields")
    data["Recommended_Next_Steps"] = data["Recommended_Next_Steps"].fillna("No immediate issue flagged by the current report.")
    data = data.rename(columns={
        "model_rank": "Model Rank", "site_id": "Site ID", "site_name": "Site Name", "readiness_score": "Readiness Score",
        "data_confidence_level": "Data Confidence Level", "recommendation_tier": "Recommendation Tier", "electrical_risk_level": "Electrical Risk Level",
        "planning_recommendation": "Planning Recommendation", "data_needed_next": "Data Needed Next", "Data_Review_Issue_Count": "Data Review Issue Count",
        "Fields_To_Review": "Fields To Review", "Recommended_Next_Steps": "Recommended Next Steps",
    })
    data["Tooltip Text"] = data.apply(lambda r: f"{r['Site Label']}\nData Confidence: {r['Data Confidence Level']}\nIssues: {r['Data Review Issue Count']}\n{DISCLAIMER}", axis=1)
    keep = ["Model Rank", "Site ID", "Site Name", "Site Label", "Readiness Score", "Data Confidence Level", "Data Review Issue Count", "Recommendation Tier", "Electrical Risk Level", "Planning Recommendation", "Data Needed Next", "Fields To Review", "Recommended Next Steps", "Tooltip Text"]
    write_csv(data[keep + [c for c in data.columns if c.isupper()]], "tableau_data_confidence.csv")

    detail = quality.rename(columns={"severity": "Severity", "site_id": "Site ID", "site_name": "Site Name", "field": "Field", "issue": "Issue", "current_value": "Current Value", "recommended_next_step": "Recommended Next Step"})
    detail["Site Label"] = detail.apply(lambda r: label(r["Site ID"], r["Site Name"]), axis=1)
    detail["Tooltip Text"] = detail.apply(lambda r: f"{r['Site Label']}\nSeverity: {r['Severity']}\nField: {r['Field']}\nIssue: {r['Issue']}\n{DISCLAIMER}", axis=1)
    write_csv(detail[["Severity", "Site ID", "Site Name", "Site Label", "Field", "Issue", "Current Value", "Recommended Next Step", "Tooltip Text"]], "tableau_data_quality_issues.csv")


def build_scenario_and_simulation() -> None:
    scenarios = required_csv(OUTPUT_DIR / "v2_port_sizing_scenario_results.csv", "port-sizing scenario results")
    scenarios["Site Label"] = scenarios.apply(row_label, axis=1)
    order = scenarios[["scenario_name", "scenario_label"]].drop_duplicates().reset_index(drop=True)
    order["Scenario Sort"] = order.index + 1
    scenarios = scenarios.merge(order, on=["scenario_name", "scenario_label"], how="left")
    scenarios["Future Gap Category"] = np.select([scenarios["future_capacity_gap"] <= 0, scenarios["future_capacity_gap"] == 1, scenarios["future_capacity_gap"] >= 2], ["No future capacity gap", "One-port future gap", "Major future capacity gap"], default="Review needed")
    scen = scenarios.rename(columns={
        "scenario_name": "Scenario Name", "scenario_label": "Scenario Label", "scenario_description": "Scenario Description", "model_rank": "Model Rank",
        "site_id": "Site ID", "site_name": "Site Name", "readiness_score": "Readiness Score", "ports_now": "Install Now Ports",
        "future_ready_capacity": "Future Ready Capacity", "scenario_min_ports_current": "Scenario Minimum Ports Current",
        "scenario_min_ports_2035_high": "Scenario Minimum Ports 2035 High", "scenario_min_ports_2050_high": "Scenario Minimum Ports 2050 High",
        "current_capacity_gap": "Current Capacity Gap", "future_capacity_gap": "Future Capacity Gap", "current_alignment": "Current Alignment",
        "future_capacity_alignment": "Future Capacity Alignment", "current_status_at_ports_now": "Current Status at Install Now Ports",
        "current_wait_at_ports_now": "Current Wait at Install Now Ports", "current_utilization_at_ports_now": "Current Utilization at Install Now Ports",
        "future_status_at_future_ready": "Future Status at Future Ready Capacity", "future_wait_at_future_ready": "Future Wait at Future Ready Capacity",
        "future_utilization_at_future_ready": "Future Utilization at Future Ready Capacity", "future_queue_risk_at_future_ready": "Future Queue Risk at Future Ready Capacity",
    })
    scen["Tooltip Text"] = scen.apply(lambda r: f"{r['Site Label']}\nScenario: {r['Scenario Label']}\nFuture Gap: {r['Future Capacity Gap']}\n{DISCLAIMER}", axis=1)
    write_csv(scen[[
        "Scenario Name", "Scenario Label", "Scenario Sort", "Scenario Description", "Model Rank", "Site ID", "Site Name", "Site Label",
        "Readiness Score", "Install Now Ports", "Future Ready Capacity", "Scenario Minimum Ports Current", "Scenario Minimum Ports 2035 High",
        "Scenario Minimum Ports 2050 High", "Current Capacity Gap", "Future Capacity Gap", "Future Gap Category", "Current Alignment",
        "Future Capacity Alignment", "Current Status at Install Now Ports", "Current Wait at Install Now Ports", "Current Utilization at Install Now Ports",
        "Future Status at Future Ready Capacity", "Future Wait at Future Ready Capacity", "Future Utilization at Future Ready Capacity",
        "Future Queue Risk at Future Ready Capacity", "Tooltip Text",
    ]], "tableau_port_sizing_scenario_heatmap.csv")

    sim = required_csv(OUTPUT_DIR / "v2_port_utilization_simulation.csv", "port utilization simulation")
    sim["Site Label"] = sim.apply(row_label, axis=1)
    sim["Is Install Now Ports"] = sim["is_ports_now"].astype(str).str.lower().eq("true")
    sim["Is Future Ready Capacity"] = sim["is_future_ready_capacity"].astype(str).str.lower().eq("true")
    sim["Recommended Port Marker"] = np.select([sim["Is Install Now Ports"] & sim["Is Future Ready Capacity"], sim["Is Install Now Ports"], sim["Is Future Ready Capacity"]], ["Install now and future-ready capacity", "Install now ports", "Future-ready capacity"], default="Simulation test point")
    demand_order = sim[["demand_case"]].drop_duplicates().reset_index(drop=True)
    demand_order["Demand Case Sort"] = demand_order.index + 1
    sim = sim.merge(demand_order, on="demand_case", how="left")
    sim = sim.rename(columns={"site_id": "Site ID", "site_name": "Site Name", "model_rank": "Model Rank", "readiness_score": "Readiness Score", "demand_case": "Demand Case", "session_multiplier": "Session Multiplier", "sessions_day": "Sessions per Day", "port_count": "Port Count", "avg_charge_hours": "Average Charge Hours", "charging_window_hours": "Charging Window Hours", "peak_factor": "Peak Factor", "utilization_pct": "Utilization Percent", "peak_demand_ratio": "Peak Demand Ratio", "estimated_wait_min": "Estimated Wait Minutes", "queue_risk_level": "Queue Risk Level", "capacity_status": "Capacity Status"})
    sim["Tooltip Text"] = sim.apply(lambda r: f"{r['Site Label']}\nDemand Case: {r['Demand Case']}\nPort Count: {r['Port Count']}\nUtilization: {r['Utilization Percent']}%\n{DISCLAIMER}", axis=1)
    write_csv(sim[["Site ID", "Site Name", "Site Label", "Model Rank", "Readiness Score", "Demand Case", "Demand Case Sort", "Session Multiplier", "Sessions per Day", "Port Count", "Average Charge Hours", "Charging Window Hours", "Peak Factor", "Utilization Percent", "Peak Demand Ratio", "Estimated Wait Minutes", "Queue Risk Level", "Capacity Status", "Is Install Now Ports", "Is Future Ready Capacity", "Recommended Port Marker", "Tooltip Text"]], "tableau_port_utilization_simulation.csv")


def quadrant(row: pd.Series) -> str:
    if row["Readiness Score"] >= 50 and row["Implementation Complexity Score"] <= 5:
        return "Advance"
    if row["Readiness Score"] >= 50:
        return "High potential, review first"
    if row["Implementation Complexity Score"] <= 5:
        return "Monitor / small pilot"
    return "Clarify use case"


def build_action_exports() -> None:
    summary = required_csv(OUTPUT_DIR / "v2_executive_site_summary.csv", "executive summary")
    summary["Site Label"] = summary.apply(row_label, axis=1)
    summary["Action Priority"] = np.where(summary["recommendation_tier"].astype(str).str.contains("Tier 1", case=False), 1, np.where(summary["recommendation_tier"].astype(str).str.contains("Tier 2", case=False), 2, 4))
    summary["Action Group"] = np.select([summary["Action Priority"] == 1, summary["Action Priority"] == 2, summary["recommendation_tier"].astype(str).str.contains("Tier 3", case=False)], ["Advance to site screening", "Refine assumptions", "Monitor or small pilot"], default="Clarify before advancement")
    matrix = summary.rename(columns={"model_rank": "Model Rank", "site_id": "Site ID", "site_name": "Site Name", "readiness_score": "Readiness Score", "data_confidence_level": "Data Confidence Level", "recommendation_tier": "Recommendation Tier", "action_label": "Action Label", "electrical_risk_level": "Electrical Risk Level", "ports_now": "Install Now Ports", "ports_2035_base": "Ports 2035 Base", "ports_2035_high": "Ports 2035 High", "ports_2050_base": "Ports 2050 Base", "ports_2050_high": "Ports 2050 High", "future_ready_capacity": "Future Ready Capacity", "expansion_strategy": "Expansion Strategy", "scenario_future_capacity_gap": "Scenario Future Capacity Gap", "scenario_sensitivity_level": "Scenario Sensitivity Level", "scenario_stress_note": "Scenario Stress Note", "major_review_flags": "Major Review Flags", "planning_recommendation": "Planning Recommendation", "data_needed_next": "Data Needed Next"})
    matrix["Tooltip Text"] = matrix.apply(lambda r: f"{r['Site Label']}\nAction Group: {r['Action Group']}\nReadiness Score: {r['Readiness Score']}\n{DISCLAIMER}", axis=1)
    write_csv(matrix[["Model Rank", "Action Priority", "Action Group", "Site ID", "Site Name", "Site Label", "Readiness Score", "Data Confidence Level", "Recommendation Tier", "Action Label", "Electrical Risk Level", "Install Now Ports", "Ports 2035 Base", "Ports 2035 High", "Ports 2050 Base", "Ports 2050 High", "Future Ready Capacity", "Expansion Strategy", "Scenario Future Capacity Gap", "Scenario Sensitivity Level", "Scenario Stress Note", "Major Review Flags", "Planning Recommendation", "Data Needed Next", "Tooltip Text"]], "tableau_action_recommendation_matrix.csv")

    q = pd.DataFrame({
        "Model Rank": numeric(summary["model_rank"]).astype(int),
        "Site ID": summary["site_id"].map(clean),
        "Site Name": summary["site_name"].map(clean),
        "Site Label": summary["Site Label"].map(clean),
        "Readiness Score": numeric(summary["readiness_score"]),
        "Implementation Complexity Score": summary["major_review_flags"].map(count_flags) + summary["electrical_risk_level"].map(risk_points) + summary["data_confidence_level"].map(confidence_points) + numeric(summary["scenario_future_capacity_gap"]),
        "Future Ready Capacity": numeric(summary["future_ready_capacity"]),
        "Readiness Threshold": 50.0,
        "Complexity Threshold": 5.0,
        "Electrical Risk Level": summary["electrical_risk_level"].map(clean),
        "Data Confidence Level": summary["data_confidence_level"].map(clean),
        "Scenario Sensitivity Level": summary["scenario_sensitivity_level"].map(clean),
        "Planning Recommendation": summary["planning_recommendation"].map(clean),
        "Data Needed Next": summary["data_needed_next"].map(clean),
    })
    q["Decision Quadrant"] = q.apply(quadrant, axis=1)
    q["Tooltip Text"] = q.apply(lambda r: f"{r['Site Label']} | Decision: {r['Decision Quadrant']} | Readiness Score: {r['Readiness Score']} | Complexity: {r['Implementation Complexity Score']}", axis=1)
    write_csv(q[["Model Rank", "Site ID", "Site Name", "Site Label", "Readiness Score", "Implementation Complexity Score", "Decision Quadrant", "Future Ready Capacity", "Readiness Threshold", "Complexity Threshold", "Electrical Risk Level", "Data Confidence Level", "Scenario Sensitivity Level", "Planning Recommendation", "Data Needed Next", "Tooltip Text"]], "tableau_action_decision_quadrant_clean.csv", quote_all=True)


def main() -> None:
    TABLEAU_DIR.mkdir(parents=True, exist_ok=True)
    base = load_base()
    build_core(base)
    build_growth(base)
    build_review(base)
    build_profile_exports()
    build_confidence_exports()
    build_scenario_and_simulation()
    build_action_exports()
    written = sorted(path.name for path in TABLEAU_DIR.glob("tableau_*.csv"))
    missing = sorted(set(EXPECTED_EXPORTS) - set(written))
    print("\nTABLEAU EXPORT SUMMARY")
    print("----------------------")
    print(f"Expected exports: {len(EXPECTED_EXPORTS)}")
    print(f"Generated exports: {len(written)}")
    if missing:
        raise SystemExit(f"Missing Tableau exports: {missing}")
    print("Status: complete")


if __name__ == "__main__":
    main()
