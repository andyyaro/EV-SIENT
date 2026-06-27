from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_DIR = Path("data/outputs")
TABLEAU_DIR = OUTPUT_DIR / "tableau"
TABLEAU_DIR.mkdir(parents=True, exist_ok=True)

DISCLAIMER = (
    "Planning-support only — not final engineering, permitting, utility, "
    "procurement, fire, ADA, stormwater, or construction approval."
)


def site_label_from_row(row):
    return f"{row['site_id']} — {row['site_name']}"


def safe_text(value):
    if pd.isna(value):
        return ""
    return str(value)


def write_csv(df, filename):
    path = TABLEAU_DIR / filename
    df.to_csv(path, index=False)
    print(f"Wrote {path} ({len(df)} rows)")


# ---------------------------------------------------------------------
# 1. Profile score heat map
# Source: v2_profile_results.csv
# Purpose: Site x scoring profile, colored by profile readiness score
# ---------------------------------------------------------------------

profile_path = OUTPUT_DIR / "v2_profile_results.csv"
profiles = pd.read_csv(profile_path)

profiles["Site Label"] = profiles.apply(site_label_from_row, axis=1)

profile_order = (
    profiles[["profile_name", "profile_label"]]
    .drop_duplicates()
    .reset_index(drop=True)
)
profile_order["Profile Sort"] = profile_order.index + 1

profiles = profiles.merge(
    profile_order,
    on=["profile_name", "profile_label"],
    how="left",
)

profile_heatmap = profiles.rename(
    columns={
        "site_id": "Site ID",
        "site_name": "Site Name",
        "site_type": "Site Type",
        "profile_name": "Profile Name",
        "profile_label": "Profile Label",
        "profile_description": "Profile Description",
        "profile_rank": "Profile Rank",
        "profile_readiness_score": "Profile Readiness Score",
        "base_model_rank": "Base Model Rank",
        "base_readiness_score": "Base Readiness Score",
        "rank_change_vs_base": "Rank Change vs Base",
        "base_recommendation_tier": "Base Recommendation Tier",
        "profile_recommendation_tier": "Profile Recommendation Tier",
        "demand_weight": "Demand Weight",
        "feasibility_weight": "Feasibility Weight",
        "safety_weight": "Safety Weight",
        "equity_weight": "Equity Weight",
    }
)

profile_heatmap["Tooltip Text"] = profile_heatmap.apply(
    lambda row: (
        f"{row['Site Label']}\n\n"
        f"Profile: {row['Profile Label']}\n"
        f"Profile Rank: {row['Profile Rank']}\n"
        f"Profile Readiness Score: {row['Profile Readiness Score']}\n\n"
        f"Base Rank: {row['Base Model Rank']}\n"
        f"Base Readiness Score: {row['Base Readiness Score']}\n"
        f"Rank Change vs Base: {row['Rank Change vs Base']}\n\n"
        f"Profile Tier: {row['Profile Recommendation Tier']}\n\n"
        f"{DISCLAIMER}"
    ),
    axis=1,
)

profile_heatmap = profile_heatmap[
    [
        "Site ID",
        "Site Name",
        "Site Label",
        "Site Type",
        "Profile Name",
        "Profile Label",
        "Profile Sort",
        "Profile Description",
        "Profile Rank",
        "Profile Readiness Score",
        "Base Model Rank",
        "Base Readiness Score",
        "Rank Change vs Base",
        "Base Recommendation Tier",
        "Profile Recommendation Tier",
        "Demand Weight",
        "Feasibility Weight",
        "Safety Weight",
        "Equity Weight",
        "Tooltip Text",
    ]
]

write_csv(profile_heatmap, "tableau_profile_score_heatmap.csv")


# ---------------------------------------------------------------------
# 2. Profile subscore heat map
# Source: v2_profile_results.csv
# Purpose: Site x score dimension, colored by dimension score
# ---------------------------------------------------------------------

dimension_map = {
    "demand_subscore": "Demand",
    "feasibility_subscore": "Electrical / Feasibility",
    "safety_subscore": "Safety / Review",
    "equity_score": "Equity",
}

dimension_order = {
    "Demand": 1,
    "Electrical / Feasibility": 2,
    "Safety / Review": 3,
    "Equity": 4,
}

subscore_long = profiles.melt(
    id_vars=[
        "site_id",
        "site_name",
        "site_type",
        "Site Label",
        "profile_name",
        "profile_label",
        "profile_description",
        "profile_rank",
        "profile_readiness_score",
        "base_model_rank",
        "base_readiness_score",
    ],
    value_vars=list(dimension_map.keys()),
    var_name="Score Dimension Raw",
    value_name="Dimension Score",
)

subscore_long["Score Dimension"] = subscore_long["Score Dimension Raw"].map(dimension_map)
subscore_long["Dimension Sort"] = subscore_long["Score Dimension"].map(dimension_order)

subscore_long = subscore_long.rename(
    columns={
        "site_id": "Site ID",
        "site_name": "Site Name",
        "site_type": "Site Type",
        "profile_name": "Profile Name",
        "profile_label": "Profile Label",
        "profile_description": "Profile Description",
        "profile_rank": "Profile Rank",
        "profile_readiness_score": "Profile Readiness Score",
        "base_model_rank": "Base Model Rank",
        "base_readiness_score": "Base Readiness Score",
    }
)

subscore_long["Tooltip Text"] = subscore_long.apply(
    lambda row: (
        f"{row['Site Label']}\n\n"
        f"Profile: {row['Profile Label']}\n"
        f"Score Dimension: {row['Score Dimension']}\n"
        f"Dimension Score: {row['Dimension Score']:.1f}\n\n"
        f"Overall Profile Readiness Score: {row['Profile Readiness Score']:.1f}\n"
        f"Profile Rank: {row['Profile Rank']}\n\n"
        f"{DISCLAIMER}"
    ),
    axis=1,
)

subscore_long = subscore_long[
    [
        "Site ID",
        "Site Name",
        "Site Label",
        "Site Type",
        "Profile Name",
        "Profile Label",
        "Profile Description",
        "Profile Rank",
        "Profile Readiness Score",
        "Base Model Rank",
        "Base Readiness Score",
        "Score Dimension",
        "Dimension Sort",
        "Dimension Score",
        "Tooltip Text",
    ]
]

write_csv(subscore_long, "tableau_profile_subscore_heatmap.csv")


# ---------------------------------------------------------------------
# 3. Profile rank stability
# Source: v2_profile_rank_summary.csv
# Purpose: Show how stable each site's rank is across profiles
# ---------------------------------------------------------------------

rank_path = OUTPUT_DIR / "v2_profile_rank_summary.csv"
rank = pd.read_csv(rank_path)

rank["Site Label"] = rank.apply(site_label_from_row, axis=1)

rank["Stability Level"] = np.select(
    [
        rank["profile_rank_range"] <= 1,
        rank["profile_rank_range"] <= 3,
        rank["profile_rank_range"] <= 5,
    ],
    [
        "Very stable",
        "Moderately stable",
        "Sensitive",
    ],
    default="Highly sensitive",
)

rank_stability = rank.rename(
    columns={
        "site_id": "Site ID",
        "site_name": "Site Name",
        "best_profile_rank": "Best Profile Rank",
        "worst_profile_rank": "Worst Profile Rank",
        "average_profile_rank": "Average Profile Rank",
        "min_profile_score": "Minimum Profile Score",
        "max_profile_score": "Maximum Profile Score",
        "average_profile_score": "Average Profile Score",
        "base_model_rank": "Base Model Rank",
        "base_readiness_score": "Base Readiness Score",
        "profile_rank_range": "Profile Rank Range",
        "profile_score_range": "Profile Score Range",
    }
)

rank_stability["Tooltip Text"] = rank_stability.apply(
    lambda row: (
        f"{row['Site Label']}\n\n"
        f"Base Rank: {row['Base Model Rank']}\n"
        f"Best Profile Rank: {row['Best Profile Rank']}\n"
        f"Worst Profile Rank: {row['Worst Profile Rank']}\n"
        f"Average Profile Rank: {row['Average Profile Rank']}\n\n"
        f"Rank Range: {row['Profile Rank Range']}\n"
        f"Score Range: {row['Profile Score Range']}\n"
        f"Stability Level: {row['Stability Level']}\n\n"
        f"{DISCLAIMER}"
    ),
    axis=1,
)

rank_stability = rank_stability[
    [
        "Site ID",
        "Site Name",
        "Site Label",
        "Base Model Rank",
        "Base Readiness Score",
        "Best Profile Rank",
        "Worst Profile Rank",
        "Average Profile Rank",
        "Minimum Profile Score",
        "Maximum Profile Score",
        "Average Profile Score",
        "Profile Rank Range",
        "Profile Score Range",
        "Stability Level",
        "Tooltip Text",
    ]
]

write_csv(rank_stability, "tableau_profile_rank_stability.csv")


# ---------------------------------------------------------------------
# 4. Data confidence summary
# Sources: v2_executive_site_summary.csv + v2_data_quality_report.csv
# Purpose: Show confidence level and number of data review issues by site
# ---------------------------------------------------------------------

exec_path = OUTPUT_DIR / "v2_executive_site_summary.csv"
summary = pd.read_csv(exec_path)

quality_path = OUTPUT_DIR / "v2_data_quality_report.csv"
quality = pd.read_csv(quality_path)

summary["Site Label"] = summary.apply(site_label_from_row, axis=1)

issue_counts = (
    quality.groupby(["site_id", "site_name"])
    .agg(
        Data_Review_Issue_Count=("issue", "count"),
        Fields_To_Review=("field", lambda x: "; ".join(sorted(set(map(str, x))))),
        Recommended_Next_Steps=(
            "recommended_next_step",
            lambda x: "; ".join(list(dict.fromkeys(map(str, x)))[:3]),
        ),
    )
    .reset_index()
)

severity_counts = pd.crosstab(quality["site_id"], quality["severity"]).reset_index()

data_confidence = summary.merge(
    issue_counts,
    on=["site_id", "site_name"],
    how="left",
).merge(
    severity_counts,
    on="site_id",
    how="left",
)

for col in ["Data_Review_Issue_Count"]:
    data_confidence[col] = data_confidence[col].fillna(0).astype(int)

for col in data_confidence.columns:
    if col.isupper():
        data_confidence[col] = data_confidence[col].fillna(0).astype(int)

data_confidence["Fields_To_Review"] = data_confidence["Fields_To_Review"].fillna("No flagged fields")
data_confidence["Recommended_Next_Steps"] = data_confidence["Recommended_Next_Steps"].fillna(
    "No immediate data-quality issue flagged by the current report."
)

data_confidence = data_confidence.rename(
    columns={
        "model_rank": "Model Rank",
        "site_id": "Site ID",
        "site_name": "Site Name",
        "readiness_score": "Readiness Score",
        "data_confidence_level": "Data Confidence Level",
        "recommendation_tier": "Recommendation Tier",
        "electrical_risk_level": "Electrical Risk Level",
        "planning_recommendation": "Planning Recommendation",
        "data_needed_next": "Data Needed Next",
        "Data_Review_Issue_Count": "Data Review Issue Count",
        "Fields_To_Review": "Fields To Review",
        "Recommended_Next_Steps": "Recommended Next Steps",
    }
)

data_confidence["Tooltip Text"] = data_confidence.apply(
    lambda row: (
        f"{row['Site Label']}\n\n"
        f"Data Confidence Level: {row['Data Confidence Level']}\n"
        f"Data Review Issue Count: {row['Data Review Issue Count']}\n"
        f"Readiness Score: {row['Readiness Score']}\n"
        f"Recommendation Tier: {row['Recommendation Tier']}\n\n"
        f"Fields to Review: {row['Fields To Review']}\n\n"
        f"Recommended Next Steps: {row['Recommended Next Steps']}\n\n"
        f"{DISCLAIMER}"
    ),
    axis=1,
)

keep_cols = [
    "Model Rank",
    "Site ID",
    "Site Name",
    "Site Label",
    "Readiness Score",
    "Data Confidence Level",
    "Data Review Issue Count",
    "Recommendation Tier",
    "Electrical Risk Level",
    "Planning Recommendation",
    "Data Needed Next",
    "Fields To Review",
    "Recommended Next Steps",
    "Tooltip Text",
]

extra_severity_cols = [col for col in data_confidence.columns if col.isupper()]
data_confidence = data_confidence[keep_cols + extra_severity_cols]

write_csv(data_confidence, "tableau_data_confidence.csv")


# Raw data-quality issues for optional detail table in Tableau
quality_detail = quality.rename(
    columns={
        "severity": "Severity",
        "site_id": "Site ID",
        "site_name": "Site Name",
        "field": "Field",
        "issue": "Issue",
        "current_value": "Current Value",
        "recommended_next_step": "Recommended Next Step",
    }
)

quality_detail["Site Label"] = quality_detail.apply(
    lambda row: f"{row['Site ID']} — {row['Site Name']}",
    axis=1,
)

quality_detail["Tooltip Text"] = quality_detail.apply(
    lambda row: (
        f"{row['Site Label']}\n\n"
        f"Severity: {row['Severity']}\n"
        f"Field: {row['Field']}\n"
        f"Issue: {row['Issue']}\n"
        f"Current Value: {row['Current Value']}\n\n"
        f"Recommended Next Step: {row['Recommended Next Step']}\n\n"
        f"{DISCLAIMER}"
    ),
    axis=1,
)

quality_detail = quality_detail[
    [
        "Severity",
        "Site ID",
        "Site Name",
        "Site Label",
        "Field",
        "Issue",
        "Current Value",
        "Recommended Next Step",
        "Tooltip Text",
    ]
]

write_csv(quality_detail, "tableau_data_quality_issues.csv")


# ---------------------------------------------------------------------
# 5. Port-sizing scenario heat map
# Source: v2_port_sizing_scenario_results.csv
# Purpose: Site x scenario, colored by future capacity gap or required ports
# ---------------------------------------------------------------------

scenario_path = OUTPUT_DIR / "v2_port_sizing_scenario_results.csv"
scenarios = pd.read_csv(scenario_path)

scenarios["Site Label"] = scenarios.apply(site_label_from_row, axis=1)

scenario_order = (
    scenarios[["scenario_name", "scenario_label"]]
    .drop_duplicates()
    .reset_index(drop=True)
)
scenario_order["Scenario Sort"] = scenario_order.index + 1

scenarios = scenarios.merge(
    scenario_order,
    on=["scenario_name", "scenario_label"],
    how="left",
)

scenarios["Future Gap Category"] = np.select(
    [
        scenarios["future_capacity_gap"] <= 0,
        scenarios["future_capacity_gap"] == 1,
        scenarios["future_capacity_gap"] >= 2,
    ],
    [
        "No future capacity gap",
        "One-port future gap",
        "Major future capacity gap",
    ],
    default="Review needed",
)

scenario_heatmap = scenarios.rename(
    columns={
        "scenario_name": "Scenario Name",
        "scenario_label": "Scenario Label",
        "scenario_description": "Scenario Description",
        "model_rank": "Model Rank",
        "site_id": "Site ID",
        "site_name": "Site Name",
        "readiness_score": "Readiness Score",
        "base_expected_sessions_day": "Base Expected Sessions Day",
        "avg_charge_hours": "Average Charge Hours",
        "charging_window_hours": "Charging Window Hours",
        "peak_factor": "Peak Factor",
        "current_multiplier": "Current Multiplier",
        "2035_high_multiplier": "2035 High Multiplier",
        "2050_high_multiplier": "2050 High Multiplier",
        "ports_now": "Install Now Ports",
        "future_ready_capacity": "Future Ready Capacity",
        "scenario_min_ports_current": "Scenario Minimum Ports Current",
        "scenario_min_ports_2035_high": "Scenario Minimum Ports 2035 High",
        "scenario_min_ports_2050_high": "Scenario Minimum Ports 2050 High",
        "current_capacity_gap": "Current Capacity Gap",
        "future_capacity_gap": "Future Capacity Gap",
        "current_alignment": "Current Alignment",
        "future_capacity_alignment": "Future Capacity Alignment",
        "current_status_at_ports_now": "Current Status at Install Now Ports",
        "current_wait_at_ports_now": "Current Wait at Install Now Ports",
        "current_utilization_at_ports_now": "Current Utilization at Install Now Ports",
        "future_status_at_future_ready": "Future Status at Future Ready Capacity",
        "future_wait_at_future_ready": "Future Wait at Future Ready Capacity",
        "future_utilization_at_future_ready": "Future Utilization at Future Ready Capacity",
        "future_queue_risk_at_future_ready": "Future Queue Risk at Future Ready Capacity",
    }
)

scenario_heatmap["Tooltip Text"] = scenario_heatmap.apply(
    lambda row: (
        f"{row['Site Label']}\n\n"
        f"Scenario: {row['Scenario Label']}\n"
        f"Scenario Description: {row['Scenario Description']}\n\n"
        f"Install Now Ports: {row['Install Now Ports']}\n"
        f"Future Ready Capacity: {row['Future Ready Capacity']}\n"
        f"Scenario Minimum Ports Current: {row['Scenario Minimum Ports Current']}\n"
        f"Scenario Minimum Ports 2035 High: {row['Scenario Minimum Ports 2035 High']}\n"
        f"Scenario Minimum Ports 2050 High: {row['Scenario Minimum Ports 2050 High']}\n\n"
        f"Current Capacity Gap: {row['Current Capacity Gap']}\n"
        f"Future Capacity Gap: {row['Future Capacity Gap']}\n"
        f"Future Gap Category: {row['Future Gap Category']}\n\n"
        f"Future Queue Risk: {row['Future Queue Risk at Future Ready Capacity']}\n\n"
        f"{DISCLAIMER}"
    ),
    axis=1,
)

scenario_heatmap = scenario_heatmap[
    [
        "Scenario Name",
        "Scenario Label",
        "Scenario Sort",
        "Scenario Description",
        "Model Rank",
        "Site ID",
        "Site Name",
        "Site Label",
        "Readiness Score",
        "Install Now Ports",
        "Future Ready Capacity",
        "Scenario Minimum Ports Current",
        "Scenario Minimum Ports 2035 High",
        "Scenario Minimum Ports 2050 High",
        "Current Capacity Gap",
        "Future Capacity Gap",
        "Future Gap Category",
        "Current Alignment",
        "Future Capacity Alignment",
        "Current Status at Install Now Ports",
        "Current Wait at Install Now Ports",
        "Current Utilization at Install Now Ports",
        "Future Status at Future Ready Capacity",
        "Future Wait at Future Ready Capacity",
        "Future Utilization at Future Ready Capacity",
        "Future Queue Risk at Future Ready Capacity",
        "Tooltip Text",
    ]
]

write_csv(scenario_heatmap, "tableau_port_sizing_scenario_heatmap.csv")


# ---------------------------------------------------------------------
# 6. Port utilization simulation
# Source: v2_port_utilization_simulation.csv
# Purpose: Rebuild utilization simulation visual in Tableau
# ---------------------------------------------------------------------

simulation_path = OUTPUT_DIR / "v2_port_utilization_simulation.csv"
simulation = pd.read_csv(simulation_path)

simulation["Site Label"] = simulation.apply(site_label_from_row, axis=1)

simulation["Is Install Now Ports"] = simulation["is_ports_now"].astype(str).str.lower().eq("true")
simulation["Is Future Ready Capacity"] = (
    simulation["is_future_ready_capacity"].astype(str).str.lower().eq("true")
)

simulation["Recommended Port Marker"] = np.select(
    [
        simulation["Is Install Now Ports"] & simulation["Is Future Ready Capacity"],
        simulation["Is Install Now Ports"],
        simulation["Is Future Ready Capacity"],
    ],
    [
        "Install now and future-ready capacity",
        "Install now ports",
        "Future-ready capacity",
    ],
    default="Simulation test point",
)

demand_case_order = (
    simulation[["demand_case"]]
    .drop_duplicates()
    .reset_index(drop=True)
)
demand_case_order["Demand Case Sort"] = demand_case_order.index + 1

simulation = simulation.merge(demand_case_order, on="demand_case", how="left")

simulation_export = simulation.rename(
    columns={
        "site_id": "Site ID",
        "site_name": "Site Name",
        "model_rank": "Model Rank",
        "readiness_score": "Readiness Score",
        "demand_case": "Demand Case",
        "session_multiplier": "Session Multiplier",
        "sessions_day": "Sessions per Day",
        "port_count": "Port Count",
        "avg_charge_hours": "Average Charge Hours",
        "charging_window_hours": "Charging Window Hours",
        "peak_factor": "Peak Factor",
        "utilization_pct": "Utilization Percent",
        "peak_demand_ratio": "Peak Demand Ratio",
        "estimated_wait_min": "Estimated Wait Minutes",
        "queue_risk_level": "Queue Risk Level",
        "capacity_status": "Capacity Status",
    }
)

simulation_export["Tooltip Text"] = simulation_export.apply(
    lambda row: (
        f"{row['Site Label']}\n\n"
        f"Demand Case: {row['Demand Case']}\n"
        f"Port Count: {row['Port Count']}\n"
        f"Recommended Marker: {row['Recommended Port Marker']}\n\n"
        f"Sessions per Day: {row['Sessions per Day']}\n"
        f"Utilization: {row['Utilization Percent']}%\n"
        f"Estimated Wait: {row['Estimated Wait Minutes']} minutes\n"
        f"Queue Risk: {row['Queue Risk Level']}\n"
        f"Capacity Status: {row['Capacity Status']}\n\n"
        f"{DISCLAIMER}"
    ),
    axis=1,
)

simulation_export = simulation_export[
    [
        "Site ID",
        "Site Name",
        "Site Label",
        "Model Rank",
        "Readiness Score",
        "Demand Case",
        "Demand Case Sort",
        "Session Multiplier",
        "Sessions per Day",
        "Port Count",
        "Average Charge Hours",
        "Charging Window Hours",
        "Peak Factor",
        "Utilization Percent",
        "Peak Demand Ratio",
        "Estimated Wait Minutes",
        "Queue Risk Level",
        "Capacity Status",
        "Is Install Now Ports",
        "Is Future Ready Capacity",
        "Recommended Port Marker",
        "Tooltip Text",
    ]
]

write_csv(simulation_export, "tableau_port_utilization_simulation.csv")


print("\nDone. Tableau export CSVs are generated files.")
print("Do not commit data/outputs/tableau/ unless you decide to version generated Tableau inputs.")


# ---------------------------------------------------------------------
# 7. Action recommendation decision matrix
# Source: v2_executive_site_summary.csv
# Purpose: Show each site's next planning action, risk, confidence, and data needs
# ---------------------------------------------------------------------

summary = pd.read_csv(OUTPUT_DIR / "v2_executive_site_summary.csv")

summary["Site Label"] = summary.apply(site_label_from_row, axis=1)

def action_priority(row):
    tier = safe_text(row.get("recommendation_tier", "")).lower()
    action = safe_text(row.get("action_label", "")).lower()
    risk = safe_text(row.get("electrical_risk_level", "")).lower()

    if "tier 1" in tier:
        return 1
    if "tier 2" in tier and "high" not in risk:
        return 2
    if "tier 2" in tier or "promising" in action:
        return 3
    if "tier 3" in tier or "monitor" in action:
        return 4
    return 5


def action_group(row):
    tier = safe_text(row.get("recommendation_tier", "")).lower()
    action = safe_text(row.get("action_label", "")).lower()
    risk = safe_text(row.get("electrical_risk_level", "")).lower()

    if "tier 1" in tier:
        return "Advance to site screening"
    if "high" in risk:
        return "Review before advancement"
    if "tier 2" in tier:
        return "Refine assumptions"
    if "tier 3" in tier or "monitor" in action:
        return "Monitor or small pilot"
    return "Do not advance without clarification"


summary["Action Priority"] = summary.apply(action_priority, axis=1)
summary["Action Group"] = summary.apply(action_group, axis=1)

decision_matrix = summary.rename(
    columns={
        "model_rank": "Model Rank",
        "site_id": "Site ID",
        "site_name": "Site Name",
        "readiness_score": "Readiness Score",
        "data_confidence_level": "Data Confidence Level",
        "recommendation_tier": "Recommendation Tier",
        "action_label": "Action Label",
        "electrical_risk_level": "Electrical Risk Level",
        "ports_now": "Install Now Ports",
        "ports_2035_base": "Ports 2035 Base",
        "ports_2035_high": "Ports 2035 High",
        "ports_2050_base": "Ports 2050 Base",
        "ports_2050_high": "Ports 2050 High",
        "future_ready_capacity": "Future Ready Capacity",
        "expansion_strategy": "Expansion Strategy",
        "scenario_future_capacity_gap": "Scenario Future Capacity Gap",
        "scenario_sensitivity_level": "Scenario Sensitivity Level",
        "scenario_stress_note": "Scenario Stress Note",
        "major_review_flags": "Major Review Flags",
        "planning_recommendation": "Planning Recommendation",
        "data_needed_next": "Data Needed Next",
    }
)

decision_matrix["Tooltip Text"] = decision_matrix.apply(
    lambda row: (
        f"{row['Site Label']}\n\n"
        f"Model Rank: {row['Model Rank']}\n"
        f"Readiness Score: {row['Readiness Score']}\n"
        f"Action Group: {row['Action Group']}\n"
        f"Recommendation Tier: {row['Recommendation Tier']}\n\n"
        f"Install Now Ports: {row['Install Now Ports']}\n"
        f"Future Ready Capacity: {row['Future Ready Capacity']}\n"
        f"Expansion Strategy: {row['Expansion Strategy']}\n\n"
        f"Electrical Risk: {row['Electrical Risk Level']}\n"
        f"Data Confidence: {row['Data Confidence Level']}\n"
        f"Scenario Sensitivity: {row['Scenario Sensitivity Level']}\n\n"
        f"Major Review Flags: {row['Major Review Flags']}\n\n"
        f"Planning Recommendation: {row['Planning Recommendation']}\n\n"
        f"Data Needed Next: {row['Data Needed Next']}\n\n"
        f"{DISCLAIMER}"
    ),
    axis=1,
)

decision_matrix = decision_matrix[
    [
        "Model Rank",
        "Action Priority",
        "Action Group",
        "Site ID",
        "Site Name",
        "Site Label",
        "Readiness Score",
        "Data Confidence Level",
        "Recommendation Tier",
        "Action Label",
        "Electrical Risk Level",
        "Install Now Ports",
        "Ports 2035 Base",
        "Ports 2035 High",
        "Ports 2050 Base",
        "Ports 2050 High",
        "Future Ready Capacity",
        "Expansion Strategy",
        "Scenario Future Capacity Gap",
        "Scenario Sensitivity Level",
        "Scenario Stress Note",
        "Major Review Flags",
        "Planning Recommendation",
        "Data Needed Next",
        "Tooltip Text",
    ]
]

write_csv(decision_matrix, "tableau_action_recommendation_matrix.csv")


# ---------------------------------------------------------------------
# 8. Action decision quadrant
# Source: v2_executive_site_summary.csv
# Purpose: Build a quadrant matrix comparing readiness and implementation complexity
# ---------------------------------------------------------------------

import csv

summary = pd.read_csv(OUTPUT_DIR / "v2_executive_site_summary.csv")

def clean_for_tableau(value):
    if pd.isna(value):
        return ""
    return str(value).replace("\n", " ").replace("\r", " ").replace(",", ";").strip()


def quadrant_site_label(row):
    return f"{row['site_id']} — {row['site_name']}"


def quadrant_risk_points(value):
    value = clean_for_tableau(value).lower()
    if "high" in value:
        return 3
    if "medium" in value:
        return 2
    if "low" in value:
        return 1
    return 2


def quadrant_confidence_points(value):
    value = clean_for_tableau(value).lower()
    if "low" in value:
        return 2
    if "medium" in value:
        return 1
    if "high" in value:
        return 0
    return 1


def quadrant_review_flag_count(value):
    text = clean_for_tableau(value)
    if text == "" or text.lower() in ["none", "nan"]:
        return 0
    return len([part for part in text.split(";") if part.strip()])


summary["Site Label"] = summary.apply(quadrant_site_label, axis=1)
summary["Review Flag Count"] = summary["major_review_flags"].apply(quadrant_review_flag_count)
summary["Electrical Risk Points"] = summary["electrical_risk_level"].apply(quadrant_risk_points)
summary["Data Confidence Points"] = summary["data_confidence_level"].apply(quadrant_confidence_points)
summary["Scenario Gap Points"] = pd.to_numeric(
    summary["scenario_future_capacity_gap"], errors="coerce"
).fillna(0)

summary["Implementation Complexity Score"] = (
    summary["Review Flag Count"]
    + summary["Electrical Risk Points"]
    + summary["Data Confidence Points"]
    + summary["Scenario Gap Points"]
)

readiness_threshold = 50.0
complexity_threshold = 5.0

def decision_quadrant_adjusted(row):
    if row["readiness_score"] >= readiness_threshold and row["Implementation Complexity Score"] <= complexity_threshold:
        return "Advance"
    if row["readiness_score"] >= readiness_threshold and row["Implementation Complexity Score"] > complexity_threshold:
        return "High potential review first"
    if row["readiness_score"] < readiness_threshold and row["Implementation Complexity Score"] <= complexity_threshold:
        return "Monitor small pilot"
    return "Deprioritize clarify use case"


summary["Decision Quadrant Adjusted"] = summary.apply(decision_quadrant_adjusted, axis=1)

quadrant = pd.DataFrame({
    "Model Rank": summary["model_rank"].astype(int),
    "Site ID": summary["site_id"].map(clean_for_tableau),
    "Site Name": summary["site_name"].map(clean_for_tableau),
    "Site Label": summary["Site Label"].map(clean_for_tableau),
    "Readiness Score": pd.to_numeric(summary["readiness_score"], errors="coerce"),
    "Implementation Complexity Score": pd.to_numeric(summary["Implementation Complexity Score"], errors="coerce"),
    "Decision Quadrant Adjusted": summary["Decision Quadrant Adjusted"].map(clean_for_tableau),
    "Future Ready Capacity": pd.to_numeric(summary["future_ready_capacity"], errors="coerce"),
    "Readiness Threshold": readiness_threshold,
    "Complexity Threshold": complexity_threshold,
    "Electrical Risk Level": summary["electrical_risk_level"].map(clean_for_tableau),
    "Data Confidence Level": summary["data_confidence_level"].map(clean_for_tableau),
    "Scenario Sensitivity Level": summary["scenario_sensitivity_level"].map(clean_for_tableau),
    "Planning Recommendation": summary["planning_recommendation"].map(clean_for_tableau),
    "Data Needed Next": summary["data_needed_next"].map(clean_for_tableau),
})

quadrant["Tooltip Text"] = quadrant.apply(
    lambda row: (
        f"{row['Site Label']} | "
        f"Decision: {row['Decision Quadrant Adjusted']} | "
        f"Readiness Score: {row['Readiness Score']} | "
        f"Implementation Complexity Score: {row['Implementation Complexity Score']} | "
        f"Future Ready Capacity: {row['Future Ready Capacity']} | "
        f"Electrical Risk: {row['Electrical Risk Level']} | "
        f"Data Confidence: {row['Data Confidence Level']} | "
        f"Planning-support only — not final engineering or permitting approval."
    ),
    axis=1,
)

write_path = TABLEAU_DIR / "tableau_action_decision_quadrant_clean.csv"
quadrant.to_csv(write_path, index=False, quoting=csv.QUOTE_ALL)
print(f"Wrote {write_path} ({len(quadrant)} rows)")
