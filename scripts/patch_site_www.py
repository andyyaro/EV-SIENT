#!/usr/bin/env python3
"""Apply the website patch package to the tracked site sources. Idempotent.

Why this ran three weeks late
-----------------------------
`docs/operations/website-patch-package/` has existed since before this program started, with a
guide, content, and an acceptance checklist. Measured against the **live** pages, essentially
none of it had been applied: `/privacy.html` and `/standards.html` were 404, no page carried an
authority disclaimer or a source-vintage footer, and - the one that matters most -
`results.html` presented site rankings and advance/monitor recommendations with **zero**
mentions of capacity, placeholder, estimate or caveat.

That last point is not a documentation nicety. Every one of the contract's 120 rows is
`capacity_basis = placeholder` and `data_confidence = Low`. The live results page told a reader
which sites to advance without telling them that nobody has confirmed the electrical service
at any of them.

The patches could not be applied as code before now because **the pages were not in the
repository at all** - they existed only as S3 objects. They are now under `site/www/`, so this
is a reviewable diff instead of a hand-edit of production.

Every factual claim inserted here was checked against `data/contract/v1/` before use: the grid
factor (596.3 lb CO2e/MWh, eGRID2023r2, accessed 2026-07-19), "all 12 sites score Low data
confidence -- none reaches even Medium" (this said "0 of 12 at High confidence" until the
weaker phrasing was replaced everywhere),
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
  Planning-support prototype - nothing on this site is an approval or an official forecast.
  <a href="privacy.html" style="color:#1B4332;">Privacy</a> ·
  <a href="standards.html" style="color:#1B4332;">Standards</a>
</footer>
"""

AUTHORITY_DISCLAIMER = """
<aside class="fcf-authority" role="note" style="background:rgba(176,137,72,.12);border-top:1px solid #B08948;border-bottom:1px solid #B08948;padding:.85rem 1.15rem;font-size:.9rem;line-height:1.55;color:#2b2b2b;">
  <strong>What this site is - and is not.</strong> This is a Future City Fellowship
  planning-support prototype. It is <strong>not</strong> engineering advice, a permit or
  code-compliance determination, a utility capacity confirmation, an official forecast, or a
  procurement or construction authorization. Every siting decision remains subject to
  electrical, ADA, fire/AHJ, stormwater and permitting review by the responsible authorities.
  <strong>No site shown here is approved.</strong>
  <strong>Electrical capacity is an unverified placeholder at all twelve sites</strong> -
  nobody has confirmed the service could support chargers.
</aside>
"""

#: The single most important insertion in this file. Placed on the results page specifically,
#: because that is where a reader meets "advance this site" language.
CAPACITY_CAVEAT = """
<aside class="fcf-capacity-caveat" role="note" style="background:rgba(179,38,30,.08);border-left:4px solid #b3261e;padding:.85rem 1.15rem;margin:1rem 0;font-size:.92rem;line-height:1.55;">
  <strong>Electrical capacity is a placeholder at all twelve sites.</strong> Nobody has
  confirmed that the electrical service at any site could support chargers - every row of the
  canonical contract reads <code>capacity_basis = placeholder</code>, and
  <strong>all 12 sites score Low data confidence - none reaches even Medium</strong>. The rankings below compare sites
  on modelled demand and screening-class cost; they are <em>not</em> a statement that any site
  is electrically feasible. No feasibility claim is permitted on placeholder capacity, and none
  is made here.
</aside>
"""


#: FIND-NUM-03, open since Phase 0 and never disclosed to a reader until now.
#:
#: The rotating gallery on results.html publishes `legacy_score` for six sites -- FFX002 58.8,
#: FFX004 54.4, PWC006 52.1, PWC002 50.3, PWC008 40.1, PWC003 29.6 -- all six matching
#: `legacy_v2` exactly and none matching `milestone2_v3`. It names FFX002 as "Top overall
#: candidate"; canonically that is FFX004 at 53.4. The page names no mode anywhere.
#:
#: The scores are NOT changed here. The owner asked for the 3D gallery to be kept as it is,
#: and re-baselining the public headline recommendation is a decision about a deliverable a
#: client has already seen, not a repair an assistant should make unilaterally. What was
#: genuinely wrong is that a reader could not tell which model produced these numbers. That is
#: fixed; the re-baselining question is logged as a human action.
MODE_MARKER = "fcf-mode-note"

MODE_NOTE = """
<aside class="fcf-mode-note" role="note" style="background:rgba(27,67,50,.07);border-left:4px solid #1B4332;padding:.8rem 1.1rem;margin:1rem 0;font-size:.9rem;line-height:1.55;">
  <strong>These rankings come from the canonical <code>milestone2_v3</code> model.</strong>
  An earlier published version of this page showed <code>legacy_v2</code> scores, under which
  FFX002 led at 58.8. The canonical model uses fixed anchors rather than scoring sites against
  each other, and ranks <strong>FFX004 (Fairfax County Government Center) first at 53.4</strong>,
  with FFX002 second at 51.8. This page has been corrected; the change is recorded rather than
  made silently. Neither ordering is a feasibility finding - electrical capacity is an
  unverified placeholder at all twelve sites.
</aside>
"""


#: Every place `results.html` called `legacy_v2` output "current" or "latest".
#:
#: The scores are frozen at the owner's request; these are not scores. A currency claim that
#: the page's own mode note directly negates is a contradiction, not a preserved deliverable.
#:
#: The "Results Explorer" line is a different problem: it asserted the provenance AND the
#: completeness of a THIRD-PARTY Framer iframe -- content outside this repository, outside
#: version control, and outside every gate this repository has. We cannot verify what it serves, so we no longer
#: claim what it contains.
CURRENCY_CORRECTIONS = [
    # The gallery is now generated from `milestone2_v3`, so the legacy hedging added while it
    # still published legacy scores is itself now wrong. Each entry maps EVERY prior variant
    # of a sentence to the canonical one, because this page has been patched more than once
    # and a rule that matches only the original text silently does nothing.
    ("The current model identifies which candidate sites appear strongest",
     "The canonical <code>milestone2_v3</code> model identifies which candidate sites appear "
     "strongest"),
    ("This page's rankings come from the <code>legacy_v2</code> baseline. They identify which "
     "candidate sites appear strongest under that mode",
     "The canonical <code>milestone2_v3</code> model identifies which candidate sites appear "
     "strongest"),

    ("An auto-rotating 3D gallery of the highest-priority planning signals from the "
     "latest model run.",
     "An auto-rotating 3D gallery of planning signals from the canonical "
     "<code>milestone2_v3</code> model."),
    ("An auto-rotating 3D gallery of the highest-priority planning signals from the "
     "<code>legacy_v2</code> baseline run.",
     "An auto-rotating 3D gallery of planning signals from the canonical "
     "<code>milestone2_v3</code> model."),

    # The static fallback shown before the JS runs. It named FFX002 as the top card; the
    # canonical top card is FFX004.
    ('<p class="detail-latin" id="detailLatin">FFX002 · City of Fairfax Regional Library</p>',
     '<p class="detail-latin" id="detailLatin">FFX004 · Fairfax County Government Center</p>'),
    ('<p class="detail-description" id="detailDescription">Best current planning signal.',
     '<p class="detail-description" id="detailDescription">Rank 1 of 12 under the canonical '
     'milestone2_v3 model.'),
    ('<p class="detail-description" id="detailDescription">Strongest site under the legacy_v2 '
     'baseline; FFX004 leads under the current model.',
     '<p class="detail-description" id="detailDescription">Rank 1 of 12 under the canonical '
     'milestone2_v3 model.'),

    # The embedded report is a separate, still-legacy artifact (owner decision 8d).
    ("A generated planning report is embedded below from an external host. Its contents are "
     "not verified by this repository; the authoritative copy is the one in "
     "<code>reports/</code>.",
     "A planning report is embedded below from an external host; this repository cannot verify "
     "what that host serves. The copy tracked here was generated <strong>2026-06-28 from the "
     "<code>legacy_v2</code> baseline</strong> - its table is headed &ldquo;Current Site "
     "Ranking&rdquo; but its scores are superseded by the gallery above, and it names no model "
     "mode. Treat it as a dated artifact, not as current model output."),
    ("The full planning analysis from the latest model run is available below as a generated "
     "report.",
     "A planning report is embedded below from an external host; this repository cannot verify "
     "what that host serves. The copy tracked here was generated <strong>2026-06-28 from the "
     "<code>legacy_v2</code> baseline</strong> - its table is headed &ldquo;Current Site "
     "Ranking&rdquo; but its scores are superseded by the gallery above, and it names no model "
     "mode. Treat it as a dated artifact, not as current model output."),
    ("carries the same superseded scores as the gallery above, and names no "
     "model mode.",
     "its scores are superseded by the gallery above, and it names no model mode."),
]


#: `methodology.html` calls V2-baseline figures "current" and "latest" three times. The 38
#: REVIEW / 12 INFO counts and the 15 Tableau exports are the V2 workflow's output, per
#: Final_Report.md:22 ("the full 25-step V2 workflow re-run"). No rank or score appears here,
#: so it is not a mode-naming exception -- it is the same currency claim, one page over, on a
#: live public surface.
METHODOLOGY_CORRECTIONS = [
    ("<h3>Current Model Run Summary</h3>",
     "<h3>Baseline Model Run Summary (<code>legacy_v2</code>)</h3>"),
    ("The latest execution of the planning-support prototype yielded the following outputs",
     "The <code>legacy_v2</code> baseline run of the planning-support prototype yielded the "
     "following outputs"),
    ("The latest model run has zero blocking validation errors.",
     "That baseline run has zero blocking validation errors."),
    # Six scenarios are listed under the heading "Current scenarios tested". The canonical
    # contract carries FOUR scenario names -- baseline, base, high, stress_combined -- and the
    # six named here (adding long sessions, short daily window, peakier demand) are the
    # legacy_v2 sweep. Labelled rather than rewritten: the sweep genuinely ran, it is simply
    # not what "current" means.
    ("<p>Current scenarios tested include:</p>",
     "<p>Scenarios tested in the <code>legacy_v2</code> sweep. The canonical "
     "<code>milestone2_v3</code> contract carries four scenario names - "
     "<code>baseline</code>, <code>base</code>, <code>high</code>, "
     "<code>stress_combined</code>:</p>"),
    ('<span class="insight-eyebrow">Current results</span>',
     '<span class="insight-eyebrow">Results (legacy_v2 sweep)</span>'),
]


# --------------------------------------------------------------- the rotating gallery
#
# The gallery published `legacy_v2` scores with no mode named, headlining FFX002 at 58.8 when
# the canonical top site is FFX004 at 53.4 (FIND-NUM-03, open since Phase 0). The owner has
# cleared re-baselining it to `milestone2_v3`.
#
# It is GENERATED rather than hand-corrected. Hand-editing would fix today's six numbers and
# leave the same trap armed: this array drifted away from the model once already, silently,
# for months. Only the SELECTION of sites and their presentation fields are editorial; every
# score, rank, tier and port count is read from the canonical fixture and the contract.

#: The editorial choice: six sites spanning the decision categories, not simply the top six.
#: Presentation fields are preserved verbatim from the original cards.
GALLERY_PRESENTATION = {
    "FFX002": {"seed": 1103, "site": "City of Fairfax Regional Library"},
    "FFX004": {"seed": 2339, "site": "Fairfax County Government Center"},
    "PWC006": {"seed": 3721, "site": "Bull Run Library"},
    "PWC002": {"seed": 4193, "site": "Neabsco-Potomac Commuter Garage"},
    "PWC008": {"seed": 5377, "site": "Potomac Library"},
    "PWC003": {"seed": 6791, "site": "Public Safety Training Center"},
}

#: Card headings for positions after the top two, keyed by the canonical tier text so they
#: cannot contradict the tier shown beside them.
TIER_TITLE = {
    "Tier 1 - advance to site screening": "Strong starter candidate",
    "High-review candidate": "Useful but high-review",
    "Tier 2 - promising candidate, refine data": "Promising, needs better data",
    "Tier 3 - lower priority / monitor": "Monitor before expanding",
    "Low public-priority / special-use": "Do not advance yet",
}

TIER_SHORT = {
    "Tier 1 - advance to site screening": "Tier 1",
    "High-review candidate": "High-review",
    "Tier 2 - promising candidate, refine data": "Tier 2",
    "Tier 3 - lower priority / monitor": "Tier 3",
    "Low public-priority / special-use": "Special-use",
}


def build_specimens() -> str:
    """Emit the gallery array from `milestone2_v3`, ordered by canonical rank."""
    import csv as _csv
    import json as _json

    scores = {}
    with open(REPO / "tests/fixture_milestone2_v3_site_results.csv") as fh:
        for row in _csv.DictReader(fh):
            scores[row["site_id"]] = row

    ports = {}
    with open(REPO / "data/contract/v1/scenario_table.csv") as fh:
        for row in _csv.DictReader(fh):
            if row["horizon_year"] == "2026":
                ports[row["site_id"]] = row

    chosen = sorted(GALLERY_PRESENTATION, key=lambda s: int(scores[s]["model_rank"]))

    out = []
    for position, site_id in enumerate(chosen):
        src, pres = scores[site_id], GALLERY_PRESENTATION[site_id]
        tier_full = src["recommendation_tier"]
        score = float(src["readiness_score"])
        now = int(float(ports[site_id]["ports_active"]))
        pathway = int(float(ports[site_id]["ports_pathway_capacity"]))

        if position == 0:
            title = "Top overall candidate"
        elif position == 1:
            title = "Second strongest candidate"
        else:
            title = TIER_TITLE.get(tier_full, tier_full)

        staging = (f"Install now: {now} ports. Future-ready: {pathway} ports."
                   if pathway > now else
                   f"Install now: {now} ports, with no additional pathway modelled.")

        out.append({
            "code": site_id,
            "title": title,
            "label": f"{site_id} · {pres['site']}",
            "site": pres["site"],
            "image": "img/card-background.png",
            "score": f"{score:.1f}",
            "tier": TIER_SHORT.get(tier_full, tier_full),
            "priority": len(chosen) - position,
            "seed": pres["seed"],
            "description": (
                f"Rank {src['model_rank']} of 12 under the canonical milestone2_v3 model. "
                f"Score: {score:.1f}. Tier: {tier_full}. {staging} "
                f"Readiness compares sites; it is not a finding that this site is "
                f"electrically feasible."),
        })

    body = ",\n        ".join(_json.dumps(item, ensure_ascii=False) for item in out)
    return "const specimens = [\n        " + body + "\n      ];"


def read(page: str) -> str:
    return (WWW / page).read_text()


def write(page: str, text: str) -> None:
    (WWW / page).write_text(text)


def insert_before_body_close(text: str, block: str) -> str:
    if "</body>" in text:
        return text.replace("</body>", f"{block}\n</body>", 1)
    return text + block


def replace_block(text: str, css_class: str, block: str) -> str:
    """Swap an existing generated `<aside class="...">` for the canonical one, in place.

    EVERY generated block needs this, not just one. The disclaimer was given a replace path
    first and the capacity caveat was left insert-only -- so editing `CAPACITY_CAVEAT`'s text
    changed the source and **nothing on any page**, which is the identical defect one block
    over, and it survived a full gate run because the marker was still present.

    Matches the element non-greedily. These asides never nest, so a non-greedy match to the
    first `</aside>` is exact rather than merely usually-right. If the element is absent the
    text is returned unchanged and the caller's own check reports the page, which is better
    than a partial rewrite.
    """
    pattern = re.compile(r'<aside class="' + re.escape(css_class) + r'".*?</aside>', re.S)
    if not pattern.search(text):
        return text
    return pattern.sub(lambda _m: block.strip(), text, count=1)


def insert_after_nav_or_body_open(text: str, block: str) -> str:
    """Put the disclaimer high on the page - after the whole masthead, before the content.

    ``</header>`` is tried before ``</nav>`` and that ordering is the entire point. These pages
    wrap the nav in ``<header class="topbar">``, which is a **flex container**; inserting after
    ``</nav>`` put the disclaimer *inside* it, where it became a flex item and rendered as a
    narrow column squashed against one edge. It was correct, present, and unreadable - which is
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
<title>{title} - Future City GMU</title>
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
    """Deliberately tiny. These two documents are headings, paragraphs, lists and bold - using
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
        else:
            # This block is GENERATED, so it must be rewritten when it changes -- not left
            # alone because a marker happens to be present. Insert-only was how the whole
            # patch package sat unapplied for three weeks (Phase 8.3): the check asked
            # "is there a disclaimer?" rather than "is it the current one?", so amending
            # the text here would have silently changed nothing on any existing page.
            text = replace_block(text, "fcf-authority", AUTHORITY_DISCLAIMER)
        if VINTAGE_MARKER not in text:
            text = insert_before_body_close(text, VINTAGE_FOOTER)
        if page == "results.html" and MODE_MARKER not in text:
            # Immediately before the rotating gallery, so the mode is read before the scores.
            gallery = '<section class="section top-signals-section">'
            if gallery in text:
                text = text.replace(gallery, MODE_NOTE.strip() + "\n  " + gallery, 1)

        if page == "methodology.html":
            for stale, fixed in METHODOLOGY_CORRECTIONS:
                text = text.replace(stale, fixed)
        if page == "results.html":
            # The gallery data itself, regenerated from `milestone2_v3` every run. Unguarded
            # and idempotent: the array is replaced wholesale, so running twice produces the
            # same bytes and a model change flows through automatically instead of drifting.
            text = re.sub(r"const specimens = \[.*?\];", lambda _m: build_specimens(),
                          text, count=1, flags=re.S)
            # NOT guarded by a marker. These are corrections to prose that already exists, so
            # a marker guard would skip them on every page that has been patched before --
            # which is the insert-only trap this file has now fallen into three times. Plain
            # string replacement is idempotent: once the stale text is gone there is nothing
            # left to match.
            for stale, fixed in CURRENCY_CORRECTIONS:
                text = text.replace(stale, fixed)
        if page == "results.html" and MODE_MARKER in text:
            text = replace_block(text, "fcf-mode-note", MODE_NOTE)
        if page == "results.html" and CAVEAT_MARKER in text:
            text = replace_block(text, "fcf-capacity-caveat", CAPACITY_CAVEAT)
        if page == "results.html" and CAVEAT_MARKER not in text:
            # Immediately after the disclaimer, so it is above the rankings rather than
            # below them.
            text = text.replace("</aside>", "</aside>\n" + CAPACITY_CAVEAT, 1)

        # Six references to one image that was uploaded six times under six names. Collapsing
        # them saves a visitor 6.5 MB and removes 6.5 MB of duplicate storage; the rendered
        # page is byte-for-byte the same picture it was before.
        # Also strips the absolute origin the originals carried. An absolute URL means the
        # page cannot be previewed anywhere but production - the local render showed six
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
