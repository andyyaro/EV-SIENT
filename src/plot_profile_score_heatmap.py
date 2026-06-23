"""Create a scoring-profile score heatmap.

This chart is easier to read than a spider/radar chart for six sites. It shows
readiness scores across the five scoring profiles with one row per site and one
column per profile.

Run from the repository root after profile analysis:

    python src/plot_profile_score_heatmap.py

Default output:

    data/outputs/charts/profile_score_heatmap.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_PROFILE_RESULTS = "data/outputs/profile_results.csv"
DEFAULT_OUTPUT = "data/outputs/charts/profile_score_heatmap.png"

PROFILE_ORDER = [
    "base",
    "demand_priority",
    "equity_priority",
    "feasibility_priority",
    "safety_priority",
]

PROFILE_AXIS_LABELS = {
    "base": "Base",
    "demand_priority": "Demand\npriority",
    "equity_priority": "Equity\npriority",
    "feasibility_priority": "Feasibility\npriority",
    "safety_priority": "Safety\npriority",
}

TIER_SHORT_LABELS = {
    "Tier 1 — advance to site screening": "Tier 1",
    "Tier 2 — promising candidate, refine data": "Tier 2",
    "High-review candidate": "High-review",
    "Tier 3 — lower priority / monitor": "Tier 3",
    "Low public-priority / special-use": "Special-use",
}


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def compact_tier(value: str) -> str:
    return TIER_SHORT_LABELS.get(str(value), str(value))


def load_profile_results(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Profile results file not found: {path}. Run src/run_profile_analysis.py first.")

    data = pd.read_csv(path)
    required = {
        "profile_name",
        "site_id",
        "site_name",
        "profile_rank",
        "profile_readiness_score",
        "base_model_rank",
        "profile_recommendation_tier",
    }
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Profile results file is missing required columns: {sorted(missing)}")

    data["profile_rank"] = pd.to_numeric(data["profile_rank"], errors="coerce")
    data["profile_readiness_score"] = pd.to_numeric(data["profile_readiness_score"], errors="coerce")
    data["base_model_rank"] = pd.to_numeric(data["base_model_rank"], errors="coerce")
    if data[["profile_rank", "profile_readiness_score", "base_model_rank"]].isna().any().any():
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
    return matrix.loc[sites, profiles]


def build_rank_matrix(data: pd.DataFrame, profiles: list[str], sites: list[str]) -> pd.DataFrame:
    matrix = data.pivot_table(
        index="site_id",
        columns="profile_name",
        values="profile_rank",
        aggfunc="first",
    )
    return matrix.loc[sites, profiles]


def build_row_labels(data: pd.DataFrame, sites: list[str]) -> list[str]:
    base_rows = (
        data.sort_values(["site_id", "profile_rank"])
        .drop_duplicates("site_id")
        .set_index("site_id")
    )
    labels = []
    for site_id in sites:
        row = base_rows.loc[site_id]
        tier = compact_tier(row.get("profile_recommendation_tier", ""))
        labels.append(f"{site_id} — {tier}")
    return labels


def plot_heatmap(data: pd.DataFrame, output_path: Path) -> None:
    ensure_parent_dir(output_path)

    profiles = profile_order(data)
    sites = site_order(data)
    score_matrix = build_score_matrix(data, profiles, sites)
    rank_matrix = build_rank_matrix(data, profiles, sites)
    row_labels = build_row_labels(data, sites)
    column_labels = [PROFILE_AXIS_LABELS.get(profile, profile.replace("_", " ").title()) for profile in profiles]

    fig, ax = plt.subplots(figsize=(10.5, 6.3))
    image = ax.imshow(score_matrix.values, aspect="auto")

    ax.set_xticks(range(len(profiles)))
    ax.set_xticklabels(column_labels)
    ax.set_yticks(range(len(sites)))
    ax.set_yticklabels(row_labels)
    ax.set_title("Scoring Profile Heatmap — Readiness Scores by Priority View")

    for row_index, site_id in enumerate(sites):
        for col_index, profile in enumerate(profiles):
            score = float(score_matrix.loc[site_id, profile])
            rank = int(rank_matrix.loc[site_id, profile])
            ax.text(
                col_index,
                row_index,
                f"{score:.1f}\n#{rank}",
                ha="center",
                va="center",
                fontsize=8,
            )

    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("Profile readiness score")

    ax.set_xlabel("Scoring profile")
    ax.set_ylabel("Candidate site")

    footer = "Each cell shows readiness score and profile rank. FFX002 stays #1 across all five scoring-priority views."
    fig.text(0.5, 0.015, footer, ha="center", fontsize=8)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a scoring-profile score heatmap.")
    parser.add_argument("--profile-results", default=DEFAULT_PROFILE_RESULTS, help="Profile results CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PNG path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile_results_path = Path(args.profile_results)
    output_path = Path(args.output)

    data = load_profile_results(profile_results_path)
    plot_heatmap(data, output_path)

    print("PROFILE SCORE HEATMAP")
    print("---------------------")
    print(f"Profile results file: {profile_results_path}")
    print(f"Saved chart: {output_path}")


if __name__ == "__main__":
    main()
