# What this can and can't tell you

A study is only useful if you know where its edge is. This page is that edge, in plain English.

Nothing here is softer than the technical statement of the same fact. Every sentence traces to
the canonical limitations list in
[`limitations_update.md`](operations/website-patch-package/content/limitations_update.md) and to
the caveat texts in `src/fcf_m2/provenance.py`, which are the single definition each surface
reads from. Terms in **bold** are in the [glossary](GLOSSARY.md).

---

## If you read nothing else

**Nobody has confirmed that any of these twelve sites has the electrical capacity to support
chargers.** Not one. The figure the model uses for capacity is a **placeholder** - a number it
needs in order to run, that nobody has checked - at all twelve sites, on all 120 rows of the
data contract.

So this project cannot tell you whether a site *can* have chargers. It was built to compare
sites and to argue for a staging strategy, and it does that with its limits labelled rather
than hidden.

That is also why the software **refuses** to state a feasibility claim rather than quietly
omitting one. If you go looking for "is this site feasible?" and find nothing, that absence is
the answer, and it is deliberate.

---

## What it can tell you

**How twelve specific sites compare to each other**, on modelled demand and screening-class
cost. In the current `milestone2_v3` mode the scoring uses **fixed anchors** rather than ranking
sites against each other, so a site's score doesn't move when another site is added or removed.
The older `legacy_v2` mode scores each site relative to the rest of the group, and its scores
*do* move - which is one reason the two are never treated as interchangeable.

**Roughly how much overbuilding costs.** This is the project's actual argument: a real
installation put in 70 ports and later took 17 of them offline. Comparing a right-sized
build against an overbuilt one is what the model is genuinely for.

**Where the pathway argument is strongest.** Conduit and trenching are cheap while the ground
is already open and expensive afterwards. The model shows which sites gain most from building
**pathway capacity** now and energising later.

**Exactly how much is not known, and where.** Every site carries a **data confidence** score
built only from typed provenance fields - never from how convincing the answer looks. All
twelve currently score 33.8, which is Low. None reaches even Medium.

**Where every number came from.** Every figure on the platform resolves to the run that
produced it, the contract version it came from, and its source. Anything that can't be
explained isn't displayed.

---

## What it cannot tell you

**Whether a site is electrically feasible.** Capacity is a placeholder at all twelve sites, so
no feasibility claim is permitted from it. Every electrical field - service rating, spare
capacity, disconnect visibility - is unconfirmed everywhere.

One field is easy to misread here. `base_load_kw` is the only populated electrical field in the
whole contract, which makes it the one most likely to be taken for a measurement. **No building
was metered.** It is a hand-adapted planning proxy carried over from an older adapter, and it
is labelled as one everywhere it appears.

**What anything will actually cost.** Costs are screening-class benchmarks for comparing
options. Not budgets. Not quotes. Not bids. Not engineering estimates.

**How many people will actually charge.** Demand is modelled and uncalibrated - no charging has
been observed at any of these sites. The growth multipliers are provisional conventions, not
forecasts.

**How long anyone will wait.** Waits are simulated from modelled demand and have never been
observed. Two different wait figures exist and they are easy to confuse:

- The **queueing estimates** carried in the data contract cover a very wide range. At FFX002
  they are effectively nil - 0.00 on most rows, and never above 1.31 minutes on any of them,
  including the 2026 starter build where they are 0.80 (average) and 1.31 (peak). Elsewhere
  they climb steeply, and the two maxima are at **different sites**: the average wait reaches
  about 69 minutes (PWC008, 2056) and the peak about 215 (PWC002, 2046). The peak column is
  also **blank on five rows** - all PWC002, at 2046 and 2056 - where the modelled queue never clears and no finite
  wait exists. A blank there means *unbounded*, not *unknown*, and it is the model's real worst
  case.
- A separate **discrete-event simulation** of the 2026 starter build reports median and
  90th-percentile waits of 0.0 at all twelve sites, at 6–20% utilisation.

Neither is a measurement. The 2026 zero is often quoted on its own; it describes the starter
build only and does not carry to later horizons.

**Whether anyone has approved any of this.** No client endorsement, no acceptance from the
[Authority Having Jurisdiction](GLOSSARY.md#ahj--authority-having-jurisdiction) (AHJ), no
utility confirmation, and no funding award exists or is implied anywhere. The expansion-trigger
policy is proposed configuration, not adopted municipal policy.

**Whether the site stays powered in an outage.** No resilience claim is made anywhere. The plan
includes no battery storage.

**Whether an expansion trigger has been met.** Triggers are defined, but no site has been
observed in operation, so **no trigger has ever been evaluated against real data.**

---

## Two things that look like results and aren't

**The MATLAB and Simulink views.** The MATLAB suite has genuinely been executed - 49 tests
passed on licensed MathWorks R2025b - but **only against a synthetic fixture, never against
these twelve sites**. No *MATLAB* output describes a real facility, and the managed-charging
numerics have never met real capacity, because no real capacity exists to meet.
The Simulink model has never been simulated at all, which the view states on its face.

**One scoring weight does nothing.** 35% of the feasibility sub-score is weighted on spare
capacity, which is `0` at all twelve sites - so that 35% currently contributes nothing to any
score. This is disclosed rather than corrected: changing it would move every published readiness
score and break the frozen baseline the project is committed to reproducing. The moment real
capacity data arrives, that weight starts working.

---

## What would change these answers

One thing, mostly: **someone confirming the electrical capacity at these sites** - the utility
or the facility manager. That single input moves capacity off `placeholder`, releases the
feasibility guard, activates the 35% weight described above, and lifts data confidence off the
floor.

Everything else here is downstream of that.

The system is built to accept it. There is a documented path for a jurisdiction to bring its own
data file, and the field layer exists so corrections can come from people standing in the
parking lot. Until then, this is a screening study that knows it is one.
