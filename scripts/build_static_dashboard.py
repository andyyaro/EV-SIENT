"""Build the static presentation dashboard from the canonical contract.

Prerequisite: `make run-v3` (populates data/outputs/v3_run).

Every visual: contract-derived values, warm-beige identity, mandatory provenance footer
(fcf_m2.visuals), offline-openable PNG + one combined PDF.
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import visuals, gis_offline  # noqa: E402
from fcf_m2.visuals import BEIGE, DARK_GREEN, MID_GREEN, BLACK, ACCENT  # noqa: E402

OUT = REPO / "dashboard/static"
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / "footer_log.json"

# The footer log is rebuilt, not extended. visuals.save() appends to whatever is
# already on disk, so leaving a previous run's file in place would duplicate every
# entry on each build (9 charts -> 18 entries -> 27 ...). Clearing it here keeps a
# rebuild idempotent, which is what the drift gate assumes.
LOG.unlink(missing_ok=True)

scen = pd.read_csv(REPO / "data/contract/v1/scenario_table.csv")
sites_dim = pd.read_csv(REPO / "data/contract/v1/site_table.csv")
v3run = REPO / "data/outputs/v3_run"  # produce with: make run-v3
legacy_scores = pd.read_csv(v3run / "site_results_legacy_v2.csv")
conf = pd.read_csv(v3run / "data_confidence_v3.csv")
econ_p = pd.read_csv(v3run / "lifecycle_costs_portfolio.csv")
peaks = pd.read_csv(v3run / "peak_wait_simulation.csv")
avoided = pd.read_csv(v3run / "avoided_evse_metric.csv")

CONTRACT_SRC = "canonical contract v1.0.0 (fcf_m2 V3 run 2026-07-19)"
VINTAGE = "inputs 2026-06-24; eGRID2023r2; verified 2026-07-19"


def c1_ranking():
    df = legacy_scores.merge(conf, on="site_id").sort_values("readiness_score")
    fig, ax = plt.subplots(figsize=(9, 6))
    visuals.style_axes(ax)
    colors = [DARK_GREEN if r <= 3 else MID_GREEN for r in df["model_rank"]]
    ax.barh(df["site_id"] + "  " + df["site_name"].str.slice(0, 34), df["readiness_score"], color=colors)
    ax.set_xlabel("Readiness score (accepted V2 baseline, model of record)")
    ax.set_title("Site readiness ranking — FFX002 leads at 58.8 (Medium confidence)", fontsize=12)
    for y, (s, cl) in enumerate(zip(df["readiness_score"], df["data_confidence_level_v3"])):
        ax.text(s + 0.5, y, cl, va="center", fontsize=7, color=BLACK)
    visuals.footer(fig, CONTRACT_SRC, VINTAGE, "legacy_v2 baseline scores",
                   "all 12 sites score Low data confidence; none reaches Medium")
    visuals.save(fig, OUT / "01_readiness_ranking.png", LOG, relative_to=REPO)


def c2_ports():
    base = scen[(scen.horizon_year == 2026) & (scen.scenario_name == "baseline")].sort_values("ports_pathway_capacity", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 6))
    visuals.style_axes(ax)
    y = np.arange(len(base))
    ax.barh(y, base["ports_pathway_capacity"], color="#D8CDB6", label="Future-ready pathway (48 total)")
    ax.barh(y, base["ports_active"], color=DARK_GREEN, label="Starter ports 2026 (25 total)")
    ax.set_yticks(y, base["site_id"])
    ax.set_xlabel("Ports")
    ax.set_title("Start small, stay expandable: 25 starter ports inside a 48-port pathway", fontsize=12)
    ax.legend(loc="lower right", frameon=False)
    visuals.footer(fig, CONTRACT_SRC, VINTAGE, "2026 baseline",
                   "pathway = conduit/panel capacity, not installed hardware")
    visuals.save(fig, OUT / "02_starter_vs_pathway.png", LOG, relative_to=REPO)


def c3_three_horizons():
    fig, ax = plt.subplots(figsize=(9.5, 6))
    visuals.style_axes(ax)
    years = [2026, 2036, 2046, 2056]
    for case, color, style in (("base", DARK_GREEN, "-"), ("high", ACCENT, "--")):
        totals = []
        for yq in years:
            q = scen[(scen.horizon_year == yq) & (scen.scenario_name == ("baseline" if yq == 2026 else case))]
            totals.append(q["ports_active"].sum())
        ax.plot(years, totals, style, marker="o", color=color, label=f"{case} adoption path")
    ax.axhline(48, color=BLACK, linewidth=1, linestyle=":", alpha=0.7)
    ax.text(2027, 48.6, "48-port pathway ceiling (saturation)", fontsize=8, color=BLACK)
    ax.set_xticks(years)
    ax.set_ylabel("Active ports (portfolio)")
    ax.set_title("Aspect 1 — ports and utilization capacity at 2036 / 2046 / 2056", fontsize=12)
    ax.legend(frameon=False)
    visuals.footer(fig, CONTRACT_SRC, VINTAGE, "V3 canonical horizons",
                   "growth multipliers provisional (uncalibrated); trigger-gated activation")
    visuals.save(fig, OUT / "03_ports_three_horizons.png", LOG, relative_to=REPO)


def c4_costs():
    fig, ax = plt.subplots(figsize=(9.5, 6))
    visuals.style_axes(ax)
    base = econ_p[econ_p.escalation_case == "base"]
    years = [2036, 2046, 2056]
    w = 3.0
    for off, case, color, label in ((-w / 2, "STG", DARK_GREEN, "Staged pilots (recommended)"),
                                    (w / 2, "OVB", "#8C2F1B", "Broad buildout now")):
        vals = [base[(base.horizon_year == y) & (base.cost_case == case)]["lifecycle_cost_npv_usd"].iloc[0] / 1e6
                for y in years]
        ax.bar([y + off for y in years], vals, width=w, color=color, label=label)
    for y in years:
        av = base[(base.horizon_year == y) & (base.cost_case == "STG")]["avoided_overbuild_cost_usd"].iloc[0] / 1e6
        top = base[(base.horizon_year == y) & (base.cost_case == "OVB")]["lifecycle_cost_npv_usd"].iloc[0] / 1e6
        ax.text(y, top + 0.06, f"avoids ${av:.2f}M", ha="center", fontsize=9, color=BLACK, fontweight="bold")
    ax.set_xticks(years)
    ax.set_ylabel("Portfolio net present cost ($M, screening)")
    ax.set_title("Aspect 2 — lifecycle cost: staged beats broad at every horizon", fontsize=12)
    ax.legend(frameon=False)
    visuals.footer(fig, CONTRACT_SRC, VINTAGE, "base escalation, 3% real discount",
                   "screening-class benchmarks — not budgets or quotes")
    visuals.save(fig, OUT / "04_lifecycle_cost.png", LOG, relative_to=REPO)


def c5_co2e():
    fig, ax = plt.subplots(figsize=(9.5, 6))
    visuals.style_axes(ax)
    years = [2026, 2036, 2046, 2056]
    for case, color in (("base", DARK_GREEN), ("high", ACCENT)):
        vals = []
        for yq in years:
            q = scen[(scen.horizon_year == yq) & (scen.scenario_name == ("baseline" if yq == 2026 else case))]
            vals.append(q["net_co2e_kg"].sum() / 1000.0)
        ax.plot(years, vals, marker="o", color=color, label=f"{case} path")
    ax.set_xticks(years)
    ax.set_ylabel("Net avoided CO2e (t/yr)")
    ax.set_title("Net avoided CO2e — grows to ≈173–260 t/yr by 2056 (screening)", fontsize=12)
    ax.legend(frameon=False)
    visuals.footer(fig, "eGRID2023 Rev 2 SRVC 596.3 lb CO2e/MWh + contract energy",
                   "factor data-year 2023, accessed 2026-07-19; refresh annually",
                   "V3 canonical horizons",
                   "9.5 kWh/session, 0.30 kWh/mi, 400 gCO2/mi displaced — benchmark assumptions")
    visuals.save(fig, OUT / "05_net_co2e.png", LOG, relative_to=REPO)


def c6_avoided_evse():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    visuals.style_axes(ax)
    years = [2026, 2036, 2046, 2056]
    vals = []
    for yq in years:
        case = "baseline" if yq == 2026 else "base"
        q = avoided[(avoided.horizon_year == yq) & (avoided["case"] == case)]
        vals.append(q["avoided_active_evse_ports"].sum())
    ax.bar(years, vals, width=4, color=MID_GREEN)
    for x, v in zip(years, vals):
        ax.text(x, v + 0.3, f"{int(v)} ports\n≈${int(v)}k/yr fees avoided", ha="center", fontsize=9)
    ax.set_xticks(years)
    ax.set_ylabel("Pathway ports not energized (base path)")
    ax.set_title("Resource management — hardware we deliberately do not install yet", fontsize=12)
    visuals.footer(fig, CONTRACT_SRC, VINTAGE, "base path",
                   "fee frame ~$1k/port/yr from client operating evidence (screening)")
    visuals.save(fig, OUT / "06_avoided_evse.png", LOG, relative_to=REPO)


def c7_peak_wait():
    df = peaks.merge(legacy_scores[["site_id", "model_rank"]], on="site_id").sort_values("model_rank").head(6)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    visuals.style_axes(ax)
    x = np.arange(len(df))
    ax.bar(x - 0.2, df["p50_wait_min"], width=0.4, color=DARK_GREEN, label="Median wait (sim)")
    ax.bar(x + 0.2, df["peak_p90_wait_min"], width=0.4, color=ACCENT, label="Peak-window P90 wait (sim)")
    ax.axhline(10, color="#8C2F1B", linestyle=":", linewidth=1)
    ax.text(len(df) - 0.5, 10.3, "10-min service target", fontsize=8, color="#8C2F1B", ha="right")
    ax.set_xticks(x, df["site_id"])
    ax.set_ylabel("Wait (minutes)")
    ax.set_title("Current demand is low — even peak-window waits sit under the target", fontsize=12)
    ax.legend(frameon=False)
    visuals.footer(fig, CONTRACT_SRC, VINTAGE, "2026 baseline, seeded discrete-event simulation (400 days)",
                   "demand synthetic/uncalibrated — screening only")
    visuals.save(fig, OUT / "07_peak_wait.png", LOG, relative_to=REPO)


def c8_limitations():
    fig, ax = plt.subplots(figsize=(9.5, 6))
    ax.axis("off")
    fig.set_facecolor(BEIGE)
    lines = [
        ("What this analysis is NOT", True),
        ("• All 12 sites score Low data confidence, none reaching Medium — every electrical value awaits confirmation", False),
        ("• Capacity is a PLACEHOLDER at 12/12 sites (no utility/facility verification yet)", False),
        ("• Demand model is synthetic and uncalibrated; growth multipliers are provisional", False),
        ("• Costs are screening-class benchmarks — not budgets, quotes, or engineering estimates", False),
        ("• No site is approved: electrical, ADA, fire, stormwater, and AHJ gates all remain", False),
        ("• Client Meeting #2 follow-up is prepared but not yet held — nothing implies endorsement", False),
        ("• No MATLAB simulation results are claimed (no licensed execution available)", False),
        ("", False),
        ("Why we show this slide", True),
        ("Honest uncertainty is the evidence discipline that makes the staged,", False),
        ("trigger-gated strategy credible: verify first, energize when data says so.", False),
    ]
    y = 0.92
    for text, is_hdr in lines:
        ax.text(0.04, y, text, fontsize=14 if is_hdr else 11.5,
                fontweight="bold" if is_hdr else "normal",
                color=DARK_GREEN if is_hdr else BLACK, transform=ax.transAxes)
        y -= 0.075
    visuals.footer(fig, CONTRACT_SRC, VINTAGE, "limitations panel", None)
    visuals.save(fig, OUT / "08_limitations.png", LOG, relative_to=REPO)


def c9_map():
    s = legacy_scores[["site_id", "site_name", "lat", "lon", "model_rank"]].copy()
    import os
    os.environ["FCF_OFFLINE"] = "1"
    from fcf_m2 import gis_offline as g
    out = g.build_site_map(s, OUT / "09_site_map_offline.png")
    # register in footer log (gis_offline stamps its own footer)
    import json
    existing = json.loads(LOG.read_text()) if LOG.exists() else []
    existing.append({"file": visuals.log_path_for(out, REPO),
                     "source": "TIGER 2024 cached + sites", "source_date": "2026-06-24"})
    LOG.write_text(json.dumps(existing, indent=2))


def combined_pdf():
    from PIL import Image
    pngs = sorted(OUT.glob("0*.png"))
    imgs = [Image.open(p).convert("RGB") for p in pngs]
    imgs[0].save(OUT / "STATIC_DASHBOARD.pdf", save_all=True, append_images=imgs[1:])
    print(f"combined PDF with {len(imgs)} pages")


for fn in (c1_ranking, c2_ports, c3_three_horizons, c4_costs, c5_co2e,
           c6_avoided_evse, c7_peak_wait, c8_limitations, c9_map):
    fn()
    print("built", fn.__name__)

combined_pdf()

problems = visuals.audit_footer_metadata(LOG, OUT)
print("footer QA problems:", problems or "NONE")
