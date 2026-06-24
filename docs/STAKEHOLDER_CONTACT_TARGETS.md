# Stakeholder Contact Targets

This document summarizes the public-source contact targets used for the stakeholder outreach phase.

The structured source-of-truth table is:

```text
data/source_extracts/stakeholder_contact_targets.csv
```

Use the CSV for phone numbers, public contact routes, source URLs, contact priority, site IDs, and notes.

## Outreach rule

These are not confirmed project partners. They are likely first contacts or routing contacts identified from public agency pages. Ask each person or office to forward the request if another staff member owns the answer.

## Best first contacts by site

```text
FFX002 — City of Fairfax Regional Library
1. City of Fairfax Regional Library branch manager route — practical operations, public hours, parking observations, likely placement routing.
2. City of Fairfax Public Works director route — public works, utilities coordination, infrastructure and facility routing.
3. City of Fairfax Fire Marshal route — fire access and AHJ/life-safety review after a likely charger area is known.

FFX001 — Fairfax City Hall or municipal building
1. City of Fairfax Public Works director route — municipal facility routing, utilities, parking/site feasibility.
2. City of Fairfax Community Development and Planning director route — planning, development review, zoning, GIS/planning routing.
3. City of Fairfax Fire Marshal route — AHJ/life-safety review after likely placement is known.

PWC002 — Neabsco-Potomac Commuter Garage
1. Prince William County Transportation director route — commuter garage, transportation capital project context, parking/commuting operations.
2. Prince William County Facilities & Fleet Management director route — county facilities, electrical capacity routing, utility services, ADA routing.
3. Prince William County Fire Marshal / Fire and Rescue route — garage fire review, emergency response, code compliance, fire access.

PWC004 — Chinn Park Regional Library
1. Prince William Public Libraries director route — library operations, renovation or reopening timeline, branch use context.
2. Prince William County Facilities & Fleet Management director route — facility condition, electrical/site questions, utility services, ADA routing.
3. Prince William County Sustainability route — EV/sustainability context and cross-agency routing.

PWC003 — Prince William County Public Safety Training Center
1. Prince William County Fire and Rescue route — decide whether this should be public charging, fleet/support, special-use, or removed.
2. Prince William County Facilities & Fleet Management route — county facility/electrical/fleet routing.
3. Prince William County Fire Marshal route — fire-code and training-center safety context.

PWC001 — PWC McCoart Government Center
1. Prince William County Facilities & Fleet Management route — government-center facility, parking/site feasibility, utility services, ADA routing.
2. Prince William County Sustainability route — county EV/sustainability context and interdepartmental routing.
3. Prince William County Information Technology / Geospatial Technology Services route — GIS/source-data questions, County Mapper, data portal, premise-address support.
```

## Source pages used

```text
City of Fairfax Regional Library branch page
City of Fairfax Public Works page
City of Fairfax Community Development and Planning page
City of Fairfax Fire Department page
Prince William County Sustainability Office page
Prince William County Facilities & Fleet Management page
Prince William County Transportation page
Prince William Public Libraries page
Prince William County Fire and Rescue page
Prince William County Information Technology page
```

## Next step after contact identification

The next status change should be from `Contact identified` to `Request sent` in:

```text
data/source_extracts/stakeholder_response_tracker.csv
```

Only change model values after a response has a source, date, confidence level, and clear model-update decision.
