# DECISIONS.md - every judgment call, its alternatives, and its reasoning

For the four teammates who did not watch this work happen. Each entry says what was decided,
what was rejected, and **why** - because the reasoning is the part that lets someone
reverse a decision later on purpose rather than by accident.

Decisions are appended, never rewritten. If one is superseded, the new entry says so and the
old one stays.

---

## DEC-000 - Phase 6B: build a data intake layer so the model is portable

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
requirement names it a first-class surface - load data, see the proposed mapping, see what
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
quietly assumes a capacity - the number looks better and means less.

### Alternatives rejected

| Alternative | Why it loses |
|---|---|
| **A second, standalone intake pipeline** | Explicitly ruled out by the requirement, and rightly: two ingestion paths diverge, and the V4 machinery in `observed.py` already encodes the refusals this needs. Extending it keeps one set of rules. |
| **Best-effort silent cleaning** - infer, convert, impute, run | The failure this project exists to avoid. A run that succeeds on data nobody inspected produces numbers nobody can defend. |
| **Reject anything that does not match the schema exactly** | Honest but useless. A jurisdiction with 80% of the fields should get a run and a *lower confidence rating*, not a refusal. |
| **A hand-written mapping config as the primary path** | Ruled out by the amendment. It is the automation fallback; the visual mapping step is the primary one, because a config file hides exactly the decisions the user most needs to see. |
| **A paid ETL tool** (Alteryx, or a Tableau/MATLAB-dependent step) | Ruled out by the amendment. Anything needed to get data into the model is Python in this package, testable under pytest, runnable in CI, and free. |

### What it extends rather than replaces

- **`src/fcf_m2/observed.py`** - the V4 ingestion machinery. It already refuses unattributed
  records and names missing metrics instead of defaulting them.
- **`src/fcf_m2/confidence.py`** - the existing typed data-confidence system, rubric
  `High ≥ 75`, `Medium ≥ 50`, else `Low`, derived **only** from typed provenance fields.
  Requirement 6B.4 routes completeness into this rather than inventing a parallel score.

### Gate

A deliberately messy third-party-shaped fixture - wrong column names, mixed units, missing
fields, different CRS - runs end to end and produces a **correctly-degraded** confidence
rating, with **every transformation traceable**.

### Open question noted at logging time

CRS reprojection done properly generally means `pyproj`. It is free and open-source, so it
satisfies the amendment, but it is a **new runtime dependency** and gets its own decision
entry when reached. A hand-rolled reprojection would be a transformation that cannot be
explained in one sentence, which the hard constraint forbids.

---

## DEC-001 - Keep `LEDGER.md` inside the repository

**Date:** 2026-07-27 · **Phase:** 0

Create the program ledger at `docs/operations/v4-program/LEDGER.md`, tracked and committed
often.

**Rejected:** an untracked scratch file, and a file in the workspace parent. Both fail the
same test - neither survives a clean clone, and the program's own recovery procedure depends
on the ledger being recoverable from git alone.

---

## DEC-002 - Fetch CesiumJS on demand rather than committing it

**Date:** 2026-07-27 · **Phase:** 3

`scripts/vendor_cesium.sh` fetches CesiumJS into a gitignored directory. The viewer probes
for the vendored copy and falls back to the pinned CDN, so a clean checkout works online and
a vendored checkout works with no network at all.

**Rejected:**

- *Commit `Build/Cesium`* - 20 MB across 375 files added to every clone, to carry a pinned
  third-party redistributable that is reproducible on demand and re-bundled at
  desktop-packaging time anyway.
- *CDN only* - the viewer must work offline.
- *Commit a minified subset* - a hand-pruned Cesium is neither upstream nor reproducible,
  and would diverge silently from the CDN build.

The fetch script **refuses to run** if the version it would fetch disagrees with the pin in
`index.html`, because a vendored copy that differs from the online one makes the viewer
behave differently offline and online - the worst of both.

---

## DEC-003 - Lock NFC tags at deployment, not at writing

**Date:** 2026-07-27 · **Phase:** 5 · **Prompted by:** the owner asking whether locking was
required at all

Tags going into public space are locked. Bench tags - demos, rehearsals, pipeline
verification - stay unlocked.

**Reasoning:** locking defends against exactly one threat, a stranger rewriting a tag that
carries the project's implicit endorsement. That threat exists only once a tag is somewhere
a stranger can reach it. A tag on a desk is not exposed to it, and locking one throws away
the ability to re-point it when a URL changes - which matters, because the capture-form
route did not exist when the first tag was written. With 50 coins and 12 sites, spares are
free.

The runbook originally said to lock every tag. That was wrong, and the question that surfaced
it was a good one.

---

## DEC-004 - Lock rather than password-protect

**Date:** 2026-07-27 · **Phase:** 5

NTAG215 supports a 32-bit password (PWD/PACK). We lock instead.

A password shared across a team and printed in a runbook protects against nobody with
physical access, which is the only attacker that matters for a coin in a car park. Locking
achieves the actual goal - permanent read-only - with no secret to leak, rotate, or forget.
The cost is that a locked tag can never be corrected, which is why verification precedes
locking as a hard sequence rather than as advice.

---

## DEC-005 - Do not use the tag UID as an identifier

**Date:** 2026-07-27 · **Phase:** 5

Every NTAG215 carries a unique read-only 7-byte UID. It is recorded in the verification log
for **inventory** - knowing which physical coin is where - and is never consulted by any code
path.

A UID is trivially cloneable, so it authenticates nothing. Treating it as identity invites
exactly the "the tag said so" reasoning this design avoids.

---

## DEC-006 - The capture form submits nowhere

**Date:** 2026-07-27 · **Phase:** 5

The field capture form assembles a CSV row in the browser and offers it for download or
email. There is no backend.

**Reasoning:** a form that posts into the model from a tag anyone can tap is an open door to
polluting the data the whole study rests on. There is no endpoint to abuse because there is
no endpoint. It also matches the existing rule that received values enter the inputs and the
model **re-runs** - never an edit in place - since a row that arrives by email is reviewed by
a human before ingestion. Secondary benefits: no recurring cost, and no store to breach.

**Rejected:** a Lambda + API Gateway endpoint. It would cost money, need authentication to be
safe, and create both an abuse surface and a data store - all to remove one email.

---

## DEC-007 - Use the existing site and distribution for NFC routes

**Date:** 2026-07-27 · **Phase:** 5 / 8

NFC landing pages and capture forms are served from the existing
`futurecityfellowship.andyyaro.com` CloudFront distribution and certificate.

**Reasoning:** the program's hard cost ceiling is $10/month aggregate. Riding infrastructure
that already exists makes the incremental cost effectively zero - 75 KB of storage, no new
distribution, no new certificate, no new DNS record.

**Rejected:** a dedicated short domain. It would read slightly better on a printed card and
would cost a registration, a certificate and a distribution, for a project whose entire
current run rate is about $0.40/month.

---

## DEC-008 - Contract v2 is derived from v1 by migration, not produced independently

**Date:** 2026-07-27 · **Phase:** 4

`data/contract/v2/` is built by reading the frozen `data/contract/v1/` and widening it.
`scripts/build_contract_v2.py` and `fcf_m2.workflow` both call the one migration function in
`src/fcf_m2/contract_v2.py`; neither reimplements it.

**Reasoning:** "v2 is additive over v1" is the entire promise of the version, and derivation
makes it true *by construction* rather than by discipline. Migration copies every v1 value
across, so a v2 number drifting from its v1 counterpart is not something the code is able to
express. The tests assert it anyway, because a guarantee nobody checks is a comment.

It is also the same rule the owner set for Phase 6B - *do not build a second, parallel intake
path* - applied one phase earlier. Two producers for two versions of the same contract is
exactly how the horizon vocabulary ended up meaning three different things across Python,
Excel and MATLAB before the V3 restructure.

**Rejected:**

| Alternative | Why it loses |
|---|---|
| **Emit v2 directly from `workflow.run`, independently of v1** | Two producers, two chances to diverge, and no mechanical proof of additivity - only a test that would have to enumerate all 48 fields correctly forever. |
| **Regenerate v1 and v2 together from the model each run** | Requires regenerating v1, which is now immutable. The reason to freeze v1 is that published artifacts quote it. |
| **A `version=` parameter on `contract.write_contract`** | One function branching on version reads tidier and is worse: v1's writer is frozen code that should not be edited to add a case for something that came after it. |

**Consequence accepted, and stated:** if the model itself changes, v2 does not update from
the model - it updates from whatever v1 it was derived from, and v1 is frozen. That is
correct for a container change and wrong for a model change. When the V4 model genuinely
produces different numbers, those go into a **new run** with its own contract directory and
its own `model_version`, not into this v2. The v2 manifest records the SHA-256 of the exact
v1 it came from, so "which v1?" stays answerable.

---

## DEC-009 - `horizon_label`'s `now` becomes `baseline` in v2, and stays `now` in v1 forever

**Date:** 2026-07-27 · **Phase:** 4 · **Closes:** FIND-NUM-04

**Reasoning:** `now` is time-relative text frozen into a dated artifact. Read in 2036, a row
labelled `now` is simply false - and "now" is the one horizon word this program prohibits
everywhere else, which made the contract the last place it survived.

It could not be fixed in v1 because v1 is immutable, and that is not an obstacle to route
around: an immutable contract plus an additive successor is *precisely* the mechanism for a
correction that arrives after publication.

**The cost, stated plainly rather than buried:** this is the one change in v2 that can break
a consumer, and it breaks quietly. A filter on `horizon_label == "now"` matches nothing in
v2, drops the baseline row, and raises no error - an empty result or a chart missing its
first column. `docs/migration-from-v3.md` leads with it and recommends filtering on
`horizon_year == 2026` instead, which did not change and never will.

**Rejected:**

| Alternative | Why it loses |
|---|---|
| **Leave `now` in v2 as well** | Carries a known-decaying label into the version that is supposed to be the good one, forever. |
| **Carry both `horizon_label` and `horizon_label_v1`** | A permanent duplicate column to spare consumers a one-line change, and two fields that must never disagree. |
| **Fix it in v1 and re-cut the hash chain** | Breaks the freeze, invalidates the pinned digest, and silently changes an artifact that published figures already quote. |

---

## DEC-010 - `model_version` stays `3.0.0` in contract v2

**Date:** 2026-07-27 · **Phase:** 4 · **Supersedes:** the first written v2 manifest, which
claimed `4.0.0` - caught during review and corrected before it left the branch.

The v2 manifest reports `model_version: 3.0.0`.

**Reasoning:** the contract version and the model version are different facts. v2 is a
*container* change - it adds fields for observations that do not exist yet. The numbers
inside it were produced by the V3 model, on rows that say `model_mode = milestone2_v3`.
Migrating them into a wider container did not re-run anything.

Stamping `4.0.0` on them would be a version claiming work that has not happened, which is the
same defect as a placeholder capacity presented as verified - one layer up, and harder to
notice, because nobody audits a version string.

`MODEL_VERSION_V4 = "4.0.0"` exists in `config.py` and is deliberately unused by any emitted
artifact. `test_v2_does_not_claim_model_version_4` fails if that changes.

**Rejected:** *bump to 4.0.0 because the work is called Phase 4.* The phase number is a plan;
the model version is a claim about output.

---

## DEC-011 - Missing data made a site look better; one fix at once, two more on 2026-10-17

**Date:** 2026-07-27 · **Phase:** 4 → 6B · **Found by:** the Phase 6B research fleet
(`wf_d029c874-d32`), **confirmed by execution before being acted on**, per the subagent
doctrine that every finding is a lead until reproduced against the actual files.

### The finding

Three places where absent or malformed input scores **better** than measured input - the
exact inverse of the principle the rest of this project enforces.

| # | Where | Behaviour | Live today? |
|---|---|---|---|
| 1 | `right_sizing.site_capacity_cap` | `parking_spaces <= 0` → cap **6**. A real 40-space lot → cap **2**. Absence allows **3× the ports** of measurement. | No |
| 2 | `scoring.INVERTED_DRIVERS` | `garage_enclosed`, `stormwater_risk` use `(1 - x)`; absent → `0.0` → term `1.0`, the **maximum**. A site with no stormwater assessment scores as though one was done and found no risk. | No |
| 3 | `scoring.yesno_to_num` | Returned `float(value)` for **any** number, unclamped. `7` on `fire_access_ok` contributed 7× its rubric weight. And `0.5` → `0.5` while `"0.5"` → `0.0`, so whether a CSV cell parsed as text or number changed the score. | No |

**None changes a published number.** All 12 real sites carry strictly `0`/`1` in every flag
and a positive `parking_spaces`, verified and pinned by a test. Every path is dormant on the
current inputs - and goes live the moment Phase 6B accepts a file nobody here prepared, which
is precisely what 6B is for.

### Decided: fix #3 now

It has no design ambiguity. A flag outside `{0, 1}` is invalid input, and the function's own
string branch has always been strictly binary - the numeric branch simply disagreed with it.
`yesno_to_num` now **refuses**, naming the field and the value.

**Refuses rather than clamps.** Clamping `7` to `1` would be a cleaner that silently improves
data - the thing this project exists not to do - and it would bury whatever produced a `7`.

### Deferred: #1 and #2 go to Phase 6B, pinned by tests meanwhile

Both need a decision with a **visible consequence for real users**, and neither has a
correct-by-inspection answer:

- **#1:** the conservative neutral (cap 2 on absence) lowers port targets for any
  jurisdiction that omits the column. That is a real cost imposed on a real user for a
  missing field.
- **#2:** the pessimistic neutral (`1`) asserts the *opposite* unverified claim - "this site
  **is** enclosed", "this site **does** have stormwater risk" - manufactured from the same
  absence. For `garage_enclosed` it also changes a user-visible review tier, which carries no
  ledger entry explaining why.

The honest alternative both share is to keep the permissive neutral and record the absence as
**coverage loss** feeding the existing confidence rubric - the model still runs, it just says
less, which is requirement 6B.4 in the owner's own words. That is the likely answer, and it
is a 6B decision because it only works once the completeness-to-confidence path exists.

`tests/test_absence_is_not_favourable.py` pins both as **known defects**. A test asserting a
defect is not an endorsement of it; it is how the defect stays visible until it is resolved.
Each carries an instruction: when it starts failing, that *is* the fix - update this entry and
delete the test rather than adjusting it.

**Rejected:** *fix all three now.* #1 and #2 would move scores for absent data under a design
nobody has chosen yet, and picking one silently is the same failure as the defect itself.

**Rejected:** *record them and write no test.* Three of this program's defects were found in
code that had been read and reasoned about but not exercised. An unpinned known defect is a
defect that gets rediscovered.

### Resolved 2026-10-17: absence earns no credit, in either direction

Decided under the owner's instruction to fix every finding of the 2026-10-17 audit (F-07,
F-08), and **not** the "likely answer" above. Keeping the permissive neutral and recording the
gap only as lost confidence leaves the ranking itself built on the gap: confidence is reported
beside the score, not inside it, so a site with no stormwater assessment would still outrank a
measured one. The rule now is that a value nobody recorded earns no credit:

| Where | Before | After |
|---|---|---|
| Absent yes/no (blank, `n/a`, `unknown`, ...) | `0.0`, "no" | NaN. Normal flags earn 0; the inverted `garage_enclosed` and `stormwater_risk` earn 0 too, instead of their maximum |
| Unrecognised yes/no text (`banana`, `partial`, `"0.5"`) | `0.0`, silently | Refused, naming the field |
| Inverted numeric drivers (existing ports, service distance, install cost, trenching) | Absent -> 0 -> `1 - 0`, the maximum | No credit. A total with an absent part (install cost, existing ports) is absent |
| Cohort-relative scaling | An absent value entered the range as 0 and moved every other site | Range taken over recorded values only |
| Numeric text (`"1,400"`, a typo) | Coerced to NaN, then 0, no record | Refused at scoring; intake reads thousands separators and reports each cell (F-07) |
| `site_capacity_cap` with no parking count | 6 | 2, the minimum (#1) |
| Unrecorded `public_access` | 0 at scoring, but 1 in right-sizing | Not public everywhere |
| Unrecorded `garage_enclosed` | Not enclosed | "High-review candidate": the review that tier asks for is exactly what an unknown enclosure needs |
| Absent `hours_open`, `avg_dwell_min` for port sizing | 0, which the queue read as a whole day's sessions in one hour | 8 h and 120 min, the defaults `right_sizing` already declared; no score credit |

Every scored output row now carries `absent_fields`, so a run says in its own rows which
inputs each site lacked.

**The costs, accepted:** a jurisdiction that omits a column gets a lower score and, for
parking, a smaller plan, until it supplies the field. Intake tells it so, cell by cell, before
anything runs. The pessimistic neutral #2 worried about - asserting "this site is enclosed" -
is avoided: the flag stays NaN in the output, and only the score and the tier treat it as
unproven.

**Published numbers: none moved.** All 12 real sites are complete. Measured: the v3 and
legacy runs before and after the change are text-identical in every output file except the
run stamps and the new, empty, `absent_fields` column.

`tests/test_absence_is_not_favourable.py` no longer pins known defects. It pins the rule,
including a property test that blanking any recorded value of any scored field at any site,
in both modes, never raises that site's score.

---

## DEC-012 - Charger efficiency: MATLAB follows Python, and the reconciliation that found it

**Date:** 2026-07-27 · **Phase:** 4 (task 4.8) · **Closes:** FIND-XMODEL-01

### The finding

`src/fcf_m2/config.py` has always declared `CHARGER_EFFICIENCY = 0.92`. Three MATLAB
functions - `makeSessionProfiles`, `electricalEconomics`, `runScenario` - defaulted
`ChargerEfficiency` to **0.93**. One physical assumption, two values, one model. Every MATLAB
energy figure came out `1/0.93` of the contract's rather than `1/0.92`: about **1.1 % high**.

### How it was found, because the method is the transferable part

Phase 4's task 4.8 is "MATLAB reconciliation against real MATLAB outputs". The reconciliation
was done rather than assumed: the pipeline was run on the **canonical** data and compared
against the contract field by field.

Identity reconciled perfectly - 120/120 on `scenario_id`, `site_id`, `horizon_year` and
`capacity_basis`. Energy did not. The gap was then **measured instead of explained away**: the
implied efficiency came out **0.9300** across all 120 rows (min 0.929141, max 0.930425, the
spread being the contract's two-decimal rounding). That is not a semantic difference between
delivered and grid energy. It is a disagreement about a constant.

### Why it survived this long

**Charger efficiency is not a contract field.** The canonical contract is precisely the
mechanism that prevents this class of drift - one number, one place, consumers quote and never
re-derive - and this quantity lived outside it. There was nothing to reconcile it against.
The drift was hiding in the one place the anti-drift mechanism does not reach.

### Decided

Python is the single producer (`data/contract/v1/README.md`), so **MATLAB follows it**: 0.93 →
0.92 in all three files. **No published number moves** - MATLAB output has never been
published, and Python's 0.92, from which every published emissions figure derives, is
unchanged.

`tests/test_cross_model_constants.py` parses the MATLAB sources for every numeric
`addParameter` default and compares the shared ones against `config.py`. `verify.sh` 17 → 18.
Mutation-tested: reverting any single file to 0.93 fails it.

**Three files, not one.** Two were found by grep; the third only by re-running the sweep after
fixing the first two. Finding one and stopping would have left two - and the two left would
have been the ones nobody looked at again.

### Rejected

| Alternative | Why it loses |
|---|---|
| **Change Python to 0.93** | Python is the single producer and every published emissions figure derives from its value. Moving it to match a downstream consumer inverts the contract's direction of authority and would change published numbers to fix a consumer's default. |
| **Add `charger_efficiency` to the contract so MATLAB reads it** | Better, and still the right destination - but contract v1 is frozen, so it belongs in v2 and then in the adapter CSV. Aligning the constants is the correct step now; carrying it in the contract is the durable fix and is recorded as open. |
| **Treat it as delivered-versus-grid semantics and document the ratio** | Tempting, and false. The ratio measured 0.9300, not a modelling difference. Documenting a disagreement as a convention is how a defect becomes permanent. |

### Left open, deliberately

`charger_efficiency` should become a **contract field** so MATLAB consumes it rather than
defaulting to a private copy - the same reasoning that put `grid_factor_value` in the contract.
Until then the test is the only thing holding the two in step, and a test is a weaker guarantee
than a value that exists once.

### The other half of task 4.8, stated plainly

**The reconciliation used GNU Octave, not MathWorks MATLAB, and that limitation is real.**
Real MATLAB runs only in the public harness, which must never carry the canonical data - so
real MATLAB has never seen the real sites and cannot until someone runs it on a licensed
machine with access to this repository.

What makes the Octave result usable as evidence, and only this far: Octave and real MATLAB
were cross-validated on a **structurally identical** fixture (same 22 columns, same order,
same vocabularies, same shape) at **2 640 cells, zero numeric divergence, 1e-9 tolerance**
(`MATLAB_LIBERATION.md` §3.7). So the 0.93 measurement reflects the model's arithmetic rather
than an Octave artefact. **It is not a MathWorks MATLAB result and nothing may present it as
one.**

---

## DEC-013 - The live Tableau workbook is wrong; publish a corrected one under a NEW name

**Date:** 2026-07-27 · **Phase:** 6 · **Decided by:** the project owner, asked directly
because the action is irreversible and outward-facing

### What the audit found

Phase 6.4 exists because *auditing the repository's own files never catches a stale published
viz*. It didn't. `EV_Charging_Site_Readiness_Workbook` - **1 097 views**, the project's
most-seen artifact - was downloaded, unpacked, and its Hyper extracts read directly. Three
superseded claims, each checked against the canonical run rather than inferred:

| # | Live on Tableau Public | Canonical | Severity |
|---|---|---|---|
| 1 | Horizons **2035 / 2050** | 2026 / 2036 / 2046 / 2056 | Retired V2 vocabulary |
| 2 | Data confidence **8 Medium, 4 Low** | **12 Low** | **Worst.** Overstates confidence to every viewer |
| 3 | Readiness from **legacy_v2** - FFX002 first at 58.8 | FFX004 first at 53.4 | **The top-ranked site is different** |

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
public display - the record of the defect - and reset a view count that is real evidence of
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
or hand-authored XML. Where a substitute shipped, the affected sheet's own subtitle names it "GROUPED bars, not the bar-in-bar", "NO REFERENCE LINE", "SYMBOL map, not a choropleth" -
and a test asserts those declarations are present, so a screenshot separated from this
repository still says what it is.

**An honest partial close, which the master prompt prefers to a fake complete one.**

---

## DEC-014 - Phase 10 gains a full line-by-line audit of the entire repository

**Date:** 2026-07-27 · **Raised by:** the project owner, mid-program · **Status:** logged before
any work began · **Phase:** 10, in addition to everything already planned there

### The requirement, in the owner's words

> *"Phase 10 should be a very meticulous audit of every single line in every single file in
> every single folder to make sure we are getting the full picture and are not missing
> anything - in addition to what was planned for phase 10."*

### Why this is not a repeat of Phase 0

Phase 0 read every line of the **inherited** repository: 229 files, twelve lanes, 224 files
read end to end, 200 findings. That read is what made the rest of the program possible.

It is also now **out of date by more than half the repository**. Measured, not estimated:

| | Phase 0 baseline | Now |
|---|---|---|
| Tracked files | 198 | **403** |
| Text lines | - | **~78 700** |

So the Phase 0 read covered code this program did not write, and roughly half of what exists
today has never been read end to end by anyone - it was *written*, which is a different thing.
Writing a file and auditing it are different activities with different failure modes, and this
program has already demonstrated the difference:

- A commit message claimed MATLAB artifacts were committed. They were not - `.gitignore`
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
2. **Dead and orphaned code.** Anything unreachable, unused, or superseded - including
   constants, gates and tests that no longer check what their name says.
3. **Gates that pass vacuously.** Four have already been caught (secret scan, link checker,
   CDN pin, capture-form test) plus the harness exposure gate that could not see CSVs. Every
   gate gets a deliberate mutation test or an explicit note saying why it cannot have one.

   **The specific recurring shape: a check that matches TEXT where it should match STRUCTURE.**
   Six instances so far, three of them in checks written during this program and two in my own
   tests within an hour of each other:

   | # | The check | What it matched instead |
   |---|---|---|
   | 1 | secret scanner | credential *names*, not values - flagged CI's own regex |
   | 2 | link checker | URLs inside fenced code blocks |
   | 3 | capture-form test | the page's own sentence "sets no cookie" as evidence it does |
   | 4 | CDN pin gate | nothing at all - passed with "0 checked, all pinned" |
   | 5 | harness exposure gate | code lines only; structurally could not see a CSV column |
   | 6 | banner test | the HTML comment *explaining* the banner is not dismissible |
   | 7 | stdlib test | the docstring sentence "No FastAPI, no Flask, no uvicorn" |

   The audit must look for this shape specifically: any check that does `substring in
   source_text` where the property is about structure, usage, or behaviour. The fix is always
   the same - parse it (AST, XML, CSV columns) or exercise it, never grep it.
4. **Numbers appearing anywhere that do not trace to the contract.** Reports, presentation,
   docs, website copy, figure captions.
5. **Anything gitignored that is load-bearing**, and anything tracked that should not be.
6. **Every stated limitation still true**, and every limitation that exists but is not stated.
7. **Secrets, credentials, account identifiers** in anything tracked or shipped.
8. **Files nobody has looked at since they were generated** - the artifacts most likely to
   have quietly drifted.

### How it will run

By fan-out, in non-overlapping lanes with an independent coverage verifier, the way Phase 0
did - that pattern found 200 findings and its verifier reported zero gaps across 20+ probes.
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

## DEC-015 - The platform is a Python-native local server, not a packaged native shell

**Date:** 2026-07-27 · **Phase:** 7 · **Basis:**
[`PHASE_7_PLATFORM_BRIEF.md`](PHASE_7_PLATFORM_BRIEF.md) - a 10-agent design panel: four
independent architectures, each adversarially challenged, then synthesised.

### The decision

`python -m fcf_m2.server` serves the one bundle `site/platform/` on loopback and adds `/api/*`
for execution. **The same directory, byte for byte, is deployed to S3 + CloudFront as the web
tier.** No Rust, no Electron, no bundled Chromium, no second frontend.

**Why:** it is the only architecture where *"one shell, two tiers"* is a property of the
**deployment** rather than a promise a build flag has to keep. The two tiers are literally the
same five files, and the tier is *detected* by asking whether `/api/operations` answers - not
compiled in. Every other angle adds a layer whose only real job is to open a window onto a
page that already exists, and each such layer is a place the tiers can drift.

### Why the other three lost - the real trades, not strawmen

**Tauri + Rust.** The strongest on size and genuinely correct that an embedded CPython can run
the model with no user Python at all - the adversarial pass proved that end to end, with all
seven contract files byte-identical. But after correction, **the Rust layer's entire remaining
job is "spawn `fcf_m2.server` and open a WebView"** - the sidecar it spawns *is* the
architecture chosen here. It costs a language nobody in this repo writes, a second
cross-platform build matrix, ~180 MiB of embedded runtime, and it runs straight into the
boundary problem below.

**Electron.** Wins one real argument: the 3D surface is CesiumJS WebGL2, and Electron
guarantees the desktop renderer is the same engine as the web tier's, where Tauri gives you
WKWebView on macOS and WebView2 on Windows with no cross-browser harness in this repo to catch
a divergence. It loses on ~279 MiB of bundled Chromium - about half the installed bundle - on
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
server, and tier detection. The panel - which read the tree rather than the prompt, and
corrected the prompt's claim that nothing was built - landed on the architecture those
components already assume. **Building the shell-independent spine before choosing the shell
was the right call**, and would still have been if the panel had chosen Tauri, because in that
design the sidecar is this same server.

### OPEN QUESTION FOR THE OWNER - not the assistant's to decide

**A downloadable installer that can genuinely *run* the model must carry
`data/inputs/real_sites_v2.csv`** - facility-level electrical and occupancy data for twelve
named public buildings - **out of a repository that is private and stays private.**

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

## DEC-016 - A public installer carries synthetic inputs; the real site data stays private

**Date:** 2026-07-27 · **Phase:** 7/8 · **Resolves the open question in DEC-015**

### Context

DEC-015 raised it: a downloadable installer that can genuinely *run* the model must carry
`data/inputs/real_sites_v2.csv` - facility-level electrical and occupancy data for twelve
named public buildings - out of a repository that stays private.

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
   pattern were published. That conversation has not happened - it is not even on the open
   human actions list.
2. **It is the one action here with no undo.** Everything else this program has done is
   revertible. Publishing twelve real facilities' electrical characteristics is not.
3. **The instruction was ambiguous and the owner explicitly allowed deferral.** "Do whatever
   you think is best, and it does not have to be now" is permission to choose the cautious
   option, not pressure to act.

**What is lost by holding: almost nothing.** A synthetic installer demonstrates the model end
to end - every screen, every operation, the whole provenance panel. What it cannot do is make
a claim about a real site, which is a claim the study cannot support anyway: capacity is a
placeholder at all twelve.

**The precedent already exists and works.** The public MATLAB harness runs on
`harness_scenarios_synthetic.csv` for exactly this reason, and that decision has since caught
a real leak (`sessions_per_day = 0.9`, which was PWC003's value) - evidence that the synthetic
boundary is doing work rather than being ceremony.

### What ships

| Surface | Data | Status |
|---|---|---|
| Web tier (public) | contract **outputs** only - already public in the reports and on the site | ships |
| Desktop tier, from a clone | the real inputs | works for anyone with repository access, which is the team |
| Public installer | **synthetic inputs**, labelled | when built |
| Real input file | - | **stays private** |

### Left open, deliberately, for the owner

Declassification remains available and nothing here forecloses it. If it is wanted, the
sequence is: **ask the two jurisdictions' facilities contacts first**, then publish, then
rebuild the installer against the real inputs. Recorded as an open human action rather than
an assistant decision, because that is what it is.

### Also decided: no Cesium ion token

The owner offered one. **Declined**, for three reasons that all point the same way:

- the master prompt requires the explorer work **with no Cesium account**, and Phase 3 already
  achieved that;
- a token in the web tier would be **visible in the deployed JavaScript** - a credential in a
  public artifact, which the standing rule forbids outright;
- ion usage above the free tier is a **recurring cost** against a $10/month ceiling.

If ion terrain is wanted later, the clean route is a domain-restricted token injected at
deploy time and never committed. That is a Phase 8 decision with its own entry, not something
to wire in now.

---

## DEC-017 - The web platform is gated at the edge, not in the browser

**Date:** 2026-07-27 · **Phase:** 8 · **Requested by the owner, approved before implementation**

### Context

The owner asked for the deployed platform to sit behind a Cognito sign-in, granting access to
an existing user (granted account 1), and asked whether it could be done without
them at the machine. Both were answered before any work started; the owner replied
*"good i approve"*. (Login identities in this file were replaced with role labels on 2026-10-17; the accounts themselves are listed only in the untracked `infra/edge-auth/granted.mjs`.)

Reconnaissance established four facts that shaped the design, each verified rather than
assumed:

1. **The user already exists and is `CONFIRMED`** in pool `us-east-1_mKrwfQTkg`. Its password
   is already set. No credential has to be created, reset, or handled - which is fortunate,
   because handling one is forbidden.
2. **The Cognito hosted-UI domain is already `ACTIVE`** (`us-east-1mkrwfqtkg`), and a **public
   app client with no secret** already uses the authorisation-code flow on this very site.
3. **The distribution serving the platform also serves the NFC layer.** `E1XZPHWHZV0OEO` has
   exactly one origin, *zero* extra cache behaviours, and the alias
   `futurecityfellowship.andyyaro.com`. `/t/FFX001`–`/t/PWC008` live on its default behaviour.
4. **The site's existing client-side sign-in is correct for what it protects, and is not a
   model for this.** An anonymous `GET /assistant.html` does return HTTP 200 and all 70 378
   bytes - but the prose in those bytes is 1 677 characters of login form, no site data, and
   the asset it guards is an API (`POST .../chat`) which answers an unauthenticated call with
   **HTTP 401**. A publicly served login page in front of a server-enforced API is the normal,
   correct shape.

   *(Recorded because the first version of this entry claimed the opposite. The initial
   measurement failed to strip `<style>` blocks and counted 26 400 characters of CSS as
   leaked prose, and the API was asserted to be unprotected without being called. Both were
   wrong; the API was then called and returned 401. The error is left visible here rather than
   quietly deleted, because a decision log that hides its own corrections is worth less than
   one that shows them.)*

5. **The granted user has no `email_verified` attribute at all** - `admin-get-user` returns
   only `email` and `sub`. This matters more than it looks: the textbook identity check is
   `email_verified === true`, and requiring it here would have produced a gate that could
   never open for the one account it exists to admit. The failure would have been invisible
   from this side, because verifying it requires signing in as that user. The allowlist
   therefore matches on **`sub`** - immutable, and the tightest possible identifier for
   "that user specifically" - *and* on `email`, with `email_verified` deliberately not
   required. See the authoriser's own comment for the same reasoning at the point of use.

### The decision

**Authentication runs in a Lambda@Edge viewer-request function attached to a new
`/platform/*` cache behaviour. The default behaviour is not touched.**

Three properties follow, and each is the reason for a constraint the owner did not ask for:

- **The NFC layer stays public.** A reader taps a coin in a car park and gets a page, with no
  account and no app - that is the whole point of Phase 5 (DEC-006). Gating the distribution
  would have broken all twelve tags. Auth is therefore scoped to one path pattern, and the
  verification step checks the tags still answer, not merely that the gate closed.
- **The gate is real, and it has to be, because this asset has no server behind it.** This is
  where the platform differs in kind from `assistant.html`. That page can gate in the browser
  because the thing worth protecting is an API that enforces auth itself; the page is just a
  door, and doors are meant to be visible. The platform is the opposite: it is a **static
  bundle**, so the bytes *are* the asset and there is no server-side chokepoint to enforce
  anything. A client-side gate over static files cannot protect them - it can only hide what
  CloudFront has already handed over. Enforcement therefore has to move to the edge.
  Viewer-request runs on every request *before* the cache is consulted, so an unauthenticated
  caller never reaches a byte, cached or not.
- **No secret exists anywhere.** The app client is **public and uses PKCE**, so there is no
  client secret to store; the session cookie holds the Cognito `id_token`, verified on each
  request against the pool's **public** JWKS. Nothing needs SSM, and nothing needs the
  environment variables Lambda@Edge does not support. The standing rule - never embed a
  credential in the app, installer, frontend, or any release artifact - is satisfied by
  construction rather than by care.

### Alternatives rejected

| Option | Why not |
|---|---|
| Client-side Cognito, as `assistant.html` does | Right shape for that page, wrong shape here. It works there because an API enforces auth server-side; the platform is static, so there is nothing behind the page to enforce anything, and hiding delivered bytes with JavaScript is not access control. |
| Application Load Balancer with built-in OIDC | ~**$16/month** at on-demand rates for the ALB alone. Exceeds the entire $10/month ceiling for one feature. |
| CloudFront Function instead of Lambda@Edge | Cannot perform RS256 verification or the token exchange - no network calls, restricted runtime. It would have to trust the cookie, which is not verification. |
| CloudFront signed cookies / signed URLs | Real gating, but unrelated to Cognito; the owner asked for a Cognito sign-in by that user specifically. |
| Gate the whole distribution | Breaks all twelve NFC tags. Not a trade-off - a regression. |

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

**That the gate opens for granted account 1.** Confirming it requires signing in as
that user, and that password is neither available to nor appropriate for the assistant to
hold. What *is* verified: an anonymous request is refused, and the NFC tags still answer.
The remaining check is one sign-in by the owner, recorded as an open human action.

### What the adversarial review changed, and the one it changed most

Six independent attack lenses were run against the authoriser before it was deployed, each
finding then put to two refuters. Eight claims came back. Treated as leads, not facts - every
one was checked against the file by hand. Four survived that check and were fixed; the rest
were either already fixed or not exploitable.

| Claim | Verdict | Outcome |
|---|---|---|
| Reflected XSS via Cognito's `error` parameter | **Real** | Already found and fixed while writing the tests, independently - two lenses converged on it. Escaping is now centralised in `escapeHtml` so no call site has to remember. |
| Percent-encoded path evades the cache behaviour | **Real risk, unresolvable by inspection** | See below - the architecture changed. |
| Sibling-subdomain cookie shadowing → permanent lockout | **Real** | Cookies now carry the `__Host-` prefix, which a browser only accepts from the exact host. |
| Authorization-code injection via a forgeable PKCE stash | **Real, same root cause** | Closed by the same `__Host-` change: the stash can no longer be planted by another subdomain. |
| Forced sign-out via `<img src=…/logout>` | **Real, low impact** | Sign-out now requires `Sec-Fetch-Dest: document`, so a subresource cannot clear the session. |

**The one that changed the design.** A cache behaviour is chosen by matching the path against
`/platform*`, and CloudFront normalises percent-encoding - *measured on the live distribution,
not assumed*: `/%61ssistant.html` returns the same 70 378 bytes as `/assistant.html`. If
pattern matching happens **before** normalisation, `/%70latform/index.html` would miss the
gated behaviour and be served by the default one, with no authentication at all. Which of
those two internal steps runs first is not something inspection can settle.

So the design stopped depending on the answer. **The platform bundle now lives in its own
bucket**, reachable only through the gated behaviour. A request that evades the path pattern
falls to the default behaviour, whose origin is the main bucket - which contains no platform
content, and returns 404. The guarantee moves from behavioural to structural, the same move
this program already made when it decided an operation *is* a CLI command rather than merely
matches one.

Incremental cost of the second bucket at 25 MB: roughly **$0.0006/month**.

*Honest note on the review itself: the workflow reported "0 findings" because a bug in the
orchestration script passed promises where it should have passed functions, so every
refutation threw and the results were discarded. The empty result was not a clean bill of
health, and was not reported as one - the agents' raw output was read from the run journal
instead. A green result whose plumbing failed is indistinguishable from a real one unless the
plumbing is checked.*

### Post-deployment defect: the gate worked and the sign-in page did not exist

Reported by the owner within minutes of the deployment being called verified:
`/platform/` redirected to Cognito, and Cognito answered
**"Login pages unavailable · Please contact an administrator."**

**Cause.** This pool runs **Managed Login version 2**, under which *every app client needs its
own branding record*. A client without one does not fall back to a default page - it has no
sign-in page at all. The newly created `future-city-platform-edge` client had none. Nothing in
the app client's own configuration hints at this; the existing `future-city-assistant-web`
client had a branding record (`50b10138-…`) and so had never exposed the gap, and the site's
other sign-in never used the hosted UI at all.

**Fix.** `create-managed-login-branding --use-cognito-provided-values`, now performed by
`deploy_platform.py` so a rebuild cannot omit it.

**The real lesson, which is about the verification and not the bug.** Every one of the 32
assertions passed while the feature was unusable, because they asserted *the gate redirects to
Cognito* - and it did. That is a strictly weaker claim than *a person can reach a sign-in
form*, and the weaker claim is the one that was checked. The verifier now **follows the
redirect** and asserts a real password field renders. This is the same failure as the two
blank Tableau sheets: verifying the step this program controls rather than the outcome the
reader experiences.

It also lands squarely on the caveat published alongside the deployment - that whether anything
*behind* the redirect worked was explicitly unverified. The caveat was correct, and being
correct about an unverified thing is not the same as it working.

**Ninth text-versus-meaning trap, caught this time.** The first check for the fix searched the
returned page for "unavailable" and reported it still present. It was: Cognito ships its entire
localisation table, including the string `"Login pages unavailable"` itself, inside a
`<script>` on *every* page - including the working one. The reliable signal is the presence of
a `type="password"` input. Had that grep been trusted, a working fix would have been reported
as broken.

### Access widened to a second account, and why the first one alone was not workable

Granted account 1 is `CONFIRMED` and enabled, so it has a
password. The owner reported never receiving a sign-in email and asked whether the email might
simply have been sent earlier, when the account was first added. **CloudTrail settles it, and
the answer is neither "sent earlier" nor the mechanism first inferred here:**

| Evidence | Finding |
|---|---|
| `AdminCreateUser`, 2026-07-09T23:38:48Z | **`messageAction: SUPPRESS`** - the invitation email was explicitly suppressed. Cognito has never sent mail to this address. |
| `AdminSetUserPassword` | **No events.** The password was not set by an admin call. |
| `RespondToAuthChallenge` ×3, same day | The `NEW_PASSWORD_REQUIRED` challenge was completed in a browser ~50 s after creation - whoever set the account up held the temporary password out of band, which is precisely why they suppressed the email. |

So the credential exists and was chosen by whoever performed that setup. **No email was ever
sent, and none could have been**: the assistant did not create the account and deliberately did
not touch its credential.

*(An earlier version of this entry said the password was set "thirty-nine seconds" after
creation and implied an admin-set. Both were wrong - the gap is ~50 seconds and it was a
browser challenge response. The numbers were read off two timestamps rather than checked
against the audit log, which was available the whole time.)*

**The second problem, which the first was hiding.** The account carried **no `email_verified`
attribute**, and this pool's recovery mechanisms are `verified_email` then
`verified_phone_number`. *"Forgot your password?" could not have delivered either.* The
missing attribute had already been noticed while building the allowlist and designed around
for **authorisation**; what was missed is that the same gap also breaks **recovery**. One
fact, two consequences, only one of them followed through.

**Still unproven: that the mailbox receives anything.** Because delivery was suppressed at
creation and never attempted since, granted account 1 has never been sent a message
by this pool. Setting `email_verified` makes Cognito *willing* to send a reset there; it is not
evidence that anything arrives.

At the owner's direction, both routes were opened:

1. **`email_verified` set to `true`** on granted account 1. This is a verification
   flag, not a credential - it lets the owner run a self-service reset in which the password
   travels from Cognito to their mailbox and is never seen by the assistant.
2. **Granted account 2 added to the allowlist.** It already existed in the same pool with
   credentials the owner holds. Widening access beyond the single account originally specified
   was the owner's explicit decision, recorded here because it changes who can read the study.

A third pool member is in the same pool and is **not** granted - a test asserts that a valid
pool member who is not allowlisted is still refused, because being able to authenticate is not
the same as being authorised.

A further test asserts that one account's `sub` paired with the other's email is **refused**.
With a single entry that was hypothetical; with two it is a real shape, and an allowlist that
checked the two fields independently would admit a token that mixes two genuine accounts.

**A guard that cried wolf.** The redeploy was refused by `assert_safe_change` with "existing
origin platform-gated was modified" - the guard treated *every* pre-existing origin as
untouchable, including the one the script itself owns and rewrites on every run. So it fired
on the second deploy of an unchanged configuration. That is worse than not having it: a check
that fails every time teaches the operator to skip it, and the genuine signal - *someone
else's* origin moved - drowns. Now exempted, with the platform origin still asserted to point
at the isolated bucket. **Lambda version 2 was published while this fired, and CloudFront was
never updated to use it**, so for a few minutes the newly published code was live nowhere. The
failure was safe, which is the point, but it was not free.

---

## DEC-018 - Blank attribution was silently accepted as the string "nan"

**Date:** 2026-07-27 · **Phase:** 7 · **Severity: the V4 loop's central guarantee, defeated
since it was written**

### What was wrong

`CapacityObservation.__post_init__` refuses an observation whose `source_document` or
`observer` is blank. The comment above it is explicit about why: *"An unattributed observation
cannot upgrade anything, so it is refused at the door rather than accepted and quietly ignored
later."*

**That refusal never fired.** pandas reads a blank CSV cell as `NaN`, and
`read_capacity_observations` did `str(row["source_document"]).strip()` - so `NaN` reached the
check as the four-character string `'nan'`. Non-empty. Check passes.

The consequence, reproduced before the fix:

```
implied_basis   = 'verified_utility'      <- the strongest basis available
capacity_source = 'verified_utility via utility_load_study: nan (Dominion Energy),
                   recorded by nan on 2026-07-01'
```

A row naming **no document and no observer** was accepted, and claimed the strongest possible
provenance. `capacity_basis` becoming `verified_utility` is exactly the condition the
fail-closed capacity guard tests for before it will emit a feasibility claim. So the guard -
this project's most-cited safeguard - could have been satisfied by a blank spreadsheet cell.

Nothing had ever been observed to fail, because nothing had ever submitted a blank cell: the
only capacity data in the repository is a hand-made fixture with every field populated.

### How it was found

**By a disagreement, not by looking for it.** A parity test was written to check that the new
browser entry form never accepts what the model rejects. It reported the opposite of the
expected failure: the *form* refused the blank row and the *model* took it. The test was built
to catch a permissive form and instead caught a permissive model.

This is the argument for cross-checking two independent implementations of the same rule. A
test written against `observed.py` alone would have encoded the same assumption the code makes that a blank cell arrives blank - and passed.

### The fix

`_as_text()` at the CSV boundary: a missing, `NaN`, or whitespace-only cell becomes `""`,
never `"nan"`. Applied to **every** text column in both readers, not only the two that were
checked - `source_org` had the same hole and would have printed `nan` inside the provenance
string that travels into the contract, which reads as a fabricated source.

Two further refusals were added while in there, both the same class of defect:

- **A capacity observation with no `site_id` is refused.** Unchecked it did not error -
  `resolve_capacity` groups by `site_id`, so it created a phantom site keyed on the empty
  string whose confirmed capacity belonged to nowhere.
- **Same for session observations.**

### Gates

- `tests/test_observed.py` - six regression tests, including one asserting that **no** text
  field can arrive as `'nan'`, so the general form of the bug is closed rather than the two
  instances that were noticed.
- `verify.sh` gate 30 - the form/model parity check that found it.

### What this says about the other refusals in this codebase

This program has repeatedly relied on the argument *"the code refuses it, therefore it cannot
happen."* This is a case where the refusal existed, was correct, was well-commented, was
covered by tests that constructed the dataclass **directly** - and was unreachable through the
path real data actually takes. **A guard is only as good as the boundary conversion in front
of it**, and the tests were aimed at the guard rather than at the boundary. That belongs in the
Phase 10 audit's brief: for every refusal, ask what the value looks like when it *arrives*, not
what it looks like in the test that constructs it.

---

## DEC-019 - The website embedded a workbook that had been deleted, and nobody traced the dependency

**Date:** 2026-07-27 · **Phase:** 8.3 · **Raised by the owner**

### What happened

DEC-013 found the live Tableau workbook wrong on three counts, a corrected workbook was
published under a **new name**, and the original was deleted - an open human action the owner
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
A status-code check distinguishes nothing. The difference is only visible in the *final URL* -
`/app/resource-not-found` versus the real view path. Any future check must follow the redirect
and read where it lands.

### Why it was not a find-and-replace

The deleted workbook had **12** sheets; the canonical one has **7**, and they are different
analyses. Four map cleanly. The rest - review burden, per-dimension subscores, profile
readiness, rank stability - come from the **old scoring model**, whose fields the canonical
contract does not carry. Rebuilding them would mean inventing the numbers underneath, so they
were removed rather than faked or quietly pointed at some unrelated chart.

The owner's instruction was *"I do not really care about the old ones… we can replace the old
ones placeholder with the current ones"*, with `dashboard.html` to keep **fewer, larger
charts** and the 3D rotating gallery on `results.html` left alone (it is images, unaffected).

### The part that was actual work

Every embed sits in a slide with a title, tab labels and explanatory copy describing *that
specific old chart*. Swapping only the URLs would have left the page describing charts it no
longer shows - **replacing a broken embed with a false one, which is worse**. So each slide's
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
   "Part N" markup, so a sequential walk counted them as slides and shifted every real one -
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
resource the repository or the live site references, checking that each still resolves - by
following redirects, not by trusting a status code.

---

## DEC-020 - The synthetic input set, and what "synthetic" turned out to mean

**Date:** 2026-07-28 · **Phase:** 8.4 · **Owner's decision: "build a synthetic site-input set"**

### What was blocking

DEC-016 required a public installer to ship synthetic inputs rather than the twelve real
facilities' data. The set was never built, which made the public installer **unbuildable**
rather than merely undone - `workflow.py` cannot start without a site table, so a public
artifact could only leak the real data or fail to run.

### It was never one file

`_load_inputs()` reads **four** site-keyed inputs. Building only the sites table would have
left three others pointing at real sites. All four are generated.

### Substituting the inputs was nowhere near sufficient

The first artifact had its four inputs correctly replaced - and still shipped **36 distinct
real facility identifiers across 87 files**: model outputs under `data/outputs`, the test
fixtures, the NFC placement cards and tag payloads, the contract, and the docs. The real site
identities are woven through everything the study has ever produced.

So a public artifact carries **no derived results at all** - the model, the synthetic inputs,
and nothing else. `src/` and `data/anchors/` were verified to contain zero real identifiers;
five scripts do contain them and are excluded by allowlist rather than by hope. The builder
then **opens the finished archive, proves no real identifier is present, and deletes it if one
is** - because a leaking artifact that exists on disk is one command from being attached to a
release.

**This is why the requirement says to verify by inspecting the built package.** Every
substitution was correct and the artifact still leaked.

### Three refusals from the model itself, each of which improved the result

The synthetic set did not work first time, and every failure was the codebase declining to
accept something it should decline:

1. **`unknown source_class values: ['synthetic']`.** The confidence system rejected an
   invented vocabulary term. It already had `synthetic_model`, worth 30 - below
   `planning_assumption` (35), above `unconfirmed` (15) - which is exactly the right weight for
   invented data. The model knew the answer; the fixture had to use its vocabulary.
2. **`RT-04: baseline starter total 24 != 25`.** The golden-baseline rule asserts the real
   study's accepted totals. A synthetic run cannot reproduce them and **must not be tuned until
   it does** - that would encode real results inside data labelled invented, which is both a
   false label and a leak. The rule now applies unless the run proves itself synthetic, and
   the test is `all` provenance rows, not `any`: a mixed run gets the strict check.
3. **`'SYN011' does not match '^(FFX|PWC)[0-9]{3}$'`.** The schema is widened for provably
   synthetic runs rather than relaxed. Making synthetic ids match the real pattern would have
   satisfied the validator by making invented data indistinguishable from the study's - the
   opposite of what a fixture is for. `jurisdiction_for("SYN…")` returns `synthetic`, never
   `fairfax` or `pwc`.

**The real run still produces exactly 25 / 48**, verified after each change.

### The overclaim, and the review that caught it

The first version of this generator stated: *"Nothing here is derived from the real files. Not
copied, not perturbed, not sampled, not fitted to their distributions."*

**That was false**, and false in the way overclaims usually are - broadly true, precisely
wrong, and contradicted by a comment twelve lines below reading *"Copied verbatim from the real
file."* An adversarial review (five attack angles, findings independently reproduced)
established:

| Claimed clean | Actually |
|---|---|
| Nothing fitted to real distributions | `avg_dwell_min`, arrival hours, spare-capacity placeholders, EV-share and risk points were drawn from `rng.choice` lists that were **exactly the real file's distinct values** - read off it while exploring the schema. That publishes the precise set of values in use across the twelve real facilities. |
| Nothing copied | Two risk free-text strings were verbatim; twelve columns are verbatim constants. |
| "A county that does not exist" | Every row still carried `state = VA`. |

All fixed: the support sets now share no member with the real ones, the risk strings are
reworded, the state code is `ZZ`.

### What is shared, deliberately, and why none of it identifies a site

"Zero overlap" is neither achievable nor desirable - a synthetic set must share the schema to
be usable. What is shared: **schema vocabularies** (`site_type`, the seven provenance field
groups) because the model cannot parse the file otherwise; **boolean and small-integer
domains** (`public_access` is 0 or 1; twelve ranks are 1..12) because that is arithmetic; the
**study's uniform conventions** (480 V, $150/ft trenching, the safety-review flags), each a
single fact true of every site equally and therefore separating none of them; and the
**electrical placeholders**.

The placeholders are load-bearing. `elec_service_rating_amp = 0` and `spare_capacity_kw = 0`
are what make `capacity_basis` come out `placeholder` at every site. A fixture that invented
capacity would make a synthetic run report **more** confidence than the real study - the one
direction a fixture must never move.

### Result

The public artifact is **0.1 MB, 44 files**, verified free of all 36 real identifiers, and the
model runs from a clean extraction: `starter_total_2026: 24`, `pathway_total: 42`,
`high_confidence_sites: 0`, capacity placeholder at 12/12. Different data, different answer,
honestly labelled - and the contract it writes declares `synthetic_inputs: true` and
`legacy_totals_checked: false` in its own manifest, so a directory that travels cannot be
quoted as the study's numbers.

---

## DEC-021 - Intake: the two ways a cleaner lies, and what stops each

**Date:** 2026-07-28 · **Phase:** 6B · **Implements DEC-000**

### What was blocking

`workflow._load_inputs` is five bare `pd.read_csv` calls, and `scoring.enrich_and_score` indexes
27 columns directly - so a file missing one raises `KeyError: 'aadt_nearest'`, measured. Column
names, units and coordinate frame are those of one Northern Virginia study. That is what makes
this a study rather than a product.

### The design in one line

Intake **proposes**; a human sees every finding **before** anything runs; `apply()` materialises
only an accepted proposal and refuses one carrying a refusal. Separating the two is the whole
point - a user who cannot see what a mapping decided before it runs is being asked to trust a
black box with the provenance of every number downstream.

### The two ways a cleaner lies

**1. It fills gaps.** The tempting behaviour is to substitute a regional average for a missing
traffic count. The run then succeeds, the site gets a demand score, and *nothing downstream can
distinguish that score from one built on real data*. The file's apparent quality rose; its
actual quality did not. So an absent field **stays absent**, is scored as an absence, lowers
confidence, and reaches provenance as `source_class = missing` - never omitted, because a field
left out of the provenance table scores as though it was never expected, which makes an
incomplete file look exactly as trustworthy as a complete one.

**2. It guesses.** A column matched below the confidence floor is reported **unmapped**, not
mapped hopefully. An absence is scored and visible; a wrong mapping is a wrong number with no
trace.

### Two refusals, deliberately not solved

**Projected coordinates are refused, not reprojected.** Doing it properly means `pyproj`; doing
it by hand would move every site by an amount nobody could check, and is a transformation that
cannot be explained in one sentence. Adding the dependency is its own decision (DEC-000's open
question), not something to smuggle in here.

**Duplicate or absent site identifiers are refused.** Two different places scored as one site is
not a degraded answer, it is a wrong one.

### The mistake this phase made, which is the mistake it exists to prevent

Acceptance was first built to upgrade `source_class` from `unconfirmed` to
`public_web_reference`. Measured consequence:

| | score | level |
|---|---|---|
| messy third-party file, mapping accepted | **58.5** | **Medium** |
| the real Northern Virginia study | **33.8** | Low |

**Guessed data outranked measured data.** The error was conflating two different things:
accepting a proposal confirms *that `staff` means `employees_day`*, and says nothing whatever
about whether that staff count is accurate or where it came from. `accept()` now clears the
**mapping** uncertainty only - `verification_status` becomes `reviewed`, `unresolved_flag`
clears for mapped fields - and `source_class` does not move, because intake has no knowledge of
the jurisdiction's own provenance and inventing one would be exactly the silent improvement
DEC-000 forbids. A jurisdiction wanting a higher rating must supply provenance for its own
figures; there is no path to one through this function.

Ordering is now ingested **0.0** → accepted **18.0** → real study **33.8**, and a test fails if
guessed data ever outranks measured data again.

### A second bug, and why the correct answer was the dangerous part

Provenance was first grouped using `provenance.FIELD_GROUP_FOR_COLUMN`, which is keyed on the
*contract output* columns and knows **3 of the 32 input fields**. The other 29 defaulted into
`site_use_and_demand`, which then inherited `missing` from the one genuinely absent field and
scored 0, while four other groups scored 0 for containing no fields at all.

The overall verdict came out **"Low"** - which is correct. It was correct **by accident**, and
an accidentally-correct answer is worse than a wrong one because nothing prompts anyone to look
again. Intake now has its own input-field map, and a test asserts every canonical field is
grouped.

### Gate

`verify.sh` gate 38. A deliberately messy fixture - 31 non-canonical column names, hours where
the model wants minutes, metres where it wants feet, one field absent - runs end to end and
produces a correctly-degraded rating. Correctly-degraded means neither easy answer: **not a
refusal, and not a confident number.**

---

## DEC-022 - On laptop and desktop screens, the site shows no disclaimer band and no vintage footer

**Date:** 2026-10-15 · **Decided by:** the project owner, on the day of a live presentation

### The decision

On screens 761 px and wider, the top authority disclaimer (`.fcf-authority`) and the bottom
source-vintage footer (`.fcf-vintage`) are hidden on every public page. Phones keep both, in the
quiet style adopted the same day. The markup stays on every page, so the text is still in the
source, in search snippets and for assistive technology that reads hidden content.

### What it does not change

- The results page keeps its red capacity caveat (`fcf-capacity-caveat`) and its mode note
  (`fcf-mode-note`) directly above the rankings, at every width. The owner was asked about the
  top and bottom banners only.
- The repository, reports and assistant still state that capacity is a placeholder at all
  twelve sites.

### Recorded rather than smoothed over

This reverses the reasoning in Phase 9, which added the capacity sentence to every page because
"it is cheap to state everywhere and expensive to omit anywhere". On a laptop, a visitor who
lands on the home page and leaves no longer sees it. That is a deliberate trade the owner made
for the presentation, and it is written down here so a later reader does not mistake it for a
regression.

### Gates

`www_visibility.test.mjs` now asserts the banners are visible and uncovered **at phone width**,
and adds one test per page asserting they are **hidden at 1440 px with the markup present**.
Mutation-tested: those desktop tests fail 4 / 4 against the pre-change production pages.

---

## DEC-023 - Another jurisdiction's sites run end to end, and are held to their own numbers

**Date:** 2026-10-17 · **Phase:** 6B · **Closes audit findings F-18, F-06, F-07, F-25** · **Builds
on DEC-011, DEC-021**

### What was blocking

`workflow.run` read four fixed files and the CLI had no way to name others, so the only way to
run another jurisdiction was to overwrite the reference study's inputs. Measured on a six-site
cohort in another city's shape, that failed twice (F-18): `KeyError: 'LIB-01'`, because MATLAB
site meta was required for every site, and, once that file was fabricated, `RT-04: baseline
starter total 12 != 25`, because the reference study's golden totals were asserted against
every non-synthetic run (F-06). Intake's output fed nothing but a confidence preview, and a
`1,400` or an `n/a` in a cell became 0 with no record (F-07).

### The decision

1. **A cohort is a directory.** `sites.csv` is required; `electrical_risk.csv`, `site_meta.csv`,
   `provenance.csv` and `cohort.json` are optional. A missing one is replaced by a default that
   invents nothing (every site `medium` risk, arrivals from 08:00, base load **unknown**,
   provenance `unconfirmed`), and every default used is a sentence in the run summary and the
   contract manifest. `intake FILE --out DIR --accept` writes one; without `--accept` it writes
   nothing, and it never overwrites a cohort.
2. **RT-04 keys on the inputs, not on how they arrived.** The 25 / 48 totals are asserted when
   a run reads the reference study's own files, identified by digest
   (`contract.REFERENCE_INPUTS`), and on no other cohort. A test pins those digests to the
   files, so editing a real input fails loudly instead of quietly switching the check off.
3. **A cohort's port plan follows the ranking its results show.** The reference study keeps its
   accepted cohort-relative (legacy) ranking (PY-02), which is what reconciles 25 / 48; on the
   fixed-anchor ranking the same rules give 25 / 47, now disclosed (F-05). A new cohort has no
   accepted baseline, and the legacy ranking is the volatile one v3 replaced. Measured on the
   worked example: planned on the legacy ranking, `EXC-03`, which the results call Tier 3, got
   an "install now" plan described as a strong ranking and 8 pathway ports; the plan totals
   were 12 / 24. On the fixed-anchor ranking they are 12 / 15, and each plan follows the rank
   and tier its site has in the results. The manifest records `cohort.plan_ranking`.
4. **A site missing a cost input gets no cost figures.** Costed with the gap as 0, it would
   look cheaper than a site that was measured.
5. **Reference-study text stays with the reference study.** On a cohort the standards register
   counts its own sites instead of claiming "battery_storage_flag=0 at all 12 sites", and names
   the permitting authority generically instead of as Fairfax City / PWC. The constants that
   remain the reference region's (Virginia's code editions, the SRVC grid factor, the screening
   tariff) are named in the manifest's `cohort.notes`.
6. **Intake reads every cell and says which ones it could not** (F-07). Thousands separators
   and a dollar sign are read with a note; blanks and `n/a`-style text are absent with a note;
   anything else (`partial`, `about 50`) is absent with a warning naming its file rows. None of
   these is a refusal: under DEC-011 an absence earns no credit, so reading a cell as absent
   cannot improve the file.

### What it does not do

- **No visual mapping screen.** `intake-review` is still a command-line review. The screen
  moves to the platform work, as the audit recommended (F-25).
- **No reprojection** (DEC-021), and **no recalibration**: the anchors were set for the
  reference region, and Tier 1 is still relative to the cohort (F-09).

### Published numbers

None moved. The reference study's v3 and legacy outputs are text-identical before and after,
except run stamps; its standards register is byte-identical.

### Gates

`tests/test_cohort_run.py` (the reference digests, intake to a validated contract, defaults
written down, costs withheld, the reference study run as a cohort still held to 25 / 48, bad
identifiers and risk levels refused) and `tests/test_input_schema.py`, which checks
`data/schema/input_schema_v1.json` against the code that implements each statement in it,
measures which fields move the score rather than trusting the schema's word, and reruns the
worked example in `docs/INPUT_SCHEMA.md`.

## DEC-024 - The planner runs the unmodified engine in the planner's own browser

**Date:** 2026-10-18 · **Phase:** platform v1 · **Builds on DEC-011, DEC-016, DEC-021, DEC-023**

### What was blocking

DEC-023 made another jurisdiction's sites run end to end, but only from the command line: a
planner needed Python, a cloned repository and a terminal, and the mapping review was still
text (F-25). A hosted service would have meant receiving planners' site files, which DEC-016's
line between private inputs and public outputs does not allow us to hold.

### The decision

1. **The engine runs where the file is.** `platform/app` is a static page that loads Pyodide
   in a Web Worker and imports `fcf_m2` from an archive built from `src/` with no edits. The
   planner's file is read in the browser and never sent anywhere; the only other requests are
   the app's own files and, after the planner chooses Show Map, basemap tiles.
2. **One bridge, no second implementation.** `src/fcf_m2/browser_api.py` exposes intake,
   mapping, check, run and explain as JSON strings. The interface fills fixed wording with the
   engine's numbers and never computes a score. `explain` returns each driver's points so they
   sum to the score shown, including the demand access adjustment.
3. **Never without a cohort.** `browser_api.run` refuses to run before a file has been checked
   and accepted, because `workflow.run` without a cohort reads the reference study's private
   inputs, which the bundle does not contain.
4. **A run can be replayed on its own date.** `workflow.run` takes `as_of`, passed to
   `build_confidence`, so a restored `.evsient` project file reproduces its saved results
   instead of aging them by the days since. Without `as_of` nothing changes.
5. **The two engines must agree.** `platform/tools/parity.mjs` runs the worked example through
   the browser archive and through the native package and fails on any difference above
   1e-9; CI runs it on every change (3,476 numbers, largest difference 3.55e-15 at commit).
6. **Licence.** The project is released under Apache-2.0 (`LICENSE`, `NOTICE`), the permissive
   licence the build plan recommended, so planners elsewhere can host their own copy.

### What it does not do

- **No public data hub yet.** County packs, the assistant and a tagged PDF report are later
  phases of the build plan.
- **No new scoring.** The browser engine is the same package; the reference study's outputs do
  not change.

### Published numbers

None moved. `as_of` defaults to today, as before.

### Gates

`tests/test_browser_api.py` (the bridge's field catalog matches `docs/INPUT_SCHEMA.md`, statuses,
refusal without a cohort, explanations that sum to the score), `tests/test_licence_manifest.py`,
and the CI `platform` job (runtime fetch with pinned hashes, engine archive, parity, app build).

## DEC-025 - Public data can fill a planner's gaps, one accepted field at a time

**Date:** 2026-10-18 · **Phase:** platform v1 · **Builds on DEC-011, DEC-016, DEC-021, DEC-024**

### What was blocking

Most planners' files do not carry a site's surroundings (households and jobs within a mile,
nearby chargers, equity need). DEC-011 scores those as absent, so a planner without a GIS team
lost credit for data the public already publishes. Filling them in the engine or on a server
would break DEC-021 (never improve silently) or DEC-024 (the file stays on the device).

### The decision

1. **A separate, public-only hub.** `platform/hub/` builds versioned releases from pinned public
   files (ACS 2020-2024 B11001, 2020 P.L. 94-171 blocks, LODES 8.4 WAC 2023, CDC/ATSDR SVI 2022,
   TIGER 2026 state boundary) and a dated AFDC snapshot, recording each input's URL, vintage,
   licence and SHA-256. It writes one Parquet pack per Virginia county (133 packs, 3.6 MB in
   all), national tables, STAC metadata and `latest.json`. Every key is new per release; only
   `latest.json` and the STAC catalogue and collections change. Nothing from `data/inputs`, the
   contract or real provenance goes in (DEC-016).
2. **Opt in, then accept per field.** The Public Data step fetches nothing until the planner
   asks. The app then fetches only the county packs around their sites from its own origin,
   checks each against the release's SHA-256, and works out each value in the browser. Every
   proposed value is shown with its source, vintage and method; a site without one gets a
   reason (outside Virginia, within the radius of the state line, no coordinates), never a 0.
3. **Recorded as public data, never as the planner's.** `browser_api.fill` takes the accepted
   values with their sources and refuses any cell the file already has. On `accept` each value
   gets a ledger entry, `derived_public_data` provenance at its site (scored 55, below the
   planner's own sources) with the release's source date, and a row in
   `public_data_fills.csv`. With no fills the cohort is byte-for-byte what it was. The bridge
   protocol is now 2.
4. **v1 fills five fields.** `nearby_households_1mi` (ACS shared to blocks by 2020 occupied
   homes), `nearby_jobs_1mi` (LODES), `equity_gap_index` (SVI national rank, household-weighted;
   labelled a proxy), `existing_l2_ports_1mi` and `existing_dcfc_ports_3mi` (AFDC open, public
   stations, including those within 3.5 miles across the line).
5. **Plain Parquet the browser can read.** Snappy compression, int32 counts and point columns
   (`lat`, `lon`), so hyparquet 1.31.2 reads them with no codec add-on and no BigInt. Not
   GeoParquet and not ZSTD, which the build plan named; neither is needed for points.

### What it does not do

- **Three fields are not in the hub yet.** `aadt_nearest` (no downloadable HPMS 2024 or VDOT
  2025 file; VDOT's live layer ends in 2022), `amenities_count_0_5mi` (no Virginia Overture
  extract or agreed category list) and `ev_share_local` (the ODbL pack is not built). The app
  names each gap and why.
- **Virginia only.** Sites elsewhere are told so and keep their gaps.
- **No new scoring.** A filled value scores exactly as the same value typed in the file; only
  data confidence differs.

### Published numbers

None moved. The reference study does not use the hub.

### Gates

`tests/test_hub_builder.py` (publisher layouts, pins, immutable keys, the five release gates:
schema, row-count change of more than 20%, coordinates, licence text, size), the DEC-025 cases
in `tests/test_browser_api.py` (provenance, ledger, refusals, an unchanged cohort without
fills), and parity (unchanged).

## DEC-026 - The planner's other columns travel with their sites, never scored; site IDs stay text

**Date:** 2026-10-18 · **Phase:** platform v1 · **Builds on DEC-011, DEC-021, DEC-024, DEC-025**

### What was blocking

The owner tested the planner with a 360-site file of 31 columns. Seven map to model fields; the
other 24 (city, region, program focus, heat risk, solar potential, the planner's own `custom_*`
notes) were read and then vanished from every screen and download. A planner who cannot see
their own columns beside the ranking has to rebuild it in a spreadsheet, and loses the context
the ranking needs. Separately, an all-digit site ID column came back from a run as numbers:
`workflow._load_cohort` read `sites.csv` with default types, so "007" returned as "7.0" and
`explain` and `provenance` found no such site.

### The decision

1. **Carry every column the model does not use, never score it** (the owner's choice). The app
   keeps each one with its site, keyed by the exact site ID the engine reads, from the mapping
   the run used. Values are shown as written; a column is formatted as numbers only when every
   value in it reads as a plain number (a leading zero, as in a ZIP code, keeps it text).
2. **Always labelled Not in the score, everywhere it appears**: extra Ranked Sites columns the
   planner adds (sortable, with a contains or range filter that narrows the table only), a card
   in the site's details, a group in Compare, marker colours on the map (five sequential steps,
   or up to eight categories and Other, with a legend), CSV columns headed "Your column (not in
   the score)", an Excel sheet of their own, a tenth report section and each profile's values,
   and `inputs/your_columns.json` in the project file, which is then `evsient-project/3`. Files
   saved as /1 and /2 still open, with the columns read again from their table.
3. **Display data only.** Nothing carried is sent to the engine's scoring, and the interface
   computes no score from it. The only things worked out from it are the order, filter and map
   colours the planner asks for. Ranking by the planner's own columns is the separate,
   labelled "Your index" in `docs/FLEXIBLE_ANALYSIS.md`, not this.
4. **Say how much of the score the file feeds.** Map Columns and Check state how many of the 22
   scored fields the file provides and that the other columns are carried, not scored. Below
   half, a warning says first that the ranking will mostly reflect missing information, not
   site suitability (the owner's file provides 1 of 22).
5. **Site IDs are text end to end.** `_load_cohort` reads `site_id`, `site_name` and
   `site_type` as text, and `electrical_risk.csv` and `site_meta.csv` key on text IDs. The
   reference study is read by its own loader and is untouched.

### Published numbers

None moved. The full suite passes, golden tests included, and parity is unchanged.

### Gates

`test_site_ids_keep_their_exact_text` in `tests/test_browser_api.py` ("007", "0042", "12" and
mixed IDs through `run`, `explain` and `provenance`, and the cohort's `sites.csv`), parity, and
the owner's 360-site file run end to end in the browser under the production CSP. That run
found an older fault: the Excel download never finished for a workbook of 160 kB or more,
because the zip library compresses large parts in a `blob:` Worker that `worker-src 'self'`
blocks. `vite.config.ts` now makes write-excel-file zip synchronously; the CSP is unchanged.

## DEC-028 - The public data hub covers six states, with the borders between them dissolved

**Date:** 2026-10-18 · **Phase:** platform v1 · **Owner decision** · **Builds on DEC-016, DEC-025**

### What was blocking

DEC-025 built the hub for Virginia alone, so a planner anywhere else was told "outside Virginia"
for every site, and a Virginia site within a mile of Maryland or the District of Columbia lost
its block-based values even though both neighbours publish the same public files.

### The decision

1. **The owner extended the hub to New York, Maryland, the District of Columbia, Colorado and
   Illinois** (Discover Financial Services is headquartered in Riverwoods, Illinois), alongside
   Virginia. `sources.json` now lists the published states; each has its own pinned 2020 P.L.
   94-171 file and LODES 8.4 (2023) workplace file. Every new input is a U.S. Census Bureau
   public-domain file, pinned by SHA-256 like the Virginia ones. No ODbL source was added: the
   owner has not decided on ODbL, so `ev_share_local` stays out.
2. **One coverage for all six states.** TIGER/Line draws a shared border with the same vertices
   in both states, so the builder removes every edge that appears in both directions and keeps
   the outline of the union. The block-based fields are offered at least 1 mile inside that
   outline, not inside a single state: a site in Arlington now gets households, jobs and the
   equity rank from Virginia and District of Columbia blocks together. A site within a mile of
   a state the hub does not cover (New Jersey, from Manhattan's west side) still gets the
   reason, never a partial total.
3. **Each state is built exactly as before.** Its blocks, and the stations inside it or within
   3.5 miles of its own boundary, go in its own county packs. A station near a shared border is
   therefore in both states' packs, and the app counts it once by its AFDC ID. Virginia's 133
   packs hold the same rows as in 2026-10-18.1 (checked table by table), and the national
   tables keep their keys.
4. **One source per field, one file per state underneath.** A filled value names one source, so
   the per-state files are grouped (`pl94171`, `lodes-wac`) and the build refuses a group whose
   files differ in publisher, vintage, publication date or licence. The Public Data step says
   which state each site is in (by its nearest census block) and lists each state's own files
   that the values near the sites were worked out from.
5. **The row-count gate compares state by state.** A new state is reported as new; a state
   already published still stops the build if its rows move more than 20%.

### Release 2026-10-18.2

386 county packs, 22.8 MB in all: Virginia 133 (3.6 MB), New York 62 (6.4 MB), Maryland 24
(1.9 MB), District of Columbia 1 (0.2 MB), Colorado 64 (2.9 MB), Illinois 102 (7.7 MB; Cook
County is the largest pack at 1.99 MB, under the 5 MB limit). Coverage: 6 rings, 8,482
vertices. All five gates pass.

### What it does not do

- **No other states.** A site elsewhere is told which states the hub covers.
- **No new fields.** `aadt_nearest`, `amenities_count_0_5mi` and `ev_share_local` are still not
  in the hub, for the reasons DEC-025 gives.

### Published numbers

None moved. The reference study does not use the hub.

### Gates

`tests/test_hub_builder.py` adds an invented neighbouring state: the shared border is dissolved,
both states publish packs under one coverage, the western state's packs are unchanged by the
neighbour, a border station is in both packs, a new state passes the row-count gate as new, and
the registry refuses a state outside its group or a group whose files disagree. The Public Data
step was run end to end in the browser against the local release, with synthetic sites in all
six states and one outside them.

## DEC-030 - The Cognito-gated `/platform*` path is retired; the planner needs no sign-in

**Date:** 2026-10-18 · **Decided by:** the project owner · **Supersedes:** DEC-017 · **Builds
on:** DEC-016, DEC-024

### The decision

Retire the Cognito-gated `/platform*` path on `futurecityfellowship.andyyaro.com`. The planner
at https://app.futurecity.andyyaro.com replaces it. It carries synthetic samples only and keeps
a planner's own file on their device (DEC-024), so there is nothing behind it to gate, and the
platform v1 plan has no accounts.

### Why the gate existed, and why that reason is gone

DEC-017 put the web platform behind an edge sign-in because its bundle carried the real study:
`provenance_v1.json` and `contract/v1/site_table.csv` hold the twelve real facilities, which
DEC-016 keeps private. The new planner never carries them, so the reason for a gate does not
apply to it, and keeping the old gated copy alive would only keep that private data on a
public distribution behind a login.

### What was retired

Removed live on 2026-10-18, before this entry:

- the `/platform*` cache behaviour and the `platform-gated` origin on distribution
  `E1XZPHWHZV0OEO`; the default behaviour, which serves the public site and the NFC pages, was
  not changed;
- the Cognito app clients `future-city-platform-edge` and `future-city-assistant-web`, with
  their managed-login branding.

Removed by hand after this entry, in order: the bucket `future-city-fellowship-platform` (backed
up locally first; the backup is kept outside the repository), the origin access control
`E1JND6HMX02LBD`, the response headers policy `fcf-platform-security`, the Lambda@Edge function
`fcf-platform-edge-auth` once its edge replicas drain, the IAM role
`fcf-platform-edge-auth-role`, and the edge-auth log groups.

In the repository: `infra/edge-auth/index.mjs`, `infra/edge-auth/granted.mjs.example` and
`tests/edge_auth/` are removed, with the `verify.sh` gate that ran them.
`scripts/deploy_platform.py` publishes the public site only (what `--www-only` did), never sends
a distribution config, and refuses `--platform`, `--gate`, `--full`, `--with-gate` and
`--platform-only` with exit code 2. It no longer needs the allowlist file, and `deploy.yml` no
longer writes it from a secret. `scripts/verify_deployment.py` now asserts that 14 former
platform paths return 404 with no redirect to Cognito, alongside the 12 NFC pages and 6 public
pages; it passed 32 of 32 against the live site on 2026-10-18. Open actions 16 and 18 are
closed as moot.

### What stays, and why

- **The Cognito user pool `us-east-1_mKrwfQTkg`.** It is shared and predates this program.
- **The embedded assistant client `future-city-assistant-embedded-client`.** It belongs to the
  assistant, not to the gate.
- **`infra/edge-auth/granted.mjs` in `.gitignore`.** A copy may still sit on a maintainer's
  disk; it holds login identities and must never be committed.
- **`site/platform/`.** It still builds the desktop installer's bundle (DEC-015, DEC-016); only
  its hosted, gated copy is retired.
- **The history.** DEC-017 and the ledger rows that describe the gate stay as written. The
  allowlist's identities also remain in git history until the repository is cleaned before it
  is made public (open action 14).

### Rejected

- **Keep the gate as a fallback.** It would keep the real study on a public distribution behind
  a login, and keep a Lambda@Edge function, a bucket and two app clients to maintain, for a path
  nobody is sent to.
- **Leave the deploy script's gate mode in place but unused.** A full `--apply` rebuilt the
  behaviour, the origin, the Lambda association and the bucket. Left in, the next person to run
  the documented command would have recreated the gate.
