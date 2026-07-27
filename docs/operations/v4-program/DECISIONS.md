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
