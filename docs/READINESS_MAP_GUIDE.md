# Readiness Map Guide

The generated readiness map is:

```text
data/outputs/charts/site_readiness_map.png
```

## What the map shows

The map plots the six candidate EV charging sites by longitude and latitude.

Each marker represents one candidate site. Marker size and color are tied to the site's readiness score. Each label shows the site ID, rank, and score.

The top-ranked site is highlighted with a star marker.

## Current map interpretation

When the full pipeline is run, the map uses the model results, sensitivity summary, and scoring profile results to add a short interpretation note.

For the current V1 run, the expected note is:

```text
FFX002 is the stable top candidate: #1 in the base model, stable in sensitivity, and #1 across 5 scoring profiles.
```

This supports the main project finding that FFX002 is not only the top site under the base model, but also remains strong when uncertainty and stakeholder-priority profiles are tested.

## What the map does not show

The map is a planning visual only.

It is not:

```text
a parcel boundary map
an engineering layout
a charger placement plan
a utility-service map
a permitting decision map
a final site-design map
```

Any real charger project would still need site-owner review, utility review, engineering design, ADA/accessibility review, Fire Marshal/AHJ review, stormwater review, permitting, procurement, and stakeholder approval.
