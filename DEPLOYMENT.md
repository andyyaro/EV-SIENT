# DEPLOYMENT.md

What is deployed, what it cost, what breaks if it goes wrong, and how to undo each piece.

Written for the person who has to change this after the people who built it have moved on.
Every figure below was measured against the live account, not estimated - where something is
an estimate it says so.

---

## 1. What is live

One CloudFront distribution, `E1XZPHWHZV0OEO`, on the alias
**`futurecityfellowship.andyyaro.com`**, serving one thing with one access rule.

| Path | Origin | Who can reach it |
|---|---|---|
| everything | `future-city-fellowship` (private, OAC) | **anyone, no account** |

Until 2026-10-18 a second row sent `/platform*` to a separate private bucket behind a Cognito
sign-in enforced by Lambda@Edge. **The owner retired that path on 2026-10-18 (DEC-030).** The
planner now lives at **https://app.futurecity.andyyaro.com**, carries synthetic samples only, and
needs no sign-in, so nothing on this distribution is gated. `/platform/...` now falls through to
the main bucket, which holds nothing under `platform/`, and returns 404
(`scripts/verify_deployment.py` checks 14 spellings).

Be careful with the default behaviour. `/t/FFX001` … `/t/PWC008` are the **NFC landing
pages** - the twelve pages a reader would reach by tapping a physical coin in a car park, with
no app and no account. **All twelve pages are live and public; no physical tag has been placed
at any site, and no placement permission has been sought** (`docs/nfc/README.md`,
`docs/nfc/PILOT_PLAN.md`). One bench tag was written and read back through iOS background NFC.
**Any change that gates the default cache behaviour breaks all twelve pages** - and once tags
are placed they are not something that can be un-deployed from a car park.

---

## 2. Resources created, and how to remove each

Everything the gated platform needed was created for it alone, and DEC-030 retires all of it.
Nothing below was shared with another project except the Cognito user pool, which stays.

| Resource | Identifier | State after DEC-030 |
|---|---|---|
| CloudFront cache behaviour | `/platform*` | **Removed 2026-10-18.** The default behaviour was not changed |
| CloudFront origin | `platform-gated` | **Removed 2026-10-18** |
| Cognito app client | `future-city-platform-edge` | **Deleted 2026-10-18**, with its managed-login branding |
| Cognito app client | `future-city-assistant-web` | **Deleted 2026-10-18**, with its managed-login branding |
| S3 bucket (gated bundle) | `future-city-fellowship-platform` | To be removed by hand, after a local backup |
| Origin access control | `E1JND6HMX02LBD` | To be removed by hand; the origin that used it is already gone |
| Response headers policy | `fcf-platform-security` | To be removed by hand; nothing references it once the behaviour is gone |
| Lambda@Edge function | `fcf-platform-edge-auth` | To be removed by hand once its edge replicas drain, which takes hours after the association is removed. This is normal, not a fault |
| IAM role | `fcf-platform-edge-auth-role` | To be removed by hand, after the function |
| Log groups | the edge-auth groups in us-east-1 and eu-central-1 | To be removed by hand, after the function |
| Cognito user pool | `us-east-1_mKrwfQTkg` | **Stays.** Pre-existing and shared; the embedded assistant client `future-city-assistant-embedded-client` stays with it |

`scripts/deploy_platform.py` can no longer recreate any of these: it publishes the public site
alone, never sends a distribution config, and refuses a gate or platform mode (section 4).

`docs/operations/v4-program/cloudfront-config-before-platform.json` holds the distribution
configuration as it was before the gate was added (account id redacted). It is a historical
record now, not a rollback target: the default behaviour has gained a response headers policy
since (section 10), which restoring from it would drop.
`docs/operations/v4-program/cloudfront-config-observed.json` is the config as last observed by
the old deploy script, on 2026-10-17, **with the gate still attached**; nothing writes it any
more.

---

## 3. Cost

**Measured, not projected.** Total spend on the whole AWS account across the last two monthly
periods, from Cost Explorer: **$0.027** and **$0.386**. The entire account - every project in
it - costs under forty cents a month.

Incremental cost of everything this program added, at on-demand rates, no Free Tier, no credits:

| Item | Measured quantity | Monthly |
|---|---|---|
| S3 storage, public site | 37 objects, 1.89 MB (**was 8.1 MB**) | $0.00004 |
| CloudFront | existing distribution, marginal requests | negligible |
| **Total incremental** | | **< $0.01 / month** |

Until DEC-030 (2026-10-18) the list also carried the gated bundle (468 objects, 25.74 MB,
$0.00059), Lambda@Edge (< $0.001) and two Cognito users ($0.00). All three go with the gate.

Against a **$10/month** ceiling. Even a conservative upper bound assuming a thousand-fold
traffic increase stays under $1.

The public site got **cheaper**: six identical copies of one background image (6.5 MB of its
8.1 MB) were replaced by a single file, so it is now 1.89 MB. That is a ~77% reduction in bytes
served on the page that used them.

**No always-on compute, no database, no load balancer, no NAT gateway.** On this distribution
there is no compute at all now that the Lambda@Edge gate is retired; the assistant's Lambda
(section 9) scales to zero and bills per request.

---

## 4. How to deploy

```bash
aws sso login --profile future-city          # the token expires; this is the usual blocker
python scripts/deploy_platform.py            # DRY RUN - prints its plan, changes nothing
python scripts/deploy_platform.py --apply
python scripts/verify_deployment.py          # 32 live assertions, both halves
python scripts/check_live_vs_main.py         # every published file byte-identical to main
```

The script is dry-run by default. It is idempotent - re-running with no changes republishes
identical bytes and reports `0 object(s) written`.

### What it publishes, and what it no longer does

It publishes `site/www`, the NFC landing pages (`site/nfc-landing` to `/t/`), the capture forms
(`site/nfc-capture` to `/f/`) and the error page, and nothing else. Pages go up with
`Cache-Control: no-cache`, as the live copies have carried since 2026-10-15; the field pages,
which have no file extension, go up as `text/html;charset=utf-8` with the five-minute cache they
were first uploaded with. Nothing is ever deleted.

Since DEC-030 (2026-10-18) that is all it does. It builds no bucket, origin, cache behaviour,
Lambda version or Cognito branding, and needs no allowlist file. It never sends a distribution
config; it reads the live one and reports anything the retired gate left behind. `--platform`,
`--gate`, `--full`, `--with-gate` and `--platform-only` are refused with exit code 2 and a
message naming DEC-030 and the planner's address. `--www-only`, which used to select this mode,
is still accepted and changes nothing.

It writes `deployed.json` at the site root, naming the commit, and refuses to run while any file
under those folders differs from HEAD, so the marker cannot name a commit that is not what went
live. `check_live_vs_main.py` then fetches every published file and compares it byte for byte
with `origin/main` (audit F-14: production had matched no commit, and nothing compared the two).
It accepts a marker naming an older commit only when no published file changed between that
commit and `main`.

### Nothing the checkout lacks can be deleted from the live site

On 2026-10-17 a full deploy from a checkout that never ran `scripts/vendor_cesium.sh` would have
had the gated bundle's `--delete` sync remove the 377 CesiumJS files the live explorer loaded.
That sync went with the gate. No sync in the script passes `--delete`, a test holds that, and if
a sync ever reports a deletion anyway the deploy stops.

### The guard that matters

`update-distribution` is a **whole-config replace**; there is no partial update. A script that
builds the config slightly wrong does not fail, it *successfully deploys a broken site*. The old
script guarded that with `assert_safe_change`. The public-site deploy does not call
`update-distribution` at all, so a deploy cannot change the default cache behaviour, the
aliases or the certificate. A change to the distribution is a deliberate act by a person, made
with its ETag, and checked afterwards with `scripts/verify_deployment.py`.

### Deploying from CI

Deliberately **not enabled**. `.github/workflows/deploy.yml` validates the deploy plan with no
credentials at all - rebuilding every generated artifact from a clean checkout, checking the
website's caveats and embeds, resolving surface links the way S3 resolves them, and checking
that the deploy refuses the retired gate modes and reports a gate left on the distribution.

The credentialed job runs only on manual dispatch and only if `AWS_DEPLOY_ROLE_ARN` is set. It
is unset, because configuring it grants **anyone who can dispatch that workflow the ability to
rewrite the live public site**. That is a standing capability and it belongs to the project
owner to grant. Long-lived access keys are not an option - the standing rules forbid them, and
they would be worse.

To enable it: create a GitHub OIDC provider in IAM, a role trusting
`repo:andyyaro/Future-City-Fellowship-:*` scoped to the main bucket plus
`cloudfront:CreateInvalidation` and `cloudfront:GetDistributionConfig` on this distribution
only, and set the secret. No OIDC provider exists in the account today. The deploy no longer
needs `cloudfront:UpdateDistribution` or any allowlist secret (DEC-030).

---

## 5. Risks, and the ones that already happened

| Risk | Status |
|---|---|
| A config change breaks the NFC tags | The deploy sends no distribution config at all; verified after every deploy by 12 live tag checks |
| The retired `/platform` path serves something | The main bucket has no platform content; 14 spellings tested to return 404 |
| The gate redirects to a sign-in page that does not exist | **Happened** (before DEC-030). See below |
| The website embeds a deleted Tableau workbook | **Happened.** See DEC-019 |
| Cost overrun | Measured monthly; account total is under $0.40 |

**The sign-in page that did not exist.** The gate correctly redirected to Cognito and Cognito
had no page to serve: this pool runs **Managed Login v2**, where every app client needs its own
branding record, and a client without one gets *"Login pages unavailable."* All 32 assertions
passed while the feature was unusable, because they asserted *the gate redirects* - a strictly
weaker claim than *a person can sign in*. The verifier then followed the redirect and asserted a
real password field rendered, until the gate was retired (DEC-030).

**The deleted workbook.** The original Tableau workbook was audited, found wrong, republished
under a new name, and deleted - and nothing re-pointed the website, so 21 embeds across two
pages resolved to `resource-not-found`. Note for any future check: **Tableau answers HTTP 302
for live and deleted views alike**, and both redirect chains end in a 200 carrying the same
1 442-byte shell. Only the final URL distinguishes them.

---

## 6. What is verified, and what is not

**Verified against the live site** (`python scripts/verify_deployment.py`, 32 assertions,
**32 passed on 2026-10-18** after the gate was removed): 8 former platform assets and 6
alternative spellings of them return 404, with no redirect to Cognito · all 12 NFC tag pages
return 200 · 6 pre-existing pages unchanged.

**Not verified by that script:** that the AWS resources behind the retired gate are gone. It
sees only what a visitor sees; section 2 lists them and their state.

Until 2026-10-18 this section described the gate: 8 gated assets redirected to Cognito, the
sign-in page rendered a real password field, and the owner signed in on 2026-07-27. That history
is in `docs/operations/v4-program/LEDGER.md`.

---

## 7. Open items

> **Corrected 2026-07-28.** Every item in this section except the last had been closed and the
> section never updated - it claimed the synthetic set did not exist, that the public installer
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
  Bash as the alternatives (`operations.py`, the `verify-all` operation's `unavailable_reason`). It still does not run there. *(This cited a line number that had already drifted to a different statement - line numbers in prose go stale on the next edit, so it names the thing instead.)*
- **No release version scheme.** *Still open.* `pyproject` pins a static `3.0.0` and the
  existing git tags are milestone markers, not versions.

---

## 8. Preview environment (separate from production)

Created 2026-10-09 to review the phone layout (`fix/mobile-web`, PR #12) on a real domain
without replacing the live site. **Nothing in sections 1-7 was modified to create it**: the
production distribution, its bucket, its DNS record and its certificate are untouched, and the
only change to the shared `andyyaro.com` zone is three new records.

**`https://preview.futurecityfellowship.andyyaro.com`** serves the public pages (`site/www/`)
and the error page. It does **not** carry the NFC pages (`/t/`, `/f/`) or `/platform/`, and every
response carries `X-Robots-Tag: noindex, nofollow`, so it never competes with the live site in
search.

| Resource | Identifier | Account |
|---|---|---|
| S3 bucket | `future-city-fellowship-preview` (us-east-1, all four public-access blocks on, tagged) | `future-city` |
| Origin access control | `EFND3H1VNU6JZ` (`fcf-preview-oac`) | `future-city` |
| Response headers policy | `fcf-preview-noindex` (`956c5570-…`): the production security headers plus `X-Robots-Tag` | `future-city` |
| CloudFront distribution | `E37O3RT3H2GH39` (`dlanp4cbtcfpr.cloudfront.net`), PriceClass_100, same cache policy and error pages as production | `future-city` |
| ACM certificate | `preview.futurecityfellowship.andyyaro.com`, us-east-1 (`04c12882-…`) | `future-city` |
| Route 53 | `preview.futurecityfellowship.andyyaro.com` A + AAAA alias, and the ACM validation CNAME `_220a9a38….preview.futurecityfellowship` | `cerfodes-dns` |

~~**Known limitation:** the AI assistant page loads, but chat cannot work from the preview.~~
**CLOSED 2026-10-15** (section 9): the assistant API now allows both
`https://futurecityfellowship.andyyaro.com` and the preview origin, and chat works from both.
Measured again 2026-10-17 with `get-api`: `AllowOrigins` lists exactly those two.
On 2026-10-18 a third origin, `https://futurecity.andyyaro.com`, was added for the redesigned
site's own Assistant page (see `site/redesign/README.md`). The two above are unchanged.

**Verified on the preview** (2026-10-09): every page 200, an unknown path 404 via the error
page, direct S3 access 403, and `tests/browser/www_mobile.test.mjs` plus
`www_visibility.test.mjs` run against it with `WWW_URL=https://preview.futurecityfellowship.andyyaro.com`:
**23 / 23, three consecutive runs**.

**Cost:** one more distribution and a bucket holding ~1.7 MB. Well under a cent a month at
preview traffic; no always-on compute.

### Updating the preview

```bash
aws s3 sync site/www s3://future-city-fellowship-preview/ --profile future-city
aws cloudfront create-invalidation --distribution-id E37O3RT3H2GH39 --paths "/*" --profile future-city
```

### Removing it, in order

```bash
# 1. DNS first, so the name stops resolving (cerfodes-dns; DELETE the three preview records only)
# 2. Disable, wait for Deployed, then delete the distribution
aws cloudfront get-distribution-config --id E37O3RT3H2GH39 --profile future-city   # edit Enabled=false, update-distribution with the ETag
aws cloudfront delete-distribution --id E37O3RT3H2GH39 --if-match <ETag> --profile future-city
# 3. Then the pieces it referenced
aws cloudfront delete-response-headers-policy --id 956c5570-3079-4f8c-bff4-cec1195ff7b8 --if-match <ETag> --profile future-city
aws cloudfront delete-origin-access-control --id EFND3H1VNU6JZ --if-match <ETag> --profile future-city
aws s3 rb s3://future-city-fellowship-preview --force --profile future-city
aws acm delete-certificate --certificate-arn <preview cert ARN> --region us-east-1 --profile future-city
```

Promoting the change to production is the normal path in section 4 after PR #12 merges; the
preview is not part of that path and can be removed independently.

---

## 9. The AI assistant is public and reads `main` (2026-10-15)

Changed on the owner's instruction, for a live presentation: no sign-in, and answers grounded
in the current branch.

| Piece | Before | After |
|---|---|---|
| Lambda `future-city-assistant-chat` code | 401 without a Cognito token; curated file lists pointed at the retired V2 layout | Anonymous visitors allowed (keyed by a salted hash of their IP, raw IP never stored); curated lists remapped to 32 files that exist on `main`; raw facility inputs blocked (`data/inputs/`, `data/provenance/`, `data/intake/`, `site/platform/`, `explorer/web/data/`, `matlab/data/`, `data/cache/`); site-wide daily cap |
| Lambda env | `GITHUB_BRANCH=v2-expansion-planning`; 20/h and 100/day per signed-in user | `GITHUB_BRANCH=main`; preview origin added; 150/h and 400/day per visitor (an audience shares one venue IP); `GLOBAL_DAILY_LIMIT=600` |
| GitHub token (Secrets Manager `future-city-assistant-secrets`) | **Rejected by GitHub (401)**, so the assistant had been answering with no repository context | Replaced by the owner with a fine-grained, read-only token for this repository (90 days) |
| API `zale82q9w3`, route `POST /chat` | `AuthorizationType=JWT` (authorizer `2pk8gx`); CORS production only; no throttling | `NONE`; CORS production + preview; stage throttle 3 req/s, burst 10 |
| `assistant.html` | Sign-in gate, token on every request | Gate never shown, no token sent. Uploaded to the preview, and to production **as this one file only**, patched from the live copy |

**Verified:** in fresh browsers on both domains, desktop and phone, no sign-in screen appears
and a question is answered. With the new token, "which site ranks first" is answered FFX004 53.4
from `README.md` on `main`, horizons 2036 / 2046 / 2056, 25 ports with a pathway for 48. Six
probing questions returned none of the private facility values (addresses, per-site figures).

> **Corrected 2026-10-17.** Six questions that found nothing did not show that nothing could be
> found. A probe written to look for the gaps found two: the blocklist named `data/inputs/` but
> not `tests/fixture_*.csv`, which carry the same facility rows, and a script holding the
> platform's login emails was readable and quoted back verbatim. Fixed in section 10.

**Rollback:** Lambda version **1** is the exact pre-change code and configuration. Since
2026-10-17 the integration invokes the `live` alias, so rolling back is
`python scripts/deploy_assistant.py --rollback 1 --apply` (section 10). **Never roll back to
version 2**: it is the 2026-10-15 code whose blocklist let test fixtures and a login email through. Restore the gate with
`aws apigatewayv2 update-route --api-id zale82q9w3 --route-id a3fm87o --authorization-type JWT --authorizer-id 2pk8gx`,
then revert the `setPublicUI` block in `assistant.html` and re-upload.

**The token expires in 90 days.** When it does, the assistant keeps answering but from no
repository context, exactly the failure found today; the log line is
`"phase_4_repo_lookup_error", "error": "HTTP Error 401: Unauthorized"`.

---

## 10. Hardening after the 2026-10-17 audit

Every change below was made against the live account and then measured. None of them touches
the default cache behaviour's origin, the NFC pages, the certificate or DNS.

### The assistant

| Piece | Before | After |
|---|---|---|
| Source | Only inside AWS: `$LATEST` plus one published version, nothing in any branch | `infra/assistant/lambda_function.py` is the source; `scripts/deploy_assistant.py` is the only route to AWS |
| Integration `zuu51m1` | Invoked the unqualified function, so `$LATEST` (any console edit) reached visitors at once | Invokes the alias `future-city-assistant-chat:live` |
| Path rule | Blocklist of seven directories | **Allowlist** (`PUBLIC_PATH_PREFIXES`, `PUBLIC_EXACT_PATHS`): a new directory is unreadable until someone decides it is public. Readable files 310 -> 161 |
| Excerpts | Passed to the model as read | Email addresses and UUIDs replaced before the model sees them, and the instructions forbid revealing contact details |
| Limits | 150/h and 400/day per visitor | 20/h and 60/day per visitor, `GLOBAL_DAILY_LIMIT=600`, `RATE_LIMIT_FAIL_CLOSED=true` (if the usage table cannot be read, the request is refused rather than allowed) |

`tests/test_assistant_paths.py` runs the deployed rule over the tracked tree and fails if a
private file becomes readable or a readable file carries an email address.

**Versions** (each immutable; `live` points at one of them):

| Version | What it is |
|---|---|
| 1 | June 2026 code, Cognito sign-in required, branch `v2-expansion-planning`. The pre-2026-10-15 state |
| 2 | 2026-10-15 public code with the blocklist. **Do not roll back to it** |
| 3 | 2026-10-17 allowlist and redaction, old limits |
| 4 | Same code as 3, new limits. **`live` points here** |

```bash
python scripts/deploy_assistant.py                       # dry run: repository vs deployed code
python scripts/deploy_assistant.py --apply               # upload, publish a version, move `live`
python scripts/deploy_assistant.py --rollback 3 --apply  # point `live` back at version 3
```

**Not possible: reserved concurrency.** The account's concurrent-execution limit is 10, and
Lambda keeps 10 unreserved, so no function in this account can reserve any. The stage throttle
(3 req/s, burst 10) and the per-visitor and site-wide caps are the cost controls. A spend cap on
the OpenAI key is the backstop, and only the key's owner can set it.

### Response headers

Measured 2026-10-17: production sent **no** security headers at all, while the preview, created
later, sent all of them.

| Behaviour | Policy | Headers |
|---|---|---|
| Default (public site, NFC pages) | `fcf-production-security` (`480181a4-…`) | HSTS 1 year, `nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-XSS-Protection` |
| ~~`/platform*`~~ | ~~`fcf-platform-security` (`ab666a54-…`)~~ | Behaviour removed 2026-10-18 (DEC-030); the policy is to be deleted by hand |

HSTS deliberately has no `includeSubDomains` and no `preload`: the `andyyaro.com` zone is shared
with other projects. There is **no Content-Security-Policy** yet; one needs an inventory of every
inline script and CDN the pages load, and a wrong one breaks pages silently.

`scripts/deploy_platform.py` never sends a distribution config, so it cannot drop the default
behaviour's policy.

Verified on `/` and on the NFC page `/t/FFX001` (and, until DEC-030, on the `/platform/` sign-in
redirect).

**Rollback:** remove `ResponseHeadersPolicyId` from the behaviour and re-send the whole config
with its ETag, then delete the policy.

### Accounts, logs, storage

| Piece | Before | After | Rollback |
|---|---|---|---|
| Cognito pool `us-east-1_mKrwfQTkg` MFA | `OFF` | `ON`, authenticator app (TOTP). Each user enrolls at their next sign-in | `set-user-pool-mfa-config --mfa-configuration OFF` |
| Log retention | Never expire | 30 days: `/aws/lambda/future-city-assistant-chat`, and the edge-auth groups in us-east-1 and eu-central-1 (those two go with the gate, DEC-030) | `delete-retention-policy` |
| `future-city-fellowship-platform` versioning | Off | `Enabled`, like the main bucket. The bucket goes with the gate (DEC-030) | Can be suspended, never removed |

**Lambda@Edge writes its logs in the region of the edge location that served the request**, and
creates that region's log group on first use with no retention. Only us-east-1 and eu-central-1
existed on 2026-10-17. When the function is deleted (DEC-030), check every region once with
`aws logs describe-log-groups --region <r>` and delete any edge-auth group left behind.

### The `/platform` allowlist is out of the repository, and so is the gate

The edge gate's allowlist (two people's Cognito ids and login emails) was inline in
`infra/edge-auth/index.mjs` until 2026-10-17, then moved to a gitignored `granted.mjs`. On
2026-10-18 the gate itself was retired (DEC-030): `infra/edge-auth/index.mjs`, its example
allowlist and its tests were removed from the repository, and the deploy no longer needs the
allowlist file. `infra/edge-auth/granted.mjs` stays in `.gitignore`, so a copy left on a
maintainer's disk can never be committed. **The identities remain in the repository's
history**; removing them from history is a rewrite of every clone and is part of cleaning the
repository before it is made public (`docs/operations/open-human-actions.md`, row 14).

**Not enabled, on purpose: CloudFront access logs.** They would record every visitor's IP
address and path, and `privacy.html` promises short-lived technical logs only.

