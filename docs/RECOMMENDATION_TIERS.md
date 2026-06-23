# Recommendation Tiers

The model translates scores and review flags into plain-English planning recommendations.

## Output columns

```text
model_rank
recommendation_tier
planning_recommendation
priority_reason
data_needed_next
```

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

## Current expected interpretation

```text
FFX002 — Tier 1 / stable top candidate
FFX001 — Tier 1 / stable second candidate
PWC002 — High-review candidate because of garage context
PWC004 — Tier 2 / strongest current PWC public-library candidate under future/reopened planning assumptions
PWC001 — Tier 3 / lower priority under current assumptions
PWC003 — Low public-priority / special-use because public access is limited
```

## Important caution

Recommendation tiers are planning-support outputs. They do not replace utility review, facility review, engineering design, ADA review, Fire Marshal/AHJ review, stormwater review, permitting, or procurement decisions.
