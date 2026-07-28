#!/usr/bin/env python3
"""Every link the platform offers must resolve to a file that exists in the bundle.

The defect this exists to prevent
---------------------------------
Five of the platform's six surfaces linked to a **directory** — `dashboard/`, `contract/v1/`,
`contract/v2/`, `nfc/`, `reports/`. There is no such thing as a directory in S3, so every one
of those links was a 404 for anyone using the deployed site.

It survived because **the local server was more capable than production**. Python's
``http.server`` generates a directory listing on the fly, so the desktop tier rendered a
perfectly good page for a path that does not exist as an object at all. Every local check
passed. Only the web tier was broken, and only for a reader who clicked.

That is the same shape as the two blank Tableau sheets and the missing Cognito sign-in page:
the thing under our control behaved, and the thing the reader touches did not. So this check
resolves links **the way S3 resolves them** — a trailing slash means `index.html`, and nothing
is generated on demand.

Run: python scripts/check_surface_links.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "site/platform"
MANIFEST = BUNDLE / "surfaces.json"


def collect_links(manifest: dict) -> list[tuple[str, str]]:
    """(surface id, href) for every link the page will render."""
    out: list[tuple[str, str]] = []
    for surface in manifest["surfaces"]:
        if surface.get("href"):
            out.append((surface["id"], surface["href"]))
        for link in surface.get("links", []):
            out.append((surface["id"], link["href"]))
    return out


def resolve_like_s3(href: str) -> Path:
    """Map an href to the object S3 would be asked for.

    A trailing slash is the whole point: CloudFront's default root object only applies at `/`,
    so `contract/v1/` reaches the origin as the key `contract/v1/` — which does not exist. The
    edge function rewrites it to `contract/v1/index.html`, and that file has to be real.
    """
    path = href.split("?")[0].split("#")[0]
    if path.endswith("/"):
        path += "index.html"
    return BUNDLE / path


def main() -> int:
    if not MANIFEST.is_file():
        print(f"{MANIFEST} is missing — run scripts/build_platform_surfaces.py first")
        return 1

    manifest = json.loads(MANIFEST.read_text())
    broken: list[str] = []
    checked = 0
    external = 0

    for surface_id, href in collect_links(manifest):
        if urlparse(href).scheme in {"http", "https"}:
            # External links (Tableau share URLs) are covered by the dedicated embed gate,
            # which checks their FORM. Reachability is not assertable offline and is not
            # claimed here.
            external += 1
            continue
        checked += 1
        target = resolve_like_s3(href)
        if not target.is_file():
            broken.append(f"{surface_id}: {href!r} -> {target.relative_to(BUNDLE)} does not exist")

    # Also check the entry form's own generated dependency, which is loaded by the page rather
    # than linked from the manifest.
    for required in ["field_schema.json", "field_validate.js", "provenance_v1.json",
                     "operations.json", "engines.json", "simulink.json"]:
        checked += 1
        if not (BUNDLE / required).is_file():
            broken.append(f"page requires {required}, which is not in the bundle")

    if broken:
        print(f"{len(broken)} broken link(s) — these are 404s for every reader on the web tier:")
        for item in broken:
            print(f"  {item}")
        print("\nNote: these can still WORK locally. Python's http.server generates directory\n"
              "listings; S3 does not. Passing on the desktop tier proves nothing here.")
        return 1

    print(f"all {checked} bundle-internal links resolve to real files "
          f"({external} external links checked by the embed gate instead)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
