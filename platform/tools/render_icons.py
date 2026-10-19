"""Render the planner's install icons from platform/app/public/icon.svg with Chromium (Playwright).

Writes platform/app/public/icons/:

  icon-192.png, icon-512.png   the icon as drawn, rounded corners and all ("any" in the manifest)
  icon-maskable-512.png        full bleed, for launchers that cut their own shape ("maskable");
                               the bolt already sits inside the central 80% safe zone
  apple-touch-icon.png         180 px, full bleed, because iOS rounds the corners itself

Run it again after changing icon.svg, and commit the PNGs.

Usage: python3 platform/tools/render_icons.py
"""

from __future__ import annotations

import re
from pathlib import Path

from playwright.sync_api import sync_playwright

APP = Path(__file__).resolve().parents[1] / "app"
SVG = (APP / "public/icon.svg").read_text()
OUT = APP / "public/icons"

# Full bleed: the background rectangle loses its corner radius.
FULL_BLEED = re.sub(r'(<rect [^>]*?)\s+rx="[^"]*"', r"\1", SVG, count=1)
if FULL_BLEED == SVG:
    raise SystemExit("icon.svg no longer has a rounded background rect; update render_icons.py")

ICONS = [("icon-192.png", 192, SVG), ("icon-512.png", 512, SVG),
         ("icon-maskable-512.png", 512, FULL_BLEED), ("apple-touch-icon.png", 180, FULL_BLEED)]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, size, svg in ICONS:
            page = browser.new_page(viewport={"width": size, "height": size})
            sized = svg.replace("<svg ", f'<svg width="{size}" height="{size}" ', 1)
            page.set_content(f"<html><body style='margin:0;background:transparent'>{sized}</body></html>")
            page.screenshot(path=str(OUT / name), omit_background=True,
                            clip={"x": 0, "y": 0, "width": size, "height": size})
            page.close()
            print(f"{name}: {size} x {size}, {(OUT / name).stat().st_size} bytes")
        browser.close()


if __name__ == "__main__":
    main()
