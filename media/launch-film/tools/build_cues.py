"""cues.json + sound/vo/words.json -> assets/cues.js (window.CUES), the one timing table the film and the mix share.

    python3 -I tools/build_cues.py

Every word time in the film is a narration start (cues.json "vo") plus that word's offset in its clip
(faster-whisper, sound/check.py). Moving a line moves its scene with it.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cues = json.loads((ROOT / "cues.json").read_text())
words = json.loads((ROOT / "sound" / "vo" / "words.json").read_text())
manifest = json.loads((ROOT / "sound" / "vo" / "manifest.json").read_text())
vo = cues["vo"]

out_words = {k: [[w, round(vo[k] + s, 3), round(vo[k] + e, 3)] for w, s, e in words[k]] for k in vo}
ends = {k: round(vo[k] + manifest[k]["duration"], 3) for k in vo}

# caption cues: from just before the first word to a little after the last, never overlapping the next cue
caps = []
for key, a, b, text in cues["captions"]:
    w = out_words[key]
    caps.append([round(w[a][1] - 0.06, 3), round(w[b][2] + 0.45, 3), text])
for i in range(len(caps) - 1):
    caps[i][1] = min(caps[i][1], round(caps[i + 1][0] - 0.02, 3))

# the music edit: film time <- track time, segment by segment; its beats, mapped onto the film
beats, downbeats, end_hit = [], [], None
mus = cues.get("music")
mb = ROOT / "sound" / "music_beats.json"
if mus and mb.exists():
    grid = json.loads(mb.read_text())
    edit = mus["edit"] + [[cues["duration"], None]]
    for (fs, ts), (fe, _) in zip(edit, edit[1:]):
        to_film = lambda x: round(fs + (x - ts), 3)
        beats += [to_film(x) for x in grid["beats"] if ts - 1e-3 <= x < ts + (fe - fs) - 1e-3]
        downbeats += [to_film(x) for x in grid["downbeats"] if ts - 1e-3 <= x < ts + (fe - fs) - 1e-3]
        if ts <= mus.get("endHit", -1) < ts + (fe - fs):
            end_hit = to_film(mus["endHit"])

data = {"fps": cues["fps"], "duration": cues["duration"], "vo": vo, "voEnd": ends, "words": out_words, "caps": caps,
        "beats": beats, "downbeats": downbeats, "endHit": end_hit}
(ROOT / "assets" / "cues.js").write_text("window.CUES = " + json.dumps(data, separators=(",", ":")) + ";\n")

# keep the composition's declared length in step with cues.json
html = ROOT / "index.html"
if html.exists():
    src = html.read_text()
    dur = f'{cues["duration"]:g}'
    src = re.sub(r'(id="root"[^>]*data-duration=")[^"]*"', r"\g<1>" + dur + '"', src)
    src = re.sub(r'(class="clip[^"]*"[^>]*data-whole[^>]*data-duration=")[^"]*"', r"\g<1>" + dur + '"', src)
    src = re.sub(r'(id="mix"[^>]*data-duration=")[^"]*"', r"\g<1>" + dur + '"', src)
    html.write_text(src)

# WebVTT sidecar for players that want soft subtitles
def ts(t):
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:06.3f}"
vtt = ["WEBVTT", ""]
for i, (a, b, text) in enumerate(caps, 1):
    vtt += [str(i), f"{ts(a)} --> {ts(b)}", text, ""]
(ROOT / "renders").mkdir(exist_ok=True)
(ROOT / "renders" / "captions.vtt").write_text("\n".join(vtt))
print(f"{len(caps)} captions; last line ends {max(ends.values()):.2f}s of {cues['duration']}s; {len(beats)} beats; end hit {end_hit}")
