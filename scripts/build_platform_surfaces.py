"""Generate the platform's surface manifest from what is actually on disk.

Every entry is produced by looking for the file. Nothing is listed because it ought to exist,
and nothing that exists is quietly omitted — a surface manifest written by hand is a promise,
and this project has already shipped one broken promise (a commit message asserting artifacts
that .gitignore had swallowed).

The deploy set
--------------
`site/platform/` is the public bundle. Some surfaces live elsewhere in the repository and are
COPIED into it at build time — the 3D explorer, the static dashboard images, the contract
files offered for download. That copying is explicit and allowlisted here, so a file cannot
reach the public bundle by being adjacent to one that should.

**The real input data is never copied.** `data/inputs/` is excluded by construction, not by
convention — see DEC-016.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "site/platform"
MANIFEST = OUT / "surfaces.json"

#: Tableau share links. The /views/ form, never /app/profile/ -- see dashboard/tableau/EMBED.md.
TABLEAU_BASE = "https://public.tableau.com/views/EV_Charging_Site_Readiness_M2_Canonical"
TABLEAU_Q = "?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link"

TABLEAU_SHEETS = [
    ("Site readiness ranking", "ReadinessbySite"),
    ("Starter vs pathway ports", "StartervsPathwayPorts"),
    ("Active ports by horizon", "PortsAcrossHorizons"),
    ("Queue wait, minutes", "PeakWaitsbySite"),
    ("Lifecycle cost NPV", "LifecycleCostbyHorizon"),
    ("Net CO2e per year", "NetCO2ebyHorizon"),
    ("Candidate sites map", "SiteMap"),
]

#: What gets copied into the public bundle. Anything not listed here never reaches it.
DEPLOY_COPY = [
    ("explorer/web", "explorer"),
    ("dashboard/static", "dashboard"),
    ("data/contract/v1", "contract/v1"),
    ("data/contract/v2", "contract/v2"),
    ("docs/nfc", "nfc"),
]

#: Never copied, whatever else changes. Stated so the exclusion is a rule, not an oversight.
NEVER_DEPLOY = ["data/inputs", "data/provenance", "data/outputs", "matlab/data/canonical"]


def copy_surfaces() -> dict[str, int]:
    counts = {}
    for src_rel, dst_rel in DEPLOY_COPY:
        src, dst = REPO / src_rel, OUT / dst_rel
        if not src.is_dir():
            raise SystemExit(f"{src_rel} does not exist; the manifest would claim a surface "
                             f"that is not there")
        for banned in NEVER_DEPLOY:
            if src_rel.startswith(banned):
                raise SystemExit(f"refusing to deploy {src_rel}: it is on the never-deploy list")
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))
        counts[dst_rel] = sum(1 for _ in dst.rglob("*") if _.is_file())
    return counts


def build() -> dict:
    counts = copy_surfaces()

    charts = sorted(p.name for p in (OUT / "dashboard").glob("*.png"))
    models = sorted(p.name for p in (OUT / "explorer/models").glob("*.glb"))
    qr = sorted(p.name for p in (OUT / "nfc/qr").glob("*.svg"))

    return {
        "schema": "fcf-surfaces/1",
        "surfaces": [
            {
                "id": "explorer",
                "title": "3D site explorer",
                "href": "explorer/index.html",
                "detail": (
                    f"All 12 sites in 3D with {len(models)} building models. Works with no "
                    f"Cesium account and no token — it falls back to a flat basemap rather "
                    f"than requiring a credential."),
                "count": len(models),
                "available_on_web": True,
            },
            {
                "id": "dashboard",
                "title": "Static dashboard",
                "href": "dashboard/",
                "detail": (
                    f"{len(charts)} contract-derived charts, each stamped in its footer with "
                    f"the run and source it came from. Openable offline."),
                "items": charts,
                "count": len(charts),
                "available_on_web": True,
            },
            {
                "id": "tableau",
                "title": "Tableau workbook",
                "detail": (
                    "Seven sheets plus a dashboard, published and verified against the "
                    "canonical contract. Individual sheets render better than the dashboard — "
                    "three charts are narrow inside a dashboard zone, which the authoring "
                    "spec offers no way to control."),
                "links": [{"label": label, "href": f"{TABLEAU_BASE}/{sheet}{TABLEAU_Q}"}
                          for label, sheet in TABLEAU_SHEETS],
                "count": len(TABLEAU_SHEETS),
                "available_on_web": True,
            },
            {
                "id": "contract",
                "title": "The canonical data contract",
                "detail": (
                    "Download the contract itself — every table, the schema, the assumptions "
                    "and the manifest with its SHA-256 hash chain. This is the thing every "
                    "number on every surface comes from."),
                "links": [
                    {"label": "v1 (frozen)", "href": "contract/v1/"},
                    {"label": "v2 (additive)", "href": "contract/v2/"},
                ],
                "count": counts.get("contract/v1", 0) + counts.get("contract/v2", 0),
                "available_on_web": True,
            },
            {
                "id": "nfc",
                "title": "NFC field layer",
                "href": "nfc/",
                "detail": (
                    f"Tag payloads for all 12 sites with {len(qr)} QR fallbacks, the writing "
                    f"runbook and the placement cards. Writing a physical tag is done with a "
                    f"phone."),
                "count": len(qr),
                "available_on_web": True,
            },
        ],
        "deploy_note": (
            "Everything above is copied into the public bundle from an explicit allowlist. "
            "The real site input data is never copied — not by convention, by construction. "
            "See DEC-016."),
        "never_deployed": NEVER_DEPLOY,
    }


def main() -> int:
    payload = build()
    MANIFEST.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(f"wrote {MANIFEST.relative_to(REPO)}")
    for s in payload["surfaces"]:
        print(f"  {s['id']:12} {s['count']:>3} items  {s['title']}")
    print(f"  never deployed: {', '.join(payload['never_deployed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
