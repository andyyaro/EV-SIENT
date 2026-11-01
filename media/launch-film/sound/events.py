"""Read the composition's event list (window.__sfx) in a headless browser -> sound/events.json.

    python3 -I sound/events.py
"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto((ROOT / "index.html").as_uri())
    pg.wait_for_function("window.__sfx !== undefined")
    ev = pg.evaluate("window.__sfx")
    b.close()
(ROOT / "sound" / "events.json").write_text(json.dumps(ev, indent=1))
print(json.dumps(ev)[:400])
