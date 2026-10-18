# Hosting for app.futurecity.andyyaro.com

The EV-SIENT Planner is a static single-page app. Its Python model runs in the visitor's browser
(Pyodide WebAssembly in a Web Worker), so the hosting only serves files: a private S3 bucket
behind one CloudFront distribution. There is no server-side code. Account IDs are written as
`ACCOUNT_ID` throughout; the JSON files here use that placeholder and are filled in at apply time.

Created 2026-10-18. All resources carry the tag `Project=evsient-platform` where AWS allows tags.

## Resources

| Resource | Name or ID | Profile |
|---|---|---|
| S3 bucket | `future-city-app` (us-east-1) | `future-city` |
| Origin access control | `E44Z5LFBLB257` (`future-city-app-oac`, SigV4, always sign) | `future-city` |
| CloudFront Function | `evsient-app-headers` (cloudfront-js-2.0, viewer-response, LIVE) | `future-city` |
| CloudFront distribution | `E1JXKS26TDP3Z2` (`d27zsj8ci8byf8.cloudfront.net`), comment "EV-SIENT Planner" | `future-city` |
| ACM certificate | `app.futurecity.andyyaro.com`, us-east-1, certificate ID `00d0055c-52cb-426a-9b7d-1fa66dadaf45`, DNS-validated | `future-city` |
| DNS records | A and AAAA alias `app.futurecity.andyyaro.com` to the distribution; ACM validation CNAME `_f6cba6cbc0a2d420337d921418190291.app.futurecity.andyyaro.com` | `cerfodes-dns` (zone `Z0099021130Y6AWD2BDB`) |

### Files in this folder

| File | What it is |
|---|---|
| `headers-function.js` | Source of the CloudFront Function. The only place the CSP is defined |
| `function-test-event.json` | Viewer-response event for `aws cloudfront test-function` |
| `distribution-config.json` | The distribution config as created (`ACCOUNT_ID` placeholder) |
| `bucket-policy.json` | The bucket policy (`ACCOUNT_ID` placeholder) |
| `dns-change.json` | The A and AAAA alias records |
| `dns-cert-validation.json` | The ACM validation CNAME |

## Settings and why

**Bucket.** Private, all four Block Public Access settings on, Object Ownership
`BucketOwnerEnforced` (ACLs disabled), default encryption SSE-S3 (AES256) with a bucket key,
SSE-C uploads blocked (the S3 default). The policy allows `s3:GetObject` only to the CloudFront
service principal when `AWS:SourceArn` is this distribution, and denies any request not made
over TLS. There is no `s3:ListBucket` grant, so a missing key returns 403 from S3, which the
distribution turns into the 404 page. Direct S3 URLs return 403.

**Distribution.** One S3 origin through OAC (no legacy OAI). Two behaviours:

| Behaviour | Cache policy | Viewer protocol | Compress | Function |
|---|---|---|---|---|
| Default (`*`) | Managed-CachingOptimized | redirect-to-https | on | `evsient-app-headers` on viewer-response |
| `/runtime/*` | Managed-CachingOptimized | redirect-to-https | on | `evsient-app-headers` on viewer-response |

The `/runtime/*` behaviour is the same as the default today. It is separate so the runtime can
get its own settings later (for example a different origin or path rewrite) without touching
the app shell, and it matches the four-behaviour layout in the build plan.

Other settings: default root object `index.html`; custom error responses 403 and 404 to
`/404.html` with status 404 (error caching 60 s); PriceClass_100 (North America and Europe
edges, the cheapest class); HTTP/2 and HTTP/3; IPv6 on; SNI-only TLS with minimum
`TLSv1.2_2021`; no logging; no WAF web ACL; GET and HEAD only. The app routes with the URL hash
(`#/start`), so mapping unknown paths to a 404 does not break deep links.

Managed-CachingOptimized (`658327ea-f89d-4fab-a63d-7e88639e58f6`) has no query strings, headers or
cookies in the cache key, gzip and Brotli on, minimum TTL 1 s, default 1 day, maximum 1 year,
and it honours the origin's `Cache-Control`. Only managed policies are used, so the distribution
can move to a flat-rate plan without changes.

**Function, not a response headers policy.** Flat-rate plans allow only AWS-managed cache,
origin-request and response-headers policies. CloudFront Functions are included at every tier,
so a viewer-response function sets the headers instead. The function is associated with this
distribution only, which a flat-rate plan also requires.

**Certificate.** ACM public certificate, DNS-validated. It is valid until 2027-05-03 and renews
automatically (`RenewalEligibility: ELIGIBLE`) as long as the validation CNAME stays in the zone.
Do not delete that record.

## Headers and the CSP

Every response, including the 404 page and the runtime files, gets:

| Header | Value |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self'; connect-src 'self' https://tiles.openfreemap.org; img-src 'self' data: blob: https://tiles.openfreemap.org; style-src 'self' 'unsafe-inline'; font-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests` |
| `Strict-Transport-Security` | `max-age=31536000` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `no-referrer` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=(), usb=()` |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `X-Robots-Tag` | `noindex, nofollow` |

`'wasm-unsafe-eval'` lets the browser compile WebAssembly; it does not allow `eval()` of
JavaScript strings. On 2026-10-18 Pyodide 314.0.7 was loaded, with numpy and pandas, under this
exact live CSP in headless Chromium and WebKit. It ran Python with no CSP violations, so Pyodide
does not need `'unsafe-eval'` here.

### Changing the CSP

The CSP is the `CSP` list at the top of `headers-function.js`, one directive per line. Edit it
there and nowhere else, then:

```bash
cd platform/infra
ETAG=$(aws cloudfront describe-function --name evsient-app-headers --profile future-city --query ETag --output text)
aws cloudfront update-function --name evsient-app-headers --if-match "$ETAG" \
  --function-config '{"Comment":"EV-SIENT Planner security headers (viewer-response)","Runtime":"cloudfront-js-2.0"}' \
  --function-code fileb://headers-function.js --profile future-city --query ETag --output text
# use the ETag printed above
aws cloudfront test-function --name evsient-app-headers --if-match <ETag> --stage DEVELOPMENT \
  --event-object fileb://function-test-event.json --profile future-city \
  --query 'TestResult.[FunctionErrorMessage,FunctionOutput]' --output text
aws cloudfront publish-function --name evsient-app-headers --if-match <ETag> --profile future-city
```

Publishing updates the live distribution within a few minutes. No invalidation is needed,
because the function runs on every response, cached or not. Check with
`curl -sI https://app.futurecity.andyyaro.com/ | grep -i content-security`.

## Deploy

```bash
cd platform/app && npx vite build            # or: npm run build
platform/tools/deploy.sh platform/app/dist   # add --dryrun to see the plan, --sourcemaps to upload *.map
```

The `runtime/` folder comes from `platform/app/public/runtime/` (written by
`platform/tools/fetch_runtime.mjs` and `build_engine.py`) and Vite copies it into `dist/`.

What `deploy.sh` does (profile `future-city`; it touches only this bucket and distribution):

| Files | Content-Type | Cache-Control |
|---|---|---|
| `*.html`, `sw.js`, `registerSW.js`, `*.webmanifest`, `runtime/engine/engine.json` | by extension | `no-cache` |
| `assets/**` (Vite, content-hashed names), `runtime/**` (versioned folders and hashed names) | by extension | `public, max-age=31536000, immutable` |
| Everything else (`icon.svg`, `theme.js`, `samples/*.csv`) | by extension | `public, max-age=300` |

- Content types are set explicitly per extension, including `.wasm` as `application/wasm`
  (needed for `WebAssembly.instantiateStreaming`), `.js` and `.mjs` as `text/javascript`, `.whl`
  and `.zip` as `application/zip`, and `.json` as `application/json`. An unknown extension is
  uploaded as `application/octet-stream` with a warning; add it to `content_type` in the script.
- `runtime/engine/engine.json` is the pointer to the current content-hashed engine archive. Its
  name never changes, so it is `no-cache`. The app fetches it with `cache: 'no-cache'`, but
  CloudFront ignores that request header, so the object's own `Cache-Control` is what matters.
- Source maps (`*.map`) are skipped unless `--sourcemaps` is given. Dotfiles are skipped.
- Immutable files already in the bucket with the same key and size are not re-uploaded.
- Upload order: immutable files, then short-lived files, then `no-cache` files, with
  `index.html` last, so a new `index.html` never points at a file that is not there yet.
- Stale keys outside `assets/` and `runtime/` are deleted. Old files under `assets/` and
  `runtime/` are kept, so open tabs keep working and the previous runtime stays available for
  rollback. Clean them up by hand now and then (`aws s3 ls s3://future-city-app/assets/ --profile future-city`).
- It invalidates only `/`, `/index.html` and `/404.html` (the first 1,000 invalidation paths a
  month are free).

### Compression

CloudFront compresses on the fly only objects of 1,000 to 10,000,000 bytes, only listed content
types (`application/wasm`, `text/javascript`, `application/json`, `text/css` and others, but not
`application/zip`), and only on a best-effort basis: if an edge skips compression under load, it
caches and serves the uncompressed copy until the object expires, which for an immutable
runtime file can be a year.

The runtime as of 2026-10-18:

| File | Size | Brotli 11 | CloudFront would compress? | Choice |
|---|---|---|---|---|
| `pyodide.asm.wasm` | 9.60 MB | 2.77 MB | Yes, but only 0.4 MB under the 10 MB limit | Pre-compressed |
| `pyodide.asm.mjs` | 1.25 MB | 0.21 MB | Yes | Pre-compressed |
| `python_stdlib.zip` | 2.55 MB | 2.49 MB | No (`application/zip`) | As is (already deflated) |
| `pandas-*.whl` | 4.18 MB | 4.14 MB | No | As is (already deflated) |
| `numpy-*.whl` | 2.96 MB | similar | No | As is (already deflated) |

So `deploy.sh` pre-compresses with Brotli (quality 11) every file under `assets/` or `runtime/`
of 1 MB or more with a compressible type (`.wasm .mjs .js .json .css .svg .html .txt .csv
.xml`), and uploads it with `Content-Encoding: br`. CloudFront then passes it through unchanged
and never recompresses it. Reasons:

- The wasm is the largest download, and a future Pyodide version could cross 10 MB, at which
  point CloudFront would send 9.6+ MB uncompressed with no warning.
- Best-effort edge compression can leave an uncompressed copy cached for a year.
- Brotli 11 is smaller than edge compression (2.77 MB against about 3.3 MB at Brotli 5 or
  3.5 MB with gzip for the wasm).

The trade-off is that these objects are always sent as Brotli, whatever the request's
`Accept-Encoding`. Every browser that runs WebAssembly decodes Brotli over HTTPS (Chrome 50,
Firefox 44, Safari 11, Edge 15 and later), so for this app that costs nothing. A plain `curl`
without Brotli support gets compressed bytes. Zip and wheel files are left alone because they
are already deflate-compressed (Brotli saves 1 to 2 %). Smaller files are left to CloudFront.
Verified live: the decoded wasm and mjs match the originals byte for byte, and Vite's JS and CSS
come back `Content-Encoding: br` from the edge.

## Verify

```bash
H=app.futurecity.andyyaro.com
curl -sI https://$H/                       # 200 and all headers above
curl -sI http://$H/                        # 301 to https
curl -sI https://$H/nope                   # 404, the 404 page
curl -sI https://$H/runtime/pyodide/314.0.7/pyodide.asm.wasm   # application/wasm, br, immutable
curl -s -o /dev/null -w '%{http_code}\n' https://future-city-app.s3.us-east-1.amazonaws.com/index.html  # 403
dig +short AAAA $H; curl -6 -sI https://$H/
```

All of these passed on 2026-10-18.

## Expected monthly cost

About $0.00 to $0.01 a month at expected traffic, all within always-free allowances or
fractions of a cent:

| Item | Pricing | Expected |
|---|---|---|
| CloudFront (pay-as-you-go) | Always free each month: 1 TB out, 10M HTTP(S) requests, 2M CloudFront Function invocations | A first visit that starts the engine is about 36 requests and 14 MB (compressed runtime included; repeat visits are mostly browser cache hits). 1,000 first visits a month is about 14 GB and 36,000 requests: $0 |
| CloudFront Function | $0.10 per million after 2M free | Runs once per response, so within the free 2M |
| Invalidations | First 1,000 paths a month free | 3 paths per deploy |
| S3 storage | $0.023 per GB-month (Standard) | About 25 MB, plus old hashed files kept for rollback: under $0.01 |
| S3 requests | PUT $0.005 per 1,000; GET $0.0004 per 1,000 | Under 40 PUTs per deploy; GETs only on CloudFront cache misses: under $0.01 |
| S3 to CloudFront transfer | Free | $0 |
| ACM public certificate | Free | $0 |
| Route 53 | Zone already paid by the DNS account; alias queries to CloudFront are free | $0 added |
| OAC | Free | $0 |

Nothing here has a monthly fee: no WAF web ACL, no Shield Advanced, no Lambda@Edge, no logging.
The main exposure is a traffic flood under pay-as-you-go (beyond 1 TB, about $0.085 per GB in
PriceClass_100). The flat-rate Free plan below removes that exposure.

## CloudFront flat-rate Free plan (not applied)

Findings on 2026-10-18 (nothing was subscribed and billing was not changed):

- **The account is eligible.** It already has two ACTIVE `CloudFront` `FREE` subscriptions
  (distributions `E2W48EXX0MR39U`, project.andyyaro.com, and `E3ABKCP34KHUVO`,
  valentine.andyyaro.com), each with a `CreatedByCloudFront-*` WAF web ACL. The account-level
  exclusion ("Your account is using AWS Free Tier") therefore does not apply.
  `aws freetier get-account-plan-state` returns `ResourceNotFoundException`, which means it is
  not on the new free account plan.
- **One Free slot is left.** The quota is 3 Free plans per account and cannot be increased.
  Using it here means no other distribution can get a Free plan later.
- **This distribution is compatible as built:** managed cache policy only, no response headers
  policy, OAC (not OAI), no legacy `ForwardedValues`, no real-time logs, no Lambda@Edge,
  2 of the 5 allowed behaviours, and its function is not shared with another distribution.
- **A WAF web ACL is required.** The plan needs a web ACL associated with the distribution. It
  is covered while the plan is active. It cannot be removed while subscribed, and if the plan is
  later cancelled the web ACL is billed at pay-as-you-go rates ($5 a month plus $1 per rule)
  unless it is disassociated and deleted at the same time. Free plans cancel immediately.
- **How to subscribe:**
  - Console (simplest; it creates the web ACL and the subscription in one step): CloudFront
    console, distribution `E1JXKS26TDP3Z2`, the pricing plan option, choose Free.
  - API: `PricingPlanManager` `CreateSubscription` in us-east-1 with `planFamily=CloudFront`,
    `planTier=FREE` and `resourceArns` holding the distribution ARN and a WAFv2 web ACL ARN
    (scope CLOUDFRONT). The web ACL must exist and be associated first (`WebACLId` in the
    distribution config). The CLI command is `aws pricing-plan-manager create-subscription`,
    but the installed AWS CLI (2.35.23) does not have it yet; a newer CLI or boto3 1.43 does.
    Create the web ACL just before subscribing, since it bills until the plan covers it.
- Free plan allowance: 1M requests and 100 GB a month, no overage charges; requests blocked by
  WAF do not count. At about 14 MB per first visit, 100 GB is roughly 7,000 first visits a month.

## Adding `/hub/*` and `/api/*` later

The plan reserves two more behaviours (the Free plan allows five):

- `/hub/*`: county data packs. Either another prefix in this bucket (no new origin; add a
  behaviour with Managed-CachingOptimized and the same function) or a second bucket with its own
  OAC. Add `hub/**` handling to `deploy.sh` or give the hub its own publish script.
- `/api/*`: the assistant proxy, a Lambda function URL behind a Lambda-type OAC. Use
  Managed-CachingDisabled and Managed-AllViewerExceptHostHeader, allow all methods, and attach
  the same function (or a variant without HTML-only headers). The CSP needs no change because
  the API is same-origin (`connect-src 'self'`).

Add each behaviour by fetching the live config (`aws cloudfront get-distribution-config`),
adding the item to `CacheBehaviors`, and `update-distribution --if-match <ETag>`. Update
`distribution-config.json` here to match.

## How this differs from futurecity.andyyaro.com

| | futurecity.andyyaro.com (`E3RNYDDSMJAZUR`) | app.futurecity.andyyaro.com (`E1JXKS26TDP3Z2`) |
|---|---|---|
| Content | Flat HTML pages, no build step | Vite build plus Pyodide runtime (about 21 MB) |
| Security headers | Custom response headers policy `fcf-redesign-noindex` | CloudFront Function `evsient-app-headers` (flat-rate compatible) |
| CSP | Strict; `connect-src` adds Cognito and the assistant API | Adds `'wasm-unsafe-eval'` and the OpenFreeMap tile host (workers come only from `'self'`: the engine worker and MapLibre's bundled worker); same-origin only otherwise |
| Behaviours | Default only | Default plus `/runtime/*` |
| Caching | HTML `no-cache`, everything else 5 minutes | HTML `no-cache`; hashed and runtime files 1 year immutable; others 5 minutes |
| Compression | Edge only | Edge, plus Brotli pre-compression for large runtime files |
| Invalidation | `/*` each deploy | `/`, `/index.html`, `/404.html` only |
| Stale files | `--delete` removes everything stale | Keeps old `assets/` and `runtime/` for open tabs and rollback |
| Bucket policy | `s3:GetObject` for its distribution only | Same, plus a deny on non-TLS requests |
| Shared settings | PriceClass_100, HTTP/2 and 3, IPv6, TLSv1.2_2021, SNI, ACM us-east-1, managed CachingOptimized, 403/404 to `/404.html`, DNS in the `cerfodes-dns` zone | same |
