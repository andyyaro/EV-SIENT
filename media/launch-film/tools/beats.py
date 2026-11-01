"""Tempo, beat grid and per-bar energy of the music bed -> sound/music_beats.json.

    python3 tools/beats.py assets/audio/music/retro-funk-energetic.mp3

Spectral-flux onset strength; tempo from its autocorrelation (70-180 BPM); beat phase from the comb that
collects the most onset energy; downbeats from which of the four phases carries the strongest low end.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import signal

SR = 22050
path = Path(sys.argv[1])
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], check=True, capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
dur = len(x) / SR
hop, nfft = 256, 2048
f, t, Z = signal.stft(x, fs=SR, nperseg=nfft, noverlap=nfft - hop, boundary=None, padded=False)
mag = np.log1p(100 * np.abs(Z))
flux = np.maximum(0, np.diff(mag, axis=1)).sum(0)
flux = np.concatenate([[0], flux])
fps = SR / hop
times = t
onset = flux - signal.medfilt(flux, 31)
onset = np.maximum(onset, 0)
# tempo
ac = np.correlate(onset, onset, mode="full")[len(onset) - 1 :]
lags = np.arange(len(ac))
bpm_l = 60 * fps / np.maximum(lags, 1)
ok = (bpm_l >= 70) & (bpm_l <= 180)
# weight toward 90-130 (a mild log-Gaussian prior)
w = np.exp(-0.5 * (np.log2(bpm_l / 115) / 0.9) ** 2)
lag = lags[ok][np.argmax((ac * w)[ok])]
# refine with parabolic interpolation
a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
lag_f = lag + 0.5 * (a - c) / (a - 2 * b + c)
period = lag_f / fps
bpm = 60 / period
# phase: comb over the whole track
best = (-1, 0)
for ph in np.linspace(0, period, 200, endpoint=False):
    bt = np.arange(ph, dur, period)
    idx = np.clip(np.round(bt * fps).astype(int), 0, len(onset) - 1)
    s = onset[idx].sum()
    if s > best[0]:
        best = (s, ph)
beats = np.arange(best[1], dur, period)
# downbeat: the phase (mod 4) with the most low-frequency onset
low = np.maximum(0, np.diff(mag[f < 150], axis=1)).sum(0)
low = np.concatenate([[0], low])
sc = []
for k in range(4):
    idx = np.clip(np.round(beats[k::4] * fps).astype(int), 0, len(low) - 1)
    sc.append(low[idx].mean())
d0 = int(np.argmax(sc))
downbeats = beats[d0::4]
# loudness per bar
rms = np.sqrt(signal.convolve(x ** 2, np.ones(SR // 10) / (SR // 10), mode="same"))
bars = []
for k in range(len(downbeats) - 1):
    a, b = int(downbeats[k] * SR), int(downbeats[k + 1] * SR)
    lo = np.abs(Z[f < 150, int(downbeats[k] * fps) : int(downbeats[k + 1] * fps)]).mean()
    bars.append([round(downbeats[k], 3), round(20 * np.log10(rms[a:b].mean() + 1e-9), 1), round(float(lo), 4)])
out = {"file": str(path), "duration": round(dur, 3), "bpm": round(bpm, 2), "period": round(period, 4),
       "beats": [round(b, 3) for b in beats], "downbeats": [round(b, 3) for b in downbeats], "downbeatScores": [round(float(s), 3) for s in sc], "bars": bars}
Path("sound/music_beats.json").write_text(json.dumps(out, indent=1))
print(f"duration {dur:.2f}s  bpm {bpm:.2f}  period {period:.4f}s  first beat {beats[0]:.3f}  downbeat phase {d0} scores {np.round(sc, 2)}")
for bar in bars:
    print(f"  bar @ {bar[0]:7.3f}s  rms {bar[1]:6.1f} dB  low {bar[2]:.4f}")
