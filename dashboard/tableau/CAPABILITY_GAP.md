# Tableau capability gap — what the build recipe asked for, and what could be built

Assessed **before** building anything, by diffing
[`TABLEAU_IMPLEMENTATION_BLOCKER.md`](TABLEAU_IMPLEMENTATION_BLOCKER.md)'s build recipe
against the authoring server's declared capability boundary
(`get_authoring_capabilities`, spec v0.1, verified against Tableau Public 2026.2.0).

**Nothing was silently substituted.** Where a substitute was used, it is named here *and* in
the affected sheet's own subtitle, so a screenshot separated from this document still says
what it is.

## The diff

| # | Recipe asks for | Buildable | What shipped |
|---|---|---|---|
| 1 | Readiness ranking — bar, colour by confidence | **yes** | As specified. |
| 2 | Starter vs pathway — **bar-in-bar** | **no** | **Grouped bars.** No dual axis in v0.1. A grouped bar is a different chart, and the subtitle says so. |
| 3 | Three horizons — line + **reference line at y=48** | **partial** | Line built. **No reference line** — none are generated. The 48-port ceiling rides in the tooltip as `pathway_capacity` and is named in the subtitle. |
| 4 | Lifecycle cost — side-by-side bar | **yes** | As specified, from the long-form cost table. |
| 5 | Net CO2e — line, caption carries factor + vintage | **yes** | Factor, subregion, rate and vintage all in the subtitle, from `config.py`. |
| 6 | Peak waits — bar + **reference line at 10 min** | **partial** | Bars built. **No reference line.** The 10-minute screening threshold is stated in the subtitle instead. |
| 7 | Map — lat/lon, size by pathway, colour top-3 | **yes**, with a caveat | **Symbol** map, which is what the recipe asked for. Coloured by data confidence rather than top-3 rank, because all twelve are `Low` and that is the more honest thing for the colour channel to carry. |
| 8 | Dashboard 1600×900, filters scoped to sheets 3–5 | **partial** | Dashboard built at 1600×900 with four sheets in one container. **No filter cards and no scoping** — dashboard extras are not generated. |
| 9 | **Story, 8 points** | **no** | **Not built.** Stories are not implemented. |

## Residual blockers — the honest list

These remain open. They need Tableau Desktop or a hand-authored workbook; this repository
does not claim them:

1. **Bar-in-bar** (recipe sheet 2) — needs a dual axis.
2. **Reference lines** (recipe sheets 3 and 6) — two of them.
3. **Dashboard filter cards, and scoping a filter to a subset of sheets** (recipe dashboard).
4. **The 8-point story** (recipe story).

None of the four changes a number. Each is a presentation affordance, and each is stated
rather than approximated — a reference line replaced by a tooltip is not a reference line,
and calling it one would be the "silently substitute a symbol map for a choropleth" failure
this assessment exists to prevent.

## What was *not* a gap

The recipe asks for a **symbol** map, not a choropleth. That is fortunate — filled maps are
outside the boundary — but it is worth recording that this was checked rather than assumed,
because a county-level readiness study is exactly the kind of work where a choropleth would
normally have been specified.

## A separate finding, and the more serious one

**The patch package's own numbers are mixed-provenance.**

`patch_package/tbl_readiness_confidence.csv` carries `readiness_score` and `model_rank`
**byte-equal to `legacy_v2`**, while the `data_confidence_level_v3` column beside them is the
v3 value. Verified against both runs, not inferred:

| site | patch package | `legacy_v2` | canonical `milestone2_v3` |
|---|---|---|---|
| FFX002 | **58.8**, rank **1** | 58.8, rank 1 | 51.8, rank **2** |
| FFX004 | 54.4, rank 2 | 54.4, rank 2 | **53.4**, rank **1** |

Nothing in the file declares the mix, so a workbook built from it would publish the legacy
ranking under a v3 heading — **the top-ranked site would be wrong**. That is the same defect
Phase 1 corrected in `README.md`, surviving in the build inputs.

So the rebuilt workbook derives every sheet from `data/contract/v1/` and the canonical
`milestone2_v3` run, and **every emitted CSV carries a `model_mode` column**. The patch
package is still used for two tables that have no canonical equivalent — portfolio costs and
peak waits — and those are contract-derived and not mode-sensitive.

The patch package is left in place rather than edited: it is what a Tableau Desktop operator
was handed, and rewriting it now would erase the evidence that the recipe needs correcting.
**Anyone following the recipe by hand must read this section first.**
