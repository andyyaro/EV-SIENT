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
  "format": null,
  "categories": ["Low", "Moderate", "High"],
  "categoriesOrdered": true,
  "missingValues": ["Unknown"],
  "decimalChar": null,
  "evsient:role": "ordinal",
  "evsient:unit": null,
  "evsient:range": null,
  "evsient:direction": "lower_better",
  "evsient:modelField": "stormwater_risk",
  "evsient:evidence": [
    {"signal": "header", "match": "risk", "text": "the header word 'risk' suggests a scale of levels"},
    {"signal": "scale", "match": "Low < Moderate < High", "text": "values match the scale Low < Moderate < High"},
    {"signal": "direction", "match": "risk", "direction": "lower_better",
     "text": "the word 'risk' in the header suggests lower is better; a proposal only, until you confirm a direction"},
    {"signal": "mapping", "match": "stormwater_risk",
     "text": "Map Columns matched this column to the model's field stormwater_risk, which the model reads as yes or no"}
  ],
  "evsient:agreement": "agree",
  "evsient:provenance": "confirmed_by_user",
  "evsient:reading": {
    "cells": 360, "read": 345, "missing": 15, "unreadable": 0, "ambiguous": 0,
    "outOfRange": 0, "notWhole": 0, "decimalSeparator": null, "distinct": 3,
    "min": null, "max": null,
    "patterns": [{"pattern": "Low", "kind": "value", "readAs": "Low (1 of 3)", "count": 167},
                 {"pattern": "Moderate", "kind": "value", "readAs": "Moderate (2 of 3)", "count": 112},
                 {"pattern": "High", "kind": "value", "readAs": "High (3 of 3)", "count": 66},
                 {"pattern": "Unknown", "kind": "missing", "readAs": "missing", "count": 15}],
    "patternsNotShown": null,
    "sentinels": []
  }
}
```

- **Roles** (`evsient:role`): `identifier`, `name`, `category`, `ordinal`, `flag` (yes/no, with
  extra states listed as missing or as categories), `count`, `measure` (has a unit), `score`
  (a bounded scale such as 0 to 100 or 1 to 5, in `evsient:range`), `percentage`, `money`
  (ISO 4217 code in `evsient:unit`), `date`, `year`, `latitude`, `longitude`, `address`,
  `text`, `unknown`. A declared Likert range (`_1_5`, `_1_7`) whose values are all whole and
  inside it is an `ordinal` with levels `[1, 2, 3, 4, 5]`; one with a value outside it or a
  decimal is a `score` and a conflict. A `flag`'s `categories` are its yes forms, its no forms
  and its extra states (such as "Seasonal"), in that order. A `measure` with no unit in its
  header has `evsient:unit` null.
- **Every entry has every key above**, in that order. The standard Frictionless keys that do not
  apply to a role (`format`, `categories`, `categoriesOrdered`, `decimalChar`) are null in the
  entry and left out of the Table Schema; `from_table_schema` restores them, so the round trip
  is exact. `format` is a date column's order (`%Y-%m-%d`, `%d/%m/%Y` or `%m/%d/%Y`, or null
  while undecided); `decimalChar` is a number column's decimal mark (null while undecided).
- **Units** are UCUM codes (`kW`, `m2`, `kW.h`) or ISO 4217 for money (`USD`). Units come from
  the header only when the header says so (`_kw`, `_m2`, `_usd`); otherwise `null`. A currency
  sign in the cells is evidence, never the unit.
- **Direction** (`evsient:direction`): `higher_better`, `lower_better`, `neither`, or `null`
  until the visitor confirms. A proposed direction lives in `evsient:evidence` only; the field
  itself stays `null` while `evsient:provenance` is `inferred`. Categories, identifiers, names,
  text, addresses and coordinates cannot be higher or lower better.
- **Evidence** items are `{"signal", "match", "text"}`, plus `"direction"` for a direction
  proposal. `signal` is `header`, `values`, `scale`, `range`, `direction` or `mapping`; `match`
  is the exact header token or value fact; `text` is the sentence shown. **Agreement** is
  `agree` when the header and the values say the same thing, `conflict` when they disagree or
  the reading found values outside a declared range, mixed decimal marks or a doubled level,
  and `unknown` when only one signal speaks.
- **Provenance**: `inferred` or `confirmed_by_user`. A confirmed entry is never relabelled.
- **Reading report**: every distinct raw pattern (capped at 50, the rest counted in
  `patternsNotShown`), how it was read (`readAs`), what kind of reading it was (`kind`: `value`,
  `missing`, `unreadable`, `ambiguous`, `sentinel`, `outOfRange`, `notWhole`, or `extra` for a
  flag's other states) and how many cells. Numbers are shown as shapes (`99.9`, `$9,999`) and
  anything unusual as its own text. `cells = read + missing + unreadable` always; `ambiguous`
  counts the cells that alone could be read two ways, read or not. Nothing is clamped, rounded
  or coerced without a pattern saying so. Read with `dtype=object`, `keep_default_na=False`; the
  missing markers are a visible list (`""`, `n/a`, `N/A`, `NULL`, `null`, `none`, `-`,
  `Unknown`, `unknown`, `TBD`, `To be confirmed`), compared without case or surrounding spaces,
  never pandas' defaults ("NA" is Namibia). `missingValues` lists the exact text found.
  Sentinels (-999, -99, 9999, 99999) are flagged in `sentinels`, never applied; -99 is not
  flagged where it is a valid longitude.
- **Decimal separators** are decided per column from unambiguous cells; ambiguous cells are
  counted, never guessed. With no deciding cell, or both marks in one column, an ambiguous cell
  is not read until the visitor chooses. Dates written with `/` follow the same rule for the
  order of day and month.
- `evsient:modelField` is the EV-SIENT field the column is mapped to, if any; mapping stays the
  job of Map Columns, and the dictionary records it. `propose` takes the mapping in intake's
  shape, `{model field: column}`.
- **Confirming**: `confirm(entries, changes)` takes `{"column", ...}` changes with any of `role`,
  `unit`, `direction`, `categories` (levels in order, lowest first), `missingValues`, `range`,
  `decimalSeparator`, `dateFormat`, or `confirm: true`, and raises a planner-readable error for
  anything the dictionary cannot hold. A change to how cells read sets `evsient:reading` to
  null; `reread(frame, entries)` makes it again. The browser reaches these through
  `bridge_propose`, `bridge_confirm` and `bridge_reread` (JSON in, JSON out).
- **The Table Schema** is `{"$schema": "https://datapackage.org/profiles/2.0/tableschema.json",
  "fields": [...], "missingValues": [""], "evsient:dictionaryVersion": 1}`; each field's own
  `missingValues` overrides the table's.
- **Typed values** (`parse`): numbers as floats, an ordinal as its level's position from 0, a
  flag as 1.0, 0.0 or NaN, a category as a pandas Categorical, a date as datetime64, other
  roles as text; columns `(name, "value")` and `(name, "raw")`, the raw cells untouched.

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

Details the engine settles (`fcf_m2.flex.index`, added with the first implementation):

- **Value function fields.** `linear` and `threshold` take `worst` and `best` (best above worst
  for higher_better, below it for lower_better); `target` takes `low`, `target` and `high`, full
  credit at the target falling to none at `low` and `high`, and only for `neither`; `ordinal`
  takes `map`, which must name every category in the dictionary entry, with values in [0, 1]
  that do not run against the confirmed direction. A linear criterion saved without anchors gets
  the observed range of the whole file, before screens, stored with `"pinnedFrom": "observed
  range"`; the run returns the completed spec, and running that spec again gives the same
  numbers.
- **Screens are keep conditions.** A site is kept when its rule is true; otherwise it is listed
  with the rule's `reason` and the columns it was missing. Operators: `var`, `==`, `!=`, `<`,
  `<=`, `>`, `>=`, `and`, `or`, `!`, `in`, `missing`; anything else is refused. Screens read the
  dictionary's reading (flags as 1 and 0, categories as their labels) and the raw text for
  columns without one. `<`, `<=`, `>`, `>=` need numbers, so a missing value never passes a
  numeric screen.
- **Robustness.** `spread` sets the Dirichlet concentration so each weight typically moves by
  that share of itself (0.25: about a quarter); `ordinalSpread` (default 0.2) moves the
  categories between the ends of each map, never past their neighbours. Ranks are counted with
  ties shared; the top k is 10 sites, or 10% of the ranked sites when there are under 100.
  "What would change the rank" gives, for each adjacent pair, the weight shift on each criterion
  (others rescaled to keep the sum at 1) at which the pair ties, and the value the lower site
  would need on each criterion.
- **Gates.** Dominance and "barely counts" use the Pearson correlation of each criterion's
  credit with the index over the ranked sites; size bias uses the Spearman correlation of the
  index with the population column (either sign); double counting uses the Spearman
  correlation of two criteria's credit over the sites that have both. A spec that fails the
  minimum-data rule is refused, and the refusal carries the `minimum_data` gate.

## 4. Where it runs

Python in `src/fcf_m2/flex/`, run in the browser by the same Pyodide worker as the engine (one
source of truth), reached through `browser_api`. pandas and numpy only by default; SciPy or
scikit-learn are imported lazily by the features that need them. Native and Pyodide results
must agree (`platform/tools/parity.mjs`).

## 5. What the assistant may see

Owner decision, 2026-10-18. The assistant proposes; the engine on the device computes every
number. What reaches the model is decided by these tiers, not by the model.

| Tier | Contents | When |
|---|---|---|
| Always | EV-SIENT's method, field definitions and FAQ; where the planner is in the app and the file's shape ("Check step, 360 rows, 31 columns") | Whenever the assistant is open |
| With consent | Column headers and their dictionary entries (role, unit, direction, scale); per-column blank share, a cardinality bucket and rounded 10th, 50th and 90th percentiles (never min or max); category labels with counts, any count under 10 suppressed; results the engine already computed (sites per tier, Explore cards, the visitor's index formula and its gates); one site's driver breakdown when the planner asks about that site, with the site renamed "Site A" | Opt-in once per session, after the planner sees the exact payload; any column can be withheld |
| Never | Rows or any single cell, sample values, site names, IDs, addresses, coordinates (even rounded), free-text notes, carried column values per site, the file name | Never |

Safeguards: Bedrock data retention `none`; the ledger records tokens, never content; headers
and labels travel as quoted, length-capped data with invisible Unicode and leading `= + - @`
removed; answers write numbers as placeholders filled from tool results, and any number that
does not match a tool result is struck through; causal verbs are refused.
