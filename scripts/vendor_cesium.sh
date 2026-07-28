#!/bin/bash
# Fetch CesiumJS into explorer/web/vendor/ so the viewer runs with no network at all.
#
# Why fetched rather than committed
# ---------------------------------
# Build/Cesium is 20 MB across 375 files. Committing it would make every clone of a
# planning-study repository 20 MB heavier to carry a third-party redistributable that is
# pinned, reproducible, and already bundled at desktop-packaging time. The version here is
# pinned to the same release index.html loads, and a gate checks the two agree, so a
# fetched copy is as deterministic as a committed one without the weight.
#
# The viewer prefers this copy when it exists and falls back to the pinned CDN otherwise,
# so a clean checkout still works online with no build step.
#
# CesiumJS is Apache-2.0. See explorer/web/vendor/LICENSE-CesiumJS.txt after fetching, and
# docs/architecture/3d-explorer-constraints.md for the attribution obligations that come
# with Google Photorealistic 3D Tiles and OSM data.
set -euo pipefail

VERSION="${CESIUM_VERSION:-1.128.0}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$REPO/explorer/web/vendor"
# `|| true` is load-bearing under `set -euo pipefail`: if the grep finds no pin the whole
# pipeline fails and the script dies HERE, so the `[ -n "$PINNED" ]` guard below could
# never observe an empty value -- an unpinned index.html would abort with no explanation
# instead of reaching the message written for exactly that case.
PINNED=$(grep -o 'cesium@[0-9]\+\.[0-9]\+' "$REPO/explorer/web/index.html" | head -1 | cut -d@ -f2 || true)

if [ -n "$PINNED" ] && [[ "$VERSION" != "$PINNED"* ]]; then
  echo "REFUSING: index.html pins cesium@$PINNED but this script would fetch $VERSION." >&2
  echo "A vendored copy that differs from the pinned CDN reference is worse than no" >&2
  echo "vendored copy at all: the viewer would behave differently offline and online." >&2
  exit 1
fi

# Pinned tarball digests, taken from the npm registry's own `dist.integrity` field.
#
# A pinned VERSION says WHICH release to fetch; it says nothing about whether the bytes that
# arrived are that release. Without this, "reproducible on demand" was a claim about a URL
# rather than about content, and 20 MB of third-party JavaScript entered the viewer — and any
# desktop package built from it — unverified.
#
# Written as a `case` rather than an associative array on purpose: macOS ships **bash 3.2**,
# which has no `declare -A`. The first version of this used one, and bash did not refuse it —
# it parsed the dotted version key as an arithmetic expression and produced
# "syntax error: invalid arithmetic operator", leaving EXPECTED unset. A verification step
# that fails open is worse than none, because it reads as protection.
expected_sha512() {
  case "$1" in
    1.128.0) echo "2fd693147bd11b8c10dc975d84e1b8ad7fcc5bfeeaf18b973f22a50ae85cab321fcf74aecc035900e745c60aafb2efa80bab78de93414b25086a3ca073f558d0" ;;
    *)       echo "" ;;
  esac
}

echo "Fetching CesiumJS $VERSION ..."
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
curl -sSL -o "$TMP/cesium.tgz" "https://registry.npmjs.org/cesium/-/cesium-${VERSION}.tgz"

EXPECTED=$(expected_sha512 "$VERSION")
if [ -z "$EXPECTED" ]; then
  # Fail closed. An unpinned version is exactly when verification matters most, so skipping
  # the check for unknown versions would disable it precisely where it is needed.
  echo "REFUSING: no pinned SHA-512 for CesiumJS $VERSION." >&2
  echo "Add its digest to expected_sha512() before vendoring it." >&2
  exit 1
fi

ACTUAL=$(shasum -a 512 "$TMP/cesium.tgz" | cut -d' ' -f1)
if [ "$ACTUAL" != "$EXPECTED" ]; then
  echo "REFUSING: CesiumJS $VERSION tarball does not match its pinned digest." >&2
  echo "  expected $EXPECTED" >&2
  echo "  actual   $ACTUAL" >&2
  echo "Either the release was re-published, the pin is wrong, or the download was tampered" >&2
  echo "with. None of those should be resolved by proceeding." >&2
  exit 1
fi
echo "  digest verified (sha512)"

tar xzf "$TMP/cesium.tgz" -C "$TMP"

rm -rf "$DEST/Cesium"
mkdir -p "$DEST"
cp -R "$TMP/package/Build/Cesium" "$DEST/Cesium"
for f in LICENSE.md LICENSE; do
  [ -f "$TMP/package/$f" ] && cp "$TMP/package/$f" "$DEST/LICENSE-CesiumJS.txt" && break
done

cat > "$DEST/README.md" <<INNER
# Vendored third-party assets — not tracked

Fetched by \`scripts/vendor_cesium.sh\`, gitignored, reproducible on demand.

- **CesiumJS $VERSION** — Apache-2.0. Full licence in \`LICENSE-CesiumJS.txt\`.

The version is pinned to match the CDN reference in \`explorer/web/index.html\`; the fetch
script refuses to run if the two disagree. Re-fetch with \`make explorer-vendor\`.
INNER

echo "Vendored to $DEST/Cesium ($(du -sh "$DEST/Cesium" | cut -f1), $(find "$DEST/Cesium" -type f | wc -l | tr -d ' ') files)"
echo "The viewer will now prefer this copy over the CDN."
