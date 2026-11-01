# infra/assistant - the public AI assistant's Lambda

`lambda_function.py` is the source of the Lambda `future-city-assistant-chat`, which answers
`POST /chat` on API Gateway `future-city-assistant-api` for both sites' Assistant pages:
`site/www/assistant.html` and the study site's `site/redesign/www/assistant.html`. The planner's
Assistant at app.futurecity.andyyaro.com is a separate service (`platform/assistant/`).

Until 2026-10-17 this code existed only inside AWS. It is tracked here so that every change to
it is reviewable and every deployed state can be rolled back.

## What it may read

The assistant needs no sign-in and reads this **private** repository with a token, so its path
rule is the boundary between the two:

- **Allowlist, not blocklist.** Only `PUBLIC_PATH_PREFIXES` and `PUBLIC_EXACT_PATHS` are
  readable. A new directory is unreadable until someone decides it is public.
- **Never readable:**
  - `tests/` (its fixtures copy the real facility rows)
  - `data/inputs/`, `data/provenance/`, `site/platform/`
  - `infra/`
  - `docs/operations/` (except the reproduction guide), `docs/human-actions/`
- **Every excerpt is scrubbed** of email addresses and UUIDs before it reaches the model.

`tests/test_assistant_paths.py` runs the function's own rule over the tracked tree. It fails if
a private file becomes readable, if a readable file carries an email address, or if the
allowlist starves the assistant of its own source-of-truth files.

## Deploy

```bash
python scripts/deploy_assistant.py            # dry run: compares repository and deployed code
python scripts/deploy_assistant.py --apply    # upload, publish a version, move the `live` alias
python scripts/deploy_assistant.py --rollback <version> --apply
```

API Gateway invokes the `live` alias, never `$LATEST`. Configuration lives in the function's
environment variables and secrets in Secrets Manager (`ASSISTANT_SECRET_ID`), never in this
file.
