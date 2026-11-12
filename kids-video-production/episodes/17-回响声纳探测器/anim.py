# -*- coding: utf-8 -*-
"""anim.py - the animated segments for the 回响·回声探测器 film.

  * v09_code_read   - program 1: the little ear reads the volume
  * v10_code_judge  - program 2: over the threshold? turn the radar head
  * v11_code_share  - program 3: red lamp, yellow bar, squad-shared lamp
  * v14_test_scan   - live test: the radar head sweeps a 120 degree cone
  * v15_test_mark   - live test: the walking robot is heard and marked
  * v16_test_quiet  - live test: the silent robot is never marked

Every segment is cut to the exact length of its narration beat, so picture
and voice stay locked.  Nothing here is a real sonar: the "device" is a
cardboard tripod, the waves are drawn arcs and the only measurement is a
toy microphone reading a harmless volume number.
"""
import os
import math
import random
import subprocess

from PIL import Image, ImageDraw

from design import *
from project import BUILD

BOT = 1520          # content must stop here - captions live below
ANIM = os.path.join(BUILD, "anim")
os.makedirs(ANIM, exist_ok=True)

C_EAR = (30, 168, 190)      # 声音传感器 小耳朵
C_NECK = (245, 166, 35)     # 小舵机 小脖子
C_BOARD = (54, 162, 105)    # Arduino 大脑
C_KEY = (228, 87, 46)       # 按键 小手指
C_LAMP = (120, 190, 245)    # LED 灯环 小灯笼
C_ALERT = (228, 87, 46)     # 红色被标记
C_AMBER = (245, 166, 35)    # 黄色读条

CREAM_RGB = (248, 242, 228)
FLOOR_C = (231, 219, 194)
FLOOR_D = (214, 199, 170)
CAMO = (58, 62, 72)          # 黑灰迷彩卡纸
CAMO_D = (34, 37, 44)
CAMO_HI = (96, 100, 114)
PAPER_W = (246, 242, 232)
KRAFT = (196, 160, 108)
KRAFT_D = (156, 120, 74)

GROUND_Y = 1150              # floor line of the test scenes
NOTE_TOP = 1360
DEV_X = 232                  # where the cardboard tripod stands
SPREAD = 60.0                # half of the 120 degree sector


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


def chip_head(img, text, color=C_EAR, fg=WHITE, size=36):
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


def cover_box(d, x, ground, w=104, h=126):
    """A cardboard box used as cover on the test field."""
    d.rounded_rectangle([x - w / 2, ground - h, x + w / 2, ground], 8,
                        fill=KRAFT, outline=KRAFT_D, width=5)
    d.line([(x - w / 2 + 6, ground - h * 0.52), (x + w / 2 - 6, ground - h * 0.52)],
           fill=KRAFT_D, width=4)
    d.line([(x, ground - h + 8), (x, ground - 8)], fill=KRAFT_D, width=4)


def draw_robot(d, x, ground, marked=0.0, walk=0.0, noisy=0.0, scale=1.0, label=None):
    """A cute paper robot that stands in for a target on the field."""
    bob = math.sin(walk * 7.0) * 5 * scale
    swing = math.sin(walk * 7.0) * 18 * scale
    h = 190 * scale
    top = ground - h + bob
    for sgn in (-1, 1):
        lx = x + sgn * 20 * scale + swing * 0.25 * sgn
        d.rounded_rectangle([lx - 11 * scale, ground - 52 * scale,
                             lx + 11 * scale, ground], 6 * scale,
                            fill=(88, 92, 104), outline=(52, 56, 66), width=3)
    d.rounded_rectangle([x - 42 * scale, top + 62 * scale,
                         x + 42 * scale, ground - 44 * scale], 16 * scale,
                        fill=(250, 250, 246), outline=C_EAR, width=5)
    d.ellipse([x - 22 * scale, top + 80 * scale,
               x + 22 * scale, top + 124 * scale], fill=C_EAR)
    for sgn in (-1, 1):
        ax = x + sgn * (46 * scale)
        d.line([(ax, top + 78 * scale), (ax + sgn * swing * 0.5, top + 120 * scale)],
               fill=(120, 124, 136), width=int(9 * scale))
    d.ellipse([x - 38 * scale, top, x + 38 * scale, top + 70 * scale],
              fill=(252, 252, 248), outline=C_EAR, width=5)
    for sgn in (-1, 1):
        ex = x + sgn * 16 * scale
        d.ellipse([ex - 10 * scale, top + 24 * scale,
                   ex + 10 * scale, top + 44 * scale], fill=(40, 44, 52))
        d.ellipse([ex - 4 * scale, top + 27 * scale,
                   ex + 4 * scale, top + 35 * scale], fill=WHITE)
    d.line([(x, top), (x + 6 * scale, top - 22 * scale)], fill=(140, 144, 156),
           width=int(5 * scale))
    d.ellipse([x - 2 * scale, top - 32 * scale, x + 14 * scale, top - 16 * scale],
              fill=C_AMBER, outline=(190, 120, 20), width=3)
    if noisy > 0.02:
        for k in range(3):
            rr = (26 + 22 * k) * scale
            fade = max(0.0, min(1.0, noisy * 1.5 - k * 0.3))
            if fade > 0.05:
                d.arc([x - rr, top - rr, x + rr, top + rr],
                      start=-120, end=-60, fill=mix(CREAM_RGB, C_AMBER, fade),
                      width=int(6 * fade) + 2)
                d.arc([x + 30 * scale - rr, top - rr, x + 30 * scale + rr, top + rr],
                      start=-120, end=-60, fill=mix(CREAM_RGB, C_AMBER, fade),
                      width=int(6 * fade) + 2)
    if marked > 0.02:
        fade = min(1.0, marked)
        my = top - 52 * scale
        d.ellipse([x - 56 * scale, my - 22 * scale,
                   x + 56 * scale, my + 22 * scale],
                  outline=mix(CREAM_RGB, C_ALERT, fade), width=int(6 * fade) + 2)
        d.rounded_rectangle([x - 50 * scale, my - 66 * scale,
                             x + 50 * scale, my - 26 * scale],
                            14 * scale, fill=mix(CREAM_RGB, C_ALERT, fade))
        d.text((x, my - 46 * scale), "已标记", font=font(int(26 * scale), True),
               fill=WHITE if fade > 0.5 else INK, anchor="mm")
    if label:
        d.text((x, ground + 34), label, font=font(24, True), fill=INK_SOFT, anchor="mm")


def draw_sonar(d, x, ground, ang=0.0, led=0.0, speak=0.0, mic=0.0):
    """The cardboard tripod sonar detector: base, tube and rotating antenna head."""
    for lx in (x - 118, x + 118):
        d.line([(x, ground - 210), (lx, ground - 6)], fill=CAMO_D, width=24)
        d.line([(x, ground - 210), (lx, ground - 6)], fill=CAMO, width=14)
    d.ellipse([x - 138, ground - 16, x - 98, ground + 14], fill=CAMO_D)
    d.ellipse([x + 98, ground - 16, x + 138, ground + 14], fill=CAMO_D)
    d.ellipse([x - 106, ground - 44, x + 106, ground + 8], fill=PAPER_W,
              outline=CAMO, width=5)
    d.ellipse([x - 80, ground - 40, x + 80, ground - 6], outline=CAMO_HI, width=3)
    top = ground - 430
    d.rounded_rectangle([x - 74, top, x + 74, ground - 190], 16,
                        fill=PAPER_W, outline=CAMO, width=5)
    for k in range(3):
        yy = top + 48 + k * 54
        d.rectangle([x - 70, yy, x + 70, yy + 20], fill=CAMO)
    led_col = mix(PAPER_W, (94, 214, 130), min(1.0, led))
    d.ellipse([x - 88, top - 26, x + 88, top + 20], fill=led_col, outline=CAMO_D, width=5)
    if led > 0.05:
        d.ellipse([x - 106, top - 46, x + 106, top + 40],
                  outline=mix(PAPER_W, (94, 214, 130), 0.45 * min(1.0, led)), width=6)
    hx, hy = x, top - 54
    d.ellipse([hx - 62, hy - 48, hx + 62, hy + 40], fill=CAMO, outline=CAMO_D, width=5)
    for sgn in (-1, 1):
        ex = hx + sgn * 64
        ey = hy - 14
        ec = mix((150, 160, 168), C_EAR, min(1.0, mic)) if sgn > 0 else (150, 160, 168)
        d.ellipse([ex - 17, ey - 19, ex + 17, ey + 15], fill=ec, outline=(16, 104, 120), width=4)
    ca, sa = math.cos(ang), math.sin(ang)
    ax1, ay1 = hx - 196 * ca, hy - 26 * sa
    ax2, ay2 = hx + 196 * ca, hy + 26 * sa
    d.line([(ax1, ay1), (ax2, ay2)], fill=CAMO_D, width=22)
    d.line([(ax1, ay1), (ax2, ay2)], fill=CAMO_HI, width=13)
    for (px_, py_) in ((ax1, ay1), (ax2, ay2)):
        d.ellipse([px_ - 23, py_ - 17, px_ + 23, py_ + 17], fill=CAMO,
                  outline=CAMO_D, width=4)
        d.ellipse([px_ - 9, py_ - 7, px_ + 9, py_ + 7], fill=C_EAR)
    if speak > 0.02:
        for k in range(3):
            rr = 24 + 20 * k
            fade = max(0.0, min(1.0, speak * 1.6 - k * 0.34))
            if fade > 0.05:
                d.arc([x + 40, hy - rr, x + 40 + rr, hy + rr],
                      start=-58, end=58, fill=mix(CREAM_RGB, C_ALERT, fade),
                      width=int(7 * fade) + 2)
    return hx, hy


def radar_cone(d, x, ground, ang, reach=470, spread=SPREAD, alpha=1.0):
    """The 120 degree fan on the floor in front of the device."""
    pts = [(x, ground)]
    for a in range(-int(spread), int(spread) + 1, 4):
        r = math.radians(a) + ang
        pts.append((x + reach * math.cos(r), ground + reach * 0.40 * math.sin(r)))
    d.polygon(pts, fill=mix(FLOOR_C, C_EAR, 0.20 * alpha))
    edge = pts[1:]
    for i in range(0, len(edge) - 1, 4):
        d.line([edge[i], edge[i + 1]], fill=mix(FLOOR_C, C_EAR, 0.75 * alpha), width=4)


def scan_rings(d, hx, hy, ang, phase, maxr=330, rings=3):
    """Blue arcs that fly out of the head each time the sweep passes the middle."""
    for k in range(rings):
        tt = phase - k * 0.16
        if tt <= 0:
            continue
        r = maxr * ease(min(1.0, tt / 0.85))
        fade = max(0.0, 1.0 - tt / 0.95)
        if fade > 0.05:
            d.arc([hx - r * 1.15, hy - r * 0.72, hx + r * 1.15, hy + r * 0.72],
                  start=math.degrees(ang) - SPREAD, end=math.degrees(ang) + SPREAD,
                  fill=mix(CREAM_RGB, C_EAR, fade), width=int(10 * fade) + 2)


def sweep_ang(t, period=3.4, span=SPREAD):
    """The radar head rocks from -60 to +60 degrees and back."""
    k = (t % period) / period
    if k < 0.5:
        a = -span + 2 * span * (k / 0.5)
    else:
        a = span - 2 * span * ((k - 0.5) / 0.5)
    return math.radians(a)


def ally_lamp(d, x, ground, on=0.0):
    """The squad-mate's little lamp - the stand-in for the shared marker."""
    d.line([(x, ground), (x, ground - 130)], fill=CAMO_D, width=12)
    d.line([(x, ground), (x, ground - 130)], fill=CAMO, width=7)
    d.rounded_rectangle([x - 46, ground - 200, x + 46, ground - 126], 12,
                        fill=PAPER_W, outline=CAMO, width=4)
    col = mix(PAPER_W, C_ALERT, min(1.0, on))
    d.ellipse([x - 25, ground - 186, x + 25, ground - 140], fill=col,
              outline=CAMO_D, width=4)
    if on > 0.05:
        d.ellipse([x - 38, ground - 198, x + 38, ground - 128],
                  outline=mix(PAPER_W, C_ALERT, 0.5 * min(1.0, on)), width=6)
    d.text((x + 34, ground - 100), "队友", font=font(25, True), fill=INK_SOFT, anchor="mm")


def bar_sign(d, x, ground, ratio, label="读条"):
    """The little yellow progress sign standing next to the device."""
    d.rounded_rectangle([x - 84, ground - 168, x + 84, ground - 66], 14,
                        fill=WHITE, outline=CAMO_D, width=4)
    d.text((x, ground - 146), label, font=font(23, True), fill=INK_SOFT, anchor="mm")
    d.rounded_rectangle([x - 66, ground - 120, x + 66, ground - 88], 14, fill=(226, 222, 212))
    ratio = max(0.0, min(1.0, ratio))
    if ratio > 0.02:
        d.rounded_rectangle([x - 66, ground - 120, x - 66 + 132 * ratio, ground - 88],
                            12, fill=C_AMBER)


def vol_meter(d, box, value, threshold=600, label="音量"):
    """A bar meter with the threshold marked, so the number means something."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    d.text((x0 + 26, y0 + 40), label, font=font(29, True), fill=INK_SOFT, anchor="lm")
    d.text((x1 - 26, y0 + 40), "阈值 %d" % threshold, font=font(26, True),
           fill=INK_SOFT, anchor="rm")
    bx0, bx1 = x0 + 26, x1 - 26
    by0, by1 = y0 + 68, y0 + 116
    d.rounded_rectangle([bx0, by0, bx1, by1], 22, fill=(226, 222, 212))
    ratio = max(0.0, min(1.0, value / 1000.0))
    fx = bx0 + (bx1 - bx0) * ratio
    col = C_ALERT if value > threshold else C_EAR
    if fx > bx0 + 8:
        d.rounded_rectangle([bx0, by0, fx, by1], 20, fill=col)
    tx = bx0 + (bx1 - bx0) * (threshold / 1000.0)
    d.line([(tx, by0 - 12), (tx, by1 + 12)], fill=INK, width=5)
    d.text((tx, by1 + 44), "%d" % threshold, font=font(26, True), fill=INK, anchor="mm")


def big_number(d, box, value, label, color=C_EAR):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    d.text((x0 + 26, y0 + 38), label, font=font(26, True), fill=INK_SOFT, anchor="lm")
    d.text(((x0 + x1) / 2, y0 + 108), str(value), font=font(66, True), fill=color, anchor="mm")


def ear_icon(d, x, y, r, hot=0.0):
    """The cute little ear that does the listening."""
    col = mix((206, 212, 218), C_EAR, min(1.0, hot))
    d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(18, 110, 128), width=5)
    d.arc([x - r * 0.55, y - r * 0.55, x + r * 0.55, y + r * 0.55],
          start=120, end=420, fill=(255, 255, 255), width=8)
    d.ellipse([x - r * 0.55, y + r * 0.10, x - r * 0.10, y + r * 0.55], fill=(255, 255, 255))


def radar_dial(d, box, ang, label="雷达盘"):
    """A little dial showing where the head is pointing."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    cx, cy = x0 + 150, y1 - 78
    R = 76
    d.arc([cx - R, cy - R, cx + R, cy + R], start=200, end=340, fill=(190, 196, 200), width=8)
    for k in (-1, 0, 1):
        a = math.radians(k * 40)
        d.line([(cx + 70 * math.cos(a), cy + 70 * math.sin(a)),
                (cx + 92 * math.cos(a), cy + 92 * math.sin(a))],
               fill=(190, 196, 200), width=4)
    d.line([(cx, cy), (cx + 78 * math.cos(ang), cy + 78 * math.sin(ang))],
           fill=C_EAR, width=9)
    d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=CAMO, outline=CAMO_D, width=4)
    d.text((x0 + 270, y0 + 42), label, font=font(29, True), fill=INK_SOFT, anchor="lm")
    d.text((x0 + 270, y0 + 100), "角度 %d 度" % int(round(math.degrees(ang))),
           font=font(34, True), fill=C_EAR, anchor="lm")
    d.text((x0 + 270, y0 + 152), "转到有声音的方向就停住", font=font(24, False),
           fill=INK_SOFT, anchor="lm")


def hud_count(d, x, y, n, label="敌人数量"):
    """A tiny game-style counter card in the corner."""
    d.rounded_rectangle([x - 116, y - 54, x + 116, y + 54], 18,
                        fill=(26, 30, 38), outline=(70, 76, 100), width=3)
    d.text((x - 96, y - 24), label, font=font(24, True), fill=(160, 170, 190), anchor="lm")
    d.text((x - 96, y + 20), str(n), font=font(42, True), fill=(255, 190, 90), anchor="lm")
    for k in range(6):
        h = 8 + 26 * abs(math.sin(k * 1.1 + 0.4))
        d.rounded_rectangle([x + 8 + k * 17, y + 22 - h, x + 20 + k * 17, y + 22], 4,
                            fill=(120, 210, 230))


# ------------------------------------------------------------------ v09
def v09_code_read(dur):
    w = SegWriter("v09_code_read")
    lines = [
        ("int v = mic.read();   // 读一次音量", ORANGE),
        ("peak = max(peak, v);  // 记住最大的那个", None),
        ("// 一秒钟读 100 次", (150, 190, 255)),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.2 else (2 if t < 3.4 else (3 if t < 5.0 else 3))
        chip_head(img, "程序 ① 读音量", C_EAR)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 640), lines, n=n)
        val = 180 + int(150 * abs(math.sin(t * 5.3)) + 120 * abs(math.sin(t * 1.7)))
        vol_meter(d, (MARGIN, 680, W - MARGIN, 900), val)
        ear_icon(d, MARGIN + 110, 1046, 66, hot=min(1.0, val / 700.0))
        d.text((MARGIN + 220, 1014), "小耳朵竖起来啦", font=font(34, True), fill=INK, anchor="lm")
        d.text((MARGIN + 220, 1068), "每秒听 100 次，记下最大的音量",
               font=font(26, False), fill=INK_SOFT, anchor="lm")
        big_number(d, (W - MARGIN - 280, 976, W - MARGIN, 1120), val, "当前音量", C_EAR)
        note_bar(img, "音量越大，说明附近越吵", "读进来的是数字，不是真的耳朵", accent=C_EAR)
        wipe_in(img, C_EAR, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v10
def v10_code_judge(dur):
    w = SegWriter("v10_code_judge")
    lines = [
        ("if (peak > 600) { found = true; }", ORANGE),
        ("dir = radarDir();    // 声音从哪来", None),
        ("servo.write(dir);   // 雷达盘转过去", None),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.4 else (2 if t < 3.8 else 3)
        chip_head(img, "程序 ② 判断有没有声音", C_NECK, INK)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 640), lines, n=n)
        val = 240 + int(520 * abs(math.sin(t * 2.1)))
        vol_meter(d, (MARGIN, 680, W - MARGIN, 900), val)
        ang = math.radians(-28 + 46 * math.sin(t * 1.1))
        radar_dial(d, (MARGIN, 940, W - MARGIN, 1160), ang)
        note_bar(img, "超过 600 就算有声音", "顺便记下它是从哪个方向传来的", accent=C_NECK)
        wipe_in(img, C_NECK, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v11
def v11_code_share(dur):
    w = SegWriter("v11_code_share")
    lines = [
        ("ledR.write(HIGH);    // 红灯亮", ORANGE),
        ("tone(BUZZ);          // 喇叭喊发现声音", None),
        ("bar.fill(100);       // 黄色读条", None),
        ("squad.send();        // 全队共享", None),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.2 else (2 if t < 3.0 else (3 if t < 4.8 else 4))
        chip_head(img, "程序 ③ 报告给队友", C_BOARD, WHITE)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 700), lines, n=n)
        # three lamps that switch on one after another
        lamps = [(C_ALERT, "红灯亮", "被标记了"),
                 (C_AMBER, "读条拉满", "敌人看得见"),
                 (C_BOARD, "队友小灯", "全队共享")]
        for k, (col, big, small) in enumerate(lamps):
            on = 0.0
            if n >= 4 and t > 5.0 + k * 0.7:
                on = min(1.0, (t - 5.0 - k * 0.7) / 0.4)
            x = MARGIN + k * ((W - 2 * MARGIN) / 3)
            cw = (W - 2 * MARGIN) / 3 - 16
            d.rounded_rectangle([x, 750, x + cw, 950], 26, fill=(255, 253, 246),
                                outline=(228, 216, 192), width=3)
            d.ellipse([x + cw / 2 - 46, 786, x + cw / 2 + 46, 878],
                      fill=mix((226, 222, 212), col, on), outline=CAMO_D, width=4)
            if on > 0.05:
                d.ellipse([x + cw / 2 - 60, 772, x + cw / 2 + 60, 892],
                          outline=mix((255, 253, 246), col, 0.5 * on), width=6)
            d.text((x + cw / 2, 906), big, font=font(28, True), fill=INK, anchor="mm")
            d.text((x + cw / 2, 936), small, font=font(21, False), fill=INK_SOFT, anchor="mm")
        ratio = 0.0
        if n >= 3:
            ratio = min(1.0, max(0.0, (t - 4.6) / 1.2))
        d.rounded_rectangle([MARGIN, 1000, W - MARGIN, 1140], 26, fill=(255, 253, 246),
                            outline=(228, 216, 192), width=3)
        d.text((MARGIN + 26, 1032), "黄色读条", font=font(27, True), fill=INK_SOFT, anchor="lm")
        bx0, bx1 = MARGIN + 26, W - MARGIN - 26
        d.rounded_rectangle([bx0, 1066, bx1, 1112], 20, fill=(226, 222, 212))
        if ratio > 0.02:
            d.rounded_rectangle([bx0, 1066, bx0 + (bx1 - bx0) * ratio, 1112], 18, fill=C_AMBER)
        d.text((bx0, 1132), "队友那边也会亮", font=font(23, False), fill=INK_SOFT, anchor="lm")
        note_bar(img, "红灯亮，喇叭喊，读条拉满", "队友那边的小灯也跟着亮", accent=C_BOARD)
        wipe_in(img, C_BOARD, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v14
def v14_test_scan(dur):
    w = SegWriter("v14_test_scan")
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        chip_head(img, "落地实测 · 雷达盘转起来", GREEN, WHITE)
        d.text((MARGIN, 206), "雷达盘转起来啦！", font=font(54, True), fill=INK, anchor="lm")
        d.text((MARGIN, 270), "前方 120 度扇形，一圈一圈慢慢扫", font=font(30, False),
               fill=INK_SOFT, anchor="lm")
        floor(d)
        ang = sweep_ang(t)
        radar_cone(d, DEV_X, GROUND_Y, ang)
        for bx in (520, 640):
            cover_box(d, bx, GROUND_Y)
        hx, hy = draw_sonar(d, DEV_X, GROUND_Y, ang, led=0.15 + 0.1 * math.sin(t * 4),
                            mic=min(1.0, 0.4 + 0.3 * abs(math.sin(t * 3))))
        phase = (t % 1.7) / 1.7
        scan_rings(d, hx, hy, ang, phase)
        draw_robot(d, 752, GROUND_Y, walk=t * 0.6, noisy=0.0, label="会动的")
        draw_robot(d, 902, GROUND_Y, walk=0.0, noisy=0.0, label="安静的")
        d.text((MARGIN, 1290), "游戏里是 75 米", font=font(28, True), fill=C_EAR, anchor="lm")
        d.text((MARGIN + 210, 1290), "咱们在桌面上就是几米", font=font(26, False),
               fill=INK_SOFT, anchor="lm")
        note_bar(img, "小耳朵一边转一边听", "只听声音，不看东西", accent=C_EAR)
        wipe_in(img, GREEN, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v15
def v15_test_mark(dur):
    w = SegWriter("v15_test_mark")
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        chip_head(img, "落地实测 · 有人被标记啦", RED, WHITE)
        d.text((MARGIN, 206), "听见脚步声了！", font=font(54, True), fill=INK, anchor="lm")
        d.text((MARGIN, 270), "移动、开枪、用技能，都会发出声音", font=font(30, False),
               fill=INK_SOFT, anchor="lm")
        floor(d)
        ang = sweep_ang(t)
        radar_cone(d, DEV_X, GROUND_Y, ang)
        for bx in (520, 640):
            cover_box(d, bx, GROUND_Y)
        hx, hy = draw_sonar(d, DEV_X, GROUND_Y, ang, led=0.0, mic=1.0)
        phase = (t % 1.7) / 1.7
        scan_rings(d, hx, hy, ang, phase)
        mark = 0.0
        if t > 3.0:
            mark = min(1.0, (t - 3.0) / 0.6)
        walk = t * 1.5
        noisy = max(0.0, min(1.0, (t - 2.2) / 0.8)) if t > 2.2 else 0.0
        draw_robot(d, 752, GROUND_Y, marked=mark, walk=walk, noisy=noisy,
                   label="会动的")
        draw_robot(d, 902, GROUND_Y, walk=0.0, noisy=0.0, label="安静的")
        speak = max(0.0, min(1.0, (t - 3.4) / 0.5)) if t > 3.4 else 0.0
        draw_sonar(d, DEV_X, GROUND_Y, ang, led=mark, speak=speak, mic=1.0)
        ally_lamp(d, 1005, GROUND_Y - 24, on=mark)
        ratio = min(1.0, max(0.0, (t - 3.2) / 1.0))
        bar_sign(d, DEV_X + 148, GROUND_Y, ratio)
        if t > 3.2:
            hud_count(d, W - MARGIN - 130, 420, 1)
        note_bar(img, "红灯亮，喇叭喊，读条拉满", "队友的小灯也亮了，这叫全队共享", accent=C_ALERT)
        wipe_in(img, RED, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v16
def v16_test_quiet(dur):
    w = SegWriter("v16_test_quiet")
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        chip_head(img, "落地实测 · 安静就不被发现", C_BOARD, WHITE)
        d.text((MARGIN, 206), "他一动不动！", font=font(54, True), fill=INK, anchor="lm")
        d.text((MARGIN, 270), "没有声音，就不会被标记", font=font(30, False),
               fill=INK_SOFT, anchor="lm")
        floor(d)
        ang = sweep_ang(t)
        radar_cone(d, DEV_X, GROUND_Y, ang)
        for bx in (520, 640):
            cover_box(d, bx, GROUND_Y)
        hx, hy = draw_sonar(d, DEV_X, GROUND_Y, ang, led=0.0, mic=0.15)
        phase = (t % 1.7) / 1.7
        scan_rings(d, hx, hy, ang, phase)
        draw_robot(d, 752, GROUND_Y, walk=t * 0.4, noisy=0.0, label="会动的")
        draw_robot(d, 902, GROUND_Y, walk=0.0, noisy=0.0, label="安静的")
        bar_sign(d, DEV_X + 148, GROUND_Y, 0.0)
        big_number(d, (W - MARGIN - 300, 370, W - MARGIN, 500), 0, "安静目标的音量", C_BOARD)
        note_bar(img, "雷达扫过他，也没有声音", "这就是回响最厉害的地方", accent=C_BOARD)
        wipe_in(img, C_BOARD, t, 0.30)
        w.add(img)
    return w.close()


def build_anims(segdur):
    """Render every animated segment to its exact narration length."""
    return {
        "v09_code_read": v09_code_read(segdur["v09_code_read"]),
        "v10_code_judge": v10_code_judge(segdur["v10_code_judge"]),
        "v11_code_share": v11_code_share(segdur["v11_code_share"]),
        "v14_test_scan": v14_test_scan(segdur["v14_test_scan"]),
        "v15_test_mark": v15_test_mark(segdur["v15_test_mark"]),
        "v16_test_quiet": v16_test_quiet(segdur["v16_test_quiet"]),
    }
