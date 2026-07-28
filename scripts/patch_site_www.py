#!/usr/bin/env python3
"""Apply the website patch package to the tracked site sources. Idempotent.

Why this ran three weeks late
-----------------------------
`docs/operations/website-patch-package/` has existed since before this program started, with a
guide, content, and an acceptance checklist. Measured against the **live** pages, essentially
none of it had been applied: `/privacy.html` and `/standards.html` were 404, no page carried an
authority disclaimer or a source-vintage footer, and — the one that matters most —
`results.html` presented site rankings and advance/monitor recommendations with **zero**
mentions of capacity, placeholder, estimate or caveat.

That last point is not a documentation nicety. Every one of the contract's 120 rows is
`capacity_basis = placeholder` and `data_confidence = Low`. The live results page told a reader
which sites to advance without telling them that nobody has confirmed the electrical service
at any of them.

The patches could not be applied as code before now because **the pages were not in the
repository at all** — they existed only as S3 objects. They are now under `site/www/`, so this
is a reviewable diff instead of a hand-edit of production.

Every factual claim inserted here was checked against `data/contract/v1/` before use: the grid
factor (596.3 lb CO2e/MWh, eGRID2023r2, accessed 2026-07-19), "0 of 12 at High confidence",
"placeholder everywhere", and the contract version and generation date. A footer asserting a
number the contract disagrees with would manufacture the divergence this phase exists to
remove.

Idempotent by design: every insertion is guarded by a marker, so running twice changes nothing
and a later content edit is a normal edit rather than a merge conflict with a generator.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WWW = REPO / "site/www"
PATCHES = REPO / "docs/operations/website-patch-package/content"

PAGES = ["index.html", "results.html", "methodology.html", "dashboard.html", "assistant.html"]

VINTAGE_MARKER = "fcf-vintage"
DISCLAIMER_MARKER = "fcf-authority"
CAVEAT_MARKER = "fcf-capacity-caveat"

VINTAGE_FOOTER = """
<footer class="fcf-vintage" style="font-size:.75rem;color:#4b4b4b;background:#f7f3ea;border-top:1px solid #d8cdb6;padding:.7rem 1.15rem;line-height:1.5;">
  Data: canonical contract v1.0.0 (generated 2026-07-19) · site inputs 2026-06-24 ·
  emissions factor EPA eGRID2023 Rev&nbsp;2, SRVC, 596.3&nbsp;lb&nbsp;CO2e/MWh
  (accessed 2026-07-19; refreshed annually) ·
  Planning-support prototype — nothing on this site is an approval or an official forecast.
  <a href="privacy.html" style="color:#1B4332;">Privacy</a> ·
  <a href="standards.html" style="color:#1B4332;">Standards</a>
</footer>
"""

AUTHORITY_DISCLAIMER = """
<aside class="fcf-authority" role="note" style="background:rgba(176,137,72,.12);border-top:1px solid #B08948;border-bottom:1px solid #B08948;padding:.85rem 1.15rem;font-size:.9rem;line-height:1.55;color:#2b2b2b;">
  <strong>What this site is — and is not.</strong> This is a Future City Fellowship
  planning-support prototype. It is <strong>not</strong> engineering advice, a permit or
  code-compliance determination, a utility capacity confirmation, an official forecast, or a
  procurement or construction authorization. Every siting decision remains subject to
  electrical, ADA, fire/AHJ, stormwater and permitting review by the responsible authorities.
  <strong>No site shown here is approved.</strong>
</aside>
"""

#: The single most important insertion in this file. Placed on the results page specifically,
#: because that is where a reader meets "advance this site" language.
CAPACITY_CAVEAT = """
<aside class="fcf-capacity-caveat" role="note" style="background:rgba(179,38,30,.08);border-left:4px solid #b3261e;padding:.85rem 1.15rem;margin:1rem 0;font-size:.92rem;line-height:1.55;">
  <strong>Electrical capacity is a placeholder at all twelve sites.</strong> Nobody has
  confirmed that the electrical service at any site could support chargers — every row of the
  canonical contract reads <code>capacity_basis = placeholder</code>, and
  <strong>0 of 12 sites reach High data confidence</strong>. The rankings below compare sites
  on modelled demand and screening-class cost; they are <em>not</em> a statement that any site
  is electrically feasible. No feasibility claim is permitted on placeholder capacity, and none
  is made here.
</aside>
"""


def read(page: str) -> str:
    return (WWW / page).read_text()


def write(page: str, text: str) -> None:
    (WWW / page).write_text(text)


def insert_before_body_close(text: str, block: str) -> str:
    if "</body>" in text:
        return text.replace("</body>", f"{block}\n</body>", 1)
    return text + block


def insert_after_nav_or_body_open(text: str, block: str) -> str:
    """Put the disclaimer high on the page — after the whole masthead, before the content.

    ``</header>`` is tried before ``</nav>`` and that ordering is the entire point. These pages
    wrap the nav in ``<header class="topbar">``, which is a **flex container**; inserting after
    ``</nav>`` put the disclaimer *inside* it, where it became a flex item and rendered as a
    narrow column squashed against one edge. It was correct, present, and unreadable — which is
    the same "hand-pressed and cut off" failure this project has already shipped once.
    """
    header = re.search(r"</header>", text)
    if header:
        return text[: header.end()] + "\n" + block + text[header.end():]
    nav = re.search(r"</nav>", text)
    if nav:
        return text[: nav.end()] + "\n" + block + text[nav.end():]
    body = re.search(r"<body[^>]*>", text)
    if body:
        return text[: body.end()] + "\n" + block + text[body.end():]
    return block + text


def build_standalone(title: str, heading: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Future City GMU</title>
<style>
body{{margin:0;background:#f5f2ea;color:#101214;font:17px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
.w{{max-width:46rem;margin:0 auto;padding:2.6rem 1.15rem}}
h1{{color:#214f3f;font-size:1.6rem;margin:0 0 1rem}}
h2{{color:#214f3f;font-size:1.12rem;margin:1.8rem 0 .5rem}}
nav a{{color:#214f3f;margin-right:1rem;font-size:.9rem}}
code{{background:rgba(16,18,20,.07);padding:.1em .35em;border-radius:3px;font-size:.9em}}
li{{margin:.35rem 0}}
</style></head><body>
<nav style="padding:1rem 1.15rem;border-bottom:1px solid rgba(16,18,20,.1);">
  <a href="index.html">Home</a><a href="dashboard.html">Dashboard</a><a href="results.html">Results</a>
  <a href="methodology.html">Methodology</a><a href="assistant.html">AI Assistant</a>
</nav>
{AUTHORITY_DISCLAIMER}
<div class="w"><h1>{heading}</h1>
{body_html}
</div>
{VINTAGE_FOOTER}
</body></html>
"""


def markdown_to_html(md: str) -> str:
    """Deliberately tiny. These two documents are headings, paragraphs, lists and bold — using
    a Markdown dependency to render them would add a runtime package for two static pages."""
    out, in_list = [], False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith("# "):
            continue                                  # the page supplies its own <h1>
        elif re.match(r"^\s*[-*]\s+|^\s*\d+\.\s+", line):
            if not in_list:
                out.append("<ul>"); in_list = True
            item = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", line)
            out.append(f"<li>{inline(item)}</li>")
        elif not line:
            if in_list:
                out.append("</ul>"); in_list = False
        else:
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<p>{inline(line.lstrip('> '))}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def main() -> int:
    if not WWW.is_dir():
        print(f"{WWW} does not exist"); return 1

    changed: list[str] = []

    for page in PAGES:
        path = WWW / page
        if not path.is_file():
            print(f"  skip {page} (not present)")
            continue
        text = original = read(page)

        if DISCLAIMER_MARKER not in text:
            text = insert_after_nav_or_body_open(text, AUTHORITY_DISCLAIMER)
        if VINTAGE_MARKER not in text:
            text = insert_before_body_close(text, VINTAGE_FOOTER)
        if page == "results.html" and CAVEAT_MARKER not in text:
            # Immediately after the disclaimer, so it is above the rankings rather than
            # below them.
            text = text.replace("</aside>", "</aside>\n" + CAPACITY_CAVEAT, 1)

        # Six references to one image that was uploaded six times under six names. Collapsing
        # them saves a visitor 6.5 MB and removes 6.5 MB of duplicate storage; the rendered
        # page is byte-for-byte the same picture it was before.
        # Also strips the absolute origin the originals carried. An absolute URL means the
        # page cannot be previewed anywhere but production — the local render showed six
        # broken images because the browser was dutifully fetching from the live site.
        text = re.sub(r"https?://futurecityfellowship\.andyyaro\.com/top-model-findings-cards-bgs/image[1-6]\.png",
                      "img/card-background.png", text)
        text = re.sub(r"top-model-findings-cards-bgs/image[1-6]\.png", "img/card-background.png", text)

        if text != original:
            write(page, text)
            changed.append(page)

    # The two pages the patch guide says to create, built from its own content files.
    for slug, title, source in [
        ("privacy.html", "Privacy notice", "privacy_notice.md"),
        ("standards.html", "Standards applied", "standards_summary.md"),
    ]:
        src = PATCHES / source
        if not src.is_file():
            print(f"  cannot create {slug}: {source} missing")
            continue
        html = build_standalone(title, title, markdown_to_html(src.read_text()))
        target = WWW / slug
        if not target.is_file() or target.read_text() != html:
            target.write_text(html)
            changed.append(slug)

    print(f"  patched: {', '.join(changed) if changed else 'nothing (already applied)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
