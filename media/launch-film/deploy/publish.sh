#!/bin/bash
# Publish the film's watch page to futurecity.andyyaro.com/film.html, next to the redesigned site.
# Copies five files and invalidates their two paths. It never syncs or deletes anything, and
# site/redesign/tools/deploy.sh excludes film.html and film/ so the site's own deploy leaves them alone.
#
#   deploy/publish.sh            # dry run: prints what it would copy
#   deploy/publish.sh --apply    # copies and invalidates (needs: aws sso login --profile future-city)
#
# Expects deploy/film/ to hold ev-sient-launch.mp4 (tools/finish.sh), poster.jpg (tools/finish.sh),
# logo.svg (assets/brand/evsient-logo-reversed.svg) and ev-sient-launch.vtt (tools/captions.py).
set -euo pipefail
cd "$(dirname "$0")"
B=s3://future-city-redesign; DIST=E3RNYDDSMJAZUR
DRY=(--dryrun); [ "${1:-}" = "--apply" ] && DRY=()
P=(--profile future-city --region us-east-1)
day="public, max-age=86400"
aws s3 cp film.html "$B/film.html" --content-type "text/html; charset=utf-8" --cache-control "no-cache" "${DRY[@]}" "${P[@]}"
aws s3 cp film/ev-sient-launch.mp4 "$B/film/ev-sient-launch.mp4" --content-type video/mp4 --cache-control "$day" "${DRY[@]}" "${P[@]}"
aws s3 cp film/poster.jpg "$B/film/poster.jpg" --content-type image/jpeg --cache-control "$day" "${DRY[@]}" "${P[@]}"
aws s3 cp film/logo.svg "$B/film/logo.svg" --content-type image/svg+xml --cache-control "$day" "${DRY[@]}" "${P[@]}"
aws s3 cp film/ev-sient-launch.vtt "$B/film/ev-sient-launch.vtt" --content-type "text/vtt; charset=utf-8" --cache-control "public, max-age=300" "${DRY[@]}" "${P[@]}"
if [ ${#DRY[@]} -eq 0 ]; then
  aws cloudfront create-invalidation --distribution-id "$DIST" --paths "/film.html" "/film/*" "${P[@]}" --query Invalidation.Id --output text
else
  echo "dry run: pass --apply to publish and invalidate /film.html and /film/*"
fi
