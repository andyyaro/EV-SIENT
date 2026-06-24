"""Create scalable visuals for larger candidate-site tests.

The official six-site charts are readable for V1, but larger synthetic tests need
visuals that avoid overcrowded labels. This script reads model outputs and
optionally profile-analysis outputs to create scalable planning visuals.

Core visuals:
1. Top-N readiness chart
2. Full compact readiness chart
3. Readiness score distribution
4. Recommendation tier count chart

Optional visuals when extra inputs are provided:
5. Scalable readiness map/scatter with only top-N labels
6. Top-N scoring-profile heatmap
7. Top-N profile rank stability chart
8. Compact data-confidence chart

Example:

    python src/plot_scalable_readiness_charts.py \
      --results data/demo/outputs/demo_site_results_50.csv \
      --input-sites data/demo/demo_sites_50.csv \
      --profile-results data/demo/outputs/demo_profile_results_50.csv \
      --output-dir data/demo/outputs/charts/scalable \
      --top-n 15
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DEFAULT_RESULTS = "data/outputs/site_results.csv"
DEFAULT_OUTPUT_DIR = "data/outputs/charts/scalable"
DEFAULT_TOP_N = 15

REQUIRED_COLUMNS = {
    "site_id",
    "site_name",
    "model_rank",
    "readiness_score",
    "recommendation_tier",
}

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

TIER_ORDER = [
    "Tier 1 — advance to site screening",
    "High-review candidate",
    "Tier 2 — promising candidate, refine data",
    "Tier 3 — lower priority / monitor",
    "Low public-priority / special-use",
]

TIER_SHORT_LABELS = {
    "Tier 1 — advance to site screening": "Tier 1",
    "Tier 2 — promising candidate, refine data": "Tier 2",
    "High-review candidate": "High-review",
    "Tier 3 — lower priority / monitor": "Tier 3",
    "Low public-priority / special-use": "Special-use",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def short_tier(value: str) -> str:
    return TIER_SHORT_LABELS.get(str(value), str(value))


def load_results(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")

    results = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(results.columns)
    if missing:
        raise ValueError(f"Results file is missing required columns: {sorted(missing)}")

    results = results.copy()
    results["model_rank"] = pd.to_numeric(results["model_rank"], errors="coerce")
    results["readiness_score"] = pd.to_numeric(results["readiness_score"], errors="coerce")
    if "data_confidence_score" in results.columns:
        results["data_confidence_score"] = pd.to_numeric(results["data_confidence_score"], errors="coerce")
    results = results.dropna(subset=["model_rank", "readiness_score"])
    results["model_rank"] = results["model_rank"].astype(int)
    results["tier_short"] = results["recommendation_tier"].apply(short_tier)
    return results.sort_values("model_rank", ascending=True).reset_index(drop=True)


def load_input_sites(path: Path | None) -> pd.DataFrame | None:
    if path is None:
        return None
    if not path.exists():
        raise FileNotFoundError(f"Input sites file not found: {path}")
    sites = pd.read_csv(path)
    required = {"site_id", "lat", "lon"}
    missing = required - set(sites.columns)
    if missing:
        raise ValueError(f"Input sites file is missing required map columns: {sorted(missing)}")
    sites["lat"] = pd.to_numeric(sites["lat"], errors="coerce")
    sites["lon"] = pd.to_numeric(sites["lon"], errors="coerce")
    return sites.dropna(subset=["lat", "lon"])


def load_profile_results(path: Path | None) -> pd.DataFrame | None:
    if path is None:
        return None
    if not path.exists():
        raise FileNotFoundError(f"Profile results file not found: {path}")
    data = pd.read_csv(path)
    required = {"profile_name", "site_id", "profile_rank", "profile_readiness_score"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Profile results file is missing required columns: {sorted(missing)}")
    data["profile_rank"] = pd.to_numeric(data["profile_rank"], errors="coerce")
    data["profile_readiness_score"] = pd.to_numeric(data["profile_readiness_score"], errors="coerce")
    return data.dropna(subset=["profile_rank", "profile_readiness_score"])


def site_rank_label(row: pd.Series) -> str:
    return f"#{int(row['model_rank'])} {row['site_id']}"


def profile_order(data: pd.DataFrame) -> list[str]:
    available = data["profile_name"].astype(str).drop_duplicates().tolist()
    ordered = [profile for profile in PROFILE_ORDER if profile in available]
    ordered.extend(profile for profile in available if profile not in ordered)
    return ordered


def top_site_ids(results: pd.DataFrame, top_n: int) -> list[str]:
    return results.head(top_n)["site_id"].astype(str).tolist()


def add_bar_labels(ax, rows: pd.DataFrame, show_tier: bool = True) -> None:
    for index, row in rows.iterrows():
        score = float(row["readiness_score"])
        label = f"{score:.1f}"
        if show_tier:
            label += f" | {row['tier_short']}"
        ax.text(score + 0.6, index, label, va="center", fontsize=8, clip_on=False)


def score_axis_bounds(scores: pd.Series, floor_to: int = 5, padding: int = 5) -> tuple[int, int]:
    min_score = float(scores.min())
    max_score = float(scores.max())
    low = max(0, int(math.floor((min_score - padding) / floor_to) * floor_to))
    high = min(100, int(math.ceil((max_score + padding) / floor_to) * floor_to))
    if high <= low:
        high = min(100, low + 10)
    return low, high


def tier_funnel_sentence(results: pd.DataFrame) -> str:
    counts = results["tier_short"].value_counts()
    total = len(results)
    if total == 0:
        return "No sites were available for tier interpretation."
    top_tier = counts.idxmax()
    top_count = int(counts.max())
    tier1_count = int(counts.get("Tier 1", 0))
    high_review_count = int(counts.get("High-review", 0))
    return (
        f"Most sites fall into {top_tier} ({top_count} of {total}), while {tier1_count} sites are Tier 1 "
        f"and {high_review_count} sites need high review. This suggests the demo run creates a broad review pool "
        "rather than over-selecting top candidates."
    )


def plot_top_n(results: pd.DataFrame, output_dir: Path, top_n: int) -> Path:
    top = results.head(top_n).copy().reset_index(drop=True)
    height = max(5.5, 0.36 * len(top) + 1.8)
    fig, ax = plt.subplots(figsize=(12.8, height))

    labels = [site_rank_label(row) for _, row in top.iterrows()]
    ax.barh(labels, top["readiness_score"])
    ax.invert_yaxis()
    add_bar_labels(ax, top)

    max_score = float(top["readiness_score"].max()) if not top.empty else 100
    ax.set_xlim(0, max(75, max_score + 14))
    ax.set_xlabel("Readiness score")
    ax.set_title(f"Top {len(top)} Candidate Sites by Readiness Score", fontsize=14, pad=16)
    ax.grid(axis="x", alpha=0.22)
    ax.set_axisbelow(True)

    fig.text(0.5, 0.035, "Top-N view is the main scalable ranking visual. Full site names remain in the CSV/results table.", ha="center", fontsize=8)
    fig.tight_layout(rect=[0.06, 0.07, 0.98, 0.95])

    output_path = output_dir / f"readiness_top_{len(top)}.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_full_compact(results: pd.DataFrame, output_dir: Path) -> Path:
    rows = results.copy().reset_index(drop=True)
    height = max(7.0, 0.22 * len(rows) + 2.0)
    fig, ax = plt.subplots(figsize=(12.8, height))

    labels = [site_rank_label(row) for _, row in rows.iterrows()]
    ax.barh(labels, rows["readiness_score"])
    ax.invert_yaxis()

    for index, row in rows.iterrows():
        score = float(row["readiness_score"])
        ax.text(score + 0.5, index, f"{score:.1f}", va="center", fontsize=6.6, clip_on=False)

    max_score = float(rows["readiness_score"].max()) if not rows.empty else 100
    ax.set_xlim(0, max(75, max_score + 10))
    ax.tick_params(axis="y", labelsize=6.5)
    ax.set_xlabel("Readiness score")
    ax.set_title(f"Full Compact Readiness Ranking ({len(rows)} Sites)", fontsize=14, pad=16)
    ax.grid(axis="x", alpha=0.20)
    ax.set_axisbelow(True)

    fig.text(0.5, 0.025, "Appendix view only: use this to audit the complete ranking, not as the main presentation chart.", ha="center", fontsize=8)
    fig.tight_layout(rect=[0.06, 0.05, 0.98, 0.95])

    output_path = output_dir / "readiness_full_compact.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_distribution(results: pd.DataFrame, output_dir: Path) -> Path:
    scores = results["readiness_score"].dropna()
    low, high = score_axis_bounds(scores, floor_to=5, padding=5)
    bin_step = 5 if high - low <= 50 else 10
    bins = list(range(low, high + bin_step, bin_step))

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.hist(scores, bins=bins, edgecolor="black", alpha=0.82)
    ax.set_xlim(low, high)
    ax.set_xlabel("Readiness score range")
    ax.set_ylabel("Number of sites")
    ax.set_title("Readiness Score Distribution", fontsize=14, pad=16)
    ax.grid(axis="y", alpha=0.22)
    ax.set_axisbelow(True)

    mean_score = scores.mean()
    median_score = scores.median()
    y_top = ax.get_ylim()[1]
    ax.axvline(mean_score, linestyle="--", linewidth=1.1, alpha=0.75)
    ax.axvline(median_score, linestyle=":", linewidth=1.4, alpha=0.75)
    ax.text(mean_score, y_top * 0.95, f"mean {mean_score:.1f}", ha="center", va="top", fontsize=8)
    ax.text(median_score, y_top * 0.82, f"median {median_score:.1f}", ha="center", va="top", fontsize=8)

    fig.text(0.5, 0.035, f"Zoomed to the observed score range ({low}–{high}) so the distribution is easier to read.", ha="center", fontsize=8)
    fig.tight_layout(rect=[0.06, 0.07, 0.98, 0.95])

    output_path = output_dir / "readiness_score_distribution.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_tier_counts(results: pd.DataFrame, output_dir: Path) -> Path:
    tier_counts = results["recommendation_tier"].value_counts()
    ordered_tiers = [tier for tier in TIER_ORDER if tier in tier_counts.index]
    ordered_tiers.extend(tier for tier in tier_counts.index if tier not in ordered_tiers)

    labels = [short_tier(tier) for tier in ordered_tiers]
    counts = [int(tier_counts[tier]) for tier in ordered_tiers]

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    bars = ax.barh(labels, counts)
    ax.invert_yaxis()

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 0.25, bar.get_y() + bar.get_height() / 2, str(count), va="center", fontsize=9, clip_on=False)

    ax.set_xlabel("Number of sites")
    ax.set_title("Recommendation Tier Counts", fontsize=14, pad=16)
    ax.grid(axis="x", alpha=0.22)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(counts) + max(2, max(counts) * 0.12))

    fig.text(0.5, 0.035, tier_funnel_sentence(results), ha="center", fontsize=8)
    fig.tight_layout(rect=[0.06, 0.08, 0.98, 0.95])

    output_path = output_dir / "recommendation_tier_counts.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_data_confidence(results: pd.DataFrame, output_dir: Path) -> Path | None:
    if "data_confidence_score" not in results.columns or "data_confidence_level" not in results.columns:
        return None

    rows = results.copy().reset_index(drop=True)
    height = max(7.0, 0.22 * len(rows) + 2.0)
    fig, ax = plt.subplots(figsize=(12.8, height))
    labels = [site_rank_label(row) for _, row in rows.iterrows()]
    ax.axvspan(0, 50, alpha=0.06)
    ax.axvspan(50, 75, alpha=0.10)
    ax.axvspan(75, 100, alpha=0.06)
    bars = ax.barh(labels, rows["data_confidence_score"])
    ax.invert_yaxis()

    for index, row in rows.iterrows():
        score = float(row["data_confidence_score"])
        level = str(row["data_confidence_level"])
        ax.text(score + 0.6, index, f"{score:.1f} | {level}", va="center", fontsize=6.8, clip_on=False)

    ax.axvline(50, linestyle="--", linewidth=1, alpha=0.45)
    ax.axvline(75, linestyle="--", linewidth=1, alpha=0.45)
    ax.set_xlim(0, 100)
    ax.tick_params(axis="y", labelsize=6.5)
    ax.set_xlabel("Data confidence score")
    ax.set_title(f"Compact Data Confidence by Rank ({len(rows)} Sites)", fontsize=14, pad=16)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)

    fig.text(0.5, 0.025, "Confidence is separate from readiness. This compact view is for larger demo result sets.", ha="center", fontsize=8)
    fig.tight_layout(rect=[0.06, 0.05, 0.98, 0.95])

    output_path = output_dir / "data_confidence_full_compact.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_readiness_map(results: pd.DataFrame, input_sites: pd.DataFrame | None, output_dir: Path, top_n: int) -> Path | None:
    if input_sites is None:
        return None

    data = results.merge(input_sites[["site_id", "lat", "lon"]], on="site_id", how="inner")
    if data.empty:
        return None

    top_ids = set(top_site_ids(results, top_n))
    fig, ax = plt.subplots(figsize=(11.5, 7.2))
    sizes = 35 + data["readiness_score"] * 4
    scatter = ax.scatter(
        data["lon"],
        data["lat"],
        s=sizes,
        c=data["readiness_score"],
        alpha=0.72,
        edgecolors="black",
        linewidths=0.35,
    )

    top = data[data["site_id"].isin(top_ids)].copy()
    for _, row in top.iterrows():
        ax.annotate(
            f"#{int(row['model_rank'])} {row['site_id']}",
            xy=(row["lon"], row["lat"]),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=7.2,
            bbox={"boxstyle": "round,pad=0.15", "fc": "white", "alpha": 0.82, "lw": 0.25},
        )

    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Readiness score")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Scalable Demo Readiness Map — Top {len(top)} Labeled", fontsize=14, pad=16)
    ax.grid(alpha=0.22)

    fig.text(0.5, 0.025, "Planning visual only: longitude/latitude scatter with top-N labels, no basemap or parcel boundary.", ha="center", fontsize=8)
    fig.tight_layout(rect=[0.04, 0.05, 0.98, 0.95])

    output_path = output_dir / f"readiness_map_top_{len(top)}_labeled.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def profile_score_matrix(profile_results: pd.DataFrame, sites: list[str], profiles: list[str]) -> pd.DataFrame:
    matrix = profile_results.pivot_table(index="site_id", columns="profile_name", values="profile_readiness_score", aggfunc="first")
    return matrix.loc[sites, profiles]


def profile_rank_matrix(profile_results: pd.DataFrame, sites: list[str], profiles: list[str]) -> pd.DataFrame:
    matrix = profile_results.pivot_table(index="site_id", columns="profile_name", values="profile_rank", aggfunc="first")
    return matrix.loc[sites, profiles]


def plot_profile_heatmap(results: pd.DataFrame, profile_results: pd.DataFrame | None, output_dir: Path, top_n: int) -> Path | None:
    if profile_results is None:
        return None

    profiles = profile_order(profile_results)
    sites = top_site_ids(results, top_n)
    available_sites = [site_id for site_id in sites if site_id in set(profile_results["site_id"].astype(str))]
    if not available_sites:
        return None

    scores = profile_score_matrix(profile_results, available_sites, profiles)
    ranks = profile_rank_matrix(profile_results, available_sites, profiles)
    height = max(5.8, 0.42 * len(available_sites) + 1.8)
    fig, ax = plt.subplots(figsize=(11.5, height))
    image = ax.imshow(scores.values, aspect="auto")

    ax.set_xticks(range(len(profiles)))
    ax.set_xticklabels([PROFILE_AXIS_LABELS.get(profile, profile.replace("_", " ").title()) for profile in profiles])
    ax.set_yticks(range(len(available_sites)))
    ax.set_yticklabels([f"#{int(results.loc[results['site_id'] == site_id, 'model_rank'].iloc[0])} {site_id}" for site_id in available_sites])

    for row_index, site_id in enumerate(available_sites):
        for col_index, profile in enumerate(profiles):
            ax.text(
                col_index,
                row_index,
                f"{float(scores.loc[site_id, profile]):.1f}\n#{int(ranks.loc[site_id, profile])}",
                ha="center",
                va="center",
                fontsize=7,
            )

    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("Profile readiness score")
    ax.set_xlabel("Scoring profile")
    ax.set_ylabel("Top candidate sites")
    ax.set_title(f"Top {len(available_sites)} Profile Heatmap", fontsize=14, pad=16)

    fig.text(0.5, 0.025, "Each cell shows profile readiness score and rank. Limited to top-N sites for readability.", ha="center", fontsize=8)
    fig.tight_layout(rect=[0.04, 0.05, 0.98, 0.95])

    output_path = output_dir / f"profile_heatmap_top_{len(available_sites)}.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_profile_rank_stability(results: pd.DataFrame, profile_results: pd.DataFrame | None, output_dir: Path, top_n: int) -> Path | None:
    if profile_results is None:
        return None

    profiles = profile_order(profile_results)
    sites = top_site_ids(results, top_n)
    available_sites = [site_id for site_id in sites if site_id in set(profile_results["site_id"].astype(str))]
    if not available_sites:
        return None

    ranks = profile_rank_matrix(profile_results, available_sites, profiles)
    x_values = list(range(len(profiles)))
    labels = [PROFILE_AXIS_LABELS.get(profile, profile.replace("_", " ").title()) for profile in profiles]

    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    for site_id in available_sites:
        y_values = ranks.loc[site_id].astype(float).tolist()
        base_rank = int(results.loc[results["site_id"] == site_id, "model_rank"].iloc[0])
        line_width = 2.4 if base_rank <= 3 else 1.35
        alpha = 0.95 if base_rank <= 3 else 0.62
        ax.plot(x_values, y_values, marker="o", linewidth=line_width, alpha=alpha)
        ax.text(x_values[-1] + 0.06, y_values[-1], site_id, va="center", fontsize=7.2)

    max_rank = int(ranks.max().max())
    ax.set_xticks(x_values)
    ax.set_xticklabels(labels)
    ax.set_ylim(max_rank + 0.6, 0.5)
    ax.set_ylabel("Rank within profile (#1 is best)")
    ax.set_xlabel("Scoring profile")
    ax.set_title(f"Top {len(available_sites)} Rank Stability Across Profiles", fontsize=14, pad=16)
    ax.grid(axis="y", alpha=0.22)
    ax.set_xlim(-0.15, len(profiles) - 0.15)

    fig.text(0.5, 0.025, "Limited to top-N base-model sites so rank movement remains readable.", ha="center", fontsize=8)
    fig.tight_layout(rect=[0.04, 0.05, 0.98, 0.95])

    output_path = output_dir / f"profile_rank_stability_top_{len(available_sites)}.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def write_summary(results: pd.DataFrame, output_dir: Path, chart_paths: list[Path], top_n: int) -> Path:
    top = results.head(top_n)
    tier_counts = results["tier_short"].value_counts()

    lines = [
        "# Scalable Readiness Visuals Summary",
        "",
        f"Sites evaluated: {len(results)}",
        f"Top-N chart size: {len(top)}",
        "",
        "## Quick interpretation",
        "",
        tier_funnel_sentence(results),
        "",
        "## Generated charts",
        "",
    ]

    for path in chart_paths:
        lines.append(f"- [{path.name}]({path.name})")

    lines.extend(["", "## Top sites", ""])
    lines.append("| Rank | Site ID | Readiness | Tier |")
    lines.append("|---:|---|---:|---|")
    for _, row in top.iterrows():
        lines.append(f"| {int(row['model_rank'])} | {row['site_id']} | {float(row['readiness_score']):.1f} | {row['tier_short']} |")

    lines.extend(["", "## Tier counts", ""])
    lines.append("| Tier | Count |")
    lines.append("|---|---:|")
    for tier, count in tier_counts.items():
        lines.append(f"| {tier} | {int(count)} |")

    lines.extend([
        "",
        "## How to use these visuals",
        "",
        "Use the top-N readiness chart and top-N map for presentation.",
        "Use the distribution and tier-count charts to understand whether the model creates a reasonable planning funnel.",
        "Use profile heatmap/rank-stability charts to check whether priority changes affect the top candidates.",
        "Use full compact charts only for audit/review.",
        "",
    ])

    output_path = output_dir / "scalable_readiness_visuals_summary.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create scalable readiness visuals from model output CSVs.")
    parser.add_argument("--results", default=DEFAULT_RESULTS, help="Model results CSV to visualize.")
    parser.add_argument("--input-sites", default=None, help="Optional input site CSV with lat/lon for scalable map visual.")
    parser.add_argument("--profile-results", default=None, help="Optional profile results CSV for scalable profile visuals.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Folder for generated scalable visuals.")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="Number of sites to include in top-N visuals.")
    parser.add_argument("--skip-full", action="store_true", help="Skip the full compact ranking chart.")
    return parser.parse_args()


def append_optional(chart_paths: list[Path], maybe_path: Path | None) -> None:
    if maybe_path is not None:
        chart_paths.append(maybe_path)


def main() -> None:
    args = parse_args()
    results_path = Path(args.results)
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    input_sites = load_input_sites(Path(args.input_sites)) if args.input_sites else None
    profile_results = load_profile_results(Path(args.profile_results)) if args.profile_results else None
    results = load_results(results_path)
    if results.empty:
        raise SystemExit("No valid rows found in results file.")

    top_n = max(1, min(args.top_n, len(results)))

    chart_paths: list[Path] = []
    chart_paths.append(plot_top_n(results, output_dir, top_n))
    chart_paths.append(plot_distribution(results, output_dir))
    chart_paths.append(plot_tier_counts(results, output_dir))
    append_optional(chart_paths, plot_data_confidence(results, output_dir))
    append_optional(chart_paths, plot_readiness_map(results, input_sites, output_dir, top_n))
    append_optional(chart_paths, plot_profile_heatmap(results, profile_results, output_dir, top_n))
    append_optional(chart_paths, plot_profile_rank_stability(results, profile_results, output_dir, top_n))
    if not args.skip_full:
        chart_paths.append(plot_full_compact(results, output_dir))

    summary_path = write_summary(results, output_dir, chart_paths, top_n)

    print("SCALABLE READINESS VISUALS")
    print("--------------------------")
    print(f"Results file: {results_path}")
    print(f"Sites evaluated: {len(results)}")
    print(f"Output folder: {output_dir}")
    print()
    print("Generated files:")
    for path in chart_paths:
        print(f"- {path}")
    print(f"- {summary_path}")


if __name__ == "__main__":
    main()
