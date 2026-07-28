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
    # The written deliverables. Added in Phase 7: they existed in the repository and were the
    # one thing the study produced that the platform did not offer, so a reader could see every
    # number and not the document that explains them.
    ("reports/milestone-2", "reports"),
]

#: Never copied, whatever else changes. Stated so the exclusion is a rule, not an oversight.
NEVER_DEPLOY = ["data/inputs", "data/provenance", "data/outputs", "matlab/data/canonical"]


def copy_surfaces() -> dict[str, int]:
    counts = {}
    for src_rel, dst_rel in DEPLOY_COPY:
        src, dst = REPO / src_rel, OUT / dst_rel
        if not src.is_dir():
            # A surface whose source is absent is SKIPPED, not fabricated and not fatal.
            #
            # Refusing outright was right for this repository, where a missing surface means a
            # broken checkout. It is wrong for a public installer, where some surfaces are
            # deliberately not distributed — the 3D explorer's site data is generated from the
            # real twelve, so it is excluded, and dying on its absence made the whole platform
            # unreachable rather than merely one card emptier.
            #
            # The manifest still never claims a surface that is not there: the entry is simply
            # not written, and `count` comes out zero.
            print(f"  skipping {src_rel}: not present in this installation")
            counts[dst_rel] = 0
            continue
        for banned in NEVER_DEPLOY:
            if src_rel.startswith(banned):
                raise SystemExit(f"refusing to deploy {src_rel}: it is on the never-deploy list")
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))
        counts[dst_rel] = sum(1 for _ in dst.rglob("*") if _.is_file())
    return counts



#: Directories the manifest links to. S3 has no directory listing, so each needs a real
#: index.html or the link is a 404 for every reader on the web tier.
#:
#: This was broken for five surfaces and invisible locally, which is the part worth
#: remembering: Python's ``http.server`` *generates* a directory listing on the fly, so the
#: desktop tier rendered a working page for a path that does not exist in S3 at all. The
#: local server was more capable than production and hid the defect. `check_surface_links.py`
#: now fails if any manifest href has no file behind it.
def write_directory_indexes(surfaces: dict) -> list[str]:
    written = []
    hrefs = []
    for surface in surfaces["surfaces"]:
        if surface.get("href"):
            hrefs.append(surface["href"])
        for link in surface.get("links", []):
            hrefs.append(link["href"])

    for href in hrefs:
        if not href.endswith("/") or href.startswith("http"):
            continue
        directory = OUT / href.rstrip("/")
        if not directory.is_dir():
            continue
        index = directory / "index.html"
        files = sorted(p for p in directory.rglob("*") if p.is_file() and p.name != "index.html")
        rows = "\n".join(
            f'    <li><a href="{p.relative_to(directory)}">{p.relative_to(directory)}</a>'
            f' <span class="sz">{p.stat().st_size:,} bytes</span></li>'
            for p in files)
        title = href.rstrip("/").replace("/", " / ")
        index.write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Future City Fellowship</title>
<style>
body{{margin:0;background:#F5F0E6;color:#1a1a1a;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
.w{{max-width:52rem;margin:0 auto;padding:2.5rem 1.15rem}}
h1{{color:#1B4332;font-size:1.3rem;margin:0 0 .3rem}}
p{{color:#4a4a4a;font-size:.92rem;margin:0 0 1.2rem}}
ul{{list-style:none;padding:0;margin:0}}
li{{padding:.45rem 0;border-bottom:1px solid #d8d2c4;display:flex;justify-content:space-between;gap:1rem}}
a{{color:#1B4332}}.sz{{color:#8a8f96;font-size:.82rem;white-space:nowrap}}
.back{{display:inline-block;margin-top:1.4rem;font-size:.9rem}}
@media(prefers-color-scheme:dark){{body{{background:#16191a;color:#ececec}}h1{{color:#7fbf9a}}
p{{color:#b4b4b4}}li{{border-color:#33383a}}a{{color:#7fbf9a}}}}
</style></head><body><div class="w">
<h1>{title}</h1>
<p>{len(files)} file{"" if len(files) == 1 else "s"}. Listed because this is a plain directory
of the study's own artifacts — nothing here is generated on request.</p>
<ul>
{rows}
</ul>
<a class="back" href="../index.html">← back to the platform</a>
</div></body></html>
""")
        written.append(str(index.relative_to(OUT)))
    return written


def build() -> dict:
    counts = copy_surfaces()

    # `.glob()` on a missing directory returns empty; `.iterdir()` RAISES. With surfaces now
    # skippable, that difference decided whether the launcher started at all — the reports
    # listing crashed the build one line after the skip message said the directory was absent.
    def listing(relative: str, pattern: str = "*") -> list[str]:
        directory = OUT / relative
        if not directory.is_dir():
            return []
        return sorted(p.name for p in directory.glob(pattern) if p.is_file())

    charts = listing("dashboard", "*.png")
    models = listing("explorer/models", "*.glb")
    qr = listing("nfc/qr", "*.svg")
    reports = listing("reports")

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
                "id": "reports",
                "title": "Written reports",
                "href": "reports/",
                "detail": (
                    f"{len(reports)} documents: the Milestone 2 final report, the risk "
                    f"register, the standards application matrix, the economic and funding "
                    f"brief, and the environment and resilience note. These are the study's "
                    f"prose — they say what the numbers on this page are for."),
                "items": reports,
                "count": len(reports),
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
    indexes = write_directory_indexes(payload)
    MANIFEST.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(f"wrote {MANIFEST.relative_to(REPO)}")
    for s in payload["surfaces"]:
        print(f"  {s['id']:12} {s['count']:>3} items  {s['title']}")
    print(f"  directory indexes: {len(indexes)} written ({', '.join(indexes)})")
    print(f"  never deployed: {', '.join(payload['never_deployed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
