"""Closed captions for the film as WebVTT: every narrated line, including the ones the film shows as titles.

python3 -I tools/captions.py   -> deploy/film/ev-sient-launch.vtt
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = json.loads((ROOT / "assets" / "cues.js").read_text().strip().removeprefix("window.CUES = ").rstrip(";"))
Wd = C["words"]


def W(k, i):
    return Wd[k][i][1]


cues = [(0.0, 1.0, "[Upbeat funk music, a city at night]"),
        (W("01-hook", 0), W("01-hook", 6) - 0.05, "Every city wants more EV chargers."),
        (W("01-hook", 6), C["vo"]["02-brand"] - 0.4, "Few can show where the first ones should go, and why."),
        (C["vo"]["02-brand"], C["vo"]["03-study"] - 0.1, "This is EV-SIENT."),
        *[tuple(c) for c in C["caps"] if c[0] < C["vo"]["05-yours"]],
        (W("05-yours", 0), W("05-yours", 4) - 0.05, "Now it's your turn."),
        *[tuple(c) for c in C["caps"] if c[0] >= C["vo"]["05-yours"]],
        (W("08-cta", 0), W("08-cta", 3) - 0.05, "EV-SIENT."),
        (W("08-cta", 3), W("08-cta", 10) - 0.05, "Plan smarter charging with your own data."),
        (W("08-cta", 10), W("08-cta", 12) + 0.9, "Try it free today.")]


def ts(t):
    return f"{int(t // 60):02d}:{t % 60:06.3f}"


out = ROOT / "deploy" / "film" / "ev-sient-launch.vtt"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("WEBVTT\n\n" + "\n".join(f"{ts(a)} --> {ts(b)}\n{t}\n" for a, b, t in cues))
print(out.relative_to(ROOT), len(cues), "cues")
