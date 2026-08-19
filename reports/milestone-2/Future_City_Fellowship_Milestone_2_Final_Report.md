# Future City Fellowship - Milestone 2 Final Report

## Safe, Code-Responsive Electrification for Fairfax City and Prince William County

**Team:** Anna · Laylas · Andy · Adama · Paula (George Mason University Future City Fellowship)
**Client contact:** [client contact], Green Buildings Manager, Prince William County Office of Sustainability
**Prepared:** 2026-07-19 (for the Milestone 2 presentation, Tuesday 2026-07-21)
**Supersedes:** `Future_City_Fellowship_Milestone_2_Phase_Report.md` (July 2026) - that report remains the authoritative record of the Phase 2 build; this report integrates the gap-closure implementation completed 2026-07-19.

> **Standing discipline.** This project is a planning-support prototype. Nothing in this report is an engineering design, permit or code determination, utility capacity confirmation, official forecast, budget, procurement package, or construction authorization. **0 of 12 candidate sites have High data confidence; electrical capacity is a placeholder at all 12 sites.** No client endorsement, AHJ acceptance, utility confirmation, or funding award exists or is implied.

---

## 1. Executive summary

Phase 1 identified a local-readiness problem: electrification is expanding faster than code interpretation, responder training, siting practice, and emergency-access planning in two contrasting Dominion-served jurisdictions - built-out Fairfax City (~25k) and county-scale Prince William County (~500k, dominated by data-center load growth). Phase 2 answered it with a reproducible decision-support system; the July 2026 compliance audit then identified exactly what Milestone 2 still required. This report documents the **implementation run of 2026-07-19** that closed every gap that code, modeling, analysis, documentation, or artifact production can close - and prepared complete, ready-to-execute packages for every gap that only the client, team, AHJ, utility, facilities staff, or fellowship staff can close.

**The leading solution (research-ranked, pending team adoption):** distributed staged pilots at the strongest candidate sites, with expandable civil/electrical pathways, monitoring of actual use, and activation of additional chargers only when predefined, equity-aware triggers are sustained. It scored 85/100 against six genuine alternatives, wins on both evidence streams (the client's own overbuild/trenching cost history and the model's low simulated utilization), and grows naturally into the hybrid portfolio (81/100) as ports multiply. The county's ~35-station fleet hub remains a coordinated parallel track, not a competitor.

**What is new since the Phase 2 report (all verified this run):**

- an **independently reproduced baseline** - the full 25-step V2 workflow re-run with every check passing (FFX002 top at 58.8; 25 starter / 48 pathway ports; 38 REVIEW + 12 INFO findings; 15 Tableau exports; 35-file package);
- a **V3 model** (`fcf_m2` 3.0.0) with two permanent modes: `legacy_v2` (bit-exact baseline reproduction, golden-tested) and `milestone2_v3` (canonical 2026 + 2036/2046/2056 horizons, fixed-anchor cohort-independent scoring with a migration report, typed data confidence, peak-window and discrete-event wait modeling, lifecycle economics, emissions, proposed equity-aware expansion triggers); 80 tests, 92% coverage;
- one **canonical cross-model data contract** (hybrid CSV + JSON, v1.0.0, 120 scenario rows, schema-validated and hash-chained) now consumed by the Excel workbook, the MATLAB adapter, the Tableau patch package, the static dashboard, and this report - ending the "three truths" problem;
- **two aspects modeled at 2036/2046/2056** (§5);
- a **lifecycle-economics layer**: staged vs broad-buildout vs defer, net present cost with avoided-cost headline (ROI deliberately rejected - no honest revenue line exists);
- a **net-CO2e layer** with a corrected, sourced grid factor (EPA eGRID2023 Rev 2, SRVC, **596.3 lb CO2e/MWh**, accessed 2026-07-19 - the research package's 590.2 figure was superseded by direct EPA verification) plus the avoided-EVSE resource-management metric;
- a **standards package** (UL 2594 + UL 3600 highlighted; UL 2231/NEC 625-as-adopted/VA USBC-SFPC/Access Board supporting; conditional standards explicitly out of scope) and a **proposed standard concept** with seven test modules and TBV-disciplined parameters;
- an updated **Excel workbook** (pie chart repaired, horizons to 2056, contract import, cost/CO2e sheets, live reconciliation checks - all PASS);
- a rebuilt **MATLAB/Simulink repository** implementing all twelve improvement items as source, tests, and documentation - with execution honestly **blocked** (no licensed MATLAB available) and exact commands prepared for a licensed runner;
- a complete **presentation package**, **static offline dashboard**, **website/assistant patch package**, and **six human-action packages** (client meeting #2, team session, AHJ, utility/facility data, public engagement, fellowship clarification).

**Honest status of the two aspects at a glance (screening values, base escalation, contract v1.0.0):**

| Horizon | Active ports (base→high) | Staged NPC | Broad NPC | Staged avoids | Net CO2e avoided (base→high) |
|---|---|---|---|---|---|
| 2026 | 25 | - | - | - | ≈43 t/yr |
| 2036 | 35 → 44 | $1.56M | $1.87M | **$0.31M** | ≈82 → 113 t/yr |
| 2046 | 44 → 48 | $2.29M | $2.64M | **$0.34M** | ≈130 → 195 t/yr |
| 2056 | 44 → 48 (pathway ceiling 48) | $3.01M | $3.41M | **$0.39M** | ≈173 → 260 t/yr |

---

## 2. Verified baseline (what this report stands on)

Every headline number was independently re-derived on 2026-07-19 by re-running the workflows on disposable copies:

| Check | Result |
|---|---|
| Python V1 (`run_all.py` + checker) | PASSED |
| Python V2 - 25 steps, output checker, baseline comparison, Tableau exports, package | ALL PASS: 12 sites; FFX002 City of Fairfax Regional Library #1 at 58.8 (Medium); FFX004 54.4; PWC006 52.1; 25 starter / 35 / 44 / 44 / 54 ports across legacy cases; 48 future-ready; 38 REVIEW + 12 INFO; 15/15 exports; 35/35 package files |
| High-confidence sites | **0 of 12** (preserved as the project's credibility signature) |
| Offline GIS | Cold-start offline fails (documented V2 defect); V3 fix: cached VA TIGER boundaries in-repo - map generation verified with networking disabled |
| MATLAB | Static inspection only. **No simulation executed - none claimed.** |

The V3 `legacy_v2` mode reproduces the accepted baseline **bit-for-bit** (golden tests assert equality with the frozen V2 outputs on every score, rank, port count, and strategy string).

## 3. Client evidence and the honest Client Meeting #2 status

The [client contact] interview supplies the project's strongest operational evidence: McCoart's 10-port install cost escalated through trenching/undergrounding distance; the Neabsco garage's 70 ports were heavily underused and 17 stations were taken offline at a ~$1,000/station/yr operating frame (~$20k/yr avoided); Virginia's "sufficient EV charging" requirement is ambiguous (LEED ~5% used as guidance); the Animal Services Center satisfied the EV-ready requirement with conduit only; ADA EV-space requirements forced a year of fleet-hub redesign (Dominion reports identical friction). [fire-service interviewee] (PWC Fire & Rescue/HazMat) established the proactive window: **no local EV fires yet**, but recognition/education and charger siting that can block responder access are live concerns.

**Client Meeting #2 has not yet occurred as defined by the program.** The [client contact] interview was an information-gathering session; the program's CM2 requires presenting the narrowed focus, brainstorming solutions with the client, and capturing feedback on the team's actual alternatives. [client contact] explicitly offered a follow-up ("either one, follow up meeting, or emails is fine"). The complete follow-up package - ready-to-send email draft, two-page pre-read, 30-minute agenda, alternatives briefing, feedback form, decision log, follow-up email, and acceptance checklist - is prepared in `docs/human-actions/client_meeting_2/`. **Nothing in this report converts that preparation into a held meeting or a client endorsement.**

## 4. Alternatives and convergence (prepared for team adoption)

Seven genuinely distinct alternatives were developed and scored in a provisional MCDA (weights 25/20/20/15/10/10 across safety-code readiness, demand fit, lifecycle cost/funding, expandability/resilience, equity, data confidence):

| Alternative | Score |
|---|---|
| **B - Distributed staged pilots + expandable pathways** | **85** |
| F - Hybrid portfolio (B + EV-ready seeding + managed charging) | 81 |
| E - Managed-charging-first | 72 |
| C - EV-ready-first (pathways only) | 71 |
| D - Centralized fleet hub + selective public (county's real parallel track) | 58 |
| A - Broad immediate buildout (the Neabsco pattern) | 41 |
| G - Defer / do nothing (comparator) | 37 |

Sensitivity: the ranking survives ±5pp on every criterion; the one honest crossover is equity-dominant weighting (~2× default), where F overtakes B - neutralized by presenting staged pilots as the hybrid's first stage.

> **CORRECTION, 2026-07-28.** Two figures in this section were superseded on 2026-07-27 and this
> dated report was never amended. It is kept as written, because it records what was presented;
> the corrections are stated here rather than substituted silently.
>
> * **Alternative G scores 40.0, not 37.** Recomputed from the same matrix and weights;
>   G's rank is unchanged.
> * **The equity crossover is at ~2.5× the default weight, not ~2×.** At 2× default equity, F
>   does **not** overtake B.
>
> Both are pinned by `tests/test_mcda_arithmetic.py`, which parses the canonical matrix and
> fails if either figure moves. The canonical source is
> `docs/human-actions/team_alternatives_session/02_PROVISIONAL_MCDA.md`. **These scores are researched provisional values; the team session package (`docs/human-actions/team_alternatives_session/`) exists precisely so the team can amend and adopt them honestly. No team adoption is claimed.**

## 5. Two aspects at 2036 / 2046 / 2056

The official requirement - two aspects modeled at 10/20/30-year timelines - is satisfied with the canonical convention 2036/2046/2056 from a stated 2026 baseline (exact calendar years are a convention, not a mandate; the fellowship-clarification draft asks for confirmation).

**Aspect 1 - site/portfolio charging demand and port/pathway capacity.** The Python model of record, extended by growth cases (base/high/stress at each horizon; multipliers 1.9/2.6 → 3.0/4.5 → 4.0/6.0, stress ×1.15 - provisional conventions pending calibration) with saturation capped by the 48-port pathway and monotonic activation. Peak-window Erlang and a seeded 400-day discrete-event simulation add P10/P50/P90 wait bands; at current demand even peak-window P90 waits sit under the 10-minute target at every top site.

**Aspect 2 - lifecycle cost and avoided overbuild, carrying the environmental outcome.** Full cash-flow model 2026–2056 per site (hardware, civil with contingency, pathway premium, trigger-year expansions, network fees on active ports only, maintenance, electricity, ~year-10 electronics replacement, decommissioning of never-needed ports in the overbuild case; low/base/high escalation; 3% real discount plus undiscounted view). Result: **the staged plan costs less than broad buildout at every horizon under every escalation case**, with the avoided-cost headline growing from $0.31M (2036) to $0.39M (2056) on the base case. The attached environmental outcome: net avoided CO2e (displaced tailpipe minus charging grid emissions, eGRID2023r2 SRVC 596.3 lb CO2e/MWh with vintage stated everywhere) reaching ≈173–260 t/yr by 2056, paired with the avoided-EVSE metric (13–23 pathway ports deliberately not energized on the base path - the direct answer to the client's decommissioning experience).

Success evidence per horizon is defined (2036: sustained trigger-level utilization at ≥2 pilots, documented first expansion decision; 2046: portfolio utilization within band, cost/port vs projection; 2056: adopted-share demand served without exceeding pathway capacity).

## 6. Canonical contract and cross-model integration

`data/contract/v1/` (schema.json, scenario_table.csv - 120 rows, site_table.csv, source_provenance.csv, standards_register.csv, assumptions.json, contract_manifest.json) is the single source of truth. Python generates it; Excel, MATLAB, Tableau exports, the static dashboard, and the presentation consume it. Validation implements the ten reconciliation tests (identity joins on `site_id` only, completeness, monotonicity, legacy totals 25/48, unit ranges, year-set equality, placeholder propagation, energy accounting, factor-vintage pinning, manifest hash chain) - all passing; deliberately corrupted contracts fail every corresponding test. The single most important field is **`capacity_basis`**: it makes placeholder-vs-verified machine-readable, so no downstream artifact can silently present placeholder capacity as real. The MATLAB adapter is now generated (PY-14), eliminating the hand-built CSV and its 2050-base/high port mismatch.

## 7. Model integrity upgrades (V3)

- **Cohort-independent scoring (PY-02):** versioned fixed anchors; the same site scores identically when unrelated sites are added or removed (tested). Ranking differences vs the cohort-relative baseline are published in a migration report; the port/pathway structure remains anchored to the accepted legacy baseline pending deliberate re-baselining.
- **Typed data confidence (PY-05):** field-level provenance with controlled source classes; note wording can no longer move confidence scores (tested). Overall confidence is traceable to a per-field breakdown. Result unchanged in substance: 0 High-confidence sites.
- **Demand honesty (PY-03):** `demand_model_status = synthetic_uncalibrated` is embedded in the contract; the calibration routine imports observed sessions, fits with a holdout split, and **refuses** the calibrated label on insufficient data or poor fit (tested).
- **Equity-aware expansion triggers (PY-20):** proposed policy - sustained utilization ≥40% or repeated 10-minute waits, ≥97% uptime before data are trusted, ≥6 months observation, pathway headroom, budget gate requiring human approval, and an **equity override** lowering the utilization gate to 25% in high-equity-need areas so low-adoption communities are not permanently starved. Every evaluation emits a full rule trace; current status everywhere: `awaiting_observed_data`. **The policy is proposed configuration, not adopted municipal policy.**

## 8. Standards and the proposed standard

**Highlighted:** UL 2594 (EVSE safety, 3rd ed. 2022) and UL 3600 (circular-economy measurement, 2023) - the only pair satisfying both the safety and sustainability rubric rows. **Essential supporting:** UL 2231-1/-2; NEC Article 625 **as adopted in Virginia (2020 NEC via the 2021 USBC, effective 2024-01-18** - the 2023 NEC is not Virginia law); Virginia USBC/SFPC (2024 code cycle underway, ~2027); Access Board EVSE guidance (**still at NPRM as of 2026-07-19**; VA USBC ADA provisions govern today); OCPP/ISO 15118 as supporting protocols (not ULSE standards). **Conditional and out of scope:** UL 2202 (no DCFC), UL 9540/9540A + NFPA 855 (no storage; `battery_storage_flag=0` at all sites - and therefore **no resilience claim is made anywhere**).

The proposed standard - *Municipal EV Charging Site Readiness and Emergency Access Standard*, explicitly a **fellowship design concept, not an official UL/ULSE proposal** - defines seven test modules (emergency access/disconnect; expandability/right-sizing documentation; accessibility cross-references; monitoring/triggers; managed-charging fail-safe; commissioning evidence; materials/end-of-life) with three conformance levels. Sourced parameters cite adopted codes by edition; every unsourced parameter is marked **TBV by ULSE/AHJ/manufacturer/adopted code**. Full texts: `docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md` and `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md` (DOCX renderings in `reports/milestone-2/`).

## 9. Technical integration, risk, environment, funding, stakeholders

- **Integration:** the full chain (utility → transformer/feeder → service entrance/panel → load management → EVSE → vehicles, with OCPP/ISO 15118 communications, metering, emergency disconnect and responder access, monitoring feeding the governance/trigger layer, and the county fleet hub as coordination-only) is documented with an 8-interface register and responsibility register (`docs/architecture/TECHNICAL_INTEGRATION_ARCHITECTURE.md`, diagram in `docs/assets/architecture/`).
- **Risk:** an 18-risk register with likelihood×consequence, owner, trigger, mitigation, evidence, residual risk, response time, and deciding human authority (`reports/milestone-2/RISK_REGISTER.md/.csv`). Top mitigations: fail-safe curtailment on comms loss; verified/labeled/illuminated disconnect at commissioning; service-capacity confirmation before design freeze; dual-path utilization logging; ADA-first layout.
- **Environment/resilience:** heat, flood, stormwater, outage, and severe-weather treatment; sourced grid factor with annual refresh; materials/take-back/UL 3600 procurement line; trenching minimization doubling as embodied-impact minimization; explicit no-resilience-claim statement (`reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md`).
- **Funding/budget:** FY2027 context (Fairfax City ≈$207.5M GF adopted 2026-05-05; PWC ≈$1.955B GF revenues adopted 2026-04-21 - a 2-port pilot is CIP-scale-trivial but must ride a process); Dominion Level 2 Charging Program (50% make-ready, 100% for qualifying disadvantaged communities) as the recommended first path; NEVI presented only with its volatility history ($885M FY26; VA solicitations anticipated Q1 2026); CFI watchlist. **No funding is implied as awarded** (`reports/milestone-2/ECONOMIC_AND_FUNDING_BRIEF.md`).
- **Stakeholders/regulatory:** the nine-lane jurisdictional map naming the deciding offices per Report 10's verified table (`reports/milestone-2/REGULATORY_STAKEHOLDER_MAP.md`); public-engagement instruments (survey, accessibility review, listening sessions, language access, VCDPA-aware privacy, feedback-to-decision traceability) in `docs/human-actions/public_engagement/`.

## 10. Artifact status

| Artifact | Status |
|---|---|
| Excel workbook | `excel/Electric_Data_Milestone_2_Updated.xlsx`: pie chart repaired and connected; proxies labeled; extended to 2056 (labeled extrapolation); canonical import; lifecycle + CO2e sheets; low/base/high; assumptions register; **six live reconciliation checks all PASS**; renders without repair warnings. Original preserved. |
| MATLAB/Simulink | `matlab/`: all 12 items implemented as source/tests/docs; static checks pass; **execution BLOCKED (no license)**; exact licensed-runner commands provided. Legacy repo preserved; committed legacy visuals usable only with the placeholder-capacity caption. |
| Tableau | Verified `.twbx` **blocked** (no Tableau Desktop; Tableau Public rejected because it publishes). Full blocker note, contract-derived patch CSVs, and an exact build recipe in `dashboard/tableau/`; the presentation-facing deliverable is the static dashboard (the team's own chosen demo strategy). |
| Static visuals | 9 contract-derived, footer-labeled, offline-openable visuals + combined PDF (`dashboard/static/`); automated footer QA passes. |
| Website/assistant | Offline patch package with file-by-file guide, privacy notice, authority disclaimers, source-vintage footer, assistant boundaries, deployment/rollback runbook (`docs/operations/website-patch-package/`). **Nothing deployed.** |
| Presentation | Final deck, PDF, speaker notes, ≤13-minute timing runbook, Q&A backup, self-contained static visuals (`presentation/`), rendered and inspected slide-by-slide. |

## 11. Limitations (unchanged in force)

1. 0 of 12 sites have High data confidence; every electrical field is unconfirmed.
2. Capacity is a placeholder at 12/12 sites; no feasibility claim is permitted on it.
3. Demand is synthetic/uncalibrated; growth multipliers are provisional conventions.
4. All costs are screening-class; the $429,500-class screens are not budgets.
5. Emissions rest on labeled benchmark assumptions and an annually-refreshed factor.
6. Client Meeting #2 is prepared, not held; no client endorsement exists.
7. Team adoption of alternatives/MCDA/conventions is prepared, not performed.
8. MATLAB execution and Tableau workbook verification are blocked by tooling, stated plainly.
9. No AHJ, utility, facility, or fellowship confirmation of anything has occurred.

## 12. Next human actions (highest priority first)

1. **Send the CM2 follow-up request to [client contact]** and hold the 30-minute touchpoint or email exchange before July 21 (`docs/human-actions/client_meeting_2/01_EMAIL_DRAFT_TO_CLIENT.md`).
2. **Hold the team alternatives session** (60–90 min) and adopt/amend the MCDA honestly; assign Paula's presentation role (`docs/human-actions/team_alternatives_session/`).
3. **Send the fellowship clarification email** (CM2 classification; year convention; standards count) (`docs/human-actions/fellowship_confirmation/`).
4. **Send the utility/facility data requests** for FFX002/FFX004/PWC006 (`docs/human-actions/utility_facility_data/`) - the single highest-value unlock (upgrades `capacity_basis` from placeholder).
5. **Schedule Fire Marshal/AHJ conversations** in both jurisdictions with the prepared question sets (`docs/human-actions/ahj_fire_marshal/`).
6. Rehearse twice to ≤13 minutes (Monday evening + Tuesday morning per the timing runbook).
7. Post-M2: run the MATLAB batch on a licensed installation; build/verify the Tableau workbook per the patch recipe; deploy the website patch per the runbook; field the engagement instruments; begin Dominion program application alignment.

## 13. Peer-team question

> **How should a city set an equitable expansion trigger for public EV charging when early utilization data are sparse - so it avoids both overbuilding and under-serving communities whose current EV adoption may be lower?**

Backups: (1) what evidence should convert EV-ready conduit into active ports, and who owns that decision; (2) how to keep a 30-year model honest when 10-year goals are already off-track (phrase with care).

---

*Implementation integrity: no original source file, repository, or external system was modified; nothing was emailed, pushed, deployed, or published; no client, team, AHJ, utility, facility, fellowship, or MATLAB-execution evidence was fabricated. Full manifests: `00_IMPLEMENTATION_MANIFEST.md`, `verification/`.*
