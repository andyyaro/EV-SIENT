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
PINNED=$(grep -o 'cesium@[0-9]\+\.[0-9]\+' "$REPO/explorer/web/index.html" | head -1 | cut -d@ -f2)

if [ -n "$PINNED" ] && [[ "$VERSION" != "$PINNED"* ]]; then
  echo "REFUSING: index.html pins cesium@$PINNED but this script would fetch $VERSION." >&2
  echo "A vendored copy that differs from the pinned CDN reference is worse than no" >&2
  echo "vendored copy at all: the viewer would behave differently offline and online." >&2
  exit 1
fi

echo "Fetching CesiumJS $VERSION ..."
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
curl -sSL -o "$TMP/cesium.tgz" "https://registry.npmjs.org/cesium/-/cesium-${VERSION}.tgz"
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
