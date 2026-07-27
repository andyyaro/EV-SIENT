# FINDINGS_REGISTER.md — every finding from the Phase 0 read

**200 findings** raised by twelve independent reader lanes over **224 files**, every assigned file read end to
end (**zero** files reported as not fully read). This is the complete register; `LEDGER.md` carries the
subset the program lead independently confirmed and the plan for acting on each.

> **Every finding here is a lead, not a fact.** Per the program's subagent doctrine, nothing is acted on
> until it is independently confirmed against the actual files. The `Confirmed` column records whether the
> lead has verified it first-hand yet. Unconfirmed does not mean doubted — it means not yet re-checked.

| Severity | Count |
|---|---|
| high | 41 |
| medium | 66 |
| low | 48 |
| info | 45 |
| **total** | **200** |

### Lane coverage

| Lane | Files read | high | medium | low | info | Not fully read |
|---|---:|---:|---:|---:|---:|---:|
| L01-model-core | 23 | 1 | 8 | 5 | 1 | 0 |
| L02-tests-scripts | 15 | 3 | 4 | 5 | 4 | 0 |
| L03-matlab-src | 9 | 3 | 8 | 4 | 4 | 0 |
| L04-matlab-tests-docs | 14 | 2 | 1 | 4 | 6 | 0 |
| L05-data-contract | 18 | 4 | 7 | 4 | 6 | 0 |
| L06-root-ci | 10 | 3 | 6 | 3 | 3 | 0 |
| L07-docs-core | 22 | 2 | 3 | 3 | 2 | 0 |
| L08-human-actions | 37 | 2 | 5 | 2 | 4 | 0 |
| L09-deliverables | 21 | 4 | 9 | 3 | 1 | 0 |
| L10-explorer-python | 12 | 6 | 3 | 6 | 5 | 0 |
| L11-explorer-web | 5 | 8 | 7 | 6 | 4 | 0 |
| L12-binaries | 38 | 3 | 5 | 3 | 5 | 0 |

---

## HIGH — 41 findings

### H-01 · `src/fcf_m2/scoring.py`
**Lane:** L01-model-core · **Category:** duplicate-scorer · **Confirmed:** not yet re-checked by the lead

**Claim.** SUBSCORE_WEIGHTS, DRIVERS, and the 'Earned:/Forgone:' driver attribution do NOT exist anywhere in repo/ — they exist only in the separate 3D explorer, which independently re-implements the scoring weights. This violates 'nothing else may re-implement the scorer' and is a live drift risk: the numbers agree today only by coincidence of hand-copying.

**Evidence.** grep -rn 'SUBSCORE_WEIGHTS|DRIVERS|Earned:|Forgone:' over repo/ (excluding .git, venv) returns ZERO hits. In incoming/explorer/fcf-3d/fcf3d/build_sites.py:92-97 `SUBSCORE_WEIGHTS = {"demand_subscore": 0.45, "feasibility_subscore": 0.30, "safety_subscore": 0.15, "equity_subscore": 0.10}`; lines 134-148 define `DRIVERS: list[Driver]` with weights 0.18/0.18/0.13/0.11/0.10/0.08/0.07; lines 238-248 compute `possible = SUBSCORE_WEIGHTS[drv.subscore] * drv.weight * 100.0 * adj`, `points_earned`, `points_forgone`. In repo/src/fcf_m2/scoring.py:140-175 the identical numbers appear as inline literals with no named constant. Also present in incoming/explorer/fcf-3d/web/app.js.

### H-02 · `dashboard/static/footer_log.json`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** yes — LEDGER FIND-REPO-03

**Claim.** scripts/verify.sh gate 8 ("hygiene: no local absolute paths in code/config") FAILS on the tree as committed, because the tracked dashboard/static/footer_log.json contains nine absolute /Users/andyyaro/... paths and the gate's pathspec includes '*.json'.

**Evidence.** dashboard/static/footer_log.json lines 7,14,21,28,35,42,49,56,59 each contain "file": "/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/0X_*.png". scripts/verify.sh:60 = `! git grep -nI '/Users/andyyaro' -- '*.py' '*.sh' '*.toml' '*.yml' '*.json' ':!scripts/verify.sh'`. I ran that exact command: exit 1 (FAIL).

### H-03 · `scripts/verify.sh`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** yes — LEDGER FIND-REPO-01/02

**Claim.** scripts/verify.sh gate 7 ("secrets") FAILS on a self-inflicted false positive: it lacks the ':!.github/workflows/tests.yml' exclusion that CI's identical scan has, and tests.yml contains the literal 'aws_secret_access_key' inside its own pattern.

**Evidence.** scripts/verify.sh:57 excludes only ':!scripts/verify.sh'; .github/workflows/tests.yml:57 excludes both ':!.github/workflows/tests.yml' and ':!scripts/verify.sh'. The grep matches .github/workflows/tests.yml:57. I ran verify.sh's exact gate command: exit 1 (FAIL). So ./scripts/verify.sh reports 2 FAIL / 8 PASS today.

### H-04 · `scripts/build_static_dashboard.py`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** dashboard/static/ is a committed generated artifact that did NOT come from scripts/build_static_dashboard.py in this repo — its footer log records a different machine's directory tree — and the footer-QA gate cannot detect this because it compares basenames only.

**Evidence.** build_static_dashboard.py:24-26 sets OUT = REPO/'dashboard/static' and LOG = OUT/'footer_log.json'; the committed log's file entries all point at '/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/'. src/fcf_m2/visuals.py:76 = `logged = {Path(e["file"]).name for e in ...}` — basename-only, so verify.sh gate 6 passes anyway (I ran it: exit 0).

### H-05 · `matlab/src/capacityGuard.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** yes — LEDGER FIND-MATLAB-02

**Claim.** Octave Tier 1 (unmodified .m) is provably unreachable, and the failure mode in the safety-critical gates is SILENT rather than loud: 14 string-array literals of the form ["a","b"] collapse to a single concatenated char row under Octave, which mangles the capacity-provenance vocabulary check and the strategy check.

**Evidence.** capacityGuard.m:53 `allowedBases = ["verified_utility", "verified_facility", ...` consumed at :76 `if ~ismember(basis, allowedBases)` and :84 `isVerified = ismember(basis, ["verified_utility", "verified_facility"]);`; managedCharging.m:57 `validStrategies = ["unmanaged", "clamp", "energy_aware"];` consumed at :59. 14 total sites: capacityGuard.m:53,60,84; loadScenarios.m:62,81; makeSessionProfiles.m:68,71,158,219,299; managedCharging.m:57; run_all_scenarios.m:51; runScenario.m:47,51

### H-06 · `matlab/src/plotScenario.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** plotScenario's mandatory provenance footer HARD-CODES the source CSV path as a literal string instead of echoing the CsvFile actually used, so any batch run against a different CSV produces figures that state a source they did not use — a provenance defect inside the file whose whole stated purpose is provenance labelling.

**Evidence.** plotScenario.m:180-183 `footer = sprintf("Source: data/canonical/matlab_scenarios.csv " + "(auto-generated adapter) | scenario %s | capacity basis: %s " + "| generated %s | Milestone 2 V3 MATLAB model", ...)` — no CsvFile argument is available to plotScenario at all (its only options are OutputFolder/SaveFigure/Visible, :31-37), while run_all_scenarios.m:45-47 exposes a settable 'CsvFile'.

### H-07 · `matlab/src/run_all_scenarios.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** yes — LEDGER FIND-MATLAB-04

**Claim.** The SHA-256 provenance hashing that produces the named deliverable hashes.txt depends on the Java bridge, which is absent under `matlab -nojvm` and absent in stock Octave. This is a hard Tier-2 blocker on the batch runner.

**Evidence.** run_all_scenarios.m:194-197 `md = java.security.MessageDigest.getInstance("SHA-256"); md.update(bytes); digest = typecast(md.digest(), "uint8");` — docstring at :19-21 claims it is "computed with java.security.MessageDigest - available in base MATLAB".

### H-08 · `.github/workflows/matlab-manual.yml`
**Lane:** L04-matlab-tests-docs · **Category:** ci-defect · **Confirmed:** not yet re-checked by the lead

**Claim.** The matlab-manual CI workflow makes test_regression permanently self-baselining: the golden file it creates in CI is never uploaded or committed, so drift can never be detected from CI.

**Evidence.** matlab/tests/test_regression.m:45-53 writes tests/golden/regression_golden.csv when absent then passes against it ('if ~isfile(goldenFile) ... writetable(current, goldenFile); log(testCase, 1, sprintf("GOLDEN CREATED at %s - commit this file..."))'). RUN_ON_LICENSED_MATLAB.md:29-30 says '**Commit that file** - it becomes the drift baseline for every later run.' But .github/workflows/matlab-manual.yml:50-53 uploads only 'matlab/test-results/' and 'matlab/outputs/' - matlab/tests/golden/ is absent from the artifact paths.

### H-09 · `matlab/data/canonical/matlab_scenarios.csv`
**Lane:** L04-matlab-tests-docs · **Category:** exposure-blocker · **Confirmed:** yes — LEDGER FIND-MATLAB-06

**Claim.** The canonical CSV cannot be published in a public harness repo as-is: it carries client identity plus four columns of study results attached to 12 named public facilities.

**Evidence.** matlab/data/canonical/matlab_scenarios.csv col 3 site_name = 12 real facilities incl. 'City of Fairfax Regional Library', 'Prince William County Public Safety Training Center', 'PWC McCoart Government Center'; col 2 site_id = FFX001-FFX004/PWC001-PWC008 (county prefixes); col 20 model_rank = 1..12, one per site (DATA_DICTIONARY.md:39 'Python site-ranking model | Portfolio priority rank of the site'); col 21 electrical_risk_level = high on PWC001/PWC002/PWC003, medium on 9 (DATA_DICTIONARY.md:40 'Python electrical-risk screen'); col 6 ports 2-8 (DATA_DICTIONARY.md:25 'Python right-sizing model ... Recommended charging ports'); col 17 sessions_per_day 0.3-15.73, 120 distinct; cols 12-13 base_load_mean/peak_kW 50.2-115.0 / 66.3-151.8; col 11 capacity_source contains '12/12 sites unconfirmed'.

### H-10 · `data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv`
**Lane:** L05-data-contract · **Category:** headline-not-traceable-to-contract · **Confirmed:** not yet re-checked by the lead

**Claim.** The 58.8 headline readiness score does NOT trace to data/contract/v1/. There is no readiness/score column anywhere in the contract — not in scenario_table.csv (48 cols), site_table.csv (9 cols), or schema.json's 48 required fields. Its sole data-layer origin is a frozen legacy_v2 INPUT. This directly violates the contract's own consumer rule 3 ('Presentation numbers cite contract_version + generated_utc from the manifest', data/contract/v1/README.md:20) and rule 'Excel/Tableau/presentation quote contract values; no re-derivation' (contract_manifest.json:48), which ~13 prose files breach by quoting 58.8.

**Evidence.** Exhaustive grep for '58.8' across data/ returns exactly ONE hit: data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv:2 → 'FFX002,City of Fairfax Regional Library,1,58.8,medium,6.0,...' where col 4 is base_readiness_score. Confirmed programmatically: scenario_table.csv has no score column; its 48 headers are contract_version…notes. Re-published outside the contract at dashboard/tableau/patch_package/tbl_readiness_confidence.csv:2 (readiness_score=58.8). Quoted in prose by README.md, CHANGELOG.md, CONTRIBUTING.md, docs/migration-from-v2.md, docs/operations/reproduction-guide.md, docs/operations/legacy-baseline/BASELINE_VERIFICATION.md, docs/operations/website-patch-package/content/methodology_update.md, .github/pull_request_template.md, presentation/deck/*Speaker_Notes.md, presentation/deck/*Timing_Runbook.md, reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md, scripts/build_static_dashboard.py, tests/test_legacy_golden.py.

### H-11 · `data/contract/v1/scenario_table.csv`
**Lane:** L05-data-contract · **Category:** internal-contradiction · **Confirmed:** yes — LEDGER FIND-NUM-01/02

**Claim.** The expected 'FFX002 = Medium confidence' is FALSE against the data. All 10 FFX002 contract rows carry data_confidence=Low, as do all 120 rows. The only 'medium' attached to FFX002 anywhere is electrical_risk_level=medium in the frozen legacy file — a different variable. Any prose pairing '58.8' with 'Medium confidence' is conflating electrical-risk-level with data-confidence.

**Evidence.** scenario_table.csv col 42 data_confidence distinct value set across all 120 rows = {'Low'} (verified via csv.DictReader + Counter). All 10 FFX002 rows: data_confidence='Low'. dashboard/tableau/patch_package/tbl_readiness_confidence.csv:2 gives FFX002 data_confidence_score_v3=33.8, data_confidence_level_v3='Low'. The 'medium' token is legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv:2 col 5 electrical_risk_level='medium' with electrical_risk_points=6.0.

### H-12 · `data/provenance/site_coordinate_sources.csv`
**Lane:** L05-data-contract · **Category:** internal-contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** Two provenance files directly contradict each other on coordinate source quality for 6 sites, and the file that FEEDS THE CONTRACT is the pessimistic one. field_provenance_v1.csv (hashed manifest input #3) marks coordinates as 'public_web_reference / replace with official GIS' for all 12 sites; site_coordinate_sources.csv marks PWC001-004 and FFX001-002 as 'Official', verified from county GIS address-point layers. One of these is wrong.

**Evidence.** data/provenance/field_provenance_v1.csv:6 'PWC001,coordinates,public_web_reference,spot_checked,public web mapping (replace with official GIS),2026-06-24,...' (same for all 12 sites, lines 6,13,20,27,34,41,48,55,62,69,76,83). vs data/provenance/site_coordinate_sources.csv:2 'PWC001,...,Prince William County GIS Premise Addresses,Prince William County Department of Information Technology GIS Division,Official,address and coordinates verified from countywide address point layer'. The contradiction propagates into data/contract/v1/source_provenance.csv:6 (identical text), which is hashed as contract table #4.

### H-13 · `data/observed/observed_sessions_template.csv`
**Lane:** L05-data-contract · **Category:** schema-insufficient-for-stated-purpose · **Confirmed:** not yet re-checked by the lead

**Claim.** The observed-sessions template is structurally insufficient to evaluate the expansion-trigger policy it exists to feed. It captures 6 fields with no port/charger id, no session timestamps, no uptime and no curtailment — but assumptions.json defines the trigger on utilization_threshold 0.4, wait_threshold_min 10.0 AND reliability_uptime_min 0.97. Uptime is uncomputable from this schema; utilisation and wait can only be approximated. This is the central Phase-4 design gap.

**Evidence.** data/observed/observed_sessions_template.csv in full (102 bytes): header 'site_id,date,sessions,energy_kwh,mean_dwell_min,facility_visitors_day' + row 'FFX002,2026-08-01,2,19.0,95,310'. Against data/contract/v1/assumptions.json:71-85 trigger_policy: utilization_threshold 0.4, wait_threshold_min 10.0, reliability_uptime_min 0.97, min_observation_months 6. Also the example row is circular: 19.0 kWh / 2 sessions = 9.5 kWh/session, exactly the energy_per_session_kwh benchmark at assumptions.json:33.

### H-14 · `README.md`
**Lane:** L06-root-ci · **Category:** headline-number-untraceable · **Confirmed:** yes — LEDGER FIND-NUM-01/02, FIND-REPO-08

**Claim.** The README headline table's "Active ports (base → high path)" column (44 → 47 / 47 → 48 / 47 → 48) does not trace to data/contract/v1. Summing ports_active across the 12 sites gives base path 25 → 35 → 44 → 44 and high path 25 → 44 → 48 → 48. The value 47 appears nowhere in the contract. Every other number in that table reconciles exactly.

**Evidence.** README.md:39-41 '| 2036 | 44 → 47 | $1.56M | ...', '| 2046 | 47 → 48 | ...', '| 2056 | 47 → 48 (48-port pathway ceiling) | ...' vs computed sums of data/contract/v1/scenario_table.csv: (2036,base)=35, (2036,high)=44, (2046,base)=44, (2046,high)=48, (2056,base)=44, (2056,high)=48; `grep -c ',47,' data/contract/v1/scenario_table.csv` = 0. Same sums reproduce in dashboard/tableau/patch_package/tbl_canonical_scenarios.csv and matlab/data/canonical/matlab_scenarios.csv.

### H-15 · `scripts/verify.sh`
**Lane:** L06-root-ci · **Category:** gate-claims-false · **Confirmed:** yes — LEDGER FIND-REPO-01/02

**Claim.** scripts/verify.sh does NOT pass on the pristine committed tree — two of its ten gates fail — yet README, CONTRIBUTING, CHANGELOG and the PR template all assert it passes or must pass. Gate 'secrets' fails because verify.sh excludes only itself, not .github/workflows/tests.yml, whose line 57 contains the literal string aws_secret_access_key. Gate 'hygiene: no local absolute paths' fails on dashboard/static/footer_log.json.

**Evidence.** scripts/verify.sh:57 `! git grep -nIiE '...|aws_secret_access_key|...' -- . ':!scripts/verify.sh'` matches .github/workflows/tests.yml:57 (re-ran read-only, git grep exit 0 = match). scripts/verify.sh:60 `! git grep -nI '/Users/andyyaro' -- '*.py' '*.sh' '*.toml' '*.yml' '*.json' ':!scripts/verify.sh'` matches dashboard/static/footer_log.json lines 7,14,21,28,35,42,49,56,59. Claims: README.md:116-120, CONTRIBUTING.md:11 'must pass before you open a PR', CHANGELOG.md:43, .github/pull_request_template.md:22.

### H-16 · `dashboard/static/footer_log.json`
**Lane:** L06-root-ci · **Category:** absolute-local-path · **Confirmed:** yes — LEDGER FIND-REPO-03

**Claim.** Nine absolute local paths from the author's machine are committed in a tracked JSON file, pointing at a build directory that is not this repository.

**Evidence.** dashboard/static/footer_log.json:7 '"file": "/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/01_readiness_ranking.png"' and the same pattern at lines 14,21,28,35,42,49,56,59. (fcf_m2.visuals.audit_footer_metadata keys on Path(e['file']).name, src/fcf_m2/visuals.py:76, so the footer QA still passes — it is pure leakage.)

### H-17 · `docs/operations/website-patch-package/content/results_2036_2046_2056.md`
**Lane:** L07-docs-core · **Category:** headline-number-does-not-trace-to-contract · **Confirmed:** yes — LEDGER FIND-NUM-01

**Claim.** The three-horizon active-ports table published to the website says 44→47 / 47→48 / 47→48, but data/contract/v1/scenario_table.csv aggregates to 35→44 / 44→48 / 44→48. The same file claims 'All values from canonical contract v1.0.0' and PATCH_GUIDE.md mandates every number on that page trace to the scenario table. The file also self-contradicts: its closing line says the staged plan avoids energizing '13–23 pathway ports', and 13 avoided against a 48 ceiling implies 35 active at 2036 — the contract value, not the printed 44. Same wrong figures also appear in root README.md:38-40, reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:36-39, and presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md:67 (which enshrines '44→47 & 47→48' in the deck's spot-check list). The CO2e columns in the same rows DO match the contract, so the error is isolated to the ports column. No verify.sh or CI gate compares prose headline numbers to contract aggregates.

**Evidence.** docs/operations/website-patch-package/content/results_2036_2046_2056.md lines 9-12: '| 2026 (baseline) | 25 | 25 | 48 |', '| 2036 | 44 | 47 | 48 |', '| 2046 | 47 | 48 | 48 |', '| 2056 | 47 | 48 | 48 |'. Contract aggregation of all 120 rows of data/contract/v1/scenario_table.csv by horizon_year x scenario_name: 2026 baseline ports=25 pathway=48; 2036 base=35, high=44; 2046 base=44, high=48; 2056 base=44, high=48. Independently confirmed identical in dashboard/tableau/patch_package/tbl_canonical_scenarios.csv. Line 3 of the doc: 'All values from canonical contract v1.0.0 (generated 2026-07-19)'. Line 29: 'The staged plan also avoids energizing 13–23 pathway ports'. dashboard/tableau/patch_package/tbl_avoided_evse.csv aggregates: 2026 baseline 23, 2036 base 13, 2046 base 4, 2056 base 4. PATCH_GUIDE.md:23-24: 'Every number on this page must trace to `data/contract/v1/scenario_table.csv`; remove any figure that does not.'

### H-18 · `docs/operations/reproduction-guide.md`
**Lane:** L07-docs-core · **Category:** absolute-local-paths-and-failing-gate · **Confirmed:** not yet re-checked by the lead

**Claim.** scripts/verify.sh cannot emit 'ALL REPOSITORY VERIFICATION GATES PASSED' at HEAD: its 'hygiene: no local absolute paths in code/config' gate greps *.json for /Users/andyyaro and the tracked file dashboard/static/footer_log.json contains nine such paths. This directly contradicts reproduction-guide.md's stated expected result and repository-migration-plan.md's claim that no machine-specific paths remain. It is also a genuine local-directory-structure leak. The footer-QA gate does not catch it because src/fcf_m2/visuals.py:audit_footer_metadata compares only Path(e['file']).name.

**Evidence.** scripts/verify.sh: gate "hygiene: no local absolute paths in code/config" runs `! git grep -nI '/Users/andyyaro' -- '*.py' '*.sh' '*.toml' '*.yml' '*.json' ':!scripts/verify.sh'`. Running that exact grep returns 9 matches, e.g. dashboard/static/footer_log.json:7 '"file": "/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/01_readiness_ranking.png"' (also lines 14,21,28,35,42,49,56,59). git ls-files confirms dashboard/static/footer_log.json is tracked. Contradicted by docs/operations/reproduction-guide.md:93 '| `./scripts/verify.sh` | `ALL REPOSITORY VERIFICATION GATES PASSED` |' and docs/repository-migration-plan.md:34 'rewritten to repo-relative paths (no machine-specific paths remain)' and :61 'no secrets, no local paths'.

### H-19 · `docs/human-actions/team_alternatives_session/02_PROVISIONAL_MCDA.md`
**Lane:** L08-human-actions · **Category:** arithmetic-error · **Confirmed:** not yet re-checked by the lead

**Claim.** Alternative G's published weighted MCDA score (37.0) is arithmetically wrong; the formula stated in the sibling file gives 40.0. All six other rows (A,B,C,D,E,F) reproduce exactly, so this is an isolated defect in a matrix the team is instructed to review and adopt.

**Evidence.** docs/human-actions/team_alternatives_session/02_PROVISIONAL_MCDA.md:28 `| G | Do nothing / defer (comparator) | 3 | 0 | 3 | 1 | 0 | 5 | 37.0 | 7 |`. Formula from docs/human-actions/team_alternatives_session/03_TEAM_SCORING_SHEET.md:26 `Weighted score = Sigma (score x weight) / 5, out of 100.` Weights from 02_PROVISIONAL_MCDA.md:11-16 (25/20/20/15/10/10). Computed: 3*25 + 0*20 + 3*20 + 1*15 + 0*10 + 5*10 = 75+0+60+15+0+50 = 200; 200/5 = 40.0, not 37.0. Verified all rows: A 41.0 OK, B 85.0 OK, C 71.0 OK, D 58.0 OK, E 72.0 OK, F 81.0 OK, G computed 40.0 vs published 37.0 MISMATCH.

### H-20 · `docs/human-actions/team_alternatives_session/04_WEIGHT_ADOPTION_PAGE.md`
**Lane:** L08-human-actions · **Category:** unreproducible-claim · **Confirmed:** not yet re-checked by the lead

**Claim.** The 'MANDATORY DISCLOSURE' equity-weighting crossover does not reproduce from the published matrix. At 2x the default equity weight (20/100) Alternative F never strictly overtakes B under any weight reallocation that keeps the total at 100 — the best case is a tie. F only wins at roughly 2.5x (equity 25). The cited source, Report 04 section 2, does not exist in the repository.

**Evidence.** docs/human-actions/team_alternatives_session/04_WEIGHT_ADOPTION_PAGE.md:7 `Sensitivity analysis (Report 04 §2) shows that at roughly **2× the default equity weight (~20/100)**, the **Hybrid portfolio (F) overtakes Staged pilots (B)** as the winner`; repeated at 02_PROVISIONAL_MCDA.md:42 `**Equity crossover:** at roughly 2× the default equity weight (~20 vs 10), **F overtakes B**`. Recomputed with B=[4,4,5,5,3,4], F=[4,4,4,5,4,3], equity 10->20 with total held at 100: donor Data-confidence -> B 83.0 / F 83.0 (TIE); donor Cost -> B 81.0 / F 81.0 (TIE); donor Expandability -> B 81.0 / F 79.0 (B wins); donor Safety -> B 83.0 / F 81.0 (B wins); donor Demand -> B 83.0 / F 81.0 (B wins). At equity 25 (from confidence 10 + cost 5): B 81.0 / F 83.0 (F wins).

### H-21 · `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md`
**Lane:** L09-deliverables · **Category:** headline-number-does-not-trace · **Confirmed:** yes — LEDGER FIND-NUM-01

**Claim.** The published active-port series (base 25→44→47→47, high 25→47→48→48) contradicts the canonical contract, which sums to base 25→35→44→44 and high 25→44→48→48. The value 47 is not a portfolio total at any horizon under any case.

**Evidence.** Summing ports_active over the 12 sites per (horizon_year, scenario_name) in dashboard/tableau/patch_package/tbl_canonical_scenarios.csv (byte-identical to data/contract/v1/scenario_table.csv, md5 2beff3f46e8f86b43427d47b7e8efab6) yields: 2026/baseline=25, 2036/base=35, 2036/high=44, 2046/base=44, 2046/high=48, 2056/base=44, 2056/high=48. Published claims: Final_Report.md:38-40 '| 2036 | 44 → 47 |', '| 2046 | 47 → 48 |', '| 2056 | 47 → 48 (pathway ceiling 48) |'; Speaker_Notes.md:74 'active ports 25 → 44 → 47 → 47 on the base path; 25 → 47 → 48 → 48 on the high path'; Timing_Runbook.md:67 '44→47 & 47→48'; repo-root README.md:39-41 same table. Contradicts reports/README.md:17 'Every number traces to data/contract/v1'.

### H-22 · `dashboard/tableau/patch_package/tbl_readiness_confidence.csv`
**Lane:** L09-deliverables · **Category:** internal-contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** FFX002 is published as '58.8 (Medium confidence)' in three artifacts while both contract-derived CSVs record Low confidence for all 12 sites.

**Evidence.** tbl_readiness_confidence.csv rows 2-13: data_confidence_score_v3=33.8 and data_confidence_level_v3=Low on every one of the 12 rows, with an identical confidence_breakdown string. tbl_canonical_scenarios.csv: data_confidence='Low' is the single distinct value across all 120 rows. Contradicting text: Final_Report.md:51 'FFX002 City of Fairfax Regional Library #1 at 58.8 (Medium)'; Speaker_Notes.md:63 'FFX002 City of Fairfax Regional Library leads at 58.8 (Medium confidence)'; repo-root README.md:47 'FFX002 — City of Fairfax Regional Library (58.8, Medium confidence)'. Speaker_Notes.md:64, one line later, says "The 'Low' labels are printed on the chart deliberately."

### H-23 · `dashboard/tableau/patch_package/tbl_canonical_scenarios.csv`
**Lane:** L09-deliverables · **Category:** horizon-convention · **Confirmed:** not yet re-checked by the lead

**Claim.** The canonical contract itself carries the prohibited horizon vocabulary: horizon_label takes values now/plus10/plus20/plus30 on rows whose model_mode is milestone2_v3, not legacy_v2.

**Evidence.** tbl_canonical_scenarios.csv (= data/contract/v1/scenario_table.csv) column horizon_label has exactly 4 distinct values across all 120 rows: ['now','plus10','plus20','plus30']; column model_mode has exactly 1 distinct value: ['milestone2_v3']. Per-site 2026 rows read e.g. 'FFX002,2,8,now'. Any platform view rendering horizon_label displays 'now'/'plus10'/'plus20'/'plus30'.

### H-24 · `dashboard/tableau/patch_package/tbl_peak_waits.csv`
**Lane:** L09-deliverables · **Category:** generated-artifact-has-no-data · **Confirmed:** not yet re-checked by the lead

**Claim.** The Tableau recipe's peak-waits worksheet plots four columns that are 0.0 on all 12 rows, so building it exactly as specified produces twelve zero-height bars.

**Evidence.** tbl_peak_waits.csv lines 2-13: p10_wait_min, p50_wait_min, p90_wait_min and peak_p90_wait_min are '0.0' on every one of the 12 data rows. TABLEAU_IMPLEMENTATION_BLOCKER.md:44 specifies '6. *Peak waits* — bar, p50 vs peak P90 wait, top-6 sites; reference line 10 min.' The only non-zero wait columns in the file are mean_wait_min (0.069–8.020) and peak_erlang_wait_min (0.381–42.365, PWC002 line 4).

### H-25 · `incoming/explorer/fcf-3d/fcf3d/build_sites.py`
**Lane:** L10-explorer-python · **Category:** horizon-convention · **Confirmed:** not yet re-checked by the lead

**Claim.** build_sites.py requires the legacy_v2 fixtures as its two REQUIRED sources and emits legacy horizon field names ports_2035/ports_2050 (and ports_2035_base/high, ports_2050_base/high) with no legacy_v2 label anywhere in the output. The governing Phase-3 claim HOLDS.

**Evidence.** lines 46-49: REQUIRED = {"results": "tests/fixture_legacy_v2_site_results.csv", "right_sizing": "tests/fixture_legacy_v2_right_sizing.csv"}; line 71 raise SourceMissing; lines 436-437: "ports_2035": _clean(row.get("recommended_ports_2035")), "ports_2050": _clean(row.get("recommended_ports_2050")); lines 463-466: "ports_2035_base"/"ports_2035_high"/"ports_2050_base"/"ports_2050_high"

### H-26 · `incoming/explorer/fcf-3d/fcf3d/build_sites.py`
**Lane:** L10-explorer-python · **Category:** horizon-convention · **Confirmed:** not yet re-checked by the lead

**Claim.** Qualification to the governing claim: the canonical milestone2_v3 contract IS read, but only as an OPTIONAL side table, so a single GeoJSON Feature carries two incompatible horizon conventions side by side, neither labelled. Verified in the shipped web/data/sites.geojson: ports_2035=2, ports_2050=2 alongside 10 scenarios at horizon_year 2026/2036/2046/2056 with horizon_label now/plus10/plus20/plus30.

**Evidence.** line 53: "scenarios": "data/contract/v1/scenario_table.csv" inside OPTIONAL (lines 73-76 skip silently if missing); line 513: props["scenarios"] = build_scenarios(scen, sid); build_scenarios lines 278-303. repo/data/contract/v1/scenario_table.csv: 120 rows, model_mode=milestone2_v3 on all 120, horizons Counter({2036:36, 2046:36, 2056:36, 2026:12})

### H-27 · `incoming/explorer/fcf-3d/README.md`
**Lane:** L10-explorer-python · **Category:** horizon-convention · **Confirmed:** not yet re-checked by the lead

**Claim.** README states a mangled horizon sequence that matches neither the canonical convention nor a labelled legacy one.

**Evidence.** README.md:199 — "- Time slider driving `ports_active` across the 2026 → 2036 → 2050 horizons," (canonical is 2026/2036/2046/2056)

### H-28 · `incoming/explorer/fcf-3d/README.md`
**Lane:** L10-explorer-python · **Category:** headline-number · **Confirmed:** not yet re-checked by the lead

**Claim.** README's worked example headline number is a legacy_v2 result presented without a legacy label. Under the canonical milestone2_v3 mode the same site is #2 at 51.8 and FFX004 is #1 at 53.4. I recomputed the six attribution figures from the fixture and they reproduce exactly, so the arithmetic is right but the regime is unstated.

**Evidence.** README.md:77-79 — "City of Fairfax Regional Library ranks #1 at 58.8. / Earned: equity gap index +8.11 pts, short service run +7.50 pts, install cost +7.50 pts. / Forgone: spare electrical capacity −10.50 pts, adjacent traffic −4.52 pts, jobs within 1 mi −4.08 pts." My recomputation from repo/tests/fixture_legacy_v2_site_results.csv: Equity gap index +8.11, Distance to electrical service +7.50, Estimated install cost +7.50; Spare electrical capacity −10.50, Adjacent traffic (AADT) −4.52, Jobs within 1 mi −4.08. repo/data/outputs/v3_run/site_results_milestone2_v3.csv: FFX002 51.8 rank 2, FFX004 53.4 rank 1.

### H-29 · `incoming/explorer/fcf-3d/tests/test_pipeline.py`
**Lane:** L10-explorer-python · **Category:** false-guarantee · **Confirmed:** not yet re-checked by the lead

**Claim.** The advertised drift gate cannot do what CLAUDE.md and README claim: the test never imports fcf_m2.scoring, it only compares the map's weights against a frozen CSV's own readiness_score column. Reweighting scoring.py without re-freezing leaves the test green.

**Evidence.** tests/test_pipeline.py:94-102 — reads only frames["results"] and row["readiness_score"]; no import of fcf_m2 anywhere in the file (imports at lines 25-33 are fcf3d only). CLAUDE.md:53 "test_attribution_reproduces_model_score guards this"; README.md:82-84 "fails the build if anyone reweights the model without updating the map".

### H-30 · `incoming/explorer/fcf-3d/fcf3d/build_sites.py`
**Lane:** L10-explorer-python · **Category:** integration-blocker · **Confirmed:** not yet re-checked by the lead

**Claim.** Phase 3 cannot simply repoint --repo at the V3 outputs: 15 columns exist only in the legacy fixture, and every one is read with .get() so they would blank SILENTLY, gutting the map's Overview and Risk-&-gaps panels.

**Evidence.** repo/tests/fixture_legacy_v2_site_results.csv has 83 columns; repo/data/outputs/v3_run/site_results_milestone2_v3.csv and site_results_legacy_v2.csv both have 72. Set difference: action_detail, action_label, ahj_review_flag, confidence_band, data_confidence_level, data_confidence_reason, data_confidence_score, data_needed_next, planning_recommendation, priority_reason, readiness_band, readiness_confidence_cell, recommended_ports_2035, recommended_ports_2050, review_reason. build_sites.py:416-449 fetch all of these via row.get().

### H-31 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** horizon-convention · **Confirmed:** not yet re-checked by the lead

**Claim.** The viewer displays 2035 and 2050 port horizons in four places with no legacy_v2 labelling, violating the canonical 2026/2036/2046/2056 convention.

**Evidence.** web/app.js:593 `<dt>2035 (base / high)</dt><dd>${int(p.right_sizing?.ports_2035_base)} / ${int(p.right_sizing?.ports_2035_high)}</dd>`; app.js:594 `<dt>2050 (base / high)</dt>`; app.js:763-764 `['Ports 2035 (base)', ...]` / `['Ports 2050 (base)', ...]`; app.js:416 `${p.ports_now}→${p.ports_2050} ports`; web/index.html:59 `<option value="ports_2050">By 2050 port need</option>`. Underlying keys ports_2035/ports_2050 and right_sizing.ports_2035_base/high, ports_2050_base/high in sites.geojson.

### H-32 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** internal-contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** One panel shows two incompatible horizon conventions: the Right-sizing key/value list shows 2035/2050 while the Scenarios table immediately below it shows canonical 2026/2036/2046/2056.

**Evidence.** app.js:591-597 renders `2035 (base / high)` and `2050 (base / high)`; app.js:609-610 then calls scenarioTable(p), which at app.js:471 renders `${esc(s.horizon_year)}`. Programmatic tally of all 120 scenario rows in sites.geojson: horizon_year counts {2026: 12, 2036: 36, 2046: 36, 2056: 36}.

### H-33 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** data-mode-not-disclosed · **Confirmed:** not yet re-checked by the lead

**Claim.** The viewer never displays which data mode is active; it loads the legacy_v2 fixture provenance into memory and discards it.

**Evidence.** sites.geojson metadata.sources = {"results": "fixture_legacy_v2_site_results.csv", "right_sizing": "fixture_legacy_v2_right_sizing.csv", ..., "electrical": "legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv"} (identical to manifest.json:8-15). app.js:870 `const meta = data.metadata ?? {};` then app.js:872 uses only `meta.site_count` and `meta.schema_version`. generated_at, score_min, score_max, sources, disclaimer, warnings are never referenced.

### H-34 · `fcf-3d/web/data/manifest.json`
**Lane:** L11-explorer-web · **Category:** dead-artifact · **Confirmed:** not yet re-checked by the lead

**Claim.** manifest.json is never read by anything; the strongest disclaimer in the tree is never displayed.

**Evidence.** grep for the string `manifest` in web/app.js and web/index.html returns zero hits. manifest.json:17 holds "Planning prototype only. Screening-class estimates; not an engineering, permitting, or procurement tool. Electrical service capacity is unconfirmed for all sites pending utility/facility review." The identical string is embedded at sites.geojson metadata.disclaimer and is also unread. What the user sees instead is app.js:873 "Planning prototype. Screening-class estimates only." at font-size 10.5px in --ink-3 (#66707e) per style.css:137.

### H-35 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** missing-disclaimer · **Confirmed:** not yet re-checked by the lead

**Claim.** Two of the four expected disclaimers are entirely absent: the 0/12 High-confidence statement and the "massing is not a design" statement.

**Evidence.** grep -i for `High confidence|0 of 12|massing|not a design|illustrative|conceptual` across web/index.html, app.js, style.css, data/manifest.json returns only one hit: app.js:486 `<p class="callout">Nudge the massing onto the actual parking area you'd` — an instruction, not a disclaimer. Data supports the missing claim: confidence_band tally across sites.geojson is Counter({'Medium confidence': 8, 'Low confidence': 4}), i.e. zero High.

### H-36 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** correctness · **Confirmed:** not yet re-checked by the lead

**Claim.** PWC005's score_reconstructed (37.0) disagrees with its readiness_score (36.9), and the Score tab prints a hardcoded checkmark asserting they are equal.

**Evidence.** sites.geojson PWC005: readiness_score=36.9, score_reconstructed=37.0 (delta 0.1; all 11 other sites delta 0.0). app.js:578-580 renders unconditionally: `Σ contributions = ${num(p.score_reconstructed, 1)} = readiness score ✓`. On PWC005 this reads "Σ contributions = 37.0 = readiness score ✓" beneath a bigscore of 36.9 (app.js:544).

### H-37 · `fcf-3d/web/index.html`
**Lane:** L11-explorer-web · **Category:** unpinned-dependency · **Confirmed:** not yet re-checked by the lead

**Claim.** The CesiumJS CDN reference is unpinned and contradicts its own adjacent comment; it also lives in index.html, not app.js as the brief assumed.

**Evidence.** index.html:9-12 comment: "CesiumJS from CDN. Google Photorealistic 3D Tiles require 1.124 or later. / For a reproducible build, pin the version: / https://cesium.com/downloads/cesiumjs/releases/1.128/Build/Cesium/Cesium.js / and vendor it into web/vendor/ for offline demos." index.html:117: `<script src="https://unpkg.com/cesium/Build/Cesium/Cesium.js"></script>`; index.html:14: `<link href="https://unpkg.com/cesium/Build/Cesium/Widgets/widgets.css" rel="stylesheet">`. Live verification: `curl -sI -L https://unpkg.com/cesium/Build/Cesium/Cesium.js` -> `HTTP/2 302 / location: /cesium@1.143.0/Build/Cesium/Cesium.js / cache-control: public, max-age=60`. web/vendor/ does not exist. No SRI on either tag. app.js contains no CDN reference at all (app.js:12 `/* global Cesium */`).

### H-38 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** accessibility · **Confirmed:** not yet re-checked by the lead

**Claim.** The site list is mouse-only, so the app's primary interaction is unreachable by keyboard, and pinning is circularly unreachable.

**Evidence.** app.js:407-425 builds `const li = el('li');` with `li.onclick = () => select(p.site_id);` and `li.oncontextmenu = (e) => { e.preventDefault(); togglePin(p.site_id); };` — no tabindex, no role, no keydown. The only keydown handler is app.js:826-832 (Escape, and `c` which requires `state.selected`, settable only by mouse click). No focus management on #panel (app.js:652), #modal (app.js:798), or #tokenGate (app.js:883); no role=dialog/aria-modal; grep for `:focus` in style.css returns zero hits; #toast has no aria-live (index.html:115).

### H-39 · `dashboard/static/footer_log.json`
**Lane:** L12-binaries · **Category:** contradiction · **Confirmed:** yes — LEDGER FIND-REPO-03

**Claim.** scripts/verify.sh's gate 'hygiene: no local absolute paths in code/config' FAILS on the current tree, yet docs/operations/reproduction-guide.md promises ALL REPOSITORY VERIFICATION GATES PASSED. dashboard/static/footer_log.json contains 9 absolute authoring-machine paths under /Users/andyyaro/Documents/, and the gate's pathspec explicitly includes '*.json'.

**Evidence.** scripts/verify.sh:59-60 `gate "hygiene: no local absolute paths in code/config" bash -c "cd '$REPO' && ! git grep -nI '/Users/andyyaro' -- '*.py' '*.sh' '*.toml' '*.yml' '*.json' ':!scripts/verify.sh'"`. I ran that exact grep: 9 hits, all dashboard/static/footer_log.json lines 7,14,21,28,35,42,49,56,59, each `"file": "/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/<name>.png"`. Contradicted by docs/operations/reproduction-guide.md:93 `| ./scripts/verify.sh | ALL REPOSITORY VERIFICATION GATES PASSED |`.

### H-40 · `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.docx`
**Lane:** L12-binaries · **Category:** generated-artifact-drift · **Confirmed:** not yet re-checked by the lead

**Claim.** All four reports/milestone-2/*.docx are stale against their Markdown sources: they still contain the pre-reorganisation directory layout that the .md files have since updated. Proven by regenerating each with scripts/md_to_docx.py into a scratchpad and diffing on (style, text) plus every table cell.

**Evidence.** Future_City_Fellowship_Milestone_2_Final_Report.docx contains `data_contract/v1/` x1, `human_actions/` x8, `repos/matlab_simulink_m2_v3/` x1, `visuals/static_dashboard/` x1, `website_patch_package/` x1, `reports/RISK_REGISTER` x1, `reports/REGULATORY_STAKEHOLDER_MAP` x1, ` tableau/` x1 — while the .md says data/contract/v1/, docs/human-actions/, matlab/, dashboard/static/, docs/operations/website-patch-package/, reports/milestone-2/RISK_REGISTER, reports/milestone-2/REGULATORY_STAKEHOLDER_MAP, dashboard/tableau/ (57 diff lines). Milestone_2_Gap_Closure_Status.docx row A1 still says `(human_actions/client_meeting_2/)` vs md `(docs/human-actions/client_meeting_2/)` (7 diff lines). FINAL_STANDARDS_APPLICATION_MATRIX.docx says `data_contract/v1/standards_register.csv` vs md `data/contract/v1/standards_register.csv`.

### H-41 · `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.pdf`
**Lane:** L12-binaries · **Category:** generated-artifact-drift · **Confirmed:** not yet re-checked by the lead

**Claim.** reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.pdf inherits every stale path from the stale DOCX it was exported from, so the client-facing PDF points at six directories that do not exist on v4-platform.

**Evidence.** PDF metadata `/Author: 'python-docx', /Creator: 'Writer', /Producer: 'LibreOffice 26.2.4.2 (AARCH64)'` proves the DOCX->PDF chain. Full-text extraction of all 7 pages yields `data_contract/v1` x1, `human_actions/` x8, `reports/RISK_REGISTER` x1, `repos/matlab_simulink_m2_v3` x1, `visuals/static_dashboard` x1, `website_patch_package` x1.


---

## MEDIUM — 66 findings

### M-01 · `src/fcf_m2/config.py`
**Lane:** L01-model-core · **Category:** internal-contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** config.py's docstring asserts 'Every result-changing constant lives here with its provenance label', but at least eight result-changing constants live in other modules with no provenance entry in config or assumptions.json.

**Evidence.** config.py:11 'Every result-changing constant lives here with its provenance label.' Counter-examples: workflow.py:35 `BASE_LOAD_GROWTH_PER_YEAR = 0.008`; scoring.py:26 `EV_SHARE_HIGH_BENCHMARK = 0.10`; economics.py:26 `END_YEAR = 2056`; peak_wait.py:51 `dwell_cv: float = 0.45`; demand.py:26-28 `MIN_OBSERVED_ROWS = 60`, `MIN_SITES_OBSERVED = 3`, `MAX_ACCEPTABLE_MAPE = 0.50`; confidence.py:22-53 SOURCE_CLASS_SCORES, VERIFICATION_STATUS_ADJ, STALENESS_THRESHOLD_DAYS=730, STALENESS_PENALTY=10, FIELD_GROUP_WEIGHTS; confidence.py:59-64 thresholds 75/50; right_sizing.py:44 `even_ceiling(value, minimum=2, maximum=12)` and :65 `parking_spaces * 0.05` and :63 default cap 6.

### M-02 · `src/fcf_m2/emissions.py`
**Lane:** L01-model-core · **Category:** duplicated-constant · **Confirmed:** not yet re-checked by the lead

**Claim.** emissions.avoided_evse_metric hardcodes the $1000/port/yr network fee instead of importing config.ECON['network_fee_usd_per_port_yr'], so changing the ECON value would silently desynchronise the avoided-EVSE metric from the lifecycle-cost model.

**Evidence.** emissions.py:79 `df["avoided_network_fee_usd_yr"] = df["avoided_active_evse_ports"] * 1000.0` — emissions.py imports nothing from ECON (imports at lines 17-27 are CHARGER_EFFICIENCY, DISPLACED_GASOLINE_G_CO2_PER_MI, ENERGY_PER_SESSION_KWH, EV_EFFICIENCY_KWH_PER_MI, GRID_FACTOR_*, LB_TO_KG). config.py:105 `"network_fee_usd_per_port_yr": 1000.0`.

### M-03 · `src/fcf_m2/scoring.py`
**Lane:** L01-model-core · **Category:** dead-weight-input · **Confirmed:** not yet re-checked by the lead

**Claim.** 35% of feasibility_subscore is weighted on spare_capacity_kw, which is literally 0 for all 12 sites, so that weight contributes exactly zero to every site's score in both modes — the feasibility subscore is effectively driven by only three of its four inputs.

**Evidence.** scoring.py:153-158 `df["feasibility_subscore"] = 100 * (0.35 * df["spare_capacity_kw_n"] + 0.25 * (1 - df["distance_to_service_ft_n"]) + 0.25 * (1 - df["install_cost_est_usd_n"]) + 0.15 * (1 - df["trenching_ft_n"]))`. Verified read-only over data/inputs/real_sites_v2.csv: 12 sites, `spare_capacity_kw` distinct values = ['0']. Corroborated by data/anchors/anchor_set_v1.json note for spare_capacity_kw: "all cohort values 0 (unconfirmed)". minmax() returns all zeros when max==min (scoring.py:61-62) and anchored() returns (0-0)/(200-0)=0.

### M-04 · `src/fcf_m2/contract.py`
**Lane:** L01-model-core · **Category:** broken-path-reference · **Confirmed:** not yet re-checked by the lead

**Claim.** contract.py's module docstring documents the contract directory as `data_contract/v1/`, but the actual contract lives at `data/contract/v1/`. Anyone following the docstring will not find the files.

**Evidence.** contract.py:6 'Contract layout (data_contract/v1/):'. Actual: `ls data/contract/v1` returns assumptions.json, contract_manifest.json, README.md, scenario_table.csv, schema.json, site_table.csv, source_provenance.csv, standards_register.csv. No `data_contract/` directory exists at the repo root (verified by `ls -la`).

### M-05 · `src/fcf_m2/contract.py`
**Lane:** L01-model-core · **Category:** missing-validation-rule · **Confirmed:** not yet re-checked by the lead

**Claim.** RT-06 is never implemented anywhere in contract.py, and the validate_scenario_table docstring misstates the implemented rule set in both directions (claims RT-07 coverage stops there while RT-08 is in fact implemented, and never mentions the missing RT-06).

**Evidence.** contract.py:140 docstring: 'Rule-based validation implementing RT-01..RT-07, RT-09 and master-prompt rules.' Body comments present: RT-01 (line 150), RT-02 (160), RT-03 (178), RT-04 (187), RT-05 (197), RT-07 (208), RT-08 (221), RT-09 (226). No 'RT-06' string exists in the file. verify_hash_chain (line 316) provides RT-10 separately.

### M-06 · `src/fcf_m2/confidence.py`
**Lane:** L01-model-core · **Category:** non-reproducible-output · **Confirmed:** not yet re-checked by the lead

**Claim.** Data-confidence scores depend on wall-clock time via date.today(), so re-running the pipeline far enough in the future will silently downgrade sites relative to the hash-sealed frozen contract, breaking reproducibility of a contract field.

**Evidence.** confidence.py:67-75 `def _staleness_penalty(source_date, today: date | None = None) ... today = today or date.today(); return STALENESS_PENALTY if (today - d).days > STALENESS_THRESHOLD_DAYS else 0` with STALENESS_THRESHOLD_DAYS = 730 (line 41) and STALENESS_PENALTY = 10 (line 42). workflow.py:147 calls `build_confidence(prov, list(scored["site_id"]))` with no `today` argument. The result lands in the contract as `data_confidence` (workflow.py:278).

### M-07 · `src/fcf_m2/economics.py`
**Lane:** L01-model-core · **Category:** model-limitation · **Confirmed:** not yet re-checked by the lead

**Claim.** The lifecycle model books only ONE electronics replacement across the entire 2026-2056 (30-year) horizon, at t=10 exactly, despite a 10-year replacement interval constant. This under-counts refresh cost in both OVB and STG and compresses the avoided-overbuild headline that the staged-vs-overbuild argument rests on.

**Evidence.** economics.py:106-109 `# replacement ~year 10 for ports active since baseline` / `if t == ECON["replacement_year_offset"] and ports[year] > 0:` — an equality test, not a modulo. config.py:110 `"replacement_year_offset": 10`. economics.py:26-27 `END_YEAR = 2056; YEARS = list(range(BASELINE_YEAR, END_YEAR + 1))` i.e. t runs 0..30, so t=20 and t=30 refreshes are never charged.

### M-08 · `src/fcf_m2/standards.py`
**Lane:** L01-model-core · **Category:** dead-link · **Confirmed:** not yet re-checked by the lead

**Claim.** standards.py cites a source register at research/CURRENT_FACTS_SOURCE_REGISTER.md to justify its 'Editions verified 2026-07-19' claim, but no research/ directory exists in this repo; the live file is docs/methodology/current-facts-source-register.md.

**Evidence.** standards.py:8 'Editions verified 2026-07-19 (see research/CURRENT_FACTS_SOURCE_REGISTER.md).' Existence check: `research/CURRENT_FACTS_SOURCE_REGISTER.md` -> MISSING; repo-root `ls -la` shows no `research/` directory. The corresponding live document is docs/methodology/current-facts-source-register.md (confirmed present, contains the IM-01 grid-factor row).

### M-09 · `scripts/build_static_dashboard.py`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** Chart 01 contradicts itself: the title hard-codes "(Medium confidence)" (a legacy-V2 label) while the per-bar annotations use V3 confidence, which is Low for all 12 sites.

**Evidence.** build_static_dashboard.py:48 `ax.set_title("Site readiness ranking — FFX002 leads at 58.8 (Medium confidence)")`; line 49 annotates with df["data_confidence_level_v3"]. I ran the V3 workflow into scratchpad: data_confidence_v3.csv has {'Low': 12}; FFX002 data_confidence_score_v3 = 33.8. The "Medium" traces to tests/fixture_legacy_v2_site_results.csv row 2 ('53.0,Medium').

### M-10 · `scripts/build_excel_workbook.py`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** Two committed-deliverable generators depend on packages declared nowhere in the repo and absent from the venv, so excel/Electric_Data_Milestone_2_Updated.xlsx and the four reports/*.docx cannot be regenerated here.

**Evidence.** build_excel_workbook.py:13 `import openpyxl`; md_to_docx.py:8 `from docx import Document`. pyproject.toml:10-20 declares numpy/pandas/matplotlib/jsonschema plus extras gis/test/presentation — neither package appears; requirements-lock.txt (21 pins) has neither. venv/bin/python -c 'import openpyxl' and 'import docx' both raise ModuleNotFoundError.

### M-11 · `.github/workflows/tests.yml`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** yes — LEDGER FIND-REPO-04/06

**Claim.** CI's push trigger does not cover the current branch, so pushes to v4-platform run no tests.

**Evidence.** .github/workflows/tests.yml:5 `branches: [main, milestone2-v3-professional-release]`; `git rev-parse --abbrev-ref HEAD` = v4-platform. Only pull_request and workflow_dispatch remain.

### M-12 · `tests/test_contract_and_integration.py`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** The doc-drift test does not test the committed doc — it compares generate_docs() against itself; only verify.sh (never run by CI) checks docs/WORKFLOW_STEPS.md.

**Evidence.** tests/test_contract_and_integration.py:135-140: `docs = workflow.generate_docs(); assert f"Step count: **{len(workflow.STEPS)}**" in docs`. scripts/verify.sh:47 is the only check against the file on disk. They currently agree (docs/WORKFLOW_STEPS.md:3 'Step count: **11**', workflow.py:37-49 has 11 STEPS).

### M-13 · `matlab/src/makeSessionProfiles.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** DiversityFactor is applied to the aggregate request curve but NOT to the sessions table, so the energy_aware strategy silently ignores it. With DiversityFactor < 1, energy_aware.requested_kWh exceeds unmanaged.requested_kWh by 1/DiversityFactor and deferred_kWh compares a scaled request against an unscaled dispatch, making it meaningless.

**Evidence.** makeSessionProfiles.m:180 `evRequest_kW = evRequest_kW * opt.DiversityFactor;` — the sessions table is built at :154-161 BEFORE this line and is never scaled. managedCharging.m:137 `requested_kWh = sum(perVehicle.requested_kWh);` derives from sessions (:232-236), while :144-146 `cumReq = cumtrapz(t_hr, evRequest_kW); ... deferred_kWh = max(max(cumReq - cumEv, [], "omitnan"), 0);` mixes the two bases. Option is exposed all the way up at runScenario.m:56-57.

### M-14 · `matlab/src/managedCharging.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** Integration-basis mismatch inside managedCharging: energy_aware accumulates delivered energy as a left-Riemann sum (p*dt) while unmanaged/clamp use trapz and the plotted curve is integrated with cumtrapz. The area under the plotted energy_aware ev_kW curve therefore does not equal the reported delivered_kWh.

**Evidence.** managedCharging.m:265 and :286 `delivered_kWh(idx) = delivered_kWh(idx) + p_kW * dt_hr;` versus :97 `requested_kWh = trapz(t_hr, evRequest_kW);`, :109-110 `requested_kWh = trapz(...); delivered_kWh = trapz(t_hr, ev_kW);`, and :145 `cumEv = cumtrapz(t_hr, ev_kW);`

### M-15 · `matlab/src/makeSessionProfiles.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** The pulse energy-pinning rescale can push instantaneous request power ABOVE the physical charger limit p_kW, inflating peak_ev_kW and peak_unmanaged_kW — both headline metrics — by roughly m/(m-1) where m is the number of covered time steps (~1.4% for a 6-hour charge at the 5-minute default).

**Evidence.** makeSessionProfiles.m:284-289 `prof = p_kW * (overlap / dt_hr); ... eNow = trapz(t_hr, prof); if eNow > 0 && eTarget_kWh > 0; prof = prof * (eTarget_kWh / eNow); end` — trapz under-counts the two half-edges of a rectangular pulse, so the correction factor is > 1. Feeds peak_unmanaged_kW via runScenario.m:139.

### M-16 · `matlab/src/makeSessionProfiles.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** The `ports` column is required but never constrains concurrency in the session-based modes — nothing caps the number of simultaneously charging sessions at the number of installed ports. It is used only in the legacy_gaussian presentation mode.

**Evidence.** makeSessionProfiles.m:219-222 lists `ports` in requiredFields; its only numeric use is :120 `evRequest_kW = s.ports * s.charger_power_kW * arrivalShape;` inside the `if mode == "legacy_gaussian"` branch opened at :112. The session branch (:121-176) never references s.ports. managedCharging's scheduler (:249-290) likewise has no port-count bound.

### M-17 · `matlab/src/makeSessionProfiles.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** The energy-aware scheduler's documented priority-class tier is inert: priority_class is hard-set to 1 for every session, so the first sort key never discriminates and the scheduler is pure earliest-departure-first.

**Evidence.** makeSessionProfiles.m:157 `ones(nSessions, 1), ...` supplies the priority_class column (named at :161). managedCharging.m:272-274 `[~, order] = sortrows([sessions.priority_class(active), sessions.departure_hr(active), sessions.arrival_hr(active)]);` and the docstring at :215-219 claims sorting "by priority_class (ascending; 1 = highest priority), then departure time".

### M-18 · `matlab/src/runScenario.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** runScenario's default GuardMode inverts capacityGuard's own fail-closed default, so the default execution path never fail-closes; feasibility mode is only reached if a caller explicitly asks for it, and run_all_scenarios hard-codes planning_illustration with no option to override.

**Evidence.** capacityGuard.m:59 `addParameter(p, "Mode", "feasibility", ...)` versus runScenario.m:46 `addParameter(p, "GuardMode", "planning_illustration", ...)`; run_all_scenarios.m:91 `"GuardMode", "planning_illustration", ...` is a literal with no corresponding addParameter in the batch runner's 7 options (:45-58).

### M-19 · `matlab/src/capacityGuard.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** yes — LEDGER FIND-MATLAB-02

**Claim.** A headline number appears in a docstring and does not trace to anything inside matlab/src/: the claim that placeholder is 'the current adapter CSV state for ALL 12 sites'. Nothing in the MATLAB layer establishes a site count; it must be traced to data/contract/v1/ or the adapter.

**Evidence.** capacityGuard.m:12-13 `%       placeholder          - declared placeholder (the current adapter\n%                              CSV state for ALL 12 sites)`. The canonical CSV read by loadScenarios has 120 data rows and 22 columns; the site count is not asserted or checked anywhere in src/.

### M-20 · `matlab/src/buildSimulinkModel.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** UNCERTAIN (untestable without MATLAB): the sole Simulink-availability gate uses `exist(name,'file') ~= 2`, which does not reliably return 2 for built-in / P-coded functions, so buildSimulinkModel may raise 'Simulink is not available' on a correctly licensed machine. Should be the first thing checked on the licensed run.

**Evidence.** buildSimulinkModel.m:55 `if exist("new_system", "file") ~= 2 || ~license("test", "Simulink")` leading to error id `buildSimulinkModel:simulinkUnavailable` at :56.

### M-21 · `matlab/tests/test_regression.m`
**Lane:** L04-matlab-tests-docs · **Category:** missing-artifact · **Confirmed:** not yet re-checked by the lead

**Claim.** matlab/tests/golden/regression_golden.csv (and its parent directory) does not exist; test_regression.m is its only consumer and creates it on first licensed run.

**Evidence.** `ls matlab/tests/golden` -> 'No such file or directory'. test_regression.m:28-29 sets goldenFile = fullfile(thisDir,'golden','regression_golden.csv'); :45 'if ~isfile(goldenFile)'. Correctly disclosed at EXECUTION_STATUS.md:11-13 and RUN_ON_LICENSED_MATLAB.md:28-30.

### M-22 · `data/contract/v1/contract_manifest.json`
**Lane:** L05-data-contract · **Category:** verification-gap · **Confirmed:** not yet re-checked by the lead

**Claim.** RT-10 hash verification checks only the 6 'tables' entries and never the 5 'inputs' entries. Drift in real_sites_v2.csv, the frozen legacy file, field_provenance_v1.csv, anchor_set_v1.json, or legacy_matlab_site_meta.csv is silently undetectable by `make validate`. (I verified all 5 by hand — they PASS today — but the tooling would not catch it tomorrow.)

**Evidence.** src/fcf_m2/contract.py:315-324 verify_hash_chain(): 'for name, expected in manifest["tables"].items():' — iterates tables only; manifest['inputs'] is never read. Docstring line 316: 'RT-10: manifest table hashes match files on disk.' The 5 input digests at contract_manifest.json:11-15 are write-only.

### M-23 · `data/inputs/legacy_matlab_site_meta.csv`
**Lane:** L05-data-contract · **Category:** latent-trap · **Confirmed:** not yet re-checked by the lead

**Claim.** legacy_matlab_site_meta.csv carries a nonzero spare_capacity_kw_placeholder column (38.4/57.6/76.8/153.6 kW) that is correctly NOT propagated into the contract (spare_capacity_kw is blank on all 120 rows). This is a live trap: any future integrator who wires that column through silently destroys the placeholder guarantee the entire program rests on.

**Evidence.** data/inputs/legacy_matlab_site_meta.csv:2-13 col 6 spare_capacity_kw_placeholder ∈ {153.6, 76.8, 57.6, 38.4}; provenance column on every row: 'hand-adapted planning placeholder from legacy MATLAB adapter (2026-07); base loads and spare capacity are UNVERIFIED planning proxies'. Verified: data/contract/v1/scenario_table.csv spare_capacity_kw is '' on 120/120 rows, and assumptions.json:86 states 'service/spare capacity NULL with capacity_basis=placeholder at all 12 sites until utility/facility confirmation'.

### M-24 · `data/inputs/real_sites_v2.csv`
**Lane:** L05-data-contract · **Category:** dead-reference · **Confirmed:** not yet re-checked by the lead

**Claim.** Three files referenced as provenance sources inside real_sites_v2.csv notes do not exist anywhere in the repository — dangling provenance pointers to an external working set.

**Evidence.** data/inputs/real_sites_v2.csv notes cells cite 'amenities_0_5mi_v4_osm_reviewed.csv' (rows for PWC001, PWC002, PWC004, FFX001, FFX002, FFX003, FFX004 and others), 'v2c003_model_row_assumptions.csv' (line 8, FFX003), 'v2c007_model_row_assumptions.csv' (line 9, FFX004). A repo-wide find for all three returns nothing.

### M-25 · `data/provenance/v2_source_confidence_tracker.csv`
**Lane:** L05-data-contract · **Category:** incomplete-coverage · **Confirmed:** not yet re-checked by the lead

**Claim.** v2_source_confidence_tracker.csv covers only 2 of 12 sites (FFX003, FFX004) and site_coordinate_sources.csv only 6 of 12, yet data/README.md classifies the whole provenance/ directory as 'typed field-level provenance driving data confidence'. Both files are also unhashed and have no programmatic consumer, so they can drift silently. Worse, v2_source_confidence_tracker uses a 10-group field taxonomy incompatible with field_provenance_v1's 7-group taxonomy — the two provenance systems cannot be joined.

**Evidence.** v2_source_confidence_tracker.csv: 20 data rows, distinct site_ids = ['FFX003','FFX004'] only. site_coordinate_sources.csv: 6 data rows, distinct site_ids = ['FFX001','FFX002','PWC001','PWC002','PWC003','PWC004'] only. data/README.md:13 classifies 'provenance/' as 'tracked reference | yes | typed field-level provenance driving data confidence'. Taxonomy mismatch: tracker groups = address_and_public_access, coordinates, hours_and_parking, nearby_EV_supply, households_jobs_traffic, amenities, equity, EV_adoption, visitors_and_employees, electrical_and_site_layout; field_provenance groups = electrical_service, safety_review_fields, site_use_and_demand, address_and_public_access, coordinates, parking_and_layout, equity_and_context. Only 2 of 10 names shared. Neither file appears in contract_manifest.json.

### M-26 · `data/inputs/real_sites_v2.csv`
**Lane:** L05-data-contract · **Category:** unpropagated-caveat · **Confirmed:** not yet re-checked by the lead

**Claim.** PWC004 (Chinn Park Regional Library) is documented in a notes cell as closed for renovation, yet it ranks 7th and carries a full 10-row scenario decade in the contract as if operating. Nothing downstream flags the operating-status caveat.

**Evidence.** data/inputs/real_sites_v2.csv:5 notes: '...official library page currently lists Chinn Park Library as closed for renovation so operating status remains a caveat; hours and parking remain future planning assumptions.' PWC004 nonetheless appears with 10 rows in scenario_table.csv, base_readiness_score 48.6 / base_rank 7 in the frozen legacy file, and 'Tier 2 — promising candidate, refine data' in tbl_readiness_confidence.csv:8. No column in scenario_table.csv or site_table.csv encodes operating status.

### M-27 · `data/contract/v1/standards_register.csv`
**Lane:** L05-data-contract · **Category:** data-not-differentiated · **Confirmed:** not yet re-checked by the lead

**Claim.** The standards register is entirely site-invariant — the identical 37-row block is replicated for all 12 sites with no per-site variation. PWC002, the only enclosed garage, gets exactly the same rows as every open-lot library, despite the legacy risk file asserting garage-specific fire/AHJ review risk for it. The 'per-site standards applicability' framing is nominal.

**Evidence.** standards_register.csv: 444 data rows, every site_id has exactly 37 rows (verified by Counter). Only 9 distinct standard_ids, and requirement/evidence_required/authority/open_ahj_question strings are identical across sites for a given (standard_id, stage). Meanwhile legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv:8 gives PWC002 electrical_risk_reason '...garage or enclosed-structure context adds fire/AHJ review risk...' and electrical_data_needed_next '...confirm garage fire/AHJ requirements', and site_table.csv:4 sets garage_enclosed=1.0 for PWC002 alone. No corresponding garage-specific row exists in the register.

### M-28 · `data/provenance/field_provenance_v1.csv`
**Lane:** L05-data-contract · **Category:** generated-artifact-drift · **Confirmed:** not yet re-checked by the lead

**Claim.** field_provenance_v1.csv and source_provenance.csv are content-identical but differ only in line endings (CRLF vs LF), producing two irreconcilable SHA-256 digests for the same 84 facts. Any check comparing the input digest to the table digest will always report a spurious difference.

**Evidence.** cmp reports 'differ: char 117, line 1'. field_provenance_v1.csv = 11470 bytes, 85 CR bytes (CRLF); source_provenance.csv = 11385 bytes, 0 CR bytes (LF). 11470-11385 = 85 = line count. `diff <(tr -d '\r' < field_provenance_v1.csv) source_provenance.csv` → identical. Digests: 9a07aa1e0dc4bca43e160459db7a0985bc99a08454fe51437481bb2f7af4d482 (input) vs 2d346861cf6216fb9b1f5c4500f8fe30c65411204d9c18fd1bbfd047a0efd875 (table). field_provenance_v1.csv is the only CRLF file in the whole data/ tree.

### M-29 · `README.md`
**Lane:** L06-root-ci · **Category:** ci-verify-divergence · **Confirmed:** yes — LEDGER FIND-NUM-01/02, FIND-REPO-08

**Claim.** README says 'CI runs the same gates on every push and pull request'. CI omits four of verify.sh's ten gates (docs step-count, dashboard 9-PNG + footer QA, /Users/andyyaro local-path scan, 25 MB size limit) — three of which the README names in the immediately preceding sentence — and the push trigger is restricted to two branches, so the active v4-platform branch gets no push CI.

**Evidence.** README.md:116-120 lists 'footer QA on every dashboard visual, secret and local-path scans, size limits' then asserts 'CI runs the same gates on every push and pull request'. .github/workflows/tests.yml:3-7 `on: push: branches: [main, milestone2-v3-professional-release]`; tests.yml has no equivalent of scripts/verify.sh:46-47, 49-54, 59-60, 62-63. Current branch is v4-platform.

### M-30 · `requirements-lock.txt`
**Lane:** L06-root-ci · **Category:** lock-ci-incoherence · **Confirmed:** yes — LEDGER FIND-REPO-05

**Claim.** requirements-lock.txt claims to record the environment used for all V3 verification (Python 3.14.6 arm64) but CI pins Python 3.12 on ubuntu-latest and never applies the lock; only make setup uses it as a constraints file. The two supported install paths can resolve different dependency sets, and the lock is never exercised by CI.

**Evidence.** requirements-lock.txt:1 '# Lock generated 2026-07-19 from Python 3.14.6 arm64 venv used for all V3 verification runs'; .github/workflows/tests.yml:21 'python-version: "3.12"', tests.yml:12 'runs-on: ubuntu-latest', tests.yml:25 'pip install -e .[test]' (no -c); Makefile:6 'venv/bin/pip install -e ".[test]" -c requirements-lock.txt'; pyproject.toml:9 'requires-python = ">=3.11"'; README.md:85 'Python 3.11+ (verified on 3.12/3.14)'.

### M-31 · `README.md`
**Lane:** L06-root-ci · **Category:** internal-contradiction · **Confirmed:** yes — LEDGER FIND-NUM-01/02, FIND-REPO-08

**Claim.** README's headline section is labelled 'canonical contract v1.0.0' but attributes FFX002 a readiness score of 58.8 and 'Medium confidence'; neither is in the contract. The contract has no score column and its data_confidence is Low in all 120 rows, and the README's own blockquote says 0 of 12 sites reach High confidence.

**Evidence.** README.md:34 '## Headline results (canonical contract v1.0.0, screening values)'; README.md:45-46 'Top-ranked site: **FFX002 — City of Fairfax Regional Library (58.8, Medium confidence)**'. data/contract/v1/scenario_table.csv: Counter of data_confidence = {'Low': 120}; no readiness-score column in scenario_table.csv or site_table.csv. 58.8/'medium' originate in data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv:2 and tests/fixture_legacy_v2_right_sizing.csv:2; V3 typed confidence for FFX002 is Low in dashboard/tableau/patch_package/tbl_readiness_confidence.csv:2.

### M-32 · `Makefile`
**Lane:** L06-root-ci · **Category:** documented-behavior-mismatch · **Confirmed:** not yet re-checked by the lead

**Claim.** 'make test' is documented in three places as enforcing an 80% coverage gate, but the Makefile target has no --cov-fail-under; it only prints a terminal report. The 80% floor exists only in verify.sh and CI.

**Evidence.** Makefile:9 '$(PY) -m pytest tests/ -q --cov=fcf_m2 --cov-report=term' vs README.md:78 'make test # 80 tests incl. legacy golden tests (coverage gate 80%)', CONTRIBUTING.md:7 'coverage gate 80%', docs/operations/reproduction-guide.md:16,90. Actual gate: scripts/verify.sh:24 and .github/workflows/tests.yml:28 both use '--cov-fail-under=80'.

### M-33 · `src/fcf_m2.egg-info/PKG-INFO`
**Lane:** L06-root-ci · **Category:** generated-artifact-committed · **Confirmed:** not yet re-checked by the lead

**Claim.** A generated build artifact directory is tracked in git and is not covered by .gitignore; it regenerates on every editable install. Contents currently match pyproject.toml (no drift today), but it is a drift surface with no ignore rule.

**Evidence.** git ls-files src/ lists src/fcf_m2.egg-info/PKG-INFO, SOURCES.txt, dependency_links.txt, requires.txt, top_level.txt; `git check-ignore -v src/fcf_m2.egg-info` exits 1 (not ignored). .gitignore has no *.egg-info/, dist/ or build/ pattern (26 lines read in full). PKG-INFO 'Version: 3.0.0' matches pyproject.toml:7.

### M-34 · `.gitignore`
**Lane:** L06-root-ci · **Category:** gitignore-gap · **Confirmed:** not yet re-checked by the lead

**Claim.** .gitignore covers venv/, .venv/, __pycache__/, *.pyc and .DS_Store but does NOT cover node_modules, ._* (macOS AppleDouble), *.egg-info/, dist/, build/, .env, *.log, .idea/ or .vscode/. The node_modules and ._* gaps matter directly for Phase 3 (the incoming JS 3D explorer) and Phase 8 (deploy bundles).

**Evidence.** .gitignore lines 1-26 in full: venv/ (2), .venv/ (3), __pycache__/ (4), *.pyc (5), .pytest_cache/ (6), .coverage (7), htmlcov/ (8), data/outputs/ (11), matlab/outputs/* (14), !matlab/outputs/.gitkeep (15), matlab/simulink/ (16), *.slxc (17), *.asv (18), .DS_Store (21), Thumbs.db (22), release/ (25), *.zip (26). No other .gitignore exists in the tree; .git/info/exclude is stock.

### M-35 · `docs/operations/reproduction-guide.md`
**Lane:** L07-docs-core · **Category:** internal-contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** reproduction-guide.md asserts 'CI runs the same gates' as scripts/verify.sh, but .github/workflows/tests.yml runs only 6 of the 10 gates. It omits the workflow-docs consistency gate, the dashboard footer-QA gate, the local-absolute-path scan, and the 25 MB file-size limit. The omitted local-path gate is exactly the one that fails, so the doc drift has been masking a real failure. tests.yml also only push-triggers on branches [main, milestone2-v3-professional-release], so the current v4-platform branch gets no push CI.

**Evidence.** docs/operations/reproduction-guide.md:65-69: 'Gates: tests + coverage floor, legacy baseline reproduction (25/48), contract rules/schema/hash chain, cross-model reconciliation with the MATLAB canonical CSV, workflow-docs consistency, dashboard footer QA, secret scan, local-path scan, file-size limit, and Markdown link check. CI runs the same gates ([.github/workflows/tests.yml]).' .github/workflows/tests.yml steps are exactly: 'Run test suite with coverage gate', 'Legacy baseline reproduction (25 starter / 48 pathway)', 'Validate tracked canonical contract', 'Cross-model reconciliation', 'Internal Markdown links', 'Secret scan (pattern-based)'. Trigger block: 'on: push: branches: [main, milestone2-v3-professional-release]'.

### M-36 · `docs/architecture/TECHNICAL_INTEGRATION_ARCHITECTURE.md`
**Lane:** L07-docs-core · **Category:** dead-reference · **Confirmed:** not yet re-checked by the lead

**Claim.** TECHNICAL_INTEGRATION_ARCHITECTURE.md cites FAILURE_MITIGATION_OPTIONS.csv twice as the evidentiary basis for its ranked mitigations, but that file does not exist anywhere in the repository. Because the reference is backticked rather than a Markdown link, scripts/check_internal_links.py does not catch it.

**Evidence.** docs/architecture/TECHNICAL_INTEGRATION_ARCHITECTURE.md:5 '**Basis:** Report 07 (Technical Integration and Failure-Mitigation Research); `rankings/FAILURE_MITIGATION_OPTIONS.csv`; EX16 (protocols); EX12 (Dominion programs).' and :52 'Top-ranked mitigations (full ranking in `FAILURE_MITIGATION_OPTIONS.csv`, carried into `RISK_REGISTER.csv`)'. `find . -iname "*FAILURE_MITIGATION*"` over the repo returns nothing; only reports/milestone-2/RISK_REGISTER.csv and .md exist.

### M-37 · `docs/WORKFLOW_STEPS.md`
**Lane:** L07-docs-core · **Category:** weak-generated-artifact-gate · **Confirmed:** not yet re-checked by the lead

**Claim.** docs/WORKFLOW_STEPS.md is generated and marked 'do not edit by hand', but the verify.sh gate named 'docs: generated workflow steps match the executable manifest' only asserts the step-count substring is present. Step names and descriptions are never compared, so renaming a step or editing a description drifts the doc silently while the gate stays green. The file is in sync today (I diffed all 11 name/description pairs), and this gate is also one of the four CI omits.

**Evidence.** scripts/verify.sh: `gate "docs: generated workflow steps match the executable manifest" bash -c "cd '$REPO' && '$PY' -c 'from fcf_m2 import workflow; d=open(\"docs/WORKFLOW_STEPS.md\").read(); assert f\"Step count: **{len(workflow.STEPS)}**\" in d'"`. docs/WORKFLOW_STEPS.md:3 'Step count: **11**'. Generator: src/fcf_m2/workflow.py:52-59 generate_docs(); manifest at src/fcf_m2/workflow.py:37-49 (11 tuples); writer at src/fcf_m2/workflow.py:380.

### M-38 · `docs/human-actions/client_meeting_2/02_CLIENT_PREREAD.md`
**Lane:** L08-human-actions · **Category:** horizon-convention · **Confirmed:** not yet re-checked by the lead

**Claim.** Horizon-convention drift in the two client-facing documents: relative '10/20/30-year' and '10-yr' labels are used without any legacy_v2 marking. The underlying numbers are correct and trace to the contract's plus10/2036 rows, so this is labelling drift rather than a wrong figure — but canon is 2026/2036/2046/2056.

**Evidence.** docs/human-actions/client_meeting_2/02_CLIENT_PREREAD.md:9 `models demand and capacity at 10/20/30-year horizons`; :15 column header `| 10-yr cost screen (NPV) |`. docs/human-actions/client_meeting_2/04_ALTERNATIVES_BRIEFING.md uses `10-yr cost order` at lines 5, 11, 19, 27, 35, 43, 51, 59 (8 occurrences). Canon from data/contract/v1/contract_manifest.json `"conventions": {"baseline_year": 2026, "horizons": [2036, 2046, 2056]}`; scenario_table.csv horizon_label values are now/plus10/plus20/plus30. The quoted NPVs do trace: FFX002 ~$134k = FFX002_2036_* lifecycle_cost_npv_usd 133641.0; FFX004 ~$166k = 166275.0; PWC006 ~$148k = 147663.0. Contrast the correct handling at docs/human-actions/fellowship_confirmation/02_CONTINGENCY_SUMMARY.md:19-21 (`Keep the current consistent 2026 baseline + 2036/2046/2056 set`).

### M-39 · `docs/human-actions/client_meeting_2/03_MEETING_AGENDA.md`
**Lane:** L08-human-actions · **Category:** dead-reference · **Confirmed:** not yet re-checked by the lead

**Claim.** Pervasive dead references: the 'Client and Public Engagement Toolkit' (cited by section 8 times) and the numbered Report series (Report 02, 04, 10, 11) do not exist anywhere in the repository, and unlike the MCDA CSV they carry no 'not tracked in this repository' disclaimer.

**Evidence.** toolkit cited at client_meeting_2/03_MEETING_AGENDA.md:5 `Per Client and Public Engagement Toolkit §1`, :21 `toolkit §5 async rule`; 05_CLIENT_FEEDBACK_FORM.md:3 `per toolkit §3`; 06_DECISION_LOG.md:3 `per toolkit §4`; 09_FOLLOWUP_EMAIL_DRAFT.md:3 `per toolkit §7`; 10_ACCEPTANCE_CHECKLIST.md:3 `Per toolkit §5`; 04_ALTERNATIVES_BRIEFING.md:5 `Format per toolkit §6`; public_engagement/01_SURVEY.md:5 `Per toolkit §8`; 03_LISTENING_SESSION_ONE_PAGER.md:5; 05_PRIVACY_NOTICE.md:5. Reports cited at human-actions/README.md:7 `Per Report 02 §4`, :28 `Report 02, ruling 5`; fellowship_confirmation/02_CONTINGENCY_SUMMARY.md:9,21,27; team_alternatives_session/01_FACILITATION_GUIDE.md:3 `Per Report 04 §5`; 06_COI_ASSUMPTION_NOTE.md:5 `from Report 04 §3`; 04_WEIGHT_ADOPTION_PAGE.md:7 `Report 04 §2`; public_engagement/04_LANGUAGE_ACCESS_PLAN.md:3 `Report 10 §3`; 07_EQUITY_REVIEW_PROTOCOL.md:3 `Report 10 §4 and the peer-question theme (Report 11)`. Verified absent: `find . -iname "*TOOLKIT*"` returns only ./venv/lib/python3.12/site-packages/mpl_toolkits; reports/ contains only milestone-2 deliverables. Only 02_PROVISIONAL_MCDA.md:5 honestly discloses `pre-V3 research archive, not tracked in this repository`.

### M-40 · `docs/human-actions/ahj_fire_marshal/05_PROPOSED_STANDARD_FEEDBACK_SHEET.md`
**Lane:** L08-human-actions · **Category:** internal-contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** The AHJ proposed-standard feedback sheet uses a 3-module numbering (M1/M2/M3) that contradicts the concept document's 7 modules. Its Q4 asks about 'M2's fail-safe on comms loss' but that content is Module 5 in the concept doc. An AHJ handed both documents reads two incompatible numbering schemes.

**Evidence.** docs/human-actions/ahj_fire_marshal/05_PROPOSED_STANDARD_FEEDBACK_SHEET.md:11-13 lists only `M1 — Emergency access & disconnect`, `M2 — Expandability & right-sizing documentation: pathway capacity declaration; utilization-monitoring capability; documented expansion triggers; load-management fail-safe behavior on communications loss`, `M3 — Accessibility & site conditions cross-references`; :20 asks `Does M2's "fail-safe on comms loss" behavior matter to your office`. But docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md defines seven modules: :23 Module 1 Emergency access and disconnect; :33 Module 2 Expandability and right-sizing documentation; :42 Module 3 Accessibility and site-condition cross-references; :51 Module 4 Monitoring and expansion triggers; :59 Module 5 Managed-charging fail-safe (`Comms-loss behavior | Disconnect network link; observe EVSE output settles to documented default-safe profile`); :67 Module 6 Commissioning; :76 Module 7 Materials/take-back. The sheet's M2 bundles concept Modules 2+4+5.

### M-41 · `docs/human-actions/utility_facility_data/03_TRACKING_REGISTER.md`
**Lane:** L08-human-actions · **Category:** schema-gap · **Confirmed:** not yet re-checked by the lead

**Claim.** The tracking register does not cover every field the facility-manager letter requests, and two requested quantities carry no units. Phase 4's ingestion schema and Phase 5's NFC capture form must resolve both gaps because the source documents do not.

**Evidence.** docs/human-actions/utility_facility_data/02_DATA_REQUEST_FACILITY_MANAGERS.md:28 requests item 9 `Any known site constraints (drainage, easements, planned repaving — repaving is an opportunity to lay conduit cheaply)` but docs/human-actions/utility_facility_data/03_TRACKING_REGISTER.md has no corresponding row — its 11 rows are Service rating (V/A/kVA), Interval load data 12+ mo, Spare capacity at peak, Transformer/feeder info, Service distance to charging area, Panel details / spare positions, Planned shutdowns/outages, Parking counts (incl. ADA), Visitor/activity counts, Fleet duty cycles (if any), Planned capital projects (lines 9-19, repeated at 25-35 and 41-51). Unitless requests: :19 item 2 `Spare breaker positions and spare panel capacity` (capacity units unstated) and :21 item 4 `Approximate distance from the electrical room/service to the candidate parking rows` (ft/m unstated). By contrast :20 item 3 does specify units (`kWh and peak demand kW by month`) and :27 item 8 specifies `daily mileage, dwell windows`.

### M-42 · `docs/human-actions/public_engagement/08_STAKEHOLDER_CONTACT_MAP.md`
**Lane:** L08-human-actions · **Category:** consent-not-obtained · **Confirmed:** not yet re-checked by the lead

**Claim.** No facility manager has been identified, contacted, or granted any permission at any of the three top sites. Any Phase-5 artifact that presents charger placement as authorised would directly contradict three files in this lane.

**Evidence.** docs/human-actions/public_engagement/08_STAKEHOLDER_CONTACT_MAP.md:15-17 — all three facility-manager rows read `[TO BE IDENTIFIED]` with Status `Placeholder` (FFX002 City of Fairfax Regional Library; FFX004 Fairfax County Government Center; PWC006 Bull Run Library `[TO BE IDENTIFIED — route via [client contact]/PWC facilities]`). docs/human-actions/utility_facility_data/03_TRACKING_REGISTER.md — all 33 rows (11 fields x 3 sites) are `not_requested`; :53 `Last updated: 2026-07-19 (creation; no requests sent)`. docs/human-actions/utility_facility_data/01_DATA_REQUEST_DOMINION.md:5 `a facility-owner authorization may be required for account-level data`. docs/human-actions/utility_facility_data/02_DATA_REQUEST_FACILITY_MANAGERS.md:5 `Nothing has been sent.`

### M-43 · `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md`
**Lane:** L09-deliverables · **Category:** claim-contradicted-by-data · **Confirmed:** yes — LEDGER FIND-NUM-01

**Claim.** 'Even peak-window P90 waits sit under the 10-minute target at every top site' is true only because every P90 column is zero; the contract contains 21 rows with peak_wait_minutes > 10, up to 215.35 min, plus 5 blank peak-wait cells all at PWC002.

**Evidence.** Final_Report.md:84 'at current demand even peak-window P90 waits sit under the 10-minute target at every top site.' In tbl_canonical_scenarios.csv: 21 rows have peak_wait_minutes > 10 (PWC002_2026_baseline 42.37, PWC002_2036_high 109.83, PWC002_2036_stress_combined 211.47, PWC002_2046_base 215.35, PWC008_2046_high 20.43, ...); max average_wait_minutes = 68.72; and peak_wait_minutes is blank for PWC002_2046_high, PWC002_2046_stress_combined, PWC002_2056_base, PWC002_2056_high, PWC002_2056_stress_combined.

### M-44 · `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md`
**Lane:** L09-deliverables · **Category:** broken-path · **Confirmed:** not yet re-checked by the lead

**Claim.** The offline-open QA checklist points at presentation/static_visuals/, a directory that does not exist anywhere in the repository, and the surrounding text contradicts presentation/README.md's 'single source, no duplicates' rule.

**Evidence.** Timing_Runbook.md:65 '- [ ] Open all 11 files in `static_visuals/` directly — each PNG opens offline'. `find . -name "static_visuals*"` over the repo returns zero matches. The count 11 matches dashboard/static/ (9 PNGs + footer_log.json + STATIC_DASHBOARD.pdf). Runbook:62 says 'Copy the whole `presentation/` folder'; Final_Report.md:124 says 'self-contained static visuals (`presentation/`)'; but presentation/ contains only assets/10_mcda_provisional.png, and presentation/README.md:15-16 states 'The nine shared data visuals live in `dashboard/static/` — single source, no duplicates.'

### M-45 · `dashboard/static/footer_log.json`
**Lane:** L09-deliverables · **Category:** absolute-local-paths · **Confirmed:** yes — LEDGER FIND-REPO-03

**Claim.** All nine entries of the tracked footer audit log carry absolute paths on the author's local machine, pointing at a directory tree that does not exist in the repo.

**Evidence.** dashboard/static/footer_log.json lines 7, 14, 21, 28, 35, 42, 49, 56, 59: "file": "/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/Milestone_2_Full_Implementation/visuals/static_dashboard/<name>.png". The verify gate still passes because src/fcf_m2/visuals.py:76 matches on Path(e['file']).name only. No secrets, tokens, AWS account IDs or keys were found anywhere in this lane.

### M-46 · `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md`
**Lane:** L09-deliverables · **Category:** dead-reference · **Confirmed:** yes — LEDGER FIND-NUM-01

**Claim.** The Final Report's integrity footer cites two manifests that do not exist in the tree, and the document it says it supersedes is also absent.

**Evidence.** Final_Report.md:156 'Full manifests: `00_IMPLEMENTATION_MANIFEST.md`, `verification/`.' Neither exists (checked at repo root and by find). Final_Report.md:8 'Supersedes: `Future_City_Fellowship_Milestone_2_Phase_Report.md` (July 2026) — that report remains the authoritative record of the Phase 2 build' — file not present. Separately, Gap_Closure_Status.md:46,69 cite lifecycle_costs.csv and :64 cites avoided_evse_metric.csv as contract evidence; both live at data/outputs/v3_run/, not data/contract/v1/. dashboard/README.md:8 names 'verify.sh'; actual path is scripts/verify.sh (the footer-gate claim itself is true — scripts/verify.sh:49-53).

### M-47 · `dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md`
**Lane:** L09-deliverables · **Category:** tableau-capability-boundary · **Confirmed:** not yet re-checked by the lead

**Claim.** The Tableau build recipe requires stories, reference lines, dashboard filter cards, cross-file joins and top-N sets; 5 of its 12 specified items are NOT-BUILDABLE against the stated capability boundary, and the recipe is internally inconsistent in four separate places.

**Evidence.** TABLEAU_IMPLEMENTATION_BLOCKER.md:30 'join nothing on names — join on `site_id`' (joins); :39 'reference line y=48 "pathway ceiling"'; :44 'reference line 10 min'; :46 'Map — lat/lon from sites dimension, size by ports_pathway, color top-3' (needs a join for ports_pathway_capacity + a set/group for top-3); :48-49 'filters kept minimal (single horizon-year filter, applied to worksheets 3–5 only)' (dashboard filter card/action — and worksheet 3 is not on the dashboard, which lists 'worksheets 1/2/4/5 + map'); :49-50 'Story: 8 points in the order of the static dashboard files 01→09' (stories — and 01→09 is nine files, not eight); :53 'every number matches `tbl_canonical_scenarios.csv`' (that file's 48 columns contain no readiness_score, no wait percentiles and no portfolio NPVs). BUILDABLE as written: worksheets 1, 2, 4, 5 and the mandatory caption rule.

### M-48 · `reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md`
**Lane:** L09-deliverables · **Category:** egrid-factor · **Confirmed:** not yet re-checked by the lead

**Claim.** 590.2 survives in two report-tier documents; both occurrences are explicit correction notes with 596.3 asserted as operative, so nothing computes from it, but the lane rule says it must survive nowhere.

**Evidence.** ENVIRONMENT_AND_RESILIENCE.md:22 'Correction note: the research package (EX10) carried ≈590.2; the implementation run verified EPA's published SRVC CO2e total output rate as 596.326 lb/MWh. 596.3 with vintage label is the value used everywhere in this implementation.' Final_Report.md:27 '596.3 lb CO2e/MWh, accessed 2026-07-19 — the research package's 590.2 figure was superseded by direct EPA verification'. Repo-wide, 590.2 also appears at CHANGELOG.md:24 and docs/methodology/current-facts-source-register.md:7 (both correction notes) and at docs/operations/v4-program/LEDGER.md:139 and AWS_INVENTORY.md:140 (both saying it is absent from the live site). 596.3 is consistent everywhere: grid_factor_value='596.3' on all 120 contract rows, plus 13 prose/config occurrences.

### M-49 · `presentation/deck/Future_City_Fellowship_Milestone_2_Speaker_Notes.md`
**Lane:** L09-deliverables · **Category:** internal-contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** The proposed standard is described as having three modules in the speaker notes and seven test modules in the Final Report and Gap Closure status.

**Evidence.** Speaker_Notes.md:88 'Proposed standard: say the label exactly — "a fellowship design concept": *Municipal EV Charging Site Readiness and Emergency Access Standard*, three modules.' Final_Report.md:105 'defines seven test modules (emergency access/disconnect; expandability/right-sizing documentation; accessibility cross-references; monitoring/triggers; managed-charging fail-safe; commissioning evidence; materials/end-of-life) with three conformance levels.' Gap_Closure_Status.md:53 (C7) 'Seven test modules, conformance levels, intervals'. ENVIRONMENT_AND_RESILIENCE.md:44 cites 'proposed-standard Module 7'.

### M-50 · `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md`
**Lane:** L09-deliverables · **Category:** horizon-convention · **Confirmed:** yes — LEDGER FIND-NUM-01

**Claim.** Three prose instances use 10/20/30-year or bare 2050 without canonical-year pairing and without a legacy_v2 label; a fourth uses 'now' informally for the 2026 baseline.

**Evidence.** Speaker_Notes.md:131 'Andy→Adama (slide 10): "Adama has the 30-year numbers."'; Final_Report.md:152 'how to keep a 30-year model honest when 10-year goals are already off-track'; Final_Report.md:92 'eliminating the hand-built CSV and its 2050-base/high port mismatch'; Speaker_Notes.md:76 'net avoided CO2e grows from ≈43 t/yr now to ≈173–260 t/yr by 2056'. LEGITIMATE by contrast (do not change): Final_Report.md:82 pairs '10/20/30-year timelines' with 'the canonical convention 2036/2046/2056 from a stated 2026 baseline'; Gap_Closure_Status.md:41,42,43,62 pair each criterion title with its canonical year; ENVIRONMENT_AND_RESILIENCE.md:17's 2030/2035/2050 are external PWC CESMP policy targets attributed to EX14; footer_log.json:6 'legacy_v2 baseline scores' is correctly labelled; '~10-year electronics refresh' (ECON:42, ENV:42, Final_Report:86, RISK R15) is an equipment service life, not a horizon.

### M-51 · `reports/milestone-2/ECONOMIC_AND_FUNDING_BRIEF.md`
**Lane:** L09-deliverables · **Category:** headline-number-does-not-trace · **Confirmed:** not yet re-checked by the lead

**Claim.** The $429,500 12-site screening cost is quoted in five places but is not any value in the contract-derived portfolio cost table.

**Evidence.** ECONOMIC_AND_FUNDING_BRIEF.md:5 'The $429,500 12-site model output is a screening value, never a budget', :43 'The $429,500 across 12 sites sits within published benchmark ranges'; Final_Report.md:131 'the $429,500-class screens are not budgets'; RISK_REGISTER.md:14 and RISK_REGISTER.csv:18 '$429500 12-site figure held as screening value never budget'. tbl_portfolio_costs.csv contains 27 rows whose base-case STG NPVs are 1,560,499 / 2,294,469 / 3,014,200 and whose DEF value is a constant 617,403; 429,500 appears nowhere. Other untraced headline numbers in this lane: 86.4/100 (BLOCKER:23), 38 REVIEW + 12 INFO (Speaker_Notes:64, Final_Report:22,51), 15 Tableau exports and 35-file package (Final_Report:22,51), 80 tests / 92% coverage (Final_Report:23), six live reconciliation checks all PASS (excel/README:18, Final_Report:119), growth multipliers 1.9/2.6→3.0/4.5→4.0/6.0 ×1.15 (Final_Report:84).

### M-52 · `incoming/explorer/fcf-3d/Makefile`
**Lane:** L10-explorer-python · **Category:** integration-blocker · **Confirmed:** not yet re-checked by the lead

**Claim.** The Makefile hardcodes "is this the model repo?" as "does it contain tests/fixture_legacy_v2_site_results.csv", in both the doctor gate and the candidates scanner. A V3-only checkout is rejected with an explicit "it is not the model repo" message.

**Evidence.** Makefile:77 `@test -f "$(FCF)/tests/fixture_legacy_v2_site_results.csv" || {`; Makefile:80 `echo "  tests/fixture_legacy_v2_site_results.csv, so it is not the model repo."`; Makefile:92 `if [ -f "$$d/tests/fixture_legacy_v2_site_results.csv" ]; then`

### M-53 · `incoming/explorer/fcf-3d/tests/test_pipeline.py`
**Lane:** L10-explorer-python · **Category:** test-coverage · **Confirmed:** not yet re-checked by the lead

**Claim.** 15 of the 46 collected tests silently skip unless FCF_REPO resolves to a real directory, including the load-bearing attribution test. The default path is machine-specific.

**Evidence.** tests/test_pipeline.py:35-38 — REPO = os.environ.get("FCF_REPO", os.path.expanduser("~/fcf/Future-City-Fellowship--main-2")); needs_repo = pytest.mark.skipif(not os.path.isdir(REPO), reason=...). grep -c "@needs_repo" = 15.

### M-54 · `incoming/explorer/fcf-3d/fcf3d/build_sites.py`
**Lane:** L10-explorer-python · **Category:** dead-code · **Confirmed:** not yet re-checked by the lead

**Claim.** The readiness_conf source (tbl_readiness_confidence.csv) is resolved and loaded into a DataFrame but never consumed by build(); it only inflates the manifest sources block. This is also the likely origin of README's "seven tables" undercount — the code resolves eight.

**Evidence.** build_sites.py:55 "readiness_conf": "dashboard/tableau/patch_package/tbl_readiness_confidence.csv"; frames["readiness_conf"] appears nowhere in build() (lines 338-538). build_sites.py docstring lines 11-18 lists only 7 source tables, omitting readiness_conf. README.md:66-67 "It joins seven frozen model tables on `site_id`". The shipped web/data/manifest.json sources block lists 8 entries.

### M-55 · `fcf-3d/web/style.css`
**Lane:** L11-explorer-web · **Category:** accessibility · **Confirmed:** not yet re-checked by the lead

**Claim.** No prefers-reduced-motion support; a 2.2s camera flight fires unconditionally at startup and 2.0s flights on every selection.

**Evidence.** grep for `prefers-reduced-motion` in web/style.css returns zero hits. app.js:376 `duration: 2.2` in flyHome(), called unconditionally at app.js:868. app.js:368 `duration: 2.0` in flyTo(), called from select() at app.js:355.

### M-56 · `fcf-3d/web/data/sites.inline.js`
**Lane:** L11-explorer-web · **Category:** broken-fallback · **Confirmed:** not yet re-checked by the lead

**Claim.** The documented file:// fallback via sites.inline.js cannot work, and app.js contradicts itself about it 14 lines apart.

**Evidence.** app.js:87-88 comment: "Falls back to the inlined copy so the app also runs straight off the filesystem with no web server." But index.html:118 is `<script src="app.js" type="module"></script>` — module scripts are blocked over file://, so app.js never executes and the `await import('./data/sites.inline.js')` at app.js:97 is blocked identically. No `<script>` tag in index.html loads sites.inline.js (grep for `inline` in index.html: no hits), so `window.__FCF_SITES__` at app.js:94 is never set independently. app.js:101-104 then says the opposite and correct thing: "serve this directory (python -m http.server 8080) rather than opening the file directly."

### M-57 · `fcf-3d/web/data/sites.geojson`
**Lane:** L11-explorer-web · **Category:** spec-conformance · **Confirmed:** not yet re-checked by the lead

**Claim.** sites.geojson carries a top-level `crs` member, which RFC 7946 section 4 removed from the spec.

**Evidence.** sites.geojson top-level keys are ['type', 'name', 'crs', 'metadata', 'features']; crs = {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3/CRS84"}}. Also a non-standard top-level "name": "chargeready_nova_candidate_sites". Everything else validates: type=FeatureCollection, 12 Features, all geometry type Point, all coordinates 3-element [lon, lat, 0.0] in valid range.

### M-58 · `fcf-3d/web/data/sites.geojson`
**Lane:** L11-explorer-web · **Category:** data-contract · **Confirmed:** not yet re-checked by the lead

**Claim.** The GeoJSON property key set is not uniform: coordinate_provenance is present on only 6 of 12 features, and the panel silently omits the section for the other 6.

**Evidence.** Programmatic key-set diff across features: FFX004, PWC006, PWC007, FFX003, PWC008, PWC005 are each missing ['coordinate_provenance']; the other six (FFX002, FFX001, PWC002, PWC004, PWC001, PWC003) have it. app.js:566 guards with `${p.coordinate_provenance ? ` ... `: ''}` so nothing is displayed and no "unknown" statement is made. Coordinate precision also varies: 7 dp on FFX003 (-77.2680915, 38.7749268) and PWC008 (-77.2806337, 38.632723) vs 6 dp elsewhere.

### M-59 · `fcf-3d/web/style.css`
**Lane:** L11-explorer-web · **Category:** attribution · **Confirmed:** not yet re-checked by the lead

**Claim.** No authored attribution string for OpenStreetMap/ODbL, Google Photorealistic 3D Tiles, or CesiumJS; the required credit widget is deliberately shrunk and faded.

**Evidence.** grep -i for `odbl|attribution|contributors|©` across index.html and app.js returns no attribution text. style.css:45 comment: "/* trim Cesium's default chrome; keep the attribution credit, it's required */" followed by style.css:51-54 `.cesium-widget-credits { bottom: 4px !important; right: 8px !important; left: auto !important; font-size: 10px !important; opacity: .65; }` and :55 links set to --ink-2 (#9aa5b4) over --bg (#0c0e11). Separately app.js:148-150 points OpenStreetMapImageryProvider directly at 'https://tile.openstreetmap.org/', which the OSMF tile usage policy prohibits for systematic application use.

### M-60 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** licensing · **Confirmed:** not yet re-checked by the lead

**Claim.** Google Photorealistic 3D Tiles is instantiated without the onlyUsingWithGoogleGeocoder acknowledgement while the geocoder is explicitly disabled.

**Evidence.** app.js:208 `state.layers.photoreal = await Cesium.createGooglePhotorealistic3DTileset();` — zero arguments. Cesium ref-doc for createGooglePhotorealistic3DTileset(apiOptions, tilesetOptions) states a one-time warning is displayed unless the caller confirms "that this tileset will only be used with the Google geocoder". app.js:156 sets `geocoder: false` in the Viewer options. (The zero-argument call itself is still valid API — the 1.125 deprecation / 1.126 removal affected only the positional createGooglePhotorealistic3DTileset(key) form.)

### M-61 · `fcf-3d/.gitignore`
**Lane:** L11-explorer-web · **Category:** build-integration · **Confirmed:** not yet re-checked by the lead

**Claim.** Every generated data and model artifact in this lane is .gitignore'd, so a clone of the explorer ships with no data at all.

**Evidence.** fcf-3d/.gitignore lines 4-8: `web/data/sites.geojson`, `web/data/sites.json`, `web/data/sites.inline.js`, `web/data/manifest.json`, `web/models/*.glb`. The files exist on disk under incoming/explorer/fcf-3d only because they were built there (all four data files share mtime Jul 26 00:27). Regenerating them requires the upstream frozen outputs per CLAUDE.md (`make data FCF_REPO=/path/to/Future-City-Fellowship`).

### M-62 · `reports/milestone-2/FINAL_STANDARDS_APPLICATION_MATRIX.docx`
**Lane:** L12-binaries · **Category:** unreproducible-artifact · **Confirmed:** not yet re-checked by the lead

**Claim.** FINAL_STANDARDS_APPLICATION_MATRIX.docx and PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.docx were NOT produced by the tracked scripts/md_to_docx.py and cannot be reproduced by it — regenerating them would silently restyle the documents.

**Evidence.** Committed docx use styles Heading 1/2/3 and table style `Table Grid`. scripts/md_to_docx.py:68-76 maps `# `->add_heading(level=0) (=Title), `## `->level 1, `### `->level 2, and line 57 hardcodes `table.style = "Light Grid Accent 3"`; line 87 renders `---` as `doc.add_paragraph("_" * 60)` where the committed files have empty paragraphs. Regeneration diff: 97 and 96 lines respectively, dominated by these three systematic shifts. Their .md sources are also in a different directory: docs/standards/, not reports/milestone-2/.

### M-63 · `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md`
**Lane:** L12-binaries · **Category:** dead-link · **Confirmed:** not yet re-checked by the lead

**Claim.** presentation/static_visuals/ does not exist, but the Timing Runbook's pre-flight checklist and the PPTX slide 17 body text (hence the exported deck PDF) both instruct the presenter to open files there.

**Evidence.** presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md:65 `- [ ] Open all 11 files in `static_visuals/` directly`. PPTX slide 17 text: `every image in this deck opens offline from presentation/static_visuals/`. `ls -d presentation/*` returns only presentation/assets, presentation/deck, presentation/README.md. The 11 files now live split across dashboard/static/ (9 PNGs + STATIC_DASHBOARD.pdf) and presentation/assets/ (10_mcda_provisional.png). Not catchable by scripts/check_internal_links.py because it is in backticks, not a markdown link.

### M-64 · `docs/assets/readme/site-map.png`
**Lane:** L12-binaries · **Category:** orphan · **Confirmed:** not yet re-checked by the lead

**Claim.** Seven binaries are orphans: five reports/milestone-2 deliverables (1 PDF + 4 DOCX) and two docs/assets/readme PNGs are referenced by zero files in the repo. site-map.png and three-horizons.png additionally have no generator anywhere.

**Evidence.** grep -rIl --exclude-dir=.git -F over the whole repo returns 0 referrers for: Future_City_Fellowship_Milestone_2_Final_Report.pdf, Future_City_Fellowship_Milestone_2_Final_Report.docx, Milestone_2_Gap_Closure_Status.docx, FINAL_STANDARDS_APPLICATION_MATRIX.docx, PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.docx, docs/assets/readme/site-map.png, docs/assets/readme/three-horizons.png. README.md:10 references only project-overview.png. No *.py/*.sh/Makefile/*.yml writes to docs/assets or presentation/assets.

### M-65 · `incoming/explorer/fcf-3d/fcf3d/build_models.py`
**Lane:** L12-binaries · **Category:** horizon-convention · **Confirmed:** not yet re-checked by the lead

**Claim.** The 3D explorer's live code path reads 2050-keyed fields that are not a canonical horizon and are not labelled legacy_v2.

**Evidence.** incoming/explorer/fcf-3d/fcf3d/build_models.py:43 `ports_pathway=asset.get("pathway_ports", props.get("ports_2050") or 2)`; fcf3d/build_sites.py:437 `"ports_2050": _clean(row.get("recommended_ports_2050"))`, :465 `"ports_2050_base"`, :466 `"ports_2050_high"`. The committed GLBs are unaffected because asset.ports/asset.pathway_ports take precedence, but the fallback is live. Related note already in repo at docs/operations/v4-program/LEDGER.md:247.

### M-66 · `docs/operations/v4-program/LEDGER.md`
**Lane:** L12-binaries · **Category:** contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** docs/operations/v4-program/LEDGER.md FIND-REPO-03 undercounts the absolute-path leak: it says six paths, the actual count is nine.

**Evidence.** LEDGER.md:153 `**dashboard/static/footer_log.json contains six absolute authoring-machine paths** (/Users/andyyaro/Documents/Milestone 2 Gaps Addressing/…)`. Actual: `git grep -cI '/Users/andyyaro' -- '*.json'` returns `dashboard/static/footer_log.json:9`, one per JSON entry (lines 7,14,21,28,35,42,49,56,59).


---

## LOW — 48 findings

### L-01 · `src/fcf_m2.egg-info/SOURCES.txt`
**Lane:** L01-model-core · **Category:** stale-generated-artifact · **Confirmed:** not yet re-checked by the lead

**Claim.** The committed egg-info build metadata is stale relative to the tree it was generated from: SOURCES.txt omits tests/conftest.py even though conftest.py was committed in the same commit as the egg-info. All five egg-info files are tracked in git while .gitignore never excludes *.egg-info/.

**Evidence.** src/fcf_m2.egg-info/SOURCES.txt lines 25-28 list only test_contract_and_integration.py, test_legacy_golden.py, test_modules.py, test_scoring_and_queueing.py. `ls tests/` shows conftest.py, README.md, fixture_legacy_v2_right_sizing.csv, fixture_legacy_v2_site_results.csv in addition. `git log --oneline -- tests/conftest.py` and `git log --oneline -- src/fcf_m2.egg-info/SOURCES.txt` both return the same single commit 252099f. `git ls-files src/fcf_m2.egg-info/` lists all 5 files as tracked; .gitignore has no *.egg-info entry. (PKG-INFO/requires.txt/top_level.txt themselves match pyproject.toml exactly — version 3.0.0, all deps and extras identical.)

### L-02 · `src/fcf_m2/scoring.py`
**Lane:** L01-model-core · **Category:** dead-code · **Confirmed:** not yet re-checked by the lead

**Claim.** scoring.py computes an `access_adjustment` column (1.00 / 0.35) that is never used in any formula — only `readiness_access_adjustment` (1.00 / 0.65) is applied — yet access_adjustment ships in the output CSVs and in the golden fixture, where a reader would reasonably assume it is load-bearing.

**Evidence.** scoring.py:131 `df["access_adjustment"] = np.where(df["public_access"] >= 1, 1.00, 0.35)`; scoring.py:132 `df["readiness_access_adjustment"] = np.where(df["public_access"] >= 1, 1.00, 0.65)`; scoring.py:151 `df["demand_subscore"] = df["demand_subscore"] * df["readiness_access_adjustment"]`. grep for 'access_adjustment' across src/ tests/ scripts/ dashboard/ excel/ presentation/ returns only those three code lines plus the header row of tests/fixture_legacy_v2_site_results.csv, which carries both columns.

### L-03 · `src/fcf_m2/scoring.py`
**Lane:** L01-model-core · **Category:** inert-config · **Confirmed:** not yet re-checked by the lead

**Claim.** The anchor set declares an `ev_share_local` anchor that the scoring code never reads, because ev_share_local is not in NORMALIZE_COLS and is instead always normalised by the module-level EV_SHARE_HIGH_BENCHMARK constant. Editing that anchor has no effect on any score.

**Evidence.** data/anchors/anchor_set_v1.json anchors block includes `"ev_share_local": {"lo": 0, "hi": 0.10, "note": "legacy fixed benchmark EV_SHARE_HIGH_BENCHMARK retained"}`. scoring.py:42-46 NORMALIZE_COLS does not include ev_share_local. scoring.py:138 `df["ev_share_local_n"] = bounded_signal(df["ev_share_local"], EV_SHARE_HIGH_BENCHMARK)` runs unconditionally in both modes, using scoring.py:26 `EV_SHARE_HIGH_BENCHMARK = 0.10`. Set-difference check: anchors not in NORMALIZE_COLS = ['ev_share_local']; NORMALIZE_COLS lacking anchors = [] (so anchor_fallback_fields is always empty).

### L-04 · `src/fcf_m2/right_sizing.py`
**Lane:** L01-model-core · **Category:** inconsistent-threshold · **Confirmed:** not yet re-checked by the lead

**Claim.** Two modules disagree on the rank cutoff for 'top of the list': the tier assignment uses rank<=2 while the expansion-strategy assignment uses rank<=3, so a rank-3 site can receive the 'install now and make future ready' strategy without being Tier 1.

**Evidence.** scoring.py:206 `if row["model_rank"] <= 2 and row["readiness_score"] >= 50: return "Tier 1 — advance to site screening"`. right_sizing.py:134 `if tier.startswith("Tier 1") or (rank <= 3 and score >= 50): return ("install_now_and_make_future_ready", ...)`. A third cutoff appears at right_sizing.py:90 `elif score >= 50 and rank <= 6 and "garage" not in site_type`.

### L-05 · `src/fcf_m2/workflow.py`
**Lane:** L01-model-core · **Category:** timestamp-inconsistency · **Confirmed:** not yet re-checked by the lead

**Claim.** The CLI's default output directory is stamped in local time while the run_id embedded in every contract row is stamped in UTC, so a default-invoked run produces a directory name that can disagree with the run_id it contains by up to a day.

**Evidence.** workflow.py:97 `run_id = f"{mode}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"`. workflow.py:363 `out = Path(args.out) if args.out else ROOT / "data/outputs" / datetime.now().strftime("run_%Y%m%d_%H%M%S")` — naive datetime.now(), no tz.

### L-06 · `scripts/verify.sh`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** yes — LEDGER FIND-REPO-01/02

**Claim.** Three different output directories are used for the same legacy-reproduction check, and the release packager only knows one of them.

**Evidence.** scripts/verify.sh:27 → data/outputs/verify_legacy; Makefile:12 → data/outputs/legacy_check; .github/workflows/tests.yml:32 → data/outputs/ci_legacy; build_release_artifact.py:23 OUTPUTS = ['data/outputs/v3_run', 'data/outputs/legacy_check'].

### L-07 · `pyproject.toml`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** The 80% coverage floor is duplicated in two hard-coded places and absent from pyproject.toml; `make test` applies no floor at all.

**Evidence.** scripts/verify.sh:24 and .github/workflows/tests.yml:28 both pass `--cov-fail-under=80`. pyproject.toml:25-27 [tool.pytest.ini_options] has only testpaths and addopts='-q'. Makefile:9 = `pytest tests/ -q --cov=fcf_m2 --cov-report=term`. Measured total: 92.15%.

### L-08 · `scripts/build_release_artifact.py`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** build_release_artifact.py will silently produce a release ZIP containing no model outputs, because both OUTPUTS directories are gitignored and absent from the working tree, and the script has no existence check.

**Evidence.** build_release_artifact.py:23 OUTPUTS = ['data/outputs/v3_run', 'data/outputs/legacy_check']; .gitignore:11 'data/outputs/'; both paths return MISSING on the current tree; lines 61-66 just skip non-existent items.

### L-09 · `scripts/README.md`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** scripts/README.md omits the `make run-v3` prerequisite for build_excel_workbook.py, and its blanket claim that all scripts use repo-relative paths is contradicted by the committed footer_log.json.

**Evidence.** scripts/README.md:10 mentions only '--source'; build_excel_workbook.py:140 reads data/outputs/v3_run/lifecycle_costs.csv and :208 avoided_evse_metric.csv. excel/README.md:20-21 states the prerequisite correctly. scripts/README.md:15-16: 'All scripts use repo-relative paths...'.

### L-10 · `scripts/build_field_provenance.py`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** build_field_provenance.py contains a branch that can never execute and a hard-coded verification_status.

**Evidence.** Line 55 selects 'verified_facility' when elec_service_rating_amp > 0 and spare_capacity_kw > 0, but all 12 sites have both == 0 (tests/fixture_legacy_v2_site_results.csv, columns elec_service_rating_amp / spare_capacity_kw). Line 45: 'verification_status': 'spot_checked' for all 84 rows.

### L-11 · `matlab/src/electricalEconomics.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** The ML-11 electrical-fidelity outputs are computed and then dropped: apparent power (kVA), peak_reduction_kW and the absolute demand-charge figures never reach results.csv, and PowerFactor is not exposed by runScenario or run_all_scenarios so the batch is permanently pinned at 0.95.

**Evidence.** electricalEconomics.m:77-79 computes `peak_kVA_unmanaged`, `peak_kVA_managed`, `peak_reduction_kW` and :137-138 the absolute demand charges; runScenario.m:157-160 copies only `econ.service_check`, `econ.cost_status`, `econ.demand_charge_savings_usd_month` into metrics. electricalEconomics.m:54 `addParameter(p, "PowerFactor", 0.95, ...)` has no counterpart in runScenario.m:44-61 or run_all_scenarios.m:43-59.

### L-12 · `matlab/src/run_all_scenarios.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** yes — LEDGER FIND-MATLAB-04

**Claim.** manifest.txt does not record ChargerEfficiency, DiversityFactor, PowerFactor or CommsLoss, so a run that varied any of them could not be reproduced from its own manifest.

**Evidence.** run_all_scenarios.m:126-138 writes exactly run_id, generated_utc, matlab_release, input_csv, scenario_rows, profile_mode, seed, tariff_supplied, assumed_site_capacity_kW plus a 3-line note. runScenario.m:54-60 exposes ChargerEfficiency, DiversityFactor and CommsLoss which run_all_scenarios never forwards or records.

### L-13 · `matlab/src/loadScenarios.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** yes — LEDGER FIND-MATLAB-01

**Claim.** loadScenarios attaches a provenance payload to the table that no consumer in src/ ever reads — run_all_scenarios recomputes the horizon list itself instead.

**Evidence.** loadScenarios.m:160-166 sets `T.Properties.Description` and `T.Properties.UserData` with source_csv, loaded_utc, horizons_in_data, cases_in_data; run_all_scenarios.m:80-81 instead does `fprintf("Horizons in data: %s\n", strjoin(string(unique(T.horizon_year)), ", "));`. Grep for `UserData` outside loadScenarios.m returns nothing.

### L-14 · `matlab/src/plotScenario.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** The scenario summary bar chart plots kW and kWh quantities on a single shared axis, which is dimensionally incoherent and should not be carried into the platform's own rendering.

**Evidence.** plotScenario.m:139-157 mixes `"Peak unmanaged (kW)"`, `"Curtailed, clamp (kWh)"`, `"Peak energy-aware (kW)"`, `"Unmet, energy-aware (kWh)"` into one `bar(ax3, cats, values, ...)` with `ylabel(ax3, "kW / kWh", "FontWeight", "bold");` at :157.

### L-15 · `matlab/EXECUTION_STATUS.md`
**Lane:** L04-matlab-tests-docs · **Category:** unverifiable-claim · **Confirmed:** not yet re-checked by the lead

**Claim.** EXECUTION_STATUS.md asserts byte-identity against a producer file that does not exist in the clone (it is gitignored), so the claim cannot be verified from the repo alone.

**Evidence.** EXECUTION_STATUS.md:74-79 'data/canonical/matlab_scenarios.csv is byte-identical to the Python producer copy (repository-root data/outputs/v3_run/matlab_scenarios.csv, regenerated via make run-v3) ... - PASS.' `ls data/outputs/` -> no such directory; .gitignore:11 'data/outputs/'. Schema drift WAS independently ruled out: src/fcf_m2/matlab_adapter.py:15-19 MATLAB_COLUMNS matches the CSV header exactly (22 names, same order).

### L-16 · `matlab/RUN_ON_LICENSED_MATLAB.md`
**Lane:** L04-matlab-tests-docs · **Category:** stale-number-risk · **Confirmed:** not yet re-checked by the lead

**Claim.** The 205 kW / 153.6 kW capacity numbers in the licensed-run runbook and test fixtures trace only to a rejected V2 placeholder, not to any current data. Correctly labelled legacy everywhere it appears, but reusable out of context.

**Evidence.** RUN_ON_LICENSED_MATLAB.md:86 "'AssumedSiteCapacity_kW',205" and :90-91 'capacity line near 205 kW (legacy 51.4 + 153.6)'. 51.4 is FFX002 base_load_mean_kW (CSV line 2). 153.6 appears in no current data: spare_capacity_kW is empty on all 120 rows, and DATA_DICTIONARY.md:27 records 'unconfirmed - V2 upload value was rejected as placeholder'. Same number as fixture at test_capacityGuard.m:92,101 and as 8*19.2 theoreticalMax at test_profiles.m:51.

### L-17 · `matlab/DATA_DICTIONARY.md`
**Lane:** L04-matlab-tests-docs · **Category:** doc-code-mismatch · **Confirmed:** not yet re-checked by the lead

**Claim.** DATA_DICTIONARY says all 22 columns are required on load, but loadScenarios requires only 19 - model_rank, electrical_risk_level and source_note are not enforced.

**Evidence.** DATA_DICTIONARY.md:53 'All columns above are required; missing column => error.' vs src/loadScenarios.m:81-87 requiredCols list, which contains 19 names ending at 'managed_charging_policy' and omits model_rank, electrical_risk_level, source_note.

### L-18 · `matlab/src/loadScenarios.m`
**Lane:** L04-matlab-tests-docs · **Category:** latent-type-risk · **Confirmed:** yes — LEDGER FIND-MATLAB-01

**Claim.** The two all-empty numeric capacity columns are never type-forced on import, so whether they arrive as double-NaN or as text is an unverified detectImportOptions heuristic. Contained by capacityGuard's defensive conversion; unit tests cannot catch it.

**Evidence.** src/loadScenarios.m:59-69 forces string type on 9 text columns only; localAssertNumeric at :113-120 is not applied to spare_capacity_kW or service_capacity_kW. Both columns are empty on all 120 CSV rows. src/capacityGuard.m:184-192 localNumericOrNaN falls back to str2double, containing the failure. test_capacityGuard.m:142-143 hardcodes NaN so the unit tests never exercise the real import. EXECUTION_STATUS.md:87 already lists 'detectImportOptions name-value combinations' as a known gap.

### L-19 · `data/contract/v1/schema.json`
**Lane:** L05-data-contract · **Category:** api-inconsistency · **Confirmed:** not yet re-checked by the lead

**Claim.** Three different casing conventions are used for the same confidence concept across adjacent contract columns, so naive string comparison silently fails: capacity_confidence is lowercase (high/medium/low/none), data_confidence is capitalised (High/Medium/Low), and electrical_risk_level in the legacy input is lowercase (medium/high).

**Evidence.** schema.json:222-229 capacity_confidence enum ['high','medium','low','none']; schema.json:281-287 data_confidence enum ['High','Medium','Low']; legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv:2 electrical_risk_level='medium'.

### L-20 · `data/contract/v1/schema.json`
**Lane:** L05-data-contract · **Category:** horizon-convention · **Confirmed:** not yet re-checked by the lead

**Claim.** horizon_label carries relative-offset naming (now/plus10/plus20/plus30) alongside the canonical absolute horizon_year. Arithmetically consistent against a 2026 base, so not a convention violation — but any artifact that surfaces horizon_label raw renders exactly the 'Now / 10 / 20 / 30-year' vocabulary the program is trying to purge from prose.

**Evidence.** schema.json:98-105 horizon_label enum ['now','plus10','plus20','plus30']; scenario_table.csv col 10 distribution now×12, plus10×36, plus20×36, plus30×36, perfectly aligned with horizon_year 2026×12, 2036×36, 2046×36, 2056×36.

### L-21 · `data/contract/v1/schema.json`
**Lane:** L05-data-contract · **Category:** egrid-factor · **Confirmed:** not yet re-checked by the lead

**Claim.** 590.2 is absent from the entire data layer (correct), but survives in 4 documentation files. In all four it is explicitly narrated as the superseded value, so these are legitimate correction notes rather than live figures — however the brief's standard is 'must survive NOWHERE', so Phase 1 needs an explicit keep-or-scrub decision.

**Evidence.** grep -rn '590\.2' over data/ returns zero hits. Repo-wide, exactly 4 hits, all correction narratives: CHANGELOG.md:24 '**596.3 lb CO2e/MWh** — correcting the 590.2 figure used earlier'; docs/methodology/current-facts-source-register.md:7 '**Correction:** research register EX10 carried ≈590.2; EPA's published CO2e total output rate for SRVC is 596.326 lb/MWh'; reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:27 'the research package's 590.2 figure was superseded by direct EPA verification'; reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:22 'the research package (EX10) carried ≈590.2...'. Contract side is hard-locked: schema.json:266 'grid_factor_value': {'const': 596.3}.

### L-22 · `data/cache/boundaries/tl_2024_va_counties.geojson`
**Lane:** L05-data-contract · **Category:** join-key-hazard · **Confirmed:** not yet re-checked by the lead

**Claim.** The cached county GeoJSON contains two features both named 'Fairfax' (Fairfax County and the independent City of Fairfax). Any consumer joining or labelling on NAME alone will collide or double-count; the same trap applies to Manassas / Manassas Park. Joins must use GEOID or NAMELSAD.

**Evidence.** data/cache/boundaries/tl_2024_va_counties.geojson parses as valid JSON, FeatureCollection, 25 features, crs EPSG:4269, STATEFP set {'51'}. NAME list in file order includes 'Fairfax' at index 8 and again at index 17, plus 'Manassas Park' (index 10) and 'Manassas' (index 21). Feature property keys are exactly ['GEOID','NAME','NAMELSAD','STATEFP'].

### L-23 · `scripts/verify.sh`
**Lane:** L06-root-ci · **Category:** nondeterministic-gate · **Confirmed:** yes — LEDGER FIND-REPO-01/02

**Claim.** verify.sh's markdown-link gate behaves differently depending on whether lychee happens to be installed on the machine, so the harness is not reproducible; CI always runs the weaker internal-only check.

**Evidence.** scripts/verify.sh:66 'if command -v lychee >/dev/null; then lychee --offline --no-progress README.md docs reports presentation dashboard excel matlab src tests scripts data ...; else "$PY" scripts/check_internal_links.py; fi' vs .github/workflows/tests.yml:53 'python scripts/check_internal_links.py'.

### L-24 · `CHANGELOG.md`
**Lane:** L06-root-ci · **Category:** horizon-convention · **Confirmed:** not yet re-checked by the lead

**Claim.** CHANGELOG says the mixed 'Now/2035/2050' conventions were replaced, but the canonical contract itself still uses the token 'now' as the horizon_label for 2026. Defensible (2026 is the baseline) but needs a Phase-1 decision given the standing rule about bare 'Now'.

**Evidence.** CHANGELOG.md:16-17 'Canonical horizons 2036 / 2046 / 2056 (10/20/30 years from a 2026 baseline), replacing the mixed Now/2035/2050 conventions.' vs data/contract/v1/scenario_table.csv horizon_label distinct values = {now, plus10, plus20, plus30}; row 2 '...,2026,now,FFX002_2026_baseline,baseline,...'.

### L-25 · `CHANGELOG.md`
**Lane:** L06-root-ci · **Category:** changelog-staleness · **Confirmed:** not yet re-checked by the lead

**Claim.** CHANGELOG.md has no entry (and no Unreleased section) for the V4 platform program, although tag pre-v4-program-20260727 and HEAD commit 95e91e0 adding docs/operations/v4-program/LEDGER.md are already on the working branch.

**Evidence.** CHANGELOG.md contains exactly two headings: '## Milestone 2 V3 (2026-07-19)' (line 3) and '## Pre-V3 history' (line 45). git log shows HEAD 95e91e0 'docs(v4-program): initialize program ledger' adding docs/operations/v4-program/LEDGER.md (147 lines); git tag -l includes pre-v4-program-20260727.

### L-26 · `docs/operations/website-patch-package/content/results_2036_2046_2056.md`
**Lane:** L07-docs-core · **Category:** imprecise-number · **Confirmed:** yes — LEDGER FIND-NUM-01

**Claim.** The claim that the staged plan 'avoids energizing 13–23 pathway ports' sits under a '10 / 20 / 30 years' heading and reads as a range across the three horizons, but the underlying data gives 23 at the 2026 baseline and 13 at 2036 base, dropping to 4 at both 2046 base and 2056 base. It overstates the later horizons.

**Evidence.** docs/operations/website-patch-package/content/results_2036_2046_2056.md:29 'The staged plan also avoids energizing 13–23 pathway ports that current demand does not justify'. dashboard/tableau/patch_package/tbl_avoided_evse.csv summed by horizon/case: ('2026','baseline') 23.0, ('2036','base') 13.0, ('2046','base') 4.0, ('2056','base') 4.0. Metric defined at src/fcf_m2/emissions.py:78 df['avoided_active_evse_ports'] = (df['ports_pathway'] - df['ports_active']).clip(lower=0).

### L-27 · `docs/operations/legacy-baseline/BASELINE_VERIFICATION.md`
**Lane:** L07-docs-core · **Category:** horizon-labelling · **Confirmed:** not yet re-checked by the lead

**Claim.** The legacy 2035/2050 headline row in BASELINE_VERIFICATION.md is legitimate legacy content (the whole document is about the reproduced V1/V2 baseline) but the row itself carries no legacy_v2 token, so it reads as a horizon violation if quoted out of context. Its numbers 35/44/44 also visually collide with the V3 contract's 35/44/44 while meaning something different (legacy ends at 54, V3 at 48).

**Evidence.** docs/operations/legacy-baseline/BASELINE_VERIFICATION.md:22 '| 2035 base / 2035 high / 2050 base / 2050 high | 35 / 44 / 44 / 54 | 35 / 44 / 44 / 54 |' under the heading ':14 ## Headline metrics — all match expected values exactly'. Contrast with the correctly self-labelling docs/WORKFLOW_STEPS.md:7 '(legacy 2035/2050 or V3 2026/2036/2046/2056)'.

### L-28 · `docs/operations/reproduction-guide.md`
**Lane:** L07-docs-core · **Category:** version-inconsistency · **Confirmed:** not yet re-checked by the lead

**Claim.** The Python version is stated three different ways across the repo, which Phase 10's clean-clone test needs resolved to one pinned answer.

**Evidence.** docs/operations/reproduction-guide.md:5-6 'verified on macOS (Apple Silicon) with Python 3.14 on 2026-07-19. Python 3.11+ is supported.'; docs/operations/legacy-baseline/BASELINE_VERIFICATION.md:3 'using a dedicated legacy virtual environment (Python 3.14.6; unpinned legacy requirements + GIS extras)'; .github/workflows/tests.yml 'python-version: "3.12"'.

### L-29 · `docs/human-actions/public_engagement/05_PRIVACY_NOTICE.md`
**Lane:** L08-human-actions · **Category:** internal-contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** Two divergent privacy notices describe the project website's assistant differently: the public engagement notice presents it as an open explainer the public might type into, while the website patch package says it is restricted to authenticated Cognito users and that conversations may be logged. The public-facing notice mentions neither authentication nor logging.

**Evidence.** docs/human-actions/public_engagement/05_PRIVACY_NOTICE.md:13 `**The website assistant explains — it does not collect.** Our project website's assistant exists to explain the study... you should not enter personal information into it.`; docs/human-actions/public_engagement/03_LISTENING_SESSION_ONE_PAGER.md:34 `not through our project website's assistant, which only explains the project`. Versus docs/operations/website-patch-package/content/privacy_notice.md `**The AI Assistant is restricted to approved, authenticated users** (Cognito)... Assistant conversations may be logged for quality and security`. Neither is live: docs/operations/v4-program/LEDGER.md:138 FIND-AWS-02 `The website patch package was **never applied**... `privacy.html` and `standards.html` both **403**`.

### L-30 · `docs/human-actions/public_engagement/05_PRIVACY_NOTICE.md`
**Lane:** L08-human-actions · **Category:** stale-text · **Confirmed:** not yet re-checked by the lead

**Claim.** Present-tense deployment language inside instruments that are explicitly undeployed: the privacy notice describes itself as already printed and posted, and the listening-session one-pager advertises a Spanish survey that does not exist.

**Evidence.** docs/human-actions/public_engagement/05_PRIVACY_NOTICE.md:1 header `# DRAFT — PREPARED 2026-07-19 — NOT PUBLISHED` but :5 `Printed on survey forms, on the listening-session handout, and posted on the project website.` and :22 `Spanish version: [PENDING — see language access plan]`. docs/human-actions/public_engagement/03_LISTENING_SESSION_ONE_PAGER.md:35 `Survey (5 min, anonymous, English/Español): [QR / LINK WHEN DEPLOYED]` while docs/human-actions/public_engagement/04_LANGUAGE_ACCESS_PLAN.md:3 states `No translations have been produced yet.` and its production register (lines 16-21) is entirely blank.

### L-31 · `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md`
**Lane:** L09-deliverables · **Category:** partial-claim · **Confirmed:** yes — LEDGER FIND-NUM-01

**Claim.** '13–23 pathway ports deliberately not energized on the base path' quotes only the 2026 and 2036 values and omits 2046/2056, where the figure is 4.

**Evidence.** Final_Report.md:86 'paired with the avoided-EVSE metric (13–23 pathway ports deliberately not energized on the base path)'. Summing avoided_active_evse_ports in tbl_avoided_evse.csv on the base path: 2026 baseline = 23 (lines 2,12,22,32,42,52,62,72,82,92,102,112), 2036 base = 13, 2046 base = 4, 2056 base = 4. Note 48 − 35 = 13 at 2036 independently corroborates that the contract's 2036 base port total is 35, not the 44 published (see the port-series finding).

### L-32 · `reports/milestone-2/RISK_REGISTER.md`
**Lane:** L09-deliverables · **Category:** internal-contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** The risk register's provenance arithmetic does not close: it says 15 failure modes plus 'four' cross-cutting risks, then lists five, and neither sum reaches the register's 18 rows.

**Evidence.** RISK_REGISTER.md:5 'upgraded from the research-phase failure-mitigation ranking FAILURE_MITIGATION_OPTIONS.csv (pre-V3 research archive, not tracked in this repository; 15 assessed failure modes) plus four cross-cutting risks from Reports 07–10: ADA redesign, overbuild/underuse, trenching cost escalation, data staleness, and funding volatility.' That list has five items; 15+4=19 and 15+5=20, but the register has 18 rows. In RISK_REGISTER.csv, R01–R16 all cite FAILURE_MITIGATION_OPTIONS row numbers (16 risks) and only R17/R18 do not, implying 16+2=18.

### L-33 · `dashboard/tableau/patch_package/tbl_portfolio_costs.csv`
**Lane:** L09-deliverables · **Category:** data-quality · **Confirmed:** not yet re-checked by the lead

**Claim.** tbl_portfolio_costs.csv's DEF (defer) case is constant at 617,403 across all three horizons and all three escalation cases, with nominal exactly equal to NPV — no discounting and no escalation applied.

**Evidence.** tbl_portfolio_costs.csv lines 2-4, 11-13, 20-22: '2036,DEF,base,617403.0,617403.0,0.0,0.0', '2036,DEF,high,617403.0,617403.0,...', '2046,DEF,base,617403.0,617403.0,...', '2056,DEF,low,617403.0,617403.0,...'. By contrast STG and OVB rows vary correctly by horizon and escalation (e.g. 2056,OVB,high,6072548.0,4030270.0). Not quoted in any prose in this lane, so latent rather than active.

### L-34 · `incoming/explorer/fcf-3d/fcf3d/build_sites.py`
**Lane:** L10-explorer-python · **Category:** dead-reference · **Confirmed:** not yet re-checked by the lead

**Claim.** Comment points at a test file that does not exist in the tree.

**Evidence.** build_sites.py:89 — "# arithmetic, not a re-interpretation of it. test_build_sites.py asserts that". The only test file is tests/test_pipeline.py.

### L-35 · `incoming/explorer/fcf-3d/tests/test_pipeline.py`
**Lane:** L10-explorer-python · **Category:** internal-contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** Test docstring says four drivers are inverted; the assertion in the same function lists six.

**Evidence.** tests/test_pipeline.py:113 — """These four drivers are the ones fcf_m2.scoring wraps in (1 - x)."""; lines 115-122 assert inverted == {existing_ports_total_n, distance_to_service_ft_n, install_cost_est_usd_n, trenching_ft_n, garage_enclosed, stormwater_risk} — six entries.

### L-36 · `incoming/explorer/fcf-3d/README.md`
**Lane:** L10-explorer-python · **Category:** overclaim · **Confirmed:** not yet re-checked by the lead

**Claim.** README says the driver points sum back exactly for all 12 sites; one site is off by 0.1 and the actual gate is a ±0.15 tolerance.

**Evidence.** README.md:81 "Those numbers sum back to 58.8 exactly, for all 12 sites." My independent recomputation over repo/tests/fixture_legacy_v2_site_results.csv: PWC005 rebuilt=37.0 vs readiness_score=36.9, delta 0.100. build_sites.py:368 uses `if abs(rebuilt - actual) > 0.15`; test_pipeline.py:100 uses `<= 0.15`.

### L-37 · `incoming/explorer/fcf-3d/README.md`
**Lane:** L10-explorer-python · **Category:** prose-code-mismatch · **Confirmed:** not yet re-checked by the lead

**Claim.** README names a driver differently from the code's own label, so the prose cannot be traced back to the emitted field.

**Evidence.** README.md:78 "short service run +7.50 pts" vs build_sites.py:157 Driver("distance_to_service_ft_n", "Distance to electrical service", 0.25, ...)

### L-38 · `incoming/explorer/fcf-3d/.gitignore`
**Lane:** L10-explorer-python · **Category:** gitignore-gap · **Confirmed:** not yet re-checked by the lead

**Claim.** .gitignore lists the four generated web/data files by name rather than using a web/data/* glob, and omits venv/ (created by make setup) and *.blend (written by build_assets.py). It does correctly exclude web/models/*.glb.

**Evidence.** Full file, 9 lines: __pycache__/ | *.pyc | .pytest_cache/ | web/data/sites.geojson | web/data/sites.json | web/data/sites.inline.js | web/data/manifest.json | web/models/*.glb | *.blend1. Makefile:31 `python3 -m venv $(VENV)` with VENV ?= venv. blender/build_assets.py:192 saves f"{sid}.blend".

### L-39 · `incoming/explorer/fcf-3d/fcf3d/build_sites.py`
**Lane:** L10-explorer-python · **Category:** fragile-join · **Confirmed:** not yet re-checked by the lead

**Claim.** The avoided-overbuild join filters on horizon_year == 2026 but not on the table's `case` column, then takes iloc[0]. Deterministic today, fragile to a contract change.

**Evidence.** build_sites.py:388 `m = avoided[(avoided["site_id"] == sid) & (avoided["horizon_year"] == 2026)]` then line 390 `m.iloc[0]`. repo/dashboard/tableau/patch_package/tbl_avoided_evse.csv has a `case` column; at horizon_year 2026 there are exactly 12 rows, all case='baseline'.

### L-40 · `fcf-3d/web/style.css`
**Lane:** L11-explorer-web · **Category:** generator-drift · **Confirmed:** not yet re-checked by the lead

**Claim.** Dead CSS rule for a pinned-state indicator that app.js never triggers, so pinned sites are invisible in the left rail.

**Evidence.** style.css:125 `#siteList li.pinned::after { content: "PIN"; }`. app.js:408 is the only class added to a list item: `if (p.site_id === state.selected) li.classList.add('selected');` — the string 'pinned' never appears as a classList argument in app.js.

### L-41 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** correctness · **Confirmed:** not yet re-checked by the lead

**Claim.** The comparison modal green-highlights the highest value on rows where highest is worst (mean wait and install cost), while the caption promises highest = best.

**Evidence.** app.js:784 `const best = isText ? -1 : nums.indexOf(Math.max(...nums.filter((n) => !Number.isNaN(n))));` applied to every non-text row. app.js:791 caption: "green marks the highest value in each numeric row". COMPARE_ROWS includes app.js:768 `['Mean wait (min)', (p) => num(p.mean_wait_min, 2)]` and app.js:769 `['Install cost (screening)', (p) => usd(p.install_cost_est_usd)]`.

### L-42 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** duplicated-constant · **Confirmed:** not yet re-checked by the lead

**Claim.** SUBSCORE_WEIGHTS is an unguarded third copy of the model weights, and the tier palette is duplicated between JS and CSS.

**Evidence.** app.js:26-31 `const SUBSCORE_WEIGHTS = { demand_subscore: 0.45, feasibility_subscore: 0.30, safety_subscore: 0.15, equity_subscore: 0.10 };`. CLAUDE.md states these mirror fcf3d/build_sites.py which mirrors fcf_m2/scoring.py, and that test_attribution_reproduces_model_score guards the Python copy; there is no JS test runner in the tree (only tests/test_pipeline.py). Tier colours duplicated: app.js:19-22 (#16b48b, #d9a23e, #7b8494, #d9534f) vs style.css:19-22 (--tier1..--tier4, same four values).

### L-43 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** data-contract · **Confirmed:** not yet re-checked by the lead

**Claim.** The placement editor emits a JSON key that does not exist in the asset contract, and no placement has ever been committed back.

**Evidence.** app.js:695 emits `height_offset_m: pl.height` inside the copied `asset` object; the generated asset dict keys are model, heading_deg, offset_east_m, offset_north_m, clamp_to_ground, ports, pathway_ports — no height_offset_m, and placementFor (app.js:240-246) never reads one. app.js:488 instructs the user to paste it back into sites.geojson properties.asset. All 12 sites currently have heading_deg=0.0, offset_east_m=0.0, offset_north_m=0.0.

### L-44 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** usability · **Confirmed:** not yet re-checked by the lead

**Claim.** A saved bad or expired Cesium ion token cannot be cleared from the UI, and the toast that mentions recovery gives impossible advice.

**Evidence.** app.js:879-880 `const saved = store.get('fcf3d.ionToken'); if (saved) { start(saved); return; }` — the gate is skipped entirely and there is no clear/replace control anywhere in index.html or app.js. app.js:193 toast: 'That base map needs a Cesium ion token. Reload and add one to enable it.' — a reload takes the stored-token path again.

### L-45 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** silent-failure · **Confirmed:** not yet re-checked by the lead

**Claim.** metadata.warnings emitted by the ETL is never checked, so any future ETL warning renders silently.

**Evidence.** sites.geojson metadata.warnings = [] and manifest.json:18 `"warnings": []`. grep for `warnings` in web/app.js returns zero hits; app.js:870-873 uses only meta.site_count and meta.schema_version.

### L-46 · `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.pdf`
**Lane:** L12-binaries · **Category:** egrid-factor · **Confirmed:** not yet re-checked by the lead

**Claim.** 590.2 survives in exactly one place across all 38 binaries — the Final Report DOCX and its exported PDF — inside an explicitly-labelled supersession sentence. It is not a live figure, but the lane rule says 590.2 must survive nowhere, so Phase 1 must adjudicate.

**Evidence.** Final Report PDF page 2 / DOCX §2: "a net-CO2e layer with a corrected, sourced grid factor (EPA eGRID2023 Rev 2, SRVC, 596.3 lb CO2e/MWh, accessed 2026-07-19 — the research package's 590.2 figure was superseded by direct EPA verification)". Token scan of all four PDFs, the PPTX, the XLSX and footer_log.json finds 596.3 in every live location and 590.2 nowhere else.

### L-47 · `dashboard/static/footer_log.json`
**Lane:** L12-binaries · **Category:** generated-artifact-drift · **Confirmed:** yes — LEDGER FIND-REPO-03

**Claim.** dashboard/static/footer_log.json has drifted from its generator in a second way beyond absoluteness: it records the pre-reorg directory visuals/static_dashboard/, whereas the current generator would emit dashboard/static/. It has never been regenerated since the repository reorganisation.

**Evidence.** footer_log.json entries all end `.../Milestone_2_Full_Implementation/visuals/static_dashboard/<name>.png`. scripts/build_static_dashboard.py:24 `OUT = REPO / "dashboard/static"`; src/fcf_m2/visuals.py:61 `entry["file"] = str(path)`. The footer audit still passes because audit_footer_metadata compares only Path(e["file"]).name. Entry 9 (09_site_map_offline.png) also has a different shape from entries 1-8: only file/source/source_date, no scenario or assumption key.

### L-48 · `excel/Electric_Data_Milestone_2_Updated.xlsx`
**Lane:** L12-binaries · **Category:** reproducibility · **Confirmed:** not yet re-checked by the lead

**Claim.** Three deliverables cannot be regenerated from a clean clone: the Excel workbook (needs an untracked source file), the QA Backup PDF (no .pptx source), and the Final deck .pptx (python-pptx output whose generating script is not tracked).

**Evidence.** scripts/build_excel_workbook.py:20-22 `_ap.add_argument("--source", required=True, help="Path to the original 'Electric Data.xlsx'")`, docstring `Original workbook is never modified`; excel/README.md `The original source workbook is not tracked in this repository`. presentation/deck/ contains only Future_City_Fellowship_Milestone_2_Final.pptx — no QA_Backup pptx. PPTX docProps/core.xml `<dc:description>generated using python-pptx</dc:description>` but no build script references the pptx path.


---

## INFO — 45 findings

### I-01 · `src/fcf_m2/config.py`
**Lane:** L01-model-core · **Category:** egrid-factor · **Confirmed:** not yet re-checked by the lead

**Claim.** The 590.2 eGRID figure survives in exactly four places repo-wide, and in every case it is explicitly labelled as the superseded/corrected-away value, never as a live factor. 596.3 is the only value in code, schema, and contract. No repair needed unless the program wants the string purged entirely.

**Evidence.** src/ contains zero occurrences of 590.2 (grep). The four surviving references: CHANGELOG.md:24 '**596.3 lb CO2e/MWh** — correcting the 590.2 figure used earlier.'; docs/methodology/current-facts-source-register.md:7 '**Correction:** research register EX10 carried ≈590.2; EPA's published CO2e total output rate for SRVC is 596.326 lb/MWh.'; reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:27 'the research package's 590.2 figure was superseded by direct EPA verification'; reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:22. Live value: config.py:91 `GRID_FACTOR_LB_PER_MWH = 596.3`, pinned as a JSON-Schema const at contract.py:117 and recorded in data/contract/v1/contract_manifest.json as `"value_lb_per_mwh": 596.3`; all 120 scenario rows carry grid_factor_value 596.3 (verified).

### I-02 · `scripts/build_excel_workbook.py`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** build_excel_workbook.py's portfolio chart plots 6 data points against 3 categories while titled 'base case'.

**Evidence.** Line 186 `Reference(wp, min_col=3, max_col=4, min_row=4, max_row=10)` spans header row 4 plus rows 5-10 = low(2036,2046,2056) + base(2036,2046,2056); line 187 `cats = Reference(wp, min_col=2, min_row=8, max_row=10)` = base horizons only; line 185 title '...by horizon (base case, screening)'.

### I-03 · `tests/test_legacy_golden.py`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** No horizon-convention violation exists in this lane: every 2035/2050 occurrence is inside an explicitly legacy-labelled artifact, and 2040 is a deliberate negative test.

**Evidence.** tests/test_legacy_golden.py:25-26 asserts ports_2035_base/high, ports_2050_base/high inside a module whose docstring is 'legacy_v2 mode must reproduce the frozen V2 baseline exactly' and which calls run_right_sizing_legacy. tests/test_contract_and_integration.py:52-56 test_unsupported_horizon_fails sets horizon_year = 2040 and asserts validation fails. No 'Now'/'10-year'/'20-year'/'30-year' strings in any assigned file.

### I-04 · `tests/test_modules.py`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** 596.3 is machine-asserted in two places and 590.2 appears nowhere in this lane; repo-wide the four 590.2 occurrences are all explicit correction notes.

**Evidence.** tests/test_modules.py:170 `assert out["grid_factor_value"] == 596.3`; tests/test_contract_and_integration.py:131 `assert (with_co2["grid_factor_value"] == 596.3).all()`. git grep '590\.2' → CHANGELOG.md:24, docs/methodology/current-facts-source-register.md:7, reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:22, reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:27 — all phrased as superseded.

### I-05 · `data/contract/v1/scenario_table.csv`
**Lane:** L02-tests-scripts · **Category:** — · **Confirmed:** yes — LEDGER FIND-NUM-01/02

**Claim.** The tracked contract and MATLAB canonical CSV have NOT drifted from their generator: a fresh V3 run reproduces them byte-for-byte apart from run_id/generated_at/source_note.

**Evidence.** I ran `workflow run --mode milestone2_v3 --out <scratchpad>/v3run`. site_table.csv and schema.json sha256 prefixes identical (0ed5e4ec7078, fb08b84ad2fd). scenario_table.csv: all 46 non-(run_id, generated_at) columns identical across 120 rows. matlab_scenarios.csv: only source_note differs, embedding the run id. Tracked run id = milestone2_v3_20260719T052322Z.

### I-06 · `matlab/src/run_all_scenarios.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** yes — LEDGER FIND-MATLAB-04

**Claim.** Backlog coverage gap: ML-02, ML-09 and ML-10 are never referenced anywhere in matlab/src/, while ML-01, ML-03, ML-04, ML-05, ML-06, ML-07, ML-08, ML-11 and ML-12 are. Similarly only H1, H2, H3, H4, H5 and H8 are referenced despite EXECUTION_STATUS.md citing H1-H15.

**Evidence.** grep -o 'ML-[0-9]*' over matlab/src/*.m yields only ML-01, ML-03, ML-04, ML-05, ML-06, ML-07, ML-08, ML-11, ML-12 (31 sites). Hypothesis refs: capacityGuard.m:2 (H3), buildSimulinkModel.m:8 (H8), managedCharging.m:12,115 (H4), makeSessionProfiles.m:9 (H1/H2/H5), :165 (H1). matlab/EXECUTION_STATUS.md:29 says "the Report 13 findings (H1-H15)".

### I-07 · `matlab/src/managedCharging.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** Docstring drift in three modules: documented output-field lists are incomplete relative to what the code actually returns.

**Evidence.** capacityGuard.m:33-42 lists 8 returned fields but :143-153 returns 10 (adds scenario_id, allowed_bases). managedCharging.m:50-53 lists 15 but :171-190 returns 19 (adds site_capacity_kW, peak_ev_kW, max_overload_kW, comms_loss). electricalEconomics.m:36-48 omits strategy_unmanaged, strategy_managed, service_check_note and tariff which :71-72, :112, :148 do set.

### I-08 · `matlab/src/run_all_scenarios.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** yes — LEDGER FIND-MATLAB-04

**Claim.** The variable named repoRoot in two files actually resolves to matlab/, not the git repository root. The resolved paths happen to be correct but the name will mislead anyone relocating the tree.

**Evidence.** run_all_scenarios.m:40-41 `thisDir = fileparts(mfilename("fullpath")); repoRoot = fileparts(thisDir);` — thisDir is matlab/src so repoRoot is matlab/. Same pattern at buildSimulinkModel.m:44-45, making the default ModelFolder matlab/simulink (:46).

### I-09 · `matlab/src/makeSessionProfiles.m`
**Lane:** L03-matlab-src · **Category:** — · **Confirmed:** not yet re-checked by the lead

**Claim.** CLEAN BILL for this lane on the four global defect classes: no horizon-convention violations, no eGRID emissions factor of any value, no absolute local paths, no secrets/keys/account IDs anywhere in the 9 files.

**Evidence.** grep -E '\b(2026|2030|2035|2036|2040|2046|2050|2056)\b|10-year|20-year|30-year|"Now"' matlab/src/*.m returns zero matches; grep -iE '596\.3|590\.2|egrid|co2|emission' matches only the local variable `eGrid` (grid-side energy) at makeSessionProfiles.m:151,156,168,173,174; grep -E '/Users/|AKIA|secret|token|password|api[_-]?key' matches only the comment word 'token' at plotScenario.m:225. Horizons come from the data (loadScenarios.m:11-14, :141, :165) and matlab/data/canonical/matlab_scenarios.csv contains exactly 2026, 2036, 2046, 2056.

### I-10 · `matlab/tests/test_horizons.m`
**Lane:** L04-matlab-tests-docs · **Category:** horizon-convention · **Confirmed:** not yet re-checked by the lead

**Claim.** Horizon convention is clean across the lane: all five legacy-year occurrences are explicitly and correctly labelled legacy, and the two archive scripts containing the literal year list are provably not referenced by anything live.

**Evidence.** Occurrences: test_horizons.m:3 (docstring 'The legacy scripts hard-coded years = ["Now","2035","2050"] (H7)'), test_horizons.m:56 (the guard literal itself), MIGRATION_NOTE.md:52 ('replaces the hard-coded ["Now","2035","2050"] loop (H7)'), RUN_ON_LICENSED_MATLAB.md:90,94,98 ('horizon label is 2026, not "Now"'; 'its horizons were Now/2035/2050'). legacy_archive/build_and_run_site_grid_behavior_model.m:64 and untitled.m:87 contain years = ["Now","2035","2050"]; repo-wide grep for those filenames returns only prose mentions in RUN_ON_LICENSED_MATLAB.md and MIGRATION_NOTE.md. MIGRATION_NOTE.md:17-18: 'Nothing in this archive is on the MATLAB path and nothing here is executed by the V3 pipeline.'

### I-11 · `matlab/README.md`
**Lane:** L04-matlab-tests-docs · **Category:** clean-check · **Confirmed:** not yet re-checked by the lead

**Claim.** The eGRID emissions factors 596.3 and 590.2 appear nowhere in matlab/ or .github/; the MATLAB layer models power and energy only.

**Evidence.** grep -rn '596\.3|590\.2|eGRID|lb CO2|CO2e' matlab/ .github/ returned zero hits.

### I-12 · `.github/workflows/matlab-manual.yml`
**Lane:** L04-matlab-tests-docs · **Category:** clean-check · **Confirmed:** not yet re-checked by the lead

**Claim.** No secrets, credentials, or absolute local paths in any assigned file; the only credential-adjacent token is a GitHub secret reference.

**Evidence.** grep -irn '/Users/|/home/|AKIA|arn:aws|[0-9]{12}|secret|token|password|api[_-]key' over matlab/tests, matlab/*.md, matlab/legacy_archive, .github/workflows/matlab-manual.yml returned only .github/workflows/matlab-manual.yml:3,4,28 - the last being 'MLM_LICENSE_TOKEN: ${{ secrets.MLM_LICENSE_TOKEN }}', a reference not a value.

### I-13 · `matlab/EXECUTION_STATUS.md`
**Lane:** L04-matlab-tests-docs · **Category:** static-verification · **Confirmed:** not yet re-checked by the lead

**Claim.** EXECUTION_STATUS.md's static-check claims independently reproduce: the block-balance table matches exactly for all 15 .m files, and the '11 distinct error IDs, zero missing' cross-check holds.

**Evidence.** Re-implementing the described algorithm gives test_capacityGuard 15, test_horizons 10, test_loadScenarios 13, test_managedCharging 19, test_profiles 11, test_regression 14, plus src counts 8/16/9/15/21/19/15/9/7 - identical to EXECUTION_STATUS.md:47-62. The 11 verifyError IDs (capacityGuard:notVerified/unknownBasis/missingBasis, loadScenarios:noMatch/fileNotFound/missingColumns/missingCapacityBasis/badArrivalWindow, managedCharging:capacityUndefined/sessionsRequired/badStrategy) all appear in error(...) calls in src/. No tabs, ASCII-only, functiontests(localfunctions) 6/6.

### I-14 · `matlab/tests/test_regression.m`
**Lane:** L04-matlab-tests-docs · **Category:** octave-compatibility · **Confirmed:** not yet re-checked by the lead

**Claim.** None of the 6 test files is Octave-runnable; the blockers are structural (unittest framework + table type + string class), not cosmetic. Porting the tests alone would not help because src/ carries the same dependencies.

**Evidence.** matlab.unittest harness functiontests(localfunctions) in all 6 files; 92 verify* calls; setupOnce/teardownOnce/TestData (65 refs); log(testCase,...) at test_regression.m:50. table type: readtable 5, writetable 5, height 9, removevars 1, sortrows 1, struct2table 1, table(...) ctor 12. detectImportOptions with 'TextType','string' and 'VariableNamingRule','preserve' 4 calls. T.Properties.VariableNames / UserData 1 each. Dynamic table field T.(col) 5 (test_horizons.m:71-72, test_regression.m:70,71,93). string-class semantics: string( 10, strlength 3, contains(...,'IgnoreCase') 1, "a" + "b" concat at test_loadScenarios.m:116 and test_regression.m:50. for site = ["FFX002","PWC001"] at test_regression.m:111 iterates once over a concatenated char row in Octave. src/ uses renamevars (loadScenarios.m:75), tiledlayout (plotScenario.m:62), exportgraphics (plotScenario.m:207).

### I-15 · `matlab/legacy_archive/untitled.m`
**Lane:** L04-matlab-tests-docs · **Category:** legacy-archive · **Confirmed:** not yet re-checked by the lead

**Claim.** Both legacy_archive scripts are pure history - unreferenced by anything live - and their identical makeProfiles bodies plus a shared header docstring confirm the H13 copy-and-diverge finding.

**Evidence.** grep -rl 'untitled\.m|build_and_run_site_grid_behavior_model' over the repo returns only matlab/RUN_ON_LICENSED_MATLAB.md, matlab/legacy_archive/MIGRATION_NOTE.md, and the two files themselves. untitled.m line 1 header reads '%% build_and_run_site_grid_behavior_model.m'. makeProfiles is numerically identical in both (starter lines 104-175 vs untitled 135-193): same shape constants exp(-0.5*((t-14)/4.5)^2)+0.25*exp(-0.5*((t-8)/1.7)^2)+0.15*exp(-0.5*((t-19)/2.0)^2), same fullEV_kW = ports*charger_power_kW, same capacity_kW = base_load_mean_kW + spare_capacity_kW, same clamp. dwell_hr is loaded (starter:101, untitled:132) and never used - hypothesis H1. untitled.m uses CRLF line endings; the starter uses LF. untitled.m:452-473 auto-generates unlabelled feasibility conclusions ('Result: this scenario stays within modeled site capacity...').

### I-16 · `data/contract/v1/contract_manifest.json`
**Lane:** L05-data-contract · **Category:** hash-chain-verified · **Confirmed:** not yet re-checked by the lead

**Claim.** All 11 manifest hashes independently verified with shasum -a 256: 11 of 11 PASS. The contract is byte-exact to its manifest. The construction is NOT a linked chain — it is 11 flat independent SHA-256 digests of raw file bytes, streamed in 65536-byte chunks, with zero normalisation (no line-ending canonicalisation, no key sorting, no whitespace handling). Tables are hashed in a fixed literal order after being written; inputs are hashed by the caller at their own locations.

**Evidence.** src/fcf_m2/contract.py:64-69 sha256_file() — hashlib.sha256 over open(path,'rb') in 65536-byte chunks, .hexdigest(). contract.py:282-283 fixed table order ['schema.json','scenario_table.csv','site_table.csv','source_provenance.csv','standards_register.csv','assumptions.json']; contract.py:291 hashes each after write (lines 275-280). contract.py:264,290 inputs passed in as inputs_hashed. Verified values: inputs 582e0b37…/064b6fdc…/9a07aa1e…/a0a3968b…/1b425597…; tables fb08b84a…/a4035888…/0ed5e4ec…/2d346861…/943f5b8f…/0ef70e9b… — every one matched.

### I-17 · `data/contract/v1/scenario_table.csv`
**Lane:** L05-data-contract · **Category:** claim-confirmed · **Confirmed:** yes — LEDGER FIND-NUM-01/02

**Claim.** Both program-critical claims CONFIRMED, one more strongly than stated. capacity_basis == placeholder at 12 of 12 sites (120 of 120 rows). data_confidence High at 0 of 12 sites — and Medium is also 0 of 12; all 12 sites are Low on all 120 rows.

**Evidence.** scenario_table.csv col 29 capacity_basis distinct set = {'placeholder'} (120 rows). Col 42 data_confidence distinct set = {'Low'}. Col 31 capacity_confidence distinct set = {'none'}. service_capacity_kw blank 120/120; spare_capacity_kw blank 120/120. capacity_source constant: 'legacy adapter future-ready placeholder; utility/facility confirmation pending (12/12 sites unconfirmed)'. Corroborated by assumptions.json:86 and by real_sites_v2.csv where elec_service_rating_amp and spare_capacity_kw are '0' at all 12 sites.

### I-18 · `data/contract/v1/site_table.csv`
**Lane:** L05-data-contract · **Category:** brief-premise-correction · **Confirmed:** not yet re-checked by the lead

**Claim.** site_table.csv contains NO capacity_basis and NO data_confidence column — it is a pure 9-column identity dimension. Those fields live at scenario grain in scenario_table.csv (cols 29 and 42). Any Phase-1 document that points at site_table.csv for capacity_basis is citing the wrong file.

**Evidence.** data/contract/v1/site_table.csv:1 header is exactly 'site_id,site_name_display,site_name_safe,jurisdiction,lat,lon,site_type,public_access,garage_enclosed' — 9 columns, 12 data rows (lines 2-13). data/contract/v1/README.md:10 describes it as 'identity dimension - one canonical spelling per site; join on site_id only'.

### I-19 · `data/inputs/legacy_matlab_site_meta.csv`
**Lane:** L05-data-contract · **Category:** lineage-verified · **Confirmed:** not yet re-checked by the lead

**Claim.** The base-load lineage is fully reproducible end-to-end from the tracked input and the assumptions file, which is strong evidence the generator ran as documented.

**Evidence.** legacy_matlab_site_meta.csv:2 FFX002 base_load_mean_kw=51.4 → scenario_table.csv FFX002_2026_baseline base_load_kw=51.4. Applying assumptions.json:29 base_load_growth_per_year=0.008: 51.4×1.008^10=55.66≈55.7 (2036 rows), ×1.008^20=60.27≈60.3 (2046 rows), ×1.008^30=65.27≈65.3 (2056 rows) — matches the contract exactly.

### I-20 · `data/contract/v1/assumptions.json`
**Lane:** L05-data-contract · **Category:** never-ran · **Confirmed:** not yet re-checked by the lead

**Claim.** No site anywhere in the 120-row contract reaches the proposed expansion-utilisation trigger; peak utilisation across the whole table is 0.2035 against a threshold of 0.4. Coherent with the 'proposed policy, not adopted' status, but it means the trigger policy is currently unexercisable by the model's own output.

**Evidence.** assumptions.json:74 utilization_threshold: 0.4. Max utilization observed in scenario_table.csv is 0.2035 (PWC002 2036_high, line 44). expansion_trigger_status is the constant string 'awaiting_observed_data (proposed policy, not adopted)' on all 120 rows. assumptions.json:24-26 confirms calibrated_at: null, n_observed_rows: 0, n_observed_sites: 0.

### I-21 · `data/contract/v1/assumptions.json`
**Lane:** L05-data-contract · **Category:** clean · **Confirmed:** not yet re-checked by the lead

**Claim.** data/ is clean of secrets, credentials, absolute local paths, AWS account IDs and PII; and clean of stale horizon tokens. The single 2035/2050 occurrence is a correctly-labelled legacy reference that should be preserved, not scrubbed.

**Evidence.** Scan of all data/ text files for /Users/, /home/, AKIA, aws_secret, api_key, password, secret, token, arn:aws and 12-digit IDs → zero matches. Standalone 2035/2050 token scan over all 120×48 scenario_table cells → zero hits (grep hits were decimals like utilization 0.2035). Only data/ hit is assumptions.json:11: '2036 re-anchors the legacy 2035 cases; 2046 inherits the legacy 2050 cases on the evidence that regional adoption is front-loaded; 2056 extends with saturation capped by pathway capacity. Status: synthetic_uncalibrated'.

### I-22 · `CHANGELOG.md`
**Lane:** L06-root-ci · **Category:** no-defect-confirmed · **Confirmed:** not yet re-checked by the lead

**Claim.** The eGRID correction held: 590.2 survives nowhere as a live factor. It appears in exactly four tracked files, all explicitly as a superseded/corrected value. 596.3 is used in all 120 contract rows and in src/fcf_m2/config.py.

**Evidence.** git grep -nI '590\.2' returns only CHANGELOG.md:24 ('correcting the 590.2 figure used earlier'), docs/methodology/current-facts-source-register.md:7 ('research register EX10 carried ~590.2; EPA's published CO2e total output rate for SRVC is 596.326 lb/MWh'), reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:22, reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:27. git grep -cI '596\.3' shows 120 hits in data/contract/v1/scenario_table.csv and 1 in src/fcf_m2/config.py.

### I-23 · `README.md`
**Lane:** L06-root-ci · **Category:** link-audit-clean · **Confirmed:** yes — LEDGER FIND-NUM-01/02, FIND-REPO-08

**Claim.** All 23 internal link/image targets referenced in README.md exist on disk; zero broken. CHANGELOG's four git refs (branch archive/pre-milestone2-v3-20260719, tags pre-milestone2-v3-20260719, v1-demo-scalability-ready, v1-review-ready) all exist. CONTRIBUTING's two links exist.

**Evidence.** Existence-checked each target with a shell loop: all 23 returned OK, including docs/assets/readme/project-overview.png, matlab/EXECUTION_STATUS.md, dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md, presentation/deck/Future_City_Fellowship_Milestone_2_Final.pdf. git branch -a / git tag -l confirm the refs.

### I-24 · `README.md`
**Lane:** L06-root-ci · **Category:** claim-verified · **Confirmed:** yes — LEDGER FIND-NUM-01/02, FIND-REPO-08

**Claim.** Several README/CHANGELOG headline claims DO check out and should not be touched in Phase 1: 80 tests (78 def test_ plus one 3-way parametrize = 80 collected), 9 dashboard visuals, 120 contract rows, 12 sites, 52 fellowship criteria, 25/48 legacy totals, docs step count 11, and all NPC/CO2e figures in the headline table.

**Evidence.** grep -c 'def test_' tests/ = 78 with tests/test_scoring_and_queueing.py:32 '@pytest.mark.parametrize("vals", [[0,1,2],[10,20,30],[0.1,0.5,0.9]])'; ls dashboard/static/0*.png | wc -l = 9; scenario_table.csv 120 rows / 12 distinct site_id; reports/milestone-2/Milestone_2_Gap_Closure_Status.md:1 'All 52 Criteria'; docs/WORKFLOW_STEPS.md:3 'Step count: **11**' matches 11 entries in src/fcf_m2/workflow.py STEPS; contract sums 1,560,499 / 2,294,469 / 3,014,200 NPC and 312,079 / 341,169 / 393,406 avoided.

### I-25 · `docs/operations/open-human-actions.md`
**Lane:** L07-docs-core · **Category:** stale-time-anchor · **Confirmed:** not yet re-checked by the lead

**Claim.** Two time-anchored statements have passed their stated windows relative to today (2026-07-27) and need re-dating or re-verification rather than silent carry-over.

**Evidence.** docs/operations/open-human-actions.md:8 row 1: 'hold the 30-min call or structured email exchange before July 21'. docs/methodology/current-facts-source-register.md:12 (IM-06): 'Virginia among states anticipated to release solicitations Q1 2026'. Same file line 7 (IM-01) also flags 'eGRID2024 preliminary data exists via API (≈−1.8% CO2e avg) but is not the official release'.

### I-26 · `docs/methodology/current-facts-source-register.md`
**Lane:** L07-docs-core · **Category:** clean · **Confirmed:** not yet re-checked by the lead

**Claim.** The eGRID correction survived correctly: 596.3 lb CO2e/MWh is the only live value anywhere, and 590.2 appears solely inside explicit superseded-value correction notes. No lane file contains a secret, AWS account ID, bucket name, distribution ID, token, or absolute local path.

**Evidence.** docs/methodology/current-facts-source-register.md:7 (IM-01): '**596.3 lb CO2e/MWh** ... **Correction:** research register EX10 carried ≈590.2; EPA's published CO2e total output rate for SRVC is 596.326 lb/MWh. All implementation artifacts use 596.3 with vintage.' Confirmed live at src/fcf_m2/config.py:91 'GRID_FACTOR_LB_PER_MWH = 596.3', data/contract/v1/contract_manifest.json grid_factor.value_lb_per_mwh = 596.3, data/contract/v1/assumptions.json:64. Repo-wide grep for '590.2' returns only 5 hits, all correction notes (CHANGELOG.md:24, this register line 7, reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md:22, .../Final_Report.md:27, docs/operations/v4-program/AWS_INVENTORY.md:140). Grep of all 22 lane files for /Users/, AKIA, aws_secret, arn:aws and 12-digit IDs: zero true positives (only SHA-256 substrings and PATCH_GUIDE.md:60's own instruction to grep for AKIA).

### I-27 · `docs/human-actions/team_alternatives_session/02_PROVISIONAL_MCDA.md`
**Lane:** L08-human-actions · **Category:** internal-contradiction · **Confirmed:** not yet re-checked by the lead

**Claim.** Presentation-length inconsistency: the MCDA evidence note says 12-minute presentation while the rest of the repository consistently says 13 minutes or less.

**Evidence.** docs/human-actions/team_alternatives_session/02_PROVISIONAL_MCDA.md:37 `more moving parts to explain and govern in a 12-minute presentation`. Versus docs/operations/open-human-actions.md:13 `Rehearse twice to ≤13 minutes`; reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md:124 `≤13-minute timing runbook` and :145 `Rehearse twice to ≤13 minutes`; reports/milestone-2/Milestone_2_Gap_Closure_Status.md:77 `10–15 minute structure ... Timed run ≤13:00`.

### I-28 · `docs/human-actions/team_alternatives_session/01_FACILITATION_GUIDE.md`
**Lane:** L08-human-actions · **Category:** missing-file · **Confirmed:** not yet re-checked by the lead

**Claim.** The facilitation guide lists 'the MCDA CSV' as required session material, but that file is not in the repository — the team cannot open it from the repo on session day.

**Evidence.** docs/human-actions/team_alternatives_session/01_FACILITATION_GUIDE.md:6 `**Materials:** this package printed or on screen; the MCDA CSV; the alternatives briefing`. The file is named at 02_PROVISIONAL_MCDA.md:5 as `SOLUTION_ALTERNATIVES_MCDA.csv (pre-V3 research archive, not tracked in this repository)`. Verified: `find . -iname "*MCDA*" -not -path "./.git/*"` returns only ./docs/human-actions/team_alternatives_session/02_PROVISIONAL_MCDA.md and ./presentation/assets/10_mcda_provisional.png.

### I-29 · `docs/human-actions/README.md`
**Lane:** L08-human-actions · **Category:** imprecise-restatement · **Confirmed:** not yet re-checked by the lead

**Claim.** The README conflates two contract columns: it reports capacity confidence as 'Low' when capacity_confidence is literally 'none' and it is data_confidence that equals 'Low'.

**Evidence.** docs/human-actions/README.md:30 `All 12 candidate sites remain electrically unconfirmed (capacity_basis = placeholder, confidence Low).` Contract truth from data/contract/v1/scenario_table.csv (120 rows): capacity_basis='placeholder' 120/120, capacity_confidence='none' 120/120, data_confidence='Low' 120/120. The sibling file docs/human-actions/utility_facility_data/04_DATA_FLOW_INTO_MODEL.md:9-14 states both correctly and separately.

### I-30 · `docs/human-actions/public_engagement/04_LANGUAGE_ACCESS_PLAN.md`
**Lane:** L08-human-actions · **Category:** unfilled-placeholder · **Confirmed:** not yet re-checked by the lead

**Claim.** A stated language-access commitment cannot be honoured because its numeric parameter was never chosen.

**Evidence.** docs/human-actions/public_engagement/04_LANGUAGE_ACCESS_PLAN.md:10 `**Live sessions:** interpretation offered on request in session announcements, with [X] business days' notice`.

### I-31 · `dashboard/tableau/patch_package/tbl_canonical_scenarios.csv`
**Lane:** L09-deliverables · **Category:** verified-true · **Confirmed:** not yet re-checked by the lead

**Claim.** The two largest patch-package CSVs are byte-identical copies of the contract, not subsets and not divergent; the cost and CO2e headline series trace exactly; and the Tableau blocker's honesty claims check out.

**Evidence.** md5 of dashboard/tableau/patch_package/tbl_canonical_scenarios.csv and data/contract/v1/scenario_table.csv are both 2beff3f46e8f86b43427d47b7e8efab6 (both 100,363 bytes, 120 data rows, 48 columns, diff empty); tbl_sites_dimension.csv and data/contract/v1/site_table.csv are both 92f19e6b6ad33e979fbf2869d856a771. Portfolio sums: STG base NPV 1,560,499/2,294,469/3,014,200 → published $1.56M/$2.29M/$3.01M; OVB 1,872,578/2,635,638/3,407,606 → $1.87M/$2.64M/$3.41M; avoided 312,079/341,169/393,406 → $0.31M/$0.34M/$0.39M (and avoided = OVB−STG exactly). Net CO2e sums: 43.4 / 82.4→112.7 / 130.1→195.1 / 173.4→260.2 t → published ≈43 / 82→113 / 130→195 / 173→260. No .twbx exists anywhere in the tree, and remotes/origin/archive/pre-milestone2-v3-20260719 does exist as claimed at BLOCKER:16.

### I-32 · `incoming/explorer/fcf-3d/fcf3d/build_sites.py`
**Lane:** L10-explorer-python · **Category:** drift-gate-verified · **Confirmed:** not yet re-checked by the lead

**Claim.** SUBSCORE_WEIGHTS and DRIVERS are NUMERICALLY IDENTICAL to repo/src/fcf_m2/scoring.py — zero differences across all 19 driver weights, all 6 inversions, and all 4 subscore weights. Structural differences (hours_open_n computed inline upstream, ev_share_local_n via bounded_signal, access_adjustment 1.00/0.35 deliberately not mirrored, .round(1)) are each handled correctly.

**Evidence.** build_sites.py:92-97 {demand 0.45, feasibility 0.30, safety 0.15, equity 0.10} == scoring.py:170-175. build_sites.py:136-174 driver weights 0.18/0.18/0.13/0.11/0.10/0.08/0.07/0.08/0.07 | 0.35/0.25/0.25/0.15 | 0.35/0.35/0.15/0.10/0.05 | 1.00 == scoring.py:140-168 identical coefficients. build_sites.py:322-323 `res["hours_open_n"] = res["hours_open"].clip(lower=0, upper=24) / 24.0` == scoring.py:146 `0.08 * df["hours_open"].clip(lower=0, upper=24) / 24`. build_sites.py:237 applies access_adj to demand only == scoring.py:151.

### I-33 · `incoming/explorer/fcf-3d/fcf3d/build_sites.py`
**Lane:** L10-explorer-python · **Category:** phase3-enabler · **Confirmed:** not yet re-checked by the lead

**Claim.** The mirrored weights reproduce milestone2_v3 scores just as accurately as legacy_v2 (weights are mode-invariant; only normalization differs), and the legacy future_ready_capacity used to size the 3D massing already equals the canonical max ports_pathway_capacity for all 12 sites. Neither the weight table nor the GLB geometry needs to change for Phase 3.

**Evidence.** Independent pure-stdlib recomputation, worst |rebuilt-actual|: fixture_legacy_v2_site_results.csv 0.100; site_results_legacy_v2.csv 0.100; site_results_milestone2_v3.csv 0.100 (FFX001 48.8 vs 48.7). scoring.py:10-12 "Subscore weights, the EV-share benchmark, the demand formula, and the port chooser are identical in both modes; only normalization differs". future_ready_capacity vs max ports_pathway_capacity: FFX001 4/4, FFX002 8/8, FFX003 4/4, FFX004 8/8, PWC001 3/3, PWC002 3/3, PWC003 2/2, PWC004 4/4, PWC005 2/2, PWC006 4/4, PWC007 4/4, PWC008 2/2.

### I-34 · `incoming/explorer/fcf-3d/fcf3d/geometry.py`
**Lane:** L10-explorer-python · **Category:** constraint-verified · **Confirmed:** not yet re-checked by the lead

**Claim.** CLAUDE.md non-negotiable #3 holds: geometry.py has zero third-party imports. Complete import list is three stdlib statements.

**Evidence.** geometry.py lines 25-28 in full: `from __future__ import annotations` / (blank) / `import math` / `from dataclasses import dataclass`. No other import statement exists in the file's 268 lines.

### I-35 · `incoming/explorer/fcf-3d/fcf3d/glb.py`
**Lane:** L10-explorer-python · **Category:** no-drift · **Confirmed:** not yet re-checked by the lead

**Claim.** The shipped generated artifacts have NOT drifted from their generator: all 12 web/models/*.glb carry extras.ports_now / extras.ports_pathway exactly matching asset.ports / asset.pathway_ports in web/data/sites.geojson, and all begin with the glTF magic.

**Evidence.** e.g. FFX002 geojson ports=2 pathway=8 vs GLB extras ports_now=2 ports_pathway=8 ada=1 parts=32; all 12 match. web/data/manifest.json: schema_version fcf3d/1.0.0, generated_at 2026-07-26T04:27:14.192759+00:00, site_count 12, score_min 29.6, score_max 58.8, warnings [].

### I-36 · `incoming/explorer/fcf-3d/CLAUDE.md`
**Lane:** L10-explorer-python · **Category:** clean-scan · **Confirmed:** not yet re-checked by the lead

**Claim.** No secrets, tokens, AWS account IDs, absolute /Users paths, or the retired 590.2 eGRID factor anywhere in the explorer tree. The 596.3 lb CO2e/MWh factor never appears either — the explorer copies net_co2e_kg out of the contract but never surfaces the grid factor.

**Evidence.** grep for 590 across the tree: no matches. grep for 596.3: no matches. grep for /Users/ in fcf3d, tests, blender, Makefile, README.md, CLAUDE.md: no matches. grep -inE 'api[_-]?key|secret|AKIA|aws_|bearer |eyJ...' returns only CLAUDE.md:65 (the policy statement), web/app.js:145 (Cesium.Ion.defaultAccessToken = token), and web/index.html:102 (a placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6..." JWT-header prefix, not a credential). repo contract grid_factor_value = 596.3 on all 120 rows, vintage eGRID2023r2 accessed 2026-07-19.

### I-37 · `fcf-3d/web/data/sites.geojson`
**Lane:** L11-explorer-web · **Category:** clean · **Confirmed:** not yet re-checked by the lead

**Claim.** No eGRID emissions factor appears anywhere in the explorer tree — neither the current 596.3 nor the corrected-away 590.2.

**Evidence.** grep -rn -E "596\.3|590\.2|eGRID|egrid|emission" across the entire fcf-3d tree returns zero hits. scenarios[].net_co2e_kg carries only precomputed results (e.g. FFX002 2026 baseline net_co2e_kg = 4180.5).

### I-38 · `fcf-3d/web/index.html`
**Lane:** L11-explorer-web · **Category:** clean · **Confirmed:** not yet re-checked by the lead

**Claim.** No secrets, tokens, AWS identifiers, or absolute local paths in any assigned file; the only token-shaped string is a truncated JWT header used as an input placeholder.

**Evidence.** grep for `/Users/|AKIA|arn:aws|aws_|secret|api[_-]?key` across index.html, app.js, style.css, manifest.json yields no credential. index.html:102 `placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6..."` decodes to the JWT header fragment {"alg":"HS256","typ": with no payload or signature. The real token is read at runtime from localStorage key 'fcf3d.ionToken' (app.js:879) and applied at app.js:145.

### I-39 · `fcf-3d/web/app.js`
**Lane:** L11-explorer-web · **Category:** clean · **Confirmed:** not yet re-checked by the lead

**Claim.** Zero field-name drift between app.js and the ETL's generated output; drift runs the other way, with 12 generated keys never rendered.

**Evidence.** Programmatic diff of every p.<field>/properties.<field> read in app.js against the union of property keys across all 12 features: all 44 top-level reads and all nested reads (subscores, right_sizing, asset, electrical, coordinate_provenance, avoided_overbuild) resolve. Never rendered: driver_attribution (19 rows/site), garage_enclosed, planning_recommendation, ports_2035, queueing (6 sub-keys), state, plus metadata generated_at, score_min, score_max, sources, disclaimer, warnings.

### I-40 · `fcf-3d/web/data/sites.json`
**Lane:** L11-explorer-web · **Category:** clean · **Confirmed:** not yet re-checked by the lead

**Claim.** node --check passes on app.js and sites.inline.js; the three data files are mutually consistent with zero mismatches.

**Evidence.** `node --check web/app.js` -> exit 0; `node --check web/data/sites.inline.js` -> exit 0. sites.json vs sites.geojson: same 12 ids in the same order, lon/lat equal within 1e-12, all other properties exactly equal, total mismatches 0. sites.inline.js payload deep-equals sites.geojson (`inline == geojson: True`). All 12 GLBs are valid glTF 2.0 with declared length == file size and generator 'fcf3d.glb (Future City Fellowship / ChargeReady NOVA)'.

### I-41 · `presentation/deck/Future_City_Fellowship_Milestone_2_Final.pptx`
**Lane:** L12-binaries · **Category:** metadata-hygiene · **Confirmed:** not yet re-checked by the lead

**Claim.** Office/PDF metadata on client-facing deliverables is uniformly the library default stub and is factually wrong in places.

**Evidence.** PPTX docProps/core.xml: `<dc:title/>` empty, `<dc:creator/>` empty, `<cp:lastModifiedBy>Steve Canny</cp:lastModifiedBy>`, `<dcterms:created>2013-01-27T09:14:16Z</dcterms:created>`; docProps/app.xml claims `<PresentationFormat>On-screen Show (4:3)</PresentationFormat>` and `<Slides>0</Slides>` while the deck is 13.333x7.5in 16:9 with 17 slides. All four DOCX: `<dc:creator>python-docx</dc:creator>`, `<dcterms:created>2013-12-23T23:15:00Z</dcterms:created>`, `<Pages>1</Pages>`, `<Words>0</Words>`. Three of four PDFs have no /Title.

### I-42 · `dashboard/static/STATIC_DASHBOARD.pdf`
**Lane:** L12-binaries · **Category:** accessibility · **Confirmed:** not yet re-checked by the lead

**Claim.** dashboard/static/STATIC_DASHBOARD.pdf — the artifact the repo calls the offline fail-safe — has zero text layer and is therefore unsearchable and not screen-reader accessible; its charts are lossily JPEG-recompressed from RGBA PNGs.

**Evidence.** pypdf extract_text() over all 9 pages returns 0 characters. Each page holds exactly one XObject named image.jpg in mode RGB at full page pixel size (p1 2750x1131 ... p9 2185x1309). Generator scripts/build_static_dashboard.py:219-221 `pngs = sorted(OUT.glob("0*.png")); imgs = [Image.open(p).convert("RGB") ...]; imgs[0].save(OUT / "STATIC_DASHBOARD.pdf", save_all=True, append_images=imgs[1:])`.

### I-43 · `incoming/explorer/fcf-3d/web/models/FFX002.glb`
**Lane:** L12-binaries · **Category:** data-integrity · **Confirmed:** not yet re-checked by the lead

**Claim.** POSITIVE: the 12 GLBs independently confirm the two headline portfolio numbers (25 starter ports, 48-port pathway) and are 1:1 consistent with sites.geojson.

**Evidence.** Decoded POSITION accessor counts (24 verts/box) per material across all 12 GLBs. ports_now per site: FFX001 2, FFX002 2, FFX003 2, FFX004 3, PWC001 2, PWC002 2, PWC003 2, PWC004 2, PWC005 2, PWC006 2, PWC007 2, PWC008 2 = 25. pathway: 4,8,4,8,3,3,2,4,2,4,4,2 = 48. ADA stall counts match geometry.py:113-119 `max(1, math.ceil(total_stalls / 25))` and stripe counts match one-per-stall (geometry.py:167-176) on all 12. Symmetric difference between geojson site_ids and model filenames is empty. manifest.json score_max 58.8 matches the deck's 'FFX002 leads at 58.8'.

### I-44 · `presentation/deck/Future_City_Fellowship_Milestone_2_Final.pptx`
**Lane:** L12-binaries · **Category:** data-integrity · **Confirmed:** not yet re-checked by the lead

**Claim.** POSITIVE: the deck has not drifted from the repo's PNG assets — all 10 PPTX-embedded images are SHA-256 identical to on-disk files, and the exported PDF matches the PPTX slide-for-slide.

**Evidence.** ppt/media/image1.png..image10.png hash-match presentation/assets/10_mcda_provisional.png (slide6), dashboard/static/01_readiness_ranking.png (slide8), 09_site_map_offline.png + 02_starter_vs_pathway.png (slide9), 03_ports_three_horizons.png + 04_lifecycle_cost.png (slide11), docs/assets/architecture/integration_architecture.png (slide13), 05_net_co2e.png + 06_avoided_evse.png (slide14), 08_limitations.png (slide15). PDF 17 pages vs PPTX 17 slides, first text line identical on all 17. dashboard/static/07_peak_wait.png is the only dashboard visual unused in the deck.

### I-45 · `incoming/explorer/fcf-3d/.gitignore`
**Lane:** L12-binaries · **Category:** deployment-risk · **Confirmed:** not yet re-checked by the lead

**Claim.** The 12 GLBs are gitignored build outputs, not tracked assets — any Phase 3 integration that assumes they travel with the repo will find an empty models directory.

**Evidence.** incoming/explorer/fcf-3d/.gitignore:8 `web/models/*.glb`. Makefile:119 `rm -rf web/data/sites.* web/data/manifest.json web/models/*.glb`. Rebuild path is `python -m fcf3d.build_models --sites web/data/sites.geojson --out web/models` (fcf3d/build_models.py docstring).
