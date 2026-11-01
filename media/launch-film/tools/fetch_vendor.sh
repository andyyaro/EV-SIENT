#!/bin/bash
# Fetch the film's pinned JavaScript libraries from npm into the folders the pages load them from.
# These are the exact files the 2026-10-23 render used (byte-identical to these releases).
#   GSAP 3.14.2 (GSAP standard licence)         -> assets/vendor/gsap.min.js
#   three.js 0.186.0 (MIT)                      -> device/vendor/
#   MapLibre GL JS 6.12.0 (BSD-3-Clause)        -> map/vendor/
set -euo pipefail
cd "$(dirname "$0")/.."
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
(cd "$T" && npm pack gsap@3.14.2 three@0.186.0 maplibre-gl@6.12.0 --silent >/dev/null)
for t in "$T"/*.tgz; do d="$T/$(basename "$t" .tgz)"; mkdir -p "$d"; tar -xzf "$t" -C "$d"; done
G="$T/gsap-3.14.2/package"; H="$T/three-0.186.0/package"; M="$T/maplibre-gl-6.12.0/package"
mkdir -p assets/vendor device/vendor/jsm map/vendor
cp "$G/dist/gsap.min.js" assets/vendor/
cp "$H/build/three.module.js" "$H/build/three.core.js" device/vendor/
cp "$H/LICENSE" device/vendor/THREE-LICENSE
cp "$H/examples/jsm/geometries/RoundedBoxGeometry.js" "$H/examples/jsm/environments/RoomEnvironment.js" device/vendor/jsm/
cp "$M/dist/maplibre-gl.mjs" "$M/dist/maplibre-gl-shared.mjs" "$M/dist/maplibre-gl-worker.mjs" "$M/dist/maplibre-gl.css" map/vendor/
cp "$M/LICENSE.txt" map/vendor/MAPLIBRE-LICENSE.txt
echo "vendored: gsap 3.14.2, three 0.186.0, maplibre-gl 6.12.0"
