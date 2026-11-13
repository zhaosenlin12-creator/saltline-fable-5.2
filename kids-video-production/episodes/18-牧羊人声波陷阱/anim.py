# -*- coding: utf-8 -*-
"""anim.py - the animated segments for the 牧羊人·声波陷阱 film.

  * v09_code_read   - program 1: the little eye measures the distance
  * v10_code_judge  - program 2: closer than 4 metres? fire once per second
  * v11_code_effect - program 3: the pop, the 2 second freeze, the screen warp
  * v14_test_beep   - live test: the beep dies out beyond 7 metres
  * v15_test_trigger- live test: the walking robot steps into 4 metres
  * v16_test_manual - live test: pressing H blows a 7 metre circle

Every segment is cut to the exact length of its narration beat, so picture
and voice stay locked.  Nothing here is a real sound charge: the "device" is
a cardboard disc, the blast is a drawn ring and the only measurement is an
ultrasonic module reading centimetres off a paper robot.
"""
import os
import math
import random
import subprocess

import numpy as np
from PIL import Image, ImageDraw

from design import *
from project import BUILD

BOT = 1520          # content must stop here - captions live below
ANIM = os.path.join(BUILD, "anim")
os.makedirs(ANIM, exist_ok=True)

C_EYE = (30, 168, 190)      # 超声波 小眼睛
C_MOUTH = (245, 166, 35)    # 小喇叭 小嘴巴
C_BOARD = (54, 162, 105)    # Arduino 大脑
C_KEY = (228, 87, 46)       # 按键 小手指
C_LAMP = (255, 148, 58)     # LED 灯环 小灯笼
C_ALERT = (228, 87, 46)     # 啪 / 红色警示
C_FLAME = (255, 132, 42)    # 橙色发声口
C_AMBER = (245, 166, 35)    # 黄色计时

CREAM_RGB = (248, 242, 228)
FLOOR_C = (231, 219, 194)
FLOOR_D = (214, 199, 170)
CAMO = (58, 62, 72)          # 黑金卡纸
CAMO_D = (34, 37, 44)
CAMO_HI = (96, 100, 114)
GOLD = (206, 162, 66)
PAPER_W = (246, 242, 232)
KRAFT = (196, 160, 108)
KRAFT_D = (156, 120, 74)

GROUND_Y = 1150              # floor line of the test scenes
NOTE_TOP = 1360
DEV_X = 250                  # where the cardboard trap stands
SPREAD = 60.0


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


class SegWriter:
    """Stream RGB frames straight into ffmpeg (no frame buffering)."""

    def __init__(self, name, w=W, h=H, fps=30):
        self.name = name
        self.out = os.path.join(ANIM, name + ".mp4")
        self.n = 0
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", "%dx%d" % (w, h), "-r", str(fps), "-i", "-",
               "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", self.out]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def add(self, frame):
        self.p.stdin.write(frame.convert("RGB").tobytes())
        self.n += 1

    def close(self):
        self.p.stdin.close()
        self.p.wait()
        print("  anim", self.name, self.n, "frames")
        return self.out


def ease(t):
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def wipe_in(img, color, t, dur=0.30):
    """Chapter wipe: an accent sheet slides down, revealing the frame from the top."""
    if t >= dur:
        return
    k = t / dur
    sheet_h = int(H * (1.0 - k)) + 1
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle([0, 0, W, sheet_h], fill=color + (255,))
    img.alpha_composite(lay)


def chip_head(img, text, color=C_EYE, fg=WHITE, size=36):
    return chip(img, MARGIN, 76, text, bg=color, fg=fg, size=size, padx=30, pady=16)


def code_reveal(img, box, lines, title=None, n=1):
    """Dark code card; the first n lines are typed in, one after the other."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=CODE_BG)
    d.rounded_rectangle([x0 + 14, y0 + 14, x1 - 14, y1 - 14], 18, outline=(58, 62, 88), width=3)
    if title:
        d.text((x0 + 48, y0 + 62), title, font=font(34, True), fill=ORANGE, anchor="lm")
        y = y0 + 126
    else:
        y = y0 + 60
    step = (y1 - y - 20) / max(1, len(lines))
    for i in range(min(n, len(lines))):
        txt, col = lines[i]
        yy = y + i * step + step / 2 - 14
        d.rounded_rectangle([x0 + 40, yy - 22, x0 + 48, yy + 20], 4, fill=col or (70, 76, 100))
        draw_code(d, x0 + 68, yy, txt)
    if 0 < n <= len(lines):
        txt = lines[n - 1][0]
        yy = y + (n - 1) * step + step / 2 - 14
        w = 0
        for chx in txt:
            w += d.textlength(chx, font=font(34, False, mono=True)) if ord(chx) <= 0x2E00 \
                else d.textlength(chx, font=font(34, False))
        d.rectangle([x0 + 68 + w + 4, yy - 16, x0 + 68 + w + 16, yy + 16], fill=(120, 230, 180))


def note_bar(img, text, sub=None, accent=ORANGE, top=NOTE_TOP):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([MARGIN, top, W - MARGIN, BOT], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    d.rounded_rectangle([MARGIN + 24, top + 22, MARGIN + 34, BOT - 22], 5, fill=accent)
    d.text((MARGIN + 56, top + 46), text, font=font(33, True), fill=INK, anchor="lm")
    if sub:
        d.text((MARGIN + 56, top + 96), sub, font=font(27, False), fill=INK_SOFT, anchor="lm")


def floor(d, y=GROUND_Y, x0=40, x1=W - 40, color=FLOOR_C):
    d.rectangle([x0, y, x1, BOT], fill=color)
    d.rectangle([x0, y, x1, y + 16], fill=FLOOR_D)
    x = x0 - 40
    while x < x1 + 120:
        d.line([(x, y + 16), (x - 46, BOT)], fill=FLOOR_D, width=3)
        x += 130


def spiral(d, x, y, r, color, width=4, turns=2.4):
    """A little spiral - the cartoon sign of a dizzy head."""
    steps = 56
    for i in range(steps):
        a0 = i * 360.0 / steps * turns
        a1 = (i + 1) * 360.0 / steps * turns
        r0 = r * (i / float(steps)) * 0.95 + 2
        r1 = r * ((i + 1) / float(steps)) * 0.95 + 2
        d.line([(x + r0 * math.cos(math.radians(a0)), y + r0 * math.sin(math.radians(a0))),
                (x + r1 * math.cos(math.radians(a1)), y + r1 * math.sin(math.radians(a1)))],
               fill=color, width=width)


def draw_trap(d, x, ground, led=0.0, speak=0.0, s=1.0, tilt=0.0):
    """The cardboard sound pancake: a flat black disc, gold rim, orange mouth."""
    rx, ry = 122 * s, 40 * s
    cy = ground - 46 * s
    # three folded paper feet
    for lx, ly in ((x - 0.78 * rx, ground - 8 * s), (x + 0.78 * rx, ground - 8 * s),
                   (x + 0.10 * rx, ground - 26 * s)):
        d.line([(x, cy), (lx, ly)], fill=CAMO_D, width=int(13 * s))
        d.line([(x, cy), (lx, ly)], fill=CAMO, width=int(7 * s))
        d.ellipse([lx - 16 * s, ly - 9 * s, lx + 16 * s, ly + 9 * s], fill=CAMO_D)
    # body
    d.ellipse([x - rx, cy - ry, x + rx, cy + ry], fill=PAPER_W, outline=CAMO, width=int(7 * s))
    d.ellipse([x - rx * 0.84, cy - ry * 0.84, x + rx * 0.84, cy + ry * 0.84], fill=CAMO)
    d.ellipse([x - rx * 0.64, cy - ry * 0.64, x + rx * 0.64, cy + ry * 0.64],
              outline=GOLD, width=int(8 * s))
    # the orange mouth in the middle
    mc = mix((96, 98, 106), C_FLAME, min(1.0, speak))
    d.ellipse([x - 34 * s, cy - 17 * s, x + 34 * s, cy + 17 * s], fill=mc,
              outline=(96, 52, 12), width=int(4 * s))
    d.ellipse([x - 16 * s, cy - 8 * s, x + 16 * s, cy + 8 * s], fill=mix(mc, WHITE, 0.35))
    # the LED ring around the rim
    if led > 0.02:
        f = min(1.0, led)
        d.ellipse([x - rx * 0.94, cy - ry * 0.94, x + rx * 0.94, cy + ry * 0.94],
                  outline=mix(PAPER_W, C_LAMP, 0.9 * f), width=int(9 * s))
    return x, cy


def draw_robot(d, x, ground, scale=1.0, walk=0.0, frozen=0.0, dizzy=0.0,
               label=None, card=False, blink=False):
    """A cute paper robot standing in for a target on the field."""
    s = scale
    bob = math.sin(walk * 7.0) * 4 * s * (0.3 if frozen > 0.02 else 1.0)
    swing = math.sin(walk * 7.0) * 16 * s * (0.25 if frozen > 0.02 else 1.0)
    h = 190 * s
    top = ground - h + bob
    for sgn in (-1, 1):
        lx = x + sgn * 20 * s + swing * 0.25 * sgn
        d.rounded_rectangle([lx - 11 * s, ground - 52 * s,
                             lx + 11 * s, ground], 6 * s,
                            fill=(88, 92, 104), outline=(52, 56, 66), width=3)
    d.rounded_rectangle([x - 42 * s, top + 62 * s,
                         x + 42 * s, ground - 44 * s], 16 * s,
                        fill=(250, 250, 246), outline=C_EYE, width=5)
    d.ellipse([x - 22 * s, top + 80 * s,
               x + 22 * s, top + 124 * s], fill=C_EYE)
    for sgn in (-1, 1):
        ax = x + sgn * (46 * s)
        if frozen > 0.02:
            # hands clamped over the ears
            hx = x + sgn * (38 * s)
            hy = top + 46 * s
            d.line([(ax, top + 78 * s), (hx, hy)], fill=(120, 124, 136), width=int(9 * s))
            d.ellipse([hx - 11 * s, hy - 11 * s, hx + 11 * s, hy + 11 * s],
                      fill=(250, 250, 246), outline=C_EYE, width=4)
        else:
            d.line([(ax, top + 78 * s), (ax + sgn * swing * 0.5, top + 120 * s)],
                   fill=(120, 124, 136), width=int(9 * s))
    d.ellipse([x - 38 * s, top, x + 38 * s, top + 70 * s],
              fill=(252, 252, 248), outline=C_EYE, width=5)
    for sgn in (-1, 1):
        ex = x + sgn * 16 * s
        ey = top + 34 * s
        if frozen > 0.02:
            spiral(d, ex, ey, 11 * s, mix((40, 44, 52), C_ALERT, min(1.0, frozen)),
                   width=max(2, int(3 * s)))
        elif blink:
            d.ellipse([ex - 10 * s, ey - 10 * s, ex + 10 * s, ey + 10 * s], fill=(40, 44, 52))
            d.ellipse([ex - 4 * s, ey - 7 * s, ex + 4 * s, ey + 1 * s], fill=WHITE)
        else:
            d.ellipse([ex - 10 * s, ey - 10 * s, ex + 10 * s, ey + 10 * s], fill=(40, 44, 52))
            d.ellipse([ex - 4 * s, ey - 7 * s, ex + 4 * s, ey + 1 * s], fill=WHITE)
    d.line([(x, top), (x + 6 * s, top - 22 * s)], fill=(140, 144, 156), width=int(5 * s))
    d.ellipse([x - 2 * s, top - 32 * s, x + 14 * s, top - 16 * s],
              fill=C_AMBER, outline=(190, 120, 20), width=3)
    if dizzy > 0.02:
        for k in range(3):
            rr = (24 + 20 * k) * s
            fade = max(0.0, min(1.0, dizzy * 1.5 - k * 0.3))
            if fade > 0.05:
                d.arc([x - rr, top - rr, x + rr, top + rr],
                      start=-120, end=-60, fill=mix(CREAM_RGB, C_ALERT, fade),
                      width=int(6 * fade) + 2)
                d.arc([x + 30 * s - rr, top - rr, x + 30 * s + rr, top + rr],
                      start=-120, end=-60, fill=mix(CREAM_RGB, C_ALERT, fade),
                      width=int(6 * fade) + 2)
    if card:
        cxx = x + 48 * s
        cyy = ground - 46 * s
        d.rounded_rectangle([cxx - 15 * s, cyy - 20 * s, cxx + 15 * s, cyy + 20 * s], 4 * s,
                            fill=(255, 214, 102), outline=(200, 150, 40), width=3)
    if label:
        d.text((x, ground + 34), label, font=font(24, True), fill=INK_SOFT, anchor="mm")


def wave_rings(d, cx, cy, phase, maxr=340, rings=3, color=C_LAMP, squash=0.42):
    """Orange sound rings rolling out of the device."""
    for k in range(rings):
        tt = phase - k * 0.18
        if tt <= 0:
            continue
        r = maxr * ease(min(1.0, tt / 0.85))
        fade = max(0.0, 1.0 - tt / 0.95)
        if fade > 0.05:
            d.ellipse([cx - r, cy - r * squash, cx + r, cy + r * squash],
                      outline=mix(CREAM_RGB, color, fade), width=int(11 * fade) + 2)


def blast_circle(d, cx, ground, r, fade=1.0, color=C_LAMP):
    """The 7 metre blast area drawn flat on the floor."""
    pts = [(cx, ground)]
    for a in range(0, 360, 6):
        rad = math.radians(a)
        pts.append((cx + r * math.cos(rad), ground + r * 0.40 * math.sin(rad)))
    d.polygon(pts, fill=mix(FLOOR_C, color, 0.24 * fade))
    d.ellipse([cx - r, ground - r * 0.40, cx + r, ground + r * 0.40],
              outline=mix(FLOOR_C, color, 0.85 * fade), width=5)


def ruler(d, box, cm, thresh=400, maxcm=800, label="距离", unit="cm"):
    """A flat distance ruler with the 4 metre trigger line marked."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    d.text((x0 + 26, y0 + 42), label, font=font(29, True), fill=INK_SOFT, anchor="lm")
    d.text((x1 - 26, y0 + 50), "%d %s" % (int(cm), unit), font=font(46, True),
           fill=C_EYE, anchor="rm")
    lx0, lx1 = x0 + 46, x1 - 46
    ly = y0 + 150
    d.line([(lx0, ly), (lx1, ly)], fill=(190, 196, 200), width=6)
    for k in range(0, maxcm + 1, 100):
        px = lx0 + (lx1 - lx0) * (k / float(maxcm))
        d.line([(px, ly - 11), (px, ly + 11)], fill=(150, 156, 160), width=4)
        d.text((px, ly + 42), str(k // 100), font=font(22, True), fill=INK_SOFT, anchor="mm")
    tx = lx0 + (lx1 - lx0) * (thresh / float(maxcm))
    d.rectangle([tx - 5, ly - 22, tx + 5, ly + 16], fill=C_ALERT)
    d.text((tx, ly - 70), "4 米", font=font(28, True), fill=C_ALERT, anchor="mm")
    mx = lx0 + (lx1 - lx0) * (max(0.0, min(float(maxcm), cm)) / float(maxcm))
    d.polygon([(mx, ly - 16), (mx - 16, ly - 42), (mx + 16, ly - 42)], fill=C_EYE)
    return mx


def pill_row(img, box, items):
    """A row of coloured pills naming the effects the pop causes."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    n = len(items)
    gap = 14
    cw = (x1 - x0 - gap * (n - 1)) / n
    for i, (col, big, small) in enumerate(items):
        x = x0 + i * (cw + gap)
        d.rounded_rectangle([x, y0, x + cw, y1], 24, fill=(255, 253, 246),
                            outline=(228, 216, 192), width=3)
        d.rounded_rectangle([x + 14, y0 + 16, x + 22, y1 - 16], 4, fill=col)
        d.text((x + 38, y0 + 44), big, font=font(30, True), fill=INK, anchor="lm")
        d.text((x + 38, y1 - 38), small, font=font(23, False), fill=INK_SOFT, anchor="lm")


def warp_frame(img, amt, seed=0):
    """The cartoon 'screen warp': the picture wobbles in horizontal bands."""
    if amt <= 0.01:
        return img
    a = np.array(img.convert("RGB"), copy=True)
    h, w = a.shape[:2]
    band = 26
    ys = np.arange(0, h, band)
    offs = (amt * 16 * np.sin(ys * 0.045 + seed)).astype(int)
    for y0, off in zip(ys, offs):
        if off:
            a[y0:y0 + band] = np.roll(a[y0:y0 + band], int(off), axis=1)
    return Image.fromarray(a)


def big_number(d, box, value, label, color=C_EYE, unit=""):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    d.text((x0 + 26, y0 + 38), label, font=font(26, True), fill=INK_SOFT, anchor="lm")
    d.text(((x0 + x1) / 2, y0 + 104), str(value) + unit, font=font(62, True),
           fill=color, anchor="mm")


# ------------------------------------------------------------------ v09
def v09_code_read(dur):
    w = SegWriter("v09_code_read")
    lines = [
        ("long us = sensor.read();  // 读一次", ORANGE),
        ("cm = us / 58;             // 换算成厘米", None),
        ("// 每秒读 10 次", (150, 190, 255)),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.2 else (2 if t < 3.2 else 3)
        chip_head(img, "程序 ① 读距离", C_EYE)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 590), lines, n=n)
        cm = int(760 - 620 * min(1.0, t / max(1.0, dur)))
        ruler(d, (MARGIN, 610, W - MARGIN, 890), cm, label="小眼睛量到的距离")
        floor(d, 1010)
        draw_trap(d, DEV_X, 1010, led=0.35 + 0.35 * math.sin(t * 4.0), s=0.74)
        rx = DEV_X + 300 + (760 - cm) * 0.42
        draw_robot(d, min(1000, rx), 1010, scale=0.56, walk=t * 3.0)
        d.text((DEV_X, 1130), "装置在这儿", font=font(24, True), fill=INK_SOFT, anchor="mm")
        note_bar(img, "声波跑出去再跑回来", "回来的时间 ÷ 2，就是它离你多远", accent=C_EYE)
        wipe_in(img, C_EYE, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v10
def v10_code_judge(dur):
    w = SegWriter("v10_code_judge")
    lines = [
        ("if (cm < 400) { fire = true; }", ORANGE),
        ("if (now - last < 1000) return;", None),
        ("tone(BUZZ);   // 滴滴，7 米外听不见", None),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.3 else (2 if t < 3.4 else 3)
        chip_head(img, "程序 ② 判断 4 米", C_MOUTH, INK)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 590), lines, n=n)
        k = min(1.0, t / max(1.0, dur * 0.72))
        cm = int(720 - 520 * k)
        fired = cm < 400
        ruler(d, (MARGIN, 610, W - MARGIN, 890), cm, label="离得够近了吗？")
        floor(d, 1010)
        draw_trap(d, DEV_X, 1010, led=(0.95 if fired else 0.25),
                  speak=(0.9 if fired else 0.0), s=0.74)
        rx = DEV_X + 300 + (720 - cm) * 0.36
        draw_robot(d, min(880, rx), 1010, scale=0.56, walk=t * 3.0)
        if fired:
            d.rounded_rectangle([W - MARGIN - 230, 960, W - MARGIN, 1056], 24, fill=C_ALERT)
            d.text((W - MARGIN - 115, 1008), "触发！", font=font(46, True),
                   fill=WHITE, anchor="mm")
        d.text((DEV_X, 1130), "小于 4 米才响", font=font(24, True), fill=INK_SOFT, anchor="mm")
        note_bar(img, "小于 4 米才触发，一秒只响一次", "滴滴声在 7 米外就听不见啦", accent=C_MOUTH)
        wipe_in(img, C_MOUTH, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v11
def v11_code_effect(dur):
    w = SegWriter("v11_code_effect")
    lines = [
        ("tone(POP);      // 啪的一声", ORANGE),
        ("freeze(2000);  // 愣住 2 秒", None),
        ("slow(50);      // 走路变慢", None),
        ("warp();        // 耳鸣 + 屏幕扭曲", None),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.2 else (2 if t < 3.0 else (3 if t < 4.6 else 4))
        chip_head(img, "程序 ③ 产生效果", C_ALERT, WHITE)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 610), lines, n=n)
        pop = 0.0
        for ts in (2.6, 6.4):
            if t > ts:
                pop = max(0.0, 1.0 - (t - ts) / 0.55)
        frozen = 0.0
        if t > 2.6:
            frozen = max(0.0, min(1.0, (t - 2.6) / 0.35))
            frozen = min(frozen, max(0.0, 1.0 - (t - 4.9) / 0.6))
        pill_row(img, (MARGIN, 630, W - MARGIN, 750), [
            (C_ALERT, "愣住 2 秒", "站住不动"),
            (C_MOUTH, "减速", "走路变慢"),
            (C_LAMP, "耳鸣", "耳朵嗡嗡响"),
            (C_EYE, "屏幕扭曲", "画面抖一抖"),
        ])
        floor(d, 1060)
        draw_trap(d, 300, 1060, led=0.9 if pop else 0.3, speak=pop, s=0.8)
        if pop > 0.02:
            wave_rings(d, 300, 1060 - 37, (t - 2.6) % 1.2, maxr=280, rings=3)
        draw_robot(d, 790, 1060, scale=0.8, walk=t * 3.0, frozen=frozen,
                   dizzy=min(1.0, max(0.0, (t - 2.8))),
                   card=(frozen < 0.1 and t > 3.4))
        if frozen > 0.5:
            d.rounded_rectangle([600, 790, 960, 856], 22, fill=C_ALERT)
            d.text((780, 823), "愣住 2 秒", font=font(36, True), fill=WHITE, anchor="mm")
        note_bar(img, "不伤人，只把纸机器人震愣住", "手里的动作被打断，卡片掉下来", accent=C_ALERT)
        img = warp_frame(img, max(0.0, 0.35 - abs(t - 3.2)) if t > 2.6 else 0.0, t)
        wipe_in(img, C_ALERT, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v14
def v14_test_beep(dur):
    w = SegWriter("v14_test_beep")
    lines = [
        ("tone(BUZZ);   // 放好就滴滴响", ORANGE),
        ("// 7 米外就听不见了", (150, 190, 255)),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.2 else 2
        chip_head(img, "实测 ① 滴滴声能听多远", C_LAMP, INK)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 400), lines, n=n)
        walk = min(1.0, t / max(1.0, dur * 0.75))
        ruler(d, (MARGIN, 600, W - MARGIN, 880), int(300 + 700 * walk),
              label="我们退了多远", unit="cm")
        floor(d, 1120)
        blink = 0.5 + 0.5 * math.sin(t * 6.0)
        draw_trap(d, DEV_X, 1120, led=blink, speak=0.5 * blink, s=0.8)
        rx = DEV_X + 280 + 380 * walk
        draw_robot(d, rx, 1120, scale=0.7, walk=t * 3.0)
        ex, ey = rx + 98, 1030
        fade = max(0.0, min(1.0, 1.0 - (walk - 0.55) / 0.45))
        d.ellipse([ex - 42, ey - 42, ex + 42, ey + 42], fill=mix(CREAM_RGB, C_EYE, fade),
                  outline=(18, 110, 128), width=5)
        d.arc([ex - 23, ey - 23, ex + 23, ey + 23], start=120, end=420, fill=WHITE, width=7)
        for k in range(3):
            rr = 52 + 24 * k
            af = max(0.0, fade - k * 0.25)
            if af > 0.05:
                d.arc([ex - rr, ey - rr, ex + rr, ey + rr], start=-60, end=60,
                      fill=mix(CREAM_RGB, C_LAMP, af), width=int(6 * af) + 2)
        lx = DEV_X + 280 + 380 * 0.72
        d.line([(lx, 900), (lx, 1260)], fill=C_ALERT, width=5)
        d.rounded_rectangle([lx - 78, 900, lx + 78, 966], 20, fill=C_ALERT)
        d.text((lx, 933), "7 米", font=font(30, True), fill=WHITE, anchor="mm")
        if walk > 0.72:
            d.rounded_rectangle([MARGIN, 900, MARGIN + 300, 975], 22, fill=(58, 62, 72))
            d.text((MARGIN + 150, 937), "听不见了！", font=font(34, True),
                   fill=WHITE, anchor="mm")
        note_bar(img, "退到 7 米外，就听不见滴滴声了", "所以别放太近，不然自己先暴露", accent=C_LAMP)
        wipe_in(img, C_LAMP, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v15
def v15_test_trigger(dur):
    w = SegWriter("v15_test_trigger")
    lines = [
        ("if (cm < 400) fire();", ORANGE),
        ("freeze(2000);  // 愣住 2 秒", None),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.2 else 2
        chip_head(img, "实测 ② 走进 4 米就触发", C_ALERT, WHITE)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 400), lines, n=n)
        walk = min(1.0, t / max(1.0, dur * 0.42))
        cm = int(700 - 300 * walk)
        ruler(d, (MARGIN, 600, W - MARGIN, 880), cm, label="它现在有多近")
        floor(d, 1120)
        lx = DEV_X + 320 + 300 * 0.46
        rx = lx + (1.0 - walk) * 300
        pop = 0.0
        if t > dur * 0.46:
            pop = max(0.0, 1.0 - (t - dur * 0.46) / (dur * 0.30))
        frozen = 0.0
        if t > dur * 0.46:
            frozen = max(0.0, min(1.0, (t - dur * 0.46) / 0.22))
            frozen = min(frozen, max(0.0, 1.0 - (t - dur * 0.86) / (dur * 0.12)))
        draw_trap(d, DEV_X, 1120, led=(0.9 if pop else 0.3), speak=pop, s=0.8)
        if pop > 0.02:
            wave_rings(d, DEV_X, 1120 - 37, (t - dur * 0.46) % 0.95, maxr=330, rings=3)
        drop = t > dur * 0.62
        draw_robot(d, rx, 1120, scale=0.7, walk=t * 3.0, frozen=frozen,
                   dizzy=min(1.0, max(0.0, (t - dur * 0.48))), card=not drop)
        if drop:
            d.rounded_rectangle([rx - 74, 1106, rx - 46, 1162], 4,
                                fill=(255, 214, 102), outline=(200, 150, 40), width=3)
        d.line([(lx, 900), (lx, 1260)], fill=C_ALERT, width=5)
        d.rounded_rectangle([lx - 74, 890, lx + 74, 954], 20, fill=C_ALERT)
        d.text((lx, 922), "4 米", font=font(30, True), fill=WHITE, anchor="mm")
        if frozen > 0.45:
            d.rounded_rectangle([MARGIN + 30, 966, MARGIN + 330, 1042], 22, fill=C_ALERT)
            d.text((MARGIN + 180, 1004), "愣住 2 秒！", font=font(36, True),
                   fill=WHITE, anchor="mm")
        note_bar(img, "啪！它当场愣住 2 秒", "捂耳朵、走路变慢，手里的卡片掉了", accent=C_ALERT)
        img = warp_frame(img, max(0.0, 0.30 - abs(t - dur * 0.55)) if pop > 0 else 0.0, t)
        wipe_in(img, C_ALERT, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v16
def v16_test_manual(dur):
    w = SegWriter("v16_test_manual")
    lines = [
        ("if (key == 'H') { blast(); }", ORANGE),
        ("// 手动引爆，范围更大", (150, 190, 255)),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.2 else 2
        chip_head(img, "实测 ③ 按 H 手动引爆", C_BOARD, WHITE)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 400), lines, n=n)
        floor(d, 1090)
        blast = 0.0
        if t > dur * 0.30:
            blast = max(0.0, 1.0 - (t - dur * 0.30) / (dur * 0.42))
        CX = 400
        R = 300
        blast_circle(d, CX, 1090, R, fade=0.35 + 0.65 * blast)
        d.line([(CX, 1090), (CX + R, 1090)], fill=(90, 96, 104), width=5)
        d.text((CX + R / 2, 1050), "7 米", font=font(30, True), fill=INK_SOFT, anchor="mm")
        frozen = 0.0
        if t > dur * 0.34:
            frozen = min(1.0, (t - dur * 0.34) / 0.22)
        draw_trap(d, CX, 1090, led=0.9 if blast else 0.3, speak=blast, s=0.82)
        if blast > 0.02:
            wave_rings(d, CX, 1090 - 38, (t - dur * 0.30) % 1.1, maxr=340, rings=3)
        draw_robot(d, CX + 150, 1090, scale=0.68, frozen=frozen,
                   dizzy=frozen, label="圈里")
        draw_robot(d, CX + 560, 1090, scale=0.68, walk=t * 3.0, label="圈外")
        kx, ky = 520, 600
        press = 1.0 if (t > dur * 0.16 and t < dur * 0.30) else 0.0
        r = 88 - 12 * press
        d.ellipse([kx - r, ky - r, kx + r, ky + r], fill=mix((214, 218, 226), C_KEY, press),
                  outline=CAMO_D, width=6)
        d.text((kx, ky), "H", font=font(80, True), fill=WHITE, anchor="mm")
        d.text((kx, ky + 120), "手动引爆", font=font(28, True), fill=INK_SOFT, anchor="mm")
        if frozen > 0.4:
            d.rounded_rectangle([720, 542, 1016, 620], 22, fill=C_ALERT)
            d.text((868, 581), "圈内：全部愣住", font=font(32, True),
                   fill=WHITE, anchor="mm")
        note_bar(img, "按一下 H，炸开 7 米的大圈", "圈里的愣住，圈外的安然无恙", accent=C_BOARD)
        wipe_in(img, C_BOARD, t, 0.30)
        w.add(img)
    return w.close()


def build_anims(segdur):
    """Render every animated segment to its exact narration length."""
    return {
        "v09_code_read": v09_code_read(segdur["v09_code_read"]),
        "v10_code_judge": v10_code_judge(segdur["v10_code_judge"]),
        "v11_code_effect": v11_code_effect(segdur["v11_code_effect"]),
        "v14_test_beep": v14_test_beep(segdur["v14_test_beep"]),
        "v15_test_trigger": v15_test_trigger(segdur["v15_test_trigger"]),
        "v16_test_manual": v16_test_manual(segdur["v16_test_manual"]),
    }
