# -*- coding: utf-8 -*-
"""s9_qa.py - automated delivery QA on the finished film.

Six sections: container, picture, audio, captions, content coverage, assets.
Every threshold that could legitimately vary per project lives in project.py
(QA_* keys); the checks themselves are fixed so a film either passes the same
bar every time or fails loudly.

Exit code is non-zero when any check fails, so it can gate a pipeline.
"""
import os
import re
import sys
import json
import wave
import subprocess

import numpy as np

from common import load_project, load_json, dec

fails, warns = [], []


def chk(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        fails.append(msg)


def warn(cond, msg):
    if not cond:
        print("  WARN " + msg)
        warns.append(msg)


def sec(x):
    h, m, s = x.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def main():
    p = load_project()
    movie = os.path.join(p.ROOT, p.OUTPUT_NAME)
    tmp = os.path.join(p.BUILD, "qa_audio.wav")

    print("=== 1. container / codec ===")
    j = json.loads(dec(["ffprobe", "-v", "error", "-print_format", "json",
                        "-show_format", "-show_streams", movie]))
    v = [s for s in j["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in j["streams"] if s["codec_type"] == "audio"][0]
    dur = float(j["format"]["duration"])
    chk(v["width"] == p.W and v["height"] == p.H,
        "resolution %dx%d = %dx%d" % (v["width"], v["height"], p.W, p.H))
    chk(v["r_frame_rate"] == "%d/1" % p.FPS, "frame rate %s = %dfps" % (v["r_frame_rate"], p.FPS))
    chk(v["codec_name"] == "h264", "video codec %s / profile %s" % (v["codec_name"], v.get("profile")))
    chk(v["pix_fmt"] == "yuv420p", "pixel format %s (player safe)" % v["pix_fmt"])
    chk(a["codec_name"] == "aac", "audio codec %s" % a["codec_name"])
    chk(a["sample_rate"] == "44100" and a["channels"] == 2,
        "audio %sHz %sch" % (a["sample_rate"], a["channels"]))
    lo, hi = p.QA_DURATION
    chk(lo <= dur <= hi, "duration %.2fs (target %g-%gs)" % (dur, lo, hi))
    chk(int(j["format"]["size"]) > 8_000_000, "file size %.1f MB" % (int(j["format"]["size"]) / 1e6))

    print("=== 2. video: black frames, motion, cuts ===")
    sw, sh = 96, int(96 * p.H / p.W)
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", movie,
                          "-vf", "scale=%d:%d" % (sw, sh), "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True).stdout
    n = len(out) // (sw * sh)
    fr = np.frombuffer(out[:n * sw * sh], dtype=np.uint8).reshape(n, sw, sh).astype(np.float32)
    mean = fr.mean(axis=(1, 2))
    chk(int((mean < 12).sum()) == 0, "no black frames (found %d)" % int((mean < 12).sum()))
    diff = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    cuts = np.where(diff > 6.0)[0]
    exp = p.QA_MIN_CUTS
    print("  hard cuts detected: %d (%d segments expect >= %d)" % (len(cuts), len(p.SEG_NAMES), exp))
    chk(len(cuts) >= exp, "at least %d visible cuts" % exp)
    still = diff < 0.18
    best = run = 0
    for s in still:
        run = run + 1 if s else 0
        best = max(best, run)
    print("  longest motionless stretch: %.2fs" % (best / p.FPS))
    chk(best / float(p.FPS) < 6.0, "no segment is visually frozen for over 6s")
    print("  mean inter-frame motion: %.3f (min %.3f max %.3f)" % (diff.mean(), diff.min(), diff.max()))

    print("=== 3. audio ===")
    dec(["ffmpeg", "-y", "-v", "error", "-i", movie, "-ac", "1", "-ar", "44100",
         "-c:a", "pcm_s16le", tmp])
    with wave.open(tmp, "rb") as w:
        nsr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    peak = float(np.abs(x).max())
    chk(peak <= 0.99, "no clipping (peak %.3f)" % peak)
    chk(peak > 0.25, "healthy peak level (peak %.3f)" % peak)
    win = nsr // 10
    m = len(x) // win
    lv = np.sqrt((x[:m * win].reshape(m, win) ** 2).mean(axis=1))
    body = lv[2:len(lv) - 6]
    chk(body.min() > 0.002, "no dead air in the body (min 100ms RMS %.4f)" % body.min())
    print("  head fade %.4f/%.4f  tail fade %.4f/%.4f" % (lv[0], lv[1], lv[-2], lv[-1]))
    print("  programme RMS %.3f (~%.1f dBFS)"
          % (np.sqrt((x ** 2).mean()), 20 * np.log10(np.sqrt((x ** 2).mean()))))

    tl = load_json(os.path.join(p.BUILD, "timeline.json"))
    sp = set()
    for l in tl["lines"]:
        for i in range(int(l["start"] * 10), int(l["end"] * 10)):
            sp.add(i)
    sp_r = [lv[i] for i in sp if i < len(lv)]
    mu_r = [lv[i] for i in range(len(lv)) if i not in sp]
    if mu_r:
        sep = 20 * np.log10(np.median(sp_r) / max(np.median(mu_r), 1e-6))
        print("  speech RMS %.3f | music-only RMS %.3f | separation %.1f dB"
              % (np.median(sp_r), np.median(mu_r), sep))
        chk(sep > p.QA_MIN_SEPARATION_DB, "voice sits clearly above the music bed")

    print("=== 4. captions ===")
    ass = open(os.path.join(p.BUILD, "subs.ass"), encoding="utf-8-sig").read()
    evs = re.findall(r"Dialogue: .*?,([\d:.]+),([\d:.]+),(\w+),.*?,(.*)$", ass, re.M)
    chk(len(evs) >= p.QA_MIN_CAPTIONS, "%d caption events" % len(evs))
    chk(not [e for e in evs if e[3].strip() == ""], "no empty caption events")
    ends = [sec(e[1]) for e in evs]
    chk(max(ends) <= dur + 0.5, "captions end inside the film (last %.1fs <= %.1fs)" % (max(ends), dur))
    chk("\\c&H0023A6F5&" in ass, "golden keyword highlight present")
    chk("fad(" in ass, "captions fade in/out")
    ov = sum(1 for i in range(len(evs) - 1) if sec(evs[i][1]) > sec(evs[i + 1][0]) + 0.02)
    chk(ov == 0, "no overlapping captions (%d overlaps)" % ov)
    gaps = [sec(evs[i + 1][0]) - sec(evs[i][1]) for i in range(len(evs) - 1)]
    print("  caption gap between phrases: min %.2fs max %.2fs" % (min(gaps), max(gaps)))

    print("=== 5. content coverage ===")
    txt = "".join(l["plain"] for l in tl["lines"])
    for kw in p.QA_KEYWORDS:
        chk(kw in txt, "script mentions %s" % kw)
    chk(len(txt) >= p.QA_MIN_CHARS, "script length %d chars" % len(txt))
    chk(len(tl["lines"]) == len(p.SCRIPT), "%d narration beats" % len(tl["lines"]))
    cps = len(txt) / tl["total"]
    print("  speaking rate %.2f Chinese chars/s (kids' science sweet spot %g-%g)"
          % (cps, p.QA_RATE_RANGE[0], p.QA_RATE_RANGE[1]))
    chk(p.QA_RATE_RANGE[0] <= cps <= p.QA_RATE_RANGE[1],
        "pacing is in the comfortable range for young viewers")

    print("=== 6. assets ===")
    ai = len([f for f in os.listdir(p.AI) if f.endswith(".png")])
    real = len([f for f in os.listdir(p.REAL) if f.endswith(".jpg")])
    seg = len([f for f in os.listdir(os.path.join(p.BUILD, "seg")) if f.endswith(".mp4")])
    chk(ai >= p.QA_MIN_AI, "%d generated illustrations" % ai)
    chk(real >= p.QA_MIN_REAL, "%d real photographs" % real)
    chk(seg == len(p.SEG_NAMES), "%d rendered segments" % seg)

    print()
    print("=" * 60)
    print("RESULT: %d failure(s), %d warning(s)" % (len(fails), len(warns)))
    for f in fails:
        print("  FAIL:", f)
    for w in warns:
        print("  WARN:", w)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
