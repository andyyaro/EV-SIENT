# DECISIONS.md — every judgment call, its alternatives, and its reasoning

For the four teammates who did not watch this work happen. Each entry says what was decided,
what was rejected, and **why** — because the reasoning is the part that lets someone
reverse a decision later on purpose rather than by accident.

Decisions are appended, never rewritten. If one is superseded, the new entry says so and the
old one stays.

---

## DEC-000 — Phase 6B: build a data intake layer so the model is portable

**Date:** 2026-07-27 · **Raised by:** the project owner, mid-program · **Status:** logged, not
yet started · **Phase:** 6B (inserted between Tableau and the platform)

### The decision

Build a data intake layer that lets another jurisdiction bring its own data and get a run.
Logged here in full **before any implementation began**, at the owner's explicit instruction.

### Why it was raised

> *"The model currently assumes our datasets, our column names, our units, our CRS, our site
> IDs, already cleaned. That makes it a Northern Virginia study, not a product."*

That is an accurate description of the current state. `src/fcf_m2/config.py` and the input
readers assume the project's own column names throughout, and nothing in the codebase
negotiates with a file it did not produce.

### Why it sits between Phase 6 and Phase 7

**Because the platform must expose it.** Intake is not a back-office import script; the
requirement names it a first-class surface — load data, see the proposed mapping, see what
failed validation and why, see the resulting confidence *before* committing to a run.
Building the platform first and retrofitting intake would produce exactly the hidden import
step the requirement rules out.

### The constraint that shapes everything else

> **Cleaning must never silently improve data quality.**

Every imputation, inferred mapping, unit conversion, dropped row and default substitution is
recorded with its reason and surfaced in provenance. **If a transformation cannot be
explained to the user in one sentence, it does not ship.**

This is the same principle the project already applies elsewhere, extended to a wider
surface. `capacityGuard` refuses to emit a feasibility claim from placeholder capacity;
`observed.py` refuses an unattributed record and names a missing trigger metric rather than
defaulting it. A cleaner that quietly fixes a file is the same failure mode as a model that
quietly assumes a capacity — the number looks better and means less.

### Alternatives rejected

| Alternative | Why it loses |
|---|---|
| **A second, standalone intake pipeline** | Explicitly ruled out by the requirement, and rightly: two ingestion paths diverge, and the V4 machinery in `observed.py` already encodes the refusals this needs. Extending it keeps one set of rules. |
| **Best-effort silent cleaning** — infer, convert, impute, run | The failure this project exists to avoid. A run that succeeds on data nobody inspected produces numbers nobody can defend. |
| **Reject anything that does not match the schema exactly** | Honest but useless. A jurisdiction with 80% of the fields should get a run and a *lower confidence rating*, not a refusal. |
| **A hand-written mapping config as the primary path** | Ruled out by the amendment. It is the automation fallback; the visual mapping step is the primary one, because a config file hides exactly the decisions the user most needs to see. |
| **A paid ETL tool** (Alteryx, or a Tableau/MATLAB-dependent step) | Ruled out by the amendment. Anything needed to get data into the model is Python in this package, testable under pytest, runnable in CI, and free. |

### What it extends rather than replaces

- **`src/fcf_m2/observed.py`** — the V4 ingestion machinery. It already refuses unattributed
  records and names missing metrics instead of defaulting them.
- **`src/fcf_m2/confidence.py`** — the existing typed data-confidence system, rubric
  `High ≥ 75`, `Medium ≥ 50`, else `Low`, derived **only** from typed provenance fields.
  Requirement 6B.4 routes completeness into this rather than inventing a parallel score.

### Gate

A deliberately messy third-party-shaped fixture — wrong column names, mixed units, missing
fields, different CRS — runs end to end and produces a **correctly-degraded** confidence
rating, with **every transformation traceable**.

### Open question noted at logging time

CRS reprojection done properly generally means `pyproj`. It is free and open-source, so it
satisfies the amendment, but it is a **new runtime dependency** and gets its own decision
entry when reached. A hand-rolled reprojection would be a transformation that cannot be
explained in one sentence, which the hard constraint forbids.

---

## DEC-001 — Keep `LEDGER.md` inside the repository

**Date:** 2026-07-27 · **Phase:** 0

Create the program ledger at `docs/operations/v4-program/LEDGER.md`, tracked and committed
often.

**Rejected:** an untracked scratch file, and a file in the workspace parent. Both fail the
same test — neither survives a clean clone, and the program's own recovery procedure depends
on the ledger being recoverable from git alone.

---

## DEC-002 — Fetch CesiumJS on demand rather than committing it

**Date:** 2026-07-27 · **Phase:** 3

`scripts/vendor_cesium.sh` fetches CesiumJS into a gitignored directory. The viewer probes
for the vendored copy and falls back to the pinned CDN, so a clean checkout works online and
a vendored checkout works with no network at all.

**Rejected:**

- *Commit `Build/Cesium`* — 20 MB across 375 files added to every clone, to carry a pinned
  third-party redistributable that is reproducible on demand and re-bundled at
  desktop-packaging time anyway.
- *CDN only* — the viewer must work offline.
- *Commit a minified subset* — a hand-pruned Cesium is neither upstream nor reproducible,
  and would diverge silently from the CDN build.

The fetch script **refuses to run** if the version it would fetch disagrees with the pin in
`index.html`, because a vendored copy that differs from the online one makes the viewer
behave differently offline and online — the worst of both.

---

## DEC-003 — Lock NFC tags at deployment, not at writing

**Date:** 2026-07-27 · **Phase:** 5 · **Prompted by:** the owner asking whether locking was
required at all

Tags going into public space are locked. Bench tags — demos, rehearsals, pipeline
verification — stay unlocked.

**Reasoning:** locking defends against exactly one threat, a stranger rewriting a tag that
carries the project's implicit endorsement. That threat exists only once a tag is somewhere
a stranger can reach it. A tag on a desk is not exposed to it, and locking one throws away
the ability to re-point it when a URL changes — which matters, because the capture-form
route did not exist when the first tag was written. With 50 coins and 12 sites, spares are
free.

The runbook originally said to lock every tag. That was wrong, and the question that surfaced
it was a good one.

---

## DEC-004 — Lock rather than password-protect

**Date:** 2026-07-27 · **Phase:** 5

NTAG215 supports a 32-bit password (PWD/PACK). We lock instead.

A password shared across a team and printed in a runbook protects against nobody with
physical access, which is the only attacker that matters for a coin in a car park. Locking
achieves the actual goal — permanent read-only — with no secret to leak, rotate, or forget.
The cost is that a locked tag can never be corrected, which is why verification precedes
locking as a hard sequence rather than as advice.

---

## DEC-005 — Do not use the tag UID as an identifier

**Date:** 2026-07-27 · **Phase:** 5

Every NTAG215 carries a unique read-only 7-byte UID. It is recorded in the verification log
for **inventory** — knowing which physical coin is where — and is never consulted by any code
path.

A UID is trivially cloneable, so it authenticates nothing. Treating it as identity invites
exactly the "the tag said so" reasoning this design avoids.

---

## DEC-006 — The capture form submits nowhere

**Date:** 2026-07-27 · **Phase:** 5

The field capture form assembles a CSV row in the browser and offers it for download or
email. There is no backend.

**Reasoning:** a form that posts into the model from a tag anyone can tap is an open door to
polluting the data the whole study rests on. There is no endpoint to abuse because there is
no endpoint. It also matches the existing rule that received values enter the inputs and the
model **re-runs** — never an edit in place — since a row that arrives by email is reviewed by
a human before ingestion. Secondary benefits: no recurring cost, and no store to breach.

**Rejected:** a Lambda + API Gateway endpoint. It would cost money, need authentication to be
safe, and create both an abuse surface and a data store — all to remove one email.

---

## DEC-007 — Use the existing site and distribution for NFC routes

**Date:** 2026-07-27 · **Phase:** 5 / 8

NFC landing pages and capture forms are served from the existing
`futurecityfellowship.andyyaro.com` CloudFront distribution and certificate.

**Reasoning:** the program's hard cost ceiling is $10/month aggregate. Riding infrastructure
that already exists makes the incremental cost effectively zero — 75 KB of storage, no new
distribution, no new certificate, no new DNS record.

**Rejected:** a dedicated short domain. It would read slightly better on a printed card and
would cost a registration, a certificate and a distribution, for a project whose entire
current run rate is about $0.40/month.

---

## DEC-008 — Contract v2 is derived from v1 by migration, not produced independently

**Date:** 2026-07-27 · **Phase:** 4

`data/contract/v2/` is built by reading the frozen `data/contract/v1/` and widening it.
`scripts/build_contract_v2.py` and `fcf_m2.workflow` both call the one migration function in
`src/fcf_m2/contract_v2.py`; neither reimplements it.

**Reasoning:** "v2 is additive over v1" is the entire promise of the version, and derivation
makes it true *by construction* rather than by discipline. Migration copies every v1 value
across, so a v2 number drifting from its v1 counterpart is not something the code is able to
express. The tests assert it anyway, because a guarantee nobody checks is a comment.

It is also the same rule the owner set for Phase 6B — *do not build a second, parallel intake
path* — applied one phase earlier. Two producers for two versions of the same contract is
exactly how the horizon vocabulary ended up meaning three different things across Python,
Excel and MATLAB before the V3 restructure.

**Rejected:**

| Alternative | Why it loses |
|---|---|
| **Emit v2 directly from `workflow.run`, independently of v1** | Two producers, two chances to diverge, and no mechanical proof of additivity — only a test that would have to enumerate all 48 fields correctly forever. |
| **Regenerate v1 and v2 together from the model each run** | Requires regenerating v1, which is now immutable. The reason to freeze v1 is that published artifacts quote it. |
| **A `version=` parameter on `contract.write_contract`** | One function branching on version reads tidier and is worse: v1's writer is frozen code that should not be edited to add a case for something that came after it. |

**Consequence accepted, and stated:** if the model itself changes, v2 does not update from
the model — it updates from whatever v1 it was derived from, and v1 is frozen. That is
correct for a container change and wrong for a model change. When the V4 model genuinely
produces different numbers, those go into a **new run** with its own contract directory and
its own `model_version`, not into this v2. The v2 manifest records the SHA-256 of the exact
v1 it came from, so "which v1?" stays answerable.

---

## DEC-009 — `horizon_label`'s `now` becomes `baseline` in v2, and stays `now` in v1 forever

**Date:** 2026-07-27 · **Phase:** 4 · **Closes:** FIND-NUM-04

**Reasoning:** `now` is time-relative text frozen into a dated artifact. Read in 2036, a row
labelled `now` is simply false — and "now" is the one horizon word this program prohibits
everywhere else, which made the contract the last place it survived.

It could not be fixed in v1 because v1 is immutable, and that is not an obstacle to route
around: an immutable contract plus an additive successor is *precisely* the mechanism for a
correction that arrives after publication.

**The cost, stated plainly rather than buried:** this is the one change in v2 that can break
a consumer, and it breaks quietly. A filter on `horizon_label == "now"` matches nothing in
v2, drops the baseline row, and raises no error — an empty result or a chart missing its
first column. `docs/migration-from-v3.md` leads with it and recommends filtering on
`horizon_year == 2026` instead, which did not change and never will.

**Rejected:**

| Alternative | Why it loses |
|---|---|
| **Leave `now` in v2 as well** | Carries a known-decaying label into the version that is supposed to be the good one, forever. |
| **Carry both `horizon_label` and `horizon_label_v1`** | A permanent duplicate column to spare consumers a one-line change, and two fields that must never disagree. |
| **Fix it in v1 and re-cut the hash chain** | Breaks the freeze, invalidates the pinned digest, and silently changes an artifact that published figures already quote. |

---

## DEC-010 — `model_version` stays `3.0.0` in contract v2

**Date:** 2026-07-27 · **Phase:** 4 · **Supersedes:** the first written v2 manifest, which
claimed `4.0.0` — caught during review and corrected before it left the branch.

The v2 manifest reports `model_version: 3.0.0`.

**Reasoning:** the contract version and the model version are different facts. v2 is a
*container* change — it adds fields for observations that do not exist yet. The numbers
inside it were produced by the V3 model, on rows that say `model_mode = milestone2_v3`.
Migrating them into a wider container did not re-run anything.

Stamping `4.0.0` on them would be a version claiming work that has not happened, which is the
same defect as a placeholder capacity presented as verified — one layer up, and harder to
notice, because nobody audits a version string.

`MODEL_VERSION_V4 = "4.0.0"` exists in `config.py` and is deliberately unused by any emitted
artifact. `test_v2_does_not_claim_model_version_4` fails if that changes.

**Rejected:** *bump to 4.0.0 because the work is called Phase 4.* The phase number is a plan;
the model version is a claim about output.

---

## DEC-011 — Missing data currently makes a site look better; one fix now, two deferred to 6B

**Date:** 2026-07-27 · **Phase:** 4 → 6B · **Found by:** the Phase 6B research fleet
(`wf_d029c874-d32`), **confirmed by execution before being acted on**, per the subagent
doctrine that every finding is a lead until reproduced against the actual files.

### The finding

Three places where absent or malformed input scores **better** than measured input — the
exact inverse of the principle the rest of this project enforces.

| # | Where | Behaviour | Live today? |
|---|---|---|---|
| 1 | `right_sizing.site_capacity_cap` | `parking_spaces <= 0` → cap **6**. A real 40-space lot → cap **2**. Absence allows **3× the ports** of measurement. | No |
| 2 | `scoring.INVERTED_DRIVERS` | `garage_enclosed`, `stormwater_risk` use `(1 - x)`; absent → `0.0` → term `1.0`, the **maximum**. A site with no stormwater assessment scores as though one was done and found no risk. | No |
| 3 | `scoring.yesno_to_num` | Returned `float(value)` for **any** number, unclamped. `7` on `fire_access_ok` contributed 7× its rubric weight. And `0.5` → `0.5` while `"0.5"` → `0.0`, so whether a CSV cell parsed as text or number changed the score. | No |

**None changes a published number.** All 12 real sites carry strictly `0`/`1` in every flag
and a positive `parking_spaces`, verified and pinned by a test. Every path is dormant on the
current inputs — and goes live the moment Phase 6B accepts a file nobody here prepared, which
is precisely what 6B is for.

### Decided: fix #3 now

It has no design ambiguity. A flag outside `{0, 1}` is invalid input, and the function's own
string branch has always been strictly binary — the numeric branch simply disagreed with it.
`yesno_to_num` now **refuses**, naming the field and the value.

**Refuses rather than clamps.** Clamping `7` to `1` would be a cleaner that silently improves
data — the thing this project exists not to do — and it would bury whatever produced a `7`.

### Deferred: #1 and #2 go to Phase 6B, pinned by tests meanwhile

Both need a decision with a **visible consequence for real users**, and neither has a
correct-by-inspection answer:

- **#1:** the conservative neutral (cap 2 on absence) lowers port targets for any
  jurisdiction that omits the column. That is a real cost imposed on a real user for a
  missing field.
- **#2:** the pessimistic neutral (`1`) asserts the *opposite* unverified claim — "this site
  **is** enclosed", "this site **does** have stormwater risk" — manufactured from the same
  absence. For `garage_enclosed` it also changes a user-visible review tier, which carries no
  ledger entry explaining why.

The honest alternative both share is to keep the permissive neutral and record the absence as
**coverage loss** feeding the existing confidence rubric — the model still runs, it just says
less, which is requirement 6B.4 in the owner's own words. That is the likely answer, and it
is a 6B decision because it only works once the completeness-to-confidence path exists.

`tests/test_absence_is_not_favourable.py` pins both as **known defects**. A test asserting a
defect is not an endorsement of it; it is how the defect stays visible until it is resolved.
Each carries an instruction: when it starts failing, that *is* the fix — update this entry and
delete the test rather than adjusting it.

**Rejected:** *fix all three now.* #1 and #2 would move scores for absent data under a design
nobody has chosen yet, and picking one silently is the same failure as the defect itself.

**Rejected:** *record them and write no test.* Three of this program's defects were found in
code that had been read and reasoned about but not exercised. An unpinned known defect is a
defect that gets rediscovered.
