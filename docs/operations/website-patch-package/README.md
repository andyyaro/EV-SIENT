# Website + AI Assistant Offline Update Package

**Nothing in this package has been deployed. No AWS resource, DNS entry, or live page was
touched in this run.** The website (`futurecityfellowship.andyyaro.com`: landing, dashboard,
results, methodology, and authenticated AI Assistant pages on S3/CloudFront + Cognito +
API Gateway/Lambda/DynamoDB) is maintained outside the repository, so this package provides
**precise patch content and a file-by-file implementation guide** (per Task 10's
source-absent path) rather than modified source files.

## Contents

| File | Purpose |
|---|---|
| `PATCH_GUIDE.md` | File-by-file/page-by-page instructions for the site maintainer |
| `content/privacy_notice.md` | New privacy page (VCDPA-aware; mirrors `docs/human-actions/public_engagement/05_PRIVACY_NOTICE.md`) |
| `content/authority_disclaimer.md` | No-engineering-authority / no-permit-decision block (every page footer + assistant) |
| `content/methodology_update.md` | V3 methodology section (modes, anchors, contract, uncalibrated-demand status) |
| `content/results_2036_2046_2056.md` | Three-horizon results content (contract-derived numbers only) |
| `content/standards_summary.md` | UL 2594 + UL 3600 + supporting standards + proposed-standard concept summary |
| `content/limitations_update.md` | Updated limitations (aligned with the repository's model-limitations discipline — root `README.md` "Known limitations") |
| `content/source_vintage_footer.html` | Footer snippet: contract version + generated date + eGRID vintage |
| `content/assistant_boundaries.md` | Assistant scope/limitation text + governance rules |
| `DEPLOYMENT_RUNBOOK.md` | Exact deploy + verification + rollback steps (S3/CloudFront) |

## Governance rules embedded in this package (PY-16)

1. Assistant remains **explanation-only**; formal public comments go through accountable
   municipal channels (stated on the assistant page and in answers).
2. No unnecessary personal data collected; no PII required to read any page.
3. Privacy notice and authority disclaimers appear site-wide.
4. Every results figure carries the source vintage (contract v1.0.0, generated 2026-07-19;
   eGRID2023 Rev 2 SRVC factor).
5. No secrets, credentials, or internal infrastructure identifiers appear in this package
   or may be added to assistant-readable content.
6. Authentication boundary (Cognito) for the assistant is preserved — nothing here makes
   the assistant public.
7. Accessibility: patch guide requires alt text on all new figures, heading hierarchy,
   and contrast ≥ WCAG AA for the new content blocks.
