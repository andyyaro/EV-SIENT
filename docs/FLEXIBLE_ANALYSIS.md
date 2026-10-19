# Flexible analysis: the contract

How the planner reads, describes and lets a visitor rank columns the EV-SIENT model does not
use. The research behind it is the 2026-10-18 report "Flexible data analysis for planners"
(kept outside the repository). This file is the contract the engine modules and the interface
share; change it here first.

Three layers stay apart on every screen and in every export:

| Layer | What it is | Ranks sites? |
|---|---|---|
| The readiness model | EV-SIENT's published score (`fcf_m2`) | Yes, the official ranking |
| Explore | Descriptive findings about the visitor's own columns | No |
| Your index | A weighted sum the visitor builds from their own columns | Yes, labelled as theirs, never official |

Owner decisions this follows (defaults from the report, 2026-10-18): EV-first product; a
visitor's index may appear in reports and the project file as a separate labelled section;
direction must be confirmed before a column enters an index; missing values earn no credit
(DEC-011) with best and worst bounds, and sites below 65% coverage are not ranked; statistics
use BH at q = 0.10, groups under 10 sites are hidden, and "k of N checked" is always shown;
SciPy and scikit-learn load only when a feature needs them; free text gets local keyword
counts only; no on-device models; nothing in this file sends anything off the device.

## 1. The column dictionary

One entry per column of the visitor's file, proposed by `fcf_m2.flex.dictionary` and confirmed
by the visitor. Stored in the `.evsient` file as a Frictionless Data Package v2 Table Schema
(`fields[]`), with EV-SIENT's own properties prefixed `evsient:`.

```json
{
  "name": "flood_risk",
  "type": "string",
  "categories": ["Low", "Moderate", "High"],
  "categoriesOrdered": true,
  "missingValues": ["Unknown"],
  "evsient:role": "ordinal",
  "evsient:unit": null,
  "evsient:range": null,
  "evsient:direction": "lower_better",
  "evsient:modelField": "stormwater_risk",
  "evsient:evidence": [
    {"signal": "header", "text": "the word 'risk' in the header"},
    {"signal": "scale", "text": "values match the scale Low < Moderate < High"}
  ],
  "evsient:agreement": "agree",
  "evsient:provenance": "inferred",
  "evsient:reading": {
    "cells": 360, "read": 287, "missing": 73, "unreadable": 0, "ambiguous": 0,
    "decimalSeparator": null,
    "patterns": [{"pattern": "Moderate", "readAs": "Moderate (2 of 3)", "count": 112},
                 {"pattern": "Unknown", "readAs": "missing", "count": 73}],
    "sentinels": []
  }
}
```

- **Roles** (`evsient:role`): `identifier`, `name`, `category`, `ordinal`, `flag` (yes/no, with
  extra states listed as missing or as categories), `count`, `measure` (has a unit), `score`
  (a bounded scale such as 0 to 100 or 1 to 5, in `evsient:range`), `percentage`, `money`
  (ISO 4217 code in `evsient:unit`), `date`, `year`, `latitude`, `longitude`, `address`,
  `text`, `unknown`.
- **Units** are UCUM codes (`kW`, `m2`, `kW.h`) or ISO 4217 for money (`USD`). Units come from
  the header only when the header says so (`_kw`, `_m2`, `_usd`); otherwise `null`.
- **Direction** (`evsient:direction`): `higher_better`, `lower_better`, `neither`, or `null`
  until the visitor confirms. A proposed direction lives in `evsient:evidence` only; the field
  itself stays `null` while `evsient:provenance` is `inferred`.
- **Provenance**: `inferred` or `confirmed_by_user`. A confirmed entry is never relabelled.
- **Reading report**: every distinct raw pattern (capped at 50, the rest counted), how it was
  read and how many cells. Nothing is clamped, rounded or coerced without a pattern saying so.
  Read with `dtype=object`, `keep_default_na=False`; the missing markers are a visible list
  (`""`, `n/a`, `N/A`, `NULL`, `null`, `none`, `-`, `Unknown`, `unknown`, `TBD`, `To be
  confirmed`), never pandas' defaults ("NA" is Namibia). Sentinels (-999, -99, 9999) are
  flagged in `sentinels`, never applied.
- **Decimal separators** are decided per column from unambiguous cells; ambiguous cells are
  counted, never guessed.
- `evsient:modelField` is the EV-SIENT field the column is mapped to, if any; mapping stays the
  job of Map Columns, and the dictionary records it.

## 2. Explore

`fcf_m2.flex.explore` takes the table and the confirmed dictionary and returns insight cards.
It never ranks sites.

```json
{
  "checked": 61, "passed": 7, "fdr": 0.10, "minGroup": 10,
  "health": {"rows": 360, "columns": 31, "described": 24, "unknown": 2},
  "cards": [{
    "id": "assoc:heat_risk_0_100:service_population",
    "kind": "association",
    "columns": ["heat_risk_0_100", "service_population"],
    "sentence": "Sites with higher Heat Risk tend to have higher Service Population.",
    "effect": {"name": "spearman_rho", "value": 0.42, "low": 0.33, "high": 0.50},
    "n": 341, "q": 0.004, "reliability": "solid",
    "stratum": null,
    "chart": {"type": "scatter", "x": "heat_risk_0_100", "y": "service_population"},
    "siteIds": [],
    "footer": "Association, not cause. Pattern 4 of 61 checked."
  }]
}
```

The eight rules: count every test the scan runs; BH across the whole scan at q = 0.10; rank by
effect size with a bootstrap interval (p only gates); hide groups under 10 sites, mark under 30
"few sites"; fixed non-causal wording; ordinal columns as ordinal; "Unknown" reported as missing
with a check of whether missingness differs by group; suppress pairs related by construction
(|rho| > 0.98); show the within-country version beside any pooled result that reverses or
vanishes inside countries. Sentences are filled from computed values by templates only.

## 3. Your index

A pack-shaped spec, built by the visitor, run by `fcf_m2.flex.index`.

```json
{
  "pack": "evsient-custom-index", "packVersion": "1.0.0",
  "name": "Heat refuge priority",
  "criteria": [
    {"column": "heat_risk_0_100", "direction": "higher_better", "weight": 0.4,
     "value": {"kind": "linear", "worst": 0, "best": 100}},
    {"column": "flood_risk", "direction": "lower_better", "weight": 0.3,
     "value": {"kind": "ordinal", "map": {"Low": 1.0, "Moderate": 0.5, "High": 0.0}}},
    {"column": "solar_roof_potential_kw", "direction": "higher_better", "weight": 0.3,
     "value": {"kind": "threshold", "worst": 50, "best": 200}}
  ],
  "screens": [{"logic": {"!=": [{"var": "flood_risk"}, "High"]}, "reason": "High flood risk"}],
  "missing": "no_credit", "minCoverage": 0.65,
  "robustness": {"draws": 2000, "spread": 0.25, "seed": 1}
}
```

- Value functions are bounded to [0, 1] with pinned anchors, so each driver is weight x value and
  drivers sum to the score, as in the readiness model. Kinds: `linear`, `threshold` (no credit
  below worst, full credit at or above best, linear between; reversed for lower_better),
  `target`, `ordinal` (an explicit map, shown on screen). Anchors default to the observed range
  but are stored, so filtering never moves them.
- Weights are normalised to sum to 1 and shown that way.
- Screens are JsonLogic (no code), applied before scoring; excluded sites are listed with the
  reason.
- Missing values earn no credit; every site also gets a best case (missing at full credit) and
  worst case, and its completeness. Sites below `minCoverage` are listed, not ranked.
- Robustness: Monte Carlo over weights (and ordinal maps), reporting each site's rank 5th to
  95th percentile and the share of draws in the top k; "what would change the rank" is computed
  exactly for adjacent pairs.
- Gates, each a fixed message: coverage under 65% per criterion; |skewness| > 2 and kurtosis >
  3.5, or kurtosis > 10 (offer winsorising); a criterion correlated with the index above 0.95
  (dominates) or between -0.3 and 0.3 (barely counts); size bias (index vs a population column
  above 0.6); double counting (Spearman between two criteria above 0.8 warn, 0.9 strong);
  minimum data (2 criteria, 10 sites, no constant criterion, every direction confirmed).
- The result always carries `"official": false` and the visitor's name for it, and is never
  drawn on the readiness colour scale.

## 4. Where it runs

Python in `src/fcf_m2/flex/`, run in the browser by the same Pyodide worker as the engine (one
source of truth), reached through `browser_api`. pandas and numpy only by default; SciPy or
scikit-learn are imported lazily by the features that need them. Native and Pyodide results
must agree (`platform/tools/parity.mjs`).
