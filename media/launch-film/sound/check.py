"""Transcribe each narration clip with faster-whisper to catch mispronunciations."""
import json, subprocess
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
VO = Path(__file__).resolve().parent / "vo"
model = WhisperModel("small.en", device="cpu", compute_type="int8")
for k, v in json.loads((VO / "manifest.json").read_text()).items():
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(VO / v["file"]), "-ar", "16000", "-ac", "1", "-f", "f32le", "-"], capture_output=True).stdout
    segs, _ = model.transcribe(np.frombuffer(pcm, np.float32), beam_size=5, language="en")
    print(f"{k}: {' '.join(s.text.strip() for s in segs)}")

# Word timings for the captions and the kinetic type.
words = {}
for k, v in json.loads((VO / "manifest.json").read_text()).items():
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(VO / v["file"]), "-ar", "16000", "-ac", "1", "-f", "f32le", "-"], capture_output=True).stdout
    segs, _ = model.transcribe(np.frombuffer(pcm, np.float32), beam_size=5, language="en", word_timestamps=True)
    words[k] = [[w.word.strip(), round(w.start, 3), round(w.end, 3)] for s in segs for w in s.words]
(VO / "words.json").write_text(json.dumps(words, indent=1))
