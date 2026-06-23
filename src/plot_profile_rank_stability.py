"""Create a profile rank stability chart.

This chart is easier to read than a spider plot or score heatmap when the main
question is rank stability. It shows the rank of each candidate site across the
five scoring profiles.

How to read it:
- x-axis = scoring profile
- y-axis = rank, with #1 at the top
- a flat line at #1 means the site stays the top candidate across profiles

Run from the repository root after profile analysis:

    python src/plot_profile_rank_stability.py

Default output:

    data/outputs/charts/profile_rank_stability_chart.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_PROFILE_RESULTS = "data/outputs/profile_results.csv"
DEFAULT_OUTPUT = "data/outputs/charts/profile_rank_stability_chart.png"

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
    required = {"profile_name", "site_id", "site_name", "profile_rank"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Profile results file is missing required columns: {sorted(missing)}")

    data["profile_rank"] = pd.to_numeric(data["profile_rank"], errors="coerce")
    if data["profile_rank"].isna().any():
        raise ValueError("Profile results contain blank or non-numeric profile_rank values.")

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


def build_rank_matrix(data: pd.DataFrame, profiles: list[str], sites: list[str]) -> pd.DataFrame:
    matrix = data.pivot_table(
        index="site_id",
        columns="profile_name",
        values="profile_rank",
        aggfunc="first",
    )
    return matrix.loc[sites, profiles]


def plot_rank_stability(data: pd.DataFrame, output_path: Path) -> None:
    ensure_parent_dir(output_path)

    profiles = profile_order(data)
    sites = site_order(data)
    rank_matrix = build_rank_matrix(data, profiles, sites)

    x_values = list(range(len(profiles)))
    labels = [PROFILE_AXIS_LABELS.get(profile, profile.replace("_", " ").title()) for profile in profiles]
    max_rank = int(rank_matrix.max().max())

    fig, ax = plt.subplots(figsize=(10.5, 6.2))

    for site_id in sites:
        y_values = rank_matrix.loc[site_id].astype(float).tolist()
        line_width = 3.0 if site_id == "FFX002" else 1.6
        alpha = 0.95 if site_id == "FFX002" else 0.72
        marker_size = 8 if site_id == "FFX002" else 5
        ax.plot(
            x_values,
            y_values,
            marker="o",
            linewidth=line_width,
            markersize=marker_size,
            alpha=alpha,
            label=site_id,
        )

        ax.text(
            x_values[-1] + 0.07,
            y_values[-1],
            site_id,
            va="center",
            fontsize=9 if site_id == "FFX002" else 8,
            fontweight="bold" if site_id == "FFX002" else "normal",
        )

    ax.set_xticks(x_values)
    ax.set_xticklabels(labels)
    ax.set_yticks(range(1, max_rank + 1))
    ax.set_ylim(max_rank + 0.45, 0.55)
    ax.set_ylabel("Rank within profile (#1 is best)")
    ax.set_xlabel("Scoring profile")
    ax.set_title("Profile Rank Stability — Candidate Rank Across Scoring Priorities")
    ax.grid(axis="y", alpha=0.25)
    ax.set_xlim(-0.2, len(profiles) - 0.2)

    footer = "How to read: a line staying at #1 means the site remains the top candidate across scoring-priority views."
    fig.text(0.5, 0.015, footer, ha="center", fontsize=8)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a profile rank stability chart.")
    parser.add_argument("--profile-results", default=DEFAULT_PROFILE_RESULTS, help="Profile results CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PNG path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile_results_path = Path(args.profile_results)
    output_path = Path(args.output)

    data = load_profile_results(profile_results_path)
    plot_rank_stability(data, output_path)

    print("PROFILE RANK STABILITY CHART")
    print("----------------------------")
    print(f"Profile results file: {profile_results_path}")
    print(f"Saved chart: {output_path}")


if __name__ == "__main__":
    main()
