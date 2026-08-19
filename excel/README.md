# `excel/` - grid-planning workbook

[← repository root](../README.md)

`Electric_Data_Milestone_2_Updated.xlsx` - the Milestone 2 update of the team's
grid-context workbook. What it contains:

- repaired 2024 resource-mix pie chart (the original had an empty chart);
- PWC peak-demand scenario extended 2026–2056 (2047+ rows are a **labeled CAGR
  extrapolation**, not source forecast data);
- the 6.5% PWC share and the 200/600/1,200 MW data-center selector labeled as
  planning proxy / scenario assumption;
- imported canonical scenario table (from `data/contract/v1` - no re-derivation);
- lifecycle-cost sheets (staged vs broad vs defer; low/base/high) and a portfolio
  summary computed with live SUMIFS formulas;
- net-CO2e sheet with the sourced grid factor (596.3 lb CO2e/MWh, eGRID2023 Rev 2 SRVC);
- an assumptions/source register and a **Reconciliation vs Python** sheet whose six
  live checks must all show PASS.

Rebuild: `python scripts/build_excel_workbook.py --source <path to the original
"Electric Data.xlsx">` after `make run-v3`. The original source workbook is not
tracked in this repository. Everything in this workbook is a planning scenario -
not an official forecast or budget.
