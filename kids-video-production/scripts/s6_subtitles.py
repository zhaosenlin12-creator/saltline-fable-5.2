# -*- coding: utf-8 -*-
"""s6_subtitles.py - build the burned-in ASS captions.

Captions reveal phrase by phrase, with 【keyword】 markup picked out in the
golden accent colour. The robot line uses the red accent so the car's own
voice is visually distinct from the narrator.

ASS colours are BGR, not RGB:
    #F5A623 -> &H0023A6F5&    #E4572E -> &H002E57E4&    white -> &H00FFFFFF&
"""
import os
import re

from common import load_project, load_json

ORANGE = "\\c&H0023A6F5&"
RED = "\\c&H002E57E4&"
WHITE = "\\c&H00FFFFFF&"
FONT = "Microsoft YaHei"

SPLIT = "，。？！；：、,!?;:"


def phrases(marked):
    """Split marked text into caption phrases, keeping punctuation."""
    out, buf, i = [], "", 0
    while i < len(marked):
        ch = marked[i]
        if ch == "【":
            j = marked.find("】", i)
            if j > 0:
                buf += marked[i:j + 1]
                i = j + 1
                continue
        buf += ch
        i += 1
        if ch in SPLIT:
            out.append(buf)
            buf = ""
    if buf.strip():
        out.append(buf)
    return [x for x in out if x.strip()]


def colorize(marked, base=WHITE, kw=ORANGE):
    """Turn 【kw】 markup into ASS colour tags."""
    out, i = "", 0
    while i < len(marked):
        if marked[i] == "【":
            j = marked.find("】", i)
            if j > 0:
                out += "{" + kw + "}" + marked[i + 1:j] + "{" + base + "}"
                i = j + 1
                continue
        out += marked[i]
        i += 1
    return out


def weight(p):
    """Speech-time weight: CJK ~1, latin ~0.55, punctuation adds a pause."""
    w = 0.0
    for ch in p:
        if ch in "【】":
            continue
        if ch in SPLIT:
            w += 1.4
        elif ord(ch) > 0x2E00:
            w += 1.0
        elif ch.isalnum():
            w += 0.55
        else:
            w += 0.3
    return max(w, 0.4)


def fmt(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)


def main():
    p = load_project()
    tl = load_json(os.path.join(p.BUILD, "timeline.json"))
    lines = tl["lines"]
    events = []
    for i, ln in enumerate(lines):
        ps = phrases(ln["text"])
        if not ps:
            continue
        start, end = ln["start"], ln["end"]
        if i + 1 < len(lines):
            end = min(end + 0.30, lines[i + 1]["start"])
        weights = [weight(x) for x in ps]
        tot = sum(weights)
        acc = 0.0
        kw = RED if ln.get("voice_key", "").startswith("male") else ORANGE
        for j, (ph, w) in enumerate(zip(ps, weights)):
            ps_start = start + (end - start) * (acc / tot)
            acc += w
            ps_end = start + (end - start) * (acc / tot)
            if j == len(ps) - 1:
                ps_end = max(ps_end, end)
            events.append((ps_start, ps_end, colorize(ph, WHITE, kw)))

    px = int(getattr(p, "SUB_W", p.W))
    py = int(getattr(p, "SUB_H", p.H))
    fs = int(getattr(p, "SUB_SIZE", 64))
    mh = int(getattr(p, "SUB_MARGIN_H", 60))
    mv = int(getattr(p, "SUB_MARGIN_V", 286))
    ow = float(getattr(p, "SUB_OUTLINE", 5.0))
    sh = float(getattr(p, "SUB_SHADOW", 1.8))
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: %d
PlayResY: %d
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Microsoft YaHei,%d,&H00FFFFFF,&H00FFFFFF,&H00303030,&H90000000,-1,0,0,0,100,100,1,0,1,%.1f,%.1f,2,%d,%d,%d,1
Style: Robot,Microsoft YaHei,%d,&H00FFFFFF,&H00FFFFFF,&H00303030,&H90000000,-1,0,0,0,100,100,1,0,1,%.1f,%.1f,2,%d,%d,%d,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" % (px, py, fs, ow, sh, mh, mh, mv, fs + 2, ow, sh, mh, mh, mv)
    body = []
    for s, e, txt in events:
        body.append("Dialogue: 0,%s,%s,Main,,0,0,0,,{\\fad(110,110)}%s" % (fmt(s), fmt(e), txt))
    path = os.path.join(p.BUILD, "subs.ass")
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(head + "\n".join(body) + "\n")
    print("subtitles: %d events -> %s" % (len(events), path))


if __name__ == "__main__":
    main()
