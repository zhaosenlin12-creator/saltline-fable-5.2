# -*- coding: utf-8 -*-
"""s2_tts.py - narration script -> MiniMax TTS -> timeline.json.

Script markup: 【...】 marks a keyword that gets highlighted in the captions.
Each beat is (id, section, voice_key, speed, gap_after_seconds, text).

Also trims leading/trailing silence by energy and normalises each line to
-1 dBFS so the mix sits predictably, then lays the lines out on a narration
clock that the visual cut list follows.
"""
import os
import re
import time
import shutil
import subprocess
import wave

import numpy as np
import requests

from common import load_project, api_key, api_keys, dump_json

TTS_API = "https://api.minimaxi.com/v1/t2a_v2"


def clean(text):
    return re.sub(r"[【】]", "", text)


def tts(text, voice, speed, out_path):
    body = {"model": "speech-02-hd", "text": text, "stream": False,
            "voice_setting": {"voice_id": voice, "speed": speed, "vol": 1.0, "pitch": 0},
            "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"}}
    # a key can run out of Token Plan allowance, so try every key we know
    for attempt in range(4):
        for key in api_keys():
            try:
                r = requests.post(TTS_API, json=body,
                                  headers={"Authorization": "Bearer " + key,
                                           "Content-Type": "application/json"},
                                  timeout=180)
                r.raise_for_status()
                j = r.json()
                if j.get("base_resp", {}).get("status_code") not in (0, None):
                    raise RuntimeError(repr(j.get("base_resp")))
                with open(out_path, "wb") as f:
                    f.write(bytes.fromhex(j["data"]["audio"]))
                return True
            except Exception as e:
                print("  TTS retry (key %s): %s" % (key[:8], e), flush=True)
        if attempt == 3:
            print("  TTS FAIL", out_path, flush=True)
            return False
        time.sleep(3 + attempt * 3)
    return False


def decode_mono(path, sr=32000):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le",
                        "-ac", "1", "-ar", str(sr), "-"],
                       capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0, sr


def trim_silence(src, dst, sr=32000, rel=0.020, pad=0.035):
    """Cut leading/trailing silence by energy, keep a short natural pad."""
    a, sr = decode_mono(src, sr)
    if len(a) == 0:
        shutil.copyfile(src, dst)
        return
    win = 256
    n = len(a) // win
    e = np.abs(a[: n * win].reshape(n, win)).max(axis=1)
    thr = max(float(e.max()) * rel, 0.004)
    idx = np.where(e > thr)[0]
    if len(idx) == 0:
        shutil.copyfile(src, dst)
        return
    st = max(0, int(idx[0] * win - pad * sr))
    en = min(len(a), int((idx[-1] + 1) * win + pad * sr))
    seg = a[st:en]
    seg = seg / (float(np.abs(seg).max()) or 1.0) * 0.89   # normalise to -1 dBFS
    with wave.open(dst, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(seg, -1, 1) * 32767).astype(np.int16).tobytes())


def main():
    p = load_project()
    voice_dir = os.path.join(p.BUILD, "voice")
    os.makedirs(voice_dir, exist_ok=True)
    lines = []
    for bid, sec, vkey, speed, gap, text in p.SCRIPT:
        voice = p.VOICES[vkey]
        mp3 = os.path.join(voice_dir, bid + ".mp3")
        if not (os.path.exists(mp3) and os.path.getsize(mp3) > 1000):
            print("TTS", bid, voice, flush=True)
            if not tts(clean(text), voice, speed, mp3):
                raise SystemExit("tts failed for " + bid)
        wav = os.path.join(voice_dir, bid + ".wav")
        trim_silence(mp3, wav)
        dur = p.probe_duration(wav) if hasattr(p, "probe_duration") else _dur(wav)
        lines.append({"id": bid, "section": sec, "voice": voice, "voice_key": vkey,
                      "speed": speed, "text": text, "plain": clean(text),
                      "mp3": mp3, "wav": wav, "dur": round(dur, 3), "gap": gap})
        print("  %s %6.2fs %s" % (bid, dur, sec), flush=True)

    t = 0.0
    for i, ln in enumerate(lines):
        t = p.LEAD_IN if i == 0 else t + lines[i - 1]["gap"]
        ln["start"] = round(t, 3)
        t += ln["dur"]
        ln["end"] = round(t, 3)
    total = t + p.TAIL_PAD
    dump_json(os.path.join(p.BUILD, "timeline.json"),
              {"lines": lines, "total": round(total, 3)})
    chars = sum(len(l["plain"]) for l in lines)
    print("TOTAL %.2fs  speech %.2fs  chars %d  rate %.2f chars/s"
          % (total, t, chars, chars / total))


def _dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(out.stdout.strip())


if __name__ == "__main__":
    main()
