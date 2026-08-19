# Deployment Runbook (maintainer-executed; NOT run in this implementation)

## Preconditions
- AWS CLI configured with the site maintainer's credentials (never stored in this repo).
- S3 origin bucket name + CloudFront distribution ID at hand (kept outside this package
  by design - see PY-18/PY-16 no-secrets rule).

## Deploy
1. Stage the patched bundle locally; run the acceptance checklist in PATCH_GUIDE.md.
2. Snapshot current site: `aws s3 sync s3://<bucket> ./site_backup_$(date +%Y%m%d)/`
3. Upload: `aws s3 sync ./site_patched/ s3://<bucket> --delete --dryrun` → review → re-run
   without `--dryrun`.
4. Invalidate cache: `aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"`
5. Verify live: privacy page loads; results numbers spot-checked against contract;
   assistant still behind Cognito; no mixed-content warnings.

## Rollback
1. `aws s3 sync ./site_backup_<date>/ s3://<bucket> --delete`
2. Re-invalidate CloudFront.
3. Record the rollback and reason in the decision log.

## Assistant config rollback
Keep the prior system prompt/config exported before editing; restoring it is a single
config write + cache flush per the assistant's admin procedure.
