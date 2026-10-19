# How Firm Are the Ranks? Score Breakdown and Rank Stability

[Back to the docs index](../README.md)

**What this is:** a planning-support sensitivity check. It shows how much the order of the sites
depends on the weights, which are a judgement, and on inputs that nobody has confirmed yet. It is
**not a probability that a site is actually the best place to build**, and it does not change any
score, rank, tier or port plan.

The code is `src/fcf_m2/stability.py`. The planner app shows it on the Results screen (each site's
"Score Breakdown" and "How Stable Is This Rank"), and `scripts/build_rank_stability.py` writes the
same numbers for the reference study's 12 sites to
`reports/rank-stability/rank_stability_reference_12_sites.json` so the public site can show them.

## 1. Score breakdown

The readiness score is a weighted sum of four subscores, each from 0 to 100:

| Subscore | Weight |
|---|---|
| Demand | 45 points |
| Feasibility | 30 points |
| Safety | 15 points |
| Equity | 10 points |

Each subscore is itself a weighted sum of drivers (households nearby, spare electrical capacity,
fire access and so on; `scoring.DRIVER_WEIGHTS`). So every driver adds

> subscore weight x 100 x driver weight x credit

points, where credit is the driver's value scaled from 0 to 1 against fixed anchors (turned around
for a lower-is-better driver) and 0 for a value nobody recorded. A site not recorded as open to the
public has its demand counted at 65%, so its demand drivers are scaled by 0.65 too.

The breakdown lists each subscore's and each driver's points. The exact points add up to the
unrounded score. For display they are rounded so that the parts add up **exactly** to the
published score: subscores to the nearest 0.1 point, drivers to the nearest 0.01 point (largest
remainder rounding; no part moves by a whole unit, and a driver earning nothing is never shown as
earning something).

## 2. One weight at a time

Each subscore weight is moved up and then down by **5 points**, and the other three are scaled in
proportion so the four still add up to 100. For example, Equity at 15 points leaves 85 points to
share among Demand, Feasibility and Safety in their original 45 : 30 : 15 ratio. For each of the
eight cases the check reports which site comes first and every rank that changes.

It then asks a sharper question: **what is the smallest change to a single weight that changes the
top site?** With the other weights scaled in proportion, each site's score is a straight line in
that one weight, so the answer is where another site's line first crosses the top site's line,
searched over the whole range from 0 to 100 points. A tie exactly at 0 or 100 points is not
counted as a change. The planner app states the result as one plain sentence.

These ranks use unrounded scores. The published ranks use scores rounded to 0.1, so two sites that
round to the same published score are told apart here by the digits the rounding hides.

## 3. Many weightings at once

Nobody can say the weights should be exactly 45, 30, 15 and 10. So the check draws **2000**
alternative weightings from a Dirichlet distribution centred on the defaults (its parameters are
50 x each default weight, a "concentration" of 50). Every draw adds up to 100 points and the draws
average to the defaults; with a concentration of 50, the Demand weight typically lands between
about 34 and 57 points (5th to 95th percentile), and Equity between about 4 and 18.

For each site it reports:

* **Chance of first place:** the share of the 2000 weightings in which it ranks first.
* **Chance of top three:** the share in which it ranks in the top three.
* **Rank range:** the 5th to 95th percentile of its rank across the weightings.

The draws use a fixed seed (**20261018**), so the same results always give the same answer. 2000
draws keep each share within about one percentage point of the value a much larger run would give,
and take a few milliseconds natively and well under a second in the browser, even for 600 sites.

Read "chance" as "share of plausible weightings", not as the chance the site is the right choice.
The concentration is itself a judgement: a lower value spreads the weights wider and the ranks
move more.

## 4. Inputs not yet confirmed

Weights are not the only soft spot. Data confidence scores how well each group of fields is sourced
(`confidence.py`), and a group below 50 of 100 is in the Low band. For each site, a driver counts as
**not yet confirmed** when any field it reads belongs to a group in the Low band there.

The check lets each such driver run from no credit to full credit and reports the **lowest and
highest score** the site could then have, and the **best and worst rank** it could reach while
every other site also moves within its own range. It runs twice:

* **Electrical capacity only.** Spare electrical capacity is a placeholder until a utility or
  facility confirms it, and it carries up to 10.5 points.
* **Every input not yet confirmed.**

This is a range, not a probability: it says what the inputs could do, not what they are likely to
do. It is only done when the run carries a confidence breakdown by field group; without one there
is no honest way to tell which inputs to vary, and the check says so instead of guessing.

## On the reference study (12 sites)

From `reports/rank-stability/rank_stability_reference_12_sites.json`, fixed-anchor scores, data
confidence judged on 2026-10-18:

* FFX004 (53.4) leads FFX002 (51.8) by 1.6 points.
* **Five more points of Equity** puts FFX002 first. **Five fewer points of Demand** leaves FFX004
  first by a tenth of a point (53.1 against 53.0).
* The smallest single change that changes the top site is Equity rising from 10 to about 13.0
  points; then FFX002 moves to first.
* Across 2000 weightings, FFX004 is first in 71%, FFX002 in 19% and PWC002 in 10%. FFX002 is in the
  top three in all of them.
* Electrical capacity is a placeholder at all 12 sites and earns no credit at any of them, which
  is why seven sites share one feasibility subscore (41.92). If capacity alone turned out anywhere
  from none to plenty, 9 of the 12 sites could rank first. With every input not yet confirmed
  allowed to move, any of the 12 could.

What this means for a reader: the top three are close, the weights alone can reorder them, and the
unconfirmed inputs (electrical capacity and the safety review above all) matter more than the
weights do. Confirming capacity is the single step that would firm up the order most.
