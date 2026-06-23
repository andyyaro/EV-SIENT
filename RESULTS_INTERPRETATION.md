# Results Interpretation Guide

This file explains how to read the current model results in simple language.

Think of the model like a **site selection coach**. It does not make the final decision for the city or county. It helps point out which sites look promising, which sites need caution, and why.

## Simple way to understand the model

The model is asking three big questions:

```text
1. Is there likely demand here?
2. Is this site practical to build on?
3. Are there safety or review concerns?
```

A simple analogy:

```text
Choosing a charging site is like choosing where to open a small coffee stand.
```

You would not only ask, "Is there space for a coffee machine?"

You would also ask:

```text
Are people nearby?
Do they stay long enough to buy coffee?
Is there already too much coffee nearby?
Is the building easy to wire and serve?
Can emergency crews access the area?
Can customers safely reach it?
```

That is what this EV charging model is doing.

## What readiness_score means

`readiness_score` is the overall priority score.

Higher means the site looks better as a public charging candidate.

Simple analogy:

```text
readiness_score is like an overall report-card grade.
```

But it is not a final approval. A high score means "worth considering first," not "approved to build."

## What demand_subscore means

`demand_subscore` estimates how much public charging need may exist around the site.

It looks at things like:

```text
nearby jobs
nearby households
traffic
nearby amenities
local EV share
dwell time
existing chargers nearby
public access
```

Simple analogy:

```text
demand_subscore is like asking, "Will enough people probably use this?"
```

A library, city hall, or government building can score well because people visit, stay for a while, and may have a reason to plug in.

A remote or limited-access site can score low because fewer public users can reach it.

## What feasibility_subscore means

`feasibility_subscore` estimates how practical the site may be to build on.

It looks at things like:

```text
spare electrical capacity
installation cost
service distance
ADA layout possibility
```

Simple analogy:

```text
feasibility_subscore is like asking, "How hard would it be to install the charger here?"
```

A site may have strong demand but still be hard to build if the electrical service is far away or expensive to upgrade.

## What safety_subscore means

`safety_subscore` estimates whether the site has obvious model-level safety or review concerns.

It looks at things like:

```text
fire access
garage/enclosed setting
emergency disconnect visibility
stormwater or firefighting runoff concern
battery storage flag
```

Simple analogy:

```text
safety_subscore is like asking, "Are there red flags before we even start design?"
```

This is not an official safety approval. It is just a planning warning system.

## What recommended_ports_now means

`recommended_ports_now` is the model's starter port recommendation for today.

Simple analogy:

```text
recommended_ports_now is like deciding how many checkout lanes to open at a store.
```

Too few ports can create waiting. Too many ports can sit unused.

The model tries to balance use and wait time.

## Important difference: readiness score vs port count

A common mistake is to think the highest readiness site always needs the most ports.

That is not true.

Simple analogy:

```text
A great coffee-shop location does not always need 20 coffee machines on day one.
```

A site can be a strong priority but still only need 2 starter ports.

In this model:

```text
readiness_score = should we prioritize this site?
recommended_ports_now = how many ports should we start with?
```

These are related, but they are not the same.

## Latest V1 ranking after amenities update

The latest run used manual V1 amenity category counts in `amenities_count_0_5mi`.

Latest ranking:

```text
1. FFX002 — City of Fairfax Regional Library: readiness_score = 60.6
2. PWC004 — Chinn Park Regional Library: readiness_score = 55.9
3. FFX001 — Fairfax City Hall or municipal building: readiness_score = 55.7
4. PWC001 — PWC McCoart Government Center: readiness_score = 53.2
5. PWC002 — Neabsco-Potomac Commuter Garage: readiness_score = 42.0
6. PWC003 — Prince William County Public Safety Training Center: readiness_score = 25.4
```

The amenity update mainly helped Fairfax City Hall and the City of Fairfax Regional Library because Old Town Fairfax has more nearby public-use destinations. It also helped Neabsco because the garage is near mixed-use activity, but the garage still remains high-review because enclosed/garage charging has extra safety and emergency-response considerations.

## Public charging priority sites

These sites currently look like the strongest public charging candidates:

```text
1. City of Fairfax Regional Library
2. Chinn Park Regional Library
3. Fairfax City Hall or municipal building
4. PWC McCoart Government Center
```

These sites rise because they combine some mix of:

```text
public access
nearby households
nearby jobs
reasonable traffic exposure
public-facing site types
nearby amenities
long enough dwell time
```

Simple analogy:

```text
These are like putting a water fountain where people already walk, wait, and gather.
```

## Special or high-review sites

These sites need more careful interpretation:

```text
5. Neabsco-Potomac Commuter Garage
6. Prince William County Public Safety Training Center
```

They are not bad sites. They are just not the same kind of public charging opportunity as a library or city hall.

Simple analogy:

```text
A garage and a public safety training center are like special rooms in a building.
They may be useful, but you do not treat them like the front lobby.
```

## Site-by-site interpretation

## FFX002 — City of Fairfax Regional Library

Current interpretation:

```text
Strongest current public charging candidate.
```

Why it ranks high:

```text
It is a public-facing library.
It has strong nearby jobs and households.
It has strong nearby amenity context in Old Town Fairfax.
Library visits usually create enough dwell time for Level 2 charging.
```

Current result:

```text
readiness_score = 60.6
demand_subscore = 42.5
recommended_ports_now = 2
recommended_ports_2050 = 3
```

Main caution:

```text
Emergency disconnect visibility is not confirmed.
```

That does not mean the site is unsafe. It means the model has not verified that design detail yet.

## PWC004 — Chinn Park Regional Library

Current interpretation:

```text
Strong public charging candidate.
```

Why it ranks high:

```text
It is a public library.
It has strong nearby household context.
It has high nearby traffic exposure.
It has library/recreation amenity context.
It has enough dwell time for Level 2 charging.
```

Current result:

```text
readiness_score = 55.9
demand_subscore = 31.9
recommended_ports_now = 2
recommended_ports_2050 = 2
```

Main caution:

```text
Emergency disconnect visibility is not confirmed.
```

## FFX001 — Fairfax City Hall or municipal building

Current interpretation:

```text
Strong public government/civic site.
```

Why it ranks well:

```text
It is public-facing.
It has very strong nearby job density.
It has strong nearby amenity context in Old Town Fairfax.
It supports civic/municipal use.
```

Current result:

```text
readiness_score = 55.7
demand_subscore = 38.9
recommended_ports_now = 2
recommended_ports_2050 = 2
```

Main caution:

```text
Existing nearby charging supply is already significant.
Emergency disconnect visibility is not confirmed.
```

## PWC001 — PWC McCoart Government Center

Current interpretation:

```text
Strong government-center candidate.
```

Why it ranks well:

```text
It is a major civic/government destination.
It has strong nearby traffic exposure.
It likely has employees and visitors during the day.
It now has some nearby amenity support, but less than the Old Town Fairfax sites.
```

Current result:

```text
readiness_score = 53.2
demand_subscore = 33.4
recommended_ports_now = 2
recommended_ports_2035 = 3
recommended_ports_2050 = 3
```

Main caution:

```text
Employee and visitor counts are still planning assumptions.
Emergency disconnect visibility is not confirmed.
```

## PWC002 — Neabsco-Potomac Commuter Garage

Current interpretation:

```text
Useful site, but high-review and possibly already served nearby.
```

Why it does not rank higher:

```text
It is a garage/enclosed setting.
There is already significant nearby charging supply.
The nearest VDOT segment is a ramp, so traffic interpretation may need review.
Garage EV charging can involve ventilation, fire access, and emergency-response questions.
```

What the amenities update changed:

```text
The garage now gets credit for nearby mixed-use amenities around Stonebridge.
That helps demand, but it does not remove the garage/fire-response review burden.
```

Current result:

```text
readiness_score = 42.0
demand_subscore = 30.0
recommended_ports_now = 2
recommended_ports_2050 = 3
```

Main caution:

```text
Enclosed garage or limited ventilation/access.
Emergency disconnect visibility is not confirmed.
```

## PWC003 — Prince William County Public Safety Training Center

Current interpretation:

```text
Real site, but not a normal public charging priority.
```

Why it ranks low:

```text
It is limited-access.
It is more rural.
Nearby households and jobs are low.
Nearest AADT is low.
No general-public amenity categories are counted in V1.
The model applies a public-access discount.
```

Current result:

```text
readiness_score = 25.4
demand_subscore = 2.1
recommended_ports_now = 2
recommended_ports_2050 = 2
```

Better interpretation:

```text
Special-use candidate.
Potential fleet-support or public-safety-support site.
Not a top public charging site.
```

Main caution:

```text
Limited or non-public access.
Emergency disconnect visibility is not confirmed.
```

## How to explain the current ranking in one paragraph

After the amenities update, the model still suggests that public-facing libraries and government/civic sites are the strongest near-term public EV charging candidates. The City of Fairfax Regional Library remains first, while Fairfax City Hall moves slightly above McCoart because the Old Town Fairfax area has stronger nearby amenity context. Chinn Park Library remains strong because of its library/recreation setting and high nearby traffic. Neabsco-Potomac Commuter Garage gains demand credit from nearby mixed-use amenities, but it remains high-review because garage charging raises ventilation, fire-access, and emergency-response questions. The Prince William County Public Safety Training Center remains a real site but is better interpreted as a special-use or fleet-support candidate because it is limited-access and has low nearby public demand indicators.

## How to read AHJ review flags

`ahj_review_flag = 1` means the model found at least one issue that deserves review.

Simple analogy:

```text
It is like a yellow caution sign, not a stop sign.
```

It does not mean:

```text
the site is impossible
the site is unsafe
the site should be rejected
```

It means:

```text
someone should check this issue before design or installation money is spent.
```

## Why many sites say emergency disconnect visibility not confirmed

This appears often because the model has not verified charger design details yet.

Simple analogy:

```text
It is like saying, "We have not checked where the emergency shutoff switch would go yet."
```

That is normal for an early planning prototype.

## How to use the results responsibly

Use the model to support questions like:

```text
Which sites should we study first?
Which sites need more review?
Which data gaps should we fill next?
Where might we start small instead of overbuilding?
```

Do not use the model to claim:

```text
This site is officially approved.
This exact number of ports must be installed.
This site has passed fire, ADA, utility, or stormwater review.
```

## Best next interpretation improvements

The results will become more reliable after improving:

```text
visitor and employee counts
parking spaces
hours open
amenities nearby with GIS/POI data
equity scoring
electrical capacity
trenching and service upgrade assumptions
fire access and emergency disconnect review
stormwater assumptions
```

## One-sentence summary

The model shows where public EV charging looks promising, where a small starter installation may be enough, and where deeper site review is needed before moving forward.
