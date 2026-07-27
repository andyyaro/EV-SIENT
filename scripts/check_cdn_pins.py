"""Every external CDN reference in the viewer must name an explicit version.

An unpinned CDN reference means the page silently renders against whatever the CDN
serves today. The explorer shipped with `unpkg.com/cesium/...` directly beneath a
comment instructing the reader to pin it.

Like the secret scan and the link checker, this reads *meaning, not text*: it inspects
the href/src attributes actually loaded by the browser, so a comment that quotes an
unpinned URL while explaining why it was pinned does not trip the gate.

Google Photorealistic 3D Tiles require CesiumJS >= 1.124, so the pin is floor-checked
too -- a pin below that would silently disable the Photoreal basemap.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HTML = sorted((REPO / "explorer/web").glob("*.html"))

ATTR = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""", re.I)
CDN_HOSTS = ("unpkg.com", "cdn.jsdelivr.net", "cdnjs.cloudflare.com", "cesium.com")
PINNED = re.compile(r"@\d+\.\d+|/releases/\d+\.\d+|/\d+\.\d+\.\d+/")
CESIUM_VERSION = re.compile(r"cesium@(\d+)\.(\d+)")
CESIUM_MIN = (1, 124)  # Google Photorealistic 3D Tiles


def main() -> int:
    problems: list[str] = []
    checked = 0
    for path in HTML:
        text = path.read_text(encoding="utf-8")
        for url in ATTR.findall(text):
            if not url.lower().startswith(("http://", "https://")):
                continue
            if not any(host in url for host in CDN_HOSTS):
                continue
            checked += 1
            rel = path.relative_to(REPO)
            if not PINNED.search(url):
                problems.append(f"{rel}: unpinned CDN reference -> {url}")
                continue
            m = CESIUM_VERSION.search(url)
            if m and (int(m.group(1)), int(m.group(2))) < CESIUM_MIN:
                problems.append(
                    f"{rel}: CesiumJS pinned to {m.group(1)}.{m.group(2)}, below the "
                    f"{CESIUM_MIN[0]}.{CESIUM_MIN[1]} required by Google Photorealistic 3D Tiles -> {url}")

    if problems:
        print("CDN PIN PROBLEMS:")
        print("\n".join(f"  {p}" for p in problems))
        return 1
    print(f"CDN references OK ({checked} checked across {len(HTML)} page(s), all version-pinned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
