#!/bin/bash
# Publish the EV-SIENT Planner build to s3://future-city-app and refresh CloudFront E1JXKS26TDP3Z2.
# Touches nothing else. See platform/infra/README.md ("Deploy") for the reasoning.
#
#   platform/tools/deploy.sh <dist-dir> [--sourcemaps] [--dryrun]
#
#   --sourcemaps  also upload *.map files (excluded by default)
#   --dryrun      print the upload plan and change nothing
#
# Rules:
#   *.html, sw.js, registerSW.js, *.webmanifest, runtime/engine/engine.json   no-cache
#   assets/** (Vite, content-hashed) and runtime/** (versioned)               public, max-age=31536000, immutable
#   everything else                                                           public, max-age=300
#   Files under assets/ or runtime/ of 1 MB or more with a text or wasm type are pre-compressed
#   with Brotli (quality 11) and uploaded with Content-Encoding: br; CloudFront passes them through.
#   Immutable files already in the bucket with the same size are skipped.
#   Old files under assets/ and runtime/ are kept (open tabs and rollback); other stale keys are deleted.
#   hub/ is never touched: the public data hub is published on its own (platform/hub/README.md).
#   Only /, /index.html and /404.html are invalidated.
#
# Works with macOS /bin/bash 3.2. Needs: aws (CLI v2, profile future-city), brotli.
set -euo pipefail

BUCKET=future-city-app
DIST_ID=E1JXKS26TDP3Z2
PROFILE=future-city
REGION=us-east-1
BR_MIN_BYTES=1000000
IMMUTABLE="public, max-age=31536000, immutable"
SHORT="public, max-age=300"
NOCACHE="no-cache"

usage() { echo "usage: $0 <dist-dir> [--sourcemaps] [--dryrun]" >&2; exit 2; }
[ $# -ge 1 ] || usage
SRC="${1%/}"; shift
SOURCEMAPS=0; DRYRUN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --sourcemaps) SOURCEMAPS=1 ;;
    --dryrun) DRYRUN=1 ;;
    *) usage ;;
  esac
  shift
done
[ -f "$SRC/index.html" ] || { echo "error: $SRC/index.html not found" >&2; exit 1; }
[ -f "$SRC/404.html" ] || echo "warning: $SRC/404.html not found; CloudFront error pages will fail" >&2

P=(--profile "$PROFILE" --region "$REGION")
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
cp -Rp "$SRC/." "$STAGE/files"
PLAN="$STAGE/plan.tsv"; : > "$PLAN"

content_type() {
  case "$(echo "${1##*.}" | tr '[:upper:]' '[:lower:]')" in
    html|htm) echo "text/html; charset=utf-8" ;;
    js|mjs) echo "text/javascript" ;;
    css) echo "text/css" ;;
    json|map) echo "application/json" ;;
    webmanifest) echo "application/manifest+json" ;;
    wasm) echo "application/wasm" ;;
    whl|zip) echo "application/zip" ;;
    svg) echo "image/svg+xml" ;;
    png) echo "image/png" ;;
    jpg|jpeg) echo "image/jpeg" ;;
    webp) echo "image/webp" ;;
    ico) echo "image/x-icon" ;;
    woff2) echo "font/woff2" ;;
    woff) echo "font/woff" ;;
    ttf) echo "font/ttf" ;;
    otf) echo "font/otf" ;;
    csv) echo "text/csv; charset=utf-8" ;;
    txt) echo "text/plain; charset=utf-8" ;;
    xml) echo "application/xml" ;;
    pdf) echo "application/pdf" ;;
    xlsx) echo "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ;;
    parquet) echo "application/vnd.apache.parquet" ;;
    *) echo "" ;;
  esac
}

brotli_candidate() {
  case "$(echo "${1##*.}" | tr '[:upper:]' '[:lower:]')" in
    wasm|mjs|js|json|css|svg|html|txt|csv|xml) return 0 ;;
    *) return 1 ;;
  esac
}

# Build the plan: order, cache-control, content-type, content-encoding, key.
cd "$STAGE/files"
while IFS= read -r -d '' f; do
  rel="${f#./}"
  base="${rel##*/}"
  case "$base" in .*) rm -f "$rel"; continue ;; esac
  case "$rel" in *.map) if [ "$SOURCEMAPS" = 0 ]; then rm -f "$rel"; continue; fi ;; esac

  ctype="$(content_type "$rel")"
  if [ -z "$ctype" ]; then
    ctype="application/octet-stream"
    echo "warning: no content type for $rel; using $ctype (add it to content_type in $0)" >&2
  fi

  case "$rel" in
    runtime/engine/engine.json|*.html|sw.js|registerSW.js|*.webmanifest) cache="$NOCACHE"; order=3 ;;
    assets/*|runtime/*) cache="$IMMUTABLE"; order=1 ;;
    *) cache="$SHORT"; order=2 ;;
  esac
  [ "$base" = "index.html" ] && order=4

  enc="-"
  size=$(wc -c < "$rel" | tr -d ' ')
  case "$rel" in
    assets/*|runtime/*)
      if [ "$size" -ge "$BR_MIN_BYTES" ] && brotli_candidate "$rel"; then
        command -v brotli >/dev/null || { echo "error: brotli is required for $rel (brew install brotli)" >&2; exit 1; }
        brotli -q 11 -c "$rel" > "$rel.br.tmp"
        touch -r "$rel" "$rel.br.tmp"
        mv "$rel.br.tmp" "$rel"
        echo "brotli: $rel $size -> $(wc -c < "$rel" | tr -d ' ') bytes"
        enc="br"
      fi
      ;;
  esac
  printf '%s\t%s\t%s\t%s\t%s\n' "$order" "$cache" "$ctype" "$enc" "$rel" >> "$PLAN"
done < <(find . -type f -print0)

# Existing objects, to skip unchanged immutable files and to prune stale ones.
REMOTE="$STAGE/remote.tsv"
aws s3api list-objects-v2 --bucket "$BUCKET" --query 'Contents[].[Key,Size]' --output text "${P[@]}" | grep -v '^None$' > "$REMOTE" || true

sort -t $'\t' -k1,1n -k2,4 "$PLAN" > "$PLAN.sorted"
cut -f1-4 "$PLAN.sorted" | uniq > "$STAGE/groups.tsv"

uploaded=0; skipped=0
while IFS=$'\t' read -r order cache ctype enc; do
  includes=()
  while IFS=$'\t' read -r o c t e rel; do
    if [ "$o" = "$order" ] && [ "$c" = "$cache" ] && [ "$t" = "$ctype" ] && [ "$e" = "$enc" ]; then
      size=$(wc -c < "$rel" | tr -d ' ')
      if [ "$cache" = "$IMMUTABLE" ] && grep -qxF "$rel"$'\t'"$size" "$REMOTE"; then
        skipped=$((skipped + 1)); continue
      fi
      includes+=(--include "$rel")
      echo "upload: $rel  [$ctype | $cache | encoding $enc]"
    fi
  done < "$PLAN.sorted"
  [ ${#includes[@]} -gt 0 ] || continue
  uploaded=$((uploaded + ${#includes[@]} / 2))
  [ "$DRYRUN" = 1 ] && continue
  extra=()
  [ "$enc" = "br" ] && extra=(--content-encoding br)
  aws s3 cp . "s3://$BUCKET/" --recursive --only-show-errors --exclude "*" "${includes[@]}" \
    --cache-control "$cache" --content-type "$ctype" "${extra[@]+"${extra[@]}"}" "${P[@]}"
done < "$STAGE/groups.tsv"
echo "uploaded $uploaded, skipped $skipped unchanged immutable"

# Prune stale keys outside assets/, runtime/ and hub/ (the hub is not part of the app build).
cut -f5 "$PLAN" | sort > "$STAGE/local.txt"
cut -f1 "$REMOTE" | sort > "$STAGE/remote-keys.txt"
comm -13 "$STAGE/local.txt" "$STAGE/remote-keys.txt" | grep -vE '^(assets|runtime|hub)/' > "$STAGE/stale.txt" || true
while IFS= read -r key; do
  [ -n "$key" ] || continue
  echo "delete: $key"
  [ "$DRYRUN" = 1 ] || aws s3 rm "s3://$BUCKET/$key" --only-show-errors "${P[@]}"
done < "$STAGE/stale.txt"

if [ "$DRYRUN" = 1 ]; then echo "dry run: nothing changed"; exit 0; fi
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/" "/index.html" "/404.html" \
  --query Invalidation.Id --output text "${P[@]}"
