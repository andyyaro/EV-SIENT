# Glossary

Every term this project uses that isn't everyday English, with one honest sentence each.

Where a term carries a limitation, the limitation is part of the definition — not a footnote.
That's deliberate: a glossary that defines "readiness score" without saying what it can't tell
you has made the term sound more solid than it is.

---

### AHJ — Authority Having Jurisdiction

The local official who actually decides whether something is permitted to be built — usually the
building official, electrical inspector, or fire marshal. Nothing in this project substitutes
for their decision.

### Capacity basis

A label on every electrical capacity figure saying **where that figure came from**, ranging from
`verified_utility` (the utility confirmed it) down to `placeholder` (nobody has checked). It is
currently `placeholder` at **all twelve sites**, which is the single most important fact about
this study.

### Data confidence

A score from 0 to 100 for how well-sourced each site's data is, derived only from typed
provenance fields — never from how good the answer looks. **All 12 sites currently score 33.8,
which is Low** — not one reaches even Medium.

### eGRID factor

The US EPA's published figure for how much carbon dioxide equivalent is emitted per unit of
electricity in a given region. This project uses **596.3 lb CO2e/MWh** (eGRID2023 Rev 2, SRVC
region, accessed 2026-07-19); it is revised annually, so emissions results must be recomputed
when it changes.

### Expansion trigger

A predefined condition — on observed utilisation, wait time, reliability and equity — proposed
as the gate that should be met before more chargers are energised. It is **proposed
configuration, not adopted municipal policy**, and because no site has been observed in
operation, **no trigger has ever been evaluated against real data.**

### Fail-closed capacity guard

Code that refuses to produce a feasibility claim unless the capacity basis is verified. It is
why this project will not tell you a site "can" support chargers: with capacity at `placeholder`
everywhere, the guard blocks that claim by design rather than by omission.

### Fixed-anchor scoring

Scoring each site against fixed reference values rather than against the other eleven, so a
site's score doesn't move when a different site is added or removed. Scores are comparable
across runs; they are not a ranking of all possible sites.

### Lifecycle cost / Net present cost

The total modelled cost of a site over the study period, discounted to today's money. These are
**screening-class estimates for comparing sites** — not budgets, not quotes, and not engineering
cost estimates.

### MCDA — Multi-Criteria Decision Analysis

A method for comparing options across several factors at once when no single number captures
them all. It produces a defensible comparison, not an objectively correct answer: change the
weights and the order can change.

### Pathway capacity

How many charging ports a site could grow to **if** the civil and electrical groundwork is built
for it now — conduit, trenching, service headroom. Building the pathway is cheap during initial
construction and expensive afterwards, which is the whole argument for staging.

### Placeholder

A value the model needs in order to run that **nobody has confirmed**. It is not an estimate and
not a measurement. Every placeholder is labelled as one everywhere it appears.

### Provenance

The record of where a number came from — which run produced it, from which contract version,
backed by which source, at what confidence. Every number on the platform is clickable, and
anything that cannot be explained is not shown.

### Readiness score

A comparative score for how ready a site appears for public charging, given what is known about
it. It compares sites **on modelled demand and screening-class cost**; it is not a statement
that any site is electrically feasible, and cannot be, because capacity is unverified
everywhere.

### Right-sizing

Choosing how many charging ports to install now, rather than as many as will fit. The direct
answer to installing 70 ports and later taking 17 of them offline.

### Screening-class

A level of precision suitable for **deciding what to study next**, not for deciding what to
build. Every cost, demand and emissions figure here is screening-class.

### Staged, evidence-gated deployment

Install a small number of ports now, build the pathway for more, and energise the rest only when
observed data clears the expansion triggers. The strategy this whole project exists to support.

### Starter ports

The number of charging ports recommended for immediate installation at a site. Across the
portfolio it is deliberately smaller than the pathway capacity — 25 now against a pathway for 48
— though at three of the twelve sites (PWC003, PWC005, PWC008) the two are equal at 2 ports, so
"starter" and "pathway" are not always different numbers.

---

## Terms from the software, if you're reading the code

### Contract (data contract)

The frozen set of tables every surface reads from, with a SHA-256 hash chain so a number on a
chart can be traced to the exact bytes it came from. `v1` is frozen; `v2` adds fields without
changing any `v1` value.

### Desktop tier / web tier

The same interface in two places. The **web tier** shows what the model produced. The **desktop
tier** can also *run* it. Capabilities the web tier lacks are shown greyed out with the reason,
never hidden.

### Legacy v2 / Milestone 2 v3

Two modes of the same model. `legacy_v2` reproduces an earlier accepted baseline bit-for-bit
(25 starter ports, 48 pathway); `milestone2_v3` is the current canonical model.

### Synthetic inputs

Invented site data shipped with the public installer so the model can run without distributing
real facility information. Every value is fabricated and labelled as such, and a run against it
declares `synthetic_inputs: true` in its own contract manifest.
