#!/usr/bin/env python3
"""The public website must carry its own caveats. Gated, because it did not for three weeks.

What this enforces and why each item is here
--------------------------------------------
The website patch package shipped with an acceptance checklist and none of it was applied. The
live pages presented site rankings and advance/monitor recommendations while saying nothing
about the study's headline limitation. This gate turns that checklist into a build failure.

The load-bearing item is the capacity caveat on `results.html`. Every one of the contract's
120 rows is `capacity_basis = placeholder` and `data_confidence = Low`; a results page that
recommends advancing a site without saying so is making a claim the data does not support.

The numeric assertions are checked against `data/contract/v1/` rather than hard-coded, so a
regenerated contract that moves the grid factor fails this gate instead of silently leaving a
stale number on the public site.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WWW = REPO / "site/www"

PAGES = ["index.html", "results.html", "methodology.html", "dashboard.html",
         "assistant.html", "privacy.html", "standards.html"]

REQUIRED_EVERYWHERE = [
    ("fcf-authority", "authority disclaimer"),
    ("fcf-vintage", "source-vintage footer"),
    ('href="privacy.html"', "privacy link"),
    ('href="standards.html"', "standards link"),
    # Added in Phase 9. The capacity caveat was required on results.html only, on the
    # reasoning that results.html is where "advance this site" language appears. But the
    # HOME PAGE never once used the word `placeholder` -- the single most important fact
    # about this study was absent from the first page anyone sees, and a reader who landed
    # there and went no further was never told it. It is cheap to state everywhere and
    # expensive to omit anywhere.
    ("placeholder at all twelve sites", "capacity-placeholder statement"),
]


def main() -> int:
    problems: list[str] = []

    for page in PAGES:
        path = WWW / page
        if not path.is_file():
            problems.append(f"{page}: missing entirely")
            continue
        text = path.read_text()
        for marker, label in REQUIRED_EVERYWHERE:
            if marker not in text:
                problems.append(f"{page}: no {label}")
        # The six-times-duplicated background. Re-introducing any of them costs a visitor
        # 6.5 MB for pictures that are the same picture.
        for dup in re.findall(r"image[1-6]\.png", text):
            problems.append(f"{page}: references {dup}, a duplicate of img/card-background.png")

    results = WWW / "results.html"
    if results.is_file():
        text = results.read_text()
        if "fcf-capacity-caveat" not in text:
            problems.append(
                "results.html: NO capacity caveat. This page recommends advancing sites; "
                "without it the page makes a claim the contract does not support.")
        if "placeholder" not in text.lower():
            problems.append("results.html: never uses the word 'placeholder'")
        # FIND-NUM-03. The rotating gallery publishes legacy_v2 scores and named no mode at
        # all, so a reader met a ranking with no way to know which model produced it -- and
        # the headline it names is not the canonical top site. The scores are deliberately
        # unchanged (the owner asked for the gallery as-is); the disclosure is mandatory.
        if "fcf-mode-note" not in text:
            problems.append(
                "results.html: NO model-mode note. The gallery must state which model "
                "produced its scores.")

        # The gallery drifted away from the model once, silently, and published the wrong top
        # site publicly for months. It is now generated from the canonical fixture -- this
        # asserts the published bytes actually match it, because a generator nobody re-runs is
        # just a slower way to drift.
        import json as _json
        match = re.search(r"const specimens = (\[.*?\]);", text, re.S)
        if not match:
            problems.append("results.html: the gallery data block is missing entirely")
        else:
            try:
                gallery = _json.loads(match.group(1))
            except ValueError as exc:
                problems.append(f"results.html: gallery data is not valid JSON ({exc})")
                gallery = []
            canonical = {}
            fixture = REPO / "tests/fixture_milestone2_v3_site_results.csv"
            if fixture.is_file():
                for row in csv.DictReader(open(fixture)):
                    canonical[row["site_id"]] = row
            for card in gallery:
                site = card.get("code")
                if site not in canonical:
                    problems.append(f"results.html: gallery card {site!r} is not a known site")
                    continue
                expected = f'{float(canonical[site]["readiness_score"]):.1f}'
                if card.get("score") != expected:
                    problems.append(
                        f"results.html: gallery shows {site} at {card.get('score')}, "
                        f"canonically {expected} — the gallery has drifted from the model")
            ranks = [int(canonical[c["code"]]["model_rank"]) for c in gallery
                     if c.get("code") in canonical]
            if ranks != sorted(ranks):
                problems.append(
                    "results.html: gallery cards are not in canonical rank order; the first "
                    "card is titled 'Top overall candidate' and must be the top-ranked site")

    # Every figure the site states must still be the contract's figure.
    rows = list(csv.DictReader(open(REPO / "data/contract/v1/scenario_table.csv")))
    factors = {r["grid_factor_value"] for r in rows}
    bases = {r["capacity_basis"] for r in rows}
    highs = [r for r in rows if r["data_confidence"] == "High"]

    for page in ["results.html", "methodology.html", "index.html"]:
        path = WWW / page
        if not path.is_file():
            continue
        text = path.read_text()
        if "596.3" in text and factors != {"596.3"}:
            problems.append(f"{page}: states 596.3 lb CO2e/MWh but the contract now has {factors}")
        if "placeholder at all twelve" in text and bases != {"placeholder"}:
            problems.append(f"{page}: claims placeholder everywhere but contract has {bases}")
        # Kept as a trap: the weaker "0 of 12 reach High" phrasing was replaced everywhere
        # because it lets a reader infer eleven sites might be Medium. If it ever comes back,
        # this still checks it against the contract.
        if "0 of 12" in text and highs:
            problems.append(f"{page}: claims 0 of 12 at High confidence but {len(highs)} rows are High")
        # The phrasing that actually ships. Without this the stronger claim was ungated while
        # the guard above quietly protected a string no page contains any more.
        if "none reaches even Medium" in text:
            above_low = sorted({r["data_confidence"] for r in rows} - {"Low"})
            if above_low:
                problems.append(
                    f"{page}: claims no site reaches Medium, but the contract has "
                    f"{above_low} confidence rows")


    # --- Tableau embeds -------------------------------------------------------------
    # The original workbook was audited, found wrong (DEC-013), republished under a new name,
    # and the original deleted — but nothing re-pointed the website, so every embed resolved to
    # `public.tableau.com/app/resource-not-found`. Note that Tableau answers 302 for live and
    # dead views alike, so a status check proves nothing; this gate checks the NAME.
    DELETED_WORKBOOK = "EV_Charging_Site_Readiness_Workbook"
    CANONICAL_WORKBOOK = "EV_Charging_Site_Readiness_M2_Canonical"

    for page in ["dashboard.html", "results.html"]:
        path = WWW / page
        if not path.is_file():
            continue
        text = path.read_text()
        dead = sorted(set(re.findall(DELETED_WORKBOOK + r"/([A-Za-z0-9\-]+)", text)))
        if dead:
            problems.append(f"{page}: references the DELETED workbook: {dead}")

        # A counter that overstates how many views exist is the kind of small lie that makes a
        # reader distrust the large ones.
        slides = len(re.findall(r'<article class="exploreSlide" data-slide="\d+">', text))
        if slides:
            for stated in set(re.findall(r'navCounter"><span class="slideNum">\d+</span>\s*/\s*(\d+)', text)):
                if int(stated) != slides:
                    problems.append(f"{page}: carousel says {stated} views, deck has {slides}")
            views = re.search(r'<span class="statLabel">Planning views</span>\s*'
                              r'<strong class="statValue">(\d+)</strong>', text, re.S)
            if views and int(views.group(1)) != slides:
                problems.append(f"{page}: hero says {views.group(1)} planning views, deck has {slides}")

        # Every chart on screen must be named correctly by the words around it.
        for m in re.finditer(r'<article class="exploreSlide".*?</article>', text, re.S):
            block = m.group(0)
            sheet = re.search(r'<iframe[^>]*src="[^"]*' + CANONICAL_WORKBOOK + r'/([A-Za-z0-9]+)', block)
            title = re.search(r'<h2 class="slideTitle">(.*?)</h2>', block, re.S)
            if sheet and title:
                for stale in ["Review Burden", "Model Transparency", "Scenario Stress Testing",
                              "Action Recommendations"]:
                    if stale in title.group(1):
                        problems.append(
                            f"{page}: a slide is still titled {stale!r} but now shows "
                            f"{sheet.group(1)} — the caption describes a chart that is gone")

    if problems:
        print(f"{len(problems)} problem(s) with the public website:")
        for item in problems:
            print(f"  {item}")
        return 1

    print(f"all {len(PAGES)} public pages carry their disclaimers, footers and caveats; "
          f"every stated figure matches contract v1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
