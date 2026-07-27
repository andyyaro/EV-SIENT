# AWS_INVENTORY.md — discovered state, before any change

**Phase 0.5 — read-only discovery. Nothing in this document was created, modified, or deleted by the
discovery that produced it.** Every line below was observed by an AWS CLI call or an HTTP request on
**2026-07-27 (UTC)**, with `--profile` passed explicitly on every command and the default profile never used.

> **No account IDs, ARNs containing them, tokens, or keys are reproduced in this file.** Where an identifier
> is needed it appears as a documented placeholder (`<ACCOUNT_FC>`, `<ACCOUNT_DNS>`). The concrete values live
> only in the local, never-committed `fcf-preflight.sh` and in the operator's SSO session.

---

## 1. Identity verification

Both profiles were verified before any other call, and both matched the expected accounts exactly.

| Profile | Expected account | Observed account | Result | Access path |
|---|---|---|---|---|
| `future-city` | `<ACCOUNT_FC>` (995…706) | matched | **PASS** | SSO assumed role, `MyOUAccountsPermissionSet` |
| `cerfodes-dns` | `<ACCOUNT_DNS>` (530…488) | matched | **PASS** | SSO assumed role, `AdministratorAccess` |

Thirteen profiles are configured on this machine. Only these two are in scope. Every command in this program
passes `--profile` explicitly; `sudo` is never used.

---

## 2. The live site, end to end

```
  futurecityfellowship.andyyaro.com
      │
      │  Route 53  ·  zone andyyaro.com  (Z0099021130Y6AWD2BDB)  ·  profile cerfodes-dns
      │  A / ALIAS  ->  d2lqiilk2m0w7v.cloudfront.net
      ▼
  CloudFront  E1XZPHWHZV0OEO   (Deployed, Enabled)
      │  cert  ACM us-east-1, futurecityfellowship.andyyaro.com, ISSUED, in use
      │  TLSv1.2_2021, sni-only, HTTP/2, IPv6 on, compress on, redirect-to-https
      │  DefaultRootObject index.html · PriceClass_All · no WAF · no logging
      │  cache policy   Managed-CachingOptimized      (658327ea-…)
      │  headers policy Managed-SecurityHeadersPolicy (5cc3b908-…)
      │  0 CloudFront Functions · 0 Lambda@Edge · 0 custom error responses · 0 extra behaviours
      │  OAC  EVHYBKH7JLT36
      ▼
  S3  future-city-fellowship   (us-east-1, versioning ENABLED, all four public-access blocks ON, untagged)
      bucket policy: s3:GetObject to the CloudFront service principal, conditioned on this distribution only
```

DNS validation for the certificate is a `_…` CNAME in the same zone. The zone `andyyaro.com` holds 25 records
total and is shared with unrelated projects — **only the two `futurecityfellowship.*` records belong to this
project.** Two other zones exist in `cerfodes-dns` (`bytechisel.com`, `cerfodes-usa.com`); neither is in scope.

### 2.1 What is actually being served — all 16 objects

| Key | Size | Last modified |
|---|---:|---|
| `index.html` | 1,270 B | 2026-06-29 |
| `results.html` | 51,875 B | 2026-06-29 |
| `methodology.html` | 52,244 B | 2026-06-29 |
| `dashboard.html` | 72,687 B | 2026-06-29 |
| `assistant.html` | 70,378 B | 2026-06-29 |
| `reports/Public_EV_Charging_Planning_Report.pdf` | 15,259 B | 2026-06-28 |
| `reports/` | 0 B | folder marker |
| `vendor/amazon-cognito-identity.min.js` | 112,315 B | 2026-06-29 |
| `vendor/` | 0 B | folder marker |
| `top-model-findings-cards-bgs/image1.jpeg` | 44,667 B | 2026-06-28 |
| `top-model-findings-cards-bgs/image1.png` … `image6.png` | 1,295,217 B **each** | 2026-06-28 |

**16 objects, 8,191,997 B total.** All six PNGs share one ETag (`f5587cb2…`) — they are **byte-identical
duplicates**, 7.77 MB of the 8.19 MB total. Last-30-day CloudFront traffic was **2,132 requests /
323,172,829 B**; the duplicated images dominate that transfer.

### 2.2 The landing page is not hosted here

`index.html` is a 1,270-byte shell whose entire body is one `<iframe>` pointing at
**`https://zany-storm-638468.framer.app/`** (reachable, HTTP 200). The public front page's content is
therefore **served by Framer, outside this AWS account and outside the repository**. Any Phase 8 work that
assumes the landing page can be corrected by an S3 sync is wrong. Recorded as **FIND-AWS-05**.

---

## 3. The AI assistant stack (pre-existing, project-owned)

| Resource | Identifier | Configuration observed |
|---|---|---|
| Cognito user pool | `us-east-1_mKrwfQTkg` ("User pool - pl3gnq") | created 2026-06-29; gates `assistant.html` |
| HTTP API | `zale82q9w3` — `future-city-assistant-api` | one route `POST /chat`, **JWT** authorization; CORS restricted to `https://futurecityfellowship.andyyaro.com`, methods POST/OPTIONS |
| Lambda | `future-city-assistant-chat` | **python3.14**, 128 MB, 30 s timeout, x86_64, 20,749 B package, last modified 2026-06-29 |
| DynamoDB | `future-city-assistant-usage` | **PAY_PER_REQUEST**, 44 items, 76,790 B, keys `pk`/`sk`, 30-day TTL via `USAGE_LOG_TTL_DAYS` |
| Secrets Manager | `future-city-assistant-secrets` | created 2026-06-29, last accessed 2026-07-24 |
| CloudWatch Logs | `/aws/lambda/future-city-assistant-chat` | 59,746 B, **retention: never expire** |
| Client SDK | `vendor/amazon-cognito-identity.min.js` | served from the site's own origin |

The Lambda is rate-limited in its own configuration (`HOURLY_USER_LIMIT=20`, `DAILY_USER_LIMIT=100`,
`RATE_LIMIT_ENABLED=true`), logs no message content (`LOG_MESSAGE_PREVIEW=false`), caps message length at
2,000 characters, and calls a third-party model (`OPENAI_MODEL=gpt-5.4-mini`) whose key is held in Secrets
Manager rather than in the function's environment. **No credential value appears in any environment variable.**
That is a good design and this program will not weaken it.

### 3.1 FIND-AWS-01 (high) — the live assistant is grounded on a superseded branch

The Lambda reads the repository at **`GITHUB_BRANCH=v2-expansion-planning`**, not `main`.

Verified against the actual remote: that branch's tip is `0be9373`, it holds 220 files, and it contains
**zero** files under `data/contract/v1/`. The canonical V3 contract does not exist on the branch the assistant
reads. Every answer the public assistant gives is therefore grounded in the pre-V3 tree — the same tree whose
numbers the V3 CHANGELOG corrected. This is the single most consequential live-surface defect found in
Phase 0, and it is invisible to any repository-only audit.

Not fixed in Phase 0 (discovery is read-only). Carried to **Phase 8**.

---

## 4. Did the website patch package ever get applied? — **No.**

`docs/operations/website-patch-package/` specifies nine patches. Its own README says *"Nothing in this package
has been deployed."* That statement is **still true on 2026-07-27**, confirmed against the live site rather
than assumed from the document.

| Patch | Requirement | Live-site evidence | Applied? |
|---|---|---|---|
| §1 landing | replace "2035/2050" with "2036 / 2046 / 2056"; add authority-disclaimer block; add source-vintage footer | `2036`/`2046`/`2056`: **zero** occurrences across all five pages. `authority`, `vintage`: zero. | **No** |
| §2 dashboard | embed the 9 static assets from `dashboard/static/`; add the capacity-placeholder caption; alt text per image | no `0N_*.png` reference anywhere; page embeds Tableau views instead | **No** |
| §3 results | insert the three-horizon section; keep "0 of 12 sites High confidence" prominent | `0 of 12`: zero occurrences | **No** |
| §4 methodology | append a "V3 (July 2026)" section, keep V2 labelled | no V3 section present | **No** |
| §5 privacy page | create `privacy.html`, link from every footer | `GET /privacy.html` → **403** (object absent) | **No** |
| §6 standards page | create `standards.html` from the standards summary | `GET /standards.html` → **403** (object absent) | **No** |
| §7 limitations | replace surfaced limitations text | `VCDPA`, `UL 2594`, `UL 3600`: zero occurrences | **No** |
| §8 assistant | insert boundary text; update corpus to V3 README + contract README | assistant page has boundary-style copy but corpus branch is `v2-expansion-planning` (§3.1) | **No** |
| §9 accessibility | alt text, one h1, focus states, WCAG AA on new blocks | no new blocks exist to carry it | **N/A** |

Recorded as **FIND-AWS-02 (high)**. Nine unapplied patches carry to **Phase 8**.

### 4.1 FIND-AWS-03 (high) — the live site does not carry the canonical horizons at all

Independent of the patch package: across all five live HTML pages and the served PDF, the canonical horizon
years **2036 / 2046 / 2056 appear zero times**. So do `2035` and `2050`. The live pages are written almost
entirely qualitatively, so this is **not** a case of stale superseded years surviving — it is a case of the
public surface carrying no horizon convention at all while the repository is explicit about one.

The eGRID factor is equally absent: **neither `596.3` nor `590.2` appears anywhere on the live site or in the
served PDF.** The corrected factor is not published; the superseded factor is at least not published either.

`58.8` appears twice, on `results.html`, and FFX002 is correctly named the top overall candidate — the one
headline the live site and the contract agree on. The served PDF
(`Public_EV_Charging_Planning_Report.pdf`, 15 KB) is a different artifact from anything in `reports/` and
contains none of the checked figures.

Full numeric reconciliation of the live site against `data/contract/v1/` is **Phase 1** work; this section
records only what discovery observed.

---

## 5. Project-owned versus unrelated

The `future-city` account holds 20 S3 buckets and 14 CloudFront distributions, almost all belonging to other
projects. **Touch nothing outside the table below.**

**Project-owned (in scope):**

| Type | Identifier |
|---|---|
| S3 bucket | `future-city-fellowship` |
| CloudFront distribution | `E1XZPHWHZV0OEO` (+ OAC `EVHYBKH7JLT36`) |
| ACM certificate | `futurecityfellowship.andyyaro.com` (us-east-1) |
| Route 53 records | `futurecityfellowship.andyyaro.com` A/ALIAS + its ACM validation CNAME, in zone `andyyaro.com` |
| Cognito user pool | `us-east-1_mKrwfQTkg` |
| HTTP API | `zale82q9w3` |
| Lambda | `future-city-assistant-chat` (+ its execution role and log group) |
| DynamoDB table | `future-city-assistant-usage` |
| Secrets Manager secret | `future-city-assistant-secrets` |

**Explicitly not ours** — do not modify: buckets and distributions for `cerfodes-*`, `aga-datathon-*`,
`my-portfolio-crc*`, `valentine-*`, `bintaidea`, `jackportfolioupdate`, `matthieu-bere-*`, `adama-andy`,
`cyse-130`, `grace-birthday`, `ikram-faith-video`, `fall-2025-schedule`, `my-blog-crc`,
`cf-templates-*`; the four `cerfodes-*-web-clean-urls` CloudFront Functions; the Amplify app
`cerfodes-globe`; and the `bytechisel.com` and `cerfodes-usa.com` hosted zones.

---

## 6. Current cost

Observed via Cost Explorer, unblended, `future-city` account:

| Month | Total |
|---|---:|
| 2026-04 | $0.00 |
| 2026-05 | $0.00 |
| 2026-06 | $0.05 |
| 2026-07 (to the 27th) | $0.39 |

July by service (non-zero only): Secrets Manager **$0.3377**, S3 $0.0458, Amplify $0.0050 (the unrelated
`cerfodes-globe` app), API Gateway and DynamoDB $0.0000.

**Estimated project-attributable run rate: ≈ $0.40 / month**, essentially all of it the one Secrets Manager
secret at its flat ~$0.40/secret/month. CloudFront, Route 53, ACM, Cognito, Lambda, and DynamoDB are all
effectively free at this traffic (2,132 requests / 323 MB per 30 days). Note these figures reflect whatever
Free Tier and credits currently apply; **Phase 8 cost estimates must be recomputed at full on-demand rates
with no Free Tier and no credits, per the program's cost rule.**

### Cost-hygiene gaps found (carry to Phase 8)

- **FIND-AWS-04 (medium)** — `/aws/lambda/future-city-assistant-chat` has **no retention policy**; logs are
  kept forever. Explicit retention is required.
- **FIND-AWS-06 (medium)** — **no AWS Budgets exist** in the account. Phase 8 requires a budget alert.
- **FIND-AWS-07 (low)** — **no project resource is tagged.** The S3 bucket has no tag set; the project
  CloudFront distribution has no `Project` tag (nine unrelated distributions carry a `Name` tag, and one
  unrelated certificate carries `Project`/`Environment`, so the account is not uniformly untagged — ours
  simply are not). Phase 8 requires tagging every new resource and should backfill these.
- **FIND-AWS-08 (low)** — six byte-identical 1.3 MB PNGs are stored and served separately, ~7.8 MB of 8.2 MB
  of origin data and most of the 323 MB monthly transfer. Deduplicating is free and reduces both.
- **FIND-AWS-09 (info)** — the project CloudFront distribution has **no custom error responses**. Any
  client-routed path in the Phase 7 web tier, and any NFC short link, will 403 rather than resolve, exactly as
  `/privacy.html` does today. Phase 8 must handle this deliberately.

---

## 7. Change log for this document

| UTC | Change |
|---|---|
| 2026-07-27 | Created from Phase 0.5 read-only discovery. **No AWS resource was created, modified, or deleted.** "After" state to be appended in Phase 8. |
