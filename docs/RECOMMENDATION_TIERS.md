# Recommendation Tiers

The model translates scores and review flags into plain-English planning recommendations.

The project uses two related planning layers:

```text
recommendation_tier = broad planning priority
action_label = next practical step after readiness and data confidence are considered together
```

## Output columns

```text
model_rank
recommendation_tier
planning_recommendation
priority_reason
data_needed_next
data_confidence_score
data_confidence_level
readiness_confidence_cell
action_label
action_detail
```

## Main public visual artifact

The public-facing tier and action interpretation is now shown most clearly in the Tableau workbook documented in:

```text
tableau/README.md
```

Static PNG charts and generated Markdown reports remain technical support outputs.

## Tier categories

### Tier 1 — advance to site screening

Strong current candidate. Advance to site screening and stakeholder confirmation before design or procurement.

### Tier 2 — promising candidate, refine data

Promising candidate. Improve demand, parking, operating-hours, and electrical assumptions before advancement.

### High-review candidate

The site has value, but a major review issue needs to be resolved before advancement. This currently applies especially to garage context.

### Low public-priority / special-use

The site should not advance as a general-public charging site until the public-access or fleet-only use case is confirmed.

### Tier 3 — lower priority / monitor

The site is lower priority than stronger alternatives in the current model. Monitor and revisit after stronger data is available.

## Current V2 tier interpretation

```text
FFX002 — Tier 1 / strongest current public candidate
FFX004 — Tier 1 / second-ranked Tier 1 candidate
PWC006 — Tier 2 / strongest current Prince William County library candidate
FFX001 — Tier 2 / credible starter-install candidate
PWC002 — High-review candidate because of garage context
PWC007 — Tier 2 / promising candidate, refine data
PWC004 — Tier 2 / promising library candidate with data and context caveats
FFX003 — Tier 2 / promising candidate, refine data
PWC008 — Tier 3 / monitor due to nearby supply and scenario sensitivity
PWC001 — Tier 3 / lower priority under current assumptions
PWC005 — Tier 3 / monitor or small pilot
PWC003 — Low public-priority / special-use because public access is limited
```

## Current action interpretation

```text
FFX002 — verify key data, then advance to site screening
FFX004 — verify key data, then advance to site screening
PWC006 — refine assumptions and keep in active planning discussion
FFX001 — starter install with expandable design, pending confirmation
PWC002 — review before advancement
PWC003 — confirm whether the site is public, fleet-only, special-use, or should be removed
```

## Important caution

Recommendation tiers and action labels are planning-support outputs. They do not replace utility review, facility review, engineering design, ADA review, fire/AHJ review, stormwater review, permitting, or procurement decisions.
