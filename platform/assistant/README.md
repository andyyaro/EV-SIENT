# Planner assistant: operations

The Assistant panel in the planner (app.futurecity.andyyaro.com) answers questions about the
method and, if the planner agrees for the session, about summaries of their results. It calls
Claude on Amazon Bedrock through this proxy. Decision: DEC-029 in
`docs/operations/v4-program/DECISIONS.md`. What may be sent: `docs/FLEXIBLE_ANALYSIS.md` section 5.

## How it fits together

```
browser (Assistant panel)                       same origin, so CSP connect-src 'self' covers it
  POST /api/assistant/ask, GET /api/assistant/status
    -> CloudFront E1JXKS26TDP3Z2, behaviour /api/assistant/* (no caching, all viewer headers
       except Host, the evsient-app-headers function), origin access control signs the request
    -> Lambda function URL (AuthType AWS_IAM, RESPONSE_STREAM): evsient-assistant
         1. this instance's token buckets, per viewer address and for everyone (in memory,
            no database call)                                    -> 429
            /status stops here: it is answered from a 30-second in-memory cache
         2. size limit (32 KB), then validate.mjs: closed objects, allowed tiers only -> 413, 400
         3. switched off?                                        -> 503 "switched off"
         4. Bedrock data retention reads "none"? (checked at cold start, then every 15 minutes;
            a failed check is retried after a minute)            -> 503 "not available"
         5. a cap this instance has already seen reached (in memory) -> 503
         6. shared rate limits in DynamoDB (limits.mjs)          -> 429
         7. spend ledger (ledger.mjs): reserve the most this call could cost against the
            month, the day and this visitor's share of the day -> 503 if any would be passed
            ("The assistant has reached this month's limit")
         8. Bedrock InvokeModelWithResponseStream, global.anthropic.claude-haiku-5-5
         9. stream NDJSON lines back; settle the ledger with the actual cost
    -> DynamoDB table evsient-assistant (ledger, rate counters, salt; no text is ever stored)
```

## What the server checks, and what the browser checks

The server enforces the shape and the limits: closed objects with only the allowed keys,
rounded numbers, sanitised labels, no statistics on columns whose role or header marks them
as identifying, sizes, rates and spend. It cannot tell whether a label is really a column
header or a category someone typed, so the content (no cells, names, notes or coordinates)
rests on the browser's payload builder, `platform/app/src/assistant/payload.ts`, which the
property tests in `test/payload.test.mjs` exercise against the 360-site fixture with
unfriendly headers and hidden characters. Both sides strip the same invisible characters
(variation selectors, the combining grapheme joiner, Hangul fillers, the braille blank, tag
characters, zero-width and other format characters) and flag the same identifying headers
(words such as `x`, `y`, `gps`, `fid`, `objectid`, `location`, and any word ending in `id`,
`name`, `address`, `zip`, `postcode`, `phone` or `email`, or starting with `lat`, `lon` or
`lng`). The header rule errs towards sharing less: `valid` or `latest_visit` also send only
their header.

| File | What it is |
|---|---|
| `src/core.mjs` | Request handling, in order of the checks above. No AWS in it |
| `src/validate.mjs` | The server boundary: what the browser may send |
| `src/ledger.mjs`, `src/store.mjs` | The spend ledger and its DynamoDB transactions |
| `src/limits.mjs` | In-memory token buckets, then per address (hashed, by /24 or /56), per session, and global limits |
| `src/retention.mjs` | Reads Bedrock's data retention mode (signed GET) |
| `src/prompt.mjs` | The system prompt, method and common questions |
| `src/pricing.mjs` | Prices per million tokens; the ledger only spends from this table |
| `src/config.mjs` | Settings from the environment; anything malformed refuses every question |
| `src/handler.mjs`, `src/index.mjs` | The Lambda entry point |
| `template.yaml` | CloudFormation: every AWS resource the assistant uses |
| `deploy/deploy.sh` | Tests, retention check, stack, code |
| `deploy/edge_config.py` | Adds or removes the CloudFront origin and behaviour (no AWS calls) |
| `test/*.test.mjs` | `node --test "platform/assistant/test/*.test.mjs"` (also run by pytest) |

The browser side is `platform/app/src/assistant/`: `payload.ts` builds what may be sent,
`AssistantPanel.tsx` shows it and asks, `answer.ts` checks the answer.

## Spend cap: how it holds

- Before each call the proxy reserves the most it could cost: every byte of the request as a
  token at the dearest input rate, plus the full output allowance. Haiku at the size limit
  (32 KB plus the system prompt) is about $0.006. The reservation is a DynamoDB conditional
  transaction, so concurrent calls cannot both take the last cent.
- After the call it settles to the cost Bedrock reports, taking for each kind of token the
  larger of what the stream and the invocation metrics say. A call without a final output
  count, or one that breaks off, keeps its whole reservation; one Bedrock refused outright
  (validation, throttling, access) costs nothing.
- Any error reading or writing the ledger refuses the question. Unsettled reservations stay
  counted. The ledger can overstate spend, never understate it.
- Caps: $5 a month (UTC calendar month), $0.35 a day so one bad day cannot use the month,
  $0.05 a day per visitor (address prefix) so one person cannot use the day, and $1 a month
  for deeper answers (off unless switched on). The visitor share allows roughly 8 questions
  at the size limit and 25 to 50 ordinary ones.
- The price row comes from the model ID (`pricing.mjs`). The proxy refuses to start if
  `ModelPrice` names a different row, or if `ModelExtraJson` sets anything other than
  `thinking` (`disabled` or `adaptive`), `output_config.effort` or `temperature`.
- Budgets and alarms only warn; the ledger is what stops spending.

## Request floods

AWS WAF costs more than the whole non-model budget, so floods are handled in the function:

- Each instance keeps token buckets in memory: per viewer address prefix (3 questions at once,
  then 1 a minute; 10 status checks at once, then 10 a minute) and for everyone (4 questions
  at once, then 3 a minute). A refused request never reaches DynamoDB, and refusals are logged
  once a minute with a count.
- The viewer address is CloudFront's `CloudFront-Viewer-Address` only. `X-Forwarded-For` is
  never used, because a viewer can write it. A request without the header (a misconfigured
  behaviour) goes into one shared, conservative bucket, and the `NoViewerAddress` alarm fires.
- The shared limits in DynamoDB: 12 questions an hour and 30 a day per address prefix, 30 a
  day per session, 20 a minute for everyone.
- `ReservedConcurrency` (template parameter, unset by default) caps the number of instances.
  The account's Lambda concurrency limit is 10 today, which leaves nothing to reserve; once
  the quota increase is granted, deploy with `--param ReservedConcurrency=2`.

Worst case outside model spend, under a sustained flood:

| Item | Cost |
|---|---|
| CloudFront requests (about $1 a million) and Lambda requests ($0.20 a million) | about $1.20 per million flood requests; the same as a flood on any path of the distribution |
| Lambda duration for refused requests (about 5 ms at 256 MB arm64) | about $0.02 per million |
| DynamoDB: at most 3 questions a minute per instance pass the buckets, 10 instances at most, up to 4 write units each | about 1.3 million questions a month, about $3.20; with `ReservedConcurrency=2`, about $0.65 |
| CloudWatch Logs: refusals sampled once a minute | pennies |

So the function adds at most about $3.20 a month (about $0.65 with reserved concurrency) on
top of CloudFront's per-request charge, which only a WAF or CloudFront's flat-rate plan can
cap.

## Deploy (coordinator, after review)

Everything uses `--profile future-city`. Pick the Region once (default plan: `us-east-2`; see
open questions in DEC-029) and use it for every step.

1. **Model access.** In the Bedrock console for that Region, open Model access and confirm
   Anthropic Claude Haiku 5.5 is available (submit Anthropic's first-use form if asked).
2. **Data retention none, invocation logging off** (per account, per Region):
   ```
   aws bedrock get-account-data-retention --region us-east-2 --profile future-city
   aws bedrock put-account-data-retention --mode none --region us-east-2 --profile future-city
   aws bedrock get-model-invocation-logging-configuration --region us-east-2 --profile future-city
   ```
   The last must show no `loggingConfig`. `deploy.sh` checks both and stops otherwise. The
   function also reads the retention mode itself (IAM `bedrock:GetAccountDataRetention`, a
   signed GET of `/data-retention`) when it starts and every 15 minutes, and answers nothing
   unless it reads `none`.
3. **Cost allocation tag.** Activate `Project` as a cost allocation tag (Billing, Cost
   allocation tags) so the non-model budget can see it. It can take a day to appear.
4. **Stack and code:**
   ```
   cd platform/assistant
   deploy/deploy.sh --region us-east-2 --dryrun            # read what it will run
   ALERT_EMAIL=<address> deploy/deploy.sh --region us-east-2
   ```
   Confirm the SNS subscription email. The stack outputs `FunctionUrlDomain` and
   `OriginAccessControlId`.
5. **Smoke test before connecting CloudFront.** A direct call to the function URL must be
   refused (`403`, AuthType AWS_IAM). CloudFront's permission is limited to its own
   distribution, this account and calls through the function URL (`InvokedViaFunctionUrl`). Then one test call with the CLI, which also confirms the
   request fields are accepted (cost: under one cent):
   ```
   aws lambda invoke --function-name evsient-assistant --region us-east-2 --profile future-city \
     --cli-binary-format raw-in-base64-out --payload file://deploy/smoke-event.json out.txt
   ```
   `out.txt` should hold a `meta` line, `text` lines and a `done` line. An `error` line with
   a Bedrock validation error means `ModelExtraJson` needs changing (try `{}`).
6. **Connect CloudFront** (review the diff before applying):
   ```
   aws cloudfront get-distribution-config --id E1JXKS26TDP3Z2 --profile future-city > live.json
   python3 deploy/edge_config.py live.json --domain <FunctionUrlDomain> --oac <OriginAccessControlId> > new.json
   diff <(python3 -m json.tool live.json) <(python3 -m json.tool new.json)
   aws cloudfront update-distribution --id E1JXKS26TDP3Z2 --if-match <ETag> \
     --distribution-config file://new.json --profile future-city
   ```
   Then copy the new behaviour and origin into `platform/infra/distribution-config.json` with
   `ACCOUNT_ID` in place of the account. Delete `live.json` and `new.json`.
7. **Check from a browser:** open the planner, open Assistant, ask one question. Check the
   status line shows Available, and the ledger item `ledger#month#YYYY-MM` has `calls` 1.
8. **Optional guard:** attach the managed policy `evsient-bedrock-retention-none-only` to the
   admin users or roles, so nobody can switch retention back on by mistake.

If CloudFront returns the site's 404 page for `/api/assistant/status`, the request was refused
at the origin (OAC or the Lambda permissions): the distribution turns every 403 and 404 into
`/404.html`, and the proxy itself never returns either.

## Raise or lower the cap

```
deploy/deploy.sh --region us-east-2 --param MonthlyCapUsd=3
deploy/deploy.sh --region us-east-2 --param MonthlyCapUsd=8 --param DailyCapUsd=0.5
```

The new cap applies to the current month at once (the ledger compares what is committed with
the cap on every call). Lowering it below what is already spent pauses the assistant until the
next month. The model budget follows `MonthlyCapUsd`. The template refuses more than $50.

## Turn it off

- **Quickest, keeps everything:** `deploy/deploy.sh --region us-east-2 --param Enabled=false`.
  Every question is refused before the model; the panel says the assistant is switched off.
- **Or:** `--param MonthlyCapUsd=0`, which shows as this month's limit reached.
- **At the edge:** `edge_config.py live.json --remove > new.json` and `update-distribution`;
  the panel then says the assistant could not be reached.
- **Remove it all:** remove the behaviour first, then
  `aws cloudformation delete-stack --stack-name evsient-assistant --region us-east-2 --profile future-city`.
  The table is kept (DeletionPolicy Retain) so a redeploy in the same month remembers what was
  spent; delete it by hand once the month is over.

## Monthly cost outside model spend

At the expected use (a few hundred questions a month), about $0.00 to $0.15:

| Item | Cost |
|---|---|
| Lambda (256 MB arm64, about 5 s a question) | free tier (400,000 GB-seconds and 1M requests a month) |
| DynamoDB on demand (about 16 write units a question) | under $0.01 per 1,000 questions |
| CloudWatch Logs (7 days), 2 metric filters, 4 alarms | $0.00 within the free tier (10 metrics, 10 alarms); $0.80 at most outside it |
| SNS email | free (first 1,000 a month) |
| Budgets (2, no actions) | $0.00 |
| CloudFront requests to /api | under $0.01 |
| Origin access control, IAM, data retention setting | free |

Worst case if every free tier is already used elsewhere: about $1 a month. Under a sustained
flood, see Request floods above: at most about $3.20 more from the function, plus
CloudFront's per-request charge.

## Retiring the old OpenAI assistant (futurecity.andyyaro.com)

Not done here. What it involves, in order:

1. Remove the assistant link and page from the site: `site/redesign/www/assistant.html`,
   `site/www/assistant.html`, and the links to them.
2. Remove the assistant API host from the futurecity.andyyaro.com CSP `connect-src` (response
   headers policy `fcf-redesign-noindex`).
3. Delete API Gateway `future-city-assistant-api` and Lambda `future-city-assistant-chat`.
4. Delete the Secrets Manager secret named by `ASSISTANT_SECRET_ID` (about $0.40 a month), and
   revoke the OpenAI key it holds in the OpenAI dashboard.
5. Remove `infra/assistant/`, `scripts/deploy_assistant.py` and `tests/test_assistant_paths.py`.
6. Close open action 12 (the OpenAI spend cap): there is no OpenAI spend left.
