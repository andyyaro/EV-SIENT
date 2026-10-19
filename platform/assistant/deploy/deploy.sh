#!/usr/bin/env bash
# Deploy the assistant proxy: checks, then the CloudFormation stack, then the function code.
# Always the future-city profile; never the default. Nothing at the CloudFront edge changes here
# (that is edge_config.py plus one reviewed update-distribution; see ../README.md).
#
#   ALERT_EMAIL=you@example.org deploy/deploy.sh --region us-east-2            first deploy
#   deploy/deploy.sh --region us-east-2                                         later deploys
#   deploy/deploy.sh --region us-east-2 --param MonthlyCapUsd=3                 change a parameter
#   deploy/deploy.sh --region us-east-2 --dryrun                                print, call nothing
#
# Run from platform/assistant. The email is read from the environment so it is never written
# into the repository or a shell script.
set -euo pipefail

PROFILE=future-city
STACK=evsient-assistant
REGION=""
DRYRUN=0
PARAMS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --region) REGION="$2"; shift 2 ;;
    --param) PARAMS+=("$2"); shift 2 ;;
    --dryrun) DRYRUN=1; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -n "$REGION" ] || { echo "give --region (the assistant's Region, for example us-east-2)" >&2; exit 2; }
[ -f template.yaml ] || { echo "run from platform/assistant" >&2; exit 2; }
unset AWS_PROFILE AWS_DEFAULT_PROFILE

run() {
  printf '+'; printf ' %q' "$@"; printf '\n'
  if [ "$DRYRUN" = 0 ]; then "$@"; fi
}

echo "== 1. Tests"
node --test "test/*.test.mjs" > /dev/null || { echo "tests failed; nothing deployed" >&2; exit 1; }

echo "== 2. Bedrock data retention in $REGION must be none, and invocation logging off"
if [ "$DRYRUN" = 0 ]; then
  MODE=$(aws bedrock get-account-data-retention --region "$REGION" --profile "$PROFILE" --query mode --output text 2>/dev/null || echo unknown)
  if [ "$MODE" != "none" ]; then
    echo "data retention in $REGION is '$MODE'. Set it first:" >&2
    echo "  aws bedrock put-account-data-retention --mode none --region $REGION --profile $PROFILE" >&2
    exit 1
  fi
  LOGGING=$(aws bedrock get-model-invocation-logging-configuration --region "$REGION" --profile "$PROFILE" --query loggingConfig --output text 2>/dev/null || echo unknown)
  if [ "$LOGGING" != "None" ] && [ -n "$LOGGING" ]; then
    echo "model invocation logging is on in $REGION; the assistant must not log prompts. Stopping." >&2
    exit 1
  fi
else
  echo "(dry run: would read get-account-data-retention and get-model-invocation-logging-configuration)"
fi

echo "== 3. Stack $STACK in $REGION"
OVERRIDES=("${PARAMS[@]+"${PARAMS[@]}"}")
if [ -n "${ALERT_EMAIL:-}" ]; then OVERRIDES+=("AlertEmail=$ALERT_EMAIL"); fi
DEPLOY=(aws cloudformation deploy --template-file template.yaml --stack-name "$STACK"
  --capabilities CAPABILITY_NAMED_IAM --tags Project=evsient-platform
  --region "$REGION" --profile "$PROFILE" --no-fail-on-empty-changeset)
if [ ${#OVERRIDES[@]} -gt 0 ]; then DEPLOY+=(--parameter-overrides "${OVERRIDES[@]}"); fi
if [ "$DRYRUN" = 0 ]; then
  "${DEPLOY[@]}"
else
  printf '+'; printf ' %q' "${DEPLOY[@]}" | sed -E 's/AlertEmail=[^ ]+/AlertEmail=<from ALERT_EMAIL>/'; printf '\n'
fi

echo "== 4. Function code"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
cp src/*.mjs "$WORK/"
(cd "$WORK" && zip -q -X assistant.zip ./*.mjs)
run aws lambda update-function-code --function-name evsient-assistant --zip-file "fileb://$WORK/assistant.zip" \
  --region "$REGION" --profile "$PROFILE" --query LastUpdateStatus --output text
run aws lambda wait function-updated --function-name evsient-assistant --region "$REGION" --profile "$PROFILE"

echo "== 5. Outputs (for edge_config.py)"
run aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --profile "$PROFILE" \
  --query "Stacks[0].Outputs[?OutputKey=='FunctionUrlDomain' || OutputKey=='OriginAccessControlId'].[OutputKey,OutputValue]" --output text
echo "Next: README.md, 'Connect CloudFront' (edge_config.py, then update-distribution)."
