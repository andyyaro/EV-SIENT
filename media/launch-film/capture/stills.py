"""Final stills for the film: 1920x1080 viewports at 2x (3840x2160), light theme, from the live sites.

python3 capture/stills.py            -> shots/*.png
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "shots"
SITE, APP = "https://futurecity.andyyaro.com", "https://app.futurecity.andyyaro.com"

def shoot(pg, name):
    pg.wait_for_timeout(900)
    pg.screenshot(path=str(OUT / f"{name}.png"))
    print("shot", name)

def scroll_to_text(pg, text, offset=90):
    pg.evaluate("""([t, off]) => {
        const el = [...document.querySelectorAll('h1,h2,h3')].find(e => e.innerText.trim().startsWith(t));
        const scroller = [document.scrollingElement, ...document.querySelectorAll('main, [class*=scroll]')]
            .find(s => s && s.scrollHeight > s.clientHeight + 10) || document.scrollingElement;
        const y = el.getBoundingClientRect().top + scroller.scrollTop - off;
        scroller.scrollTo(0, y); window.scrollTo(0, y);
    }""", [text, offset])

def go(pg, name):
    btn = pg.locator("main").get_by_role("button", name=name, exact=True).first
    for _ in range(90):
        if btn.count() and btn.get_attribute("aria-disabled") != "true" and btn.is_enabled():
            break
        pg.wait_for_timeout(1000)
    btn.click(); pg.wait_for_timeout(4000)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2, color_scheme="light")
    pg = ctx.new_page()
    # Public site
    pg.goto(SITE + "/", wait_until="networkidle"); pg.wait_for_timeout(1500)
    shoot(pg, "site-overview")
    scroll_to_text(pg, "Top candidates", 60); shoot(pg, "site-candidates")
    pg.goto(SITE + "/compare.html", wait_until="networkidle"); pg.wait_for_timeout(1500)
    scroll_to_text(pg, "Side by Side", 40); shoot(pg, "site-compare-chart")
    scroll_to_text(pg, "Where Each Score Comes From", 40); shoot(pg, "site-compare-parts")
    pg.goto(SITE + "/method.html", wait_until="networkidle"); pg.wait_for_timeout(1500)
    shoot(pg, "site-method")
    # Planner
    pg.goto(APP + "/", wait_until="networkidle"); pg.wait_for_timeout(2500)
    shoot(pg, "app-start")
    pg.get_by_text("Try the Example City Sample").click(); pg.wait_for_timeout(3000)
    shoot(pg, "app-upload")
    go(pg, "Continue to Map Columns"); shoot(pg, "app-map-columns")
    pg.get_by_role("button", name="Accept All Matched").first.click(); pg.wait_for_timeout(1200)
    shoot(pg, "app-map-columns-accepted")
    go(pg, "Continue to Check"); shoot(pg, "app-check")
    go(pg, "Continue to Public Data"); shoot(pg, "app-public-data")
    go(pg, "Continue to Run"); shoot(pg, "app-run")
    go(pg, "Run the Model"); pg.wait_for_timeout(2000); shoot(pg, "app-results")
    pg.get_by_role("button", name="Show Map").first.click(); pg.wait_for_timeout(9000)
    scroll_to_text(pg, "Ranked Sites", 40); pg.wait_for_timeout(4000); shoot(pg, "app-results-map")
    scroll_to_text(pg, "Why This Score", 40); shoot(pg, "app-why")
    scroll_to_text(pg, "How Stable Is This Rank", 40); shoot(pg, "app-stable")
    pg.locator("nav, aside").get_by_role("button", name="Explore").first.click(); pg.wait_for_timeout(5000)
    shoot(pg, "app-explore")
    pg.locator("nav, aside").get_by_role("button", name="Report").first.click(); pg.wait_for_timeout(6000)
    shoot(pg, "app-report")
    pg.get_by_role("link", name="Assistant").first.click(); pg.wait_for_timeout(3000)
    shoot(pg, "app-assistant")
    b.close()
