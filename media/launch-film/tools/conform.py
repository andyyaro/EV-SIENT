"""The edit: which recorded frame plays on each film frame, keyed to the narration.

python3 -I tools/conform.py      -> assets/shots/<shot>.mp4 and assets/edit.js (window.EDIT)

Each shot is a list of (film time, recording frame) keys; between keys the recording plays at whatever
speed joins them (a hold is two keys on one frame). Times come from narration words (assets/cues.js), so
moving a line moves its shot. The cut times live here too, snapped to the music's beats, and the film reads
them from window.EDIT: one timing table for picture, pointer and sound.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FPS = 30
WIDTH = 2880                     # the window shows a 1920 page at 0.75; pushes go to about 2.3x

C = json.loads((ROOT / "assets" / "cues.js").read_text().strip().removeprefix("window.CUES = ").rstrip(";"))
V = C["vo"]


def W(k, i):
    return C["words"][k][i][1]


def snap(t, tol=0.16):
    best, d = t, tol
    for b in C["beats"]:
        if abs(b - t) <= d:
            best, d = b, abs(b - t)
    return round(best, 3)


def fr(t):
    return round(t * FPS)


# ---------------------------------------------------------------- the cuts (film seconds)
WIN0 = V["03-study"] - 0.32                    # the window rises with the study site
CMP = snap(V["04-stable"] - 0.25)               # overview -> compare
OUT1 = V["05-yours"] - 0.62                     # the window falls away for "Now it's your turn"
L0 = W("05-yours", 4) - 0.35                    # the laptop rises (device/laptop.html uses the same)
L1 = V["06-device"] - 0.9                       # square on the screen
MC = snap(V["06-device"] - 0.25)                # upload -> map columns
RUN = snap(W("06-device", 5) - 0.15)            # map columns -> run
PRESS = W("06-device", 8)                       # "model": Run the Model is pressed
RES = 31.62                                     # run -> results: the same page, swapped without a cut
REP = snap(W("07-results", 10) - 0.15)          # results -> report
CLICK = W("07-results", 17) + 0.04              # "one click": Download .pdf
MORE = snap(V["07b-more"] - 0.1)                # report -> public data
ASK = snap(W("07b-more", 5) - 0.2)              # public data -> assistant
OFF = snap(W("07b-more", 11) + 0.2)             # assistant -> offline
END0 = V["08-cta"] - 0.62                       # everything falls back for the call to action

CUTS = dict(WIN0=WIN0, CMP=CMP, OUT1=OUT1, L0=L0, L1=L1, MC=MC, RUN=RUN, PRESS=PRESS, RES=RES, REP=REP, CLICK=CLICK,
            MORE=MORE, ASK=ASK, OFF=OFF, END0=END0)

# ---------------------------------------------------------------- the shots: (film s, recording frame) keys
TAIL = 0.35   # a shot runs on past its cut while it slides out
SHOTS = {
    "overview": ("site-overview", WIN0 - 0.05, CMP + TAIL, [
        (WIN0, 0), (W("03-study", 9), 29),                 # the top of the page, the 12-site tiles
        (W("03-study", 9) + 2.0, 89),                      # under the weights card: down to the top candidates
        (CMP + TAIL, 175)]),
    "compare": ("site-compare", CMP - 0.1, OUT1 + 0.45, [
        (CMP - 0.1, 40), (W("04-stable", 8) - 0.1, 104),   # the chart, while 2,000 counts up
        (W("04-stable", 8) + 1.55, 154),                   # down to where each score comes from
        (OUT1 + 0.45, 222)]),
    "upload": ("app-upload", L0 - 0.05, MC + TAIL, [
        (L0, 0), (L0 + 131 / 48, 131),                     # 1.6x: Start a New Project, the file dropped in
        (MC + TAIL, 131)]),
    "mapcols": ("app-map", MC - 0.1, RUN + TAIL, [
        (MC - 0.1, 62), (W("06-device", 4), 113),          # "columns": Accept All Matched
        (RUN + TAIL, 140)]),
    "run": ("app-run", RUN - 0.1, RES + 0.05, [
        (RUN - 0.1, 113 - round((PRESS - RUN + 0.1) * FPS)), (PRESS, 113),   # the pointer at its own pace
        (PRESS + 0.15, 115), (PRESS + 0.25, 116), (PRESS + 0.6, 116),       # Step 1 of 2: preparing the sites
        (PRESS + 0.7, 117), (RES - 0.5, 117), (RES - 0.4, 118),             # Step 2 of 2: running the model
        (RES + 0.05, 118)]),                                                # (119 is a blank "Loading" frame: never shown)
    "results": ("app-results", RES, REP + TAIL, [
        (RES, 0), (V["07-results"] - 0.05, 8),             # results stay up through "never leaves your device"
        (W("07-results", 3) + 0.1, 50),                    # "ranked,": down to the ranked table
        (W("07-results", 3) + 0.2, 64),
        (W("07-results", 5), 90),                          # "why": rank 1 chosen
        (W("07-results", 9) + 0.15, 157),                  # down to Why This Score
        (REP + TAIL, 175)]),
    "report": ("app-report", REP - 0.1, MORE + TAIL, [
        (REP - 0.1, 14), (REP + 0.5, 34),                  # Report, in the sidebar
        (CLICK, 89),                                       # "one click": Download .pdf
        (CLICK + 1.5, 134), (MORE + TAIL, 136)]),
    "fill": ("app-fill", MORE - 0.1, ASK + TAIL, [
        (MORE - 0.1, 62), (W("07b-more", 4), 111),         # "data,": Look Up Public Data
        (ASK + TAIL, 118)]),                               # (the lookup's result is not shown: Example City is invented)
    "assistant": ("app-assistant", ASK - 0.1, OFF + TAIL, [
        (ASK - 0.1, 296), (W("07b-more", 9) + 0.1, 360),   # the question typed and sent
        (OFF + TAIL, 374)]),                               # "Writing": the cut comes before the answer
    "offline": ("app-offline", OFF - 0.1, END0 + 0.45, [
        (OFF - 0.1, 0), (W("07b-more", 14) - 0.15, 9),     # "offline": the connection drops
        (END0 + 0.45, 9 + round((END0 + 0.6 - W("07b-more", 14)) * FPS))]),
}


def frame_at(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, f0), (t1, f1) in zip(keys, keys[1:]):
        if t <= t1:
            return round(f0 + (f1 - f0) * (t - t0) / (t1 - t0))
    return keys[-1][1]


def conform(name, take, start, end, keys):
    meta = json.loads((ROOT / "rec" / take / "meta.json").read_text())
    n = meta["frames"]
    f0, f1 = fr(start), fr(end)
    src = [min(n - 1, max(0, frame_at(keys, f / FPS))) for f in range(f0, f1 + 1)]
    out = ROOT / "assets" / "shots" / f"{name}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as lst:
        for k in src:
            lst.write(f"file '{ROOT / 'rec' / take / 'f' / f'{k:05d}.jpg'}'\nduration {1 / FPS:.6f}\n")
        lst.write(f"file '{ROOT / 'rec' / take / 'f' / f'{src[-1]:05d}.jpg'}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst.name,
                    "-vf", f"scale={WIDTH}:-2:flags=lanczos,fps={FPS}", "-frames:v", str(len(src)),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    str(out)], check=True)
    Path(lst.name).unlink()
    # pointer per film frame, and each recording mark as the film time it first plays
    marks = {}
    for k, v in meta["marks"].items():
        for m in (v if isinstance(v, list) else [v]):
            if m <= src[0] or m > src[-1]:
                continue
            t = next((round((f0 + i) / FPS, 3) for i, s in enumerate(src) if s >= m), None)
            if t is not None:
                marks.setdefault(k, []).append(t)
    return {"start": round(f0 / FPS, 4), "dur": round(len(src) / FPS, 4), "src": f"assets/shots/{name}.mp4",
            "cursor": [meta["cursor"][k] for k in src], "frames": src, "marks": {k: v if len(v) > 1 else v[0] for k, v in marks.items()}}


if __name__ == "__main__":
    edit = {"cuts": {k: round(v, 3) for k, v in CUTS.items()}, "shots": {}}
    for name, (take, start, end, keys) in SHOTS.items():
        edit["shots"][name] = conform(name, take, start, end, keys)
        s = edit["shots"][name]
        print(f"{name:10s} {s['start']:6.2f}-{s['start'] + s['dur']:6.2f}  frames {s['frames'][0]}..{s['frames'][-1]}  marks {s['marks']}")
    # the hook's site positions and the laptop's screen corners, per frame of their renders
    hook = json.loads((ROOT / "assets" / "map" / "hook.json").read_text())
    ids = [x[0] for x in hook["frames"][0]["sites"]]
    edit["hook"] = {"timing": hook["timing"], "ids": ids, "zoom": [round(f["zoom"], 3) for f in hook["frames"]],
                    "xy": [[[x[1], x[2]] for x in f["sites"]] for f in hook["frames"]]}
    lap = json.loads((ROOT / "assets" / "device" / "laptop.json").read_text())
    edit["laptop"] = {"timing": lap["timing"], "corners": [f["corners"] for f in lap["frames"]]}
    (ROOT / "assets" / "edit.js").write_text("window.EDIT = " + json.dumps(edit, separators=(",", ":")) + ";\n")
    print("cuts", edit["cuts"])
    # the film's video clips take their times from here
    html = (ROOT / "index.html").read_text()
    clips = {f"v-{k}": (v["start"], v["dur"]) for k, v in edit["shots"].items()}
    clips["hookv"] = (0, round(len(edit["hook"]["zoom"]) / FPS, 4))
    clips["lapv"] = (round(fr(L0) / FPS, 4), round(len(edit["laptop"]["corners"]) / FPS, 4))
    for vid, (a, d) in clips.items():
        html, n = re.subn(rf'(<video id="{vid}" class="clip" data-start=")[^"]*(" data-duration=")[^"]*"', rf"\g<1>{a}\g<2>{d}" + '"', html)
        if not n:
            print("warning: no clip", vid)
    (ROOT / "index.html").write_text(html)
