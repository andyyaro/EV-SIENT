# Planner assistant: operations

The Assistant panel in the planner (app.futurecity.andyyaro.com) answers questions about the
method and, if the planner agrees for the session, about summaries of their results. It calls
a model through this proxy. `Provider` picks which:

- `openai`, the default since 19 October 2026: OpenAI's Responses API with `gpt-5.4-mini`, on
  the key the site's earlier assistant already uses (Secrets Manager, `us-east-1`).
- `bedrock`: Claude on Amazon Bedrock, built and kept working for when Bedrock offers
  Anthropic models on this account (it does not today; a support case is open).
- `anthropic`: Anthropic's Claude API directly, built and tested, not in use.

Decision: DEC-029 and its addendum in `docs/operations/v4-program/DECISIONS.md`. What may be
sent: `docs/FLEXIBLE_ANALYSIS.md` section 5.

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
         4. the provider is ready? (checked at cold start, then every 15 minutes; a failed
            check is retried after a minute)                     -> 503 "not available"
            openai: the API key was read from the Secrets Manager secret
            anthropic: the API key was read from SSM Parameter Store
            bedrock: Bedrock data retention in this Region reads "none"
         5. a cap this instance has already seen reached (in memory) -> 503
         6. shared rate limits in DynamoDB (limits.mjs)          -> 429
         7. spend ledger (ledger.mjs): reserve the most this call could cost against the
            month, the day and this visitor's share of the day -> 503 if any would be passed
            ("The assistant has reached this month's limit")
         8. openai: POST https://api.openai.com/v1/responses (streaming, store false),
            gpt-5.4-mini
            anthropic: POST https://api.anthropic.com/v1/messages (streaming), claude-haiku-5-5
            bedrock: InvokeModelWithResponseStream, global.anthropic.claude-haiku-5-5
            No retries; the call stops at the 45-second timeout or when the viewer goes away
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
| `src/openai.mjs` | The OpenAI Responses API call, its events translated into the ones `core.mjs` reads |
| `src/anthropic.mjs` | The Claude API call |
| `src/sse.mjs`, `src/apikey.mjs` | Server-sent events parsing; the API key held in memory |
| `src/retention.mjs` | Reads Bedrock's data retention mode (signed GET) |
| `src/prompt.mjs` | The system prompt, method and common questions |
| `src/pricing.mjs` | Prices per million tokens; the ledger only spends from this table |
| `src/config.mjs` | Settings from the environment; anything malformed refuses every question |
| `src/handler.mjs`, `src/index.mjs` | The Lambda entry point |
| `template.yaml` | CloudFormation: every AWS resource the assistant uses |
| `deploy/deploy.sh` | Tests, the provider's checks, stack, code |
| `deploy/edge_config.py` | Adds or removes the CloudFront origin and behaviour (no AWS calls) |
| `test/*.test.mjs` | `node --test "platform/assistant/test/*.test.mjs"` (also run by pytest) |

The browser side is `platform/app/src/assistant/`: `payload.ts` builds what may be sent,
`AssistantPanel.tsx` shows it and asks, `answer.ts` checks the answer.

## Spend cap: how it holds

- Before each call the proxy reserves the most it could cost: every byte of the request as a
  token at the dearest input rate, plus the full output allowance. At the size limit (32 KB
  plus the system prompt) that is about $0.037 with gpt-5.4-mini ($0.006 with Haiku 5.5); an
  ordinary question reserves about $0.015 and costs about $0.004. The reservation is a
  DynamoDB conditional transaction, so concurrent calls cannot both take the last cent.
- After the call it settles to the cost the provider reports, taking for each kind of token
  the larger count the stream (and, on Bedrock, the invocation metrics) gives. OpenAI reports
  usage once, in `response.completed` (or `response.incomplete`); cached input tokens are
  priced at the cached rate and reasoning tokens as output. A call without a final usage
  count, or one that breaks off or fails mid-answer, keeps its whole reservation; one the
  provider refused outright (an HTTP error from OpenAI or the Claude API; validation,
  throttling or access on Bedrock) costs nothing.
- Any error reading or writing the ledger refuses the question. Unsettled reservations stay
  counted. The ledger can overstate spend, never understate it.
- Caps: $5 a month (UTC calendar month), $0.35 a day so one bad day cannot use the month,
  $0.05 a day per visitor (address prefix) so one person cannot use the day, and $1 a month
  for deeper answers (off unless switched on, and Claude only). With gpt-5.4-mini the visitor
  share allows about 4 questions a day at the size limit and about 10 ordinary ones; the day
  about 80 ordinary questions; the month about 1,100.
- The price row comes from the provider and the model ID (`pricing.mjs`). gpt-5.4-mini is
  $0.75 per million input tokens, $0.075 cached and $4.50 output: OpenAI's standard list price
  as read on 19 October 2026 from developers.openai.com/api/docs/pricing. **Verify it against
  OpenAI's current price list before each deploy**; if it has changed, change `pricing.mjs`
  and its test first. The proxy refuses to start if the model ID is not one the provider uses
  or has no price row, or if `MODEL_PRICE` names a different row.
- Extra request fields come from an allow-list only. OpenAI (`OpenAIExtraJson`, default `{}`
  as the earlier assistant sends): `reasoning.effort` and `text.verbosity`. The output limit
  is `MAX_TOKENS` (1200), never an extra field, because the reservation is worked out from it.
  Claude (`ModelExtraJson`): `thinking` (`disabled` or `adaptive`), `output_config.effort`,
  `temperature`. Anything else refuses to start.
- Budgets and alarms only warn; the ledger is what stops spending.
- **A second cap outside AWS, at the provider.** AWS budgets do not see OpenAI or Claude API
  spend; the provider bills it. With OpenAI, the owner sets a monthly budget on the OpenAI
  project that holds the key (open action 12 in `docs/operations/open-human-actions.md`,
  still open: the key is shared with the earlier site assistant, which has no cap of its
  own). With the Claude API: a $5 monthly spend limit on the Claude Console workspace and
  prepaid credits only. The $5 ledger stays the hard cap in this code either way.

## Where questions go

Whatever the provider, only the question, the conversation so far, the current step, the
file's size and, with consent for the session, the summaries listed above are sent. Rows,
cells, names and the file never leave the browser.

- **OpenAI (`Provider=openai`, the default):** OpenAI's standard API data terms apply. The
  panel and the system prompt say exactly that and claim no more: no zero retention, no
  particular retention period. The request sets `store: false`, so OpenAI does not keep the
  response for later retrieval through the API, and sends no metadata (the earlier assistant
  sent a session ID and a user ID; this proxy sends neither).
- **Claude API (`Provider=anthropic`):** Anthropic's standard commercial terms apply. Per
  Anthropic's privacy centre (privacy.claude.com, read 19 October 2026), inputs and outputs are
  not used to train models by default, and are deleted within 30 days, except where kept longer
  to enforce the usage policy (up to 2 years for flagged content) or as the law requires. This
  is not zero retention, and neither the panel nor the system prompt claims it is.
- **Bedrock (`Provider=bedrock`):** data retention is set to none in the Region and the proxy
  checks it every 15 minutes; it answers nothing otherwise.
- The panel shows the sentence for the provider the proxy reports in `/status`, and the system
  prompt says the same (`prompt.mjs` `DATA_HANDLING`; a test keeps the two in step).

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

Reading the key costs next to nothing: with OpenAI, one Secrets Manager `GetSecretValue` per
instance at cold start and every 15 minutes ($0.05 per 10,000 calls; under 3,000 a month per
instance that stays warm, so under $0.02), on a secret that already exists (no new $0.40 a
month). With the Claude API, an SSM standard parameter and its reads are free, and so is the
AWS managed key `aws/ssm`.

## Deploy (coordinator, after review)

Everything uses `--profile future-city`. The assistant's Region is `us-east-2`; use it for
every step. `deploy.sh` always passes `Provider` to the stack (from `--param`, else what the
stack already has, else `openai`), and runs only that provider's checks.

### The provider's prerequisites

**OpenAI (`Provider=openai`, the default).** Nothing to create: the key is the
`OPENAI_API_KEY` field of the earlier site assistant's secret, `future-city-assistant-secrets`
in `us-east-1` (`OpenAISecretName`, `OpenAISecretRegion`). The function reads it across
Regions by name at cold start and every 15 minutes, keeps only that field, in memory, and
never logs it; without it the assistant says it is not available. Its role may call
`secretsmanager:GetSecretValue` on that one secret only
(`arn:aws:secretsmanager:us-east-1:<account>:secret:future-city-assistant-secrets-??????`).
`deploy.sh` describes the secret (metadata, never the value) and stops if it is missing or
encrypted with a customer managed KMS key, which the role could not decrypt. Then:

- **Set a monthly budget on the OpenAI project that holds the key** (open action 12). The
  key is shared with the earlier assistant, so this one cap bounds both; the $5 ledger bounds
  this proxy alone.
- **Check the price** in `src/pricing.mjs` against OpenAI's current price list.
- The secret also holds the earlier assistant's GitHub token, and the role can read the whole
  secret (it keeps only the OpenAI key). To narrow that, put the OpenAI key in a secret of its
  own and deploy with `--param OpenAISecretName=<that name>`.

**Bedrock (`Provider=bedrock`).** Only once Bedrock offers Anthropic models on this account:

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
3. **Optional guard:** attach the managed policy `evsient-bedrock-retention-none-only` to the
   admin users or roles, so nobody can switch retention back on by mistake.

**Claude API (`Provider=anthropic`).** Not in use. The owner would put the key in SSM
Parameter Store in the stack's Region, typed at a prompt so it stays out of shell history:
`read -rs KEY`, then `aws ssm put-parameter --name /evsient/assistant/anthropic-api-key
--type SecureString --value "$KEY" --region us-east-2 --profile future-city`, then
`unset KEY`; set a $5 monthly spend limit on the Claude Console workspace and buy prepaid
credits only. `deploy.sh` checks the parameter exists as a SecureString (never its value).

### Every provider

1. **Cost allocation tag.** Activate `Project` as a cost allocation tag (Billing, Cost
   allocation tags) so the non-model budget can see it. It can take a day to appear.
2. **Stack and code:**
   ```
   cd platform/assistant
   deploy/deploy.sh --region us-east-2 --dryrun --param Provider=openai     # read what it will run
   deploy/deploy.sh --region us-east-2 --param Provider=openai
   ```
   On the first deploy, put `ALERT_EMAIL=<address>` in front, then confirm the SNS
   subscription email. The stack outputs `FunctionUrlDomain` and `OriginAccessControlId`.
3. **Smoke test before connecting CloudFront.** A direct call to the function URL must be
   refused (`403`, AuthType AWS_IAM). CloudFront's permission is limited to its own
   distribution, this account and calls through the function URL (`InvokedViaFunctionUrl`).
   Then one test call with the CLI, which also confirms the request fields are accepted
   (cost: about one cent):
   ```
   aws lambda invoke --function-name evsient-assistant --region us-east-2 --profile future-city \
     --cli-binary-format raw-in-base64-out --payload file://deploy/smoke-event.json out.txt
   ```
   `out.txt` should hold a `meta` line, `text` lines and a `done` line. An `error` line means
   the call failed; the function's log names the error (an OpenAI error code such as
   `invalid_api_key` or `insufficient_quota`, or a Bedrock exception). A validation error
   points at the extra request fields (`OpenAIExtraJson` or `ModelExtraJson`; try `{}`).
4. **Connect CloudFront** (review the diff before applying):
   ```
   aws cloudfront get-distribution-config --id E1JXKS26TDP3Z2 --profile future-city > live.json
   python3 deploy/edge_config.py live.json --domain <FunctionUrlDomain> --oac <OriginAccessControlId> > new.json
   diff <(python3 -m json.tool live.json) <(python3 -m json.tool new.json)
   aws cloudfront update-distribution --id E1JXKS26TDP3Z2 --if-match <ETag> \
     --distribution-config file://new.json --profile future-city
   ```
   Then copy the new behaviour and origin into `platform/infra/distribution-config.json` with
   `ACCOUNT_ID` in place of the account. Delete `live.json` and `new.json`.
5. **Check from a browser:** open the planner, open Assistant, ask one question. Check the
   status line shows Available, "What the Assistant Can and Cannot See" names the provider,
   and the ledger item `ledger#month#YYYY-MM` has `calls` 1.

If CloudFront returns the site's 404 page for `/api/assistant/status`, the request was refused
at the origin (OAC or the Lambda permissions): the distribution turns every 403 and 404 into
`/404.html`, and the proxy itself never returns either.

### Switching provider

`deploy/deploy.sh --region us-east-2 --param Provider=bedrock` (after the Bedrock
prerequisites), or `Provider=openai` to come back. Each provider's IAM statements exist only
while it is selected. The ledger is shared, so the month's spend carries over.

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
4. **While this proxy runs with `Provider=openai`, keep the secret and the key**: the planner's
   assistant reads the same `future-city-assistant-secrets`. Remove only `GITHUB_TOKEN` from
   it (and revoke that token), so the secret holds the OpenAI key alone. Delete the secret
   (about $0.40 a month) and revoke the OpenAI key only once this proxy has moved to another
   provider.
5. Remove `infra/assistant/`, `scripts/deploy_assistant.py` and `tests/test_assistant_paths.py`.
6. Open action 12 (the OpenAI spend cap) stays open while this proxy uses OpenAI; it closes
   when a budget is set on the OpenAI project, or when no OpenAI spend is left.
