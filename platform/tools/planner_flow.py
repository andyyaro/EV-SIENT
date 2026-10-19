"""Drive the EV-SIENT Planner through its screens with Playwright, for the QA scripts.

Shared by matrix.py (device matrix) and a11y_audit.py (axe-core, contrast, keyboard). It walks
Start -> Upload (Example City sample) -> Map Columns -> Check -> Run -> Results -> Report once per
page, then moves between the screens through the app's own history handling, so each screen can be
shown again at any window size without running the model again.

Not a test of the engine's numbers: platform/tools/parity.mjs and browser_check.py do that.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

SCREENS = ["start", "upload", "map", "check", "run", "results", "compare", "report"]

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
    accept = page.get_by_role("button", name="Accept All Matched", exact=True)
    if accept.count():
        accept.first.click()
    page.get_by_role("button", name="Continue to Check", exact=True).click()
    _wait_h1(page, "Check")
    page.locator(".st-coverage").wait_for(timeout=BOOT_TIMEOUT_MS)

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
        _wait_h1(page, {"start": "Rank Your", "upload": "Upload", "map": "Map Columns", "check": "Check",
                        "run": "Run", "results": "Results", "report": "Report"}[screen])
        page.evaluate("() => window.scrollTo(0, 0)")
    if screen == "report":
        page.locator(".rp-sheet .rp").first.wait_for(timeout=60_000)
    settle(page)
