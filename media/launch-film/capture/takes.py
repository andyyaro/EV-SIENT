"""The film's screen recordings, taken from the live sites frame by frame (see rec.py).

python3 -I capture/takes.py app      -> assets/rec/app-*.mp4 (+ .json with pointer and marks)
python3 -I capture/takes.py site     -> assets/rec/site-*.mp4

The planner takes run as one session, in order, so each picks up where the last one left the page:
upload, map, fill, run, results, report, assistant, offline. Everything shown is the invented
Example City sample; the assistant is asked one question about it.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rec import Rec, ROOT  # noqa: E402

SITE, APP = "https://futurecity.andyyaro.com", "https://app.futurecity.andyyaro.com"
CSV = ROOT.parent.parent / "platform" / "app" / "public" / "samples" / "example-city.csv"
DOWNLOADS = ROOT / "rec" / "downloads"
QUESTION = "Why does the top site rank first?"
QUESTION_A = "What drives Site A's score?"


def button(pg, name, scope="main"):
    return pg.locator(scope).get_by_role("button", name=name, exact=True).first


def wait_ready(loc, seconds=90):
    for _ in range(seconds * 4):
        if loc.count() and loc.is_visible() and loc.is_enabled() and loc.get_attribute("aria-disabled") != "true":
            return loc
        loc.page.wait_for_timeout(250)
    raise RuntimeError(f"not ready: {loc}")


def heading_y(pg, text, off=90):
    """The document scroll that puts a heading `off` px below the top."""
    return pg.evaluate("""([t, off]) => {
        const el = [...document.querySelectorAll('h1,h2,h3')].find(e => e.innerText.trim().startsWith(t));
        if (!el) return null;
        const max = document.scrollingElement.scrollHeight - innerHeight;
        return Math.max(0, Math.min(max, el.getBoundingClientRect().top + document.scrollingElement.scrollTop - off));
    }""", [text, off])


def into_view(r, loc, frames=30):
    """If a control is off screen, scroll the page (eased, recorded) so it sits in the lower part of the view."""
    b = loc.bounding_box()
    if b and (b["y"] < 60 or b["y"] + b["height"] > 1020):
        top = r.pg.evaluate("document.scrollingElement.scrollTop")
        r.scroll("doc", max(0, top + b["y"] - 700), frames)


def press(r, loc, frames=20, hold=4, after=10, name=None):
    """Move to a control (scrolling to it if needed), rest a beat, click it."""
    wait_ready(loc)
    into_view(r, loc)
    r.move_to(loc, frames)
    r.hold(hold)
    r.click(name=name, after=after)


# ---------------------------------------------------------------- the planner

def drag_file(r, pg, x, y, frames):
    """Carry the sample file to (x, y) the way the page sees a file dragged from the desktop: drag events
    with the real file on the drop zone once the pointer is over it, then a drop."""
    pg.evaluate("""text => {
        const dt = new DataTransfer();
        dt.items.add(new File([text], 'example-city.csv', {type: 'text/csv'}));
        window.__dt = dt;
    }""", CSV.read_text())
    fire = """([type, x, y]) => {
        const el = document.querySelector('.st-drop');
        const b = el.getBoundingClientRect();
        if (type !== 'drop' && !(x >= b.left && x <= b.right && y >= b.top && y <= b.bottom)) return false;
        el.dispatchEvent(new DragEvent(type, {bubbles: true, cancelable: true, clientX: x, clientY: y, dataTransfer: window.__dt}));
        return true;
    }"""
    r.mark("dragStart")
    x0, y0 = r.x, r.y
    from rec import hand
    entered = False
    for i in range(1, frames + 1):
        e = hand(i / frames)
        r.x, r.y = x0 + (x - x0) * e, y0 + (y - y0) * e
        pg.mouse.move(r.x, r.y)
        inside = pg.evaluate(fire, ["dragenter" if not entered else "dragover", r.x, r.y])
        if inside and not entered:
            entered = True
            r.mark("dragEnter")
        r.shot()
    r.hold(6)
    pg.evaluate(fire, ["drop", r.x, r.y])
    r.mark("drop")


def app_takes(pg):
    pg.goto(APP + "/", wait_until="networkidle")
    pg.wait_for_timeout(3000)

    # 1. Start a new project, then drop the spreadsheet in
    r = Rec(pg, "app-upload")
    r.x, r.y = 1500, 980
    pg.mouse.move(r.x, r.y)
    r.hold(10)
    press(r, button(pg, "Start a New Project"), frames=24, name="start")
    r.hold(20)
    r.x, r.y = 1960, 760
    drag_file(r, pg, 1130, 380, 30)
    r.until("!!document.querySelector('main') && [...document.querySelectorAll('main button')].some(b => b.innerText.includes('Continue to Map Columns') && !b.disabled && b.getAttribute('aria-disabled') !== 'true')", 300, after=24)
    r.finish()

    # 2. Map Columns: accept what was matched
    r = Rec(pg, "app-map", rate=r.rate)
    r.hold(4)
    press(r, button(pg, "Continue to Map Columns"), name="toMap", after=24)
    press(r, button(pg, "Accept All Matched"), frames=24, name="accept", after=30)
    press(r, button(pg, "Continue to Check"), name="toCheck", after=30)
    r.finish()

    # 3. Public Data: look up what public data could fill
    r = Rec(pg, "app-fill", rate=r.rate)
    r.hold(4)
    press(r, button(pg, "Continue to Public Data"), name="toFill", after=24)
    look = button(pg, "Look Up Public Data")
    if look.count():
        press(r, look, frames=22, name="lookUp", after=6)
        r.until("![...document.querySelectorAll('[role=progressbar], progress')].length && ![...document.querySelectorAll('main button')].some(b => b.innerText.includes('Look Up Public Data'))", 400, after=40)
    else:
        r.hold(40)
    r.finish()

    # 4. Run the model, in this browser, to the results
    r = Rec(pg, "app-run", rate=r.rate)
    r.hold(4)
    press(r, button(pg, "Continue to Run"), name="toRun", after=24)
    press(r, button(pg, "Run the Model"), frames=24, name="run", after=0)
    r.until("!!document.querySelector('button.rs-site')", 900, after=40)
    r.finish()

    # 5. Results: down the ranked table to rank 1, then why it scored that way
    r = Rec(pg, "app-results", rate=r.rate)
    r.hold(10)
    y = heading_y(pg, "Ranked Sites", 40)
    if y is not None:
        r.mark("toTable")
        r.scroll("doc", y, 40)
        r.hold(14)
    first = pg.locator("button.rs-site").first
    press(r, first, frames=22, name="pick", after=20)
    y = heading_y(pg, "Why This Score", 40)
    if y is not None:
        r.mark("toWhy")
        r.scroll("doc", y, 44)
    r.hold(50)
    r.finish()

    # 6. Report: download the accessible PDF
    r = Rec(pg, "app-report", rate=r.rate)
    r.hold(4)
    press(r, pg.locator("nav, aside").get_by_role("button", name="Report").first, frames=26, name="toReport", after=10)
    pdf = pg.locator("main").get_by_role("button", name="Download .pdf").first
    r.until("[...document.querySelectorAll('main button')].some(b => b.innerText.includes('Download .pdf') && !b.disabled)", 600, after=10)
    r.move_to(pdf, 26)
    r.hold(6)
    with pg.expect_download(timeout=180_000) as dl:
        r.click(name="download")
        r.until("[...document.querySelectorAll('[role=status]')].some(e => e.innerText.startsWith('Saved'))", 900, after=40)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    dl.value.save_as(DOWNLOADS / dl.value.suggested_filename)
    r.finish()

    # 7. Assistant: share the Example City results for this session and ask one question
    r = Rec(pg, "app-assistant", rate=r.rate)
    r.hold(4)
    press(r, pg.get_by_role("link", name="Assistant").first, frames=26, name="open", after=10)
    r.until("!!document.querySelector('.as-sheet') && !document.querySelector('.as-sheet').innerText.includes('Checking')", 300, after=12)
    review = pg.locator(".as-sheet").get_by_role("button", name="Review What Would Be Shared").first
    if review.count():
        press(r, review, frames=22, name="review", after=16)
        share = pg.locator(".as-sheet").get_by_role("button", name="Share for This Session").first
        if share.count() and share.is_enabled():
            press(r, share, frames=20, name="share", after=16)
        else:
            press(r, pg.locator(".as-sheet").get_by_role("button", name="Cancel").first, frames=20, after=10)
    press(r, pg.locator("#as-question"), frames=22, name="focus", after=4)
    r.type(QUESTION, frames_per_char=2)
    r.hold(6)
    r.mark("send")
    pg.keyboard.press("Enter")
    r.until("document.querySelectorAll('.as-turn--assistant').length > 0 && !document.querySelector('.as-turn[aria-busy]')", 1200, after=60)
    answer = pg.locator(".as-turn--assistant").last.inner_text()
    (ROOT / "rec" / "assistant-answer.txt").write_text(f"Q: {QUESTION}\n\n{answer}\n")
    r.finish()

    # 8. Offline: the connection drops; the assistant says so and the planner keeps working
    r = Rec(pg, "app-offline", rate=r.rate)
    r.hold(10)
    r.mark("offline")
    pg.context.set_offline(True)
    r.hold(60)
    press(r, pg.locator(".as-sheet").get_by_role("button", name="Done").first, frames=22, name="done", after=20)
    press(r, pg.locator("nav, aside").get_by_role("button", name="Explore").first, frames=26, name="explore", after=60)
    pg.context.set_offline(False)
    r.finish()


# ---------------------------------------------------------------- the assistant, on the results

SHEET = ".as-sheet__body"
SETTLED = "document.getAnimations().every(a => a.playState !== 'running')"


def sheet_into_view(r, loc, frames=26):
    """Scroll the assistant sheet (its own scroller, recorded) so a control in it is in view."""
    b, box = loc.bounding_box(), r.pg.locator(SHEET).bounding_box()
    if b["y"] + b["height"] > box["y"] + box["height"] - 20 or b["y"] < box["y"]:
        top = r.pg.evaluate(f"document.querySelector({SHEET!r}).scrollTop")
        r.scroll(SHEET, max(0, top + b["y"] - box["y"] - box["height"] * 0.55), frames)


def to_results(pg):
    """The Example City sample run to its results, unrecorded."""
    pg.goto(APP + "/", wait_until="networkidle")
    pg.wait_for_timeout(2500)
    pg.get_by_text("Try the Example City Sample").first.click()
    for name in ["Continue to Map Columns", "Accept All Matched", "Continue to Check", "Continue to Public Data", "Continue to Run", "Run the Model"]:
        wait_ready(button(pg, name)).click()
        pg.wait_for_timeout(1500)
    pg.wait_for_function("!!document.querySelector('button.rs-site')", timeout=180_000)
    pg.wait_for_timeout(2500)


def assistant_take(pg):
    to_results(pg)
    r = Rec(pg, "app-assistant")
    r.x, r.y = 1300, 900
    pg.mouse.move(r.x, r.y)
    r.hold(8)
    press(r, pg.get_by_role("link", name="Assistant").first, frames=26, name="open", after=8)
    r.until("!!document.querySelector('.as-sheet') && document.querySelector('.as-sheet').innerText.includes('Available')", 300, after=4)
    r.until(SETTLED, 300, after=6)
    sheet = pg.locator(".as-sheet")
    press(r, sheet.get_by_role("button", name="Review What Would Be Shared").first, frames=22, name="review", after=6)
    r.until(SETTLED, 300, after=6)
    # share rank 1's breakdown, sent as Site A (its name stays on this device)
    one = sheet.locator("label", has_text="One site's score breakdown").first
    press(r, one, frames=20, name="site", after=6)
    r.until(SETTLED, 300, after=4)
    pick = sheet.locator("select").first
    pick.wait_for()
    sheet_into_view(r, pick)
    r.move_to(pick, 18)
    r.hold(4)
    first = pg.evaluate("[...document.querySelectorAll('.as-sheet select option')].map(o => [o.value, o.textContent]).filter(o => o[0])[0]")
    pick.select_option(first[0])
    r.mark("picked")
    r.until("!document.querySelector('.as-sheet [role=alert]') && !!document.querySelector('.as-preview') && document.querySelector('.as-preview').innerText.includes('Site A')", 300, after=10)
    share = sheet.get_by_role("button", name="Share for This Session").first
    sheet_into_view(r, share)
    press(r, share, frames=20, name="share", after=14)
    ask = pg.locator("#as-question")
    press(r, ask, frames=22, name="focus", after=4)
    r.type(QUESTION_A, frames_per_char=2)
    r.hold(6)
    r.mark("send")
    pg.keyboard.press("Enter")
    # follow the answer down the sheet as it streams in
    for _ in range(1500):
        done = pg.evaluate("document.querySelectorAll('.as-turn--assistant').length > 0 && !document.querySelector('.as-turn[aria-busy]')")
        pg.evaluate(f"(() => {{ const b = document.querySelector({SHEET!r}); b.scrollTop = b.scrollHeight; }})()")
        r.shot()
        if done:
            break
    r.mark("answered")
    r.hold(60)
    answer = pg.locator(".as-turn--assistant").last.inner_text()
    (ROOT / "rec" / "assistant-answer.txt").write_text(f"Site A = {first[1]}\nQ: {QUESTION_A}\n\n{answer}\n")
    r.finish()


# ---------------------------------------------------------------- the study site

def site_takes(pg):
    pg.goto(SITE + "/", wait_until="networkidle")
    pg.wait_for_timeout(2500)
    r = Rec(pg, "site-overview")
    r.x, r.y = 1500, 1000
    pg.mouse.move(r.x, r.y)
    r.hold(30)
    y = heading_y(pg, "Top candidates", 60)
    r.mark("toTop")
    r.scroll("doc", y, 60)
    r.hold(20)
    row = pg.locator("#top-title").locator("xpath=ancestor::section[1]").locator("tr, li, a").first
    if row.count():
        r.move_to(row, 26)
    r.hold(40)
    r.finish()

    pg.goto(SITE + "/compare.html", wait_until="networkidle")
    pg.wait_for_timeout(2500)
    r = Rec(pg, "site-compare", rate=r.rate)
    r.x, r.y = 1500, 1000
    pg.mouse.move(r.x, r.y)
    r.hold(20)
    r.mark("toChart")
    r.scroll("doc", heading_y(pg, "Side by Side", 40), 44)
    r.hold(40)
    r.mark("toParts")
    r.scroll("doc", heading_y(pg, "Where Each Score Comes From", 40), 50)
    r.hold(20)
    rows = pg.locator("#breakdown-title").locator("xpath=ancestor::section[1]").locator("tbody tr")
    for i in range(min(3, rows.count())):
        r.move_to(rows.nth(i), 18, dx=-200)
        r.hold(10)
    r.hold(30)
    r.finish()


if __name__ == "__main__":
    which = sys.argv[1:] or ["app", "site"]
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2, color_scheme="light",
                            accept_downloads=True)
        pg = ctx.new_page()
        if "app" in which:
            app_takes(pg)
        if "site" in which:
            site_takes(pg)
        if "assistant" in which:
            assistant_take(pg)
        b.close()
