"""Drive the EV-SIENT Planner through its screens with Playwright, for the QA scripts.

Shared by matrix.py (device matrix) and a11y_audit.py (axe-core, contrast, keyboard). It walks
Start -> Upload (Example City sample) -> Map Columns -> Check -> Public Data -> Run -> Results ->
Report once per page (leaving the sample's Fleet column unmatched, so Results has one of Your
Columns to show), then moves between the screens through the app's own history handling, so
each screen can be shown again at any window size without running the model again.

Not a test of the engine's numbers: platform/tools/parity.mjs and browser_check.py do that.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

SCREENS = ["start", "upload", "map", "check", "fill", "run", "results", "compare", "explore", "report"]

# The live engine boots Pyodide and runs the model; give it room on a cold, slow machine.
BOOT_TIMEOUT_MS = 240_000


@dataclass
class Watch:
    """Console errors, page errors and every request that leaves the app's own origin."""

    origin: str
    errors: list[str] = field(default_factory=list)
    offsite: list[str] = field(default_factory=list)

    def attach(self, page) -> None:
        page.on("console", lambda m: self.errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: self.errors.append(f"pageerror: {e}"))

        def on_request(r) -> None:
            url = r.url
            if url.startswith(("data:", "blob:", "about:")) or url.startswith(self.origin):
                return
            self.offsite.append(url)

        page.on("request", on_request)


def app_url(base: str, mock: bool) -> str:
    return base.rstrip("/") + "/" + ("?engine=mock" if mock else "")


def _wait_h1(page, text: str, timeout: int = 30_000) -> None:
    page.locator("#main h1", has_text=text).first.wait_for(timeout=timeout)


def go(page, step: str) -> None:
    """Show a step the planner has already opened, as the Back button would."""
    page.evaluate(
        """(step) => { history.pushState(null, '', '#/' + step); dispatchEvent(new PopStateEvent('popstate')); }""",
        step,
    )
    page.wait_for_timeout(150)


def settle(page, ms: int = 250) -> None:
    page.evaluate("() => document.fonts && document.fonts.ready")
    page.wait_for_timeout(ms)


def run_flow(page, base: str, mock: bool) -> dict:
    """Walk the whole flow once. Returns timings in seconds."""
    t0 = time.time()
    page.goto(app_url(base, mock))
    _wait_h1(page, "Rank Your Candidate Charging Sites")
    # The model loads on the Start screen; wait for it so later steps do not race the boot.
    page.locator(".st-engine__body", has_text="Ready.").wait_for(timeout=BOOT_TIMEOUT_MS)
    boot = time.time() - t0

    page.get_by_role("button", name="Try the Example City Sample", exact=True).click()
    _wait_h1(page, "Upload")
    page.locator("#found-title").wait_for(timeout=BOOT_TIMEOUT_MS)

    page.get_by_role("button", name="Continue to Map Columns", exact=True).click()
    _wait_h1(page, "Map Columns")
    # Fleet is read but not scored; left unmatched, it is carried as one of Your Columns.
    show_all = page.locator('button[aria-controls="grp-matched-list"]', has_text="Show All")
    if show_all.count():
        show_all.click()
    page.locator("#col-fleet_vehicles").select_option("")
    page.locator(".st-map-row--unmatched#field-fleet_vehicles").wait_for(timeout=60_000)
    accept = page.get_by_role("button", name="Accept All Matched", exact=True)
    if accept.count():
        accept.first.click()
    page.get_by_role("button", name="Continue to Check", exact=True).click()
    _wait_h1(page, "Check")
    page.locator(".st-coverage").wait_for(timeout=BOOT_TIMEOUT_MS)

    # Example City lacks a field public data could fill, so Check leads to Public Data. The flow
    # does not look anything up there (the sample is outside the hub's coverage).
    page.get_by_role("button", name="Continue to Public Data", exact=True).click()
    _wait_h1(page, "Public Data")
    page.get_by_role("button", name="Continue to Run", exact=True).click()
    _wait_h1(page, "Run")
    t1 = time.time()
    page.get_by_role("button", name="Run the Model", exact=True).click()
    _wait_h1(page, "Results", timeout=BOOT_TIMEOUT_MS)
    run = time.time() - t1

    # A site selected (the second, so the selection is the planner's) and two sites in Compare.
    page.locator(".rs-ranked button.rs-site").nth(1).click()
    boxes = page.locator(".rs-ranked .rs-check input")
    boxes.nth(0).check()
    boxes.nth(1).check()
    page.locator(".rs-compare").wait_for()
    # Fleet added to the ranked table from Your Columns, and the control closed again.
    toggle = page.locator(".rs-yours__toggle")
    toggle.click()
    page.locator(".rs-yours__option", has_text="Fleet").locator("input").check()
    toggle.click()
    page.locator("th.rs-col-yours").first.wait_for()
    page.locator(".sd-card .ex__sentence, .sd-card .sd-error").first.wait_for(timeout=60_000)

    go(page, "report")
    _wait_h1(page, "Report")
    page.locator(".rp-sheet .rp").first.wait_for(timeout=120_000)
    return {"boot_s": round(boot, 1), "run_s": round(run, 1)}


def show(page, screen: str) -> None:
    """Show one screen of a session run_flow has already walked."""
    if screen == "compare":
        go(page, "results")
        _wait_h1(page, "Results")
        page.locator("#rs-compare-title").scroll_into_view_if_needed()
    else:
        go(page, screen)
        _wait_h1(page, {"start": "Rank Your", "upload": "Upload", "map": "Map Columns", "check": "Check", "fill": "Public Data",
                        "run": "Run", "results": "Results", "explore": "Explore", "report": "Report"}[screen])
        page.evaluate("() => window.scrollTo(0, 0)")
    if screen == "report":
        page.locator(".rp-sheet .rp").first.wait_for(timeout=60_000)
    if screen == "explore":
        # The first visit runs the scan; the stand-in engine shows its explanation instead.
        page.locator('[data-explore-state="done"], [data-explore-state="unavailable"], [data-explore-state="error"]').first.wait_for(
            timeout=BOOT_TIMEOUT_MS)
    settle(page)
