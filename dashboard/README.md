# `dashboard/` — presentation dashboards

[← repository root](../README.md)

## `static/` — the guaranteed offline dashboard

Nine contract-derived visuals + `STATIC_DASHBOARD.pdf`, each carrying a mandatory
source/vintage/assumption footer (`footer_log.json` is the audit trail; verify.sh
fails if any chart lacks a footer entry). These are the presentation-facing assets —
the team's chosen demo strategy is static visuals, deliberately independent of live
software, networks, or logins.

Rebuild: `make run-v3 && python scripts/build_static_dashboard.py`.

## `tableau/` — patch package for a Tableau Desktop operator

A verified `.twbx` could not be produced (no Tableau Desktop available; Tableau
Public was rejected because it can only save to its public cloud). This folder
contains the honest blocker note, six contract-derived CSVs, and an exact
worksheet/dashboard/story build recipe — see
[TABLEAU_IMPLEMENTATION_BLOCKER.md](tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md).
Nothing here claims a verified workbook.
