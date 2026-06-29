# Future City Fellowship AI Assistant
## Phase 5 Deployment and Maintenance Runbook

**Current stable assistant version:** `phase_5m_direct_file_source_alignment`  
**Production site:** `https://futurecityfellowship.andyyaro.com/assistant.html`  
**Production API endpoint:** `POST https://zale82q9w3.execute-api.us-east-1.amazonaws.com/chat`  
**Source-of-truth repo branch:** `v2-expansion-planning`  
**Status:** Phase 5 hardened version is active and working.

---

## 1. What the assistant does

The Future City Fellowship AI Assistant is a protected, repo-aware chatbot for the Future City Fellowship public EV charging site-readiness and right-sizing model.

It can answer questions about:

- The EV charging site-readiness model
- The scoring methodology
- Datasets and data sources
- Tableau exports and workbook support files
- Model assumptions and limitations
- V2 workflow files and generated outputs
- Codebase structure and source-of-truth documentation

The assistant is not a public, unrestricted AI chatbot. It is designed as a controlled project assistant for approved users.

---

## 2. Current production architecture

The current production flow is:

```text
User opens assistant.html
        ↓
Cognito Hosted UI sign-in
        ↓
assistant.html stores short in-session conversation context
        ↓
Browser sends POST /chat with Cognito JWT
        ↓
API Gateway HTTP API validates JWT authorizer
        ↓
Lambda future-city-assistant-chat runs backend logic
        ↓
Lambda reads OpenAI/GitHub secrets from AWS Secrets Manager
        ↓
Lambda checks DynamoDB usage counters and rate limits
        ↓
Lambda inspects private GitHub repo files on v2-expansion-planning branch
        ↓
Lambda sends selected repo context to GPT model
        ↓
Lambda logs usage metadata to DynamoDB
        ↓
Frontend renders Markdown-formatted answer and Sources checked
```

---

## 3. Main AWS resources

### Frontend

```text
S3 / CloudFront hosted website
Live page: /assistant.html
CloudFront invalidation path after frontend edits: /assistant.html
```

### API Gateway

```text
API name: future-city-assistant-api
API ID: zale82q9w3
Stage: $default
Route: POST /chat
Endpoint: https://zale82q9w3.execute-api.us-east-1.amazonaws.com/chat
Auth: JWT authorizer attached to POST /chat
```

### Lambda

```text
Function name: future-city-assistant-chat
Runtime: Python 3.14
Timeout: 30 seconds
Current phase marker: phase_5m_direct_file_source_alignment
```

### Cognito

```text
User Pool ID: us-east-1_mKrwfQTkg
App Client ID: 27lfqn0m4i6e05nvcd5nqmqqe8
Hosted domain: https://us-east-1mkrwfqtkg.auth.us-east-1.amazoncognito.com/
Callback URL: https://futurecityfellowship.andyyaro.com/assistant.html
Sign-out URL: https://futurecityfellowship.andyyaro.com/assistant.html
```

### GitHub source of truth

```text
Owner: andyyaro
Repository: Future-City-Fellowship-
Branch: v2-expansion-planning
Token storage: AWS Secrets Manager
```

### DynamoDB usage table

```text
Table name: future-city-assistant-usage
Partition key: pk    String
Sort key: sk         String
Billing mode: On-demand
TTL attribute: expiresAt
```

### Secrets Manager

```text
Secret name: future-city-assistant-secrets
Required keys:
  OPENAI_API_KEY
  GITHUB_TOKEN
```

Do not paste or expose these secret values in chat, GitHub, screenshots, documentation, or frontend code.

---

## 4. Current Lambda environment variables

The Lambda should keep non-secret configuration in environment variables.

### Required config

```text
ALLOWED_ORIGIN=https://futurecityfellowship.andyyaro.com
MAX_MESSAGE_LENGTH=2000
MAX_OUTPUT_TOKENS=1200
OPENAI_MODEL=gpt-5.4-mini

GITHUB_OWNER=andyyaro
GITHUB_REPO=Future-City-Fellowship-
GITHUB_BRANCH=v2-expansion-planning

MAX_REPO_FILES=6
MAX_FILES_TO_SCAN=32
MAX_REPO_CONTEXT_CHARS=22000
MAX_REPO_FILE_CHARS=6500
MAX_GITHUB_FILE_BYTES=120000
REPO_TREE_CACHE_SECONDS=600
MAX_REFERENCED_FILES=4

USAGE_TABLE_NAME=future-city-assistant-usage
RATE_LIMIT_ENABLED=true
HOURLY_USER_LIMIT=10
DAILY_USER_LIMIT=100
USAGE_LOG_TTL_DAYS=30
LOG_MESSAGE_PREVIEW=false
RATE_LIMIT_FAIL_CLOSED=false

ASSISTANT_SECRET_ID=future-city-assistant-secrets
SECRETS_CACHE_SECONDS=300

MAX_HISTORY_TURNS=6
MAX_HISTORY_CHARS_PER_TURN=800
```

### Variables that should NOT remain in Lambda env vars

These should now live only in AWS Secrets Manager:

```text
OPENAI_API_KEY
GITHUB_TOKEN
```

If these appear again in Lambda environment variables, remove them after confirming Secrets Manager works.

---

## 5. Current security posture

The assistant is protected by several layers:

1. **Cognito sign-in gate** on the frontend.
2. **API Gateway JWT authorizer** on `POST /chat`.
3. **No OpenAI or GitHub secret in browser code.**
4. **OpenAI API key and GitHub token stored in Secrets Manager.**
5. **GitHub token is read-only and scoped to the selected repository.**
6. **DynamoDB usage logging and per-user rate limits are active.**
7. **Frontend renders Markdown safely instead of injecting raw HTML.**
8. **CloudWatch alarms monitor errors, throttles, latency, and API failures.**

---

## 6. Phase 5 improvements completed

| Phase | Improvement | Status |
|---|---|---|
| 5A | Markdown rendering | Complete |
| 5B | DynamoDB usage logging and rate limits | Complete |
| 5C | Better source selection | Complete |
| 5D | Secrets Manager migration | Complete |
| 5E | CloudWatch alarms and dashboard | Complete |
| 5F | Cleaner frontend error handling | Complete |
| 5G | Better broad overview source selection | Complete |
| 5H/5I/5J | Response guardrails and scoring finalizer | Complete |
| 5K | Conversation context for follow-ups | Complete |
| 5L/5M | Source-answer consistency and direct file source alignment | Complete |

---

## 7. Monitoring setup

### SNS topic

```text
Topic name: future-city-assistant-alerts
Purpose: sends email notifications when alarms enter ALARM state
```

### CloudWatch alarms

The main production alarms are:

```text
future-city-assistant-lambda-errors
future-city-assistant-lambda-duration-high
future-city-assistant-lambda-throttles
future-city-assistant-api-5xx-errors
future-city-assistant-api-latency-high
```

### Alarm meanings

```text
Lambda errors:
  Lambda had at least 1 error in 5 minutes.

Lambda duration high:
  Average Lambda duration reached 25 seconds or more.

Lambda throttles:
  Lambda had at least 1 throttled invocation in 5 minutes.

API 5xx errors:
  API Gateway had at least 1 server-side/backend error in 5 minutes.

API latency high:
  API Gateway average latency reached 25 seconds or more.
```

### CloudWatch dashboard

Dashboard name:

```text
future-city-assistant-dashboard
```

Recommended widgets:

```text
Lambda Invocations
Lambda Errors
Lambda Duration
Lambda Throttles
API Gateway Count
API Gateway 5xx
API Gateway Latency
```

---

## 8. Normal deployment procedures

### Frontend-only update

Use this when updating only `assistant.html`.

```text
1. Upload the new assistant.html to S3 as assistant.html.
2. Invalidate CloudFront path: /assistant.html
3. Open https://futurecityfellowship.andyyaro.com/assistant.html
4. Sign in.
5. Ask one normal test question.
6. Confirm answer renders correctly and sources appear.
```

### Backend-only update

Use this when updating only Lambda code.

```text
1. Go to Lambda → future-city-assistant-chat → Code.
2. Replace lambda_function.py with the new backend version.
3. Click Deploy.
4. Run an authenticated Lambda test event.
5. Confirm statusCode = 200 and ok = true.
6. Confirm phase marker is the expected new phase.
7. Test from the live website.
8. Confirm DynamoDB logs the request.
```

### Full frontend + backend update

Use this when both files change.

```text
1. Deploy Lambda code first.
2. Run Lambda test.
3. Upload assistant.html to S3.
4. Invalidate CloudFront /assistant.html.
5. Test live signed-in page.
6. Check DynamoDB logs.
7. Check CloudWatch logs if anything fails.
```

---

## 9. Standard regression test after changes

After any meaningful update, test these prompts from the live site:

```text
tell me more about this project
walk me through the scoring model
yeah do that
what datasets does the model use?
what are the project limitations?
what files support the Tableau exports?
```

Expected behavior:

```text
- Assistant answers normally.
- Markdown renders correctly.
- Follow-up “yeah do that” uses the previous context.
- Sources checked are relevant.
- File-specific answers include the direct files in Sources checked.
- DynamoDB logs each successful request.
- Rate-limit counters increase.
```

---

## 10. DynamoDB checks

Go to:

```text
DynamoDB → Tables → future-city-assistant-usage → Explore table items
```

Useful fields to verify:

```text
phase
status
userEmail
userSub
repoBranch
sourceCount
sourcesJson
input_tokens
output_tokens
total_tokens
latencyMs
messageLength
expiresAt
```

For the current stable version, recent successful rows should show:

```text
phase: phase_5m_direct_file_source_alignment
status: success
repoBranch: v2-expansion-planning
sourceCount: populated
userEmail: real Cognito user email
```

Hourly and daily counters should appear as separate counter records.

---

## 11. Rate limits

Current production setting:

```text
HOURLY_USER_LIMIT=10
DAILY_USER_LIMIT=100
```

This means each signed-in user can send:

```text
10 messages per hour
100 messages per day
```

To temporarily test rate-limit behavior:

```text
1. Set HOURLY_USER_LIMIT=1.
2. Ask another question from the website.
3. Confirm the frontend shows a clean rate-limit message.
4. Immediately restore HOURLY_USER_LIMIT=10.
```

Do not forget to restore the value.

---

## 12. Troubleshooting guide

### Problem: Website shows an auth/session error

Check:

```text
- Is the user signed in through Cognito?
- Did the token expire?
- Is API Gateway JWT authorizer still attached to POST /chat?
- Does frontend assistant.html still include the correct Cognito values?
```

### Problem: API returns 401 Unauthorized

Likely causes:

```text
- Missing Authorization header
- Expired Cognito token
- Wrong Cognito App Client ID / audience
- JWT authorizer detached from route
```

### Problem: API returns 403 Forbidden

Likely causes:

```text
- Token is valid but not accepted by authorizer configuration
- Cognito issuer or audience mismatch
```

### Problem: API returns 429 rate limit

Likely cause:

```text
User hit HOURLY_USER_LIMIT or DAILY_USER_LIMIT.
```

Check DynamoDB counters and adjust limits only if needed.

### Problem: API returns 500

Check:

```text
CloudWatch Logs → Lambda → future-city-assistant-chat
```

Likely causes:

```text
- Secrets Manager permission issue
- Missing secret key
- OpenAI API issue
- GitHub API issue
- DynamoDB permission issue
- Unexpected backend code error
```

### Problem: Assistant cannot access GitHub repo

Check:

```text
- GITHUB_OWNER=andyyaro
- GITHUB_REPO=Future-City-Fellowship-
- GITHUB_BRANCH=v2-expansion-planning
- Secret future-city-assistant-secrets contains GITHUB_TOKEN
- GitHub token has read-only Contents permission
- Token has not expired
```

### Problem: Assistant cannot call OpenAI

Check:

```text
- Secret future-city-assistant-secrets contains OPENAI_API_KEY
- OpenAI project has billing/credits available
- OPENAI_MODEL is set correctly
- Lambda can read Secrets Manager
```

### Problem: Sources checked are irrelevant

Check whether the question type needs better source routing.

Known source priorities:

```text
Broad project overview:
  README.md
  docs/README.md
  docs/METHODOLOGY.md
  docs/DATA_SOURCES.md
  docs/DATA_DICTIONARY.md

Scoring questions:
  docs/METHODOLOGY.md
  docs/DATA_DICTIONARY.md
  docs/V2_CURRENT_WORKFLOW_GUIDE.md
  src/ev_charger_model.py, if available

Dataset questions:
  docs/DATA_SOURCES.md
  docs/DATA_DICTIONARY.md
  data/dataset_metadata.csv
  data/source_dataset_log.csv

Tableau/export questions:
  src/build_tableau_exports.py
  src/check_tableau_exports.py
  docs/V2_CURRENT_WORKFLOW_GUIDE.md
  docs/DATA_DICTIONARY.md
  tableau/README.md
```

---

## 13. Token and secret rotation

### GitHub token

The GitHub fine-grained token was configured as a read-only repository token. It should be rotated before expiration.

When rotating:

```text
1. Create a new fine-grained GitHub token.
2. Scope it only to andyyaro/Future-City-Fellowship-.
3. Give repository Contents read-only permission.
4. Update GITHUB_TOKEN inside future-city-assistant-secrets.
5. Test the assistant.
6. Revoke the old token.
```

### OpenAI key

When rotating:

```text
1. Create a new OpenAI project API key.
2. Update OPENAI_API_KEY inside future-city-assistant-secrets.
3. Test Lambda directly.
4. Test the live site.
5. Delete/revoke the old OpenAI key.
```

---

## 14. Rollback plan

If a backend update breaks the assistant:

```text
1. Open Lambda → future-city-assistant-chat → Versions or Code history if available.
2. Restore the previous known-good lambda_function.py.
3. Deploy.
4. Run the Lambda test event.
5. Test the website.
6. Check DynamoDB and CloudWatch.
```

Known stable phase to roll back to:

```text
phase_5m_direct_file_source_alignment
```

If a frontend update breaks the assistant:

```text
1. Re-upload the previous known-good assistant.html.
2. Invalidate CloudFront path /assistant.html.
3. Refresh browser with cache cleared.
4. Test sign-in and one assistant question.
```

---

## 15. Planning-support disclaimer

The assistant and the model are planning-support artifacts only.

They do not replace:

```text
Engineering review
Utility coordination
Permitting approval
Fire Marshal / AHJ review
ADA/accessibility review
Stormwater review
Procurement review
Construction approval
Stakeholder approval
```

The assistant should describe model outputs as screening, prioritization, and discussion support, not official determinations.

---

## 16. Current recommended next steps

Now that Phase 5 is locked, the recommended next work items are:

```text
1. Visual polish pass for assistant.html.
2. Add this runbook to the project documentation folder.
3. Optional: add a lightweight admin usage summary view later.
4. Optional: add automated deployment instead of manual Lambda/S3 updates.
5. Optional: Phase 6 feature work, such as richer project Q&A or downloadable assistant summaries.
```

---

## 17. Quick checklist

Before presenting or demoing the assistant:

```text
[ ] Assistant page loads at /assistant.html
[ ] Approved user can sign in
[ ] Prompt returns a clean Markdown-formatted answer
[ ] Sources checked appear
[ ] DynamoDB logs the request
[ ] CloudWatch alarms are OK
[ ] Secrets are not in frontend code
[ ] OPENAI_API_KEY is not in Lambda environment variables
[ ] GITHUB_TOKEN is not in Lambda environment variables
[ ] GITHUB_BRANCH is v2-expansion-planning
[ ] HOURLY_USER_LIMIT is set to the intended value
```
