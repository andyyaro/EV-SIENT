# DEPLOYMENT.md

What is deployed, what it cost, what breaks if it goes wrong, and how to undo each piece.

Written for the person who has to change this after the people who built it have moved on.
Every figure below was measured against the live account, not estimated — where something is
an estimate it says so.

---

## 1. What is live

One CloudFront distribution, `E1XZPHWHZV0OEO`, on the alias
**`futurecityfellowship.andyyaro.com`**, serving two different things with two different
access rules.

| Path | Origin | Who can reach it |
|---|---|---|
| `/platform*` | `future-city-fellowship-platform` (private, OAC) | **Cognito sign-in required** |
| everything else | `future-city-fellowship` (private, OAC) | **anyone, no account** |

The second row is the one to be careful about. `/t/FFX001` … `/t/PWC008` are the **NFC landing
pages** — the twelve pages a reader would reach by tapping a physical coin in a car park, with
no app and no account. **All twelve pages are live and public; no physical tag has been placed
at any site, and no placement permission has been sought** (`docs/nfc/README.md`,
`docs/nfc/PILOT_PLAN.md`). One bench tag was written and read back through iOS background NFC.
**Any change that gates the default cache behaviour breaks all twelve pages** — and once tags
are placed they are not something that can be un-deployed from a car park.

### Why the platform has its own bucket

Not tidiness — it is the whole access-control argument.

A cache behaviour is chosen by matching the request path against `/platform*`. CloudFront also
normalises percent-encoding: **measured on this distribution**, `/%61ssistant.html` returns the
same 70 378 bytes as `/assistant.html`. If pattern matching happens *before* normalisation,
`/%70latform/index.html` would miss the gated behaviour and be served with no authentication.

Rather than depend on the order of two internal CloudFront steps, the platform bundle lives in
a bucket the default behaviour's origin cannot see. A request that evades the path pattern
lands on the main bucket, which holds **zero** objects under `platform/`, and gets a 404. The
guarantee is structural rather than behavioural.

---

## 2. Resources created, and how to remove each

Everything below is reversible. Nothing was created that another project depends on.

| Resource | Identifier | Rollback |
|---|---|---|
| S3 bucket (gated bundle) | `future-city-fellowship-platform` | `aws s3 rb --force`. Nothing else references it once the cache behaviour is gone. |
| Origin access control | `E1JND6HMX02LBD` | Delete after the origin is removed. |
| CloudFront origin | `platform-gated` | Remove from `Origins`, re-send config. |
| CloudFront cache behaviour | `/platform*` | Set `CacheBehaviors.Quantity` to 0. **This alone fully un-gates and un-deploys the platform**, leaving the public site untouched. |
| Lambda@Edge function | `fcf-platform-edge-auth` (versions 1–5) | Detach from the behaviour first; Lambda@Edge replicas take hours to drain before the function can be deleted. This is normal, not a fault. |
| IAM role | `fcf-platform-edge-auth-role` | Delete after the function. |
| Cognito app client | `future-city-platform-edge` | Delete. The **user pool is pre-existing and shared** — do not delete it. |
| Cognito managed-login branding | per-client record | Deleting it removes the client's sign-in page entirely (see §5). |

**The fastest full rollback** — platform gone, public site and NFC layer untouched — is to set
`CacheBehaviors.Quantity` to `0` and re-send the distribution config. Everything else can be
cleaned up afterwards at leisure.

`docs/operations/v4-program/cloudfront-config-before-platform.json` holds the distribution
configuration as it was before each change (account id redacted), rewritten on every run of the
deploy script.

---

## 3. Cost

**Measured, not projected.** Total spend on the whole AWS account across the last two monthly
periods, from Cost Explorer: **$0.027** and **$0.386**. The entire account — every project in
it — costs under forty cents a month.

Incremental cost of everything this program added, at on-demand rates, no Free Tier, no credits:

| Item | Measured quantity | Monthly |
|---|---|---|
| S3 storage, gated bundle | 468 objects, 25.74 MB | $0.00059 |
| S3 storage, public site | 37 objects, 1.89 MB (**was 8.1 MB**) | $0.00004 |
| Lambda@Edge | 128 MB, ~50 ms, low hundreds of requests | < $0.001 |
| Cognito | 2 granted users | **$0.00** (free below 50 000 MAU) |
| CloudFront | existing distribution, marginal requests | negligible |
| **Total incremental** | | **< $0.01 / month** |

Against a **$10/month** ceiling. Even a conservative upper bound assuming a thousand-fold
traffic increase stays under $1.

The public site got **cheaper**: six identical copies of one background image (6.5 MB of its
8.1 MB) were replaced by a single file, so it is now 1.89 MB. That is a ~77% reduction in bytes
served on the page that used them.

**No always-on compute, no database, no load balancer, no NAT gateway.** The one piece of
compute is Lambda@Edge, which scales to zero and bills per request.

---

## 4. How to deploy

```bash
aws sso login --profile future-city          # the token expires; this is the usual blocker
python scripts/deploy_platform.py            # DRY RUN — prints its plan, changes nothing
python scripts/deploy_platform.py --apply
python scripts/verify_deployment.py          # 33 live assertions, both halves
```

The script is dry-run by default. It is idempotent — re-running with no changes republishes
identical bytes and reports `0 object(s) written`.

### The guard that matters

`update-distribution` is a **whole-config replace**; there is no partial update. A script that
builds the config slightly wrong does not fail, it *successfully deploys a broken site*. So
`assert_safe_change` refuses to send a config in which the default cache behaviour, the
existing origin, the aliases or the certificate differ by so much as a key — and refuses if the
gated behaviour stops pointing at the isolated bucket.

It has already earned that: it caught a redeploy that would have modified the platform origin
in place, and was itself then corrected for crying wolf on unchanged configs. A check that
fails every time is a check people learn to skip.

### Deploying from CI

Deliberately **not enabled**. `.github/workflows/deploy.yml` validates the deploy plan with no
credentials at all — rebuilding every generated artifact from a clean checkout, checking the
website's caveats and embeds, resolving surface links the way S3 resolves them, and exercising
the deploy guards against configs that would gate the NFC layer or drop the alias.

The credentialed job runs only on manual dispatch and only if `AWS_DEPLOY_ROLE_ARN` is set. It
is unset, because configuring it grants **anyone who can dispatch that workflow the ability to
rewrite the live public site**. That is a standing capability and it belongs to the project
owner to grant. Long-lived access keys are not an option — the standing rules forbid them, and
they would be worse.

To enable it: create a GitHub OIDC provider in IAM, a role trusting
`repo:andyyaro/Future-City-Fellowship-:*` scoped to the two buckets plus
`cloudfront:CreateInvalidation` and `cloudfront:UpdateDistribution` on this distribution only,
and set the secret. No OIDC provider exists in the account today.

---

## 5. Risks, and the ones that already happened

| Risk | Status |
|---|---|
| A config change breaks the NFC tags | Guarded by `assert_safe_change`; verified after every deploy by 12 live tag checks |
| A path spelling evades the gate | Structurally impossible — the main bucket has no platform content. 6 spellings tested |
| The gate redirects to a sign-in page that does not exist | **Happened.** See below |
| The website embeds a deleted Tableau workbook | **Happened.** See DEC-019 |
| Cost overrun | Measured monthly; account total is under $0.40 |

**The sign-in page that did not exist.** The gate correctly redirected to Cognito and Cognito
had no page to serve: this pool runs **Managed Login v2**, where every app client needs its own
branding record, and a client without one gets *"Login pages unavailable."* All 32 assertions
passed while the feature was unusable, because they asserted *the gate redirects* — a strictly
weaker claim than *a person can sign in*. The verifier now follows the redirect and asserts a
real password field renders.

**The deleted workbook.** The original Tableau workbook was audited, found wrong, republished
under a new name, and deleted — and nothing re-pointed the website, so 21 embeds across two
pages resolved to `resource-not-found`. Note for any future check: **Tableau answers HTTP 302
for live and deleted views alike**, and both redirect chains end in a 200 carrying the same
1 442-byte shell. Only the final URL distinguishes them.

---

## 6. What is verified, and what is not

**Verified against the live site** (`python scripts/verify_deployment.py`, 33 assertions):
8 gated assets return 302 to Cognito with zero bytes served · 6 alternative path spellings fail
to evade · the Cognito sign-in page renders a real password field · all 12 NFC tag pages return
200 · 6 pre-existing pages unchanged · direct S3 access returns 403 · the main bucket holds 0
objects under `platform/`.

**Verified by a human:** the gate opens, and the platform renders behind it (owner sign-in,
2026-07-27).

**Not verified:** every surface *inside* the platform. "It renders" establishes that
`index.html` and its assets are served through the gate. It does not establish that the
provenance panel resolves, that the explorer and dashboard sub-surfaces load, or that tier
detection reports the web tier correctly. Those are separate claims and no one has exercised
them.

---

## 7. Open items

> **Corrected 2026-07-28.** Every item in this section except the last had been closed and the
> section never updated — it claimed the synthetic set did not exist, that the public installer
> could not be built at all, that Cesium was fetched without a checksum, and that nothing
> carried `--hash` lines. All four were false when read. Found by the DEC-014 line-by-line
> audit. The closures are recorded below rather than the section being silently deleted.

- ~~No synthetic site-input set exists~~ **CLOSED (DEC-020).** Four synthetic files are tracked
  under `data/synthetic/`, and `build_release_artifact.py --public` builds a complete artifact
  by substituting them for the real inputs. Verified by running it.
- ~~`vendor_cesium.sh` has no checksum~~ **CLOSED.** It verifies a pinned **SHA-512** against the
  downloaded tarball (`vendor_cesium.sh:64`).
- ~~`requirements-lock.txt` carries zero `--hash` lines~~ **CLOSED, with a stated limit.**
  `requirements-hashed.txt` carries **839 digests across 27 pins**. The lock itself still has
  none, deliberately: it is used as a *constraints* file for an editable install, and pip
  refuses hashes on an editable requirement. So "reproducible build" is truthful for the clean
  non-editable install and the packaging build, **and for nothing else**.
- ~~`verify-all` will not run on Windows~~ **CLOSED as a disclosure, not as a capability.** The
  operation now declares that it cannot run on a stock Windows machine and names WSL and Git
  Bash as the alternatives (`operations.py`, the `verify-all` operation's `unavailable_reason`). It still does not run there. *(This cited a line number that had already drifted to a different statement — line numbers in prose go stale on the next edit, so it names the thing instead.)*
- **No release version scheme.** *Still open.* `pyproject` pins a static `3.0.0` and the
  existing git tags are milestone markers, not versions.
