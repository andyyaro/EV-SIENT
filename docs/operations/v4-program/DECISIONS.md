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

   **The specific recurring shape: a check that matches TEXT where it should match STRUCTURE.**
   Six instances so far, three of them in checks written during this program and two in my own
   tests within an hour of each other:

   | # | The check | What it matched instead |
   |---|---|---|
   | 1 | secret scanner | credential *names*, not values — flagged CI's own regex |
   | 2 | link checker | URLs inside fenced code blocks |
   | 3 | capture-form test | the page's own sentence "sets no cookie" as evidence it does |
   | 4 | CDN pin gate | nothing at all — passed with "0 checked, all pinned" |
   | 5 | harness exposure gate | code lines only; structurally could not see a CSV column |
   | 6 | banner test | the HTML comment *explaining* the banner is not dismissible |
   | 7 | stdlib test | the docstring sentence "No FastAPI, no Flask, no uvicorn" |

   The audit must look for this shape specifically: any check that does `substring in
   source_text` where the property is about structure, usage, or behaviour. The fix is always
   the same — parse it (AST, XML, CSV columns) or exercise it, never grep it.
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

---

## DEC-015 — The platform is a Python-native local server, not a packaged native shell

**Date:** 2026-07-27 · **Phase:** 7 · **Basis:**
[`PHASE_7_PLATFORM_BRIEF.md`](PHASE_7_PLATFORM_BRIEF.md) — a 10-agent design panel: four
independent architectures, each adversarially challenged, then synthesised.

### The decision

`python -m fcf_m2.server` serves the one bundle `site/platform/` on loopback and adds `/api/*`
for execution. **The same directory, byte for byte, is deployed to S3 + CloudFront as the web
tier.** No Rust, no Electron, no bundled Chromium, no second frontend.

**Why:** it is the only architecture where *"one shell, two tiers"* is a property of the
**deployment** rather than a promise a build flag has to keep. The two tiers are literally the
same five files, and the tier is *detected* by asking whether `/api/operations` answers — not
compiled in. Every other angle adds a layer whose only real job is to open a window onto a
page that already exists, and each such layer is a place the tiers can drift.

### Why the other three lost — the real trades, not strawmen

**Tauri + Rust.** The strongest on size and genuinely correct that an embedded CPython can run
the model with no user Python at all — the adversarial pass proved that end to end, with all
seven contract files byte-identical. But after correction, **the Rust layer's entire remaining
job is "spawn `fcf_m2.server` and open a WebView"** — the sidecar it spawns *is* the
architecture chosen here. It costs a language nobody in this repo writes, a second
cross-platform build matrix, ~180 MiB of embedded runtime, and it runs straight into the
boundary problem below.

**Electron.** Wins one real argument: the 3D surface is CesiumJS WebGL2, and Electron
guarantees the desktop renderer is the same engine as the web tier's, where Tauri gives you
WKWebView on macOS and WebView2 on Windows with no cross-browser harness in this repo to catch
a divergence. It loses on ~279 MiB of bundled Chromium — about half the installed bundle — on
a project whose entire tracked payload is **13.5 MiB**. Worse, it cannot auto-update within
the $10/month ceiling (signing alone is ~$8.25/month), so a desktop user's browser ages
indefinitely while the web tier's does not. Shipping a stale browser to make a planning study
feel like an app is a security trade this project should not make.

**Web-first progressive.** Architecturally almost identical to the winner, and its instincts
about the capability probe and a deploy allowlist are adopted. It loses on one mechanism: it
has the **public `https://` page fetch `http://127.0.0.1`**. That is mixed content, it is the
shape a port-scanning ad script has, and it is what Private Network Access exists to restrict.
Serving the identical files from the local server instead makes every request same-origin and
costs nothing. **The idea survives; the direction of the arrow is reversed.**

### What this validates, and what that says about sequencing

Five Phase 7 components were built *while the panel ran*, deliberately chosen to be
shell-independent: the provenance resolver, the operations registry, the web tier, the local
server, and tier detection. The panel — which read the tree rather than the prompt, and
corrected the prompt's claim that nothing was built — landed on the architecture those
components already assume. **Building the shell-independent spine before choosing the shell
was the right call**, and would still have been if the panel had chosen Tauri, because in that
design the sidecar is this same server.

### OPEN QUESTION FOR THE OWNER — not the assistant's to decide

**A downloadable installer that can genuinely *run* the model must carry
`data/inputs/real_sites_v2.csv`** — facility-level electrical and occupancy data for twelve
named public buildings — **out of a repository that is private and stays private.**

That is a declassification decision about real facilities in two jurisdictions, and it belongs
to the project owner and the client, not to this program. Until it is answered:

- The **web tier ships**. It serves only contract *outputs*, which are already public-facing
  in the reports and on the site.
- The **desktop tier runs from a clone** for anyone who has repository access. That covers the
  team, which is who actually needs to execute anything.
- **No public installer is built.** Recorded as a residual limitation rather than quietly
  descoped.

Three options exist and none is obviously right: ship an installer carrying a **synthetic**
input set (honest, and the model then computes nothing about real sites); ship a
clone-and-run path only (what happens by default); or declassify the input file (a real
decision with real consequences for twelve named buildings).

---

## DEC-016 — A public installer carries synthetic inputs; the real site data stays private

**Date:** 2026-07-27 · **Phase:** 7/8 · **Resolves the open question in DEC-015**

### Context

DEC-015 raised it: a downloadable installer that can genuinely *run* the model must carry
`data/inputs/real_sites_v2.csv` — facility-level electrical and occupancy data for twelve
named public buildings — out of a repository that stays private.

The project owner responded *"yeah declassify it"*, then *"let's use a most up-to-date one
instead"*, then, when asked which was meant, *"do whatever you think is best, and it does not
have to be now."*

### The decision

**The real input data stays private. A public installer ships a synthetic input set,
unmistakably labelled.**

### Reasoning

The owner has the authority to publish this repository's contents and said so. The decision is
still to hold, for three reasons:

1. **The data is not only ours to publish.** It describes buildings owned by the City of
   Fairfax and Prince William County, and this study is run *in consultation with* Prince
   William County's Office of Sustainability. A facilities manager would reasonably expect to
   be asked before their building's electrical service rating, spare capacity and occupancy
   pattern were published. That conversation has not happened — it is not even on the open
   human actions list.
2. **It is the one action here with no undo.** Everything else this program has done is
   revertible. Publishing twelve real facilities' electrical characteristics is not.
3. **The instruction was ambiguous and the owner explicitly allowed deferral.** "Do whatever
   you think is best, and it does not have to be now" is permission to choose the cautious
   option, not pressure to act.

**What is lost by holding: almost nothing.** A synthetic installer demonstrates the model end
to end — every screen, every operation, the whole provenance panel. What it cannot do is make
a claim about a real site, which is a claim the study cannot support anyway: capacity is a
placeholder at all twelve.

**The precedent already exists and works.** The public MATLAB harness runs on
`harness_scenarios_synthetic.csv` for exactly this reason, and that decision has since caught
a real leak (`sessions_per_day = 0.9`, which was PWC003's value) — evidence that the synthetic
boundary is doing work rather than being ceremony.

### What ships

| Surface | Data | Status |
|---|---|---|
| Web tier (public) | contract **outputs** only — already public in the reports and on the site | ships |
| Desktop tier, from a clone | the real inputs | works for anyone with repository access, which is the team |
| Public installer | **synthetic inputs**, labelled | when built |
| Real input file | — | **stays private** |

### Left open, deliberately, for the owner

Declassification remains available and nothing here forecloses it. If it is wanted, the
sequence is: **ask the two jurisdictions' facilities contacts first**, then publish, then
rebuild the installer against the real inputs. Recorded as an open human action rather than
an assistant decision, because that is what it is.

### Also decided: no Cesium ion token

The owner offered one. **Declined**, for three reasons that all point the same way:

- the master prompt requires the explorer work **with no Cesium account**, and Phase 3 already
  achieved that;
- a token in the web tier would be **visible in the deployed JavaScript** — a credential in a
  public artifact, which the standing rule forbids outright;
- ion usage above the free tier is a **recurring cost** against a $10/month ceiling.

If ion terrain is wanted later, the clean route is a domain-restricted token injected at
deploy time and never committed. That is a Phase 8 decision with its own entry, not something
to wire in now.

---

## DEC-017 — The web platform is gated at the edge, not in the browser

**Date:** 2026-07-27 · **Phase:** 8 · **Requested by the owner, approved before implementation**

### Context

The owner asked for the deployed platform to sit behind a Cognito sign-in, granting access to
an existing user, `redacted-3@example.org`, and asked whether it could be done without
them at the machine. Both were answered before any work started; the owner replied
*"good i approve"*.

Reconnaissance established four facts that shaped the design, each verified rather than
assumed:

1. **The user already exists and is `CONFIRMED`** in pool `us-east-1_mKrwfQTkg`. Its password
   is already set. No credential has to be created, reset, or handled — which is fortunate,
   because handling one is forbidden.
2. **The Cognito hosted-UI domain is already `ACTIVE`** (`us-east-1mkrwfqtkg`), and a **public
   app client with no secret** already uses the authorisation-code flow on this very site.
3. **The distribution serving the platform also serves the NFC layer.** `E1XZPHWHZV0OEO` has
   exactly one origin, *zero* extra cache behaviours, and the alias
   `futurecityfellowship.andyyaro.com`. `/t/FFX001`–`/t/PWC008` live on its default behaviour.
4. **The site's existing client-side sign-in is correct for what it protects, and is not a
   model for this.** An anonymous `GET /assistant.html` does return HTTP 200 and all 70 378
   bytes — but the prose in those bytes is 1 677 characters of login form, no site data, and
   the asset it guards is an API (`POST .../chat`) which answers an unauthenticated call with
   **HTTP 401**. A publicly served login page in front of a server-enforced API is the normal,
   correct shape.

   *(Recorded because the first version of this entry claimed the opposite. The initial
   measurement failed to strip `<style>` blocks and counted 26 400 characters of CSS as
   leaked prose, and the API was asserted to be unprotected without being called. Both were
   wrong; the API was then called and returned 401. The error is left visible here rather than
   quietly deleted, because a decision log that hides its own corrections is worth less than
   one that shows them.)*

5. **The granted user has no `email_verified` attribute at all** — `admin-get-user` returns
   only `email` and `sub`. This matters more than it looks: the textbook identity check is
   `email_verified === true`, and requiring it here would have produced a gate that could
   never open for the one account it exists to admit. The failure would have been invisible
   from this side, because verifying it requires signing in as that user. The allowlist
   therefore matches on **`sub`** — immutable, and the tightest possible identifier for
   "that user specifically" — *and* on `email`, with `email_verified` deliberately not
   required. See the authoriser's own comment for the same reasoning at the point of use.

### The decision

**Authentication runs in a Lambda@Edge viewer-request function attached to a new
`/platform/*` cache behaviour. The default behaviour is not touched.**

Three properties follow, and each is the reason for a constraint the owner did not ask for:

- **The NFC layer stays public.** A reader taps a coin in a car park and gets a page, with no
  account and no app — that is the whole point of Phase 5 (DEC-006). Gating the distribution
  would have broken all twelve tags. Auth is therefore scoped to one path pattern, and the
  verification step checks the tags still answer, not merely that the gate closed.
- **The gate is real, and it has to be, because this asset has no server behind it.** This is
  where the platform differs in kind from `assistant.html`. That page can gate in the browser
  because the thing worth protecting is an API that enforces auth itself; the page is just a
  door, and doors are meant to be visible. The platform is the opposite: it is a **static
  bundle**, so the bytes *are* the asset and there is no server-side chokepoint to enforce
  anything. A client-side gate over static files cannot protect them — it can only hide what
  CloudFront has already handed over. Enforcement therefore has to move to the edge.
  Viewer-request runs on every request *before* the cache is consulted, so an unauthenticated
  caller never reaches a byte, cached or not.
- **No secret exists anywhere.** The app client is **public and uses PKCE**, so there is no
  client secret to store; the session cookie holds the Cognito `id_token`, verified on each
  request against the pool's **public** JWKS. Nothing needs SSM, and nothing needs the
  environment variables Lambda@Edge does not support. The standing rule — never embed a
  credential in the app, installer, frontend, or any release artifact — is satisfied by
  construction rather than by care.

### Alternatives rejected

| Option | Why not |
|---|---|
| Client-side Cognito, as `assistant.html` does | Right shape for that page, wrong shape here. It works there because an API enforces auth server-side; the platform is static, so there is nothing behind the page to enforce anything, and hiding delivered bytes with JavaScript is not access control. |
| Application Load Balancer with built-in OIDC | ~**$16/month** at on-demand rates for the ALB alone. Exceeds the entire $10/month ceiling for one feature. |
| CloudFront Function instead of Lambda@Edge | Cannot perform RS256 verification or the token exchange — no network calls, restricted runtime. It would have to trust the cookie, which is not verification. |
| CloudFront signed cookies / signed URLs | Real gating, but unrelated to Cognito; the owner asked for a Cognito sign-in by that user specifically. |
| Gate the whole distribution | Breaks all twelve NFC tags. Not a trade-off — a regression. |

### The scope change this represents, stated plainly

The master prompt describes the web tier as *the primary distribution, zero friction*. A
sign-in is friction, and this is a deliberate departure made at the owner's request. What is
**not** changed: the NFC field layer, which was always the zero-friction surface and remains
open to anyone with a phone.

### Cost

Cognito is free below 50 000 monthly actives. Lambda@Edge is $0.60 per million requests plus
$0.00005001/GB-s; for a private page with one user this rounds to **under $0.05/month**.
Aggregate incremental cost stays inside the $10/month ceiling.

### What could not be verified, and why

**That the gate opens for `redacted-3@example.org`.** Confirming it requires signing in as
that user, and that password is neither available to nor appropriate for the assistant to
hold. What *is* verified: an anonymous request is refused, and the NFC tags still answer.
The remaining check is one sign-in by the owner, recorded as an open human action.

### What the adversarial review changed, and the one it changed most

Six independent attack lenses were run against the authoriser before it was deployed, each
finding then put to two refuters. Eight claims came back. Treated as leads, not facts — every
one was checked against the file by hand. Four survived that check and were fixed; the rest
were either already fixed or not exploitable.

| Claim | Verdict | Outcome |
|---|---|---|
| Reflected XSS via Cognito's `error` parameter | **Real** | Already found and fixed while writing the tests, independently — two lenses converged on it. Escaping is now centralised in `escapeHtml` so no call site has to remember. |
| Percent-encoded path evades the cache behaviour | **Real risk, unresolvable by inspection** | See below — the architecture changed. |
| Sibling-subdomain cookie shadowing → permanent lockout | **Real** | Cookies now carry the `__Host-` prefix, which a browser only accepts from the exact host. |
| Authorization-code injection via a forgeable PKCE stash | **Real, same root cause** | Closed by the same `__Host-` change: the stash can no longer be planted by another subdomain. |
| Forced sign-out via `<img src=…/logout>` | **Real, low impact** | Sign-out now requires `Sec-Fetch-Dest: document`, so a subresource cannot clear the session. |

**The one that changed the design.** A cache behaviour is chosen by matching the path against
`/platform*`, and CloudFront normalises percent-encoding — *measured on the live distribution,
not assumed*: `/%61ssistant.html` returns the same 70 378 bytes as `/assistant.html`. If
pattern matching happens **before** normalisation, `/%70latform/index.html` would miss the
gated behaviour and be served by the default one, with no authentication at all. Which of
those two internal steps runs first is not something inspection can settle.

So the design stopped depending on the answer. **The platform bundle now lives in its own
bucket**, reachable only through the gated behaviour. A request that evades the path pattern
falls to the default behaviour, whose origin is the main bucket — which contains no platform
content, and returns 404. The guarantee moves from behavioural to structural, the same move
this program already made when it decided an operation *is* a CLI command rather than merely
matches one.

Incremental cost of the second bucket at 25 MB: roughly **$0.0006/month**.

*Honest note on the review itself: the workflow reported "0 findings" because a bug in the
orchestration script passed promises where it should have passed functions, so every
refutation threw and the results were discarded. The empty result was not a clean bill of
health, and was not reported as one — the agents' raw output was read from the run journal
instead. A green result whose plumbing failed is indistinguishable from a real one unless the
plumbing is checked.*

### Post-deployment defect: the gate worked and the sign-in page did not exist

Reported by the owner within minutes of the deployment being called verified:
`/platform/` redirected to Cognito, and Cognito answered
**"Login pages unavailable · Please contact an administrator."**

**Cause.** This pool runs **Managed Login version 2**, under which *every app client needs its
own branding record*. A client without one does not fall back to a default page — it has no
sign-in page at all. The newly created `future-city-platform-edge` client had none. Nothing in
the app client's own configuration hints at this; the existing `future-city-assistant-web`
client had a branding record (`50b10138-…`) and so had never exposed the gap, and the site's
other sign-in never used the hosted UI at all.

**Fix.** `create-managed-login-branding --use-cognito-provided-values`, now performed by
`deploy_platform.py` so a rebuild cannot omit it.

**The real lesson, which is about the verification and not the bug.** Every one of the 32
assertions passed while the feature was unusable, because they asserted *the gate redirects to
Cognito* — and it did. That is a strictly weaker claim than *a person can reach a sign-in
form*, and the weaker claim is the one that was checked. The verifier now **follows the
redirect** and asserts a real password field renders. This is the same failure as the two
blank Tableau sheets: verifying the step this program controls rather than the outcome the
reader experiences.

It also lands squarely on the caveat published alongside the deployment — that whether anything
*behind* the redirect worked was explicitly unverified. The caveat was correct, and being
correct about an unverified thing is not the same as it working.

**Ninth text-versus-meaning trap, caught this time.** The first check for the fix searched the
returned page for "unavailable" and reported it still present. It was: Cognito ships its entire
localisation table, including the string `"Login pages unavailable"` itself, inside a
`<script>` on *every* page — including the working one. The reliable signal is the presence of
a `type="password"` input. Had that grep been trusted, a working fix would have been reported
as broken.

### Access widened to a second account, and why the first one alone was not workable

The granted account `redacted-3@example.org` is `CONFIRMED` and enabled, so it has a
password. The owner reported never receiving a sign-in email and asked whether the email might
simply have been sent earlier, when the account was first added. **CloudTrail settles it, and
the answer is neither "sent earlier" nor the mechanism first inferred here:**

| Evidence | Finding |
|---|---|
| `AdminCreateUser`, 2026-07-09T23:38:48Z | **`messageAction: SUPPRESS`** — the invitation email was explicitly suppressed. Cognito has never sent mail to this address. |
| `AdminSetUserPassword` | **No events.** The password was not set by an admin call. |
| `RespondToAuthChallenge` ×3, same day | The `NEW_PASSWORD_REQUIRED` challenge was completed in a browser ~50 s after creation — whoever set the account up held the temporary password out of band, which is precisely why they suppressed the email. |

So the credential exists and was chosen by whoever performed that setup. **No email was ever
sent, and none could have been**: the assistant did not create the account and deliberately did
not touch its credential.

*(An earlier version of this entry said the password was set "thirty-nine seconds" after
creation and implied an admin-set. Both were wrong — the gap is ~50 seconds and it was a
browser challenge response. The numbers were read off two timestamps rather than checked
against the audit log, which was available the whole time.)*

**The second problem, which the first was hiding.** The account carried **no `email_verified`
attribute**, and this pool's recovery mechanisms are `verified_email` then
`verified_phone_number`. *"Forgot your password?" could not have delivered either.* The
missing attribute had already been noticed while building the allowlist and designed around
for **authorisation**; what was missed is that the same gap also breaks **recovery**. One
fact, two consequences, only one of them followed through.

**Still unproven: that the mailbox receives anything.** Because delivery was suppressed at
creation and never attempted since, `redacted-3@example.org` has never been sent a message
by this pool. Setting `email_verified` makes Cognito *willing* to send a reset there; it is not
evidence that anything arrives.

At the owner's direction, both routes were opened:

1. **`email_verified` set to `true`** on `redacted-3@example.org`. This is a verification
   flag, not a credential — it lets the owner run a self-service reset in which the password
   travels from Cognito to their mailbox and is never seen by the assistant.
2. **`redacted-6@example.org` added to the allowlist.** It already existed in the same pool with
   credentials the owner holds. Widening access beyond the single account originally specified
   was the owner's explicit decision, recorded here because it changes who can read the study.

`redacted-1@example.org` is in the same pool and is **not** granted — a test asserts that a valid
pool member who is not allowlisted is still refused, because being able to authenticate is not
the same as being authorised.

A further test asserts that one account's `sub` paired with the other's email is **refused**.
With a single entry that was hypothetical; with two it is a real shape, and an allowlist that
checked the two fields independently would admit a token that mixes two genuine accounts.

**A guard that cried wolf.** The redeploy was refused by `assert_safe_change` with "existing
origin platform-gated was modified" — the guard treated *every* pre-existing origin as
untouchable, including the one the script itself owns and rewrites on every run. So it fired
on the second deploy of an unchanged configuration. That is worse than not having it: a check
that fails every time teaches the operator to skip it, and the genuine signal — *someone
else's* origin moved — drowns. Now exempted, with the platform origin still asserted to point
at the isolated bucket. **Lambda version 2 was published while this fired, and CloudFront was
never updated to use it**, so for a few minutes the newly published code was live nowhere. The
failure was safe, which is the point, but it was not free.

---

## DEC-018 — Blank attribution was silently accepted as the string "nan"

**Date:** 2026-07-27 · **Phase:** 7 · **Severity: the V4 loop's central guarantee, defeated
since it was written**

### What was wrong

`CapacityObservation.__post_init__` refuses an observation whose `source_document` or
`observer` is blank. The comment above it is explicit about why: *"An unattributed observation
cannot upgrade anything, so it is refused at the door rather than accepted and quietly ignored
later."*

**That refusal never fired.** pandas reads a blank CSV cell as `NaN`, and
`read_capacity_observations` did `str(row["source_document"]).strip()` — so `NaN` reached the
check as the four-character string `'nan'`. Non-empty. Check passes.

The consequence, reproduced before the fix:

```
implied_basis   = 'verified_utility'      <- the strongest basis available
capacity_source = 'verified_utility via utility_load_study: nan (Dominion Energy),
                   recorded by nan on 2026-07-01'
```

A row naming **no document and no observer** was accepted, and claimed the strongest possible
provenance. `capacity_basis` becoming `verified_utility` is exactly the condition the
fail-closed capacity guard tests for before it will emit a feasibility claim. So the guard —
this project's most-cited safeguard — could have been satisfied by a blank spreadsheet cell.

Nothing had ever been observed to fail, because nothing had ever submitted a blank cell: the
only capacity data in the repository is a hand-made fixture with every field populated.

### How it was found

**By a disagreement, not by looking for it.** A parity test was written to check that the new
browser entry form never accepts what the model rejects. It reported the opposite of the
expected failure: the *form* refused the blank row and the *model* took it. The test was built
to catch a permissive form and instead caught a permissive model.

This is the argument for cross-checking two independent implementations of the same rule. A
test written against `observed.py` alone would have encoded the same assumption the code makes
— that a blank cell arrives blank — and passed.

### The fix

`_as_text()` at the CSV boundary: a missing, `NaN`, or whitespace-only cell becomes `""`,
never `"nan"`. Applied to **every** text column in both readers, not only the two that were
checked — `source_org` had the same hole and would have printed `nan` inside the provenance
string that travels into the contract, which reads as a fabricated source.

Two further refusals were added while in there, both the same class of defect:

- **A capacity observation with no `site_id` is refused.** Unchecked it did not error —
  `resolve_capacity` groups by `site_id`, so it created a phantom site keyed on the empty
  string whose confirmed capacity belonged to nowhere.
- **Same for session observations.**

### Gates

- `tests/test_observed.py` — six regression tests, including one asserting that **no** text
  field can arrive as `'nan'`, so the general form of the bug is closed rather than the two
  instances that were noticed.
- `verify.sh` gate 30 — the form/model parity check that found it.

### What this says about the other refusals in this codebase

This program has repeatedly relied on the argument *"the code refuses it, therefore it cannot
happen."* This is a case where the refusal existed, was correct, was well-commented, was
covered by tests that constructed the dataclass **directly** — and was unreachable through the
path real data actually takes. **A guard is only as good as the boundary conversion in front
of it**, and the tests were aimed at the guard rather than at the boundary. That belongs in the
Phase 10 audit's brief: for every refusal, ask what the value looks like when it *arrives*, not
what it looks like in the test that constructs it.

---

## DEC-019 — The website embedded a workbook that had been deleted, and nobody traced the dependency

**Date:** 2026-07-27 · **Phase:** 8.3 · **Raised by the owner**

### What happened

DEC-013 found the live Tableau workbook wrong on three counts, a corrected workbook was
published under a **new name**, and the original was deleted — an open human action the owner
carried out. **Nothing re-pointed the website.** Its embeds still named
`EV_Charging_Site_Readiness_Workbook`, so every one of them resolved to
`public.tableau.com/app/resource-not-found`: **12 distinct sheets, 21 references**, across
`dashboard.html` and `results.html`.

The owner surfaced it, not the program: *"you had me deleted the initial workbook published
having its visuals embedded/used on the website, what does that mean?"* The dependency was
never traced when the deletion was requested, and the deployment earlier the same day
republished the broken pages without noticing.

**Detection note worth keeping.** Tableau answers **HTTP 302 for live and deleted views
alike**, and both redirect chains end in a 200 carrying the same 1 442-byte JavaScript shell.
A status-code check distinguishes nothing. The difference is only visible in the *final URL* —
`/app/resource-not-found` versus the real view path. Any future check must follow the redirect
and read where it lands.

### Why it was not a find-and-replace

The deleted workbook had **12** sheets; the canonical one has **7**, and they are different
analyses. Four map cleanly. The rest — review burden, per-dimension subscores, profile
readiness, rank stability — come from the **old scoring model**, whose fields the canonical
contract does not carry. Rebuilding them would mean inventing the numbers underneath, so they
were removed rather than faked or quietly pointed at some unrelated chart.

The owner's instruction was *"I do not really care about the old ones… we can replace the old
ones placeholder with the current ones"*, with `dashboard.html` to keep **fewer, larger
charts** and the 3D rotating gallery on `results.html` left alone (it is images, unaffected).

### The part that was actual work

Every embed sits in a slide with a title, tab labels and explanatory copy describing *that
specific old chart*. Swapping only the URLs would have left the page describing charts it no
longer shows — **replacing a broken embed with a false one, which is worse**. So each slide's
title, chip label, tooltip, and info bar was rewritten to name the chart now behind it.

Two hard-coded counters also had to be derived rather than left: the carousel's `1 / 7` and the
hero's *"Planning views: 7"*. The deck's JavaScript reads the *current* slide from the DOM but
not the *total*, so after removing two slides the page advertised seven views over five.

### Result

| | Before | After |
|---|---|---|
| Slides in the deck | 7 (+2 clones) | **5** (+2 clones) |
| Distinct sheets embedded | 12, all dead | **7, all canonical** |
| References to the deleted workbook | 21 | **0** |
| Chart height | `clamp(450px, 60vh, 650px)` | `clamp(520px, 70vh, 820px)` |

New deck: Site Readiness · Location Context · Port Right-Sizing (2 tabs) · Cost and Emissions
(2 tabs) · Waiting Times. All seven canonical sheets are used.

### Two attempts that produced a wrong deck, kept here because the reason generalises

1. **Renumbering in place.** The carousel's two clones carry their own `data-slide` and
   "Part N" markup, so a sequential walk counted them as slides and shifted every real one —
   the deck read Part 1…7 for five charts.
2. **Patching the clones' attributes.** A clone is a copy of an entire slide's markup. After
   the slide it was cloned from was deleted, it kept displaying a chart that existed nowhere
   else in the deck. Fixing the attribute did not fix the content.

Both were replaced by regenerating the deck from the surviving slides, so a clone is *derived
from* its source and cannot disagree with it.

### Gate

`scripts/check_site_www.py` now fails if any page references the deleted workbook, if a stated
view count disagrees with the number of slides, or if a slide still carries a title naming a
chart it no longer shows.

### Open question this raises for Phase 10

**What else was deleted or renamed without tracing what depended on it?** This one was caught
because the owner remembered. The audit brief should include a pass over every external
resource the repository or the live site references, checking that each still resolves — by
following redirects, not by trusting a status code.

---

## DEC-020 — The synthetic input set, and what "synthetic" turned out to mean

**Date:** 2026-07-28 · **Phase:** 8.4 · **Owner's decision: "build a synthetic site-input set"**

### What was blocking

DEC-016 required a public installer to ship synthetic inputs rather than the twelve real
facilities' data. The set was never built, which made the public installer **unbuildable**
rather than merely undone — `workflow.py` cannot start without a site table, so a public
artifact could only leak the real data or fail to run.

### It was never one file

`_load_inputs()` reads **four** site-keyed inputs. Building only the sites table would have
left three others pointing at real sites. All four are generated.

### Substituting the inputs was nowhere near sufficient

The first artifact had its four inputs correctly replaced — and still shipped **36 distinct
real facility identifiers across 87 files**: model outputs under `data/outputs`, the test
fixtures, the NFC placement cards and tag payloads, the contract, and the docs. The real site
identities are woven through everything the study has ever produced.

So a public artifact carries **no derived results at all** — the model, the synthetic inputs,
and nothing else. `src/` and `data/anchors/` were verified to contain zero real identifiers;
five scripts do contain them and are excluded by allowlist rather than by hope. The builder
then **opens the finished archive, proves no real identifier is present, and deletes it if one
is** — because a leaking artifact that exists on disk is one command from being attached to a
release.

**This is why the requirement says to verify by inspecting the built package.** Every
substitution was correct and the artifact still leaked.

### Three refusals from the model itself, each of which improved the result

The synthetic set did not work first time, and every failure was the codebase declining to
accept something it should decline:

1. **`unknown source_class values: ['synthetic']`.** The confidence system rejected an
   invented vocabulary term. It already had `synthetic_model`, worth 30 — below
   `planning_assumption` (35), above `unconfirmed` (15) — which is exactly the right weight for
   invented data. The model knew the answer; the fixture had to use its vocabulary.
2. **`RT-04: baseline starter total 24 != 25`.** The golden-baseline rule asserts the real
   study's accepted totals. A synthetic run cannot reproduce them and **must not be tuned until
   it does** — that would encode real results inside data labelled invented, which is both a
   false label and a leak. The rule now applies unless the run proves itself synthetic, and
   the test is `all` provenance rows, not `any`: a mixed run gets the strict check.
3. **`'SYN011' does not match '^(FFX|PWC)[0-9]{3}$'`.** The schema is widened for provably
   synthetic runs rather than relaxed. Making synthetic ids match the real pattern would have
   satisfied the validator by making invented data indistinguishable from the study's — the
   opposite of what a fixture is for. `jurisdiction_for("SYN…")` returns `synthetic`, never
   `fairfax` or `pwc`.

**The real run still produces exactly 25 / 48**, verified after each change.

### The overclaim, and the review that caught it

The first version of this generator stated: *"Nothing here is derived from the real files. Not
copied, not perturbed, not sampled, not fitted to their distributions."*

**That was false**, and false in the way overclaims usually are — broadly true, precisely
wrong, and contradicted by a comment twelve lines below reading *"Copied verbatim from the real
file."* An adversarial review (five attack angles, findings independently reproduced)
established:

| Claimed clean | Actually |
|---|---|
| Nothing fitted to real distributions | `avg_dwell_min`, arrival hours, spare-capacity placeholders, EV-share and risk points were drawn from `rng.choice` lists that were **exactly the real file's distinct values** — read off it while exploring the schema. That publishes the precise set of values in use across the twelve real facilities. |
| Nothing copied | Two risk free-text strings were verbatim; twelve columns are verbatim constants. |
| "A county that does not exist" | Every row still carried `state = VA`. |

All fixed: the support sets now share no member with the real ones, the risk strings are
reworded, the state code is `ZZ`.

### What is shared, deliberately, and why none of it identifies a site

"Zero overlap" is neither achievable nor desirable — a synthetic set must share the schema to
be usable. What is shared: **schema vocabularies** (`site_type`, the seven provenance field
groups) because the model cannot parse the file otherwise; **boolean and small-integer
domains** (`public_access` is 0 or 1; twelve ranks are 1..12) because that is arithmetic; the
**study's uniform conventions** (480 V, $150/ft trenching, the safety-review flags), each a
single fact true of every site equally and therefore separating none of them; and the
**electrical placeholders**.

The placeholders are load-bearing. `elec_service_rating_amp = 0` and `spare_capacity_kw = 0`
are what make `capacity_basis` come out `placeholder` at every site. A fixture that invented
capacity would make a synthetic run report **more** confidence than the real study — the one
direction a fixture must never move.

### Result

The public artifact is **0.1 MB, 44 files**, verified free of all 36 real identifiers, and the
model runs from a clean extraction: `starter_total_2026: 24`, `pathway_total: 42`,
`high_confidence_sites: 0`, capacity placeholder at 12/12. Different data, different answer,
honestly labelled — and the contract it writes declares `synthetic_inputs: true` and
`legacy_totals_checked: false` in its own manifest, so a directory that travels cannot be
quoted as the study's numbers.
