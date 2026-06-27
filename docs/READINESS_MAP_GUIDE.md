# Readiness Map Guide

The static generated readiness and decision maps are support visuals for technical review and reproducibility.

The main public-facing visual artifact is now the Tableau workbook documented in:

```text
tableau/README.md
```

Use Tableau for the polished public interactive view. Use the static maps when checking generated outputs, package contents, or GitHub preview assets.

## Static generated map outputs

Current V2 map outputs:

```text
data/outputs/charts/v2_site_readiness_map.png
data/outputs/charts/v2_site_decision_map.png
data/outputs/charts/v2_site_decision_map_readme.png
```

The committed README preview asset is:

```text
docs/assets/charts/v2_site_decision_map_readme.png
```

![V2 GIS decision map preview](assets/charts/v2_site_decision_map_readme.png)

## What the static decision map shows

The V2 decision map summarizes all 12 candidate EV charging sites using visual cues for:

```text
site location
model rank
recommendation tier
review burden / review risk
right-sizing and future-ready planning context
```

The README-optimized version uses all 12 site callout tags so that GitHub readers can identify each candidate without opening Tableau.

## Static map roles

```text
v2_site_readiness_map.png = analytical geography/readiness scatter
v2_site_decision_map.png = presentation-oriented GIS decision graphic combining rank, tier, review risk, and port-sizing
v2_site_decision_map_readme.png = README-optimized GIS decision graphic with all 12 candidate callout tags
```

## Tableau map roles

The Tableau workbook contains interactive map views for candidate locations and review burden. Those Tableau maps are the public-facing map layer.

## Current map interpretation

```text
FFX002 is the strongest current public candidate.
FFX004 is the second-ranked Tier 1 candidate.
PWC006 is the strongest current Prince William County library candidate.
PWC002 is useful but high-review.
PWC003 should remain special-use unless its use case changes.
```

## How to read special cases

```text
PWC002 = high-review garage candidate
PWC004 = library candidate with context and data caveats
PWC003 = public-access or fleet/special-use decision needed
PWC008 = monitor due to nearby supply and combined-stress sensitivity
```

These notes are shown because the map is a planning-support visual. A site can look promising in the model while still needing important real-world confirmation.

## What the static maps do not show

The maps are planning visuals only.

They are not:

```text
parcel boundary maps
engineering layouts
charger placement plans
utility-service maps
permitting decision maps
final site-design maps
```

Any real charger project would still need site-owner review, utility review, engineering design, accessibility review, permitting, procurement, and stakeholder approval.
