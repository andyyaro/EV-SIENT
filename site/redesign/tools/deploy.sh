#!/bin/bash
# Publish the redesign to s3://future-city-redesign and invalidate E3RNYDDSMJAZUR. Touches nothing else.
# The launch film (film.html and film/) is published on its own, so both syncs leave it alone.
set -euo pipefail
R="$1"; P=(--profile future-city --region us-east-1); B=s3://future-city-redesign
EX=(--exclude "*.md" --exclude "_template.html" --exclude ".*" --exclude "*/.DS_Store")
aws s3 sync "$R" "$B" --delete "${EX[@]}" --exclude "*" --include "*.html" --exclude "_template.html" --exclude "film.html" --exclude "film/*" --cache-control "no-cache" --content-type "text/html; charset=utf-8" "${P[@]}"
aws s3 sync "$R" "$B" --delete "${EX[@]}" --exclude "*.html" --exclude "film/*" --cache-control "public, max-age=300" "${P[@]}"
aws cloudfront create-invalidation --distribution-id E3RNYDDSMJAZUR --paths "/*" "${P[@]}" --query Invalidation.Id --output text
