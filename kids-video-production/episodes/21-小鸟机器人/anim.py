# -*- coding: utf-8 -*-
"""anim.py - the animated segments for the 简易小鸟机器人 film.

  * v09_code_wing  - program 1: left wing 60 deg, right wing 120 deg = flap
  * v10_code_light - program 2: brighter than 500? turn towards the light
  * v11_code_back  - program 3: closer than 20 cm? stop, back up, chirp
  * v14_test_flap  - live test: the wings beat up and down
  * v15_test_block - live test: a box blocks the way, it backs away
  * v16_test_light - live test: a torch shines, it turns and sings

Every segment is cut to the exact length of its narration beat, so picture
and voice stay locked.  The bird is drawn - it is a kraft-paper prop with
toy wheels, two servo paper wings, a light-sensor eye and one LED.

Layout rule for this episode: every info panel lives in the top third of the
frame (y 175-365) and the bird performs on the floor below (ground 1120), so
nothing ever covers the character.
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

C_BOT = (54, 162, 105)     # Arduino 大脑
C_EYE = (30, 168, 190)     # 光敏电阻 小眼睛
C_RADAR = (198, 92, 168)   # 超声波 小雷达
C_WING = (245, 166, 35)    # 小舵机 小翅膀
C_MOUTH = (255, 140, 60)   # 小喇叭 小嘴巴
C_LAMP = (255, 196, 60)    # LED 小灯笼
C_ALERT = (228, 87, 46)    # 红色
C_BLUE = (58, 76, 96)      # 深色
C_BIRD = (62, 138, 208)    # 小鸟身子 天空蓝

CREAM_RGB = (248, 242, 228)
FLOOR_C = (231, 219, 194)
FLOOR_D = (214, 199, 170)
KRAFT = (196, 160, 108)
KRAFT_D = (150, 114, 70)
KRAFT_L = (224, 196, 152)
DARK = (52, 58, 70)
DARK_L = (78, 86, 100)
TAPE = (246, 214, 92)
FEATHER_L = (255, 190, 96)
FEATHER_R = (128, 190, 222)
GOLD = (250, 206, 96)

GROUND_Y = 1120
NOTE_TOP = 1360


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


def side_chip(img, text, color=C_LAMP, fg=INK, size=28):
    """A takeaway chip in the top-right corner, opposite the chapter title."""
    d = ImageDraw.Draw(img)
    f = font(size, True)
    tw = d.textlength(text, font=f)
    x0 = W - MARGIN - tw - 44
    d.rounded_rectangle([x0, 78, W - MARGIN, 142], 32, fill=color)
    d.text((x0 + 22, 110), text, font=f, fill=fg, anchor="lm")


def hud_card(img, box, big, small, accent=C_BIRD, big_size=40, small_size=26):
    """A small information card used along the top of a live-test frame."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    d.rounded_rectangle([x0 + 20, y0 + 20, x0 + 30, y1 - 20], 5, fill=accent)
    d.text((x0 + 48, y0 + (y1 - y0) / 2 - 22), big, font=font(big_size, True),
           fill=INK, anchor="lm")
    d.text((x0 + 48, y0 + (y1 - y0) / 2 + 26), small, font=font(small_size, False),
           fill=INK_SOFT, anchor="lm")


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


def tape_path(d, y, x0, x1, dash=52, gap=34, color=TAPE):
    """The yellow tape line taped on the floor as the flight route."""
    x = x0
    while x < x1:
        d.rounded_rectangle([x, y - 9, min(x + dash, x1), y + 9], 8, fill=color,
                            outline=(214, 176, 60), width=3)
        x += dash + gap


def room(d, ground=GROUND_Y):
    """A cosy living-room wall behind the floor, so the test shots have a place."""
    d.rectangle([0, 0, W, ground], fill=(223, 234, 231))
    d.rectangle([0, ground - 28, W, ground], fill=(205, 219, 215))
    d.line([(0, ground - 28), (W, ground - 28)], fill=(184, 201, 197), width=4)
    # window with a bit of sun, kept low so the HUD stays clear
    wx0, wy0, wx1, wy1 = 110, 430, 500, 830
    d.rounded_rectangle([wx0 - 16, wy0 - 16, wx1 + 16, wy1 + 16], 18,
                        fill=(255, 252, 244), outline=(200, 187, 163), width=5)
    d.rounded_rectangle([wx0, wy0, wx1, wy1], 10, fill=(194, 221, 238))
    d.ellipse([wx0 + 34, wy0 + 30, wx0 + 122, wy0 + 118], fill=(250, 226, 150))
    d.line([((wx0 + wx1) // 2, wy0), ((wx0 + wx1) // 2, wy1)], fill=(255, 252, 244), width=12)
    d.line([(wx0, (wy0 + wy1) // 2), (wx1, (wy0 + wy1) // 2)], fill=(255, 252, 244), width=12)
    # a small framed picture on the other wall
    px0, py0, px1, py1 = 660, 470, 880, 690
    d.rounded_rectangle([px0, py0, px1, py1], 12, fill=(255, 252, 244),
                        outline=(200, 187, 163), width=5)
    d.rectangle([px0 + 24, py0 + 24, px1 - 24, py1 - 24], fill=(212, 231, 220))
    # a little bird picture in the frame, so the room feels like home
    d.ellipse([px0 + 56, py0 + 118, px0 + 124, py0 + 172], fill=(120, 176, 214))
    d.polygon([(px0 + 118, py0 + 138), (px0 + 144, py0 + 146), (px0 + 118, py0 + 154)],
              fill=C_MOUTH)


def draw_feather(d, x, y, ang, s=1.0, col=FEATHER_L, rib=KRAFT_D):
    """One paper feather wing, drawn along the given angle."""
    L, Wd = 124 * s, 32 * s
    pts = [(0, 0), (L * 0.34, -Wd * 0.55), (L, -Wd * 0.26),
           (L * 0.82, Wd * 0.38), (L * 0.24, Wd * 0.60)]
    rot = [(x + px * math.cos(ang) - py * math.sin(ang),
            y + px * math.sin(ang) + py * math.cos(ang)) for px, py in pts]
    d.polygon(rot, fill=col, outline=rib, width=max(2, int(3 * s)))
    for t in (0.30, 0.52, 0.74):
        ex = x + L * t * math.cos(ang)
        ey = y + L * t * math.sin(ang)
        d.line([(x, y), (ex, ey)], fill=mix(col, rib, 0.45), width=max(2, int(3 * s)))


def draw_bird(d, x, ground, s=1.0, led=0.0, led_col=None, flap=0.0, drive=0.0,
              turn=0.0, back=0.0, head=0.0, label=None):
    """The cardboard bird robot: a fat kraft body, a round head, two paper wings."""
    bob = math.sin(drive * 7.0) * 2.4 * s
    cx = x
    cy = ground - 104 * s + bob
    bw, bh = 86 * s, 72 * s
    hr = 50 * s

    # shadow on the floor
    d.ellipse([cx - bw * 1.06, ground - 16 * s, cx + bw * 1.06, ground + 10 * s],
              fill=(214, 200, 174))

    # tail feathers behind the body
    for k, off in enumerate((-34, 0, 34)):
        d.polygon([(cx + off * s - 18 * s, ground - 56 * s),
                   (cx + off * s + 18 * s, ground - 56 * s),
                   (cx + off * s, ground - 12 * s)],
                  fill=FEATHER_R if k % 2 else FEATHER_L, outline=KRAFT_D, width=3)

    # wings behind the body
    a = math.sin(flap * 6.2)
    ang_l = math.radians(192 + 32 * a)
    ang_r = math.radians(-34 - 32 * a)
    draw_feather(d, cx - bw * 0.80, cy - 10 * s, ang_l, s, FEATHER_L)
    draw_feather(d, cx + bw * 0.80, cy - 10 * s, ang_r, s, FEATHER_R)

    # wheels peeking out under the body
    for wx in (cx - 56 * s, cx + 56 * s):
        r = 23 * s
        d.ellipse([wx - r, ground - 10 * s - r * 0.9, wx + r, ground - 10 * s + r * 0.35],
                  fill=DARK, outline=DARK_L, width=3)
        spin = drive * 9.0
        d.line([(wx - r * 0.6 * math.cos(spin), ground - 10 * s - r * 0.45 - r * 0.5 * math.sin(spin)),
                (wx + r * 0.6 * math.cos(spin), ground - 10 * s - r * 0.45 + r * 0.5 * math.sin(spin))],
               fill=(150, 156, 168), width=int(5 * s))

    # fat bird body
    d.ellipse([cx - bw, cy - bh, cx + bw, cy + bh], fill=KRAFT, outline=KRAFT_D, width=5)
    d.ellipse([cx - bw + 12 * s, cy - bh + 10 * s, cx + bw - 12 * s, cy + bh - 10 * s],
              outline=KRAFT_L, width=4)
    d.ellipse([cx - 44 * s, cy - 40 * s, cx + 44 * s, cy + 52 * s],
              fill=(250, 246, 232), outline=KRAFT_D, width=3)

    # the little radar on the chest
    d.rounded_rectangle([cx - 26 * s, cy + 2 * s, cx + 26 * s, cy + 28 * s], 8 * s,
                        fill=(226, 232, 238), outline=(120, 132, 150), width=3)
    for k in (-1, 1):
        d.ellipse([cx + k * 12 * s - 6 * s, cy + 9 * s, cx + k * 12 * s + 6 * s, cy + 21 * s],
                  fill=C_RADAR)

    # neck
    hx = cx + head * 24 * s
    hy = cy - bh - 36 * s
    d.polygon([(cx - 26 * s, cy - bh + 10 * s), (cx + 26 * s, cy - bh + 10 * s),
               (hx + 22 * s, hy + hr * 0.6), (hx - 22 * s, hy + hr * 0.6)],
              fill=KRAFT, outline=KRAFT_D, width=4)

    # round head
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=KRAFT, outline=KRAFT_D, width=5)
    d.ellipse([hx - hr + 11 * s, hy - hr + 9 * s, hx + hr - 11 * s, hy + hr - 9 * s],
              outline=KRAFT_L, width=4)
    # a little crest of feathers on top
    for k, off in enumerate((-18, 0, 18)):
        d.polygon([(hx + off * s - 9 * s, hy - hr + 4 * s),
                   (hx + off * s + 9 * s, hy - hr + 4 * s),
                   (hx + off * s + 4 * s, hy - hr - 30 * s)],
                  fill=FEATHER_L if k % 2 else FEATHER_R, outline=KRAFT_D, width=3)
    # the light-sensor eye
    ex = hx - 2 * s + head * 8 * s
    d.ellipse([ex - 30 * s, hy - 16 * s, ex + 6 * s, hy + 20 * s],
              fill=(250, 252, 252), outline=(18, 110, 128), width=4)
    d.ellipse([ex - 18 * s, hy - 4 * s, ex - 2 * s, hy + 12 * s], fill=C_EYE)
    d.ellipse([ex - 14 * s, hy - 1 * s, ex - 8 * s, hy + 5 * s], fill=(240, 252, 254))
    # the orange paper beak
    bx = hx + 6 * s + head * 24 * s
    d.polygon([(bx, hy - 4 * s), (bx + 38 * s, hy + 10 * s), (bx, hy + 26 * s)],
              fill=C_MOUTH, outline=(190, 96, 40), width=3)
    # the lantern on the head
    lc = led_col or C_LAMP
    col = mix(KRAFT_L, lc, min(1.0, max(0.0, led)))
    d.ellipse([hx - 17 * s, hy - hr - 22 * s, hx + 17 * s, hy - hr + 4 * s],
              fill=col, outline=KRAFT_D, width=4)
    if led > 0.05:
        d.ellipse([hx - 31 * s, hy - hr - 36 * s, hx + 31 * s, hy - hr + 18 * s],
                  outline=mix(CREAM_RGB, lc, 0.5 * min(1.0, led)), width=5)

    # turning arrow
    if turn > 0.02:
        ax, ay = cx, hy - hr - 60 * s
        d.arc([ax - 58 * s, ay - 58 * s, ax + 58 * s, ay + 58 * s],
              start=200, end=340, fill=mix(CREAM_RGB, C_ALERT, turn), width=7)
        d.polygon([(ax + 52 * s, ay - 10 * s), (ax + 30 * s, ay - 24 * s),
                   (ax + 34 * s, ay + 2 * s)], fill=mix(CREAM_RGB, C_ALERT, turn))
    if back > 0.02:
        for k in (-1, 1):
            xx = cx + k * 104 * s
            d.polygon([(xx - 18 * s, ground - 62 * s), (xx + 16 * s, ground - 62 * s),
                       (xx, ground - 38 * s)], fill=mix(CREAM_RGB, C_ALERT, back))
    if label:
        d.text((x, hy - hr - 70 * s), label, font=font(26, True),
               fill=INK_SOFT, anchor="mm")


def draw_scrap(d, x, ground, s=1.0, col=(252, 248, 232)):
    """A little colourful paper feather scrap on the floor."""
    d.polygon([(x - 34 * s, ground - 5 * s), (x - 8 * s, ground - 28 * s),
               (x + 22 * s, ground - 14 * s), (x + 34 * s, ground - 3 * s)],
              fill=col, outline=(196, 182, 154), width=3)
    d.line([(x - 8 * s, ground - 28 * s), (x + 12 * s, ground - 16 * s)],
           fill=(224, 214, 192), width=3)


def draw_box(d, x, ground, w=112, h=126, label=None):
    """A cardboard box used as an obstacle on the flight route."""
    d.rounded_rectangle([x - w / 2, ground - h, x + w / 2, ground], 8,
                        fill=KRAFT, outline=KRAFT_D, width=5)
    d.line([(x - w / 2 + 6, ground - h * 0.52), (x + w / 2 - 6, ground - h * 0.52)],
           fill=KRAFT_D, width=4)
    d.line([(x, ground - h + 8), (x, ground - 8)], fill=KRAFT_D, width=4)
    d.rectangle([x - w / 2 + 14, ground - h + 12, x + w / 2 - 14, ground - h + 32],
                fill=KRAFT_L, outline=KRAFT_D, width=3)
    if label:
        d.text((x, ground - h - 22), label, font=font(26, True), fill=INK_SOFT, anchor="mm")


def draw_torch(d, x, ground, s=1.0, beam=True):
    """A hand torch lying on the floor, throwing its beam to the LEFT."""
    y = ground - 26 * s
    if beam:
        d.polygon([(x - 26 * s, y - 14 * s), (x - 520 * s, ground - 200 * s),
                   (x - 520 * s, ground + 40 * s)], fill=(255, 246, 198))
        d.polygon([(x - 26 * s, y - 14 * s), (x - 520 * s, ground - 200 * s),
                   (x - 520 * s, ground + 40 * s)], outline=(250, 222, 132), width=3)
    d.rounded_rectangle([x - 6 * s, y - 20 * s, x + 76 * s, y + 20 * s], 14 * s,
                        fill=(96, 106, 124), outline=(58, 66, 82), width=4)
    d.ellipse([x - 32 * s, y - 22 * s, x - 2 * s, y + 22 * s], fill=(255, 236, 170),
              outline=(120, 110, 70), width=4)
    d.ellipse([x - 24 * s, y - 14 * s, x - 10 * s, y + 14 * s], fill=(255, 252, 226))


def distance_bar(d, box, cm, thresh=20, maxcm=100, label="小雷达量的距离"):
    """How far the obstacle is, with the danger zone marked in red."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    d.text((x0 + 26, y0 + 38), label, font=font(28, True), fill=INK_SOFT, anchor="lm")
    d.text((x1 - 26, y0 + 44), "%d cm" % int(cm), font=font(42, True),
           fill=(C_ALERT if cm <= thresh else C_RADAR), anchor="rm")
    bx0, bx1 = x0 + 46, x1 - 46
    by0, by1 = y0 + 68, y0 + 114
    d.rounded_rectangle([bx0, by0, bx1, by1], 22, fill=(226, 222, 212))
    danger = bx0 + (bx1 - bx0) * (thresh / float(maxcm))
    d.rounded_rectangle([bx0, by0, danger, by1], 20, fill=mix((226, 222, 212), C_ALERT, 0.45))
    ratio = max(0.0, min(1.0, cm / float(maxcm)))
    fx = bx0 + (bx1 - bx0) * ratio
    if fx > bx0 + 10:
        d.rounded_rectangle([bx0, by0, fx, by1], 20,
                            fill=C_ALERT if cm <= thresh else C_RADAR)
    d.text((danger, by1 + 30), "20", font=font(24, True), fill=C_ALERT, anchor="mm")
    d.text((bx0, by1 + 30), "0", font=font(22, True), fill=INK_SOFT, anchor="mm")
    d.text((bx1, by1 + 30), "%d" % maxcm, font=font(22, True), fill=INK_SOFT, anchor="mm")


def light_bar(d, box, val, thresh=500, maxval=800, label="小眼睛看到的亮度", sun=False):
    """How bright it is; past 500 the bird turns towards the light."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    d.text((x0 + 26, y0 + 38), label, font=font(28, True), fill=INK_SOFT, anchor="lm")
    d.text((x1 - 26, y0 + 44), "%d" % int(val), font=font(42, True),
           fill=(C_LAMP if val >= thresh else C_EYE), anchor="rm")
    if sun:
        sx, sy, sr = x1 - 150, y0 + 44, 26
        for k in range(7):
            ang = k * (2 * math.pi / 7)
            d.line([(sx + math.cos(ang) * (sr + 7), sy + math.sin(ang) * (sr + 7)),
                    (sx + math.cos(ang) * (sr + 16), sy + math.sin(ang) * (sr + 16))],
                   fill=(248, 206, 110), width=4)
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 226, 138),
                  outline=(238, 186, 78), width=4)
    bx0, bx1 = x0 + 46, x1 - 46
    by0, by1 = y0 + 68, y0 + 114
    d.rounded_rectangle([bx0, by0, bx1, by1], 22, fill=(226, 222, 212))
    mark = bx0 + (bx1 - bx0) * (thresh / float(maxval))
    d.rounded_rectangle([bx0, by0, mark, by1], 20, fill=mix((226, 222, 212), C_LAMP, 0.5))
    ratio = max(0.0, min(1.0, val / float(maxval)))
    fx = bx0 + (bx1 - bx0) * ratio
    if fx > bx0 + 10:
        d.rounded_rectangle([bx0, by0, fx, by1], 20, fill=C_LAMP if val >= thresh else C_EYE)
    d.text((mark, by1 + 30), "500", font=font(24, True), fill=(196, 140, 30), anchor="mm")
    d.text((bx0, by1 + 30), "0", font=font(22, True), fill=INK_SOFT, anchor="mm")
    d.text((bx1, by1 + 30), "%d" % maxval, font=font(22, True), fill=INK_SOFT, anchor="mm")


def servo_bars(d, box, left, right, left_max=180, right_max=180):
    """The two wing angles - one high, one low, so the bird beats its wings."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    d.text((x0 + 26, y0 + 38), "两个翅膀的角度", font=font(28, True), fill=INK_SOFT, anchor="lm")
    for i, (name, val, col) in enumerate((("左翅膀", left, FEATHER_L), ("右翅膀", right, FEATHER_R))):
        yy = y0 + 82 + i * 52
        d.text((x0 + 26, yy + 16), name, font=font(26, True), fill=INK, anchor="lm")
        bx0, bx1 = x0 + 140, x1 - 96
        d.rounded_rectangle([bx0, yy, bx1, yy + 30], 15, fill=(226, 222, 212))
        r = max(0.0, min(1.0, val / float(left_max)))
        if r > 0.02:
            d.rounded_rectangle([bx0, yy, bx0 + (bx1 - bx0) * r, yy + 30], 15, fill=col)
        d.text((bx1 + 12, yy + 16), "%d°" % int(val), font=font(26, True),
               fill=INK_SOFT, anchor="lm")


def pill_row(img, box, items):
    """A row of coloured pills naming what the bird does."""
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
        d.text((x + 38, y0 + 44), big, font=font(29, True), fill=INK, anchor="lm")
        d.text((x + 38, y1 - 38), small, font=font(22, False), fill=INK_SOFT, anchor="lm")


def bubble(d, box, big, small=None, color=C_ALERT, tail=(520, 980)):
    """A comic speech bubble for the bird's chirp."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 34, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=4)
    d.polygon([(tail[0], tail[1]), (tail[0] - 56, tail[1] + 46), (tail[0] + 16, tail[1] + 10)],
              fill=(255, 253, 246), outline=(228, 216, 192), width=4)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2 - (16 if small else 0)), big,
           font=font(46, True), fill=color, anchor="mm")
    if small:
        d.text(((x0 + x1) / 2, (y0 + y1) / 2 + 40), small, font=font(28, True),
               fill=INK, anchor="mm")


# ------------------------------------------------------------------ v09
def v09_code_wing(dur):
    w = SegWriter("v09_code_wing")
    lines = [
        ("wingL.write(60);   // 左翅膀抬高", ORANGE),
        ("wingR.write(120);  // 右翅膀放下", None),
        ("// 一高一低，翅膀就扇起来", (150, 190, 255)),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.3 else (2 if t < 3.4 else 3)
        chip_head(img, "程序 ① 张开翅膀", C_BIRD, WHITE)
        side_chip(img, "一高一低才错得开", C_BIRD, WHITE, 26)
        code_reveal(img, (MARGIN, 175, W - MARGIN, 525), lines, n=n)
        servo_bars(d, (MARGIN, 550, W - MARGIN, 735), 60, 120)
        floor(d, 1120)
        tape_path(d, 1120 + 8, MARGIN + 20, W - MARGIN - 20)
        cx = 300 + 500 * min(1.0, t / max(1.0, dur * 0.8))
        draw_bird(d, cx, 1120, s=1.25, led=0.35 + 0.45 * abs(math.sin(t * 4.0)),
                  led_col=C_LAMP, flap=t * 2.2, drive=t * 3.0)
        note_bar(img, "两个角度不一样，翅膀才错得开", "一高一低，就像小鸟在扇翅膀", accent=C_BIRD)
        wipe_in(img, C_BIRD, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v10
def v10_code_light(dur):
    w = SegWriter("v10_code_light")
    lines = [
        ("l = light.read();   // 量一次亮度", ORANGE),
        ("if (l > 500) {", None),
        ("  turnToLight(); sing(); }", (150, 190, 255)),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.3 else (2 if t < 3.6 else 3)
        chip_head(img, "程序 ② 看见光就转过来", C_EYE, WHITE, size=34)
        side_chip(img, "超过 500 就转头", GOLD, INK, 26)
        code_reveal(img, (MARGIN, 175, W - MARGIN, 525), lines, n=n)
        val = 180 + 420 * min(1.0, max(0.0, (t - 1.2) / max(1.0, dur * 0.62)))
        light_bar(d, (MARGIN, 550, W - MARGIN, 735), val, sun=True)
        floor(d, 1120)
        turn = 1.0 if val >= 500 else 0.0
        cx = 380 + 260 * min(1.0, max(0.0, (t - 1.0) / max(1.0, dur * 0.6)))
        draw_bird(d, cx, 1120, s=1.25, led=0.4 + 0.4 * abs(math.sin(t * 4.0)),
                  led_col=C_LAMP, flap=t * 2.4, drive=t * 2.2, turn=turn,
                  head=turn * 0.85)
        note_bar(img, "小眼睛一直盯着亮不亮", "光一变多，它就把头转过去", accent=C_EYE)
        wipe_in(img, C_EYE, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v11
def v11_code_back(dur):
    w = SegWriter("v11_code_back")
    lines = [
        ("d = sonar.read();   // 量一次距离", ORANGE),
        ("if (d < 20) { back(); }", None),
        ("sing(\"啾\");  // 再唱一声", (150, 190, 255)),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.4 else (2 if t < 3.8 else 3)
        chip_head(img, "程序 ③ 前面太近就后退", C_ALERT, WHITE, size=32)
        side_chip(img, "先退一步更安全", C_ALERT, WHITE, 26)
        code_reveal(img, (MARGIN, 175, W - MARGIN, 525), lines, n=n)
        phase = t / max(1.0, dur)
        cm = 95 - 80 * min(1.0, phase / 0.55)
        distance_bar(d, (MARGIN, 550, W - MARGIN, 735), cm)
        floor(d, 1120)
        draw_box(d, 900, 1120, w=118, h=132, label="纸箱")
        cx = 300 + 380 * min(1.0, phase / 0.62)
        if phase > 0.62:
            cx = 680 - 200 * min(1.0, (phase - 0.62) / 0.38)
        back = 1.0 if phase > 0.55 else 0.0
        draw_bird(d, cx, 1120, s=1.25, led=(0.9 if back else 0.35),
                  led_col=(C_ALERT if back else C_LAMP), flap=t * 2.4, drive=t * 3.0,
                  back=back)
        note_bar(img, "前面太近就停一下、往后退", "退一点再唱一声，接着继续飞", accent=C_ALERT)
        wipe_in(img, C_ALERT, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v14
def v14_test_flap(dur):
    w = SegWriter("v14_test_flap")
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        room(d, 1120)
        floor(d, 1120)
        tape_path(d, 1120 + 6, MARGIN + 30, W - MARGIN - 30)
        chip_head(img, "实测 ① 扇翅膀", C_BIRD, WHITE)
        side_chip(img, "一上一下", C_BIRD, WHITE, 26)
        hud_card(img, (MARGIN, 175, MARGIN + 420, 290), "%d 下" % int(t * 2), "翅膀扇了多少下",
                 accent=C_BIRD, big_size=42, small_size=25)
        hud_card(img, (MARGIN + 450, 175, W - MARGIN, 290), "扇得又稳又好看", "左翅膀高、右翅膀低",
                 accent=C_LAMP, big_size=34, small_size=25)
        k = min(1.0, t / max(1.0, dur * 0.86))
        cx = 320 + 500 * k
        draw_bird(d, cx, 1120, s=1.25, led=0.35 + 0.5 * abs(math.sin(t * 6.0)),
                  led_col=C_LAMP, flap=t * 2.6, drive=t * 3.0)
        note_bar(img, "左翅膀高、右翅膀低", "两个角度错开，翅膀就一上一下地扇", accent=C_BIRD)
        wipe_in(img, C_BIRD, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v15
def v15_test_block(dur):
    w = SegWriter("v15_test_block")
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        room(d, 1120)
        floor(d, 1120)
        chip_head(img, "实测 ② 遇到纸箱绕开", C_RADAR, WHITE, size=34)
        side_chip(img, "快退开！", C_RADAR, WHITE, 26)
        draw_box(d, 900, 1120, w=118, h=132, label="纸箱")
        phase = t / max(1.0, dur)
        if phase < 0.45:
            cx = 300 + 340 * (phase / 0.45)
            cm = 95 - 80 * (phase / 0.45)
            turn = 0.0
            back = 0.0
        elif phase < 0.68:
            cx = 640 - 180 * ((phase - 0.45) / 0.23)
            cm = 15
            turn = 0.0
            back = 1.0
        else:
            cx = 460 + 260 * ((phase - 0.68) / 0.32)
            cm = 15 + 70 * ((phase - 0.68) / 0.32)
            turn = 0.0
            back = 0.0
        draw_bird(d, cx, 1120, s=1.25, led=(0.9 if back else 0.35),
                  led_col=(C_ALERT if back else C_LAMP), flap=t * 2.6, drive=t * 3.0,
                  turn=turn, back=back)
        distance_bar(d, (MARGIN, 175, W - MARGIN, 360), cm, label="小雷达量的距离")
        if back:
            d.rounded_rectangle([W - MARGIN - 330, 400, W - MARGIN, 480], 22, fill=C_ALERT)
            d.text((W - MARGIN - 165, 440), "停！往后退！", font=font(29, True),
                   fill=WHITE, anchor="mm")
        note_bar(img, "前面只剩 15 厘米，它马上退开", "停一下、往后退、啾一声，再接着往前飞", accent=C_RADAR)
        wipe_in(img, C_RADAR, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v16
def v16_test_light(dur):
    w = SegWriter("v16_test_light")
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        room(d, 1120)
        floor(d, 1120)
        chip_head(img, "实测 ③ 照到光就唱歌", C_LAMP, INK)
        side_chip(img, "啾啾啾！", C_LAMP, INK, 26)
        draw_torch(d, 960, 1120, s=1.05)
        for k in range(5):
            draw_scrap(d, 470 + k * 58, 1120, s=1.05,
                       col=(252, 248, 232) if k % 2 else (238, 246, 255))
        phase = t / max(1.0, dur)
        val = 160 + 520 * min(1.0, phase / 0.45)
        cx = 330 + 90 * min(1.0, phase / 0.55)
        turn = 1.0 if val >= 500 else 0.0
        draw_bird(d, cx, 1120, s=1.25, led=0.4 + 0.5 * abs(math.sin(t * 6.0)),
                  led_col=C_LAMP, flap=t * (3.2 if turn else 2.4), drive=t * 2.0,
                  turn=turn, head=turn * 0.9)
        light_bar(d, (MARGIN, 175, W - MARGIN, 360), val)
        if turn:
            bubble(d, (MARGIN + 20, 430, MARGIN + 320, 560), "啾啾！",
                   color=C_MOUTH, tail=(MARGIN + 110, 560, MARGIN + 60, 620))
        note_bar(img, "手电筒一照，小眼睛就看见啦", "它把头转过来对着光，还唱起了歌", accent=C_LAMP)
        wipe_in(img, C_LAMP, t, 0.30)
        w.add(img)
    return w.close()


def build_anims(segdur):
    """Render every animated segment to its exact narration length."""
    return {
        "v09_code_wing": v09_code_wing(segdur["v09_code_wing"]),
        "v10_code_light": v10_code_light(segdur["v10_code_light"]),
        "v11_code_back": v11_code_back(segdur["v11_code_back"]),
        "v14_test_flap": v14_test_flap(segdur["v14_test_flap"]),
        "v15_test_block": v15_test_block(segdur["v15_test_block"]),
        "v16_test_light": v16_test_light(segdur["v16_test_light"]),
    }
