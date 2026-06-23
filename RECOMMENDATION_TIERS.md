# Recommendation Tiers

## Purpose

The model now translates scores and review flags into plain-English planning recommendations.

This helps the prototype move from only ranking sites to explaining what a planner should do next.

## New output columns

The normal `site_results.csv` output now includes:

```text
model_rank
recommendation_tier
planning_recommendation
priority_reason
data_needed_next
```

## Tier logic

### Tier 1 — advance to site screening

Used when a site is publicly accessible, not an enclosed-garage candidate, ranks near the top, and has a readiness score of at least 50.

Meaning:

```text
Strong current candidate. Advance to site screening and stakeholder confirmation before design or procurement.
```

### Tier 2 — promising candidate, refine data

Used when a public site has moderate readiness, usually readiness score 45 or higher, but is not a top Tier 1 candidate.

Meaning:

```text
Promising candidate. Improve demand, parking, operating-hours, and electrical assumptions before advancement.
```

### High-review candidate

Used when a site has a major model-level review trigger, especially enclosed or garage context.

Meaning:

```text
Keep in the planning discussion, but require garage, fire/AHJ, access, and electrical review before advancement.
```

### Low public-priority / special-use

Used when a site is limited-access or not a normal public-charging location.

Meaning:

```text
Do not advance as a general-public charging site until the public-access or fleet-only use case is confirmed.
```

### Tier 3 — lower priority / monitor

Used when a public candidate remains below stronger alternatives in the current model.

Meaning:

```text
Monitor as a lower-priority candidate and revisit after stronger data is available.
```

## Why recommendations are separate from scores

A high score does not automatically mean a site is ready to build.

A site can have demand and equity value while still needing major review. For example, a garage can be useful from a public-access or commuter perspective, but still require more fire, access, conduit-routing, ventilation, and electrical review.

The recommendation layer keeps that distinction clear.

## Current expected interpretation

Based on the latest V1 model:

```text
FFX002 — Tier 1 / stable top candidate
FFX001 — Tier 1 / stable second candidate
PWC004 — Tier 2 / strongest current PWC public-library candidate
PWC002 — High-review candidate because of garage context
PWC001 — Tier 3 / lower priority under current assumptions
PWC003 — Low public-priority / special-use because public access is limited
```

## Important caution

These tiers are planning-support outputs. They do not replace:

```text
utility review
facility review
engineering design
ADA review
Fire Marshal or AHJ review
stormwater review
permitting
procurement decisions
```

The recommendation layer should be updated when stronger site, electrical, demand, or stakeholder data becomes available.
