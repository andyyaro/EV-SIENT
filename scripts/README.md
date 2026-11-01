# `scripts/` - verification and artifact builders

[← repository root](../README.md)

| Script | Purpose |
|---|---|
| `verify.sh` | Every repository gate: tests+coverage, legacy reproduction, contract validation, cross-model reconciliation, footer QA, secret/path/size scans, link check. Run from the repo root. |
| `check_internal_links.py` | Relative-Markdown-link checker (used by verify.sh and CI) |
| `build_static_dashboard.py` | Rebuilds `dashboard/static/` from the contract (prereq: `make run-v3`) |
| `build_excel_workbook.py` | Rebuilds `excel/Electric_Data_Milestone_2_Updated.xlsx`; requires the team's original source workbook via `--source` (not tracked here) |
| `build_field_provenance.py` | Regenerates `data/provenance/field_provenance_v1.csv` from the site table (documented derivation rules) |
| `build_release_artifact.py` | Hash-logged release ZIP of source + outputs; run locally, and by `package.yml` for tagged releases |
| `md_to_docx.py` | Markdown → styled Word conversion used for the report deliverables |

All scripts use repo-relative paths and write generated outputs to gitignored
locations except the deliverables they intentionally refresh.
