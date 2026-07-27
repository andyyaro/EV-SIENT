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

---

## DEC-012 — Charger efficiency: MATLAB follows Python, and the reconciliation that found it

**Date:** 2026-07-27 · **Phase:** 4 (task 4.8) · **Closes:** FIND-XMODEL-01

### The finding

`src/fcf_m2/config.py` has always declared `CHARGER_EFFICIENCY = 0.92`. Three MATLAB
functions — `makeSessionProfiles`, `electricalEconomics`, `runScenario` — defaulted
`ChargerEfficiency` to **0.93**. One physical assumption, two values, one model. Every MATLAB
energy figure came out `1/0.93` of the contract's rather than `1/0.92`: about **1.1 % high**.

### How it was found, because the method is the transferable part

Phase 4's task 4.8 is "MATLAB reconciliation against real MATLAB outputs". The reconciliation
was done rather than assumed: the pipeline was run on the **canonical** data and compared
against the contract field by field.

Identity reconciled perfectly — 120/120 on `scenario_id`, `site_id`, `horizon_year` and
`capacity_basis`. Energy did not. The gap was then **measured instead of explained away**: the
implied efficiency came out **0.9300** across all 120 rows (min 0.929141, max 0.930425, the
spread being the contract's two-decimal rounding). That is not a semantic difference between
delivered and grid energy. It is a disagreement about a constant.

### Why it survived this long

**Charger efficiency is not a contract field.** The canonical contract is precisely the
mechanism that prevents this class of drift — one number, one place, consumers quote and never
re-derive — and this quantity lived outside it. There was nothing to reconcile it against.
The drift was hiding in the one place the anti-drift mechanism does not reach.

### Decided

Python is the single producer (`data/contract/v1/README.md`), so **MATLAB follows it**: 0.93 →
0.92 in all three files. **No published number moves** — MATLAB output has never been
published, and Python's 0.92, from which every published emissions figure derives, is
unchanged.

`tests/test_cross_model_constants.py` parses the MATLAB sources for every numeric
`addParameter` default and compares the shared ones against `config.py`. `verify.sh` 17 → 18.
Mutation-tested: reverting any single file to 0.93 fails it.

**Three files, not one.** Two were found by grep; the third only by re-running the sweep after
fixing the first two. Finding one and stopping would have left two — and the two left would
have been the ones nobody looked at again.

### Rejected

| Alternative | Why it loses |
|---|---|
| **Change Python to 0.93** | Python is the single producer and every published emissions figure derives from its value. Moving it to match a downstream consumer inverts the contract's direction of authority and would change published numbers to fix a consumer's default. |
| **Add `charger_efficiency` to the contract so MATLAB reads it** | Better, and still the right destination — but contract v1 is frozen, so it belongs in v2 and then in the adapter CSV. Aligning the constants is the correct step now; carrying it in the contract is the durable fix and is recorded as open. |
| **Treat it as delivered-versus-grid semantics and document the ratio** | Tempting, and false. The ratio measured 0.9300, not a modelling difference. Documenting a disagreement as a convention is how a defect becomes permanent. |

### Left open, deliberately

`charger_efficiency` should become a **contract field** so MATLAB consumes it rather than
defaulting to a private copy — the same reasoning that put `grid_factor_value` in the contract.
Until then the test is the only thing holding the two in step, and a test is a weaker guarantee
than a value that exists once.

### The other half of task 4.8, stated plainly

**The reconciliation used GNU Octave, not MathWorks MATLAB, and that limitation is real.**
Real MATLAB runs only in the public harness, which must never carry the canonical data — so
real MATLAB has never seen the real sites and cannot until someone runs it on a licensed
machine with access to this repository.

What makes the Octave result usable as evidence, and only this far: Octave and real MATLAB
were cross-validated on a **structurally identical** fixture (same 22 columns, same order,
same vocabularies, same shape) at **2 640 cells, zero numeric divergence, 1e-9 tolerance**
(`MATLAB_LIBERATION.md` §3.7). So the 0.93 measurement reflects the model's arithmetic rather
than an Octave artefact. **It is not a MathWorks MATLAB result and nothing may present it as
one.**

---

## DEC-013 — The live Tableau workbook is wrong; publish a corrected one under a NEW name

**Date:** 2026-07-27 · **Phase:** 6 · **Decided by:** the project owner, asked directly
because the action is irreversible and outward-facing

### What the audit found

Phase 6.4 exists because *auditing the repository's own files never catches a stale published
viz*. It didn't. `EV_Charging_Site_Readiness_Workbook` — **1 097 views**, the project's
most-seen artifact — was downloaded, unpacked, and its Hyper extracts read directly. Three
superseded claims, each checked against the canonical run rather than inferred:

| # | Live on Tableau Public | Canonical | Severity |
|---|---|---|---|
| 1 | Horizons **2035 / 2050** | 2026 / 2036 / 2046 / 2056 | Retired V2 vocabulary |
| 2 | Data confidence **8 Medium, 4 Low** | **12 Low** | **Worst.** Overstates confidence to every viewer |
| 3 | Readiness from **legacy_v2** — FFX002 first at 58.8 | FFX004 first at 53.4 | **The top-ranked site is different** |

Starter and pathway totals (25 / 48) do reconcile.

**#2 is the one that matters most.** Everything else in this program is arranged so that
uncertainty is visible; a public artifact quietly upgrading eight sites to *Medium* undoes
that for the audience that never reads the repository.

### The decision

**Publish the corrected workbook under a new name. Do not overwrite.**

`EV_Charging_Site_Readiness_M2_Canonical` is published fresh; the 1 097-view workbook and its
URL are left exactly as they are, for the owner to hide or delete from the Tableau UI.

**Reasoning:** Tableau Public replaces a same-named workbook **irreversibly, with no version
history**. Overwriting would destroy the only remaining copy of what has actually been on
public display — the record of the defect — and reset a view count that is real evidence of
reach. A new name costs one manual cleanup step and keeps every option open.

**Accepted cost, stated:** for a period, two workbooks on the same profile disagree in
public. That is a worse steady state than one correct workbook and a better one than an
irreversible action taken on the assistant's judgement.

**Rejected:**

| Alternative | Why it loses |
|---|---|
| **Overwrite in place** | Irreversible, no version history, destroys the evidence and the view count. Keeps the URL working, which is the only real argument for it. |
| **Publish nothing** | Leaves a public artifact overstating data confidence. The corrected workbook exists and is verified; withholding it protects nobody. |
| **Owner deletes the old one first, then publish** | Cleanest end state. Not chosen because it blocks on a manual step; remains available afterwards. |

### The patch package carries the same defect

`patch_package/tbl_readiness_confidence.csv` has `readiness_score` and `model_rank`
**byte-equal to `legacy_v2`** with a v3 confidence column beside them, and nothing declaring
the mix. Anyone following the documented build recipe by hand would republish the wrong
ranking under a v3 heading.

**Left in place rather than edited.** It is what a Tableau Desktop operator was handed, and
rewriting it now would erase the evidence that the recipe itself needs correcting.
`CAPABILITY_GAP.md` carries the warning where an operator will read it before starting.

### Residual blockers, not closed

Four, all presentation affordances, none affecting a number: **bar-in-bar**, **two reference
lines**, **dashboard filter scoping**, and the **8-point story**. Each needs Tableau Desktop
or hand-authored XML. Where a substitute shipped, the affected sheet's own subtitle names it
— "GROUPED bars, not the bar-in-bar", "NO REFERENCE LINE", "SYMBOL map, not a choropleth" —
and a test asserts those declarations are present, so a screenshot separated from this
repository still says what it is.

**An honest partial close, which the master prompt prefers to a fake complete one.**

---

## DEC-014 — Phase 10 gains a full line-by-line audit of the entire repository

**Date:** 2026-07-27 · **Raised by:** the project owner, mid-program · **Status:** logged before
any work began · **Phase:** 10, in addition to everything already planned there

### The requirement, in the owner's words

> *"Phase 10 should be a very meticulous audit of every single line in every single file in
> every single folder to make sure we are getting the full picture and are not missing
> anything — in addition to what was planned for phase 10."*

### Why this is not a repeat of Phase 0

Phase 0 read every line of the **inherited** repository: 229 files, twelve lanes, 224 files
read end to end, 200 findings. That read is what made the rest of the program possible.

It is also now **out of date by more than half the repository**. Measured, not estimated:

| | Phase 0 baseline | Now |
|---|---|---|
| Tracked files | 198 | **403** |
| Text lines | — | **~78 700** |

So the Phase 0 read covered code this program did not write, and roughly half of what exists
today has never been read end to end by anyone — it was *written*, which is a different thing.
Writing a file and auditing it are different activities with different failure modes, and this
program has already demonstrated the difference:

- A commit message claimed MATLAB artifacts were committed. They were not — `.gitignore`
  silently swallowed them, and nobody noticed for four commits.
- CI was red for five consecutive commits while the ledger recorded gates green.
- Two Tableau sheets published as title-only, blank, and were called verified.
- `charger_efficiency` held two different values in two halves of one model for the entire
  life of the project.

Every one of those was found by looking at the thing itself rather than at the report of it.
An audit that reads what was actually written, rather than what the commit messages say was
written, is the mechanism that catches the next one.

### What the audit must cover, beyond re-reading

The reading is the method, not the goal. What it is looking *for*:

1. **Claims versus reality.** Every assertion in a README, a docstring, a commit message, a
   ledger entry or a decision record, checked against the code and the artifacts. This program
   has already produced at least one false commit-message claim; the audit assumes there are
   more.
2. **Dead and orphaned code.** Anything unreachable, unused, or superseded — including
   constants, gates and tests that no longer check what their name says.
3. **Gates that pass vacuously.** Four have already been caught (secret scan, link checker,
   CDN pin, capture-form test) plus the harness exposure gate that could not see CSVs. Every
   gate gets a deliberate mutation test or an explicit note saying why it cannot have one.
4. **Numbers appearing anywhere that do not trace to the contract.** Reports, presentation,
   docs, website copy, figure captions.
5. **Anything gitignored that is load-bearing**, and anything tracked that should not be.
6. **Every stated limitation still true**, and every limitation that exists but is not stated.
7. **Secrets, credentials, account identifiers** in anything tracked or shipped.
8. **Files nobody has looked at since they were generated** — the artifacts most likely to
   have quietly drifted.

### How it will run

By fan-out, in non-overlapping lanes with an independent coverage verifier, the way Phase 0
did — that pattern found 200 findings and its verifier reported zero gaps across 20+ probes.
Findings go to `FINDINGS_REGISTER.md` with the same `Confirmed` discipline: **every subagent
finding is a lead, not a fact, until it is reproduced against the actual file**.

### Cost, accepted deliberately

This is the most expensive single item in the program and it is worth it. The alternative is
landing a body of work whose own author has read roughly half of it, on a project whose
central claim is that every number can be traced. **There is no deadline; thoroughness beats
speed at every decision point**, and this is the decision point where that rule matters most.

### Rejected

| Alternative | Why it loses |
|---|---|
| **Audit only what changed since Phase 0** | Cheaper and wrong. The Phase 0 read is now old enough that inherited files have been edited by this program many times; "unchanged" is not a property anyone has verified. |
| **Sample-audit the high-risk areas** | Sampling finds what you expect. Every defect listed above was in a place nobody was worried about. |
| **Rely on the 23 verification gates** | The gates encode what was already thought of. Four of them have themselves been caught passing vacuously, which is precisely the failure a gate cannot self-detect. |
