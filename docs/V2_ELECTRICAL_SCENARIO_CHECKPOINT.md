# V2 Electrical Scenario Checkpoint

## Status

The V2 electrical-feasibility scenario module was added to the workflow and successfully ran as part of `python src/run_v2.py`.

The V2 output checker passed after the new electrical outputs were added.

## Expected electrical case ranking

```text
Rank 1  FFX002 — City of Fairfax Regional Library — base 58.8 — adjusted 55.8 — medium risk
Rank 2  FFX004 — Fairfax County Government Center — base 54.4 — adjusted 51.4 — medium risk
Rank 3  PWC006 — Bull Run Library — base 52.1 — adjusted 49.1 — medium risk
Rank 4  FFX001 — Fairfax City Hall or municipal building — base 51.0 — adjusted 48.0 — medium risk
Rank 5  PWC007 — Central Library — base 50.2 — adjusted 47.2 — medium risk
Rank 6  PWC004 — Chinn Park Regional Library — base 48.6 — adjusted 45.6 — medium risk
Rank 7  PWC002 — Neabsco-Potomac Commuter Garage — base 50.3 — adjusted 44.3 — high risk
Rank 8  FFX003 — Pohick Regional Library — base 46.8 — adjusted 43.8 — medium risk
Rank 9  PWC008 — Potomac Library — base 40.1 — adjusted 37.1 — medium risk
Rank 10 PWC005 — Haymarket Gainesville Library — base 36.9 — adjusted 33.9 — medium risk
Rank 11 PWC001 — PWC McCoart Government Center — base 39.8 — adjusted 33.8 — high risk
Rank 12 PWC003 — Prince William County Public Safety Training Center — base 29.6 — adjusted 23.6 — high risk
```

## Interpretation

The main V2 conclusion remains stable after adding electrical uncertainty.

Bull Run Library remains the strongest Prince William County Batch 002 candidate and stays rank 3 under the expected electrical case.

Central Library improves relative to Neabsco-Potomac Garage under the electrical screen because the garage candidate is classified as high electrical risk, while Central Library is medium risk.

Neabsco-Potomac Garage remains useful for planning discussion, but the electrical scenario confirms that its garage/enclosed context and review complexity should prevent it from being treated as a simple near-term site.

McCoart and the Public Safety Training Center are also high-risk under the electrical screen, mostly because of unconfirmed electrical inputs and/or special-use context.

## What this does and does not mean

This is not a confirmed electrical engineering result. It is a planning screen.

The output should be read as:

```text
This site needs earlier electrical review before advancement.
```

not as:

```text
This site cannot work electrically.
```

## Remaining work

The next improvements should focus on either:

```text
1. making a short technical README explaining the full V2 workflow; or
2. adding the next candidate batch, likely transit or municipal parking sites.
```

Actual electrical confirmation would require facilities, utility, AHJ, or Fire Marshal input, but the model now has a defensible way to handle uncertainty before outreach.
