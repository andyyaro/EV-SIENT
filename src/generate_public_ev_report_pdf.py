"""Generate the public EV charging planning PDF report from V2 model outputs."""
from __future__ import annotations

import argparse
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DEFAULT_EXECUTIVE_SUMMARY = "data/outputs/v2_executive_site_summary.csv"
DEFAULT_QUALITY = "data/outputs/v2_data_quality_report.csv"
DEFAULT_SCENARIOS = "data/outputs/v2_port_sizing_scenario_results.csv"
DEFAULT_OUTPUT = "data/outputs/Public_EV_Charging_Planning_Report.pdf"
REPORT_TITLE = "Public EV Charging Planning Report"
REPORT_SUBTITLE = "Site-readiness and right-sizing model results"
REPORT_FILENAME = "Public_EV_Charging_Planning_Report.pdf"
DISCLAIMER = (
    "Planning-support artifact only. These outputs support early screening, prioritization, and discussion. "
    "They do not replace final engineering design, utility coordination, permitting, procurement, ADA review, "
    "fire/AHJ review, stormwater review, construction approval, site survey, or stakeholder confirmation."
)
BUCKETS = [
    ("Advance / strong starter candidates", "These are the strongest current starter candidates in the model."),
    ("Good starter candidates with expandable design", "These sites may support starter installations, but should be planned with expansion and verification in mind."),
    ("Resolve review issues before expansion", "These sites may be useful, but review burden or electrical constraints should be addressed before major expansion."),
    ("Monitor / small pilot", "These sites should be monitored or considered for smaller pilot-style planning rather than immediate expansion."),
    ("Do not advance for general-public buildout yet", "A site should not advance as a general-public charging site unless public-access or fleet-only use-case assumptions change."),
]
REVIEW_FIELDS = [
    "electrical service rating", "spare electrical capacity", "emergency disconnect visibility",
    "visitor/employee counts", "operating hours", "parking count", "likely charger placement",
    "garage/fire/AHJ/access review for garage or special-use sites",
]
SCENARIOS = ["base", "high_growth", "long_sessions", "short_daily_window", "peakier_demand", "combined_stress"]


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_csv(path: str | Path, *, required: bool = False) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        if required:
            raise FileNotFoundError(f"Required input not found: {file_path}")
        return pd.DataFrame()
    return pd.read_csv(file_path)


def clean(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return (str(value).strip().replace("—", "-").replace("–", "-").replace("“", '"').replace("”", '"').replace("’", "'"))


def num(value: Any) -> float:
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else 0.0
    except (TypeError, ValueError):
        return 0.0


def as_int(value: Any) -> str:
    return str(int(round(num(value)))) if clean(value) != "" else ""


def score(value: Any) -> str:
    return f"{num(value):.1f}"


def tier_short(value: Any) -> str:
    text = clean(value)
    if text.startswith("Tier 1"):
        return "Tier 1"
    if text.startswith("Tier 2"):
        return "Tier 2"
    if text.startswith("Tier 3"):
        return "Tier 3"
    if text.startswith("High-review"):
        return "High-review"
    if "special" in text.lower() or "low public" in text.lower():
        return "Special-use"
    return text


def bucket_for(row: pd.Series) -> str:
    tier = clean(row.get("recommendation_tier", ""))
    strategy = clean(row.get("expansion_strategy", "")).lower()
    rec = clean(row.get("planning_recommendation", "")).lower()
    if tier.startswith("Tier 1"):
        return BUCKETS[0][0]
    if tier.startswith("Tier 2"):
        return BUCKETS[1][0]
    if tier.startswith("High-review") or "electrical_review" in strategy or "review before" in rec:
        return BUCKETS[2][0]
    if tier.startswith("Tier 3") or "monitor" in strategy or "monitor" in rec:
        return BUCKETS[3][0]
    if tier.startswith("Low public") or "special" in tier.lower() or "do_not_advance" in strategy:
        return BUCKETS[4][0]
    return BUCKETS[3][0]


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=28, leading=33, alignment=TA_CENTER, spaceAfter=16),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontName="Helvetica", fontSize=13, leading=18, textColor=colors.HexColor("#55555a"), alignment=TA_CENTER, spaceAfter=8),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=23, spaceBefore=8, spaceAfter=12),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, spaceBefore=6, spaceAfter=6),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=colors.HexColor("#222226"), spaceAfter=8),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName="Helvetica", fontSize=8, leading=11, textColor=colors.HexColor("#55555a")),
        "th": ParagraphStyle("th", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=colors.white),
        "td": ParagraphStyle("td", parent=base["BodyText"], fontName="Helvetica", fontSize=7.5, leading=9.5, textColor=colors.HexColor("#222226")),
        "metric_value": ParagraphStyle("metric_value", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.white, alignment=TA_CENTER),
        "metric_label": ParagraphStyle("metric_label", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#cfcfd2"), alignment=TA_CENTER),
    }


def para(text: Any, st: dict[str, ParagraphStyle], kind: str = "body") -> Paragraph:
    escaped = clean(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(escaped, st[kind])


def cell(text: Any, st: dict[str, ParagraphStyle], header: bool = False) -> Paragraph:
    return para(text, st, "th" if header else "td")


def table_style(table: Table) -> None:
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b0b0c")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d9d9de")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f8fa")]),
    ]))


def severity_count(quality: pd.DataFrame, severity: str) -> int:
    if quality.empty or "severity" not in quality.columns:
        return 0
    return int((quality["severity"].astype(str).str.upper() == severity).sum())


def summary_metrics(summary: pd.DataFrame, quality: pd.DataFrame, tableau_exports: int) -> dict[str, str]:
    categories = {bucket_for(row) for _, row in summary.iterrows()} if not summary.empty else set()
    tier1 = int(summary["recommendation_tier"].astype(str).str.startswith("Tier 1").sum()) if "recommendation_tier" in summary.columns else 0
    return {
        "Candidate sites": str(len(summary)), "Tier 1 starters": str(tier1),
        "Decision categories": str(len(categories)), "Tableau-ready exports": str(tableau_exports),
        "Blocking validation errors": str(severity_count(quality, "ERROR")),
        "Review confirmations": str(severity_count(quality, "REVIEW")),
    }


def metric_callout(metrics: dict[str, str], st: dict[str, ParagraphStyle]) -> Table:
    row = [[para(value, st, "metric_value"), para(label, st, "metric_label")] for label, value in metrics.items()]
    t = Table([row], colWidths=[1.05 * inch] * len(row), hAlign="CENTER")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0b0b0c")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#333338")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def ranking_table(summary: pd.DataFrame, st: dict[str, ParagraphStyle]) -> LongTable:
    rows = [[cell(h, st, True) for h in ["Rank", "Site", "Readiness", "Tier", "Planning note"]]]
    for _, r in summary.iterrows():
        site = f"{clean(r.get('site_id'))} - {clean(r.get('site_name'))}"
        note = r.get("planning_recommendation", r.get("priority_reason", ""))
        rows.append([cell(as_int(r.get("model_rank")), st), cell(site, st), cell(score(r.get("readiness_score")), st), cell(tier_short(r.get("recommendation_tier")), st), cell(note, st)])
    t = LongTable(rows, colWidths=[0.42 * inch, 1.8 * inch, 0.65 * inch, 0.75 * inch, 2.7 * inch], repeatRows=1)
    table_style(t)
    return t


def right_sizing_table(summary: pd.DataFrame, st: dict[str, ParagraphStyle]) -> LongTable:
    rows = [[cell(h, st, True) for h in ["Site", "Install now", "Future-ready", "Strategy / note"]]]
    for _, r in summary.iterrows():
        site = f"{clean(r.get('site_id'))} - {clean(r.get('site_name'))}"
        note = r.get("right_sizing_validation_note", r.get("expansion_strategy", r.get("planning_recommendation", "")))
        rows.append([cell(site, st), cell(as_int(r.get("ports_now")), st), cell(as_int(r.get("future_ready_capacity")), st), cell(note, st)])
    t = LongTable(rows, colWidths=[2.2 * inch, 0.85 * inch, 0.9 * inch, 2.7 * inch], repeatRows=1)
    table_style(t)
    return t


def decision_bucket_blocks(summary: pd.DataFrame, st: dict[str, ParagraphStyle]) -> list[Any]:
    if summary.empty:
        return [para("No decision-bucket data available.", st)]
    output: list[Any] = []
    data = summary.copy()
    data["decision_category"] = data.apply(bucket_for, axis=1)
    for i, (bucket, meaning) in enumerate(BUCKETS, start=1):
        rows = data[data["decision_category"] == bucket]
        if rows.empty:
            continue
        sites = "; ".join(f"{clean(row.site_id)} - {clean(row.site_name)}" for row in rows.itertuples())
        output += [para(f"{i}. {bucket}", st, "h2"), para(meaning, st), para(f"Sites: {sites}", st), Spacer(1, 0.05 * inch)]
    return output


def review_blocks(quality: pd.DataFrame, st: dict[str, ParagraphStyle]) -> list[Any]:
    counts = {s: severity_count(quality, s) for s in ["ERROR", "WARNING", "REVIEW", "INFO"]}
    rows = [[cell(h, st, True) for h in ["Error", "Warning", "Review", "Info"]], [cell(counts["ERROR"], st), cell(counts["WARNING"], st), cell(counts["REVIEW"], st), cell(counts["INFO"], st)]]
    t = Table(rows, colWidths=[1.4 * inch] * 4, hAlign="LEFT")
    table_style(t)
    bullets = [para(f"• {field}", st) for field in REVIEW_FIELDS]
    return [para("Review flags are not failures; they identify where more confirmation is needed before final planning or implementation.", st), t, Spacer(1, 0.16 * inch), para("Recurring fields requiring confirmation", st, "h2"), *bullets]


def scenario_blocks(scenarios: pd.DataFrame, st: dict[str, ParagraphStyle]) -> list[Any]:
    if scenarios.empty or "scenario_name" not in scenarios.columns or "future_capacity_gap" not in scenarios.columns:
        return [para("Scenario results were not available in the expected scenario-output file.", st)]
    data = scenarios.copy()
    data["future_capacity_gap"] = pd.to_numeric(data["future_capacity_gap"], errors="coerce").fillna(0)
    max_gap = data.groupby("scenario_name", dropna=False)["future_capacity_gap"].max().to_dict()
    no_gap = [s for s in SCENARIOS if s in max_gap and num(max_gap[s]) <= 0]
    with_gap = [s for s in SCENARIOS if s in max_gap and num(max_gap[s]) > 0]
    output = []
    if no_gap:
        output.append(para(f"No future-ready capacity gaps in: {', '.join(no_gap)}.", st))
    if with_gap:
        output.append(para(f"Future-ready capacity gaps appear in: {', '.join(with_gap)}.", st))
    gap_rows = data[data["future_capacity_gap"] > 0]
    if not gap_rows.empty:
        rows = [[cell(h, st, True) for h in ["Scenario", "Site", "Gap"]]]
        for _, r in gap_rows.iterrows():
            rows.append([cell(r.get("scenario_name"), st), cell(r.get("site_id"), st), cell(as_int(r.get("future_capacity_gap")), st)])
        t = Table(rows, colWidths=[2.2 * inch, 2.0 * inch, 0.8 * inch], hAlign="LEFT")
        table_style(t)
        output.append(t)
    return output


def footer(canvas, doc) -> None:  # noqa: ANN001 - ReportLab callback signature
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#77777c"))
    canvas.drawCentredString(letter[0] / 2, 0.42 * inch, f"Public EV Charging Planning Report | Planning-support artifact only | Page {doc.page}")
    canvas.restoreState()


def story(summary: pd.DataFrame, quality: pd.DataFrame, scenarios: pd.DataFrame, generated_at: str, tableau_exports: int) -> list[Any]:
    st = styles()
    items: list[Any] = [Spacer(1, 1.05 * inch), para(REPORT_TITLE, st, "title"), para(REPORT_SUBTITLE, st, "subtitle"), para("Future City Fellowship Phase 2 prototype", st, "subtitle"), Spacer(1, 0.2 * inch), para(f"Generated: {generated_at}", st, "subtitle"), para(f"File: {REPORT_FILENAME}", st, "subtitle"), Spacer(1, 0.35 * inch), para(DISCLAIMER, st), PageBreak()]
    items += [para("Executive Summary", st, "h1"), para("This report summarizes the latest run of the public EV charging site-readiness and right-sizing model. It is intended to help screen candidate sites, compare planning signals, identify starter candidates, and surface review needs before implementation decisions move forward.", st), metric_callout(summary_metrics(summary, quality, tableau_exports), st), Spacer(1, 0.22 * inch)]
    if not summary.empty:
        top = summary.sort_values("model_rank").iloc[0]
        items.append(para(f"Top current planning signal: {clean(top.get('site_id'))} - {clean(top.get('site_name'))}, with readiness score {score(top.get('readiness_score'))}.", st))
    items += [para(DISCLAIMER, st, "small"), PageBreak(), para("Current Ranking", st, "h1"), para("The ranking lists the candidate sites in order of current model readiness. Scores are screening indicators, not final approvals.", st), ranking_table(summary, st), PageBreak(), para("Decision Buckets", st, "h1"), para("Decision buckets translate scores and review signals into planning categories for discussion.", st), *decision_bucket_blocks(summary, st), PageBreak(), para("Right-Sizing Recommendations", st, "h1"), para("Right-sizing separates install-now ports from future-ready capacity. Install-now ports represent starter planning, while future-ready capacity indicates what the site may need to accommodate as demand grows.", st), right_sizing_table(summary, st), PageBreak(), para("Review Burden", st, "h1"), *review_blocks(quality, st), PageBreak(), para("Scenario Sensitivity", st, "h1"), para("Scenario testing checks whether future-ready capacity remains adequate under alternate planning assumptions such as high growth, longer sessions, shorter daily charging windows, peakier demand, and combined stress.", st), *scenario_blocks(scenarios, st), PageBreak(), para("Planning Interpretation", st, "h1"), para("Use the report as a starting point for prioritization. Strong starter candidates should move into facility, utility, ADA, fire/AHJ, and stakeholder confirmation. Sites with review burdens should resolve key implementation questions before major expansion. Sites with lower public-priority or special-use signals should not be treated as general-public buildout candidates unless the public-access or fleet-only use case changes.", st), Spacer(1, 0.14 * inch), para("Planning-Support Disclaimer", st, "h1"), para(DISCLAIMER, st)]
    return items


def build_pdf(args: argparse.Namespace) -> None:
    summary = read_csv(args.executive_summary, required=True)
    quality = read_csv(args.quality)
    scenarios = read_csv(args.scenarios)
    ensure_parent(args.output)
    doc = SimpleDocTemplate(args.output, pagesize=letter, rightMargin=0.55 * inch, leftMargin=0.55 * inch, topMargin=0.55 * inch, bottomMargin=0.65 * inch, title=REPORT_TITLE, author="Future City Fellowship EV Charging Project")
    doc.build(story(summary, quality, scenarios, args.generated_at, args.tableau_export_count), onFirstPage=footer, onLaterPages=footer)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the public EV charging planning PDF report from V2 model outputs.")
    parser.add_argument("--executive-summary", default=DEFAULT_EXECUTIVE_SUMMARY)
    parser.add_argument("--quality", default=DEFAULT_QUALITY)
    parser.add_argument("--scenarios", default=DEFAULT_SCENARIOS)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--generated-at", default=datetime.now().strftime("%Y-%m-%d %H:%M"))
    parser.add_argument("--tableau-export-count", type=int, default=15)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_pdf(args)
    print("PUBLIC EV CHARGING PLANNING REPORT")
    print("-----------------------------------")
    print(f"Saved PDF: {args.output}")


if __name__ == "__main__":
    main()
