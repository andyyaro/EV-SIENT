"""Narration: one wav per line of sound/script.json, voiced by Kokoro-82M (af_heart), plus sound/vo/manifest.json.

Run with a Python that has kokoro and soundfile:  python3 sound/voice.py [--check]
Each clip is trimmed, resampled to 48 kHz mono and loudness-normalised (two-pass loudnorm, -16 LUFS, -1.5 dBTP).
--check transcribes every clip with faster-whisper so mispronunciations show up.
"""
import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np, soundfile as sf

HERE = Path(__file__).resolve().parent
VO = HERE / "vo"
VOICE, LANG, SPEED, SR, OUT_SR = "af_heart", "a", 1.0, 24000, 48000

def ffmpeg(*a):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *a], capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-1500:])
    return r.stderr

def trim(x, pad=0.05, db=-42.0):
    peak = float(np.max(np.abs(x))) or 1.0; w = int(0.01 * SR); n = len(x) // w
    rms = np.sqrt(np.mean(x[: n * w].reshape(n, w) ** 2, axis=1))
    loud = np.where(20 * np.log10(rms / peak + 1e-12) > db)[0]
    s = max(0, loud[0] * w - int(pad * SR)); e = min(len(x), (loud[-1] + 1) * w + int(pad * SR))
    return x[s:e]

def normalise(src, dst, I=-16.0, TP=-1.5, LRA=11.0):
    m = ffmpeg("-i", str(src), "-af", f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-")
    m = json.loads(m[m.rindex("{"): m.rindex("}") + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    ffmpeg("-y", "-i", str(src), "-af", af, "-ar", str(OUT_SR), "-ac", "1", "-c:a", "pcm_s16le", str(dst))

def main():
    from kokoro import KPipeline
    lines = json.loads((HERE / "script.json").read_text())
    pipe = KPipeline(lang_code=LANG, repo_id="hexgrad/Kokoro-82M")
    VO.mkdir(exist_ok=True); man = {}
    for ln in lines:
        audio = np.concatenate([np.asarray(a) for _, _, a in pipe(ln.get("speak") or ln["text"], voice=VOICE, speed=SPEED)]).astype(np.float32)
        audio = trim(audio)
        with tempfile.TemporaryDirectory() as t:
            raw = Path(t) / "raw.wav"; sf.write(raw, audio, SR, subtype="FLOAT")
            normalise(raw, VO / f"{ln['key']}.wav")
        d = sf.info(VO / f"{ln['key']}.wav").duration
        man[ln["key"]] = {"file": f"{ln['key']}.wav", "duration": round(d, 3), "text": ln["text"], "voice": VOICE, "speed": SPEED}
        print(f"{ln['key']:11s} {d:5.2f} s  {len(ln['text'].split())} words")
    (VO / "manifest.json").write_text(json.dumps(man, indent=1))
    print("total speech", round(sum(v["duration"] for v in man.values()), 2), "s")
    if "--check" in sys.argv:
        from faster_whisper import WhisperModel
        model = WhisperModel("small.en", device="cpu", compute_type="int8")
        for k, v in man.items():
            segs, _ = model.transcribe(str(VO / v["file"]), beam_size=5, language="en")
            print(f"  heard {k}: {' '.join(s.text.strip() for s in segs)}")

if __name__ == "__main__":
    main()
