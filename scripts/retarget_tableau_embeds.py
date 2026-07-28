#!/usr/bin/env python3
"""Re-point the website's Tableau embeds at the canonical workbook. Idempotent.

Why this was necessary
----------------------
The original workbook `EV_Charging_Site_Readiness_Workbook` was audited and found wrong on
three counts (DEC-013), a corrected workbook was published under a new name, and the original
was then deleted. **Nothing re-pointed the website.** Its embeds still named the deleted
workbook, so every one of them resolved to `public.tableau.com/app/resource-not-found` —
verified by following the redirect, because Tableau answers 302 for live and dead views alike
and the status code alone distinguishes nothing.

That dependency was never traced when the deletion was requested. This script is the repair.

Why it is not a find-and-replace
--------------------------------
The deleted workbook had 12 sheets; the canonical one has 7, and they are different analyses.
Four map cleanly. The rest — review burden, per-dimension subscores, profile readiness, rank
stability — came from the **old scoring model**, whose fields the canonical contract does not
carry. They cannot be rebuilt without inventing the numbers underneath them, so they are
removed rather than faked or silently pointed at some unrelated chart.

More importantly, every embed sits inside a slide with a title, tab labels and explanatory copy
describing *that specific old chart*. Swapping only the URLs would leave the page describing
charts it no longer shows — replacing a broken embed with a **false** one, which is worse. So
the surrounding copy is rewritten with the URL.

The slide order was chosen so this script only ever DELETES markup, never synthesises it: the
two-chart slide lands on a slide that already had multiple tabs.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WWW = REPO / "site/www"

OLD_WORKBOOK = "EV_Charging_Site_Readiness_Workbook"
NEW_WORKBOOK = "EV_Charging_Site_Readiness_M2_Canonical"

#: old sheet -> (canonical sheet, human title). Only these four have a genuine counterpart.
SHEET_MAP = {
    "Bar-EVChargingReadinessbySite": ("ReadinessbySite", "Readiness by Site"),
    "Map-EVChargingCandidateReadinesswithContext": ("SiteMap", "Candidate Sites Map"),
    "Line-EVChargingPortGrowthbyPlanningYear": ("StartervsPathwayPorts", "Starter vs Pathway Ports"),
    "Line-PortUtilizationSimulation": ("PortsAcrossHorizons", "Active Ports by Horizon"),
    "HeatMap-ProfileReadinessScorebyScoringProfile": ("LifecycleCostbyHorizon", "Lifecycle Cost NPV"),
    "HeatMap-SiteSubscoresbyDimension": ("NetCO2ebyHorizon", "Net CO2e Avoided per Year"),
    "HeatMap-PortSizingScenarioGaps": ("PeakWaitsbySite", "Queue Wait, Minutes"),
}

#: Slides whose subject has no canonical equivalent at all. Removed entirely.
DELETE_SLIDES = ["4", "7"]

#: Chips inside a surviving slide whose sheet has no counterpart. Removed, leaving the slide.
DELETE_CHIP_SHEETS = ["Range-ProfileRankStabilitybySite", "Lollipop-DataConfidencebySite"]

#: (old slide title, new slide title, new info-bar line)
RETITLE = [
    ("Model Transparency", "Cost and Emissions",
     "Screening-class figures for comparison between sites — never budgets or quotes."),
    ("Scenario Stress Testing", "Waiting Times",
     "Modelled waits, not measured ones. No site has been observed in operation."),
]

CHIP_COPY = {
    "StartervsPathwayPorts": dict(
        label="Starter vs pathway",
        title="Tableau visualization: Starter vs Pathway Ports",
        info="Starter ports are what to install now; pathway capacity is what to leave room for.",
        note="Both figures rest on placeholder electrical capacity and are not feasibility claims.",
        what="Starter port counts against the pathway capacity each site could grow into.",
        why="It connects site selection to sizing, so a starter install does not foreclose growth."),
    "PortsAcrossHorizons": dict(
        label="Across horizons",
        title="Tableau visualization: Active Ports by Horizon",
        info="Look for where demand grows enough to justify more than a starter install.",
        note="Horizons are 2026, 2036, 2046 and 2056. Demand is modelled, never measured.",
        what="Active ports at each planning horizon under the base case.",
        why="It shows which sites change materially over time and which stay flat."),
    "LifecycleCostbyHorizon": dict(
        label="Lifecycle cost",
        title="Tableau visualization: Lifecycle Cost NPV by Horizon",
        info="Screening-class estimates for comparison — not budgets, quotes, or engineering costs.",
        note="Net present value across the study horizons, on published benchmark assumptions.",
        what="Lifecycle cost NPV per site at each horizon.",
        why="It allows sites to be compared on cost without implying any figure is a quote."),
    "NetCO2ebyHorizon": dict(
        label="Net CO2e avoided",
        title="Tableau visualization: Net CO2e Avoided per Year",
        info="Uses the EPA eGRID2023 Rev 2 SRVC factor, which changes annually.",
        note="596.3 lb CO2e/MWh, accessed 2026-07-19. Results must be recomputed when it changes.",
        what="Net annual CO2e associated with each site's modelled charging.",
        why="It states the emissions basis explicitly so the figure can be re-derived."),
}



#: `results.html` uses inline `switchTableau(...)` chips rather than data-attributes. Its two
#: dead tabs are re-pointed at canonical sheets and RELABELLED — leaving a lone tab would look
#: broken, and keeping the old labels over new charts would be a false caption.
RESULTS_CHIPS = {
    "Bar-ReviewBurdenbySite": ("StartervsPathwayPorts", "Starter vs Pathway Ports", "Starter vs pathway"),
    "Matrix-ActionDecisionQuadrant": ("PeakWaitsbySite", "Queue Wait, Minutes", "Queue wait"),
}


def retarget_results_chips(text: str) -> str:
    for old_sheet, (new_sheet, title, label) in RESULTS_CHIPS.items():
        pattern = re.compile(
            r"<button([^>]*?)onclick=\"switchTableau\('([^']*)" + re.escape(old_sheet) +
            r"([^']*)', '([^']*)', this\)\"([^>]*)>([^<]*)</button>")

        def fix(m, ns=new_sheet, ti=title, la=label):
            prefix = m.group(2).replace(OLD_WORKBOOK, NEW_WORKBOOK)
            return (f"<button{m.group(1)}onclick=\"switchTableau('{prefix}{ns}{m.group(3)}', "
                    f"'Tableau visualization: {ti}', this)\"{m.group(5)}>{la}</button>")

        text = pattern.sub(fix, text)
    return text



#: Literal copy that survives elsewhere in the markup — a chip label with no data-url, and the
#: info bars beneath the two repurposed slides. Left alone these describe the OLD chart while
#: the NEW one is on screen, which is a false caption rather than a stale one.
LITERAL_COPY = [
    (">Scenario gaps</button>", ">Queue wait</button>"),
    ("Use this to find where future-ready capacity may break under stress.",
     "Modelled waits under the base case — no site has been observed in operation."),
    ("Stable strong sites are easier to explain to stakeholders.",
     "Screening-class figures for comparing sites — never budgets, quotes, or engineering estimates."),
    ("Tableau visualization: HeatMap - Port Sizing Scenario Gaps",
     "Tableau visualization: Queue Wait, Minutes"),
    ("Start here — compare Tier 1 and high-review sites first.",
     "Start here — compare sites before anything else. Every one rests on placeholder capacity."),
]


def rebuild_deck(text: str) -> str:
    """Renumber the real slides and regenerate the carousel clones from them."""
    block = re.compile(r'(<!--[^>]*?-->\s*)?<article(?P<attrs>[^>]*)class="exploreSlide"(?P<rest>[^>]*)>.*?</article>',
                       re.S)
    matches = list(block.finditer(text))
    if len(matches) < 3:
        return text

    real = [m for m in matches if "data-clone" not in (m.group("attrs") + m.group("rest"))]
    if not real:
        return text

    def renumber(markup: str, index: int) -> str:
        markup = re.sub(r'(data-slide=")\d+(")', lambda m: f"{m.group(1)}{index}{m.group(2)}", markup)
        markup = re.sub(r'(<span class="slideStep">Part )\d+(</span>)',
                        lambda m: f"{m.group(1)}{index}{m.group(2)}", markup)
        return markup

    rebuilt = []
    for i, m in enumerate(real, start=1):
        markup = renumber(m.group(0), i)
        title = re.search(r'<h2 class="slideTitle">(.*?)</h2>', markup, re.S)
        clean = re.sub(r'<[^>]+>', '', title.group(1)).strip() if title else f"Slide {i}"
        markup = re.sub(r'^<!--[^>]*?-->\s*', '', markup)
        rebuilt.append(f"<!-- Slide {i}: {clean} -->\n{markup}")

    def as_clone(markup: str, note: str) -> str:
        body = re.sub(r'^<!--[^>]*?-->\s*', '', markup)
        body = body.replace('<article class="exploreSlide"',
                            '<article aria-hidden="true" class="exploreSlide" data-clone="true"', 1)
        return f"<!-- {note} -->\n{body}"

    deck = ([as_clone(rebuilt[-1], f"Clone of Slide {len(rebuilt)} (left peek on Slide 1)")]
            + rebuilt
            + [as_clone(rebuilt[0], f"Clone of Slide 1 (right peek on Slide {len(rebuilt)})")])

    return text[:matches[0].start()] + "\n".join(deck) + text[matches[-1].end():]


def retarget(text: str) -> str:
    # 1. Remove whole slides whose subject has no canonical counterpart.
    #
    # THE GUARD IS THE IMPORTANT PART, and it was missing. This step selects slides by
    # POSITION, and step 7 renumbers the survivors 1..N -- so on a deck that had already been
    # retargeted, a different slide occupied position 4 and was eaten. Run repeatedly, the
    # script walked the deck down 7 -> 5 -> 4 -> 3 and then went quiet, because with three
    # slides left there is no position 4 to match. That is why it LOOKED idempotent when
    # measured afterwards: it had already reached its fixed point by destroying the deck.
    #
    # Measured cost: `Cost and Emissions` and `Waiting Times` were deleted from
    # site/www/dashboard.html between 8e3cfb3 and a858ec7, taking LifecycleCostbyHorizon,
    # NetCO2ebyHorizon and PeakWaitsbySite off the public site. The owner noticed the carousel
    # had shrunk; no gate did.
    #
    # A slide that no longer references OLD_WORKBOOK has already been processed. Requiring that
    # reference makes the step a no-op on its own output, which is what idempotent means.
    for num in DELETE_SLIDES:
        pattern = re.compile(
            r'\n?<!--\s*Slide[^>]*?-->\s*<article class="exploreSlide" data-slide="' + num + r'">.*?</article>',
            re.S)
        match = pattern.search(text)
        if match and OLD_WORKBOOK in match.group(0):
            text = text[:match.start()] + text[match.end():]

    # 2. Remove orphaned chips inside surviving slides.
    for sheet in DELETE_CHIP_SHEETS:
        text = re.sub(r'<button[^>]*data-url="[^"]*' + re.escape(sheet) + r'[^"]*"[^>]*>[^<]*</button>\s*',
                      "", text)

    # 3. Retitle repurposed slides and their info bars.
    for old_title, new_title, info in RETITLE:
        text = text.replace(f'<h2 class="slideTitle">{old_title}</h2>',
                            f'<h2 class="slideTitle">{new_title}</h2>')
        text = text.replace(f'<span class="slideInfoText">{info}</span>', "")  # avoid duplicates

    # 4. Point every surviving reference at the canonical workbook and sheet.
    for old_sheet, (new_sheet, _label) in SHEET_MAP.items():
        text = text.replace(f"{OLD_WORKBOOK}/{old_sheet}", f"{NEW_WORKBOOK}/{new_sheet}")

    # 5. Rewrite chip copy so the words match the chart now behind them.
    for new_sheet, copy in CHIP_COPY.items():
        def fix(m, c=copy):
            btn = m.group(0)
            for attr, value in [("data-info", c["info"]), ("data-note", c["note"]),
                                ("data-tip", c["info"][:1].lower() + c["info"][1:]),
                                ("data-title", c["title"]), ("data-what", c["what"]),
                                ("data-why", c["why"])]:
                btn = re.sub(attr + r'="[^"]*"', f'{attr}="{value}"', btn)
            return re.sub(r'>([^<]*)</button>', f'>{c["label"]}</button>', btn)
        text = re.sub(r'<button[^>]*data-url="[^"]*' + re.escape(new_sheet) + r'[^"]*"[^>]*>[^<]*</button>',
                      fix, text)

    # 6. iframe titles carry the old chart names in their accessible name.
    for old_sheet, (new_sheet, label) in SHEET_MAP.items():
        text = re.sub(r'title="Tableau visualization: [^"]*"(?=[^>]*' + re.escape(new_sheet) + r')',
                      f'title="Tableau visualization: {label}"', text)

    for old, new in LITERAL_COPY:
        text = text.replace(old, new)

    # 7. Rebuild the deck deterministically.
    #
    #    Two earlier attempts patched numbers in place and both produced a wrong deck: the
    #    carousel's two clones carry their own `data-slide` and "Part N" markup, so any
    #    sequential renumbering that walks the document counts them as slides and shifts every
    #    real one. And because a clone is a copy of an entire slide's markup, deleting the slide
    #    it was cloned from leaves it displaying a chart that exists nowhere else.
    #
    #    So the deck is not patched, it is regenerated: take the real slides in order, number
    #    them 1..N, then derive both clones from the finished list. A clone cannot disagree with
    #    its source if it is produced from it.
    text = rebuild_deck(text)


    # 8. Counters that state how many views there are must state the truth.
    #
    #    Two were hard-coded: the carousel's "1 / 7" and the hero's "Planning views: 7". The
    #    deck's JS derives the *current* slide from the DOM but not the *total*, so after
    #    removing two slides the page cheerfully advertised seven views over five. Derived here
    #    rather than substituted, so the next change to the deck cannot leave them stale.
    real_count = len(re.findall(r'<article class="exploreSlide" data-slide="\d+">', text))
    if real_count:
        text = re.sub(r'(<div class="navCounter"><span class="slideNum">\d+</span>\s*/\s*)\d+(</div>)',
                      lambda m, n=real_count: f"{m.group(1)}{n}{m.group(2)}", text)
        text = re.sub(r'(<span class="statLabel">Planning views</span>\s*<strong class="statValue">)\d+(</strong>)',
                      lambda m, n=real_count: f"{m.group(1)}{n}{m.group(2)}", text, flags=re.S)

    # 9. Fewer charts means each one gets more room.
    text = text.replace("height: clamp(450px, 60vh, 650px)", "height: clamp(520px, 70vh, 820px)")
    text = text.replace("height: clamp(400px, 50vh, 550px)", "height: clamp(460px, 60vh, 640px)")
    return text


def main() -> int:
    changed = []
    for page in ["dashboard.html", "results.html"]:
        path = WWW / page
        if not path.is_file():
            continue
        before = path.read_text()
        after = retarget_results_chips(retarget(before))
        if after != before:
            path.write_text(after)
            changed.append(page)

    problems = []
    for page in ["dashboard.html", "results.html"]:
        path = WWW / page
        if not path.is_file():
            continue
        text = path.read_text()
        left = re.findall(OLD_WORKBOOK + r"/([A-Za-z0-9\-]+)", text)
        if left:
            problems.append(f"{page}: still references the DELETED workbook: {sorted(set(left))}")

    print(f"  retargeted: {', '.join(changed) if changed else 'nothing (already applied)'}")
    if problems:
        for p in problems:
            print(f"  PROBLEM {p}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
