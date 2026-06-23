"""Create a scoring-profile spider/radar chart.

This chart shows how each candidate site's readiness score changes across the
scoring profiles. It is meant to support the profile-comparison story: FFX002
stays strongest across all five scoring-priority views.

Run from the repository root after profile analysis:

    python src/plot_profile_spider_chart.py

Default output:

    data/outputs/charts/profile_spider_chart.png
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_PROFILE_RESULTS = "data/outputs/profile_results.csv"
DEFAULT_OUTPUT = "data/outputs/charts/profile_spider_chart.png"

PROFILE_ORDER = [
    "base",
    "demand_priority",
    "equity_priority",
    "feasibility_priority",
    "safety_priority",
]

PROFILE_AXIS_LABELS = {
    "base": "Base",
    "demand_priority": "Demand",
    "equity_priority": "Equity",
    "feasibility_priority": "Feasibility",
    "safety_priority": "Safety",
}


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def load_profile_results(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Profile results file not found: {path}. Run src/run_profile_analysis.py first.")

    data = pd.read_csv(path)
    required = {"profile_name", "site_id", "site_name", "profile_rank", "profile_readiness_score"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Profile results file is missing required columns: {sorted(missing)}")

    data["profile_rank"] = pd.to_numeric(data["profile_rank"], errors="coerce")
    data["profile_readiness_score"] = pd.to_numeric(data["profile_readiness_score"], errors="coerce")
    if data["profile_rank"].isna().any() or data["profile_readiness_score"].isna().any():
        raise ValueError("Profile results contain blank or non-numeric rank/score values.")

    return data


def profile_order(data: pd.DataFrame) -> list[str]:
    available = data["profile_name"].astype(str).drop_duplicates().tolist()
    ordered = [profile for profile in PROFILE_ORDER if profile in available]
    ordered.extend(profile for profile in available if profile not in ordered)
    return ordered


def site_order(data: pd.DataFrame) -> list[str]:
    base_rows = data[data["profile_name"].astype(str) == "base"].copy()
    if not base_rows.empty:
        return base_rows.sort_values("profile_rank")["site_id"].astype(str).tolist()

    summary = (
        data.groupby("site_id", as_index=False)["profile_rank"]
        .mean()
        .sort_values("profile_rank")
    )
    return summary["site_id"].astype(str).tolist()


def build_score_matrix(data: pd.DataFrame, profiles: list[str], sites: list[str]) -> pd.DataFrame:
    matrix = data.pivot_table(
        index="site_id",
        columns="profile_name",
        values="profile_readiness_score",
        aggfunc="first",
    )
    missing_profiles = [profile for profile in profiles if profile not in matrix.columns]
    if missing_profiles:
        raise ValueError(f"Missing profile score columns after pivot: {missing_profiles}")
    return matrix.loc[sites, profiles]


def plot_spider_chart(data: pd.DataFrame, output_path: Path) -> None:
    ensure_parent_dir(output_path)

    profiles = profile_order(data)
    sites = site_order(data)
    score_matrix = build_score_matrix(data, profiles, sites)

    axis_labels = [PROFILE_AXIS_LABELS.get(profile, profile.replace("_", " ").title()) for profile in profiles]
    angles = [2 * math.pi * index / len(profiles) for index in range(len(profiles))]
    angles_closed = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(8.4, 8.4), subplot_kw={"polar": True})

    for site_id in sites:
        values = score_matrix.loc[site_id].astype(float).tolist()
        values_closed = values + [values[0]]
        line_width = 2.6 if site_id == "FFX002" else 1.2
        alpha = 0.95 if site_id == "FFX002" else 0.55
        ax.plot(angles_closed, values_closed, linewidth=line_width, alpha=alpha, label=site_id)
        if site_id == "FFX002":
            ax.fill(angles_closed, values_closed, alpha=0.08)

    ax.set_xticks(angles)
    ax.set_xticklabels(axis_labels)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=8)
    ax.set_title("Scoring Profile Spider Chart — Readiness Score by Priority View", pad=24)
    ax.legend(loc="upper right", bbox_to_anchor=(1.24, 1.12), title="Site")

    footer = "Outer edge = stronger profile readiness score. FFX002 is emphasized because it ranks #1 across all profiles."
    fig.text(0.5, 0.02, footer, ha="center", fontsize=8)
    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a scoring-profile spider/radar chart.")
    parser.add_argument("--profile-results", default=DEFAULT_PROFILE_RESULTS, help="Profile results CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PNG path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile_results_path = Path(args.profile_results)
    output_path = Path(args.output)

    data = load_profile_results(profile_results_path)
    plot_spider_chart(data, output_path)

    print("PROFILE SPIDER CHART")
    print("--------------------")
    print(f"Profile results file: {profile_results_path}")
    print(f"Saved chart: {output_path}")


if __name__ == "__main__":
    main()
