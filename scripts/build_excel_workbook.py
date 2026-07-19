"""Build excel/Electric_Data_Milestone_2_Updated.xlsx from the original workbook.

Implements Task 4: pie-chart repair, source citations, proxy labels, 2056 extension,
canonical scenario import, lifecycle-cost + CO2e sheets, staged-vs-broad comparison,
low/base/high cases, assumptions register, reconciliation checks, notices, charts.
Original workbook is never modified.
"""

import shutil
from pathlib import Path

import pandas as pd
import openpyxl
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

import argparse
_ap = argparse.ArgumentParser(description="Rebuild the updated Excel workbook from the team's source workbook (not tracked in this repo).")
_ap.add_argument("--source", required=True, help="Path to the original 'Electric Data.xlsx'")
_args = _ap.parse_args()
REPO = Path(__file__).resolve().parents[1]
SRC = Path(_args.source)
OUT = REPO / "excel/Electric_Data_Milestone_2_Updated.xlsx"

BEIGE = "F5F0E6"
GREEN = "1B4332"
NOTE_FILL = PatternFill("solid", fgColor="FFF3D6")
HDR_FONT = Font(bold=True, color=GREEN)
NOTE_FONT = Font(italic=True, size=9, color="7A5B00")
TITLE_FONT = Font(bold=True, size=13, color=GREEN)

OUT.parent.mkdir(parents=True, exist_ok=True)
shutil.copy(SRC, OUT)
wb = openpyxl.load_workbook(OUT)

dash = wb["Dashboard"]
eng = wb["Electrification Engine"]

# ---------- 1-2. Repair the empty resource-mix pie chart ----------
# remove the dead pie chart (zero series), rebuild connected to Engine data
dead = [ch for ch in dash._charts if ch.__class__.__name__ == "PieChart"]
for ch in dead:
    dash._charts.remove(ch)
pie = PieChart()
pie.title = "2024 Capacity Resource Mix by Unit Type"
data = Reference(eng, min_col=2, min_row=3, max_row=11)       # B3:B11 MW values
cats = Reference(eng, min_col=1, min_row=3, max_row=11)       # A3:A11 labels
pie.add_data(data, titles_from_data=False)
pie.set_categories(cats)
pie.height, pie.width = 8.5, 11
dash.add_chart(pie, "A5")

# ---------- 3-4-5. Source citations + proxy/assumption labels ----------
dash["A3"] = ("PLANNING SCENARIO — NOT AN OFFICIAL FORECAST. Prepared by the Future City "
              "Fellowship team for Milestone 2 (July 2026).")
dash["A3"].font = NOTE_FONT; dash["A3"].fill = NOTE_FILL
dash["J2"] = "Data-center growth term (MW):"
dash["J2"].font = NOTE_FONT
dash["J3"] = ("SCENARIO ASSUMPTION: the selected +MW value (200/600/1,200) is a flat "
              "data-center load-growth scenario input chosen by the team — not a Dominion "
              "or PJM forecast.")
dash["J3"].font = NOTE_FONT; dash["J3"].fill = NOTE_FILL
dash["A29"] = ("Sources: resource mix and unit tables — Dominion Energy Integrated Resource Plan "
               "materials as captured in workbook Table012/Fig 3.1.1.1 (2024 capacity data, "
               "accessed 2026); baseline demand projections — PJM/Dominion zone forecast extract "
               "in 'Electrification Engine' cols M:O (through 2046); 2047-2056 values are labeled "
               "extrapolation. PWC share (6.5%) is a planning proxy, not a measured allocation.")
dash["A29"].font = NOTE_FONT

t = wb["Table012 (Page 39)"]
t["A15"] = ("Source: Figure 3.1.1.1, 2024 Capacity Resource Mix by Unit Type (Dominion 2024 "
            "capacity data; vintage 2024, captured 2026). Values are the utility's published "
            "mix, not a team calculation.")
t["A15"].font = NOTE_FONT

eng["E12"] = ("PWC Summer/Winter = zone peak x 6.5% PWC PLANNING PROXY + data-center scenario "
              "term (Dashboard K2). The 6.5% share is a team planning proxy — not an official "
              "load allocation.")
eng["E12"].font = NOTE_FONT; eng["E12"].fill = NOTE_FILL

# ---------- 6. Extend model years through 2056 ----------
# Baseline zone data (cols M:O) end at 2046. Extend F/G with a labeled CAGR extrapolation.
eng["K14"] = "Extrapolation rate/yr (2041-2046 CAGR, baseline zone summer peak):"
eng["K14"].font = NOTE_FONT
eng["L14"] = "=(F35/F30)^(1/5)-1"
for i, year in enumerate(range(2047, 2057)):
    r = 36 + i
    eng[f"E{r}"] = year
    eng[f"F{r}"] = f"=F{r-1}*(1+$L$14)"
    eng[f"G{r}"] = f"=G{r-1}*(1+$L$14)"
    eng[f"H{r}"] = f"=F{r}*0.065+Dashboard!K2"
    eng[f"I{r}"] = f"=G{r}*0.065+Dashboard!K2"
eng["J13"] = ("2047-2056: EXTRAPOLATED at the 2041-2046 baseline growth rate (L14) — labeled "
              "planning extrapolation, not part of the source forecast.")
eng["J13"].font = NOTE_FONT; eng["J13"].fill = NOTE_FILL

# rebuild the dashboard bar chart extended to 2056 (fresh chart, clean styling)
for ch in [c for c in dash._charts if c.__class__.__name__ == "BarChart"]:
    dash._charts.remove(ch)
bar = BarChart()
bar.type = "col"
bar.grouping = "clustered"
bar.title = "PWC Peak Demand Scenario 2026-2056 (6.5% proxy share + DC scenario; 2047+ extrapolated)"
bar.y_axis.title = "Megawatts"
# add header labels so series get names
eng["H14"] = "PWC Summer"
eng["I14"] = "PWC Winter"
d = Reference(eng, min_col=8, max_col=9, min_row=14, max_row=45)
cats2 = Reference(eng, min_col=5, min_row=15, max_row=45)
bar.add_data(d, titles_from_data=True)
bar.set_categories(cats2)
bar.height, bar.width = 9.5, 15
dash.add_chart(bar, "J5")

# ---------- 7. Canonical scenario import ----------
scen = pd.read_csv(REPO / "data/contract/v1/scenario_table.csv")
ws = wb.create_sheet("Canonical Scenarios (M2)")
ws["A1"] = "Canonical cross-model scenario table — generated by fcf_m2 (contract v1.0.0)"
ws["A1"].font = TITLE_FONT
ws["A2"] = ("Values are imported directly from data_contract/v1/scenario_table.csv. Per the "
            "consumer rules, this sheet does not re-derive contract quantities. Capacity is a "
            "PLACEHOLDER at all 12 sites; demand is synthetic/uncalibrated; costs are "
            "screening-class estimates.")
ws["A2"].font = NOTE_FONT; ws["A2"].fill = NOTE_FILL
cols = ["site_id", "site_name", "jurisdiction", "horizon_year", "scenario_name", "ports_active",
        "ports_pathway_capacity", "sessions_per_day", "energy_required_kwh_day", "utilization",
        "average_wait_minutes", "peak_wait_minutes", "capacity_basis", "lifecycle_cost_npv_usd",
        "avoided_overbuild_cost_usd", "net_co2e_kg", "data_confidence", "equity_indicator"]
for j, c in enumerate(cols, 1):
    cell = ws.cell(row=4, column=j, value=c)
    cell.font = HDR_FONT
for i, (_, r) in enumerate(scen.iterrows(), 5):
    for j, c in enumerate(cols, 1):
        v = r[c]
        ws.cell(row=i, column=j, value=(None if pd.isna(v) else (float(v) if isinstance(v, (int, float)) else str(v))))
ws.freeze_panes = "A5"

# ---------- 8-10-11. Lifecycle cost sheets ----------
lc = pd.read_csv(REPO / "data/outputs/v3_run/lifecycle_costs.csv")
wl = wb.create_sheet("Lifecycle Costs")
wl["A1"] = "Lifecycle cost comparison — staged (STG) vs broad overbuild (OVB) vs defer (DEF)"
wl["A1"].font = TITLE_FONT
wl["A2"] = ("SCREENING/PLANNING ESTIMATES ONLY (benchmark cost classes + client operating "
            "evidence; no quotes, budgets, or engineering estimates). NPC = net present cost, "
            "real discount rate 3.0% (planning assumption). Escalation cases: low 1% / base 2.5% / high 4%.")
wl["A2"].font = NOTE_FONT; wl["A2"].fill = NOTE_FILL
hdr = ["site_id", "horizon_year", "cost_case", "escalation_case",
       "lifecycle_cost_nominal_usd", "lifecycle_cost_npv_usd", "avoided_overbuild_cost_usd"]
for j, c in enumerate(hdr, 1):
    wl.cell(row=4, column=j, value=c).font = HDR_FONT
for i, (_, r) in enumerate(lc.iterrows(), 5):
    for j, c in enumerate(hdr, 1):
        wl.cell(row=i, column=j, value=float(r[c]) if isinstance(r[c], (int, float)) else str(r[c]))
wl.freeze_panes = "A5"
n_lc = len(lc)

# Portfolio summary with FORMULAS over the detail sheet (SUMIFS)
wp = wb.create_sheet("Portfolio Cost Summary")
wp["A1"] = "Portfolio lifecycle cost (NPV USD, screening) — staged vs broad, by horizon and case"
wp["A1"].font = TITLE_FONT
wp["A2"] = ("Computed with live SUMIFS formulas over 'Lifecycle Costs'. Headline: avoided cost = "
            "NPC(OVB) - NPC(STG). PLANNING SCENARIO — NOT A BUDGET.")
wp["A2"].font = NOTE_FONT; wp["A2"].fill = NOTE_FILL
wp["A4"] = "escalation_case"; wp["B4"] = "horizon_year"
for j, cc in enumerate(["STG", "OVB", "DEF"], 3):
    wp.cell(row=4, column=j, value=f"NPC {cc} (USD)").font = HDR_FONT
wp.cell(row=4, column=6, value="Avoided cost OVB-STG (USD)").font = HDR_FONT
wp["A4"].font = HDR_FONT; wp["B4"].font = HDR_FONT
row = 5
last = 4 + n_lc
for esc in ("low", "base", "high"):
    for hy in (2036, 2046, 2056):
        wp.cell(row=row, column=1, value=esc)
        wp.cell(row=row, column=2, value=hy)
        for j, cc in enumerate(["STG", "OVB", "DEF"], 3):
            wp.cell(row=row, column=j, value=(
                f"=SUMIFS('Lifecycle Costs'!F5:F{last},'Lifecycle Costs'!B5:B{last},B{row},"
                f"'Lifecycle Costs'!C5:C{last},\"{cc}\",'Lifecycle Costs'!D5:D{last},A{row})"))
        wp.cell(row=row, column=6, value=f"=D{row}-C{row}")
        row += 1

# staged-vs-broad chart (base escalation)
chart = BarChart()
chart.title = "Staged vs broad buildout — portfolio NPC by horizon (base case, screening)"
data = Reference(wp, min_col=3, max_col=4, min_row=4, max_row=10)
cats = Reference(wp, min_col=2, min_row=8, max_row=10)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
chart.height, chart.width = 8, 14
wp.add_chart(chart, "H4")

# ---------- 9. Net CO2e sheet ----------
we = wb.create_sheet("Net CO2e")
we["A1"] = "Net avoided CO2e by horizon (portfolio, base case)"
we["A1"].font = TITLE_FONT
we["A2"] = ("Grid factor: 596.3 lb CO2e/MWh — EPA eGRID2023 Rev 2 (data year 2023, released "
            "2025-06-12), SRVC subregion, accessed 2026-07-19. Refresh annually (eGRID2024 "
            "pending). Displacement assumptions: 9.5 kWh/session, 0.30 kWh/mi EV efficiency, "
            "400 gCO2/mi displaced gasoline LDV — benchmark assumptions, labeled, uncalibrated.")
we["A2"].font = NOTE_FONT; we["A2"].fill = NOTE_FILL
we["A4"] = "Grid factor (lb CO2e/MWh)"; we["B4"] = 596.3
we["A5"] = "Factor vintage"; we["B5"] = "eGRID2023r2 SRVC, accessed 2026-07-19"
we["A4"].font = HDR_FONT; we["A5"].font = HDR_FONT
hdr = ["horizon_year", "case", "energy_delivered_MWh_yr", "net_CO2e_avoided_t_yr", "avoided_active_EVSE_ports"]
for j, c in enumerate(hdr, 1):
    we.cell(row=7, column=j, value=c).font = HDR_FONT
av = pd.read_csv(REPO / "data/outputs/v3_run/avoided_evse_metric.csv")
r0 = 8
for hy in (2026, 2036, 2046, 2056):
    for case in (["baseline"] if hy == 2026 else ["base", "high"]):
        sub = scen[(scen.horizon_year == hy) & (scen.scenario_name == case)]
        asub = av[(av.horizon_year == hy) & (av["case"] == case)]
        we.cell(row=r0, column=1, value=hy)
        we.cell(row=r0, column=2, value=case)
        we.cell(row=r0, column=3, value=round(sub["energy_delivered_kwh"].sum() / 1000.0, 1))
        we.cell(row=r0, column=4, value=round(sub["net_co2e_kg"].sum() / 1000.0, 2))
        we.cell(row=r0, column=5, value=int(asub["avoided_active_evse_ports"].sum()))
        r0 += 1
line = LineChart()
line.title = "Net avoided CO2e (t/yr) — base case (screening; factor vintage eGRID2023r2)"
data = Reference(we, min_col=4, min_row=7, max_row=r0 - 1)
cats = Reference(we, min_col=1, min_row=8, max_row=r0 - 1)
line.add_data(data, titles_from_data=True)
line.set_categories(cats)
line.height, line.width = 8, 13
we.add_chart(line, "G7")

# ---------- 12. Assumptions & source register ----------
wa = wb.create_sheet("Assumptions & Sources")
wa["A1"] = "Assumptions and source register (Milestone 2 update, 2026-07-19)"
wa["A1"].font = TITLE_FONT
rows = [
    ("Item", "Value", "Class", "Source / vintage"),
    ("PWC share of zone peak", "6.5%", "planning proxy", "team assumption; not an official allocation"),
    ("Data-center growth term", "200/600/1,200 MW selector", "scenario assumption", "team scenario; not a Dominion/PJM forecast"),
    ("Baseline zone projections", "2026-2046", "source data", "PJM/Dominion zone forecast extract (workbook cols M:O)"),
    ("2047-2056 baseline", "CAGR extrapolation (cell Engine!L14)", "labeled extrapolation", "computed in-workbook"),
    ("Resource mix", "2024 capacity mix", "source data", "Dominion Fig 3.1.1.1, vintage 2024"),
    ("Growth multipliers", "2036: 1.9/2.6 · 2046: 3.0/4.5 · 2056: 4.0/6.0 (+stress x1.15)", "provisional convention", "research Report 05; pending calibration"),
    ("Demand model", "synthetic linear, floor 0.3 sessions/day", "synthetic_uncalibrated", "V2 prototype formula; no observed sessions yet"),
    ("EVSE power", "19.2 kW AC L2", "design basis", "model config"),
    ("Energy/session", "9.5 kWh", "benchmark assumption", "AFDC-class typical L2 session; TBV"),
    ("Hardware", "$6,500/port +25% soft costs", "screening benchmark", "AFDC/NREL cost classes"),
    ("Network fee", "$1,000/port/yr", "client evidence frame", "[client contact] interview (~$1k/station/yr)"),
    ("Maintenance", "$400/port/yr", "screening benchmark", "AFDC/DOE"),
    ("Tariff", "$0.11/kWh placeholder", "placeholder", "Dominion tariff TBV; demand charges not modeled without tariff"),
    ("Discount rate", "3.0% real", "planning assumption", "OMB A-94-style real rate class"),
    ("Escalation", "1% / 2.5% / 4% (low/base/high)", "screening cases", "team convention"),
    ("Grid factor", "596.3 lb CO2e/MWh", "sourced", "EPA eGRID2023 Rev 2, SRVC, accessed 2026-07-19; refresh annually"),
    ("EV efficiency", "0.30 kWh/mi", "benchmark assumption", "EPA-class LDV benchmark"),
    ("Displaced vehicle", "400 gCO2/mi", "benchmark assumption", "EPA fleet-average-class benchmark"),
    ("Capacity at all 12 sites", "PLACEHOLDER (unverified)", "placeholder", "utility/facility confirmation pending"),
    ("Data confidence", "0 of 12 sites High", "model output", "structured provenance scoring (V3)"),
    ("FY2027 budgets", "Fairfax City ≈$207.5M GF; PWC ≈$1.955B GF revenues", "sourced", "adopted budgets 2026-05-05 / 2026-04-21"),
]
for i, row_vals in enumerate(rows, 3):
    for j, v in enumerate(row_vals, 1):
        c = wa.cell(row=i, column=j, value=v)
        if i == 3:
            c.font = HDR_FONT
wa.column_dimensions["A"].width = 28
wa.column_dimensions["B"].width = 40
wa.column_dimensions["C"].width = 24
wa.column_dimensions["D"].width = 60

# ---------- 13. Reconciliation checks ----------
wr = wb.create_sheet("Reconciliation vs Python")
wr["A1"] = "Cross-model reconciliation checks (live formulas)"
wr["A1"].font = TITLE_FONT
wr["A2"] = "Every check must show PASS. Values on the left are computed from this workbook's imported sheets; expectations from the Python contract."
wr["A2"].font = NOTE_FONT
n_scen = len(scen)
last_s = 4 + n_scen
checks = [
    ("2026 baseline starter ports", f"=SUMIFS('Canonical Scenarios (M2)'!F5:F{last_s},'Canonical Scenarios (M2)'!D5:D{last_s},2026,'Canonical Scenarios (M2)'!E5:E{last_s},\"baseline\")", 25),
    ("2026 pathway ports", f"=SUMIFS('Canonical Scenarios (M2)'!G5:G{last_s},'Canonical Scenarios (M2)'!D5:D{last_s},2026,'Canonical Scenarios (M2)'!E5:E{last_s},\"baseline\")", 48),
    ("Scenario rows", f"=COUNTA('Canonical Scenarios (M2)'!A5:A{last_s})", n_scen),
    ("Sites", f"=SUMPRODUCT(1/COUNTIF('Canonical Scenarios (M2)'!A5:A{last_s},'Canonical Scenarios (M2)'!A5:A{last_s}))", 12),
    ("STG NPV 2056 base (portfolio)", "='Portfolio Cost Summary'!C10",
     round(lc[(lc.horizon_year == 2056) & (lc.cost_case == "STG") & (lc.escalation_case == "base")]["lifecycle_cost_npv_usd"].sum(), 0)),
    ("Avoided cost 2056 base > 0", "='Portfolio Cost Summary'!F10>0", True),
]
wr["A4"] = "Check"; wr["B4"] = "Workbook value"; wr["C4"] = "Python/contract expectation"; wr["D4"] = "Status"
for c in ("A4", "B4", "C4", "D4"):
    wr[c].font = HDR_FONT
for i, (name, formula, expect) in enumerate(checks, 5):
    wr.cell(row=i, column=1, value=name)
    wr.cell(row=i, column=2, value=formula)
    wr.cell(row=i, column=3, value=expect if not isinstance(expect, bool) else str(expect))
    if isinstance(expect, bool):
        wr.cell(row=i, column=4, value=f'=IF(B{i}=TRUE,"PASS","FAIL")')
    else:
        wr.cell(row=i, column=4, value=f'=IF(ABS(B{i}-C{i})<1,"PASS","FAIL")')
wr.column_dimensions["A"].width = 34

for sheet in wb.worksheets:
    sheet.sheet_view.showGridLines = True

wb.save(OUT)
print("saved", OUT)
