"""Frame-by-frame screen recorder for the live sites: every frame is the real page, rendered by Chromium at
1920×1080 CSS px and 2× density (3840×2160), captured in sequence.

Why not a screen recording: a real-time capture of a 4K page runs at a handful of frames per second and
judders. Here each frame is taken on purpose: scrolling and pointer moves are set per frame (eased, so
they read as a hand), and the page's own CSS animations are slowed by the same factor the capture is slow,
so transitions play at their true speed in the 30 fps result. Work the page does on its own (the model run,
the assistant's answer, map tiles) runs in real time while frames are taken.

The pointer is not in the screenshots; its position per frame is written to meta.json and the film draws
it, so it moves exactly as the page saw it move.
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REC = ROOT / "rec"
FPS = 30


def eio(p: float) -> float:
    """The film's EIO: exponential in, exponential out."""
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    ei = lambda q: 0.0 if q <= 0 else 2 ** (10 * (q - 1))
    eo = lambda q: 1.0 if q >= 1 else 1 - 2 ** (-10 * q)
    return ei(2 * p) / 2 if p < 0.5 else (1 + eo(2 * p - 1)) / 2


def hand(p: float) -> float:
    """A pointer move: quick start, long settle (minimum-jerk), as a hand moves a mouse."""
    p = min(1.0, max(0.0, p))
    return p ** 3 * (10 - 15 * p + 6 * p * p)


class Rec:
    def __init__(self, page, name: str, rate: float | None = None):
        self.pg = page
        self.name = name
        self.dir = REC / name
        if self.dir.exists():
            shutil.rmtree(self.dir)
        (self.dir / "f").mkdir(parents=True)
        self.n = 0
        self.cur = []          # [x, y, pressed] per frame, CSS px
        self.marks = {}        # name -> frame
        self.x, self.y, self.down = 960.0, 1180.0, False
        self.cdp = page.context.new_cdp_session(page)
        self.cdp.send("Animation.enable")
        self.t_last = None
        self.rate = rate
        if rate is None:
            # measure how long one frame takes, and slow the page's animations to match
            t0 = time.perf_counter()
            for _ in range(3):
                page.screenshot(type="jpeg", quality=90)
            dt = (time.perf_counter() - t0) / 3
            self.rate = max(0.05, min(1.0, (1 / FPS) / dt))
        self.cdp.send("Animation.setPlaybackRate", {"playbackRate": self.rate})

    # ---------- primitives ----------
    def shot(self):
        self.pg.screenshot(path=str(self.dir / "f" / f"{self.n:05d}.jpg"), type="jpeg", quality=92)
        self.cur.append([round(self.x, 1), round(self.y, 1), 1 if self.down else 0])
        self.n += 1

    def mark(self, name: str):
        self.marks[name] = self.n

    def hold(self, frames: int):
        for _ in range(frames):
            self.shot()

    def move(self, x: float, y: float, frames: int, curve=hand):
        x0, y0 = self.x, self.y
        for i in range(1, frames + 1):
            e = curve(i / frames)
            # a slight arc, as a wrist moves
            arc = math.sin(math.pi * e) * min(40.0, math.hypot(x - x0, y - y0) * 0.08)
            self.x, self.y = x0 + (x - x0) * e, y0 + (y - y0) * e - arc
            self.pg.mouse.move(self.x, self.y)
            self.shot()

    def move_to(self, locator, frames: int, dx: float = 0, dy: float = 0):
        b = locator.bounding_box()
        self.move(b["x"] + b["width"] / 2 + dx, b["y"] + b["height"] / 2 + dy, frames)

    def click(self, hold_frames: int = 3, after: int = 0, name: str | None = None):
        self.pg.mouse.move(self.x, self.y)
        self.down = True
        self.pg.mouse.down()
        if name:
            self.mark(name)
        self.hold(hold_frames)
        self.pg.mouse.up()
        self.down = False
        self.hold(after)

    def scroll(self, scroller: str, to_y: float, frames: int, curve=eio):
        """Scroll an element (a CSS selector, or 'doc' for the page) to to_y over frames, eased."""
        js_get = "document.scrollingElement.scrollTop" if scroller == "doc" else f"document.querySelector({json.dumps(scroller)}).scrollTop"
        y0 = self.pg.evaluate(js_get)
        for i in range(1, frames + 1):
            y = y0 + (to_y - y0) * curve(i / frames)
            if scroller == "doc":
                self.pg.evaluate("y => document.scrollingElement.scrollTo({top: y, behavior: 'instant'})", y)
            else:
                self.pg.evaluate("([s, y]) => { document.querySelector(s).scrollTop = y; }", [scroller, y])
            self.shot()

    def type(self, text: str, frames_per_char: int = 2):
        for ch in text:
            self.pg.keyboard.type(ch)
            self.mark_list("keys")
            self.hold(frames_per_char)

    def mark_list(self, name: str):
        self.marks.setdefault(name, [])
        if isinstance(self.marks[name], list):
            self.marks[name].append(self.n)

    def until(self, js: str, max_frames: int = 600, after: int = 0):
        """Keep taking frames until a condition holds in the page (work that runs in real time)."""
        for _ in range(max_frames):
            if self.pg.evaluate(js):
                break
            self.shot()
        else:
            raise RuntimeError(f"{self.name}: timed out waiting for {js}")
        self.hold(after)

    # ---------- output ----------
    def finish(self, crf: int = 16, width: int = 2880):
        meta = {"name": self.name, "fps": FPS, "frames": self.n, "duration": round(self.n / FPS, 3),
                "size": [1920, 1080], "animationRate": round(self.rate, 3), "cursor": self.cur, "marks": self.marks}
        (self.dir / "meta.json").write_text(json.dumps(meta))
        out = ROOT / "assets" / "rec" / f"{self.name}.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(self.dir / "f" / "%05d.jpg"),
                        "-vf", f"scale={width}:-2:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(out)], check=True)
        (ROOT / "assets" / "rec" / f"{self.name}.json").write_text(json.dumps(meta))
        print(f"{self.name}: {self.n} frames ({self.n / FPS:.2f}s), animation rate {self.rate:.3f}, marks {self.marks}")
        return meta
