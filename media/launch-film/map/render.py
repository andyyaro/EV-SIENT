"""Render the hook's map flight (map/flight.html) frame by frame.

python3 -I map/render.py                 -> assets/map/hook.mp4, assets/map/hook.json (site positions per frame)
python3 -I map/render.py 0 240 30        -> only every 30th frame of 0..240, to map/test/ (a look at the path)
"""
from __future__ import annotations

import functools
import http.server
import json
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FRAMES = ROOT / "map" / "frames"
TAIL = 0.45   # seconds rendered past the cut, for the crossfade into the brand


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=str(ROOT))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main():
    test = len(sys.argv) > 1
    srv = serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}/map/flight.html"
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        pg.on("console", lambda m: m.type in ("error", "warning") and print("console:", m.text))
        pg.goto(url)
        pg.wait_for_function("window.mapReady === true", timeout=120_000)
        timing = pg.evaluate("window.timing")
        print("timing", timing, "renderer", pg.evaluate("(() => { const g = document.createElement('canvas').getContext('webgl2'); const d = g.getExtension('WEBGL_debug_renderer_info'); return d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : '?'; })()"))
        last = int(round((timing["END"] + TAIL) * 30))
        if test:
            a, z, step = (int(x) for x in sys.argv[1:4])
            frames, out = list(range(a, min(z, last) + 1, step)), ROOT / "map" / "test"
        else:
            frames, out = list(range(0, last + 1)), FRAMES
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        acc = pg.locator("#acc")
        info, t0 = [], time.perf_counter()
        for f in frames:
            r = pg.evaluate("f => window.renderFrame(f)", f)
            acc.screenshot(path=str(out / f"{f:04d}.png"))
            info.append(r)
            if f % 15 == 0 or test:
                xy = [(x, y) for _, x, y in r["sites"]]
                box = f"x {min(x for x, _ in xy):.0f}-{max(x for x, _ in xy):.0f} y {min(y for _, y in xy):.0f}-{max(y for _, y in xy):.0f}"
                print(f"frame {f} t={r['t']:.2f} sub={r['sub']} zoom={r['zoom']:.2f} sites {box}  {time.perf_counter() - t0:.0f}s", flush=True)
        b.close()
    srv.shutdown()
    if test:
        return
    dst = ROOT / "assets" / "map"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / "hook.json").write_text(json.dumps({"fps": 30, "timing": timing, "frames": info}))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", str(FRAMES / "%04d.png"),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    str(dst / "hook.mp4")], check=True)
    print("wrote", dst / "hook.mp4", len(info), "frames")


if __name__ == "__main__":
    main()
