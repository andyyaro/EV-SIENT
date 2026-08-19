# SESSION HANDOFF - written 2026-08-04

For whoever picks this up next, human or assistant, with none of the conversation that produced
it. Everything here was checked at the moment of writing, not remembered.

---

## 1. Bottom line

**The V4 platform program is complete and shipped.** Nothing is half-finished, nothing is
uncommitted, and no work is blocked on the machine. `v3.0.0` is published as a **pre-release**.

| | |
|---|---|
| `main` | `bcb88a1` |
| `v4-platform` | `bcb88a1` - identical, fully contained in `main` |
| Working tree | clean, no stashes |
| Unpushed commits | none, on any of six local branches |
| Open PRs | none |
| Gates | **40 PASS / 0 FAIL** |
| CI on `main` | green |
| Secret scan | clean, 491 tracked files, 11 patterns |
| Release | `v3.0.0`, prerelease, not draft, 4 assets |

---

## 2. The one thing that would change the release

**Nobody has ever run the Windows build on Windows.** That is the sole reason `v3.0.0` is
marked pre-release, and it is stated on the Release page rather than left to the badge.

The owner intends to open a session on a Windows machine to close this. **The full test prompt
for that session is in §6 below** - it is self-contained and needs nothing from the conversation
that wrote it.

If that test passes, the follow-up is mechanical:

```bash
gh release edit v3.0.0 --prerelease=false
```

plus removing `prerelease: true` from `.github/workflows/package.yml` (the comment there names
this exact condition as the trigger) and updating the "Windows install unexercised" row in
[`RESIDUAL_RISKS.md`](RESIDUAL_RISKS.md).

---

## 3. Two live-state facts a new session must not guess at

**The AWS SSO token was expired and has been renewed** (2026-08-04), and a full live audit ran
against the real estate - see §3a. It will expire again; before any AWS work:

```bash
aws sso login --profile future-city     # S3, CloudFront, certs, hosting, deployment
aws sso login --profile cerfodes-dns    # Route 53 ONLY
aws sts get-caller-identity --profile future-city   # verify before every phase; mismatch -> stop
```

### 3a. The live estate, audited 2026-08-04 with credentials

Asked of AWS directly, not inferred from the deploy script:

| Check | Observed |
|---|---|
| `verify_deployment.py` against the public URLs | **33 passed, 0 failed** |
| Platform bucket public-access blocks | **all four on** |
| Objects under `platform/` in the MAIN bucket | **0** - the isolation is structural, not behavioural |
| CloudFront cache behaviours | **1**, `/platform*`, at **Lambda v8** |
| Gate allowlist | **2 accounts**, matched on `sub` **and** `email` |
| Cognito pool members | **3 confirmed** - so `redacted-1@example.org` can sign in to the shared pool and **cannot** reach `/platform/*` |
| Spend, 30 days | **$0.50** against a $10/month ceiling |

**This program's incremental AWS cost is effectively zero.** The two largest lines - Secrets
Manager and Amplify - were created 2026-06-29 and 2026-07-07, before this program began on
2026-07-27. Neither is ours. (Running the Cost Explorer query itself cost $0.04 of that $0.50.)

A shared user pool is **not** shared access: the authoriser holds an explicit two-entry
allowlist, so pool membership alone opens nothing.

**The live platform is 4 files behind the repo, and it does not matter.** `site/platform/`'s
`app.js`, `index.html`, `styles.css` and `surfaces.json` changed in `27a6bdb` after the last
deploy (2026-07-28). Checked, not assumed: those changes only affect surfaces that are **absent
from an installation**, and the live deployment is built from the full repository where every
surface is present - `surfaces.json` in this tree marks **none** absent. So nothing on the live
site is currently wrong. Redeploying is tidying, not a fix:

```bash
python scripts/deploy_platform.py            # dry run, read-only, says what it WOULD do
python scripts/deploy_platform.py --apply     # then verify with scripts/verify_deployment.py
```

---

## 4. What is verified, and what is not

**Verified by observation, not inference:**

- Both published release assets **downloaded from the Release page** and inspected: checksums
  verify with `shasum -a 256 -c`, all four model input paths present, `INSTALL.md` included,
  `verify.sh` correctly absent, zero backslash paths, zero non-UTF-8 text files, **zero real
  facility identifiers**.
- The macOS artifact **installed and launched from a CI build**: 5/5 platform surfaces HTTP 200,
  rendered page 12 756 characters with zero `undefined` / `[object Object]` / `NaN`.
- Live deployment: 33/33 script assertions plus 7/7 rendered browser checks (2026-07-28).
- Clean-clone walkthrough from an empty directory: 40/40 gates, no documentation corrections
  needed.

**Not verified, and stated as such in [`RESIDUAL_RISKS.md`](RESIDUAL_RISKS.md):**

- **Nobody has confirmed the electrical capacity at any of the twelve sites.** `capacity_basis`
  is `placeholder` on **120/120** contract rows; data confidence is **Low** at all twelve. This
  governs everything else.
- The Windows artifact has never been installed.
- MATLAB ran **49/49 on a synthetic fixture only**, never against the real sites. Simulink was
  **built and never simulated**.
- No NFC tag has been placed.
- Nothing shipped is signed or notarized.

---

## 5. What needs a person, not a session

Tracked in [`../open-human-actions.md`](../open-human-actions.md). The ones that are actually
open and actually matter:

| # | What | Why it needs the owner |
|---|---|---|
| **8b** | Remove the superseded Tableau workbook from the public profile | Only the account holder can delete it. It publishes `legacy_v2` ranks (FFX002 first at 58.8) while the canonical answer is FFX004 at 53.4 - **a wrong number sitting in public** |
| **8e** | Republish the workbook so the CO₂e sheet is not read backwards | `net_co2e_kg` is *avoided* emissions |
| **11** | Facilities consent before any real site data is published | Other people must say yes |
| **4** | Utility + facility data requests | **This is what unblocks the capacity placeholder**, and therefore every feasibility question |

**Known stale rows in that tracker:** 8c (gallery re-baseline), 8d (the PDF) and 9 (website
deploy) are **done** - decided by the owner and executed - but are still listed as open
decisions. They should be struck through with dates the way rows 7 and 8 already are. Left
undone deliberately: editing a decision log is the owner's call, not a cleanup task.

---

## 6. The Windows test prompt

Paste this whole block into a session on the Windows machine. It assumes nothing.

```
Test the Windows build of Future City Fellowship v3.0.0 on this machine. You are the
first person ever to run it on Windows - that is the entire point of this session, and
it is the only reason the release is marked pre-release.

REPO (private, note the trailing hyphen):
  https://github.com/andyyaro/Future-City-Fellowship-
RELEASE:
  v3.0.0, asset fcf-platform-v3.0.0-windows.zip and its .sha256
  Published sha256: ae3c7a41b1e6f0334969ce0db9f4dd8fddb77d1ec5bd8e985104ff5fc26e3e15

HOUSE RULES (these override defaults):
- Honesty is the product. Never claim something works that you did not run. Never
  soften a limitation. If a step fails, report the failure verbatim - a failed test
  here is a SUCCESSFUL session, because it found something four Windows-only defects
  already slipped past.
- Do NOT put "Co-Authored-By: Claude" or "Generated with Claude Code" on any commit,
  PR or artifact. Use the machine's git identity.
- Do NOT disable SmartScreen, Defender, or any security setting. A SmartScreen warning
  is EXPECTED and correct - there is no code-signing certificate. Click through it the
  normal way (More info -> Run anyway) or right-click the zip -> Properties -> Unblock.
- Do not weaken a check to make something pass. Do not force-push, rewrite history,
  or delete branches or tags.
- Verify the way a recipient would: download the published asset from the Release page.
  Do NOT clone the repo and build your own artifact - that tests the wrong thing.

WHAT TO DO, in order:

1. Download the .zip and .sha256 from the v3.0.0 Release page.
2. Verify the checksum:  certutil -hashfile fcf-platform-v3.0.0-windows.zip SHA256
   Compare to the .sha256 file, which holds one line: digest, two spaces, filename.
   Report whether they match.
3. Right-click the zip -> Properties -> Unblock if the checkbox is there. Extract it.
4. Read INSTALL.md, which ships INSIDE the bundle at the top level. Follow it exactly
   as written, and report ANY step where the guide's description does not match what
   actually happens. The guide being wrong is a defect worth as much as a crash.
5. Double-click run-platform.cmd. Record what happens at every stage: SmartScreen,
   the Python version check, the dependency install, the first-run build (~1 minute),
   and the browser opening.
6. Once the platform is up, click through it. Report anything that is blank, broken,
   says "undefined", or offers a link that 404s.

SPECIFICALLY CONFIRM THESE SIX - each is a defect that was found and fixed, and this
is the first time any of them is being checked on real Windows rather than inferred:

  a) All four model input paths exist in the extracted folder:
       data\inputs\real_sites_v2.csv
       data\inputs\legacy_v2_electrical_risk_summary_frozen_2026-07-19.csv
       data\inputs\legacy_matlab_site_meta.csv
       data\provenance\field_provenance_v1.csv
     (These were MISSING on Windows before - the build wrote them to the wrong paths.)
  b) RELEASE_MANIFEST.json contains NO backslashes in its "files" keys. 58 of 60 did.
  c) The CSVs are valid UTF-8. Open data\inputs\real_sites_v2.csv and confirm the note
     column reads "SYNTHETIC FIXTURE - invented facility" with a proper em dash, not a
     mangled character. Confirm pandas can read it with default settings.
  d) THIRD_PARTY_LICENCES.md lists tzdata (a Windows-only dependency of pandas). It
     should be there on Windows and is correctly absent on macOS.
  e) scripts\verify.sh is NOT present, and the platform's "verify-all" operation shows
     as unavailable with the reason "not part of this installation" - NOT the Windows
     bash reason.
  f) The platform shows FIVE surfaces labelled "not in this installation" (explorer,
     dashboard, contract, reports, NFC) with NO Open link on any of them. The sixth,
     Tableau, should have working external links.

ALSO CONFIRM the data is synthetic: site ids are SYN001, SYN002 and so on. If you see
FFX001-FFX004 or PWC001-PWC008, or a real Virginia facility name, STOP IMMEDIATELY and
report it - that is a DEC-016 breach and the release must be pulled.

REPORT: write what you observed, step by step, including exact error text. Then record
it in docs/operations/v4-program/VERIFICATION.md as a new section and add a row to
docs/operations/v4-program/LEDGER.md.

IF EVERYTHING PASSES: open a PR that removes "prerelease: true" from
.github/workflows/package.yml (the comment there names this exact condition), updates
the "Windows install unexercised" row in docs/operations/v4-program/RESIDUAL_RISKS.md,
and flip the existing v3.0.0 Release off pre-release with:
  gh release edit v3.0.0 --prerelease=false
Run .\scripts\verify.sh under Git Bash or WSL if available; if neither is, say so
rather than claiming gates passed.

IF ANYTHING FAILS: do not fix it and quietly move on. Report it first, then fix it,
then re-download a rebuilt artifact and re-test. Leave the release as pre-release.
```

Python 3.11+ must be on that machine or the first thing you see is the version check refusing -
a valid result, but not the one you want.

---

## 7. Standing rules a new session must not have to rediscover

- **Honesty is the product.** Never claim an engine ran that did not run - GNU Octave is not
  MathWorks MATLAB, and a Python reimplementation is not MATLAB. Never soften a limitation.
  New plumbing with no real data ships empty and labelled.
- **Nothing is "done" until observed working.** Verify the way the consumer will: render the
  page, download the published artifact, install it. Reading the source is not verification.
- **Never read `$?` through a pipe.** `| head` and `| tail` return *their* exit status. This
  caused two pushes behind failing gates and one wrong measurement in this program.
- **Parse or exercise; never grep.** At least a dozen defects here were text-versus-meaning
  errors - prose accurate about something other than the thing it annotated. Three of them were
  inside tests written to catch that exact class.
- **A gate suite only checks the tree it runs in**, and passes identically on any branch. It
  cannot tell you that seven commits landed on the wrong branch; the owner caught that.
- **Mutation-test every new gate.** A gate that cannot fail is decoration.
- **DEC-016 is absolute:** no real facility identifier in the public installer. The twelve sites
  are FFX001–FFX004 and PWC001–PWC008. A distinctive *fragment* of a name counts - `Neabsco`
  shipped for weeks behind a guard that matched whole names only.
- **No `Co-Authored-By: Claude` or "Generated with Claude Code"** on commits, PRs or artifacts.
  Owner's instruction, 2026-07-28.
- Never force-push, rewrite published history, delete branches or tags, or weaken a test to make
  it pass. AWS work uses `--profile future-city` (Route 53 only: `cerfodes-dns`), never the
  default profile, never `sudo`. Aggregate new recurring cost stays **≤ $10/month**.

---

## 8. Where to look

| Question | File |
|---|---|
| What happened, in order, with dates | [`LEDGER.md`](LEDGER.md) |
| Every check run and its observed result | [`VERIFICATION.md`](VERIFICATION.md) |
| What is still unverified or needs a person | [`RESIDUAL_RISKS.md`](RESIDUAL_RISKS.md) |
| Why a decision was made | [`DECISIONS.md`](DECISIONS.md) |
| What is deployed and how to remove it | [`/DEPLOYMENT.md`](../../../DEPLOYMENT.md) |
| What a reader can and cannot conclude | [`/docs/WHAT_THIS_CAN_AND_CANNOT_TELL_YOU.md`](../../WHAT_THIS_CAN_AND_CANNOT_TELL_YOU.md) |
