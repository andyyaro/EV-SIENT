# VERIFICATION — every check run, and what was actually observed

**Recorded 2026-07-28.** This document exists because "verified" in this program means *observed
working*, not *believed to work*. Every line below is something that was run and whose output
was read. Where a check could not be run, it says so and why — an unrun check recorded as
passing is the failure this whole program is organised against.

The distinction is not academic. This program has already produced: a commit message asserting
work that did not happen; five consecutive red CI runs reported as green; two blank published
charts called verified; a sign-in page that did not exist behind 32 passing assertions; and a
gate suite that passed 38/38 while the repository declared an operation whose script was not
committed. Every one was caught by looking at the thing rather than at the report of it.

---

## 1. Repository gate suite — 39 PASS / 0 FAIL

`./scripts/verify.sh`, exit code captured directly (never through a pipe — `| tail` returns
*tail's* exit code, which is how two failing gates were once pushed).

| # | Gate | Result |
|---|---|---|
| 1 | python: test suite with coverage gate (legacy golden + cohort invariance + contract + offline GIS) | PASS |
| 2 | python: `legacy_v2` reproduces the accepted baseline (25 starter / 48 pathway) | PASS |
| 3 | contract: tracked `v1` passes all rules + JSON Schema + RT-10 hash chain | PASS |
| 4 | contract: `v2` rebuilds byte-identically from the frozen `v1`; every shared field unchanged | PASS |
| 5 | contract: tracked `v2` passes v1 rules + v2 rules + JSON Schema + RT-10 hash chain | PASS |
| 6 | cross-model: shared physical constants agree between Python and MATLAB | PASS |
| 7 | cross-model: MATLAB canonical CSV reconciles with the contract | PASS |
| 8 | docs: generated workflow steps match the executable manifest | PASS |
| 9 | dashboard: static assets present + every chart footer-logged | PASS |
| 10 | platform: Simulink view matches the real `.slx` and states it was never simulated | PASS |
| 11 | platform: generated artifacts byte-identical via the platform and via the CLI | PASS |
| 12 | platform: public bundle matches its manifest and excludes the real site inputs | PASS |
| 13 | platform: engines are distinguishable and every divergence is surfaced | PASS |
| 14 | platform: local server binds loopback, requires a token, runs only declared operations | PASS |
| 15 | platform: web tier is wired to what exists, computes nothing, keeps its caveats | PASS |
| 16 | platform: operations match the CLI byte-for-byte; web tier states what it cannot do | PASS |
| 17 | platform: every displayed number resolves to its lineage; both tiers agree | PASS |
| 18 | tableau: workbook data matches the contract; `.twb` declares its sheets and caveats | PASS |
| 19 | tableau: embeds use the `/views/` share form, never the profile page form | PASS |
| 20 | secrets: no keys/tokens/account IDs in tracked files | PASS |
| 21 | hygiene: no machine-specific absolute paths in tracked source | PASS |
| 22 | hygiene: no tracked file over 25 MB | PASS |
| 23 | clone-safety: every declared dependency is tracked, not just present on this machine | PASS |
| 24 | 3d: explorer suite passes (attribution reproduces the model score in BOTH modes) | PASS |
| 25 | 3d: `sites.geojson` strict-valid RFC 7946, 12 expected sites in Northern Virginia | PASS |
| 26 | 3d: all 12 GLB models well-formed glTF 2.0 | PASS |
| 27 | 3d: viewer JS parses and every CDN reference is version-pinned | PASS |
| 28 | matlab: nothing destined for the PUBLIC harness carries site-identifying data | PASS |
| 29 | field-entry: the browser's rules never accept what the model rejects | PASS |
| 30 | platform: the desktop launcher builds what is derivable and refuses what is not | PASS |
| 31 | platform: every surface link resolves to a file that exists in the bundle | PASS |
| 32 | supply chain: hashed requirements match the lock; every pin carries a digest | PASS |
| 33 | packaging: tags-only, time-bounded, never claims notarization | PASS |
| 34 | intake: a messy third-party file degrades confidence rather than being cleaned up | PASS |
| 35 | synthetic: the public input set is usable, honest, and not a disguised copy | PASS |
| 36 | website: public pages carry their caveats and embed only the canonical workbook | PASS |
| 37 | browser: the form refuses VISIBLY, and the explorer's first screen asks nothing of a reader | PASS |
| 38 | edge-auth: only a verified `id_token` for the granted account reaches the origin | PASS |
| 39 | links: markdown links resolve | PASS |

---

## 2. Test suites — counted, not estimated

| Suite | Result | How it was counted |
|---|---|---|
| Python | **669 tests collected**, all passing | `pytest --collect-only`, read |
| Coverage | floor **80%**, enforced | `--cov-fail-under=80` in `verify.sh` and `tests.yml` |
| Node — edge authoriser | **50 pass / 0 fail** | `node --test tests/edge_auth/*.test.mjs` |
| Node — real browser | **16 pass / 0 fail** | headless Chrome over CDP; skips loudly if Chrome absent |
| MATLAB | **49 passed / 0 failed** on MathWorks R2025b Update 5 | CI run record in `matlab/EXECUTION_STATUS.md` |
| Octave ↔ MATLAB | **2 640 cells, 0 numeric divergences** at 1e-9 | cross-validation run |

The Python count is deliberately **not** written into README, CONTRIBUTING or the reproduction
guide. It was hardcoded there as "80 tests", went stale, and went stale again within an hour of
being corrected to 652. Those documents now describe the suite instead of counting it.

---

## 3. Model reproduction — the permanent obligations

| Check | Expected | Observed |
|---|---|---|
| `legacy_v2` starter total | 25 | **25** |
| `legacy_v2` pathway total | 48 | **48** |
| Contract v1 shape | 120 rows, 12 sites | **120 rows, 12 sites** |
| `capacity_basis` | `placeholder` on every row | **120/120 placeholder** |
| `data_confidence` | `Low` on every row | **120/120 Low** |
| Canonical top site (`milestone2_v3`) | FFX004 | **FFX004 at 53.4** |
| Legacy top site (`legacy_v2`) | FFX002 | **FFX002 at 58.8** |
| RT-10 hash chain | 11/11 | **11/11**, recomputed independently |

---

## 4. Continuous integration

CI invokes `verify.sh` rather than keeping a second list of steps, so there is one definition of
green. Last five runs on `v4-platform`: **success, success, success, success, success** —
read from `gh run list`, not assumed.

**Standing correction:** CI is checked *after every push*. It was red for five consecutive
commits while this program reported green, because `verify.sh` was run locally and this
repository's own CI never looked at.

---

## 5. Live deployment

| Check | Observed |
|---|---|
| `/platform/` gated assets | 302 → Cognito, zero bytes served |
| 6 alternative path spellings (`/%70latform/…`, `//`, `/./`, `/../`, case) | none evade the gate |
| All 12 NFC tag pages `/t/FFX001`–`/t/PWC008` | **HTTP 200, public, no account** |
| Pre-existing pages | untouched, byte counts unchanged |
| Main bucket under `platform/` | **0 objects** — the isolation is structural |
| Direct S3 GET of the gated bucket | **403** |
| Sign-in actually works | **confirmed by the owner signing in**, both granted accounts |

**Not claimed:** that every surface inside the platform behaves for a human. "It renders"
establishes that `index.html` and its assets are served through the gate. The provenance panel,
explorer and dashboard sub-surfaces, and tier detection have not been exercised by a person.

---

## 6. Artifacts verified by reading them, not by trusting the build

- **Tableau workbook** — downloaded the *published* `.twbx` and read its Hyper extracts:
  FFX004 rank 1 @ 53.4, all 12 Low, horizons 2026/2036/2046/2056, totals 25/48.
- **Static dashboard** — every chart footer-logged; regenerated and diffed.
- **Public installer** — extracted from a clean directory and run end to end: 0.2 MB, 44 files,
  free of all 36 real identifiers, 6/6 endpoints serving.
- **Stamped planning report** — 9 pages (1 cover + 8 originals); the 8 originals verified
  **unaltered** by text-extraction diff of all 437 lines.
- **Explorer gallery** — the published `specimens` array parsed as JSON and each score compared
  to the canonical fixture.

---

## 7. What could not be verified here, and why

| Item | Why not | Where it is recorded |
|---|---|---|
| Real MATLAB against the real sites | The public harness must never carry facility data | `EXECUTION_STATUS.md` |
| Simulink numerics | The model was **built**, never **simulated** | Simulink view states it on its face |
| Windows install | No Windows machine; CI builds the artifact only | `docs/INSTALL.md` |
| Notarization | Ad-hoc signature achieves nothing for Gatekeeper (`spctl` exit 3, measured) | `docs/INSTALL.md` |
| Editable dev install integrity | pip cannot hash an editable requirement — measured, not assumed | `add_lock_hashes.py` |
| Content of two Framer-hosted iframes | Third-party hosted, outside version control and every gate | `RESIDUAL_RISKS.md` |
| A real fresh-clone walkthrough | Gate 23 catches the mechanical case only | `RESIDUAL_RISKS.md` |

---

## 8. Method notes worth keeping

- **Verify the way the consumer will.** Render the page; fetch the published artifact. Reading
  the source is not verification — that is how two blank Tableau charts shipped.
- **A gate suite only checks the tree it runs in.** It cannot see a file present locally and
  absent from a clone. Gate 23 exists because that failed three times.
- **Mutation-test every new gate.** A gate that cannot fail is decoration. Every gate added in
  this program was checked by deliberately breaking what it guards.
- **Parse or exercise; never grep.** At least eleven defects in this program were text-versus-
  meaning errors: prose that was accurate about something other than the thing it annotated.
