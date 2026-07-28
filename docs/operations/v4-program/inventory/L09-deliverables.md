# LANE L09 — DASHBOARD, EXCEL, PRESENTATION, REPORTS (text content)

**Lane ID:** L09-deliverables
**Repo root for all relative paths below:** `/Users/andyyaro/Downloads/Future-City-Fellowship-MapUpdate/repo`
**Branch:** `v4-platform` (HEAD). Remote branches present: `main`, `archive/pre-milestone2-v3-20260719`, `milestone2-v3-professional-release`, `v2-expansion-planning`. Tags: `pre-milestone2-v3-20260719`, `pre-v4-program-20260727`, `v1-demo-scalability-ready`, `v1-review-ready`.
**Read discipline:** every assigned text file was read end-to-end with `Read` (no `limit`). The two large CSVs (`tbl_canonical_scenarios.csv`, `tbl_avoided_evse.csv`) were read in full — `tbl_avoided_evse.csv` line-by-line via Read (122 lines), `tbl_canonical_scenarios.csv` (121 lines × 48 cols, 100 KB) was consumed programmatically column-by-column and row-aggregated rather than eyeballed; every column's full distinct-value set was enumerated and is reproduced below. Binary assets in scope-adjacent directories (`.pptx`, `.pdf`, `.docx`, `.png`, `.xlsx`) were **not** in this lane's read list; where I inspected one (the xlsx sheet list) it is labelled as such.

---

## PART A — PER-FILE INVENTORY

### dashboard/README.md
- **Role:** Directory-level orientation for the two dashboard tracks — the guaranteed-offline static dashboard and the Tableau patch package.
- **Kind:** authored
- **Reads:** n/a (prose). Names `footer_log.json`, `verify.sh`, `make run-v3`, `scripts/build_static_dashboard.py`.
- **Written by / read by:** Human-authored; linked from repo-root `README.md` and from `presentation/README.md` line 15.
- **Key contents:** 23 lines. "Nine contract-derived visuals + `STATIC_DASHBOARD.pdf`" (L7); "`footer_log.json` is the audit trail; verify.sh fails if any chart lacks a footer entry" (L8-9); "the team's chosen demo strategy is static visuals, deliberately independent of live software, networks, or logins" (L10-11); rebuild command `make run-v3 && python scripts/build_static_dashboard.py` (L13); "A verified `.twbx` could not be produced (no Tableau Desktop available; Tableau Public was rejected because it can only save to its public cloud)" (L17-19); "six contract-derived CSVs, and an exact worksheet/dashboard/story build recipe" (L19-20); "Nothing here claims a verified workbook." (L22).
- **Notes:** (a) `verify.sh` named at L8 does **not** exist at repo root — the actual file is `scripts/verify.sh` (73 lines). The claim itself is TRUE: `scripts/verify.sh` L49-53 runs a gate `"dashboard: static assets present + every chart footer-logged"` that asserts `ls dashboard/static/0*.png | wc -l -eq 9` and calls `fcf_m2.visuals.audit_footer_metadata('dashboard/static/footer_log.json','dashboard/static')`. Only the path is imprecise. (b) The relative link at L21 `tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md` resolves correctly. (c) `[← repository root](../../../../README.md)` resolves correctly.

### dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md
- **Role:** The honest blocker note explaining why no `.twbx` exists, plus the complete Tableau Desktop build recipe.
- **Kind:** authored (data-contract-adjacent: it is the spec Phase 6 must satisfy or honestly retire)
- **Reads:** n/a. Specifies six CSV inputs in `patch_package/`.
- **Written by / read by:** Linked from `dashboard/README.md` L21; referenced by `reports/.../Final_Report.md` L121 ("Full blocker note, contract-derived patch CSVs, and an exact build recipe in `dashboard/tableau/`").
- **Key contents:** **QUOTED IN FULL IN PART D BELOW** (Phase 6 requirement).
- **Notes:** Status date `2026-07-19`. Claims the original legacy workbook `EV_Charging_Site_Readiness_Workbook.twbx` "lives in the pre-V3 archive branch (`archive/pre-milestone2-v3-20260719`), not in this tree" — **VERIFIED**: no `.twbx` exists anywhere in this tree, and `remotes/origin/archive/pre-milestone2-v3-20260719` does exist. The recipe's target filename is `EV_Charging_Site_Readiness_M2_Final.twbx`. Cites the research score "static visuals, 86.4/100" (L23) — a headline number with no contract trace. Contains `596.3` at L43. Recipe internal inconsistencies and capability-boundary conflicts enumerated in Part E.

### dashboard/static/footer_log.json
- **Role:** Audit trail asserting that each of the nine static-dashboard PNGs carries a source / vintage / assumption footer.
- **Kind:** generated (by `scripts/build_static_dashboard.py`, consumed by `fcf_m2.visuals.audit_footer_metadata`)
- **Reads:** n/a (it is data).
- **Written by / read by:** Written by the static-dashboard builder; read by `scripts/verify.sh` L49-53 → `audit_footer_metadata(log_path, chart_dir)` in `src/fcf_m2/visuals.py` L71-81, which matches on `Path(e["file"]).name` (basename only).
- **Key contents:** JSON array, 9 objects, 63 lines. Eight objects have keys `source`, `source_date`, `scenario`, `assumption`, `file`; the ninth (L58-62, `09_site_map_offline.png`) has only `file`, `source` (`"TIGER 2024 cached + sites"`), `source_date` (`"2026-06-24"`) — no `scenario`, no `assumption`. Repeated source string: `"canonical contract v1.0.0 (fcf_m2 V3 run 2026-07-19)"`; repeated source_date `"inputs 2026-06-24; eGRID2023r2; verified 2026-07-19"`. Entry 1 scenario = `"legacy_v2 baseline scores"`, assumption `"0 of 12 sites have High data confidence"`. Entry 2 scenario `"2026 baseline"`, assumption `"pathway = conduit/panel capacity, not installed hardware"`. Entry 3 scenario `"V3 canonical horizons"`, assumption `"growth multipliers provisional (uncalibrated); trigger-gated activation"`. Entry 4 scenario `"base escalation, 3% real discount"`, assumption `"screening-class benchmarks — not budgets or quotes"`. Entry 5 (L31) source `"eGRID2023 Rev 2 SRVC 596.3 lb CO2e/MWh + contract energy"`, source_date `"factor data-year 2023, accessed 2026-07-19; refresh annually"`, assumption `"9.5 kWh/session, 0.30 kWh/mi, 400 gCO2/mi displaced — benchmark assumptions"`. Entry 6 assumption `"fee frame ~$1k/port/yr from client operating evidence (screening)"`. Entry 7 scenario `"2026 baseline, seeded discrete-event simulation (400 days)"`, assumption `"demand synthetic/uncalibrated — screening only"`. Entry 8 scenario `"limitations panel"`, assumption `""` (empty string).
- **Notes:** **Every one of the nine `file` values is an absolute path on a machine that is not this repo**: `/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/<name>.png`. The audit passes anyway because `audit_footer_metadata` takes only `.name`, so this is stale leakage rather than a functional break — but it leaks a local user path and a directory name (`visuals/static_dashboard`) that no longer exists. Entry 1's scenario is `legacy_v2 baseline scores` — this is a *correctly labelled* legacy reference. Entry 9's missing `assumption`/`scenario` keys break the otherwise-uniform schema.

### dashboard/tableau/patch_package/tbl_sites_dimension.csv
- **Role:** Site dimension table (identity, geography, type) for the Tableau build.
- **Kind:** generated — **byte-identical copy** of `data/contract/v1/site_table.csv` (md5 `92f19e6b6ad33e979fbf2869d856a771` for both; `diff` returns no differences).
- **Reads:** n/a.
- **Written by / read by:** Produced by the contract generator; consumed by Tableau worksheet 7 (map) and as the join key source (`site_id`).
- **Key contents:** 12 data rows, 9 columns, ordered: `site_id, site_name_display, site_name_safe, jurisdiction, lat, lon, site_type, public_access, garage_enclosed`. Values: `site_id` ∈ {FFX001–FFX004, PWC001–PWC008}; `jurisdiction` ∈ {`fairfax` (4), `pwc` (8)}; `site_type` ∈ {`office` (3), `library` (7), `garage` (1), `public_safety` (1)}; `public_access` = 1.0 for 11 sites, **0.0 for PWC003** (Prince William County Public Safety Training Center); `garage_enclosed` = 1.0 **only for PWC002** (Neabsco-Potomac Commuter Garage), 0.0 elsewhere. Latitudes 38.63–38.86, longitudes −77.27 to −77.63 (Northern Virginia). `site_name_safe` is the display name with spaces→underscores.
- **Notes:** Row order is by model rank, not alphabetical (FFX004, FFX002, PWC002, PWC006, PWC007, FFX001, PWC004, PWC001, FFX003, PWC008, PWC005, PWC003) — this is the *2026-baseline port-allocation* order, not the readiness rank order in `tbl_readiness_confidence.csv` (which is FFX002, FFX004, PWC006, FFX001, PWC002, …). Corroborates RISK_REGISTER R08 ("only PWC002 Neabsco among 12"; "11/12 are surface"). Trailing newline present (file ends line 14 empty).

### dashboard/tableau/patch_package/tbl_readiness_confidence.csv
- **Role:** Per-site readiness score, subscores, tier, and V3 typed data confidence — feeds Tableau worksheet 1.
- **Kind:** generated (V3 run); no identical twin in `data/contract/v1/`.
- **Reads:** n/a.
- **Written by / read by:** Produced by the V3 model; consumed by Tableau worksheet 1 and by static visual `01_readiness_ranking.png`.
- **Key contents:** 12 data rows, 12 columns, ordered: `site_id, site_name, model_rank, readiness_score, demand_subscore, feasibility_subscore, safety_subscore, equity_subscore, recommendation_tier, data_confidence_score_v3, data_confidence_level_v3, confidence_breakdown`. Ranks 1–12 with scores: FFX002 **58.8**, FFX004 **54.4**, PWC006 **52.1**, FFX001 51.0, PWC002 50.3, PWC007 50.2, PWC004 48.6, FFX003 46.8, PWC008 40.1, PWC001 39.8, PWC005 36.9, PWC003 29.6. `safety_subscore` = 90.0 for 11 sites, **75.0 for PWC002**. `equity_subscore` spans 0.0 (PWC008) to 100.0 (PWC002). `recommendation_tier` ∈ {`Tier 1 — advance to site screening` (FFX002, FFX004), `Tier 2 — promising candidate, refine data` (PWC006, FFX001, PWC007, PWC004, FFX003), `High-review candidate` (PWC002), `Tier 3 — lower priority / monitor` (PWC008, PWC001, PWC005), `Low public-priority / special-use` (PWC003)}. **`data_confidence_score_v3` = 33.8 and `data_confidence_level_v3` = `Low` for ALL 12 sites, with an identical `confidence_breakdown` string on every row**: `electrical_service=0.0; site_use_and_demand=55.0; address_and_public_access=90.0; coordinates=60.0; parking_and_layout=35.0; safety_review_fields=0.0; equity_and_context=55.0`.
- **Notes:** Two consequences. (1) The Tableau recipe's worksheet 1 says "color by `data_confidence_level_v3`" — with a single distinct value this produces a **monochrome** chart, and the caption "0 of 12 sites High confidence" is true but the colour encoding carries zero information. (2) `FFX002 = Low` here **directly contradicts** the deck, the Final Report L51 and root `README.md` L47, all of which say "FFX002 … 58.8 (**Medium** confidence)". See Finding F-02.

### dashboard/tableau/patch_package/tbl_portfolio_costs.csv
- **Role:** Portfolio-level lifecycle cost by horizon × cost case × escalation case — feeds Tableau worksheet 4 and static visual `04_lifecycle_cost.png`.
- **Kind:** generated (V3 economics module; sibling of `data/outputs/v3_run/lifecycle_costs.csv`)
- **Reads:** n/a.
- **Written by / read by:** Produced by the V3 economics layer; consumed by Tableau worksheet 4; the same three base-case NPV pairs are the headline table in the Final Report, root README, speaker notes and runbook.
- **Key contents:** 27 data rows (3 horizons × 3 cost cases × 3 escalation cases), 8 columns ordered: `horizon_year, cost_case, escalation_case, lifecycle_cost_nominal_usd, lifecycle_cost_npv_usd, avoided_overbuild_cost_usd, avoided_overbuild_cost_nominal_usd, estimate_class`. `horizon_year` ∈ {2036, 2046, 2056} — **no 2026 row**. `cost_case` ∈ {`DEF` (defer), `OVB` (overbuild/broad), `STG` (staged)}. `escalation_case` ∈ {`base`, `high`, `low`}. `estimate_class` = `screening_planning_estimate` on all 27 rows. DEF is constant at 617,403 nominal = 617,403 NPV in all 9 DEF rows (a flat, non-discounted, non-escalated figure — worth a Phase 1 sanity check). Base-case headline triple: 2036 STG NPV **1,560,499** / OVB NPV **1,872,578** / avoided **312,079**; 2046 STG **2,294,469** / OVB **2,635,638** / avoided **341,169**; 2056 STG **3,014,200** / OVB **3,407,606** / avoided **393,406**. Arithmetic checks out exactly: avoided = OVB NPV − STG NPV in all three. Extremes: 2056 OVB high nominal 6,072,548; 2036 STG low NPV 1,495,233.
- **Notes:** The published headline "$1.56M / $1.87M / $0.31M" etc. **traces cleanly** to these rows. Avoided cost is monotone increasing in all three escalation cases at all three horizons, supporting the Final Report L86 claim "the staged plan costs less than broad buildout at every horizon under every escalation case" — **VERIFIED TRUE** from this file (STG NPV < OVB NPV in all 9 base/high/low × horizon combinations).

### dashboard/tableau/patch_package/tbl_peak_waits.csv
- **Role:** Per-site simulated wait statistics for the 2026 baseline — feeds Tableau worksheet 6 and static visual `07_peak_wait.png`.
- **Kind:** generated (seeded discrete-event simulation, seed `20260719`)
- **Reads:** n/a.
- **Written by / read by:** Produced by the V3 wait model; consumed by Tableau worksheet 6.
- **Key contents:** 12 data rows, 10 columns ordered: `site_id, ports, mean_wait_min, p10_wait_min, p50_wait_min, p90_wait_min, peak_p90_wait_min, peak_erlang_wait_min, sim_utilization, seed`. `ports` = 2 for 11 sites, **3 for FFX004**. `seed` = 20260719 on every row. `sim_utilization` 0.0626 (FFX003) – 0.1961 (FFX004). `peak_erlang_wait_min` 0.381 (PWC005) – **42.365 (PWC002)**; all others < 2.2 min. `mean_wait_min` 0.069 (FFX003) – **8.020 (PWC002)**. Values are carried at full float precision (17 significant digits).
- **Notes:** **`p10_wait_min`, `p50_wait_min`, `p90_wait_min` and `peak_p90_wait_min` are `0.0` for all 12 sites, without exception.** The Tableau recipe's worksheet 6 is specified as "bar, **p50 vs peak P90 wait**, top-6 sites; reference line 10 min" — built exactly as specified this renders **twelve zero-height bars** below a 10-minute reference line. The only non-degenerate wait columns in this file are `mean_wait_min` and `peak_erlang_wait_min`. Separately, PWC002's `peak_erlang_wait_min` of 42.37 min is 4× the stated 10-minute target. See Findings F-05 and F-06.

### dashboard/tableau/patch_package/tbl_avoided_evse.csv
- **Role:** Per-site × horizon × case count of pathway ports deliberately NOT energized, and the avoided annual network/maintenance fee — feeds Tableau and static visual `06_avoided_evse.png`.
- **Kind:** generated (V3 resource-management metric; sibling of `data/outputs/v3_run/avoided_evse_metric.csv`)
- **Reads:** n/a.
- **Written by / read by:** Produced by the V3 model; consumed by the avoided-EVSE visual and the "avoided-overbuild story" narrative (speaker notes slide 14).
- **Key contents:** 120 data rows (12 sites × 10 site-horizon-case combinations), 6 columns ordered: `site_id, horizon_year, case, avoided_active_evse_ports, avoided_network_fee_usd_yr, avoided_evse_note`. `case` ∈ {`baseline` (2026 only), `base`, `high`, `stress_combined` (2036/2046/2056)}. `avoided_network_fee_usd_yr` = `avoided_active_evse_ports × 1000.0` exactly, on every row. `avoided_evse_note` is one identical sentence on all 120 rows: *"Ports kept as pathway-only capacity instead of energized hardware; avoided annual network/maintenance fees use the client's ~$1k/station/yr operating frame (screening)."* Non-zero values only: FFX002 (6 at 2026-baseline; 4/2/2 at 2036 base/high/stress; 2/0/0 at 2046; 2/0/0 at 2056), FFX004 (5; 4/2/2; 2/0/0; 2/0/0), PWC006 (2 then all 0), FFX001 (2 then all 0), PWC002 (1 then all 0), PWC007 (2 then all 0), PWC004 (2; 2/0/0; then 0), FFX003 (2; 2/0/0; then 0), PWC001 (1; 1/0/0; then 0). PWC008, PWC005, PWC003 are 0 everywhere.
- **Notes:** Portfolio sums by horizon on the **base path**: 2026 = **23**, 2036 = **13**, 2046 = **4**, 2056 = **4**. 25 active + 23 avoided = 48 pathway at 2026 ✓. But 2036 base: 35 active + 13 avoided = 48 ✓ — which pins the contract's 2036 base active-port total at **35**, not the 44 the reports publish. The Final Report's "13–23 pathway ports deliberately not energized on the base path" (L86) therefore quotes only the 2026 and 2036 endpoints and silently drops the 2046/2056 value of 4. See Findings F-01 and F-04.

### dashboard/tableau/patch_package/tbl_canonical_scenarios.csv
- **Role:** The full canonical scenario table (site × horizon × case) shipped into the Tableau patch package.
- **Kind:** generated — **byte-identical copy** of `data/contract/v1/scenario_table.csv`. Both files md5 `2beff3f46e8f86b43427d47b7e8efab6`, both 100,363 bytes; `diff` returns nothing. **It is a full copy, not a subset and not divergent.**
- **Reads:** n/a.
- **Written by / read by:** Python contract generator (`fcf_m2`) produces it under `data/contract/v1/`; the copy here is consumed by Tableau worksheets 2, 3, 5, and referenced by the recipe's acceptance criterion.
- **Key contents:** 120 data rows, **48 columns**. Full ordered column list:
  `contract_version, run_id, generated_at, site_id, site_name, jurisdiction, site_type, public_or_fleet, horizon_year, horizon_label, scenario_id, scenario_name, model_mode, ports_active, ports_pathway_capacity, evse_power_kw, sessions_per_day, energy_per_session_kwh, energy_required_kwh_day, charging_window_hr, average_dwell_hr, peak_factor, utilization, average_wait_minutes, peak_wait_minutes, base_load_kw, service_capacity_kw, spare_capacity_kw, capacity_basis, capacity_source, capacity_confidence, managed_charging_policy, energy_delivered_kwh, energy_curtailed_kwh, lifecycle_cost_nominal_usd, lifecycle_cost_npv_usd, avoided_overbuild_cost_usd, grid_factor_value, grid_factor_units, grid_factor_vintage, net_co2e_kg, data_confidence, equity_indicator, expansion_trigger_status, source_date, source_id, assumption_flag, notes`
  Constant-valued columns (single distinct value across all 120 rows): `contract_version` = `1.0.0`; `run_id` = `milestone2_v3_20260719T052322Z`; `generated_at` = `2026-07-19T05:23:22.201169+00:00`; `model_mode` = `milestone2_v3`; `evse_power_kw` = `19.2`; `energy_per_session_kwh` = `9.5`; `capacity_basis` = `placeholder`; `capacity_source` = `legacy adapter future-ready placeholder; utility/facility confirmation pending (12/12 sites unconfirmed)`; `capacity_confidence` = `none`; `managed_charging_policy` = `none`; `energy_curtailed_kwh` = `0.0`; `grid_factor_value` = **`596.3`** (all 120 rows); `grid_factor_units` = `lb CO2e/MWh`; `grid_factor_vintage` = `eGRID2023r2, accessed 2026-07-19`; `data_confidence` = **`Low`** (all 120 rows); `expansion_trigger_status` = `awaiting_observed_data (proposed policy, not adopted)`; `source_date` = `2026-06-24`; `source_id` = `real_sites_v2+frozen_v2_outputs+anchors_v1`; `assumption_flag` = `growth multipliers provisional; demand synthetic_uncalibrated; capacity placeholder; costs screening-class; emissions benchmark assumptions`.
  **Entirely empty columns:** `service_capacity_kw` and `spare_capacity_kw` — 120/120 blank (consistent with `capacity_basis=placeholder`).
  Low-cardinality columns: `horizon_year` ∈ {2026, 2036, 2046, 2056}; **`horizon_label` ∈ {`now`, `plus10`, `plus20`, `plus30`}**; `scenario_name` ∈ {`baseline`, `base`, `high`, `stress_combined`}; `jurisdiction` ∈ {fairfax, pwc}; `site_type` ∈ {garage, library, office, public_safety}; `public_or_fleet` ∈ {public, mixed}; `ports_active` ∈ {2,3,4,6,8}; `ports_pathway_capacity` ∈ {2,3,4,8}; `charging_window_hr` ∈ {4.0, 7.0, 8.0}; `average_dwell_hr` ∈ {1.5, 2.0, 3.0, 4.0}; `peak_factor` ∈ {1.002375, 1.08075, 1.1, 1.277375, 3.3000000000000003}; `equity_indicator` = 12 distinct values 0.191–0.769 (one per site); `notes` = 7 distinct recommendation sentences.
  Continuous ranges: `utilization` 0.0563–0.658 (max 65.8%); `average_wait_minutes` 0.0–68.72; `peak_wait_minutes` 0.0–215.35 with **5 blank cells** (`PWC002_2046_high`, `PWC002_2046_stress_combined`, `PWC002_2056_base`, `PWC002_2056_high`, `PWC002_2056_stress_combined`); `lifecycle_cost_*` blank on the 12 `2026_baseline` rows.
  **Portfolio aggregates I computed (these are the ground truth for Phase 1):**

  | horizon | case | Σ ports_active | Σ ports_pathway | Σ net_co2e (t) | Σ NPV ($) | Σ nominal ($) | Σ avoided ($) |
  |---|---|---:|---:|---:|---:|---:|---:|
  | 2026 | baseline | **25** | 48 | **43.4** | — | — | — |
  | 2036 | base | **35** | 48 | **82.4** | 1,560,499 | 1,716,833 | 312,079 |
  | 2036 | high | **44** | 48 | **112.7** | 1,560,499 | 1,716,833 | 312,079 |
  | 2036 | stress_combined | 44 | 48 | 129.6 | 1,560,499 | 1,716,833 | 312,079 |
  | 2046 | base | **44** | 48 | **130.1** | 2,294,469 | 2,900,157 | 341,169 |
  | 2046 | high | **48** | 48 | **195.1** | 2,294,469 | 2,900,157 | 341,169 |
  | 2046 | stress_combined | 48 | 48 | 224.4 | 2,294,469 | 2,900,157 | 341,169 |
  | 2056 | base | **44** | 48 | **173.4** | 3,014,200 | 4,435,354 | 393,406 |
  | 2056 | high | **48** | 48 | **260.2** | 3,014,200 | 4,435,354 | 393,406 |
  | 2056 | stress_combined | 48 | 48 | 299.2 | 3,014,200 | 4,435,354 | 393,406 |

- **Notes:** Three things matter here. (1) The **CO2e** headline series (≈43 / 82→113 / 130→195 / 173→260 t/yr) **traces exactly** to this file. (2) The **cost** headline series traces exactly. (3) The **port** headline series does **not** — the published base path is `25 → 44 → 47 → 47` and the published high path is `25 → 47 → 48 → 48`, whereas this file gives base `25 → 35 → 44 → 44` and high `25 → 44 → 48 → 48`. The value **47 never occurs** as a portfolio total anywhere in the contract. See Finding F-01. (4) Lifecycle cost columns are **replicated identically across base/high/stress within a horizon** — i.e. the per-scenario cost columns carry the portfolio STG-base value, not a scenario-specific cost; anyone summing `lifecycle_cost_npv_usd` across the whole table would triple-count. (5) `horizon_label` ships `now`/`plus10`/`plus20`/`plus30` in `model_mode=milestone2_v3` rows — see Finding F-03.

### excel/README.md
- **Role:** Explains what the Milestone 2 grid-planning workbook contains and how to rebuild it.
- **Kind:** authored
- **Reads:** n/a. Names `excel/Electric_Data_Milestone_2_Updated.xlsx`, `data/contract/v1`, `scripts/build_excel_workbook.py`, `make run-v3`.
- **Written by / read by:** Linked from repo-root README; the workbook it describes is `excel/Electric_Data_Milestone_2_Updated.xlsx` (56,112 bytes).
- **Key contents:** 24 lines. Claims: repaired 2024 resource-mix pie chart ("the original had an empty chart"); "PWC peak-demand scenario extended **2026–2056** (**2047+ rows are a labeled CAGR extrapolation**, not source forecast data)" (L10-11); "the **6.5%** PWC share and the **200/600/1,200 MW** data-center selector labeled as planning proxy / scenario assumption" (L12-13); "imported canonical scenario table (from `data/contract/v1` — no re-derivation)" (L14); lifecycle-cost sheets (staged vs broad vs defer; low/base/high) with "live SUMIFS formulas"; "net-CO2e sheet with the sourced grid factor (**596.3 lb CO2e/MWh**, eGRID2023 Rev 2 SRVC)" (L16); "a **Reconciliation vs Python** sheet whose **six live checks must all show PASS**" (L18); rebuild `python scripts/build_excel_workbook.py --source <path to the original "Electric Data.xlsx">` after `make run-v3`; "The original source workbook is not tracked in this repository." (L21-22); "Everything in this workbook is a planning scenario — not an official forecast or budget." (L23).
- **Notes:** `scripts/build_excel_workbook.py` exists ✓. I opened the `.xlsx` container (not a lane read-assignment, flagged as such): sheet names are **Dashboard, Table012 (Page 39), Electrification Engine, Canonical Scenarios (M2), Lifecycle Costs, Portfolio Cost Summary, Net CO2e, Assumptions & Sources, Reconciliation vs Python** — nine sheets, consistent with the README's description, and four embedded charts (`xl/charts/chart1..4.xml`). The workbook has no `sharedStrings.xml` (all strings inline), so I did not verify PASS/FAIL cell values; the "six live checks all PASS" claim is **unverified in this lane**.

### presentation/README.md
- **Role:** Orientation for the Milestone 2 presentation package.
- **Kind:** authored
- **Reads:** n/a. Names four deck artifacts and `presentation/assets/`.
- **Written by / read by:** Linked from repo-root README; links out to `../dashboard/README.md`.
- **Key contents:** 22 lines. Deck = "**17-slide** final deck (**13-beat** story; every slide rendered and inspected)"; speaker notes = "Per-slide **30–60 s** talking points"; runbook = "Per-slide budget summing to **13:00**". "`assets/` Presentation-specific graphics (the provisional-MCDA chart). **The nine shared data visuals live in [`dashboard/static/`](../../../../dashboard/README.md) — single source, no duplicates.**" (L13-16). Rules: "static visuals only (no live demo), placeholder-capacity captions on every capacity slide, source/vintage footers on every data slide, peer question on the closing slide, Paula's speaking role left as an editable table (deliberately unassigned — a team decision, not the model's)." (L17-21).
- **Notes:** `presentation/assets/` contains exactly one file, `10_mcda_provisional.png` (162,772 bytes) — consistent with "the provisional-MCDA chart". **The "no duplicates / single source" statement is contradicted by the timing runbook L62+L65 and by the Final Report L124** — see Finding F-07.

### presentation/deck/Future_City_Fellowship_Milestone_2_Speaker_Notes.md
- **Role:** Per-slide talking points plus the claims-discipline reminders and the editable speaker-assignment table.
- **Kind:** authored
- **Reads:** n/a.
- **Written by / read by:** Mirrors slide 17 of the `.pptx`; referenced by `presentation/README.md` L9 and by the Final Report L124.
- **Key contents:** 132 lines. Header: deck `.pptx`, **17 slides, 16:9**, Date **2026-07-21**, Target **≤ 13:00**. Claims-discipline block L8-14 (quoted verbatim in Part D). Slide-by-slide: S1 Anna ~0:15; S2 Anna ~0:45 ("which of 12 sites, how many ports, what staging logic, **over 2036/2046/2056**"); S3 Laylas ~0:55 ([client contact] PWC; McCoart trenching; **Neabsco: 70 ports, 17 stations later offline, ~$1,000/station/yr**; **~35-station county fleet hub**; [fire-service interviewee] Fire/HazMat "no local EV fires yet"); S4 Laylas ~0:40 (CM2 honest status); S5 Adama ~0:55 (seven alternatives); S6 Adama ~0:50 (**B: 85/100; F hybrid: 81**; "at roughly **double the equity weight**, F overtakes B"); S7 Andy ~0:55 (six workflow steps; pilot **2–3 ports**; gates); S8 Andy ~0:50 (**FFX002 … 58.8 (Medium confidence); FFX004 54.4; PWC006 52.1**; **0 of 12 sites reach High data confidence; 38 REVIEW + 12 INFO findings**; "The 'Low' labels are printed on the chart deliberately."); S9 Andy ~0:40 (**25 starter ports** inside a **48-port** pathway; top-3 highlighted); S10 Adama ~0:55 (**ports 25 → 44 → 47 → 47 base; 25 → 47 → 48 → 48 high**; **staged NPC $1.56M / $2.29M / $3.01M vs broad $1.87M / $2.64M / $3.41M**; **avoids $0.31M / $0.34M / $0.39M**; **≈43 t/yr now to ≈173–260 t/yr by 2056**); S11 Adama ~0:35; S12 Laylas ~0:55 (**UL 2594 3rd ed. 2022; UL 3600 2023**; **2020 NEC via 2021 VA USBC, effective 2024-01-18**; Access Board still NPRM; **three modules**); S13 Andy ~0:50; S14 Anna ~0:55 (**≈173–260 t/yr by 2056**; **eGRID2023 Rev 2 SRVC, 596.3 lb CO2e/MWh, accessed 2026-07-19**; **Dominion L2 — 50% upfront make-ready, 100% in disadvantaged communities**); S15 Laylas ~0:50 ("0 of 12 sites High confidence" verbatim); S16 Anna ~0:50 (peer question; four immediate actions; pilot ask **2–3 starter ports at FFX002 / FFX004 / PWC006**); S17 Anna ~0:25. Speaker table L123-129: Anna ~3:10, Laylas ~3:20, Adama ~3:15, Andy ~3:15, **Paula = "TO BE ASSIGNED BY THE TEAM"**.
- **Notes:** Slide 12 says the proposed standard has "**three modules**" — the Final Report L105 and Gap Closure C7 both say "**seven test modules**". Internal contradiction (Finding F-09). Slide 8 says FFX002 is "Medium confidence" (Finding F-02). L131 handoff phrase "Adama has the **30-year** numbers" is an uncontextualised 10/20/30 formulation (Finding F-03b). L76 "≈43 t/yr **now**" uses the informal "now" for the 2026 baseline. Speaker times sum: 3:10+3:20+3:15+3:15 = 13:00 with Paula unassigned — i.e. the budget has **no slack allocated to Paula**, so assigning her a slide necessarily re-balances (the runbook L45 acknowledges this).

### presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md
- **Role:** Per-slide time budget, rehearsal checkpoints, fallback cuts, and the offline-open QA checklist.
- **Kind:** authored
- **Reads:** n/a. Names `Future_City_Fellowship_Milestone_2_Final.pptx/.pdf`, `..._QA_Backup.pdf`, `static_visuals/`, `09_site_map_offline.png`.
- **Written by / read by:** Referenced by `presentation/README.md` L10 and the Final Report L124 ("≤13-minute timing runbook").
- **Key contents:** 69 lines. Presentation **2026-07-21**; hard target **≤13:00**; rehearsal target **12:15** ("leaves ~45 s of real-world slack"). Per-slide budget table L10-26 summing to exactly 13:00 (0:15, 0:45, 0:55, 0:40, 0:55, 0:50, 0:55, 0:50, 0:40, 0:55, 0:35, 0:55, 0:50, 0:55, 0:50, 0:50, 0:25). Checkpoints: **4:20** after S6 (→ Cut 1 if past 4:45), **8:15** after S11 (→ Cut 2 if past 8:45), **11:45** after S15 (→ Cut 3 if past 12:15). Cut Level 1 saves ~35 s (S11 → 5-second flash); Cut 2 saves ~40 s (S5 collapses); Cut 3 saves ~30 s (S9 caption-only; S13 drops architecture walk). **"Never cut: slide 4 (CM2 honesty), slide 15 (limitations), slide 16 (peer question + asks)"** (L38). Rehearsal Monday **2026-07-20 ~8:00 pm** full-dress; Tuesday **2026-07-21** final check. QA checklist L60-69: copy the whole `presentation/` folder; **"Turn networking off"**; all **17 pages** render; deck uses **Georgia + Arial only**; "Open all **11 files** in `static_visuals/`"; "Stand **3 m** from the screen"; spot-check set (L67, quoted below); every data slide shows source/vintage footer; PDF copies on USB **and** a second laptop.
  L67 canonical spot-check string verbatim: `58.8 / 54.4 / 52.1 · 25/48 · 44→47 & 47→48 · $1.56M/$1.87M · $2.29M/$2.64M · $3.01M/$3.41M · $0.31M/$0.34M/$0.39M · ≈43 → ≈173–260 t/yr · 596.3 lb CO2e/MWh (eGRID2023 Rev 2, accessed 2026-07-19)`.
- **Notes:** **`presentation/static_visuals/` does not exist** — `find` over the whole repo returns zero matches for `static_visuals*`. The count "11 files" matches the contents of `dashboard/static/` (9 PNGs + `footer_log.json` + `STATIC_DASHBOARD.pdf` = 11), so this checklist item is a stale pointer to the pre-repo layout. Broken QA step (Finding F-07). Cut savings sum to ~105 s, enough to recover from any single checkpoint overrun. The L67 spot-check string canonises the wrong port numbers (Finding F-01).

### reports/README.md
- **Role:** Index of the final Milestone 2 documents and their formats.
- **Kind:** authored
- **Reads:** n/a.
- **Written by / read by:** Linked from repo-root README; links to `milestone-2/` and `../docs/standards/`.
- **Key contents:** 18 lines. Table rows: Final_Report (md·docx·pdf); Gap_Closure_Status (md·docx) — "All **52** fellowship criteria dispositioned (**29** closed / **11** already complete / **9** ready for human action / **2** partial / **1** blocked)"; FINAL_STANDARDS_APPLICATION_MATRIX (docx, md in `docs/standards`); PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT (docx, md in docs/standards); RISK_REGISTER (md·csv) — "**18 risks** with likelihood/consequence/owner/mitigation/residual/authority"; three topic briefs. Closing: "The Markdown versions are canonical; docx/pdf are rendered deliverables. **Every number traces to `data/contract/v1` (contract v1.0.0, generated 2026-07-19).**" (L16-17).
- **Notes:** The final sentence is the strongest traceability claim in the repo and it is **false for the port series** (Finding F-01) and for the FFX002 confidence label (F-02). Counts 29+11+9+2+1 = 52 ✓ and match the Gap Closure summary table exactly. Links `milestone-2/` ✓ and `../docs/standards/` ✓ both resolve.

### reports/milestone-2/ECONOMIC_AND_FUNDING_BRIEF.md
- **Role:** Funding-source landscape, FY2027 budget context, cost structure, and the NPC-not-ROI economic-measure decision.
- **Kind:** authored
- **Reads:** n/a. Cites Report 09; EX11–EX13, EX15; IM-06, IM-07, IM-08; [client contact] interview.
- **Written by / read by:** Referenced from the Final Report L112 and `reports/README.md` L14.
- **Key contents:** 53 lines. Date **2026-07-19**. Discipline line L5: "**No funding is awarded, applied for, or implied.** … The **$429,500** 12-site model output is a **screening value, never a budget.**" §1 FY2027 context: Fairfax City adopted **2026-05-05**, ≈**$207.5M** GF (**+4.5%** vs FY26), FY2027–2031 CIP, "a 2-port pilot (order **$30–60k** installed, screening class)"; PWC adopted **2026-04-21**, ≈**$1.955B** GF revenues, RE tax **$0.906**, FY2027–2032 CIP. §2 funding table: Dominion L2 = **50%** upfront make-ready, balance on-bill over **10 years**, **100%** for disadvantaged communities; Dominion Fleet same 50%; Dominion EV Charging Access = no-cost install for qualifying communities; NEVI = "frozen **Feb 2025** → court-ordered release **June 2025** → new interim guidance **Aug 2025**", **$885M** apportioned FY2026, "**Virginia solicitations anticipated Q1 2026**"; CFI; state/local DEQ/VDOT; user fees (no fee policy adopted); PPP. §3 recommended path (Dominion L2 first; local CIP; NEVI/CFI upside only; **"Budget-shortfall floor: pilot-only deployment — Alternative C degrades gracefully"**). §4 benchmarks (EX15): average L2 install ≈**$2,500/connector**, range **$1k–$10k**; maintenance ≈**$400/yr** per L2; **NREL: soft costs can exceed 50%** of project cost; client frame **~$1,000/station/yr**, **17 decommissioned stations ≈ $20k/yr avoided**; civil contingency **20–30%**; **~10-yr electronics replacement**. §5: "**Selected (MCDA winner, 85.8): Net Present Cost comparison**" with "**avoided cost (84.6, effectively tied)**"; "**ROI is explicitly rejected for Milestone 2 (MCDA 52.8)**". §6 standing caveats (quoted in Part D).
- **Notes:** "**Virginia solicitations anticipated Q1 2026**" is stated in a document dated 2026-07-19 — Q1 2026 is already in the past at authoring time; the document does flag "status to re-verify" (L35), so it is honestly hedged but stale. The MCDA scores in §5 (85.8 / 84.6 / 52.8) are an **economic-measure** MCDA, distinct from the **alternatives** MCDA in the Final Report §4 (85 / 81 / 72 / 71 / 58 / 41 / 37) — two different 100-point scales in the same program; do not conflate. "Alternative **C** degrades gracefully" as the pilot-only floor is questionable: in the Final Report §4, C = "EV-ready-first (pathways only)" and **B** is the staged-pilot option; RISK_REGISTER.csv R18 repeats the same "Alternative C" phrasing, so the two files agree with each other but possibly not with the alternatives table (Finding F-10, low confidence).

### reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md
- **Role:** Environmental conditions, the authoritative grid emissions factor, the net-CO2e model, circularity/end-of-life, and the explicit no-resilience-claim statement.
- **Kind:** authored (carries the **authoritative** eGRID factor statement)
- **Reads:** n/a. Cites Report 08, Report 10 §1; EX09, EX10, EX14, EX15; IM-01, IM-02, IM-05.
- **Written by / read by:** Referenced from the Final Report L111; the factor it fixes is the value in `grid_factor_value` on all 120 contract rows.
- **Key contents:** 49 lines. §1 conditions table (heat / heavy precipitation & flooding / stormwater / outages / regional grid context). Outage row L16: "**No battery storage is in scope (`battery_storage_flag=0` at all 12 sites), and therefore this project makes NO resilience claim.**" Regional-grid row L17: PWC CESMP targets "**50% GHG cut vs 2005 by 2030; 100% renewable county-gov electricity by 2030; county-wide 2035; carbon-neutral county ops 2050**". §2 **Factor: 596.3 lb CO2e/MWh**, SRVC total output emission rate, **eGRID2023 Rev 2**, data year **2023**, initial release **2025-01-15**, Rev 2 released **2025-06-12**, source EPA eGRID summary data (IM-01); correction note L22 (quoted below); annual refresh — "**eGRID2024 preliminary data exists via API (≈−1.8% CO2e average)** but is not the official release and is not used"; risk R12. §3 net-CO2e model: "Annual kWh delivered per horizon (**2036/2046/2056**)"; "kWh × **596.3** lb CO2e/MWh"; displaced = (kWh ÷ EV efficiency benchmark) × displaced-vehicle gCO2/mile; 2024 regional capacity mix "**36.2% gas, 14.5% nuclear, 11.5% coal, ~15.7% renewables incl. purchases, 0.1% battery**". §4 UL 3600 (**1st ed., 2023-01-09**, IM-05); **~10-year** EVSE electronics refresh; **17** decommissioned stations ≈ **$20k/yr**; proposed-standard **Module 7**. §5 resilience statement (quoted in Part D); "UL 9540/9540A and **NFPA 855 (2026 ed.)**".
- **Notes:** L22 is the **only place in the repo outside CHANGELOG.md and `docs/methodology/current-facts-source-register.md`** where `590.2` appears in a report-tier document, and it appears as an explicit correction note. Verbatim: *"Correction note: the research package (EX10) carried ≈590.2; the implementation run verified EPA's published SRVC CO2e total output rate as 596.326 lb/MWh. **596.3 with vintage label is the value used everywhere in this implementation.**"* This is documentation *of* the correction, not a surviving use of the wrong value — but the lane brief says 590.2 "must survive NOWHERE", so Phase 1 must make an explicit keep/strike decision (Finding F-08). The `2035` and `2050` at L17 are **external PWC CESMP policy target years**, not project horizons — legitimate but they will trip any naive horizon grep.

### reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md
- **Role:** The integrated Milestone 2 project record — the canonical narrative deliverable.
- **Kind:** authored (canonical per `reports/README.md` L16)
- **Reads:** n/a. References `data/contract/v1/`, `docs/human-actions/*`, `docs/standards/*`, `docs/architecture/*`, `docs/operations/website-patch-package/`, `dashboard/static/`, `dashboard/tableau/`, `excel/`, `matlab/`, `presentation/`, `00_IMPLEMENTATION_MANIFEST.md`, `verification/`.
- **Written by / read by:** Rendered to `.docx` and `.pdf` siblings in the same directory; indexed by `reports/README.md`.
- **Key contents:** 157 lines, 13 sections. Header: team Anna·Laylas·Andy·Adama·Paula (GMU); client [client contact], Green Buildings Manager, PWC Office of Sustainability; prepared **2026-07-19** for **2026-07-21**; supersedes `Future_City_Fellowship_Milestone_2_Phase_Report.md`. Standing-discipline blockquote L10 (quoted in Part D). §1: Fairfax City **~25k**, PWC **~500k**; leading solution scored **85/100**, hybrid **81/100**, county **~35-station** fleet hub; new-since-Phase-2 bullets — baseline reproduced (FFX002 **58.8**; **25 starter / 48 pathway**; **38 REVIEW + 12 INFO**; **15** Tableau exports; **35-file** package); V3 model `fcf_m2` **3.0.0`, two modes `legacy_v2` / `milestone2_v3`, **80 tests, 92% coverage**; contract **v1.0.0, 120 scenario rows**; the eGRID bullet L27 (**596.3**, "the research package's **590.2** figure was superseded"); Excel; MATLAB "**blocked** (no licensed MATLAB available)"; six human-action packages. Headline table L35-40 (2026/2036/2046/2056 × ports / staged NPC / broad NPC / staged avoids / net CO2e). §2 verified-baseline table: Python V1 PASSED; V2 ALL PASS with "**25 starter / 35 / 44 / 44 / 54 ports across legacy cases; 48 future-ready**"; **0 of 12** High confidence; offline GIS ("Cold-start offline fails (documented V2 defect); V3 fix: cached VA TIGER boundaries in-repo"); MATLAB "**No simulation executed — none claimed.**" §3 client evidence (McCoart **10-port** install; Neabsco **70 ports**, **17** offline, **~$1,000/station/yr**, **~$20k/yr**; LEED **~5%**; ADA **a year** of redesign; **no local EV fires yet**). §4 seven alternatives with weights **25/20/20/15/10/10** and scores **B 85, F 81, E 72, C 71, D 58, A 41, G 37**; sensitivity "survives **±5pp**"; crossover at "**~2×** default" equity weight. §5 two aspects (L82 the 10/20/30 requirement statement; growth multipliers **1.9/2.6 → 3.0/4.5 → 4.0/6.0, stress ×1.15**; **48-port** cap; seeded **400-day** DES; **P10/P50/P90**; "**under the 10-minute target at every top site**"; **3% real discount**; avoided cost **$0.31M (2036) → $0.39M (2056)**; **596.3**; **≈173–260 t/yr**; **13–23 pathway ports** not energized). §6 contract file list, **120 rows**, ten reconciliation tests, "legacy totals **25/48**", `capacity_basis`, and "eliminating the hand-built CSV and its **2050**-base/high port mismatch". §7 V3 integrity (PY-02, PY-05, PY-03 `demand_model_status = synthetic_uncalibrated`, PY-20 triggers: **≥40%** utilization, repeated **10-minute** waits, **≥97%** uptime, **≥6 months** observation, equity override to **25%**). §8 standards (UL 2594 3rd ed. 2022; UL 3600 2023; **2020 NEC via the 2021 USBC, effective 2024-01-18**; Access Board **still at NPRM as of 2026-07-19**; **seven test modules**, **three conformance levels**). §9 integration/risk/environment/funding/stakeholders (**8-interface** register; **18-risk** register; Fairfax **≈$207.5M**, PWC **≈$1.955B**; **$885M** FY26; **nine-lane** jurisdictional map). §10 artifact-status table (**six live reconciliation checks all PASS**; MATLAB "**execution BLOCKED (no license)**"; Tableau "**blocked**"; **9** static visuals; website "**Nothing deployed.**"; presentation "**≤13-minute** timing runbook"). §11 nine numbered limitations (quoted in Part D). §12 seven next human actions. §13 peer question + two backups.
- **Notes:** Referenced-path check: `docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md` ✓, `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md` ✓, `docs/architecture/TECHNICAL_INTEGRATION_ARCHITECTURE.md` ✓, `docs/assets/architecture/` ✓, all six `docs/human-actions/*` ✓, `docs/human-actions/client_meeting_2/01_EMAIL_DRAFT_TO_CLIENT.md` ✓, `docs/operations/website-patch-package/` ✓, `matlab/` ✓. **MISSING: `00_IMPLEMENTATION_MANIFEST.md` and `verification/`** (L156) — neither exists at repo root or anywhere in the tree. **MISSING: `Future_City_Fellowship_Milestone_2_Phase_Report.md`** (L8, the superseded document) — plausibly intentional (archived), but the sentence claims "that report remains the authoritative record", pointing at nothing readers can reach. `lifecycle_costs.csv` (cited in Gap Closure B8/F4) exists at `data/outputs/v3_run/lifecycle_costs.csv`, **not** in `data/contract/v1/`; `avoided_evse_metric.csv` likewise at `data/outputs/v3_run/`.

### reports/milestone-2/Milestone_2_Gap_Closure_Status.md
- **Role:** Final disposition of all 52 fellowship criteria after the 2026-07-19 implementation run.
- **Kind:** authored
- **Reads:** n/a. Cites the July 2026 compliance-gap audit (13 HAVE / 22 PARTIAL / 17 NOT HAVE) and Report 02.
- **Written by / read by:** Indexed by `reports/README.md`; rendered to `.docx`.
- **Key contents:** 87 lines. Prior audit: **13 HAVE / 22 PARTIAL / 17 NOT HAVE** (= 52 ✓). Vocabulary: Closed by implementation / Ready for human action / Partially implemented / Blocked / Already complete. Summary: **29 / 11 / 9 / 2 / 1 = 52** ✓. Integrity rule L23: "**no externally dependent criterion was converted to 'closed.'**" 52-row table with owner codes T/C/F/U/A. Notable rows: A1–A4, A5–A8, G5 = Ready for human action (9 total: A1,A2,A3,A4,A5,A6,A7,A8,G5); **B3 "10-year outcome modeled" → 2036**; **B4 "20-year" → 2046**; **B5 "30-year" → 2056**; B6 "RT-06 year-set equality enforced across Python/Excel/MATLAB adapter/visuals/deck"; B7 = **Partially implemented**; **D1 = Blocked** (missing utility/facility data, "capacity unconfirmed 12/12"); **F2 = Partially implemented**; C2 "UL 2594 + UL 3600 … only pair covering both rubric rows"; C7 "**Seven test modules**"; C8 "**18-risk** register"; E2 "Net CO2e at **2036/2046/2056**"; H2 "**≤13-min** timing runbook". Closing L86: what must never be claimed (quoted in Part D).
- **Notes:** Counts are internally consistent (9 "Ready" rows, 2 "Partially implemented" rows B7+F2, 1 "Blocked" row D1 — all verifiable by counting the table). The 10/20/30-year phrasing at B3/B4/B5/E2/F2 is **the fellowship criterion wording** and is immediately paired with the canonical years — legitimate, not a horizon violation. This document is the single best cross-check on what the program may and may not claim.

### reports/milestone-2/REGULATORY_STAKEHOLDER_MAP.md
- **Role:** Who decides what, per jurisdiction, plus the stakeholder-role table and engagement posture.
- **Kind:** authored
- **Reads:** n/a. Cites Report 10 §1/§3/§5; EX07–EX09, EX12–EX14; IM-02, IM-03.
- **Written by / read by:** Referenced from the Final Report L113 ("the nine-lane jurisdictional map").
- **Key contents:** 47 lines. Naming discipline L5 (quoted in Part D). §1 jurisdictional table — **nine lanes** ✓ (building permit/electrical, fire review, EV-ready new construction, accessibility, zoning/site plan, stormwater, utility interconnection, procurement, data/privacy). Instruments: **2021 Virginia USBC (eff. 2024-01-18; 2020 NEC basis; 2021 VCC §406.2.7 for EV) — 2024 code cycle underway, expected ≈2027**; **2021 Virginia SFPC**; **AFDC listing 12646**; **Access Board EVSE NPRM (2024-09-03, still NPRM as of 2026-07-19)**; **VSMP**-delegated local programs; **Dominion (SCC-regulated)**; **VPPA**; **VCDPA**. Closing L23: "Final interpretation of adopted editions rests with each AHJ." §2 ten-role stakeholder table with a **Verification status** column — city-side client counterpart is "**verify with jurisdiction**"; PWC side verified ([client contact]). §3 engagement posture (facility-user intercept/online surveys at top-3; accessibility-community review; listening sessions; "Web/assistant channels are for **explanation, not collection** (VCDPA-aware, no unnecessary PII)"; "**Spanish at minimum** for PWC candidates"). §4 social-implication flags (equity override; parking displacement; fee policy; **EVITP-certified installer** requirement; "**zero local EV fires** per Adams interview"; **no-app/tap-to-pay** capability required in procurement).
- **Notes:** Consistently hedged; the "verify with jurisdiction" markers are exactly the epistemic discipline Phase 7 must carry into the platform. Names a specific site not otherwise mentioned in this lane: PWC002 Neabsco commuter-garage users.

### reports/milestone-2/RISK_REGISTER.md
- **Role:** Human-readable 18-risk register with scoring discipline and reading notes.
- **Kind:** authored (human-readable twin of the CSV)
- **Reads:** n/a. Derived from the research-phase `FAILURE_MITIGATION_OPTIONS.csv` (explicitly "pre-V3 research archive, **not tracked in this repository**").
- **Written by / read by:** Machine twin is `RISK_REGISTER.csv`; referenced from Final Report L110 and `reports/README.md` L13.
- **Key contents:** 37 lines. L4: "**Machine version:** `RISK_REGISTER.csv` (same 18 rows)". Scoring discipline L6 (quoted in Part D). Ranked table, 18 rows, score = L×C: **R01 4×4=16**, **R10 4×4=16**, **R17 4×4=16**, **R07 3×5=15**, R04 4×3=12, R05 3×4=12, R06 4×3=12, R13 4×3=12, R14 4×3=12, R18 4×3=12, R09 3×3=9, R11 3×3=9, R16 3×3=9, R02 2×4=8, R08 2×4=8, R12 4×2=8, R15 3×2=6, R03 2×2=4. Embedded numbers: "**12/12 today**" unconfirmed; "documented **1-year** schedule cost"; "**NEVI 97%** as benchmark practice"; "**596.3** lb CO2e/MWh, eGRID2023 Rev 2 (IM-01)"; "**20–30%** civil contingency"; "**$429,500** 12-site figure stays a screening value, never a budget"; "client **17-station** experience"; "only **PWC002 Neabsco** of 12"; "**11/12** are surface"; "**~10-yr** electronics refresh". §2 reading notes: three client-evidence risks are R14 (Neabsco) / R17 (McCoart) / R07 (Adams); R01 is the highest-value data request.
- **Notes:** **Arithmetic/wording inconsistency at L5:** "plus **four** cross-cutting risks from Reports 07–10: ADA redesign, overbuild/underuse, trenching cost escalation, data staleness, and funding volatility" — that list contains **five** items, and 15 assessed failure modes + 4 (or 5) ≠ 18 either way. In the CSV, R01–R16 all cite `FAILURE_MITIGATION_OPTIONS` rows (16 risks, not 15) and only R17/R18 do not. Finding F-11. All 18 L/C/score triples match the CSV exactly — verified cell-by-cell.

### reports/milestone-2/RISK_REGISTER.csv
- **Role:** Machine-readable risk register with the evidence-basis column that the .md omits.
- **Kind:** authored (hand-maintained data, not model output)
- **Reads:** n/a.
- **Written by / read by:** Human twin `RISK_REGISTER.md`; cited by Final Report L110.
- **Key contents:** 18 data rows, 12 columns ordered: `risk_id, risk, likelihood_1_5, consequence_1_5, score, owner, trigger_indicator, mitigation, evidence_basis, residual_risk, required_response_time, deciding_authority`. Rows R01→R18 in **numeric ID order** (the .md is in **score-descending** order). `score` = likelihood × consequence on all 18 rows ✓. `evidence_basis` cites `FAILURE_MITIGATION_OPTIONS` rows 1–25, plus EX03/EX09/EX12/EX15, IM-01/IM-02/IM-06/IM-07, Report 08/09/10, the Adams interview, and the client transcript. Numbers embedded: "**596.3** lb CO2e/MWh eGRID2023 Rev 2 per IM-01" (R12); "**$429500** 12-site figure held as screening value never budget" (R17); "**$1k-$10k** per connector range" (R17); "**50 percent** upfront **100 percent** for disadvantaged communities" (R18); "**$885M** FY26 VA solicitations anticipated Q1 2026" (R18); "**NEVI 97%**" (R06); "**20-30 percent** contingency" (R17); "**~10-year** electronics refresh" (R15); "only **PWC002 Neabsco** among 12" / "**11/12** are surface" (R08); "**12/12 sites unconfirmed**" (R01).
- **Notes:** Unquoted CSV — all commas inside prose fields were replaced by spaces or hyphens (e.g. "grid factors costs code status", "FAILURE_MITIGATION_OPTIONS rows 12 25", "$429500", "50 percent"), so it parses cleanly but has lost punctuation and the `$429,500` thousands separator. R01's `evidence_basis` cites a "**client Crisis Receiving Center capacity limit**" — a facility that appears **nowhere else** in this lane's documents (worth a Phase 1 provenance check).

---

## PART B — EVERY QUANTITATIVE CLAIM IN THIS LANE

Legend for **Attributed?**: `contract` = the document names the canonical contract / a contract file as the source; `source-ID` = it cites an EX##/IM##/Report## research identifier; `client` = client-interview evidence; `none` = asserted without attribution.
**Trace** is my own check against the six patch-package CSVs (= the contract).

| # | Value | Units | File | Line | Attributed? | Trace |
|---|---|---|---|---|---|---|
| 1 | 9 | static visuals | dashboard/README.md | 7 | none | ✓ 9 PNGs in `dashboard/static/` |
| 2 | 86.4/100 | research score for "static visuals" demo strategy | dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md | 23 | none | **NOT TRACEABLE in this lane** |
| 3 | 12 | worksheets in the original legacy workbook | TABLEAU_IMPLEMENTATION_BLOCKER.md | 58 | none | untestable — workbook not in tree |
| 4 | 13 | extracts in the original legacy workbook | TABLEAU_IMPLEMENTATION_BLOCKER.md | 58 | none | untestable |
| 5 | 6 | patch-package CSVs | TABLEAU_IMPLEMENTATION_BLOCKER.md | 30-32 | n/a | ✓ 6 files |
| 6 | 7 | worksheets in the recipe | TABLEAU_IMPLEMENTATION_BLOCKER.md | 34 | n/a | ✓ 7 listed |
| 7 | 48 | pathway-ceiling reference line (ports) | TABLEAU_IMPLEMENTATION_BLOCKER.md | 39 | contract | ✓ Σ ports_pathway = 48 |
| 8 | 596.3 | lb CO2e/MWh | TABLEAU_IMPLEMENTATION_BLOCKER.md | 43 | contract | ✓ all 120 rows |
| 9 | 10 | min, peak-wait reference line | TABLEAU_IMPLEMENTATION_BLOCKER.md | 44 | none | ✓ target exists; but 21 contract rows exceed it |
| 10 | 1600×900 | px dashboard size | TABLEAU_IMPLEMENTATION_BLOCKER.md | 47 | n/a | n/a |
| 11 | 8 | story points | TABLEAU_IMPLEMENTATION_BLOCKER.md | 49 | n/a | **inconsistent** — "01→09" is 9 files |
| 12 | 12 | sites at `capacity_basis` = placeholder | TABLEAU_IMPLEMENTATION_BLOCKER.md | 51 | contract | ✓ 120/120 rows `placeholder` |
| 13 | 0 of 12 | sites at High confidence | TABLEAU_IMPLEMENTATION_BLOCKER.md, footer_log.json, speaker notes 64/105, ECON 52, Final Report 10/52/128, RISK 6 | many | contract | ✓ `data_confidence` = Low on 120/120 |
| 14 | 9.5 | kWh/session | footer_log.json | 34 | contract | ✓ `energy_per_session_kwh` = 9.5 on 120/120 |
| 15 | 0.30 | kWh/mi EV efficiency benchmark | footer_log.json | 34 | none (labelled "benchmark assumptions") | not a contract column |
| 16 | 400 | gCO2/mi displaced | footer_log.json | 34 | none (labelled benchmark) | not a contract column |
| 17 | 3% | real discount rate | footer_log.json 26, Final Report 86, root README | — | contract | not a contract column; consistent across docs |
| 18 | ~$1k | /port/yr fee frame | footer_log.json 41, tbl_avoided_evse (all rows) | — | client | ✓ `avoided_network_fee = ports × 1000` |
| 19 | 400 | days, seeded DES | footer_log.json 47, Final Report 84 | — | contract | seed `20260719` in tbl_peak_waits ✓; 400-day horizon not in CSV |
| 20 | 2024 | TIGER vintage | footer_log.json | 60 | none | n/a |
| 21 | 6.5% | PWC share (planning proxy) | excel/README.md | 12 | labelled proxy | not in this lane's CSVs |
| 22 | 200/600/1,200 | MW data-center selector | excel/README.md | 12 | labelled scenario assumption | not in this lane's CSVs |
| 23 | 2047+ | CAGR-extrapolation start row | excel/README.md | 11 | labelled extrapolation | n/a |
| 24 | 6 | live reconciliation checks, all PASS | excel/README.md 18, Final Report 119 | — | none | **unverified** (workbook has no sharedStrings; not read in this lane) |
| 25 | 596.3 | lb CO2e/MWh | excel/README.md | 16 | contract | ✓ |
| 26 | 17 | slides | presentation/README.md 8, speaker notes 3, runbook 4/63/64 | — | n/a | consistent across 4 files |
| 27 | 13 | beats | presentation/README.md 8 | — | n/a | ✓ beats 1–13 in speaker notes |
| 28 | 30–60 | s per slide | presentation/README.md | 9 | n/a | ✓ budgets 0:15–0:55 |
| 29 | 13:00 | total presentation time | presentation/README.md 10, runbook 6/26 | — | n/a | ✓ budget column sums to 13:00 |
| 30 | 12:15 | rehearsal target | runbook | 3 | n/a | n/a |
| 31 | ~45 s | real-world slack | runbook | 3 | n/a | 13:00 − 12:15 = 45 s ✓ |
| 32 | 4:20 / 8:15 / 11:45 | checkpoint times | runbook | 29-31 | n/a | ✓ match running totals |
| 33 | 4:45 / 8:45 / 12:15 | cut triggers | runbook | 29-31 | n/a | n/a |
| 34 | ~35 / ~40 / ~30 | s saved per cut level | runbook | 35-37 | none | n/a |
| 35 | 11 | files in `static_visuals/` | runbook | 65 | none | **directory does not exist**; 11 = count of `dashboard/static/` |
| 36 | 3 | m viewing distance | runbook | 66 | n/a | n/a |
| 37 | 58.8 / 54.4 / 52.1 | readiness scores | runbook 67, speaker notes 63, Final Report 51 | — | contract | ✓ `tbl_readiness_confidence` rows 1–3 |
| 38 | 25/48 | starter / pathway ports | runbook 67, speaker notes 69, Final Report 22/51/92 | — | contract | ✓ Σ 2026 baseline |
| 39 | **44→47 & 47→48** | active ports by horizon | runbook 67, speaker notes 74, Final Report 38-40, root README 39-41 | — | contract ("canonical contract v1.0.0") | ✗ **CONTRADICTED** — contract gives base 35/44/44, high 44/48/48; 47 never occurs |
| 40 | $1.56M / $2.29M / $3.01M | staged NPC | runbook 67, speaker notes 75, Final Report 38-40 | — | contract | ✓ 1,560,499 / 2,294,469 / 3,014,200 |
| 41 | $1.87M / $2.64M / $3.41M | broad NPC | same | — | contract | ✓ 1,872,578 / 2,635,638 / 3,407,606 |
| 42 | $0.31M / $0.34M / $0.39M | avoided cost | same | — | contract | ✓ 312,079 / 341,169 / 393,406 |
| 43 | ≈43 t/yr | 2026 net avoided CO2e | runbook 67, speaker notes 76, Final Report 37 | — | contract | ✓ 43.4 t |
| 44 | ≈82 → 113 t/yr | 2036 net CO2e base→high | Final Report | 38 | contract | ✓ 82.4 / 112.7 |
| 45 | ≈130 → 195 t/yr | 2046 | Final Report | 39 | contract | ✓ 130.1 / 195.1 |
| 46 | ≈173 → 260 t/yr | 2056 | Final Report 40, speaker notes 76/98, runbook 67 | — | contract | ✓ 173.4 / 260.2 |
| 47 | 596.3 | lb CO2e/MWh | runbook 67, speaker notes 98, Final Report 27/86, ENV 21/31, RISK md 27 / csv 13, excel README 16, footer_log 31, blocker 43 | — | contract / IM-01 | ✓ all 120 rows |
| 48 | 70 | ports at Neabsco | speaker notes 34, Final Report 60 | — | client | client evidence; not in contract |
| 49 | 17 | stations decommissioned | speaker notes 34, Final Report 60, ENV 44, ECON 40, RISK md 20 | — | client | client evidence |
| 50 | ~$1,000 | /station/yr keep-online | speaker notes 34, Final Report 60, ECON 40 | — | client | ✓ matches avoided-fee unit |
| 51 | ~$20k/yr | avoided keep-online cost | Final Report 60, ENV 44, ECON 40 | — | client | 17 × ~$1,000 ≈ $17k, stated as ~$20k — rounding |
| 52 | ~35 | station county fleet hub | speaker notes 35, Final Report 18 | — | client | client evidence |
| 53 | 85/100 | Alternative B MCDA | speaker notes 52, Final Report 18/70 | — | "provisional" | not in contract; provisional research score |
| 54 | 81 | Alternative F | speaker notes 52, Final Report 18/71 | — | provisional | not in contract |
| 55 | 72 / 71 / 58 / 41 / 37 | Alternatives E / C / D / A / G | Final Report | 72-76 | provisional | not in contract |
| 56 | 25/20/20/15/10/10 | MCDA criterion weights | Final Report | 66 | provisional | sums to 100 ✓ |
| 57 | ±5pp | sensitivity band | Final Report | 78 | provisional | n/a |
| 58 | ~2× / "double" | equity weight at crossover | Final Report 78, speaker notes 52 | — | provisional | n/a |
| 59 | 38 REVIEW + 12 INFO | model findings | speaker notes 64, Final Report 22/51 | — | contract | not a contract column — **needs Phase 1 trace** |
| 60 | 15 | Tableau exports (V2) | Final Report | 22/51 | contract | not traceable in this lane |
| 61 | 35 | package files (V2) | Final Report | 22/51 | contract | not traceable in this lane |
| 62 | 2–3 | starter ports in the pilot | speaker notes 57/112, Final Report/RISK R02 | — | none | contract 2026 ports_active ∈ {2,3} ✓ |
| 63 | 3.0.0 | `fcf_m2` version | Final Report | 23 | none | contract_version is 1.0.0 (different field) |
| 64 | 80 tests / 92% coverage | test suite | Final Report | 23 | none | **not verified in this lane** |
| 65 | 120 | scenario rows | Final Report 24/92, Gap Closure B2 | — | contract | ✓ exactly 120 |
| 66 | v1.0.0 | contract version | many | — | contract | ✓ `contract_version` = 1.0.0 on 120/120 |
| 67 | 1.9/2.6 → 3.0/4.5 → 4.0/6.0, ×1.15 | growth multipliers (base/high per horizon; stress) | Final Report | 84 | "provisional conventions" | not a contract column |
| 68 | 10-minute | wait target | Final Report 84/99, blocker 44 | — | proposed policy | **21 contract rows exceed 10 min; max 215.35** |
| 69 | 13–23 | pathway ports not energized, base path | Final Report | 86 | contract | partial — 2026=23, 2036=13, **2046=4, 2056=4** |
| 70 | 25/48 | legacy totals reconciliation test | Final Report | 92 | contract | ✓ |
| 71 | ten | reconciliation tests | Final Report | 92 | contract | not verified in this lane |
| 72 | ≥40% / 25% / ≥97% / ≥6 months | trigger thresholds (utilization, equity override, uptime, observation) | Final Report | 99 | "proposed configuration, not adopted" | not contract columns |
| 73 | 2020 NEC / 2021 USBC / 2024-01-18 | code basis + effective date | speaker notes 12/86, Final Report 103, REG 13 | — | IM-03 / EX07 | consistent across 3 files ✓ |
| 74 | UL 2594 3rd ed. 2022 | standard edition | speaker notes 85, Final Report 103 | — | IM-05 | consistent ✓ |
| 75 | UL 3600 2023 / 1st ed. 2023-01-09 | standard edition | speaker notes 85, Final Report 103, ENV 39 | — | IM-05 | consistent ✓ |
| 76 | NFPA 855 (2026 ed.) | standard edition | ENV | 48 | none | n/a |
| 77 | seven / three | test modules / conformance levels of the proposed standard | Final Report 105, Gap Closure C7 | — | none | ✗ **speaker notes L88 says "three modules"** |
| 78 | 8 | interfaces in the integration register | Final Report 109, Gap Closure D3 | — | none | not verified in this lane |
| 79 | 18 | risks | Final Report 110, reports/README 13, RISK md 4 | — | n/a | ✓ 18 rows in both md and csv |
| 80 | ≈$207.5M / +4.5% | Fairfax City FY2027 GF | ECON 13, Final Report 112 | — | EX13, IM-08 | consistent ✓ |
| 81 | ≈$1.955B / $0.906 | PWC FY2027 GF revenues / RE tax rate | ECON 14, Final Report 112 | — | EX13, IM-08 | consistent ✓ |
| 82 | 2026-05-05 / 2026-04-21 | FY2027 adoption dates | ECON | 13-14 | EX13, IM-08 | n/a |
| 83 | FY2027–2031 / FY2027–2032 | CIP windows | ECON | 13-14 | EX13, IM-08 | n/a |
| 84 | $30–60k | installed cost, 2-port pilot (screening) | ECON | 13 | none ("screening class") | not in contract |
| 85 | 50% / 100% / 10 years | Dominion L2 make-ready terms | ECON 22, Final Report 112, speaker notes 100, RISK R18 | — | IM-07, EX12 | consistent ✓ |
| 86 | $885M | NEVI FY2026 apportionment | ECON 25, Final Report 112, RISK R18 | — | IM-06, EX11 | consistent ✓ |
| 87 | Feb 2025 / June 2025 / Aug 2025 | NEVI freeze / release / interim guidance | ECON | 25 | EX11 | n/a |
| 88 | Q1 2026 | anticipated VA NEVI solicitations | ECON 25/35, Final Report 112, RISK R18 | — | IM-06 | **stale relative to the 2026-07-19 doc date** |
| 89 | ≈$2,500/connector; $1k–$10k | L2 install benchmark + range | ECON 40, RISK R17 | — | EX15 | consistent ✓ |
| 90 | ≈$400/yr | L2 maintenance per unit | ECON | 40 | EX15 | not in contract |
| 91 | >50% | NREL soft-cost share | ECON | 40 | EX15 (NREL) | n/a |
| 92 | 20–30% | civil contingency | ECON 42, RISK R17 | — | "class-of-estimate" | consistent ✓ |
| 93 | ~10-yr | electronics replacement cycle | ECON 42, ENV 42, Final Report 86, RISK R15 | — | "industry practice benchmark" | consistent ✓ |
| 94 | **$429,500** | 12-site screening cost | ECON 5/43, Final Report 131, RISK md 14 / csv R17 | — | "model output", "screening value" | **NOT in `tbl_portfolio_costs`** (which gives 1.56M/2.29M/3.01M NPV) — needs Phase 1 trace |
| 95 | 85.8 / 84.6 / 52.8 | economic-measure MCDA: NPC / avoided cost / ROI | ECON | 47-48 | provisional MCDA | separate scale from the alternatives MCDA |
| 96 | ~5% | LEED "sufficient EV charging" guidance | Final Report | 60 | client | n/a |
| 97 | 36.2% / 14.5% / 11.5% / ~15.7% / 0.1% | 2024 regional capacity mix (gas/nuclear/coal/renewables/battery) | ENV | 35 | Report 08, "verified local workbook" | not in this lane's CSVs |
| 98 | 50% by 2030 / 100% by 2030 / 2035 / 2050 | PWC CESMP targets | ENV | 17 | EX14 | external policy targets, not project horizons |
| 99 | −1.8% | eGRID2024 preliminary CO2e average change | ENV | 23 | none | explicitly "not used" |
| 100 | 596.326 | lb/MWh, EPA published SRVC rate | ENV | 22 | IM-01 | rounds to 596.3 ✓ |
| 101 | 590.2 | lb CO2e/MWh (superseded) | ENV 22, Final Report 27 | — | EX10, labelled superseded | **see Finding F-08** |
| 102 | 2025-01-15 / 2025-06-12 | eGRID2023 initial release / Rev 2 release | ENV | 21 | IM-01 | n/a |
| 103 | 13 HAVE / 22 PARTIAL / 17 NOT HAVE | prior audit counts | Gap Closure | 3 | July 2026 audit | sums to 52 ✓ |
| 104 | 29 / 11 / 9 / 2 / 1 = 52 | final dispositions | Gap Closure 16-21, reports/README 10 | — | n/a | ✓ table rows count out |
| 105 | 7×6 | MCDA matrix shape | Gap Closure | 37 | provisional | ✓ 7 alternatives × 6 criteria |
| 106 | nine-lane | jurisdictional map | Final Report 113, REG §1 | — | Report 10 | ✓ 9 rows |
| 107 | 12646 | AFDC listing number | REG | 15 | none | n/a |
| 108 | 2024-09-03 | Access Board NPRM date | REG 16, RISK R10 | — | IM-02 | consistent ✓ |
| 109 | ≈2027 | expected next VA code cycle | REG 13, Final Report 103 | — | IM-03 | consistent ✓ |
| 110 | 16 / 15 / 12 / 9 / 8 / 6 / 4 | risk scores | RISK md 12-29, csv | — | "team screening judgments" | ✓ all = L×C, md and csv agree row-for-row |
| 111 | 97% | NEVI uptime benchmark | RISK R06, Final Report 99 | — | FHWA NEVI practice | consistent ✓ |
| 112 | 11/12 surface, 1 enclosed | site form factor | RISK R08 | — | `site_table` flags | ✓ `garage_enclosed`=1 only PWC002 |
| 113 | 15 assessed failure modes + "four" cross-cutting | register provenance | RISK md | 5 | pre-V3 archive (untracked) | ✗ list names **five**; 15+4≠18 |
| 114 | 1–5 | likelihood/consequence scale | RISK md 6, csv header | — | "not measured probabilities" | ✓ |
| 115 | ~25k / ~500k | Fairfax City / PWC population | Final Report | 16 | none | not in contract |
| 116 | 10-port | McCoart install size | Final Report | 60 | client | n/a |
| 117 | 19.2 | kW EVSE power | tbl_canonical_scenarios | all | contract | ✓ constant, never quoted in prose |
| 118 | 0.658 | max site utilization | tbl_canonical_scenarios | — | contract | ✓ computed; never quoted in prose |
| 119 | 617,403 | USD, DEF-case lifecycle cost (all 9 DEF rows) | tbl_portfolio_costs | 2-4, 11-13, 20-22 | contract | ✓ but suspiciously constant across horizons and escalation cases |
| 120 | 42.365 | min, PWC002 peak Erlang wait | tbl_peak_waits | 4 | contract | ✓; contradicts the 10-min narrative if plotted |

---

## PART C — HORIZON-CONVENTION SCAN (canonical = 2026 / 2036 / 2046 / 2056)

Complete `grep -nE "\b(2035|2050|2030|2045|2055)\b|10/20/30|10-year|20-year|30-year|10-yr|20-yr|30-yr|Now"` over all 15 assigned text files, classified:

**DEFECTS (unlabelled, stale, or convention-violating):**
| File:Line | Text | Why it's a defect |
|---|---|---|
| `dashboard/tableau/patch_package/tbl_canonical_scenarios.csv` (= `data/contract/v1/scenario_table.csv`), all 120 rows, column `horizon_label` | `now`, `plus10`, `plus20`, `plus30` | The contract itself carries the 10/20/30 + "now" vocabulary on rows whose `model_mode` is `milestone2_v3` (not `legacy_v2`). This is the machine-readable root of the convention drift; every downstream label inherits it. |
| `presentation/deck/..._Speaker_Notes.md:131` | "Andy→Adama (slide 10): **\"Adama has the 30-year numbers.\"**" | Spoken line, no canonical-year pairing, no legacy label. |
| `reports/.../Future_City_Fellowship_Milestone_2_Final_Report.md:152` | "how to keep a **30-year** model honest when **10-year** goals are already off-track" | Peer-question backup; no canonical-year pairing. |
| `reports/.../Future_City_Fellowship_Milestone_2_Final_Report.md:92` | "eliminating the hand-built CSV and its **2050**-base/high port mismatch" | A bare `2050` describing a historical defect; not labelled legacy_v2, and 2050 is not a canonical horizon. |
| `presentation/deck/..._Speaker_Notes.md:76` | "net avoided CO2e grows from ≈43 t/yr **now** to ≈173–260 t/yr by 2056" | Informal "now" for the 2026 baseline; mirrors the contract's `horizon_label=now`. |

**LEGITIMATE (correctly labelled or clearly non-horizon):**
| File:Line | Text | Why it's fine |
|---|---|---|
| `Final_Report.md:82` | "The official requirement — two aspects modeled at **10/20/30-year** timelines — is satisfied with the canonical convention **2036/2046/2056** from a stated **2026** baseline" | Explicitly quotes the fellowship requirement and immediately maps it to canonical years. This is the model sentence. |
| `Gap_Closure_Status.md:41,42,43` | B3 "10-year outcome modeled" → 2036; B4 "20-year" → 2046; B5 "30-year" → 2056 | Criterion titles, each paired with the canonical year in the same row. |
| `Gap_Closure_Status.md:62` | E2 "Environmental benefits quantified **10/20/30**" → "Net CO2e at **2036/2046/2056**" | Same pattern. |
| `Gap_Closure_Status.md:67` | F2 "**10-yr** cost order per alternative" | Cost-order horizon, criterion-derived; borderline — Phase 1 may want it re-worded. |
| `ECONOMIC_AND_FUNDING_BRIEF.md:42`, `ENVIRONMENT_AND_RESILIENCE.md:42`, `Final_Report.md:86`, `RISK_REGISTER.md:28`, `RISK_REGISTER.csv:16` | "~10-yr / ~10-year electronics replacement / refresh" | Equipment service life, not a planning horizon. Not a violation. |
| `ECONOMIC_AND_FUNDING_BRIEF.md:22` | Dominion "balance on-bill over **10 years**" | Financing term. |
| `ENVIRONMENT_AND_RESILIENCE.md:17` | PWC CESMP "50% GHG cut vs 2005 by **2030**; 100% renewable … by **2030**; county-wide **2035**; carbon-neutral county ops **2050**" | External adopted-policy target years, correctly attributed to EX14. Not project horizons — but they WILL trip a naive `2035|2050` grep, so Phase 1 must whitelist this line rather than "fix" it. |
| `dashboard/static/footer_log.json:6` | `"scenario": "legacy_v2 baseline scores"` | Correctly labelled legacy. |
| `excel/README.md:11` | "PWC peak-demand scenario extended **2026–2056** (**2047+** rows are a labeled CAGR extrapolation)" | Canonical span; 2047 is a data-row boundary, not a horizon. |

**CLEAN:** `dashboard/README.md`, `TABLEAU_IMPLEMENTATION_BLOCKER.md`, `presentation/README.md`, `reports/README.md`, `REGULATORY_STAKEHOLDER_MAP.md`, and the five non-canonical patch CSVs contain no horizon-convention violations. `Timing_Runbook.md` contains none either (its `2026-07-20`/`2026-07-21` are calendar dates).

## PART C2 — eGRID FACTOR SCAN (590.2 must survive nowhere; 596.3 is current)

**`590.2` — every occurrence in the entire repository (not just this lane):**
| File:Line | Context |
|---|---|
| `CHANGELOG.md:24` | "**596.3 lb CO2e/MWh** — correcting the 590.2 figure used earlier." |
| `docs/methodology/current-facts-source-register.md:7` | "**Correction:** research register EX10 carried ≈590.2; EPA's published CO2e total output rate for SRVC is 596.326 lb/MWh. All implementation artifacts use 596.3 with vintage." |
| `docs/operations/v4-program/LEDGER.md:139` | FIND-AWS-03: "Neither `596.3` nor `590.2` appears anywhere live." |
| `docs/operations/v4-program/AWS_INVENTORY.md:140` | "neither `596.3` nor `590.2` appears anywhere on the live site" |
| **`reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:27`** | "**596.3 lb CO2e/MWh**, accessed 2026-07-19 — the research package's **590.2** figure was superseded by direct EPA verification" |
| **`reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:22`** | "Correction note: the research package (EX10) carried ≈**590.2**; the implementation run verified EPA's published SRVC CO2e total output rate as 596.326 lb/MWh. **596.3 with vintage label is the value used everywhere in this implementation.**" |

Every occurrence is inside an explicit correction/supersession sentence. **No file uses 590.2 as a live value.** Two of the six are in this lane's reports. Phase 1 decision needed: the lane brief's "must survive NOWHERE" is stricter than "must not be used"; see Finding F-08.

**`596.3` — every occurrence in this lane:** `excel/README.md:16`; `dashboard/static/footer_log.json:31`; `dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md:43`; `presentation/deck/..._Timing_Runbook.md:67`; `presentation/deck/..._Speaker_Notes.md:98`; `reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:21,22,31`; `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:27,86`; `reports/milestone-2/RISK_REGISTER.md:27`; `reports/milestone-2/RISK_REGISTER.csv:13`; plus **120 rows** of `tbl_canonical_scenarios.csv` (`grid_factor_value` = `596.3` with `grid_factor_units` = `lb CO2e/MWh` and `grid_factor_vintage` = `eGRID2023r2, accessed 2026-07-19`). **Fully consistent — no drift.**

---

## PART D — DISCLAIMERS, QUOTED VERBATIM (Phase 7 must reproduce all of these in the platform)

**D1 — Final Report standing discipline** (`Future_City_Fellowship_Milestone_2_Final_Report.md:10`):
> **Standing discipline.** This project is a planning-support prototype. Nothing in this report is an engineering design, permit or code determination, utility capacity confirmation, official forecast, budget, procurement package, or construction authorization. **0 of 12 candidate sites have High data confidence; electrical capacity is a placeholder at all 12 sites.** No client endorsement, AHJ acceptance, utility confirmation, or funding award exists or is implied.

**D2 — Final Report §11 Limitations (unchanged in force)** (`Final_Report.md:126-136`), all nine, verbatim:
> 1. 0 of 12 sites have High data confidence; every electrical field is unconfirmed.
> 2. Capacity is a placeholder at 12/12 sites; no feasibility claim is permitted on it.
> 3. Demand is synthetic/uncalibrated; growth multipliers are provisional conventions.
> 4. All costs are screening-class; the $429,500-class screens are not budgets.
> 5. Emissions rest on labeled benchmark assumptions and an annually-refreshed factor.
> 6. Client Meeting #2 is prepared, not held; no client endorsement exists.
> 7. Team adoption of alternatives/MCDA/conventions is prepared, not performed.
> 8. MATLAB execution and Tableau workbook verification are blocked by tooling, stated plainly.
> 9. No AHJ, utility, facility, or fellowship confirmation of anything has occurred.

**D3 — Final Report implementation-integrity footer** (`Final_Report.md:156`):
> *Implementation integrity: no original source file, repository, or external system was modified; nothing was emailed, pushed, deployed, or published; no client, team, AHJ, utility, facility, or MATLAB-execution evidence was fabricated. Full manifests: `00_IMPLEMENTATION_MANIFEST.md`, `verification/`.*

**D4 — Final Report §3 CM2 status** (`Final_Report.md:62`, final sentence):
> **Nothing in this report converts that preparation into a held meeting or a client endorsement.**

**D5 — Final Report §4 MCDA provisionality** (`Final_Report.md:78`, final sentence):
> **These scores are researched provisional values; the team session package (`docs/human-actions/team_alternatives_session/`) exists precisely so the team can amend and adopt them honestly. No team adoption is claimed.**

**D6 — Final Report §7 trigger-policy status** (`Final_Report.md:99`, final sentence):
> **The policy is proposed configuration, not adopted municipal policy.**

**D7 — Gap Closure integrity rule** (`Milestone_2_Gap_Closure_Status.md:23`):
> Integrity rule applied throughout: **no externally dependent criterion was converted to "closed."** The nine client/team criteria hold complete action packages but remain honestly open until the humans act.

**D8 — Gap Closure "What must never be claimed until the humans act"** (`Milestone_2_Gap_Closure_Status.md:86`):
> Client endorsement or CM2 completion (A1–A4, G5) · team adoption of alternatives, scores, thresholds, or conventions (A5–A8, B7, F2) · verified electrical capacity anywhere (D1) · AHJ acceptance of any parameter (C7 validation) · MATLAB execution results · a verified Tableau workbook · any funding award.

**D9 — Economic brief discipline header** (`ECONOMIC_AND_FUNDING_BRIEF.md:5`):
> **Discipline:** **No funding is awarded, applied for, or implied.** Every source below is a candidate path requiring application, eligibility confirmation, and appropriation. The $429,500 12-site model output is a **screening value, never a budget.**

**D10 — Economic brief §6 Standing caveats** (`ECONOMIC_AND_FUNDING_BRIEF.md:52`):
> Nothing is approved; no funding is awarded; 0 of 12 sites carry High data confidence; service capacity is unconfirmed at all 12 sites; all dollar figures above are screening-class or benchmark values with sources and dates attached.

**D11 — Economic brief screening-value restatement** (`ECONOMIC_AND_FUNDING_BRIEF.md:43`):
> **The $429,500 across 12 sites sits within published benchmark ranges but remains a screening value** — it is not a budget, a request, or an estimate of record.

**D12 — Environment brief claims discipline** (`ENVIRONMENT_AND_RESILIENCE.md:5`):
> **Claims discipline:** every environmental number in this project carries a baseline definition, a factor vintage, and an assumption list. Values below labeled "benchmark" or "provisional" are planning inputs, not measurements.

**D13 — Environment brief no-resilience-claim (table cell)** (`ENVIRONMENT_AND_RESILIENCE.md:16`):
> **No battery storage is in scope (`battery_storage_flag=0` at all 12 sites), and therefore this project makes NO resilience claim.**

**D14 — Environment brief §5 explicit resilience statement** (`ENVIRONMENT_AND_RESILIENCE.md:48`):
> **No resilience claim is made in this project.** There is no battery storage at any of the 12 candidate sites, charging depends on grid availability, and severe-weather outages will interrupt service. Any future storage addition would be a scope change invoking UL 9540/9540A and NFPA 855 (2026 ed.) and a new AHJ review — at which point resilience could be evaluated, not before.

**D15 — Regulatory map naming discipline** (`REGULATORY_STAKEHOLDER_MAP.md:5`):
> **Naming discipline:** office names below reproduce only what Report 10's verified jurisdictional table states. Any office or contact not verified there is marked **"verify with jurisdiction."** No engagement material is sent in this phase.

**D16 — Regulatory map AHJ deference** (`REGULATORY_STAKEHOLDER_MAP.md:23`, final clause):
> Final interpretation of adopted editions rests with each AHJ.

**D17 — Risk register scoring discipline** (`RISK_REGISTER.md:6`):
> **Scoring discipline:** Likelihood and consequence are 1–5 **team screening judgments at pilot scale, not measured probabilities**; score = likelihood × consequence. They exist to rank attention, not to certify risk levels. Every mitigation is design intent pending AHJ/utility confirmation; nothing is approved, and service capacity is unconfirmed at 12/12 sites (0 sites carry High data confidence).

**D18 — Speaker-notes claims-discipline reminders** (`..._Speaker_Notes.md:8-14`), all seven, verbatim:
> - Never say the client **approved, endorsed, or chose** anything. Say: *"the client's interview evidence shaped the design; the compliant Client Meeting #2 follow-up is prepared, not yet held."*
> - Service **capacity is a placeholder at 12 of 12 sites** — say "pending utility/facility confirmation" any time capacity or ports come up.
> - All dollar figures are **screening-class**, never budgets or quotes.
> - The MCDA is **provisional** until the team adopts it. The proposed standard is a **fellowship design concept**, not an existing standard.
> - Virginia enforces the **2020 NEC via the 2021 USBC (eff. 2024-01-18)** — never cite the 2023 NEC as governing.
> - NEVI is volatile **upside only**; Dominion L2 is the primary candidate path, unconfirmed.
> - No MATLAB simulation results are claimed; Python contract v1.0.0 (run 2026-07-19) is the model of record.

**D19 — Runbook pre-flight negative check** (`..._Timing_Runbook.md:58`):
> - [ ] Confirm nobody's notes claim: client endorsement, a held CM2, confirmed capacity, budgets, or adopted MCDA.

**D20 — Tableau blocker status + verification statement** (`TABLEAU_IMPLEMENTATION_BLOCKER.md:3` and `:56-60`):
> **Status (2026-07-19): a verified `.twbx` presentation dashboard could NOT be produced in this environment.**

> ## Verification statement
> The original workbook (12 worksheets, 13 extracts, no dashboard/story) is byte-identical to the archive copy. Nothing in this directory claims a working `.twbx` was produced or verified in this run.

**D21 — dashboard/README Tableau line** (`dashboard/README.md:22`):
> Nothing here claims a verified workbook.

**D22 — excel/README planning-scenario disclaimer** (`excel/README.md:22-23`):
> The original source workbook is not tracked in this repository. Everything in this workbook is a planning scenario — not an official forecast or budget.

**D23 — Contract-embedded disclaimer strings** (present on all 120 rows of `tbl_canonical_scenarios.csv` / `scenario_table.csv`) — these are machine-readable disclaimers the platform can surface directly:
> `assumption_flag` = "growth multipliers provisional; demand synthetic_uncalibrated; capacity placeholder; costs screening-class; emissions benchmark assumptions"
> `capacity_source` = "legacy adapter future-ready placeholder; utility/facility confirmation pending (12/12 sites unconfirmed)"
> `expansion_trigger_status` = "awaiting_observed_data (proposed policy, not adopted)"
> `capacity_basis` = "placeholder" · `capacity_confidence` = "none" · `data_confidence` = "Low"

**D24 — Static-visual footer assumptions** (`footer_log.json`, one per chart): "0 of 12 sites have High data confidence"; "pathway = conduit/panel capacity, not installed hardware"; "growth multipliers provisional (uncalibrated); trigger-gated activation"; "screening-class benchmarks — not budgets or quotes"; "9.5 kWh/session, 0.30 kWh/mi, 400 gCO2/mi displaced — benchmark assumptions"; "fee frame ~$1k/port/yr from client operating evidence (screening)"; "demand synthetic/uncalibrated — screening only".

**D25 — Avoided-EVSE note** (all 120 rows of `tbl_avoided_evse.csv`):
> Ports kept as pathway-only capacity instead of energized hardware; avoided annual network/maintenance fees use the client's ~$1k/station/yr operating frame (screening).

---

## PART E — TABLEAU BLOCKER, QUOTED IN FULL + CAPABILITY PRE-CLASSIFICATION

### E1. `dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md` — complete text (61 lines)

```markdown
# Tableau Implementation Blocker — and the complete workaround package

**Status (2026-07-19): a verified `.twbx` presentation dashboard could NOT be produced in this environment.**

## Why this is blocked

- **Tableau Desktop is not installed** on this machine.
- **Tableau Public** (installed) was deliberately **not used**: it can only save workbooks to
  Tableau's public cloud, which would publish project data externally — prohibited by the
  no-external-side-effects rule of this run.
- Editing the packaged workbook XML blind (unzipping the original legacy workbook
  `EV_Charging_Site_Readiness_Workbook.twbx`, rewriting the XML, and repacking) was
  evaluated and rejected: without Tableau to open the result, a hand-patched `.twbx`
  cannot be verified, and the master prompt forbids claiming a valid workbook that was
  never opened. The original workbook is preserved untouched — it lives in the pre-V3
  archive branch (`archive/pre-milestone2-v3-20260719`), not in this tree.

## What exists instead (fully satisfying the presentation)

1. **Static presentation dashboard** — `dashboard/static/` (9 contract-derived
   visuals + `STATIC_DASHBOARD.pdf`), all offline-openable, all footer-labeled. This is the
   presentation-facing deliverable; the July 18 team decision and the research (static
   visuals, 86.4/100) already selected static assets as the demo strategy.
2. **Complete patch package** — `patch_package/` with contract-derived CSVs and the exact
   build recipe below, so anyone with Tableau Desktop can produce and verify
   `EV_Charging_Site_Readiness_M2_Final.twbx` in under an hour.

## Exact build recipe for a Tableau Desktop operator

Data sources (connect to all six; join nothing on names — join on `site_id`):
`tbl_sites_dimension.csv`, `tbl_canonical_scenarios.csv`, `tbl_readiness_confidence.csv`,
`tbl_portfolio_costs.csv`, `tbl_avoided_evse.csv`, `tbl_peak_waits.csv`

Worksheets (7):
1. *Readiness ranking* — bar, `readiness_score` by `site_id`, color by `data_confidence_level_v3`
   (palette: dark green #1B4332 / tan #B08948); caption: "0 of 12 sites High confidence".
2. *Starter vs pathway* — bar-in-bar, `ports_active` (2026 baseline) inside `ports_pathway_capacity`.
3. *Three horizons* — line, SUM(ports_active) by `horizon_year` for case base vs high;
   reference line y=48 "pathway ceiling".
4. *Lifecycle cost* — side-by-side bar from `tbl_portfolio_costs` (escalation_case=base),
   STG vs OVB NPV by horizon; label avoided cost on STG bars.
5. *Net CO2e* — line, SUM(net_co2e_kg)/1000 by horizon/case; caption MUST carry
   "eGRID2023 Rev 2 SRVC 596.3 lb CO2e/MWh, accessed 2026-07-19".
6. *Peak waits* — bar, p50 vs peak P90 wait, top-6 sites; reference line 10 min.
7. *Map* — `lat`/`lon` from sites dimension, size by ports_pathway, color top-3.

Dashboard: one 1600×900 dashboard, title "EV Charging Site Readiness — Milestone 2",
worksheets 1/2/4/5 + map; **filters kept minimal** (single horizon-year filter, applied
to worksheets 3–5 only). Story: 8 points in the order of the static dashboard files
01→09. EVERY sheet caption must include source + vintage + the placeholder-capacity
label where capacity appears (`capacity_basis` = placeholder at all 12 sites).

Acceptance: open without errors; every number matches `tbl_canonical_scenarios.csv`;
export dashboard as PNG/PDF and diff against `dashboard/static/`.

## Verification statement

The original workbook (12 worksheets, 13 extracts, no dashboard/story) is byte-identical
to the archive copy. Nothing in this directory claims a working `.twbx` was produced or
verified in this run.
```

### E2. Every view/feature the patch package specifies, pre-classified

Forbidden-capability list assumed (from the lane brief): stories · parameters · LOD expressions · joins/custom SQL · live connections · sets · groups · hierarchies · table calculations · reference lines · filled/choropleth maps · custom territories · map layers · spatial files · dashboard filter cards · legends · actions · floating zones · device layouts.

| # | Specified item | Verdict | Forbidden feature(s) required | Notes |
|---|---|---|---|---|
| DS | Six data sources, "**join nothing on names — join on `site_id`**" | **NOT-BUILDABLE as specified** | **joins** | Each worksheet below only ever needs ONE of the six files — except worksheet 7. If the recipe is rewritten as six independent single-table sources, the join instruction disappears and everything except #7 survives. Phase 6 should treat "no joins" as the rewrite, not a blocker. |
| WS1 | *Readiness ranking* — bar, `readiness_score` by `site_id`, colour by `data_confidence_level_v3`, palette #1B4332 / #B08948, caption "0 of 12 sites High confidence" | **BUILDABLE** | none (custom colour palette + worksheet caption are both allowed; if a **legend** must be shown it becomes NOT-BUILDABLE) | **Data caveat:** `data_confidence_level_v3` = `Low` on all 12 rows, so the colour encoding is monochrome and one of the two palette colours is never used. |
| WS2 | *Starter vs pathway* — bar-in-bar, `ports_active` (2026 baseline) inside `ports_pathway_capacity` | **BUILDABLE** | none (dual-axis + synchronised axes + a worksheet-level filter `horizon_year = 2026`) | Single source (`tbl_canonical_scenarios`). Renders 25 inside 48 at portfolio level, or per-site 2-inside-8 etc. |
| WS3 | *Three horizons* — line, `SUM(ports_active)` by `horizon_year`, base vs high; **reference line y=48 "pathway ceiling"** | **NOT-BUILDABLE as specified** | **reference lines** | The line chart itself is fine. Substitute: add a constant-48 measure as a second synchronised line, or state the ceiling in the caption. **Also a data problem:** the line will read 25→35→44→44 (base) and 25→44→48→48 (high), which visibly contradicts the deck's 44→47→47 / 47→48→48. |
| WS4 | *Lifecycle cost* — side-by-side bar from `tbl_portfolio_costs` filtered `escalation_case=base`, STG vs OVB NPV by horizon, avoided cost labelled on STG bars | **BUILDABLE** | none (worksheet filter + mark label) | Single source. Must also exclude `cost_case=DEF` or the chart shows three series, not two. The recipe does not say to exclude DEF — an omission Phase 6 should fix. |
| WS5 | *Net CO2e* — line, `SUM(net_co2e_kg)/1000` by horizon/case, caption carrying the eGRID string | **BUILDABLE** | none (a basic calculated field, not an LOD and not a table calc) | Single source. Caption text is mandated and is allowed. |
| WS6 | *Peak waits* — bar, **p50 vs peak P90**, **top-6 sites**, **reference line 10 min** | **NOT-BUILDABLE** | **reference lines**; "top-6" needs a **set** or a Top-N filter (a plain Top-N-by-field filter is allowed; an `INDEX()`-based one is a **table calculation** and is not) | **Fatal data problem independent of capability:** `p50_wait_min` = 0.0 and `peak_p90_wait_min` = 0.0 for **all 12 sites** in `tbl_peak_waits.csv`. Built exactly as written this is twelve zero-height bars. The only non-zero wait columns are `mean_wait_min` and `peak_erlang_wait_min` (PWC002 = 42.37 min). Phase 6 must either re-spec the measures or retire the view. |
| WS7 | *Map* — `lat`/`lon` from sites dimension, **size by `ports_pathway`**, **colour top-3** | **NOT-BUILDABLE** | **joins** (size measure `ports_pathway_capacity` lives in `tbl_canonical_scenarios`, not `tbl_sites_dimension`) + **sets or groups** (colour top-3) | A plain symbol map from lat/lon is NOT on the forbidden list, so the base map survives; the two encodings do not. Buildable degraded form: symbol map, uniform size, uniform colour, top-3 named in the caption. |
| DB | Dashboard 1600×900, title "EV Charging Site Readiness — Milestone 2", worksheets 1/2/4/5 + map, "**single horizon-year filter, applied to worksheets 3–5 only**" | **NOT-BUILDABLE as specified** | **dashboard filter cards** and the apply-to-worksheets mechanism (a filter **action**) | **Also internally inconsistent:** worksheet 3 is not placed on the dashboard, yet the dashboard filter is specified to apply to worksheets 3–5. Fixed-size 1600×900 with tiled zones is fine (no floating zones, no device layouts requested). |
| ST | **Story: 8 points** in the order of static dashboard files 01→09 | **NOT-BUILDABLE** | **stories** | **Also internally inconsistent:** files 01→09 is nine files, not eight. |
| CAP | "EVERY sheet caption must include source + vintage + the placeholder-capacity label" | **BUILDABLE** | none | Captions are allowed and are the substitute vehicle for the disclaimers that legends/reference lines would otherwise carry. Non-negotiable per D18/D23. |
| ACC | Acceptance: "open without errors; **every number matches `tbl_canonical_scenarios.csv`**; export dashboard as PNG/PDF and diff against `dashboard/static/`" | **UNSATISFIABLE AS WRITTEN** | n/a | `readiness_score` (WS1) and every wait column (WS6) and every portfolio-cost column (WS4) are **not in** `tbl_canonical_scenarios.csv` — that file has 48 columns and none of them is `readiness_score`, `p50_wait_min`, or `lifecycle_cost_npv_usd` at portfolio granularity. The acceptance criterion must be re-scoped to "matches its own source CSV". The PNG/PDF diff against `dashboard/static/` is also loose: two of the nine static assets (`08_limitations.png`, `09_site_map_offline.png`) have no Tableau counterpart. |

**Score: 4 of 12 specified items are BUILDABLE as written (WS1, WS2, WS4, WS5, plus the caption rule = 5 including CAP); 5 are NOT-BUILDABLE (DS-as-written, WS3, WS6, WS7, DB, ST); 1 acceptance criterion is unsatisfiable.** Two of the not-buildable views (WS3, WS6) would also expose data problems (the 35/44/44 port series and the all-zero wait percentiles) if they were built.

---

## PART F — CROSS-FILE CONSISTENCY LEDGER (what agrees, what does not)

**Agrees across all files that state it:** 0 of 12 High confidence · capacity placeholder at 12/12 · 596.3 lb CO2e/MWh + eGRID2023 Rev 2 SRVC + accessed 2026-07-19 · 25 starter / 48 pathway at 2026 · 58.8 / 54.4 / 52.1 readiness scores · $1.56M/$2.29M/$3.01M staged NPC · $1.87M/$2.64M/$3.41M broad NPC · $0.31M/$0.34M/$0.39M avoided · ≈43 / 82–113 / 130–195 / 173–260 t/yr net CO2e · 18 risks with matching L/C/score in md and csv · 52 criteria = 29+11+9+2+1 · 17 slides / 13 beats / 13:00 · 2020 NEC via 2021 USBC eff. 2024-01-18 · UL 2594 (3rd ed. 2022) + UL 3600 (2023) · Dominion 50%/100% · $885M NEVI FY26 · $429,500 screening value · MATLAB blocked, Tableau blocked, nothing deployed.

**Does not agree:** active-port series (F-01) · FFX002 confidence label (F-02) · proposed-standard module count (F-09) · `presentation/static_visuals/` vs "no duplicates" (F-07) · risk-register provenance arithmetic (F-11) · avoided-EVSE range (F-04).

---

## PART G — FILES ASSIGNED AND READ

All 15 assigned text files were read in full:
1. `dashboard/README.md` (23 L)
2. `dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md` (61 L)
3. `dashboard/static/footer_log.json` (63 L)
4. `dashboard/tableau/patch_package/tbl_avoided_evse.csv` (122 L)
5. `dashboard/tableau/patch_package/tbl_canonical_scenarios.csv` (121 L × 48 cols — full programmatic column/row analysis)
6. `dashboard/tableau/patch_package/tbl_peak_waits.csv` (14 L)
7. `dashboard/tableau/patch_package/tbl_portfolio_costs.csv` (29 L)
8. `dashboard/tableau/patch_package/tbl_readiness_confidence.csv` (14 L)
9. `dashboard/tableau/patch_package/tbl_sites_dimension.csv` (14 L)
10. `excel/README.md` (24 L)
11. `presentation/README.md` (22 L)
12. `presentation/deck/Future_City_Fellowship_Milestone_2_Speaker_Notes.md` (132 L)
13. `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md` (69 L)
14. `reports/README.md` (18 L)
15. `reports/milestone-2/ECONOMIC_AND_FUNDING_BRIEF.md` (53 L)
16. `reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md` (49 L)
17. `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md` (157 L)
18. `reports/milestone-2/Milestone_2_Gap_Closure_Status.md` (87 L)
19. `reports/milestone-2/REGULATORY_STAKEHOLDER_MAP.md` (47 L)
20. `reports/milestone-2/RISK_REGISTER.md` (37 L)
21. `reports/milestone-2/RISK_REGISTER.csv` (20 L)

**Not read (binary / out of lane, listed for completeness):** `dashboard/static/*.png` (9), `dashboard/static/STATIC_DASHBOARD.pdf`, `excel/Electric_Data_Milestone_2_Updated.xlsx` (container inspected only — sheet names), `presentation/assets/10_mcda_provisional.png`, `presentation/deck/*.pptx` and `*.pdf` (3), `reports/milestone-2/*.docx` (4) and `*.pdf` (1). None of these was assigned as a text read.

**Read-only compliance:** no file under `repo/` or `incoming/explorer/fcf-3d` was created, modified, or deleted. The only writes were to the scratchpad.

---

## PART H — FINDINGS (referenced as F-nn above)

### F-01 — HIGH — The published active-port series does not exist in the contract
Every headline artifact publishes base path `25 → 44 → 47 → 47` and high path `25 → 47 → 48 → 48`.
Sum of `ports_active` over the 12 sites in `dashboard/tableau/patch_package/tbl_canonical_scenarios.csv`
(byte-identical to `data/contract/v1/scenario_table.csv`, md5 `2beff3f46e8f86b43427d47b7e8efab6`) is:

| horizon | base | high | stress_combined |
|---|---:|---:|---:|
| 2026 (`baseline`) | 25 | — | — |
| 2036 | **35** | **44** | 44 |
| 2046 | **44** | **48** | 48 |
| 2056 | **44** | **48** | 48 |

`47` is not a portfolio total at any horizon under any case. The published "base" series is closer to the
contract's **high** series, shifted. Affected lines:
- `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:38-40`
- `presentation/deck/Future_City_Fellowship_Milestone_2_Speaker_Notes.md:74`
- `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md:67` (the QA spot-check string, i.e. the
  checklist step that is supposed to *catch* this instead canonises it)
- `README.md:39-41` (repo root — outside this lane but same defect, recorded for Phase 1 completeness)

Directly contradicts `reports/README.md:17` — "Every number traces to `data/contract/v1` (contract v1.0.0,
generated 2026-07-19)."

### F-02 — HIGH — FFX002 is published as "Medium confidence"; the contract says Low, for all 12 sites
`tbl_readiness_confidence.csv` gives `data_confidence_score_v3 = 33.8`, `data_confidence_level_v3 = Low` on
**all 12 rows**, and `tbl_canonical_scenarios.csv` gives `data_confidence = Low` on **all 120 rows**. But:
- `Future_City_Fellowship_Milestone_2_Final_Report.md:51` — "FFX002 City of Fairfax Regional Library #1 at 58.8 (**Medium**)"
- `..._Speaker_Notes.md:63` — "FFX002 … leads at 58.8 (**Medium confidence**)"
- `README.md:47` (repo root) — "**FFX002 — City of Fairfax Regional Library (58.8, Medium confidence)**"

Most likely a surviving V2 legacy label. Note the speaker notes then say at L64 "The '**Low**' labels are printed
on the chart deliberately" — the same document asserts both values one line apart.

### F-03 — HIGH — Horizon-convention drift is baked into the contract itself
`horizon_label` in `tbl_canonical_scenarios.csv` / `data/contract/v1/scenario_table.csv` takes the values
`now`, `plus10`, `plus20`, `plus30` on rows whose `model_mode` is `milestone2_v3` — not `legacy_v2`. Any
platform view that renders `horizon_label` will display exactly the vocabulary the horizon rule prohibits.
**F-03b (medium):** two prose instances with no canonical-year pairing and no legacy label —
`..._Speaker_Notes.md:131` ("Adama has the **30-year** numbers") and
`Future_City_Fellowship_Milestone_2_Final_Report.md:152` ("how to keep a **30-year** model honest when
**10-year** goals are already off-track").
**F-03c (medium):** `Future_City_Fellowship_Milestone_2_Final_Report.md:92` — a bare "**2050**-base/high port
mismatch", describing a historical defect in the retired hand-built MATLAB CSV, unlabelled.

### F-04 — MEDIUM — "13–23 pathway ports not energized" quotes only two of four horizons
`Future_City_Fellowship_Milestone_2_Final_Report.md:86`. Portfolio sums of
`avoided_active_evse_ports` on the base path in `tbl_avoided_evse.csv`: **2026 = 23, 2036 = 13, 2046 = 4,
2056 = 4**. The stated range excludes the 2046/2056 value entirely. Note that 2036 base = 13 avoided
arithmetically confirms 48 − 35 = 13, i.e. the avoided-EVSE file independently corroborates F-01's
finding that the contract's 2036 base port total is 35, not 44.

### F-05 — HIGH — The specified Tableau peak-waits view has no data
`tbl_peak_waits.csv` has `p10_wait_min`, `p50_wait_min`, `p90_wait_min` and `peak_p90_wait_min` = `0.0` on
**all 12 rows**. `TABLEAU_IMPLEMENTATION_BLOCKER.md:44` specifies worksheet 6 as "bar, **p50 vs peak P90**
wait, top-6 sites; reference line 10 min" — twelve zero-height bars. The static visual
`dashboard/static/07_peak_wait.png` presumably plots something else (not read; binary).

### F-06 — MEDIUM — "P90 waits sit under the 10-minute target at every top site" is a fragile claim
`Future_City_Fellowship_Milestone_2_Final_Report.md:84`. It is literally true only because every P90 column
is 0.0 (F-05). Meanwhile `tbl_peak_waits.csv:4` gives PWC002 `peak_erlang_wait_min` = **42.365 min**, and
`tbl_canonical_scenarios.csv` contains **21 rows with `peak_wait_minutes` > 10**, maximum **215.35 min**
(`PWC002_2046_base`), plus 19 rows with `average_wait_minutes` > 10, maximum 68.72. Five `peak_wait_minutes`
cells are blank, all PWC002 (`PWC002_2046_high`, `PWC002_2046_stress_combined`, `PWC002_2056_base`,
`PWC002_2056_high`, `PWC002_2056_stress_combined`) — a silent gap in the worst-performing site.

### F-07 — MEDIUM — Broken path + contradiction about where the static visuals live
`..._Timing_Runbook.md:65` — "Open all **11 files** in `static_visuals/` directly". No directory named
`static_visuals` exists anywhere in the repository (`find` returns zero matches). The count 11 matches the
contents of `dashboard/static/` (9 PNGs + `footer_log.json` + `STATIC_DASHBOARD.pdf`). Compounding it,
runbook L62 says "Copy the whole `presentation/` folder to the presentation machine" and
`Future_City_Fellowship_Milestone_2_Final_Report.md:124` says the presentation has "self-contained static
visuals (`presentation/`)" — but `presentation/` contains exactly one image
(`assets/10_mcda_provisional.png`), and `presentation/README.md:15-16` explicitly states "The nine shared data
visuals live in `dashboard/static/` — **single source, no duplicates**." The offline-open QA step therefore
cannot be executed as written.

### F-08 — MEDIUM — `590.2` survives in two report-tier documents (as a labelled correction)
`reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:22` and
`reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:27`. Both occurrences are inside an
explicit supersession sentence and both immediately assert 596.3 as the operative value, so nothing computes
from 590.2. But the lane rule is "596.3 is current; 590.2 was corrected away and must survive NOWHERE" —
Phase 1 must make an explicit decision: keep the correction notes (audit value) or strike the number and
describe the correction without restating the wrong figure. Same question applies to `CHANGELOG.md:24` and
`docs/methodology/current-facts-source-register.md:7`.

### F-09 — MEDIUM — Proposed standard: three modules or seven?
`..._Speaker_Notes.md:88` — "*Municipal EV Charging Site Readiness and Emergency Access Standard*, **three
modules**". `Future_City_Fellowship_Milestone_2_Final_Report.md:105` and
`Milestone_2_Gap_Closure_Status.md:53` (C7) both say "**seven test modules**".
`ENVIRONMENT_AND_RESILIENCE.md:44` cites "proposed-standard **Module 7**", which only exists if there are
seven. The speaker will say the wrong number out loud.

### F-10 — LOW — "Alternative C degrades gracefully" as the pilot-only budget floor
`ECONOMIC_AND_FUNDING_BRIEF.md:36` and `RISK_REGISTER.csv:19` (R18) both describe the budget-shortfall floor
as "pilot-only deployment — Alternative C degrades gracefully". In
`Future_City_Fellowship_Milestone_2_Final_Report.md:73`, **C = "EV-ready-first (pathways only)"** while
**B = "Distributed staged pilots"**. "Pilot-only" reads like B, not C. The two economics documents agree with
each other, so this may be intentional (C = install nothing, keep pathways) — flagged as **uncertain**, needs
a one-line check against the alternatives source.

### F-11 — LOW — Risk-register provenance arithmetic does not close
`RISK_REGISTER.md:5` — "upgraded from … `FAILURE_MITIGATION_OPTIONS.csv` (… **15 assessed failure modes**)
plus **four** cross-cutting risks from Reports 07–10: ADA redesign, overbuild/underuse, trenching cost
escalation, data staleness, and funding volatility." The list contains **five** items, and neither 15+4 nor
15+5 equals the register's 18 rows. In `RISK_REGISTER.csv`, R01–R16 all carry `FAILURE_MITIGATION_OPTIONS`
row citations (16, not 15) and only R17/R18 do not — so the true decomposition looks like 16 + 2.

### F-12 — MEDIUM — Absolute local paths (and a stale directory) in a tracked, verified artifact
`dashboard/static/footer_log.json`, all nine entries, key `file`:
`/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/<name>.png`.
This leaks a local username and a directory tree that does not exist in the repo. It does not break the
footer QA gate because `src/fcf_m2/visuals.py:76` matches on `Path(e["file"]).name` only, but it should be
regenerated to repo-relative paths. No secrets, tokens, AWS account IDs, or keys were found anywhere in this
lane.

### F-13 — MEDIUM — Referenced deliverables that do not exist
- `Future_City_Fellowship_Milestone_2_Final_Report.md:156` — "Full manifests: `00_IMPLEMENTATION_MANIFEST.md`,
  `verification/`." **Neither exists** anywhere in the tree.
- `Future_City_Fellowship_Milestone_2_Final_Report.md:8` — "**Supersedes:**
  `Future_City_Fellowship_Milestone_2_Phase_Report.md` … that report remains the authoritative record of the
  Phase 2 build." **Not in the tree** (plausibly archived, but the sentence points readers at nothing).
- `Milestone_2_Gap_Closure_Status.md:46,69` cite `lifecycle_costs.csv` and `:64` cites
  `avoided_evse_metric.csv` as contract evidence; both exist at `data/outputs/v3_run/`, **not** under
  `data/contract/v1/`. Minor path imprecision.
- `dashboard/README.md:8` names `verify.sh`; the file is `scripts/verify.sh`. The behavioural claim is TRUE
  (`scripts/verify.sh:49-53` runs the footer gate) — only the path is loose.
- `RISK_REGISTER.md:5,35` cite `FAILURE_MITIGATION_OPTIONS.csv` and correctly state it is "**not tracked in
  this repository**" — honest, not a defect.
- Verified present and correct: all six `docs/human-actions/*` packages, both `docs/standards/*.md`,
  `docs/architecture/TECHNICAL_INTEGRATION_ARCHITECTURE.md`, `docs/assets/architecture/`,
  `docs/operations/website-patch-package/`, `matlab/`, `scripts/build_static_dashboard.py`,
  `scripts/build_excel_workbook.py`, `Makefile` targets `run-v3` / `dashboard` / `verify`.

### F-14 — MEDIUM — The Tableau recipe is internally inconsistent, before any capability boundary is applied
(a) `TABLEAU_IMPLEMENTATION_BLOCKER.md:48-49` — the dashboard contains "worksheets 1/2/4/5 + map" but the
single horizon-year filter is specified as "applied to **worksheets 3–5** only"; worksheet 3 is not on the
dashboard. (b) L49-50 — "Story: **8 points** in the order of the static dashboard files **01→09**" — that is
nine files. (c) L53 acceptance — "every number matches `tbl_canonical_scenarios.csv`", but `readiness_score`
(WS1), the wait percentiles (WS6) and the portfolio NPVs (WS4) are **not columns of that file**. (d) L54 —
"diff against `dashboard/static/`", but two of the nine static assets (`08_limitations.png`,
`09_site_map_offline.png`) have no worksheet counterpart. See Part E2 for the full BUILDABLE /
NOT-BUILDABLE classification.

### F-15 — LOW — Headline numbers with no contract trace
Phase 1 should chase these specifically: `86.4/100` static-visuals research score
(`TABLEAU_IMPLEMENTATION_BLOCKER.md:23`); `$429,500` 12-site screening cost (`ECONOMIC_AND_FUNDING_BRIEF.md:5,43`,
`Final_Report.md:131`, `RISK_REGISTER.md:14`, `RISK_REGISTER.csv:18`) — it is **not** any value in
`tbl_portfolio_costs.csv`, whose base-case NPVs are 1.56M / 2.29M / 3.01M; `38 REVIEW + 12 INFO` findings
(`Speaker_Notes.md:64`, `Final_Report.md:22,51`); `15` Tableau exports and `35`-file package
(`Final_Report.md:22,51`); `80 tests, 92% coverage` (`Final_Report.md:23`); `six live reconciliation checks all
PASS` (`excel/README.md:18`, `Final_Report.md:119`); growth multipliers `1.9/2.6 → 3.0/4.5 → 4.0/6.0, ×1.15`
(`Final_Report.md:84`); the `ten` reconciliation tests (`Final_Report.md:92`); `8`-interface register
(`Final_Report.md:109`). None of these is a column in any of the six patch-package CSVs.

### F-16 — LOW — `tbl_portfolio_costs.csv` DEF case is suspiciously constant
All nine `DEF` rows carry `lifecycle_cost_nominal_usd` = `lifecycle_cost_npv_usd` = **617,403.0**, identical
across 2036/2046/2056 and across low/base/high escalation, with nominal exactly equal to NPV (i.e. no
discounting and no escalation applied). Worth a generator check in Phase 1; it is not quoted in any prose in
this lane, so it is a latent rather than an active defect.

### F-17 — LOW — Stale-at-authoring funding date
`ECONOMIC_AND_FUNDING_BRIEF.md:25,35`, `Final_Report.md:112`, `RISK_REGISTER.csv:19` — "Virginia solicitations
**anticipated Q1 2026**" in documents dated **2026-07-19**. The brief hedges it ("status to re-verify"), so it
is honest but overdue for refresh; Phase 9 framing should not present it as forward-looking.

### F-18 — INFO — Things this lane VERIFIED as true (do not "fix" these)
- No `.twbx` exists anywhere in the tree, and `remotes/origin/archive/pre-milestone2-v3-20260719` does exist —
  `TABLEAU_IMPLEMENTATION_BLOCKER.md` is honest about the blocker.
- `tbl_canonical_scenarios.csv` is a **byte-identical copy** of `data/contract/v1/scenario_table.csv`
  (md5 `2beff3f46e8f86b43427d47b7e8efab6`); `tbl_sites_dimension.csv` is a byte-identical copy of
  `data/contract/v1/site_table.csv` (md5 `92f19e6b6ad33e979fbf2869d856a771`). Neither has drifted from its
  generator.
- The cost headline series and the CO2e headline series both trace exactly to the contract.
- `avoided = OVB NPV − STG NPV` holds exactly at all three horizons.
- "The staged plan costs less than broad buildout at every horizon under every escalation case"
  (`Final_Report.md:86`) — TRUE: STG NPV < OVB NPV in all 9 horizon × escalation combinations.
- `RISK_REGISTER.md` and `RISK_REGISTER.csv` agree row-for-row on all 18 likelihood/consequence/score triples.
- Gap-closure counts close: 13+22+17 = 52 prior; 29+11+9+2+1 = 52 final; 9 "Ready for human action" rows and
  2 "Partially implemented" rows are countable in the table.
- The MCDA weights 25/20/20/15/10/10 sum to 100.
- The runbook per-slide budget sums to exactly 13:00.
- `596.3` is consistent in all 13 prose/config occurrences plus all 120 contract rows; no drift.
- No secrets, tokens, AWS account IDs, or credentials appear anywhere in this lane.
