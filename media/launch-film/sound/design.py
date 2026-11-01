"""Sound for the EV-SIENT launch film, v2: treated narration, the music bed, recorded foley and city ambience.

    python3 -I tools/build_cues.py                                    # cues.json -> assets/cues.js
    python3 -I sound/events.py                                        # composition -> sound/events.json
    python3 sound/design.py           # -> assets/audio/mix.wav (48 kHz stereo, -16 LUFS)

Layers:
- Narration: Kokoro-82M, voice af_heart (sound/voice.py), each line placed at its cues.json start, then given a
  studio chain: high-pass at 80 Hz, a little less low-mid mud, presence and air, a de-esser, gentle compression,
  and a small room so it sits in a space instead of on top of the picture.
- Music: cues.json "music": an edit list of [film time, track time] segments cut on downbeats with short
  equal-power crossfades. The bed sits near -18 LUFS where nobody speaks and ducks 8 dB under the voice.
- Ambience: a night city under the opening flight. It follows the camera: close to the street on the glide,
  thinning as the camera climbs over the region, rising again as it dives onto the site, gone on the logo.
- Foley: Mixkit recordings (assets/audio/sfx, see assets/audio/SOURCE.md), each placed on the frame it belongs to
  (sound/events.json, read from the composition) and panned to where it happens on screen: the pointer's real
  clicks, real keystrokes for the typed question, the lights switching on over the map, whooshes on the camera
  moves, the counter's ticks. A few sounds stay synthesized where they are musical: the sub hit on the logo and
  the plucks as the four parts fill.
Master: two-pass loudnorm to -16 LUFS integrated, -1.5 dBTP.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "assets" / "audio" / "mix.wav"
SFXD = ROOT / "assets" / "audio" / "sfx"
CUES = json.loads((ROOT / "cues.json").read_text())
EV = json.loads((HERE / "events.json").read_text())
EDIT = json.loads((ROOT / "assets" / "edit.js").read_text().strip().removeprefix("window.EDIT = ").rstrip(";"))
MAN = json.loads((HERE / "vo" / "manifest.json").read_text())
SR = 48000
DUR = float(CUES["duration"])
N = int(SR * DUR)
rng = np.random.default_rng(2026)

buses = {name: np.zeros((2, N)) for name in ("music", "sfx", "amb", "voice")}


def add(bus: str, t: float, sig: np.ndarray, pan=0.0, gain: float = 1.0) -> None:
    """Mix a mono (or stereo) signal into a bus at time t (s). Mono is equal-power panned (-1 left … +1 right);
    `pan` may be an array as long as the signal, for a sound that travels."""
    i = int(round(t * SR))
    if sig.ndim == 1:
        a = (np.asarray(pan) + 1) * np.pi / 4
        sig = np.vstack([np.cos(a) * sig, np.sin(a) * sig])
    if i >= N or sig.shape[1] == 0:
        return
    s0 = max(0, -i)
    i = max(i, 0)
    j = min(N, i + sig.shape[1] - s0)
    buses[bus][:, i:j] += gain * sig[:, s0 : s0 + (j - i)]


def db(x: float) -> float:
    return 10 ** (x / 20)


def read_wav(path: Path) -> np.ndarray:
    sr, x = wavfile.read(path)
    x = x.astype(np.float64)
    if x.dtype.kind == "i" or np.abs(x).max() > 1.5:
        x /= 32768.0
    assert sr == SR, (path, sr)
    return x.T if x.ndim == 2 else x


def decode(path: Path, af: str | None = None) -> np.ndarray:
    """Any audio file -> float64 stereo at SR, via ffmpeg (optionally through a filter chain)."""
    cmd = ["ffmpeg", "-v", "error", "-i", str(path)] + (["-af", af] if af else []) + ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64).reshape(-1, 2).T


def loudness(x: np.ndarray) -> float:
    """Integrated loudness (LUFS) of a stereo signal, measured by ffmpeg's ebur128."""
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        wavfile.write(f.name, SR, x.T.astype(np.float32))
        err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f.name, "-af", "ebur128", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
    tail = err[err.rfind("Summary:"):]
    return float(tail.split("I:")[1].split("LUFS")[0])


def ffx(x: np.ndarray, af: str) -> np.ndarray:
    """Run a stereo signal through an ffmpeg filter chain."""
    with tempfile.TemporaryDirectory() as td:
        a = Path(td) / "a.wav"
        wavfile.write(a, SR, x.T.astype(np.float32))
        return decode(a, af)[:, : x.shape[1]]


# ---------- recorded foley ----------
@lru_cache(maxsize=None)
def sample(name: str, rate: float = 1.0) -> np.ndarray:
    """A Mixkit effect as mono at SR, peak-normalised to 0 dBFS. rate < 1 plays it slower and lower."""
    x = decode(SFXD / f"{name}.mp3").mean(0)
    if rate != 1.0:
        x = signal.resample(x, int(len(x) / rate))
    return x / (np.abs(x).max() + 1e-12)


# where each effect's moment is, in seconds from its start: the onset of a click, the peak of a whoosh
MOMENT = {"air-woosh": 0.72, "deep-whoosh-impact": 0.52, "fast-whoosh": 0.74, "fast-small-sweep": 0.30, "short-sweep": 0.46,
          "quick-zoom-impact": 0.42, "electric-charge-hum": 0.40, "electric-switch": 0.265, "electric-pop": 0.012,
          "mouse-click-close": 0.011, "light-button": 0.008, "light-pop-whoosh": 0.02, "message-pop": 0.053,
          "confirmation-tone": 0.005, "interface-select": 0.105, "tech-transition-slide": 0.05}


def fx(name: str, t: float, gain_db: float, pan=0.0, rate: float = 1.0, until: float | None = None) -> None:
    """Place an effect so its moment lands on film time t. `until` cuts it (with a 20 ms fade) that many s after t."""
    x = sample(name, rate).copy()
    m = MOMENT.get(name, 0.0) / rate
    if until is not None:
        k = int((m + until) * SR)
        x = x[:k]
        f = min(len(x), int(0.02 * SR))
        x[-f:] *= np.linspace(1, 0, f)
    add("sfx", t - m, x, pan, db(gain_db))


def slices(name: str, rel_db: float, gap: float, length: float) -> list[np.ndarray]:
    """Cut a recording of many hits (keystrokes, ticks) into single hits, each from just before its onset."""
    x = sample(name)
    hop = SR // 1000
    e = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, mode="same"))[::hop]
    th = e.max() * db(rel_db)
    on, last = [], -10_000
    for i in range(1, len(e)):
        if e[i] > th >= e[i - 1] and i - last > gap * 1000:
            on.append(i)
            last = i
    out = []
    for i in on:
        a = max(0, (i - 4) * hop)
        s = x[a : a + int(length * SR)].copy()
        if len(s) < int(length * SR):
            continue
        s[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
        out.append(s / (np.abs(s).max() + 1e-12))
    return out


KEYS = slices("laptop-typing", -20, 0.04, 0.085)
TICKS = slices("ticking-counter", -20, 0.02, 0.022)


# ---------- synthesized, where the sound is musical ----------
def env(n: int, a: float, d: float) -> np.ndarray:
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)


def noise(n: int) -> np.ndarray:
    return rng.standard_normal(n)


def band(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return signal.sosfilt(signal.butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)


def blip(t: float, freq: float, gain=0.12, dec=0.25, pan=0.0) -> None:
    """A soft sine blip with a fifth on top."""
    n = int((dec * 5) * SR)
    tt = np.arange(n) / SR
    x = (np.sin(2 * np.pi * freq * tt) + 0.35 * np.sin(2 * np.pi * freq * 1.5 * tt)) * env(n, 0.004, dec)
    add("sfx", t, x * gain, pan)


def hit(t: float, gain=0.5) -> None:
    """A sub drop (70 -> 42 Hz) under a short air burst, for the logo and the music's drops."""
    n = int(1.4 * SR)
    tt = np.arange(n) / SR
    f = 42 + 28 * np.exp(-tt / 0.08)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.005, 0.38)
    air = band(noise(n), 800, 6000) * env(n, 0.002, 0.09) * 0.25
    add("sfx", t, (sub + air) * gain)


def shimmer(t: float, gain=0.10) -> None:
    """A rising shimmer for the call to action."""
    n = int(1.6 * SR)
    tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * (1 + 0.02 * tt) * tt) / (k + 1) for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]))
    e = np.minimum(1, tt / 0.35) * np.exp(-np.maximum(0, tt - 0.35) / 0.5)
    for p, d in ((-0.4, 0), (0.4, int(0.012 * SR))):
        add("sfx", t + d / SR, x * e * gain, p)


def chime(t: float, notes=(880.0, 1318.5), gap=0.09, gain=0.10, pan=0.0) -> None:
    for k, f in enumerate(notes):
        n = int(1.2 * SR)
        tt = np.arange(n) / SR
        x = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt / 0.08)) * env(n, 0.003, 0.32)
        add("sfx", t + k * gap, x * gain, pan)


def travel(n: int, a: float, b: float) -> np.ndarray:
    return np.linspace(a, b, n)


# ---------- narration, with a studio chain ----------
for key, start in CUES["vo"].items():
    add("voice", start, read_wav(HERE / "vo" / MAN[key]["file"]))
dry = buses["voice"].mean(0)
CHAIN = ("highpass=f=80:p=2,"
         "equalizer=f=280:t=q:w=1.1:g=-2.5,"           # less low-mid mud
         "equalizer=f=3400:t=q:w=1.3:g=2.2,"           # presence
         "highshelf=f=9500:g=2.5,"                     # air
         "deesser=i=0.35:m=0.5:f=0.55,"
         "acompressor=threshold=0.09:ratio=3:attack=6:release=90:knee=3:makeup=1.5")
vox = ffx(np.vstack([dry, dry]), CHAIN).mean(0)
# a small, bright room: pre-delay 9 ms, RT60 about 0.3 s, decorrelated left and right, kept well under the voice
n_ir = int(0.45 * SR)
tt = np.arange(n_ir) / SR
irs = []
for k in range(2):
    r = noise(n_ir) * np.exp(-tt * 6.91 / 0.3)
    r = signal.sosfilt(signal.butter(2, [350, 7000], btype="band", fs=SR, output="sos"), r)
    r = np.concatenate([np.zeros(int(0.009 * SR)), r])
    irs.append(r / np.sqrt((r ** 2).sum()))
wet = np.vstack([signal.fftconvolve(vox, irs[k])[:N] for k in range(2)])
buses["voice"] = np.vstack([vox, vox]) + wet * db(-15)
print(f"voice: chain + room, {loudness(buses['voice']):.1f} LUFS")

# ---------- ambience: a night city under the flight, following the camera's height ----------
H = EV["hook"]
amb = decode(SFXD / "city-night-ambience.mp3")
seg = amb[:, int(18 * SR) : int(18 * SR) + int((H["end"] + 0.6) * SR)]
seg = seg * db(-24 - loudness(seg))
zoom = np.array(EDIT["hook"]["zoom"])
zt = np.arange(len(zoom)) / 30
g_db = np.interp(zoom, [10.2, 12.0, 15.0, 17.6], [-15.0, -10.0, -1.0, 2.0])
g = db(np.interp(np.arange(seg.shape[1]) / SR, zt, g_db))
fade = np.clip(np.arange(seg.shape[1]) / (0.3 * SR), 0, 1)
out_t = np.arange(seg.shape[1]) / SR
fade *= np.clip((H["end"] + 0.15 - out_t) / 0.35, 0, 1) ** 2
add("amb", 0.0, seg * g * fade)

# ---------- foley, on the composition's frames ----------
# the opening: the camera cranes up on "chargers", the sites switch on, the top three light, the dive
fx("air-woosh", H["tp0"] + 0.55, -15, rate=0.8)
for t, p in H["lights"]:
    fx("electric-pop", t, -30, pan=p)
    blip(t, 1760.0, gain=0.018, dec=0.12, pan=p)
for k, (t, p) in enumerate(H["top"]):
    fx("electric-switch", t, -14, pan=p)
    blip(t + 0.01, [880.0, 1108.7, 1318.5][k], gain=0.09, pan=p)
fx("electric-charge-hum", H["why"] + 0.25, -22, pan=H["hero"])
blip(H["why"], 1318.5, gain=0.07, pan=H["hero"])
fx("fast-whoosh", H["end"] - 0.02, -11)                               # the dive accelerates into the logo
fx("deep-whoosh-impact", H["end"], -9)
hit(EV["brand"], gain=0.42)                                         # the pin lands, on the music's drop
fx("short-sweep", EV["word"] + 0.35, -19, pan=0.3)                  # the wordmark wipes in
fx("fast-small-sweep", EV["brandOut"] + 0.25, -19)
fx("air-woosh", EV["win0"] + 0.35, -18)                             # the window rises

# the study: the weights card, the four parts, the counter, the highlights, the cuts inside the window
fx("tech-transition-slide", EV["parts0"], -21)
for k, t in enumerate(EV["parts"]):
    blip(t, [523.3, 659.3, 784.0, 1046.5][k], gain=0.11, dec=0.18, pan=-0.45 + 0.3 * k)
fx("fast-small-sweep", EV["countIn"] + 0.2, -21, pan=-0.6)
c0, c1 = EV["count"]
for k in range(26):                                                 # the odometer to 2,000, slowing as it lands
    t = c0 + (c1 - c0) * (1 - (1 - k / 26) ** 2.2)
    add("sfx", t, TICKS[k % len(TICKS)] * db(-17 - 4 * k / 26), -0.6)
for t in EV["rings"]:
    fx("light-button", t, -22, pan=0.15)
    blip(t, 1568.0, gain=0.035, dec=0.12, pan=0.15)
for t in EV["cuts"]:                                                # the incoming shot arrives from the right
    n = len(sample("fast-small-sweep"))
    fx("fast-small-sweep", t, -20, pan=travel(n, 0.5, -0.3))
fx("fast-whoosh", EV["out1"] + 0.36, -16)                           # the window falls away
hit(EV["turn"][0] + 0.05, gain=0.28)                                # "Now it's your turn", on the second drop

# the laptop rises out of the dark; the window lifts off its screen
l0, l1 = EV["laptop"]
fx("air-woosh", l0 + 0.75, -15, rate=0.7)
fx("light-pop-whoosh", l1 + 0.12, -19)
# the pointer: every press in the recordings, where it happens; the file dropped; the question typed
for t, p, _ in EV["clicks"]:
    fx("mouse-click-close", t, -13, pan=p)
fx("short-sweep", EV["drag"][0] + 0.35, -27, pan=0.1)
fx("light-pop-whoosh", EV["drag"][1], -17, pan=0.1)
fx("message-pop", EV["drag"][1] + 0.04, -20, pan=0.1)
for k, t in enumerate(EV["keys"]):
    add("sfx", t, KEYS[(k * 7) % len(KEYS)] * db(-15 + rng.uniform(-2, 1)), -0.05)
# the model runs; the results arrive; the promise; the PDF
fx("electric-charge-hum", EV["run"][0] + 0.45, -24)
fx("interface-select", EV["run"][1], -17)
fx("message-pop", EV["badge"] + 0.08, -15, pan=0.45)
fx("confirmation-tone", EV["toast"] + 0.05, -17, pan=0.45)
# and more: three notes arrive on the right; the connection drops
for k, t in enumerate(EV["notes"]):
    fx("light-pop-whoosh", t + 0.05, -17, pan=0.55)
    blip(t + 0.05, [784.0, 987.8, 1174.7][k], gain=0.06, dec=0.2, pan=0.55)
fx("electric-switch", EV["offline"], -15, pan=-0.2)
# the call to action
fx("fast-whoosh", EV["end0"] + 0.36, -15)
hit(EV["ctaIn"], gain=0.28)
shimmer(EV["cta"][0], gain=0.07)
shimmer(EV["hit"] - 0.25, gain=0.09)
chime(EV["hit"], notes=(1318.5, 1975.5), gain=0.06)

# ---------- music bed: the edit (film <- track, cut on downbeats), ducked under the voice ----------
mus = CUES.get("music")
if mus and (ROOT / mus["file"]).exists():
    src = decode(ROOT / mus["file"])
    xf = mus.get("xfade", 0.03)
    edit = mus["edit"] + [[DUR, None]]
    bed = np.zeros((2, N))
    for k, ((fs, ts), (fe, _)) in enumerate(zip(edit, edit[1:])):
        a = fs - (xf if k else 0.0)
        b = min(DUR, fe + xf) if fe < DUR else DUR
        i0, i1 = int(round(a * SR)), int(round(b * SR))
        j0 = int(round((ts + (a - fs)) * SR))
        seg = src[:, j0 : j0 + (i1 - i0)]
        seg = np.pad(seg, ((0, 0), (0, (i1 - i0) - seg.shape[1])))
        w = np.ones(i1 - i0)
        L = int(round(2 * xf * SR))
        if k:
            w[:L] *= np.sin(np.linspace(0, np.pi / 2, L))
        if fe < DUR:
            w[-L:] *= np.cos(np.linspace(0, np.pi / 2, L))
        bed[:, i0:i1] += seg * w
    bed *= db(mus.get("target_lufs", -18.0) - loudness(bed))
    hop = SR // 100
    vb = buses["voice"].mean(0)
    rms = np.sqrt(np.convolve(vb ** 2, np.ones(hop) / hop, mode="same"))[::hop]
    act = (rms > db(-45)).astype(float)
    g = np.zeros_like(act)
    a_up, a_dn = np.exp(-1 / 6), np.exp(-1 / 45)
    for k in range(len(act)):
        prev = g[k - 1] if k else 0.0
        g[k] = act[k] + (prev - act[k]) * (a_up if act[k] > prev else a_dn)
    duck = db(mus.get("duck_db", -8.0)) ** g
    buses["music"] += bed * np.interp(np.arange(N), np.arange(len(duck)) * hop, duck)
    print(f"music: {mus['file']}, {len(mus['edit'])} segments, target {mus.get('target_lufs', -18)} LUFS, duck {mus.get('duck_db', -8)} dB")
else:
    print("music: none (narration and sound effects only)")

buses["sfx"] *= db(CUES.get("sfx_gain_db", 0.0))
for name, bus in buses.items():
    if np.abs(bus).max() > 0:
        print(f"  {name:6s} {loudness(bus):6.1f} LUFS  peak {20 * np.log10(np.abs(bus).max()):5.1f} dBFS")
mix = buses["voice"] + buses["sfx"] + buses["amb"] + buses["music"]
OUT.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as td:
    pre = Path(td) / "pre.wav"
    wavfile.write(pre, SR, (mix.T / max(1.0, np.abs(mix).max())).astype(np.float32))
    ln = "loudnorm=I=-16:TP=-1.5:LRA=11"
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(pre), "-af", ln + ":print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    j0 = err.rfind("{")
    m = json.loads(err[j0 : err.index("}", j0) + 1])
    ln2 = (f"{ln}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
           f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", ln2, "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", str(OUT)], check=True)
print("wrote", OUT.relative_to(ROOT), f"{DUR:.2f}s; loudness {loudness(read_wav(OUT)):.1f} LUFS")
