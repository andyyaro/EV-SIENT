"""Create a redesigned V2 EV charging decision board.

This visual is intentionally not a latitude/longitude scatter map. The detailed
geographic map already exists as ``v2_site_readiness_map.png``. This script
creates a stakeholder-facing decision board that groups candidate sites by the
planning action the model suggests.

Default input:
- data/outputs/v2_executive_site_summary.csv

Default output:
- data/outputs/charts/v2_site_decision_map.png
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import FancyBboxPatch, Rectangle
import pandas as pd

DEFAULT_INPUT = "data/outputs/v2_executive_site_summary.csv"
DEFAULT_OUTPUT = "data/outputs/charts/v2_site_decision_map.png"

ACTION_ORDER = [
    "Advance now",
    "Refine assumptions",
    "High-review",
    "Monitor",
    "Special-use",
]

BUCKET_DESCRIPTIONS = {
    "Advance now": "Best near-term candidates",
    "Refine assumptions": "Promising, verify details",
    "High-review": "Requires technical review",
    "Monitor": "Lower priority / watchlist",
    "Special-use": "Not general-public buildout",
}


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def safe_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> int | None:
    number = safe_float(value)
    if number is None:
        return None
    return int(round(number))


def compact_tier(value: Any) -> str:
    text = str(value or "").strip()
    lower = text.lower()
    if "tier 1" in lower:
        return "Tier 1"
    if "tier 2" in lower:
        return "Tier 2"
    if "tier 3" in lower:
        return "Tier 3"
    if "high-review" in lower:
        return "High-review"
    if "special-use" in lower or "low public-priority" in lower:
        return "Special-use"
    return text if text else "Unclassified"


def classify_action(row: pd.Series) -> str:
    tier = compact_tier(row.get("recommendation_tier", ""))
    action = str(row.get("action_label", "")).lower()
    strategy = str(row.get("expansion_strategy", "")).lower()
    site_id = str(row.get("site_id", ""))

    if tier == "Special-use" or "special" in strategy or site_id == "PWC003":
        return "Special-use"
    if tier == "High-review" or "review" in strategy or "technical review" in action:
        return "High-review"
    if tier == "Tier 3" or "monitor" in strategy or "monitor" in action:
        return "Monitor"
    if tier == "Tier 1":
        return "Advance now"
    return "Refine assumptions"


def wrap_text(text: Any, width: int) -> str:
    text = "" if pd.isna(text) else str(text)
    return "\n".join(textwrap.wrap(text, width=width))


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    data = pd.read_csv(path)
    required = {"model_rank", "site_id", "site_name", "readiness_score", "recommendation_tier"}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Decision-map input is missing required columns: {missing}")

    if "ports_now" not in data.columns and "recommended_ports_now" in data.columns:
        data["ports_now"] = data["recommended_ports_now"]
    if "ports_now" not in data.columns:
        data["ports_now"] = ""

    if "future_ready_capacity" not in data.columns and "recommended_ports_2050" in data.columns:
        data["future_ready_capacity"] = data["recommended_ports_2050"]
    if "future_ready_capacity" not in data.columns:
        data["future_ready_capacity"] = ""

    if "electrical_risk_level" not in data.columns:
        data["electrical_risk_level"] = "unknown"
    if "major_review_flags" not in data.columns:
        data["major_review_flags"] = ""
    if "expansion_strategy" not in data.columns:
        data["expansion_strategy"] = ""
    if "current_alignment" not in data.columns:
        data["current_alignment"] = ""
    if "future_alignment" not in data.columns:
        data["future_alignment"] = ""

    data["model_rank"] = pd.to_numeric(data["model_rank"], errors="coerce")
    data["readiness_score"] = pd.to_numeric(data["readiness_score"], errors="coerce")
    data["decision_bucket"] = data.apply(classify_action, axis=1)
    data["tier_short"] = data["recommendation_tier"].apply(compact_tier)
    return data.sort_values(["model_rank", "site_id"]).reset_index(drop=True)


def score_norm(data: pd.DataFrame) -> Normalize:
    scores = pd.to_numeric(data["readiness_score"], errors="coerce").dropna()
    if scores.empty:
        return Normalize(vmin=0, vmax=100)
    low = max(0.0, float(scores.min()) - 3)
    high = min(100.0, float(scores.max()) + 3)
    if low == high:
        high = low + 1
    return Normalize(vmin=low, vmax=high)


def score_color(cmap, norm: Normalize, value: Any, alpha: float = 1.0) -> tuple[float, float, float, float]:
    score = safe_float(value)
    if score is None:
        return (0.88, 0.88, 0.88, alpha)
    r, g, b, _ = cmap(norm(score))
    return (r, g, b, alpha)


def text_color_for_score(value: Any) -> str:
    score = safe_float(value)
    if score is None:
        return "#111827"
    return "white" if score < 43 else "#111827"


def format_int(value: Any) -> str:
    number = safe_int(value)
    return str(number) if number is not None else "-"


def review_note(row: pd.Series) -> str:
    flags = str(row.get("major_review_flags", "")).strip()
    if flags and flags.lower() != "nan":
        return flags

    site_id = str(row.get("site_id", ""))
    risk = str(row.get("electrical_risk_level", "")).lower()
    bucket = str(row.get("decision_bucket", ""))
    if site_id == "PWC002":
        return "Garage / Fire Marshal / AHJ / electrical review"
    if site_id == "PWC003":
        return "Special-use or public-access decision"
    if site_id == "PWC008":
        return "Monitor due to nearby charging supply"
    if risk == "high":
        return "Electrical review before expansion"
    if bucket == "Refine assumptions":
        return "Verify site assumptions before advancement"
    return ""


def add_card(ax, x: float, y: float, width: float, height: float, row: pd.Series, cmap, norm: Normalize) -> None:
    score = row.get("readiness_score", None)
    color = score_color(cmap, norm, score, alpha=1.0)
    soft_color = score_color(cmap, norm, score, alpha=0.13)

    card = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.010,rounding_size=0.015",
        linewidth=1.15,
        edgecolor=color,
        facecolor=soft_color,
        zorder=2,
    )
    ax.add_patch(card)

    stripe_height = max(0.010, height * 0.075)
    ax.add_patch(Rectangle((x, y + height - stripe_height), width, stripe_height, facecolor=color, edgecolor="none", zorder=3))

    rank = format_int(row.get("model_rank"))
    site_id = str(row.get("site_id", ""))
    site_name = wrap_text(row.get("site_name", ""), 23)
    score_text = f"{safe_float(score):.1f}" if safe_float(score) is not None else "n/a"
    tier = str(row.get("tier_short", ""))
    ports_now = format_int(row.get("ports_now"))
    future_ready = format_int(row.get("future_ready_capacity"))
    risk = str(row.get("electrical_risk_level", "unknown")).title()
    current_alignment = str(row.get("current_alignment", "")).replace("_", " ")
    note = wrap_text(review_note(row), 31)

    left = x + 0.018
    top = y + height - 0.028
    ax.text(left, top, f"#{rank}  {site_id}", ha="left", va="top", fontsize=10.2, fontweight="bold", color="#111827", zorder=4)
    ax.text(left, top - height * 0.18, site_name, ha="left", va="top", fontsize=8.8, color="#111827", linespacing=1.05, zorder=4)
    ax.text(left, top - height * 0.46, f"Score {score_text} | {tier}", ha="left", va="top", fontsize=8.2, color="#1f2937", zorder=4)
    ax.text(left, top - height * 0.60, f"Ports {ports_now} now -> {future_ready} future", ha="left", va="top", fontsize=8.1, color="#1f2937", zorder=4)
    ax.text(left, top - height * 0.74, f"Electrical risk: {risk}", ha="left", va="top", fontsize=8.0, color="#1f2937", zorder=4)

    if current_alignment and current_alignment.lower() != "nan":
        ax.text(left, y + 0.043, current_alignment.title(), ha="left", va="bottom", fontsize=7.3, color="#374151", zorder=4)
    if note:
        ax.text(left, y + 0.016, f"Review: {note}", ha="left", va="bottom", fontsize=7.1, color="#6b3f00", linespacing=1.0, zorder=4)


def draw_board(ax, data: pd.DataFrame, cmap, norm: Normalize) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    gap_x = 0.014
    column_width = (1 - gap_x * (len(ACTION_ORDER) + 1)) / len(ACTION_ORDER)
    column_bottom = 0.018
    column_top = 0.985
    header_height = 0.088
    cards_top = column_top - header_height - 0.022
    cards_bottom = 0.040

    for index, bucket in enumerate(ACTION_ORDER):
        x = gap_x + index * (column_width + gap_x)
        sites = data[data["decision_bucket"] == bucket].sort_values("model_rank")

        column = FancyBboxPatch(
            (x, column_bottom),
            column_width,
            column_top - column_bottom,
            boxstyle="round,pad=0.006,rounding_size=0.014",
            linewidth=1.0,
            edgecolor="#d0d7de",
            facecolor="#f8fafc",
            zorder=1,
        )
        ax.add_patch(column)

        header = FancyBboxPatch(
            (x + 0.010, column_top - header_height),
            column_width - 0.020,
            header_height - 0.010,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            linewidth=0.8,
            edgecolor="#c7ccd1",
            facecolor="#eef2f7",
            zorder=2,
        )
        ax.add_patch(header)

        ax.text(
            x + column_width / 2,
            column_top - 0.031,
            f"{bucket} ({len(sites)})",
            ha="center",
            va="top",
            fontsize=10.0,
            fontweight="bold",
            color="#111827",
            zorder=3,
        )
        ax.text(
            x + column_width / 2,
            column_top - 0.058,
            BUCKET_DESCRIPTIONS[bucket],
            ha="center",
            va="top",
            fontsize=7.0,
            color="#4b5563",
            zorder=3,
        )

        if sites.empty:
            ax.text(x + column_width / 2, 0.48, "No sites", ha="center", va="center", fontsize=9, color="#6b7280", style="italic")
            continue

        card_gap = 0.015
        available_height = cards_top - cards_bottom
        card_height = min(0.164, (available_height - card_gap * (len(sites) - 1)) / len(sites))
        y = cards_top - card_height
        for _, row in sites.iterrows():
            add_card(ax, x + 0.010, y, column_width - 0.020, card_height, row, cmap, norm)
            y -= card_height + card_gap


def top_pwc_site(data: pd.DataFrame) -> pd.Series | None:
    pwc = data[data["site_id"].astype(str).str.startswith("PWC")].sort_values("model_rank")
    if pwc.empty:
        return None
    return pwc.iloc[0]


def draw_sidebar(ax, data: pd.DataFrame) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    box = FancyBboxPatch(
        (0.015, 0.015),
        0.970,
        0.970,
        boxstyle="round,pad=0.012,rounding_size=0.020",
        linewidth=1.0,
        edgecolor="#c7ccd1",
        facecolor="#ffffff",
        zorder=1,
    )
    ax.add_patch(box)

    ranked = data.sort_values("model_rank")
    top = ranked.iloc[0]
    top_pwc = top_pwc_site(data)

    lines = [
        "Decision highlights",
        "",
        "Top candidate",
        f"#{format_int(top.get('model_rank'))} {top.get('site_id')}",
        wrap_text(top.get("site_name", ""), 26),
        f"Score {safe_float(top.get('readiness_score')):.1f} | {compact_tier(top.get('recommendation_tier'))}",
        f"Ports {format_int(top.get('ports_now'))} now -> {format_int(top.get('future_ready_capacity'))} future",
        "",
    ]

    if top_pwc is not None:
        lines.extend([
            "Top Prince William site",
            f"#{format_int(top_pwc.get('model_rank'))} {top_pwc.get('site_id')}",
            wrap_text(top_pwc.get("site_name", ""), 26),
            f"Score {safe_float(top_pwc.get('readiness_score')):.1f}",
            "",
        ])

    lines.append("Top 3 overall")
    for _, row in ranked.head(3).iterrows():
        lines.append(f"• #{format_int(row.get('model_rank'))} {row.get('site_id')} — {safe_float(row.get('readiness_score')):.1f}")

    lines.extend(["", "Bucket counts"])
    for bucket in ACTION_ORDER:
        lines.append(f"• {bucket}: {int((data['decision_bucket'] == bucket).sum())}")

    lines.extend([
        "",
        "How to read",
        "• Columns = action decision",
        "• Card shade = readiness score",
        "• Ports line = now -> future-ready",
        "• Risk line = electrical screen",
    ])

    ax.text(0.055, 0.955, "\n".join(lines), ha="left", va="top", fontsize=9.3, color="#111827", linespacing=1.28, zorder=2)


def draw_header(fig, data: pd.DataFrame) -> None:
    top = data.sort_values("model_rank").iloc[0]
    fig.text(0.043, 0.965, "Candidate EV Charging Sites — Decision Board", ha="left", va="top", fontsize=21, fontweight="bold", color="#111827")
    fig.text(
        0.043,
        0.936,
        f"{len(data)} candidate sites grouped by planning action | top current site: {top.get('site_id')} ({safe_float(top.get('readiness_score')):.1f})",
        ha="left",
        va="top",
        fontsize=11.2,
        color="#4b5563",
    )


def draw_footer(fig) -> None:
    fig.text(
        0.043,
        0.018,
        "Planning prototype visual only — supports early screening and prioritization; not a permitting, engineering, utility, procurement, or construction approval.",
        ha="left",
        va="bottom",
        fontsize=8.8,
        color="#6b7280",
    )


def plot_decision_board(data: pd.DataFrame, output_path: Path) -> None:
    ensure_parent(output_path)
    cmap = plt.get_cmap("viridis")
    norm = score_norm(data)

    fig = plt.figure(figsize=(19, 11), facecolor="white")
    board_ax = fig.add_axes([0.035, 0.080, 0.735, 0.825])
    sidebar_ax = fig.add_axes([0.790, 0.120, 0.180, 0.742])

    draw_board(board_ax, data, cmap, norm)
    draw_sidebar(sidebar_ax, data)
    draw_header(fig, data)
    draw_footer(fig)

    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a redesigned V2 site decision board.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="V2 executive summary CSV input.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output PNG path.")
    # Backward-compatible ignored arguments so older workflow commands do not crash.
    parser.add_argument("--results", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--electrical-summary", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--right-sizing", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--right-sizing-validation", default=None, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    data = load_data(input_path)
    plot_decision_board(data, output_path)

    print("V2 SITE DECISION BOARD")
    print("----------------------")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Sites plotted: {len(data)}")
    print("Done.")


if __name__ == "__main__":
    main()
