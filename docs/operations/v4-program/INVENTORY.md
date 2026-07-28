# INVENTORY.md — every file in all three trees

**Phase 0.3 deliverable.** Every text file below was **read end to end**, not skimmed; every binary was
opened and checked for corruption, for being referenced by something, and for matching what its name and
documentation claim. Produced by twelve non-overlapping reader lanes plus an independent coverage verifier,
with the load-bearing MATLAB and 3D-explorer sources additionally read line by line by the program lead.

- **229 files** — 198 tracked in `repo/`, 31 in `incoming/explorer/fcf-3d/`
- The snapshot tree (`incoming/snapshot/Future-City-Fellowship--main-2/`) is **byte-identical** to
  `origin/main` across all 198 files and so is not enumerated separately — see `RECONCILIATION.md`.
- Full per-file detail lives in [`inventory/`](inventory/), one file per lane. This page is the index.

## How to read this

| | |
|---|---|
| **Kind: authored** | written by a person; edit it directly |
| **Kind: generated** | produced by the named generator. **Never hand-edit.** Change the generator and regenerate. |
| **Kind: binary** | not read byte-level; verified openable, non-corrupt, referenced, and consistent with its documentation |
| **Lane** | which detail file in [`inventory/`](inventory/) documents it |

## The lanes

| Lane | Scope | Detail |
|---|---|---|
| L01 | The Python model — `src/fcf_m2/` (the single scorer) | [`inventory/L01-model-core.md`](inventory/L01-model-core.md) |
| L02 | Tests and build scripts — `tests/`, `scripts/` | [`inventory/L02-tests-scripts.md`](inventory/L02-tests-scripts.md) |
| L03 | MATLAB source — `matlab/src/` (9 files) incl. Simulink topology and Octave inventory | [`inventory/L03-matlab-src.md`](inventory/L03-matlab-src.md) |
| L04 | MATLAB tests, docs, legacy archive, canonical CSV, exposure classification | [`inventory/L04-matlab-tests-docs.md`](inventory/L04-matlab-tests-docs.md) |
| L05 | Data and the canonical contract — `data/` incl. the RT-10 hash chain | [`inventory/L05-data-contract.md`](inventory/L05-data-contract.md) |
| L06 | Root files and CI — `README`, `CHANGELOG`, `Makefile`, `pyproject`, `.github/` | [`inventory/L06-root-ci.md`](inventory/L06-root-ci.md) |
| L07 | Core documentation — `docs/` incl. the website patch package | [`inventory/L07-docs-core.md`](inventory/L07-docs-core.md) |
| L08 | Human-action packages — `docs/human-actions/` (37 files) | [`inventory/L08-human-actions.md`](inventory/L08-human-actions.md) |
| L09 | Deliverables — `dashboard/`, `excel/`, `presentation/`, `reports/` | [`inventory/L09-deliverables.md`](inventory/L09-deliverables.md) |
| L10 | 3D explorer — Python ETL, build, tests | [`inventory/L10-explorer-python.md`](inventory/L10-explorer-python.md) |
| L11 | 3D explorer — web viewer and built data | [`inventory/L11-explorer-web.md`](inventory/L11-explorer-web.md) |
| L12 | Binary verification — PDFs, PPTX, DOCX, XLSX, PNGs, GLBs | [`inventory/L12-binaries.md`](inventory/L12-binaries.md) |

## The shape of the repository, in one paragraph

`src/fcf_m2/` is the **only** scorer; nothing else in the project may re-derive a number. It runs in eleven
declared steps (`workflow.STEPS`) under one of two modes — `legacy_v2` (bit-exact reproduction of the
accepted V2 baseline) or `milestone2_v3` (canonical, fixed-anchor, cohort-independent) — and its terminal
product is the **canonical data contract** at `data/contract/v1/`: six tables plus a manifest carrying a
SHA-256 chain over five inputs and six outputs. Every other artifact in the repository is a **consumer** of
that contract: the MATLAB layer reads a generated adapter CSV, the Excel workbook and static dashboard and
reports are built from it, and the Tableau patch package quotes it. `tests/` guards the legacy goldens and
the contract; `scripts/verify.sh` is the local gate harness and `.github/workflows/tests.yml` the CI one.
The 3D explorer sits outside all of this — it was never in the repository, and it reads the *legacy* fixtures
rather than the canonical contract, which is the defect Phase 3 exists to fix.

## Complete file table

### Tree: `repo` — 198 files

| File | Size | Kind | Lane |
|---|---:|---|---|
| `.github/pull_request_template.md` | 891 B | authored | [L06](inventory/) |
| `.github/workflows/matlab-manual.yml` | 1.6 KB | authored | [L06](inventory/) |
| `.github/workflows/tests.yml` | 2.1 KB | authored | [L06](inventory/) |
| `.gitignore` | 387 B | authored | [L06](inventory/) |
| `CHANGELOG.md` | 2.7 KB | authored | [L06](inventory/) |
| `CONTRIBUTING.md` | 2.3 KB | authored | [L06](inventory/) |
| `Makefile` | 626 B | authored | [L06](inventory/) |
| `README.md` | 8.8 KB | authored | [L06](inventory/) |
| `dashboard/README.md` | 1.0 KB | authored | [L09](inventory/) |
| `dashboard/static/01_readiness_ranking.png` | 178.9 KB | generated — `scripts/build_static_dashboard.py` | [L09, L12](inventory/) |
| `dashboard/static/02_starter_vs_pathway.png` | 98.4 KB | generated — `scripts/build_static_dashboard.py` | [L09, L12](inventory/) |
| `dashboard/static/03_ports_three_horizons.png` | 126.6 KB | generated — `scripts/build_static_dashboard.py` | [L09, L12](inventory/) |
| `dashboard/static/04_lifecycle_cost.png` | 103.7 KB | generated — `scripts/build_static_dashboard.py` | [L09, L12](inventory/) |
| `dashboard/static/05_net_co2e.png` | 133.5 KB | generated — `scripts/build_static_dashboard.py` | [L09, L12](inventory/) |
| `dashboard/static/06_avoided_evse.png` | 103.2 KB | generated — `scripts/build_static_dashboard.py` | [L09, L12](inventory/) |
| `dashboard/static/07_peak_wait.png` | 85.0 KB | generated — `scripts/build_static_dashboard.py` | [L09, L12](inventory/) |
| `dashboard/static/08_limitations.png` | 166.8 KB | generated — `scripts/build_static_dashboard.py` | [L09, L12](inventory/) |
| `dashboard/static/09_site_map_offline.png` | 184.1 KB | generated — `scripts/build_static_dashboard.py` | [L09, L12](inventory/) |
| `dashboard/static/STATIC_DASHBOARD.pdf` | 1.1 MB | binary | [L09, L12](inventory/) |
| `dashboard/static/footer_log.json` | 3.5 KB | generated — `scripts/build_static_dashboard.py` | [L09](inventory/) |
| `dashboard/tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md` | 3.6 KB | authored | [L09](inventory/) |
| `dashboard/tableau/patch_package/tbl_avoided_evse.csv` | 23.1 KB | authored | [L09](inventory/) |
| `dashboard/tableau/patch_package/tbl_canonical_scenarios.csv` | 98.0 KB | authored | [L09](inventory/) |
| `dashboard/tableau/patch_package/tbl_peak_waits.csv` | 1.2 KB | authored | [L09](inventory/) |
| `dashboard/tableau/patch_package/tbl_portfolio_costs.csv` | 2.1 KB | authored | [L09](inventory/) |
| `dashboard/tableau/patch_package/tbl_readiness_confidence.csv` | 4.0 KB | authored | [L09](inventory/) |
| `dashboard/tableau/patch_package/tbl_sites_dimension.csv` | 1.4 KB | authored | [L09](inventory/) |
| `data/README.md` | 2.0 KB | authored | [L05](inventory/) |
| `data/anchors/anchor_set_v1.json` | 2.2 KB | authored | [L05](inventory/) |
| `data/cache/boundaries/ATTRIBUTION.md` | 722 B | authored | [L05](inventory/) |
| `data/cache/boundaries/tl_2024_va_counties.geojson` | 168.0 KB | authored | [L05](inventory/) |
| `data/contract/v1/README.md` | 1.3 KB | authored | [L05](inventory/) |
| `data/contract/v1/assumptions.json` | 4.0 KB | generated — `fcf_m2.contract` (`make run-v3`) | [L05](inventory/) |
| `data/contract/v1/contract_manifest.json` | 2.1 KB | generated — `fcf_m2.contract` (`make run-v3`) | [L05](inventory/) |
| `data/contract/v1/scenario_table.csv` | 98.0 KB | generated — `fcf_m2.contract` (`make run-v3`) | [L05](inventory/) |
| `data/contract/v1/schema.json` | 5.6 KB | generated — `fcf_m2.contract` (`make run-v3`) | [L05](inventory/) |
| `data/contract/v1/site_table.csv` | 1.4 KB | generated — `fcf_m2.contract` (`make run-v3`) | [L05](inventory/) |
| `data/contract/v1/source_provenance.csv` | 11.1 KB | generated — `fcf_m2.contract` (`make run-v3`) | [L05](inventory/) |
| `data/contract/v1/standards_register.csv` | 176.8 KB | generated — `fcf_m2.contract` (`make run-v3`) | [L05](inventory/) |
| `data/inputs/legacy_matlab_site_meta.csv` | 2.0 KB | authored | [L05](inventory/) |
| `data/inputs/legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv` | 4.3 KB | authored | [L05](inventory/) |
| `data/inputs/real_sites_v2.csv` | 10.6 KB | authored | [L05](inventory/) |
| `data/observed/observed_sessions_template.csv` | 102 B | authored | [L05](inventory/) |
| `data/provenance/field_provenance_v1.csv` | 11.2 KB | generated — `scripts/build_field_provenance.py` | [L05](inventory/) |
| `data/provenance/site_coordinate_sources.csv` | 1.7 KB | authored | [L05](inventory/) |
| `data/provenance/v2_source_confidence_tracker.csv` | 4.2 KB | authored | [L05](inventory/) |
| `docs/README.md` | 2.2 KB | authored | [L07](inventory/) |
| `docs/WORKFLOW_STEPS.md` | 1.1 KB | generated — `fcf_m2.workflow` STEPS (`make docs`) | [L07](inventory/) |
| `docs/architecture/TECHNICAL_INTEGRATION_ARCHITECTURE.md` | 6.0 KB | authored | [L07](inventory/) |
| `docs/assets/architecture/integration_architecture.png` | 388.0 KB | binary | [L07, L12](inventory/) |
| `docs/assets/readme/project-overview.png` | 123.3 KB | binary | [L07, L12](inventory/) |
| `docs/assets/readme/site-map.png` | 153.4 KB | binary | [L07, L12](inventory/) |
| `docs/assets/readme/three-horizons.png` | 114.7 KB | binary | [L07, L12](inventory/) |
| `docs/human-actions/README.md` | 3.4 KB | authored | [L08](inventory/) |
| `docs/human-actions/ahj_fire_marshal/01_QUESTION_SET_FAIRFAX_CITY_FIRE_MARSHAL.md` | 3.0 KB | authored | [L08](inventory/) |
| `docs/human-actions/ahj_fire_marshal/02_QUESTION_SET_PWC_FIRE_MARSHAL.md` | 3.2 KB | authored | [L08](inventory/) |
| `docs/human-actions/ahj_fire_marshal/03_SITE_REVIEW_PACKET_TOP3.md` | 3.0 KB | authored | [L08](inventory/) |
| `docs/human-actions/ahj_fire_marshal/04_CODE_EDITION_CONFIRMATION_CHECKLIST.md` | 1.9 KB | authored | [L08](inventory/) |
| `docs/human-actions/ahj_fire_marshal/05_PROPOSED_STANDARD_FEEDBACK_SHEET.md` | 2.4 KB | authored | [L08](inventory/) |
| `docs/human-actions/client_meeting_2/01_EMAIL_DRAFT_TO_CLIENT.md` | 2.4 KB | authored | [L08](inventory/) |
| `docs/human-actions/client_meeting_2/02_CLIENT_PREREAD.md` | 3.6 KB | authored | [L08](inventory/) |
| `docs/human-actions/client_meeting_2/03_MEETING_AGENDA.md` | 1.7 KB | authored | [L08](inventory/) |
| `docs/human-actions/client_meeting_2/04_ALTERNATIVES_BRIEFING.md` | 4.5 KB | authored | [L08](inventory/) |
| `docs/human-actions/client_meeting_2/05_CLIENT_FEEDBACK_FORM.md` | 783 B | authored | [L08](inventory/) |
| `docs/human-actions/client_meeting_2/06_DECISION_LOG.md` | 395 B | authored | [L08](inventory/) |
| `docs/human-actions/client_meeting_2/07_WHAT_CHANGED_REGISTER.md` | 573 B | authored | [L08](inventory/) |
| `docs/human-actions/client_meeting_2/08_ATTENDANCE_RECORD.md` | 647 B | authored | [L08](inventory/) |
| `docs/human-actions/client_meeting_2/09_FOLLOWUP_EMAIL_DRAFT.md` | 1.3 KB | authored | [L08](inventory/) |
| `docs/human-actions/client_meeting_2/10_ACCEPTANCE_CHECKLIST.md` | 1.9 KB | authored | [L08](inventory/) |
| `docs/human-actions/fellowship_confirmation/01_EMAIL_DRAFT_FELLOWSHIP_STAFF.md` | 2.4 KB | authored | [L08](inventory/) |
| `docs/human-actions/fellowship_confirmation/02_CONTINGENCY_SUMMARY.md` | 2.7 KB | authored | [L08](inventory/) |
| `docs/human-actions/public_engagement/01_SURVEY.md` | 2.1 KB | authored | [L08](inventory/) |
| `docs/human-actions/public_engagement/02_ACCESSIBLE_USER_REVIEW.md` | 2.8 KB | authored | [L08](inventory/) |
| `docs/human-actions/public_engagement/03_LISTENING_SESSION_ONE_PAGER.md` | 2.6 KB | authored | [L08](inventory/) |
| `docs/human-actions/public_engagement/04_LANGUAGE_ACCESS_PLAN.md` | 1.9 KB | authored | [L08](inventory/) |
| `docs/human-actions/public_engagement/05_PRIVACY_NOTICE.md` | 2.3 KB | authored | [L08](inventory/) |
| `docs/human-actions/public_engagement/06_FEEDBACK_TO_DECISION_MATRIX.md` | 1.0 KB | authored | [L08](inventory/) |
| `docs/human-actions/public_engagement/07_EQUITY_REVIEW_PROTOCOL.md` | 2.4 KB | authored | [L08](inventory/) |
| `docs/human-actions/public_engagement/08_STAKEHOLDER_CONTACT_MAP.md` | 2.8 KB | authored | [L08](inventory/) |
| `docs/human-actions/team_alternatives_session/01_FACILITATION_GUIDE.md` | 3.2 KB | authored | [L08](inventory/) |
| `docs/human-actions/team_alternatives_session/02_PROVISIONAL_MCDA.md` | 3.3 KB | authored | [L08](inventory/) |
| `docs/human-actions/team_alternatives_session/03_TEAM_SCORING_SHEET.md` | 1.0 KB | authored | [L08](inventory/) |
| `docs/human-actions/team_alternatives_session/04_WEIGHT_ADOPTION_PAGE.md` | 1.4 KB | authored | [L08](inventory/) |
| `docs/human-actions/team_alternatives_session/05_DISSENT_LOG.md` | 698 B | authored | [L08](inventory/) |
| `docs/human-actions/team_alternatives_session/06_COI_ASSUMPTION_NOTE.md` | 1.5 KB | authored | [L08](inventory/) |
| `docs/human-actions/team_alternatives_session/07_DECISION_RECORD_TEMPLATE.md` | 1.6 KB | authored | [L08](inventory/) |
| `docs/human-actions/utility_facility_data/01_DATA_REQUEST_DOMINION.md` | 2.5 KB | authored | [L08](inventory/) |
| `docs/human-actions/utility_facility_data/02_DATA_REQUEST_FACILITY_MANAGERS.md` | 2.1 KB | authored | [L08](inventory/) |
| `docs/human-actions/utility_facility_data/03_TRACKING_REGISTER.md` | 3.0 KB | authored | [L08](inventory/) |
| `docs/human-actions/utility_facility_data/04_DATA_FLOW_INTO_MODEL.md` | 3.0 KB | authored | [L08](inventory/) |
| `docs/methodology/current-facts-source-register.md` | 3.9 KB | authored | [L07](inventory/) |
| `docs/migration-from-v2.md` | 4.6 KB | authored | [L07](inventory/) |
| `docs/operations/legacy-baseline/BASELINE_VERIFICATION.md` | 2.6 KB | authored | [L07](inventory/) |
| `docs/operations/legacy-baseline/v1_output_hashes.txt` | 1.4 KB | authored | [L07](inventory/) |
| `docs/operations/legacy-baseline/v2_output_hashes.txt` | 8.4 KB | authored | [L07](inventory/) |
| `docs/operations/open-human-actions.md` | 3.1 KB | authored | [L07](inventory/) |
| `docs/operations/reproduction-guide.md` | 3.8 KB | authored | [L07](inventory/) |
| `docs/operations/website-patch-package/DEPLOYMENT_RUNBOOK.md` | 1.2 KB | authored | [L07](inventory/) |
| `docs/operations/website-patch-package/PATCH_GUIDE.md` | 3.1 KB | authored | [L07](inventory/) |
| `docs/operations/website-patch-package/README.md` | 2.5 KB | authored | [L07](inventory/) |
| `docs/operations/website-patch-package/content/assistant_boundaries.md` | 1.1 KB | authored | [L07](inventory/) |
| `docs/operations/website-patch-package/content/authority_disclaimer.md` | 471 B | authored | [L07](inventory/) |
| `docs/operations/website-patch-package/content/limitations_update.md` | 1.1 KB | authored | [L07](inventory/) |
| `docs/operations/website-patch-package/content/methodology_update.md` | 1.5 KB | authored | [L07](inventory/) |
| `docs/operations/website-patch-package/content/privacy_notice.md` | 1.0 KB | authored | [L07](inventory/) |
| `docs/operations/website-patch-package/content/results_2036_2046_2056.md` | 1.4 KB | authored | [L07](inventory/) |
| `docs/operations/website-patch-package/content/source_vintage_footer.html` | 418 B | authored | [L07](inventory/) |
| `docs/operations/website-patch-package/content/standards_summary.md` | 1.5 KB | authored | [L07](inventory/) |
| `docs/repository-migration-plan.md` | 3.5 KB | authored | [L07](inventory/) |
| `docs/standards/FINAL_STANDARDS_APPLICATION_MATRIX.md` | 12.6 KB | authored | [L07](inventory/) |
| `docs/standards/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.md` | 9.8 KB | authored | [L07](inventory/) |
| `excel/Electric_Data_Milestone_2_Updated.xlsx` | 54.8 KB | generated — `scripts/build_excel_workbook.py` | [L09, L12](inventory/) |
| `excel/README.md` | 1.2 KB | authored | [L09](inventory/) |
| `matlab/DATA_DICTIONARY.md` | 4.9 KB | authored | [L04](inventory/) |
| `matlab/EXECUTION_STATUS.md` | 4.2 KB | authored | [L04](inventory/) |
| `matlab/README.md` | 10.4 KB | authored | [L04](inventory/) |
| `matlab/RUN_ON_LICENSED_MATLAB.md` | 5.1 KB | authored | [L04](inventory/) |
| `matlab/data/canonical/matlab_scenarios.csv` | 52.5 KB | generated — `fcf_m2.matlab_adapter` (`make run-v3`) | [L04](inventory/) |
| `matlab/legacy_archive/MIGRATION_NOTE.md` | 4.6 KB | authored | [L04](inventory/) |
| `matlab/legacy_archive/build_and_run_site_grid_behavior_model.m` | 12.9 KB | authored | [L04](inventory/) |
| `matlab/legacy_archive/untitled.m` | 32.2 KB | authored | [L04](inventory/) |
| `matlab/outputs/.gitkeep` | 0 B | authored | [L04](inventory/) |
| `matlab/src/buildSimulinkModel.m` | 10.6 KB | authored | [L03](inventory/) |
| `matlab/src/capacityGuard.m` | 8.4 KB | authored | [L03](inventory/) |
| `matlab/src/electricalEconomics.m` | 6.8 KB | authored | [L03](inventory/) |
| `matlab/src/loadScenarios.m` | 8.3 KB | authored | [L03](inventory/) |
| `matlab/src/makeSessionProfiles.m` | 13.1 KB | authored | [L03](inventory/) |
| `matlab/src/managedCharging.m` | 13.2 KB | authored | [L03](inventory/) |
| `matlab/src/plotScenario.m` | 9.5 KB | authored | [L03](inventory/) |
| `matlab/src/runScenario.m` | 7.7 KB | authored | [L03](inventory/) |
| `matlab/src/run_all_scenarios.m` | 8.1 KB | authored | [L03](inventory/) |
| `matlab/tests/test_capacityGuard.m` | 5.4 KB | authored | [L04](inventory/) |
| `matlab/tests/test_horizons.m` | 3.6 KB | authored | [L04](inventory/) |
| `matlab/tests/test_loadScenarios.m` | 4.6 KB | authored | [L04](inventory/) |
| `matlab/tests/test_managedCharging.m` | 9.0 KB | authored | [L04](inventory/) |
| `matlab/tests/test_profiles.m` | 6.4 KB | authored | [L04](inventory/) |
| `matlab/tests/test_regression.m` | 5.5 KB | authored | [L04](inventory/) |
| `presentation/README.md` | 1.2 KB | authored | [L09](inventory/) |
| `presentation/assets/10_mcda_provisional.png` | 159.0 KB | binary | [L09, L12](inventory/) |
| `presentation/deck/Future_City_Fellowship_Milestone_2_Final.pdf` | 1.4 MB | binary | [L09, L12](inventory/) |
| `presentation/deck/Future_City_Fellowship_Milestone_2_Final.pptx` | 1.5 MB | binary | [L09, L12](inventory/) |
| `presentation/deck/Future_City_Fellowship_Milestone_2_QA_Backup.pdf` | 153.3 KB | binary | [L09, L12](inventory/) |
| `presentation/deck/Future_City_Fellowship_Milestone_2_Speaker_Notes.md` | 10.1 KB | authored | [L09](inventory/) |
| `presentation/deck/Future_City_Fellowship_Milestone_2_Timing_Runbook.md` | 4.9 KB | authored | [L09](inventory/) |
| `pyproject.toml` | 822 B | authored | [L06](inventory/) |
| `reports/README.md` | 1.2 KB | authored | [L09](inventory/) |
| `reports/milestone-2/ECONOMIC_AND_FUNDING_BRIEF.md` | 5.9 KB | authored | [L09](inventory/) |
| `reports/milestone-2/ENVIRONMENT_AND_RESILIENCE.md` | 6.0 KB | authored | [L09](inventory/) |
| `reports/milestone-2/FINAL_STANDARDS_APPLICATION_MATRIX.docx` | 42.8 KB | generated — `scripts/md_to_docx.py` | [L09, L12](inventory/) |
| `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.docx` | 46.9 KB | generated — `scripts/md_to_docx.py` | [L09, L12](inventory/) |
| `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.md` | 21.7 KB | authored | [L09](inventory/) |
| `reports/milestone-2/Future_City_Fellowship_Milestone_2_Final_Report.pdf` | 184.0 KB | binary | [L09, L12](inventory/) |
| `reports/milestone-2/Milestone_2_Gap_Closure_Status.docx` | 42.5 KB | generated — `scripts/md_to_docx.py` | [L09, L12](inventory/) |
| `reports/milestone-2/Milestone_2_Gap_Closure_Status.md` | 12.9 KB | authored | [L09](inventory/) |
| `reports/milestone-2/PROPOSED_MUNICIPAL_EV_STANDARD_CONCEPT.docx` | 41.9 KB | generated — `scripts/md_to_docx.py` | [L09, L12](inventory/) |
| `reports/milestone-2/REGULATORY_STAKEHOLDER_MAP.md` | 5.0 KB | authored | [L09](inventory/) |
| `reports/milestone-2/RISK_REGISTER.csv` | 9.3 KB | authored | [L09](inventory/) |
| `reports/milestone-2/RISK_REGISTER.md` | 7.6 KB | authored | [L09](inventory/) |
| `requirements-lock.txt` | 428 B | authored | [L06](inventory/) |
| `scripts/README.md` | 1.1 KB | authored | [L02](inventory/) |
| `scripts/build_excel_workbook.py` | 16.1 KB | authored | [L02](inventory/) |
| `scripts/build_field_provenance.py` | 3.6 KB | authored | [L02](inventory/) |
| `scripts/build_release_artifact.py` | 3.4 KB | authored | [L02](inventory/) |
| `scripts/build_static_dashboard.py` | 11.1 KB | authored | [L02](inventory/) |
| `scripts/check_internal_links.py` | 1017 B | authored | [L02](inventory/) |
| `scripts/md_to_docx.py` | 3.7 KB | authored | [L02](inventory/) |
| `scripts/verify.sh` | 3.6 KB | authored | [L02](inventory/) |
| `src/README.md` | 2.1 KB | authored | [L01](inventory/) |
| `src/fcf_m2.egg-info/PKG-INFO` | 854 B | authored | [L01](inventory/) |
| `src/fcf_m2.egg-info/SOURCES.txt` | 721 B | authored | [L01](inventory/) |
| `src/fcf_m2.egg-info/dependency_links.txt` | 1 B | authored | [L01](inventory/) |
| `src/fcf_m2.egg-info/requires.txt` | 196 B | authored | [L01](inventory/) |
| `src/fcf_m2.egg-info/top_level.txt` | 7 B | authored | [L01](inventory/) |
| `src/fcf_m2/__init__.py` | 0 B | authored | [L01](inventory/) |
| `src/fcf_m2/confidence.py` | 4.6 KB | authored | [L01](inventory/) |
| `src/fcf_m2/config.py` | 7.4 KB | authored | [L01](inventory/) |
| `src/fcf_m2/contract.py` | 17.1 KB | authored | [L01](inventory/) |
| `src/fcf_m2/demand.py` | 6.2 KB | authored | [L01](inventory/) |
| `src/fcf_m2/economics.py` | 7.7 KB | authored | [L01](inventory/) |
| `src/fcf_m2/emissions.py` | 3.7 KB | authored | [L01](inventory/) |
| `src/fcf_m2/gis_offline.py` | 3.1 KB | authored | [L01](inventory/) |
| `src/fcf_m2/matlab_adapter.py` | 3.4 KB | authored | [L01](inventory/) |
| `src/fcf_m2/peak_wait.py` | 4.3 KB | authored | [L01](inventory/) |
| `src/fcf_m2/queueing.py` | 2.1 KB | authored | [L01](inventory/) |
| `src/fcf_m2/right_sizing.py` | 12.7 KB | authored | [L01](inventory/) |
| `src/fcf_m2/scoring.py` | 8.2 KB | authored | [L01](inventory/) |
| `src/fcf_m2/standards.py` | 10.9 KB | authored | [L01](inventory/) |
| `src/fcf_m2/triggers.py` | 3.8 KB | authored | [L01](inventory/) |
| `src/fcf_m2/visuals.py` | 2.9 KB | authored | [L01](inventory/) |
| `src/fcf_m2/workflow.py` | 20.0 KB | authored | [L01](inventory/) |
| `tests/README.md` | 1.3 KB | authored | [L02](inventory/) |
| `tests/conftest.py` | 1.4 KB | authored | [L02](inventory/) |
| `tests/fixture_legacy_v2_right_sizing.csv` | 3.2 KB | authored | [L02](inventory/) |
| `tests/fixture_legacy_v2_site_results.csv` | 26.2 KB | authored | [L02](inventory/) |
| `tests/test_contract_and_integration.py` | 8.0 KB | authored | [L02](inventory/) |
| `tests/test_legacy_golden.py` | 1.7 KB | authored | [L02](inventory/) |
| `tests/test_modules.py` | 9.7 KB | authored | [L02](inventory/) |
| `tests/test_scoring_and_queueing.py` | 3.5 KB | authored | [L02](inventory/) |

### Tree: `fcf-3d` — 31 files

| File | Size | Kind | Lane |
|---|---:|---|---|
| `.gitignore` | 151 B | authored | [L10](inventory/) |
| `CLAUDE.md` | 4.5 KB | authored | [L10](inventory/) |
| `Makefile` | 4.4 KB | authored | [L10](inventory/) |
| `README.md` | 10.1 KB | authored | [L10](inventory/) |
| `blender/build_assets.py` | 6.7 KB | authored | [L10](inventory/) |
| `fcf3d/__init__.py` | 0 B | authored | [L10](inventory/) |
| `fcf3d/build_models.py` | 2.7 KB | authored | [L10](inventory/) |
| `fcf3d/build_sites.py` | 24.7 KB | authored | [L10](inventory/) |
| `fcf3d/geometry.py` | 9.0 KB | authored | [L10](inventory/) |
| `fcf3d/glb.py` | 7.4 KB | authored | [L10](inventory/) |
| `requirements.txt` | 159 B | authored | [L10](inventory/) |
| `tests/test_pipeline.py` | 12.1 KB | authored | [L10](inventory/) |
| `web/app.js` | 32.5 KB | authored | [L11](inventory/) |
| `web/data/manifest.json` | 796 B | authored | [L11](inventory/) |
| `web/data/sites.geojson` | 217.6 KB | authored | [L11](inventory/) |
| `web/data/sites.inline.js` | 163.1 KB | authored | [L11](inventory/) |
| `web/data/sites.json` | 200.5 KB | authored | [L11](inventory/) |
| `web/index.html` | 4.7 KB | authored | [L11](inventory/) |
| `web/models/FFX001.glb` | 19.2 KB | binary | [L12](inventory/) |
| `web/models/FFX002.glb` | 29.0 KB | binary | [L12](inventory/) |
| `web/models/FFX003.glb` | 19.2 KB | binary | [L12](inventory/) |
| `web/models/FFX004.glb` | 29.0 KB | binary | [L12](inventory/) |
| `web/models/PWC001.glb` | 17.8 KB | binary | [L12](inventory/) |
| `web/models/PWC002.glb` | 17.8 KB | binary | [L12](inventory/) |
| `web/models/PWC003.glb` | 14.9 KB | binary | [L12](inventory/) |
| `web/models/PWC004.glb` | 19.2 KB | binary | [L12](inventory/) |
| `web/models/PWC005.glb` | 14.9 KB | binary | [L12](inventory/) |
| `web/models/PWC006.glb` | 19.2 KB | binary | [L12](inventory/) |
| `web/models/PWC007.glb` | 19.2 KB | binary | [L12](inventory/) |
| `web/models/PWC008.glb` | 14.9 KB | binary | [L12](inventory/) |
| `web/style.css` | 14.9 KB | authored | [L11](inventory/) |