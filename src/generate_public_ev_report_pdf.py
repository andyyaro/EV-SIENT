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
TITLE = "Public EV Charging Planning Report"
SUBTITLE = "Site-readiness and right-sizing model results"
DISCLAIMER = (
    "Planning-support artifact only. These outputs support early screening, prioritization, and discussion. "
    "They do not replace final engineering design, utility coordination, permitting, procurement, ADA review, "
    "fire/AHJ review, stormwater review, construction approval, site survey, or stakeholder confirmation."
)
FONT, BOLD, ITALIC = "Times-Roman", "Times-Bold", "Times-Italic"
SCENARIOS = ["base", "high_growth", "long_sessions", "short_daily_window", "peakier_demand", "combined_stress"]
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
    "garage/fire/AHJ/access review",
]


def clean(x: Any) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    s = str(x).strip()
    for a, b in {"—": "-", "–": "-", "“": '"', "”": '"', "’": "'", "•": "-"}.items():
        s = s.replace(a, b)
    return s


def esc(x: Any) -> str:
    return clean(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def n(x: Any) -> float:
    try:
        y = float(x)
        return y if math.isfinite(y) else 0.0
    except Exception:
        return 0.0


def site(r: pd.Series) -> str:
    return f"{clean(r.get('site_id'))} - {clean(r.get('site_name'))}"


def tier(x: Any) -> str:
    t = clean(x)
    if t.startswith("Tier 1"):
        return "Tier 1"
    if t.startswith("Tier 2"):
        return "Tier 2"
    if t.startswith("Tier 3"):
        return "Tier 3"
    if t.startswith("High-review"):
        return "High-review"
    if "special" in t.lower() or "low public" in t.lower():
        return "Special-use"
    return t


def bucket(r: pd.Series) -> str:
    t = clean(r.get("recommendation_tier"))
    strategy = clean(r.get("expansion_strategy")).lower()
    rec = clean(r.get("planning_recommendation")).lower()
    if t.startswith("Tier 1"):
        return BUCKETS[0][0]
    if t.startswith("Tier 2"):
        return BUCKETS[1][0]
    if t.startswith("High-review") or "electrical_review" in strategy or "review before" in rec:
        return BUCKETS[2][0]
    if t.startswith("Tier 3") or "monitor" in strategy or "monitor" in rec:
        return BUCKETS[3][0]
    if t.startswith("Low public") or "special" in t.lower() or "do_not_advance" in strategy:
        return BUCKETS[4][0]
    return BUCKETS[3][0]


def read_csv(path: str, required: bool = False) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        if required:
            raise FileNotFoundError(f"Required input not found: {p}")
        return pd.DataFrame()
    return pd.read_csv(p)


def style() -> dict[str, ParagraphStyle]:
    b = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=b["Title"], fontName=BOLD, fontSize=30, leading=36, alignment=TA_CENTER, spaceAfter=16),
        "sub": ParagraphStyle("sub", parent=b["Normal"], fontName=FONT, fontSize=13, leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#444444"), spaceAfter=8),
        "h1": ParagraphStyle("h1", parent=b["Heading1"], fontName=BOLD, fontSize=18, leading=23, spaceBefore=10, spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=b["Heading2"], fontName=BOLD, fontSize=12.5, leading=16, spaceBefore=8, spaceAfter=5),
        "p": ParagraphStyle("p", parent=b["BodyText"], fontName=FONT, fontSize=10.2, leading=14.2, spaceAfter=8),
        "small": ParagraphStyle("small", parent=b["BodyText"], fontName=ITALIC, fontSize=8.5, leading=11.5, textColor=colors.HexColor("#555555")),
        "th": ParagraphStyle("th", parent=b["BodyText"], fontName=BOLD, fontSize=8.0, leading=9.6, textColor=colors.white),
        "td": ParagraphStyle("td", parent=b["BodyText"], fontName=FONT, fontSize=8.0, leading=10.0),
        "mv": ParagraphStyle("mv", parent=b["BodyText"], fontName=BOLD, fontSize=18, leading=21, alignment=TA_CENTER),
        "ml": ParagraphStyle("ml", parent=b["BodyText"], fontName=FONT, fontSize=7.8, leading=9.5, alignment=TA_CENTER, textColor=colors.HexColor("#555555")),
    }


def P(x: Any, s: dict[str, ParagraphStyle], k: str = "p") -> Paragraph:
    return Paragraph(esc(x), s[k])


def C(x: Any, s: dict[str, ParagraphStyle], header: bool = False) -> Paragraph:
    return P(x, s, "th" if header else "td")


def style_table(t: Table) -> Table:
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d0d0d0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
    ]))
    return t


def divider() -> Table:
    t = Table([[""]], colWidths=[7.1 * inch], rowHeights=[0.02 * inch])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.black)]))
    return t


def severity(q: pd.DataFrame, val: str) -> int:
    return 0 if q.empty or "severity" not in q.columns else int((q["severity"].astype(str).str.upper() == val).sum())


def metrics(summary: pd.DataFrame, quality: pd.DataFrame, exports: int, s: dict[str, ParagraphStyle]) -> Table:
    cats = {bucket(r) for _, r in summary.iterrows()} if not summary.empty else set()
    tier1 = int(summary["recommendation_tier"].astype(str).str.startswith("Tier 1").sum()) if "recommendation_tier" in summary.columns else 0
    vals = {"Candidate sites": len(summary), "Tier 1 starters": tier1, "Decision categories": len(cats), "Tableau exports": exports, "Blocking errors": severity(quality, "ERROR"), "Review items": severity(quality, "REVIEW")}
    t = Table([[P(v, s, "mv") for v in vals.values()], [P(k.upper(), s, "ml") for k in vals.keys()]], colWidths=[1.15 * inch] * 6)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d7d7d7")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def intro_table(s: dict[str, ParagraphStyle], generated: str) -> Table:
    rows = [[C("Report title", s, True), C(TITLE, s)], [C("Generated", s, True), C(generated, s)], [C("Purpose", s, True), C("Screen candidate public EV charging sites, right-size starter installations, and identify review needs.", s)], [C("Use boundary", s, True), C("Planning support only; not engineering, permitting, procurement, or construction approval.", s)]]
    t = Table(rows, colWidths=[1.35 * inch, 5.6 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#111111")), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d0d0d0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def ranking(summary: pd.DataFrame, s: dict[str, ParagraphStyle]) -> LongTable:
    rows = [[C(h, s, True) for h in ["Rank", "Site", "Score", "Tier", "Planning recommendation"]]]
    for _, r in summary.iterrows():
        rows.append([C(int(n(r.get("model_rank"))), s), C(site(r), s), C(f"{n(r.get('readiness_score')):.1f}", s), C(tier(r.get("recommendation_tier")), s), C(r.get("planning_recommendation", r.get("priority_reason", "")), s)])
    return style_table(LongTable(rows, colWidths=[0.42 * inch, 1.8 * inch, 0.5 * inch, 0.78 * inch, 3.45 * inch], repeatRows=1))


def buckets(summary: pd.DataFrame, s: dict[str, ParagraphStyle]) -> Table:
    data = summary.copy()
    if not data.empty:
        data["decision_category"] = data.apply(bucket, axis=1)
    rows = [[C(h, s, True) for h in ["Decision category", "Meaning", "Sites"]]]
    for name, meaning in BUCKETS:
        sub = data[data["decision_category"] == name] if not data.empty else pd.DataFrame()
        sites = "; ".join(site(r) for _, r in sub.iterrows()) if not sub.empty else "None in this run"
        rows.append([C(name, s), C(meaning, s), C(sites, s)])
    return style_table(Table(rows, colWidths=[1.65 * inch, 2.5 * inch, 2.8 * inch], repeatRows=1))


def sizing(summary: pd.DataFrame, s: dict[str, ParagraphStyle]) -> LongTable:
    rows = [[C(h, s, True) for h in ["Site", "Install now", "Future-ready", "Strategy / review note"]]]
    for _, r in summary.iterrows():
        note = r.get("right_sizing_validation_note", "") or r.get("expansion_strategy", "") or r.get("planning_recommendation", "")
        rows.append([C(site(r), s), C(int(n(r.get("ports_now"))), s), C(int(n(r.get("future_ready_capacity"))), s), C(note, s)])
    return style_table(LongTable(rows, colWidths=[2.15 * inch, 0.85 * inch, 0.9 * inch, 3.05 * inch], repeatRows=1))


def scenario_summary(scenarios: pd.DataFrame, s: dict[str, ParagraphStyle]) -> Table:
    rows = [[C(h, s, True) for h in ["Scenario", "Maximum future-ready gap", "Sites with a gap"]]]
    if scenarios.empty or "scenario_name" not in scenarios.columns or "future_capacity_gap" not in scenarios.columns:
        rows.append([C("Not available", s), C("", s), C("Scenario output was not available in the expected format.", s)])
    else:
        data = scenarios.copy()
        data["future_capacity_gap"] = pd.to_numeric(data["future_capacity_gap"], errors="coerce").fillna(0)
        names = SCENARIOS + [x for x in data["scenario_name"].astype(str).drop_duplicates().tolist() if x not in SCENARIOS]
        for name in names:
            sub = data[data["scenario_name"].astype(str) == name]
            if sub.empty:
                continue
            gaps = sub[sub["future_capacity_gap"] > 0]
            sites = "; ".join(f"{clean(r.get('site_id'))}: gap {int(n(r.get('future_capacity_gap')))}" for _, r in gaps.iterrows()) if not gaps.empty else "None"
            rows.append([C(sub.iloc[0].get("scenario_label", name), s), C(int(sub["future_capacity_gap"].max()), s), C(sites, s)])
    return style_table(Table(rows, colWidths=[2.0 * inch, 1.65 * inch, 3.3 * inch], repeatRows=1))


def bullets(items: list[str], s: dict[str, ParagraphStyle]) -> list[Any]:
    return [P(f"- {x}", s) for x in items]


def findings(summary: pd.DataFrame, scenarios: pd.DataFrame) -> list[str]:
    out: list[str] = []
    if not summary.empty:
        ordered = summary.sort_values("model_rank")
        top = ordered.iloc[0]
        out.append(f"{site(top)} is the strongest current planning signal, with readiness score {n(top.get('readiness_score')):.1f}.")
        t1 = ordered[ordered["recommendation_tier"].astype(str).str.startswith("Tier 1")]
        if not t1.empty:
            out.append("Tier 1 starter candidates in this run are: " + "; ".join(site(r) for _, r in t1.iterrows()) + ".")
    if not scenarios.empty and "future_capacity_gap" in scenarios.columns:
        d = scenarios.copy()
        d["future_capacity_gap"] = pd.to_numeric(d["future_capacity_gap"], errors="coerce").fillna(0)
        gaps = d[d["future_capacity_gap"] > 0]
        out.append("No future-ready capacity gaps appear in the tested port-sizing scenarios." if gaps.empty else "Scenario testing identifies future-ready capacity gaps for: " + "; ".join(f"{clean(r.get('site_id'))} under {clean(r.get('scenario_name'))}" for _, r in gaps.iterrows()) + ".")
    out.append("All results remain planning-screen indicators and require facility, utility, ADA, fire/AHJ, permitting, procurement, and stakeholder confirmation before implementation.")
    return out


def footer(canvas, doc) -> None:
    canvas.saveState()
    w, _ = letter
    canvas.setStrokeColor(colors.HexColor("#d0d0d0"))
    canvas.line(0.65 * inch, 0.58 * inch, w - 0.65 * inch, 0.58 * inch)
    canvas.setFont(FONT, 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(0.65 * inch, 0.38 * inch, TITLE)
    canvas.drawRightString(w - 0.65 * inch, 0.38 * inch, f"Page {doc.page}")
    canvas.restoreState()


def section(story: list[Any], title: str, intro: str, body: list[Any], s: dict[str, ParagraphStyle], br: bool = True) -> None:
    story += [P(title, s, "h1"), divider(), Spacer(1, 0.12 * inch), P(intro, s), *body]
    if br:
        story.append(PageBreak())


def build_story(summary: pd.DataFrame, quality: pd.DataFrame, scenarios: pd.DataFrame, generated: str, exports: int) -> list[Any]:
    s = style()
    story: list[Any] = [
        Spacer(1, 0.85 * inch), P(TITLE, s, "title"), P(SUBTITLE, s, "sub"),
        P("Future City Fellowship Phase 2 prototype", s, "sub"), P("Built by Andy Yaro, George Mason University", s, "sub"),
        Spacer(1, 0.3 * inch), divider(), Spacer(1, 0.25 * inch), intro_table(s, generated),
        Spacer(1, 0.35 * inch), P(DISCLAIMER, s, "small"), PageBreak(),
    ]
    section(story, "Executive Summary", "This report summarizes the latest run of the public EV charging site-readiness and right-sizing model. It is intended to compare candidate sites, identify stronger starter opportunities, flag review needs, and separate near-term installation from future-ready planning.", [metrics(summary, quality, exports, s), Spacer(1, 0.18 * inch), P("Key findings", s, "h2"), *bullets(findings(summary, scenarios), s), P(DISCLAIMER, s, "small")], s)
    section(story, "Current Site Ranking", "The ranking below orders candidate sites by the current readiness score. The score is a screening signal only; it should guide review and discussion rather than determine final approval.", [ranking(summary, s)], s)
    section(story, "Decision Buckets", "Decision buckets translate the model outputs into planning categories that are easier to discuss with stakeholders.", [buckets(summary, s)], s)
    section(story, "Right-Sizing Recommendations", "Right-sizing separates install-now ports from future-ready capacity. Install-now ports represent starter planning. Future-ready capacity indicates what the site should be prepared to accommodate if demand grows.", [sizing(summary, s)], s)
    section(story, "Review Burden", "Review flags are not failures. They identify inputs or site conditions that need confirmation before final design, procurement, permitting, or implementation decisions.", [style_table(Table([[C(h, s, True) for h in ["Error", "Warning", "Review", "Info"]], [C(severity(quality, "ERROR"), s), C(severity(quality, "WARNING"), s), C(severity(quality, "REVIEW"), s), C(severity(quality, "INFO"), s)]], colWidths=[1.25 * inch] * 4)), Spacer(1, 0.16 * inch), P("Recurring confirmation fields", s, "h2"), *bullets(REVIEW_FIELDS, s)], s)
    section(story, "Scenario Sensitivity", "Scenario testing checks whether future-ready capacity remains adequate under alternate planning assumptions, including higher growth, longer charging sessions, shorter charging windows, peakier demand, and combined stress.", [scenario_summary(scenarios, s)], s)
    section(story, "Planning Interpretation", "Use the report as a starting point for prioritization. Strong starter candidates should move into facility, utility, ADA, fire/AHJ, and stakeholder confirmation. Sites with higher review burden should resolve implementation questions before major expansion. Sites with lower public-priority or special-use signals should not be treated as general-public buildout candidates unless the public-access or fleet-only use case changes.", [Spacer(1, 0.1 * inch), P("Planning-support disclaimer", s, "h2"), P(DISCLAIMER, s)], s, br=False)
    return story


def build_pdf(args: argparse.Namespace) -> None:
    summary = read_csv(args.executive_summary, True)
    quality = read_csv(args.quality)
    scenarios = read_csv(args.scenarios)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(args.output, pagesize=letter, rightMargin=0.65 * inch, leftMargin=0.65 * inch, topMargin=0.65 * inch, bottomMargin=0.72 * inch, title=TITLE, author="Future City Fellowship EV Charging Project")
    doc.build(build_story(summary, quality, scenarios, args.generated_at, args.tableau_export_count), onFirstPage=footer, onLaterPages=footer)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate the public EV charging planning PDF report from V2 model outputs.")
    p.add_argument("--executive-summary", default=DEFAULT_EXECUTIVE_SUMMARY)
    p.add_argument("--quality", default=DEFAULT_QUALITY)
    p.add_argument("--scenarios", default=DEFAULT_SCENARIOS)
    p.add_argument("--output", default=DEFAULT_OUTPUT)
    p.add_argument("--generated-at", default=datetime.now().strftime("%Y-%m-%d %H:%M"))
    p.add_argument("--tableau-export-count", type=int, default=15)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    build_pdf(args)
    print("PUBLIC EV CHARGING PLANNING REPORT")
    print("-----------------------------------")
    print(f"Saved PDF: {args.output}")


if __name__ == "__main__":
    main()
