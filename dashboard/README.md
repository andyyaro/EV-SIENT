# `dashboard/` - presentation dashboards

[← repository root](../README.md)

## `static/` - the guaranteed offline dashboard

Nine contract-derived visuals + `STATIC_DASHBOARD.pdf`, each carrying a mandatory
source/vintage/assumption footer (`footer_log.json` is the audit trail; verify.sh
fails if any chart lacks a footer entry). These are the presentation-facing assets -
the team's chosen demo strategy is static visuals, deliberately independent of live
software, networks, or logins.

Rebuild: `make run-v3 && python scripts/build_static_dashboard.py`.

## `tableau/` - patch package for a Tableau Desktop operator

> **Corrected 2026-07-28.** This section said a verified `.twbx` could not be produced and
> that nothing here claims a verified workbook. Both were true when written and are no longer;
> the paragraph below replaces them. The original blocker note is kept for the record.

The workbook **has** been built, published and verified from the live artifact: `build/`
holds the `.twb`, the `.twbx`, a build manifest and seven sheet CSVs, all generated from the
canonical contract. It was verified by downloading the *published* package and reading its
Hyper extracts - FFX004 rank 1 at 53.4, all 12 sites Low confidence, horizons
2026/2036/2046/2056, totals 25/48. Those are contract v1's totals; the official pathway is 47
since DEC-027 (`data/contract/v3`), and the workbook has not been rebuilt from v3.

**Four kinds of presentation feature remain unbuildable** - **five rows** in the gap table, because the two reference lines are separate sheets - and each is named rather than approximated in [CAPABILITY_GAP.md](tableau/CAPABILITY_GAP.md): bar-in-bar, a reference line at y=48, a reference line at 10 min, dashboard filter scoping, and the 8-point story. The original blocker note is preserved at
[TABLEAU_IMPLEMENTATION_BLOCKER.md](tableau/TABLEAU_IMPLEMENTATION_BLOCKER.md) as the record of
why the package existed.
