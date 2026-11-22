# -*- coding: utf-8 -*-
"""anim.py - the animated segments for the 巡逻机器人 film.

  * v09_code_cruise - program 1: both motors the same speed = straight line
  * v10_code_avoid  - program 2: closer than 20 cm? stop, back up, turn left
  * v11_code_report - program 3: someone is there! blink, wave, shout
  * v14_test_cruise - live test: it follows the tape line
  * v15_test_avoid  - live test: it dodges the cardboard box
  * v16_test_hello  - live test: it waves at the kid who walks in

Every segment is cut to the exact length of its narration beat, so picture
and voice stay locked.  The robot is drawn - it is a kraft-paper prop with
toy wheels, a servo paper arm and a single LED.  The only "sensing" is an
ultrasonic module reading centimetres off a cardboard box.
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
C_EYE = (30, 168, 190)     # 超声波 小眼睛
C_EAR = (198, 92, 168)     # 人体感应 小耳朵
C_ARM = (245, 166, 35)     # 小舵机 小胳膊
C_MOUTH = (255, 140, 60)   # 小喇叭 小嘴巴
C_LAMP = (255, 196, 60)    # LED 小灯笼
C_ALERT = (228, 87, 46)    # 红色
C_BLUE = (58, 76, 96)      # 底盘深色

CREAM_RGB = (248, 242, 228)
FLOOR_C = (231, 219, 194)
FLOOR_D = (214, 199, 170)
KRAFT = (196, 160, 108)
KRAFT_D = (150, 114, 70)
KRAFT_L = (224, 196, 152)
DARK = (52, 58, 70)
DARK_L = (78, 86, 100)
TAPE = (246, 214, 92)
SKIN = (250, 214, 180)
SHIRT = (96, 170, 210)
PANTS = (78, 96, 126)

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


def tape_path(d, y, x0, x1, dash=52, gap=34, color=TAPE):
    """The yellow tape line taped on the floor as the patrol route."""
    x = x0
    while x < x1:
        d.rounded_rectangle([x, y - 9, min(x + dash, x1), y + 9], 8, fill=color,
                            outline=(214, 176, 60), width=3)
        x += dash + gap


def draw_car(d, x, ground, s=1.0, led=0.0, led_col=None, wave=0.0, drive=0.0,
             turn=0.0, label=None, back=False):
    """The cardboard patrol robot: kraft chassis, toy wheels, waving paper arm."""
    bob = math.sin(drive * 8.0) * 3 * s
    # wheels
    for wx in (x - 58 * s, x + 58 * s):
        r = 30 * s
        d.ellipse([wx - r, ground - 8 * s - r * 2, wx + r, ground - 8 * s + r * 0.2],
                  fill=DARK, outline=DARK_L, width=3)
        spin = drive * 9.0
        d.line([(wx - r * 0.6 * math.cos(spin), ground - 8 * s - r - r * 0.6 * math.sin(spin)),
                (wx + r * 0.6 * math.cos(spin), ground - 8 * s - r + r * 0.6 * math.sin(spin))],
               fill=(150, 156, 168), width=int(5 * s))
    # caster
    d.ellipse([x - 12 * s, ground - 26 * s, x + 12 * s, ground - 2 * s], fill=DARK_L)
    # chassis
    bx0, bx1 = x - 96 * s, x + 96 * s
    by0, by1 = ground - 118 * s + bob, ground - 26 * s + bob
    d.rounded_rectangle([bx0, by0, bx1, by1], 18 * s, fill=KRAFT, outline=KRAFT_D, width=5)
    d.rounded_rectangle([bx0 + 10 * s, by0 + 10 * s, bx1 - 10 * s, by1 - 10 * s], 12 * s,
                        outline=KRAFT_L, width=4)
    # speaker grille on the belly
    for k in range(3):
        for j in range(3):
            d.ellipse([bx0 + 26 * s + j * 13 * s, by1 - 34 * s + k * 11 * s,
                       bx0 + 32 * s + j * 13 * s, by1 - 28 * s + k * 11 * s],
                      fill=KRAFT_D)
    # head on a short neck
    hx0, hx1 = x + 4 * s, x + 94 * s
    hy0, hy1 = by0 - 74 * s + bob, by0 + 6 * s + bob
    d.rectangle([x + 40 * s, hy1 - 4 * s, x + 58 * s, by0 + 8 * s], fill=KRAFT_D)
    d.rounded_rectangle([hx0, hy0, hx1, hy1], 16 * s, fill=KRAFT_L, outline=KRAFT_D, width=5)
    # the two eyes (ultrasonic)
    for ex in (hx0 + 22 * s, hx0 + 52 * s):
        d.ellipse([ex - 13 * s, (hy0 + hy1) / 2 - 13 * s, ex + 13 * s, (hy0 + hy1) / 2 + 13 * s],
                  fill=(250, 252, 252), outline=(18, 110, 128), width=4)
        d.ellipse([ex - 5 * s, (hy0 + hy1) / 2 - 5 * s, ex + 5 * s, (hy0 + hy1) / 2 + 5 * s],
                  fill=C_EYE)
    # the little ear
    d.ellipse([hx1 - 12 * s, hy0 + 6 * s, hx1 + 2 * s, hy0 + 20 * s],
              fill=mix(KRAFT_L, C_EAR, 0.75), outline=KRAFT_D, width=3)
    # the lantern on top
    lc = led_col or C_LAMP
    col = mix(KRAFT_L, lc, min(1.0, max(0.0, led)))
    d.ellipse([x + 36 * s, hy0 - 26 * s, x + 66 * s, hy0 + 4 * s], fill=col,
              outline=KRAFT_D, width=4)
    if led > 0.05:
        d.ellipse([x + 26 * s, hy0 - 36 * s, x + 76 * s, hy0 + 14 * s],
                  outline=mix(CREAM_RGB, lc, 0.5 * min(1.0, led)), width=5)
    # the waving paper arm
    if wave > 0.02:
        ax, ay = bx0 + 6 * s, by0 + 22 * s
        ang = math.radians(-60 + 26 * math.sin(wave * 7.0))
        ex2 = ax - 62 * s * math.cos(ang)
        ey2 = ay - 62 * s * math.sin(ang)
        d.line([(ax, ay), (ex2, ey2)], fill=KRAFT_D, width=int(11 * s))
        d.ellipse([ax - 11 * s, ay - 11 * s, ax + 11 * s, ay + 11 * s], fill=C_ARM,
                  outline=KRAFT_D, width=3)
        d.rounded_rectangle([ex2 - 22 * s, ey2 - 8 * s, ex2 + 22 * s, ey2 + 8 * s], 6 * s,
                            fill=KRAFT_L, outline=KRAFT_D, width=3)
    else:
        d.ellipse([bx0 - 12 * s, by0 + 12 * s, bx0 + 12 * s, by0 + 36 * s], fill=C_ARM,
                  outline=KRAFT_D, width=3)
    # direction arrows when it turns
    if turn > 0.02:
        ax, ay = x, by0 - 30 * s
        d.arc([ax - 62 * s, ay - 62 * s, ax + 62 * s, ay + 62 * s],
              start=200, end=340, fill=mix(CREAM_RGB, C_ALERT, turn), width=7)
        d.polygon([(ax - 56 * s, ay - 12 * s), (ax - 34 * s, ay - 26 * s),
                   (ax - 38 * s, ay - 2 * s)], fill=mix(CREAM_RGB, C_ALERT, turn))
    if back > 0.02:
        d.text((x, by1 + 30 * s), "往后退", font=font(int(26 * s), True),
               fill=mix(CREAM_RGB, C_ALERT, back), anchor="mm")
    if label:
        d.text((x, ground + 34), label, font=font(24, True), fill=INK_SOFT, anchor="mm")


def draw_person(d, x, ground, s=1.0, walk=0.0, wave=0.0):
    """A kid standing in for the person the robot reports."""
    swing = math.sin(walk * 7.0) * 16 * s
    h = 250 * s
    top = ground - h
    for sgn in (-1, 1):
        lx = x + sgn * 18 * s + swing * 0.3 * sgn
        d.rounded_rectangle([lx - 11 * s, ground - 62 * s, lx + 11 * s, ground], 6 * s,
                            fill=PANTS, outline=(56, 70, 96), width=3)
        d.rounded_rectangle([lx - 18 * s, ground - 12 * s, lx + 18 * s, ground], 6 * s,
                            fill=(70, 76, 88))
    d.rounded_rectangle([x - 38 * s, top + 70 * s, x + 38 * s, ground - 58 * s], 16 * s,
                        fill=SHIRT, outline=(52, 122, 162), width=4)
    for sgn in (-1, 1):
        ax = x + sgn * 38 * s
        if sgn < 0 and wave > 0.02:
            ang = math.radians(-150 + 28 * math.sin(wave * 7.0))
            ex2 = ax + 56 * s * math.cos(ang)
            ey2 = top + 86 * s + 56 * s * math.sin(ang)
            d.line([(ax, top + 86 * s), (ex2, ey2)], fill=SKIN, width=int(11 * s))
            d.ellipse([ex2 - 9 * s, ey2 - 9 * s, ex2 + 9 * s, ey2 + 9 * s], fill=SKIN)
        else:
            d.line([(ax, top + 86 * s), (ax + sgn * swing * 0.5, top + 128 * s)],
                   fill=SKIN, width=int(11 * s))
    d.ellipse([x - 33 * s, top, x + 33 * s, top + 66 * s], fill=SKIN,
              outline=(206, 168, 138), width=4)
    d.arc([x - 34 * s, top - 6 * s, x + 34 * s, top + 48 * s], start=180, end=360,
          fill=(92, 66, 48), width=int(11 * s))
    for sgn in (-1, 1):
        ex = x + sgn * 13 * s
        d.ellipse([ex - 5 * s, top + 30 * s, ex + 5 * s, top + 40 * s], fill=(48, 48, 52))
    d.arc([x - 14 * s, top + 44 * s, x + 14 * s, top + 58 * s], start=0, end=180,
          fill=(190, 110, 110), width=3)


def draw_box(d, x, ground, w=112, h=126, label=None):
    """A cardboard box used as an obstacle on the patrol route."""
    d.rounded_rectangle([x - w / 2, ground - h, x + w / 2, ground], 8,
                        fill=KRAFT, outline=KRAFT_D, width=5)
    d.line([(x - w / 2 + 6, ground - h * 0.52), (x + w / 2 - 6, ground - h * 0.52)],
           fill=KRAFT_D, width=4)
    d.line([(x, ground - h + 8), (x, ground - 8)], fill=KRAFT_D, width=4)
    d.rectangle([x - w / 2 + 14, ground - h + 12, x + w / 2 - 14, ground - h + 32],
                fill=KRAFT_L, outline=KRAFT_D, width=3)
    if label:
        d.text((x, ground - h - 22), label, font=font(26, True), fill=INK_SOFT, anchor="mm")


def distance_bar(d, box, cm, thresh=20, maxcm=100, label="离箱子多远"):
    """How far the obstacle is, with the danger zone marked in red."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    d.text((x0 + 26, y0 + 40), label, font=font(28, True), fill=INK_SOFT, anchor="lm")
    d.text((x1 - 26, y0 + 46), "%d cm" % int(cm), font=font(44, True),
           fill=(C_ALERT if cm <= thresh else C_EYE), anchor="rm")
    bx0, bx1 = x0 + 46, x1 - 46
    by0, by1 = y0 + 74, y0 + 124
    d.rounded_rectangle([bx0, by0, bx1, by1], 22, fill=(226, 222, 212))
    danger = bx0 + (bx1 - bx0) * (thresh / float(maxcm))
    d.rounded_rectangle([bx0, by0, danger, by1], 20, fill=mix((226, 222, 212), C_ALERT, 0.45))
    ratio = max(0.0, min(1.0, cm / float(maxcm)))
    fx = bx0 + (bx1 - bx0) * ratio
    if fx > bx0 + 10:
        d.rounded_rectangle([bx0, by0, fx, by1], 20,
                            fill=C_ALERT if cm <= thresh else C_EYE)
    d.text((danger, by1 + 34), "20", font=font(26, True), fill=C_ALERT, anchor="mm")
    d.text((bx0, by1 + 34), "0", font=font(24, True), fill=INK_SOFT, anchor="mm")
    d.text((bx1, by1 + 34), "%d" % maxcm, font=font(24, True), fill=INK_SOFT, anchor="mm")


def speed_bars(d, box, left, right):
    """Two motor speed bars - equal bars mean a straight line."""
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], 26, fill=(255, 253, 246),
                        outline=(228, 216, 192), width=3)
    d.text((x0 + 26, y0 + 40), "两个轮子的速度", font=font(28, True), fill=INK_SOFT, anchor="lm")
    for i, (name, val, col) in enumerate((("左轮", left, C_BOT), ("右轮", right, C_EYE))):
        yy = y0 + 88 + i * 54
        d.text((x0 + 26, yy + 16), name, font=font(26, True), fill=INK, anchor="lm")
        bx0, bx1 = x0 + 106, x1 - 40
        d.rounded_rectangle([bx0, yy, bx1, yy + 32], 16, fill=(226, 222, 212))
        r = max(0.0, min(1.0, val))
        if r > 0.02:
            d.rounded_rectangle([bx0, yy, bx0 + (bx1 - bx0) * r, yy + 32], 16, fill=col)
        d.text((bx1 + 8, yy + 16), str(int(r * 100)), font=font(24, True),
               fill=INK_SOFT, anchor="lm")


def pill_row(img, box, items):
    """A row of coloured pills naming what the robot does."""
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
    """A comic speech bubble for the robot's shout."""
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
def v09_code_cruise(dur):
    w = SegWriter("v09_code_cruise")
    lines = [
        ("motorL.write(200);  // 左轮往前", ORANGE),
        ("motorR.write(200);  // 右轮往前", None),
        ("// 两边一样快，就走直线", (150, 190, 255)),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.3 else (2 if t < 3.4 else 3)
        chip_head(img, "程序 ① 直线巡逻", C_BOT, WHITE)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 560), lines, n=n)
        speed_bars(d, (MARGIN, 590, W - MARGIN, 760), 0.78, 0.78)
        floor(d, 1040)
        tape_path(d, 1040 + 8, MARGIN + 20, W - MARGIN - 20)
        cx = MARGIN + 90 + 720 * min(1.0, t / max(1.0, dur * 0.8))
        draw_car(d, cx, 1040, s=0.78, led=0.35 + 0.45 * abs(math.sin(t * 4.0)),
                 led_col=C_LAMP, drive=t * 3.0)
        d.text((cx, 1160), "走了 %d 厘米" % int(30 + 600 * min(1.0, t / max(1.0, dur * 0.8))),
               font=font(27, True), fill=INK_SOFT, anchor="mm")
        d.rounded_rectangle([MARGIN + 20, 900, MARGIN + 300, 980], 22, fill=C_BOT)
        d.text((MARGIN + 160, 940), "走得又稳又直！", font=font(30, True),
               fill=WHITE, anchor="mm")
        note_bar(img, "两个轮子转得一样快，它就走直线", "差一点点，它就会歪到一边去", accent=C_BOT)
        wipe_in(img, C_BOT, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v10
def v10_code_avoid(dur):
    w = SegWriter("v10_code_avoid")
    lines = [
        ("d = sonar.read();   // 量一下距离", ORANGE),
        ("if (d < 20) { back(); turnLeft(); }", None),
        ("else { forward(); }", None),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.4 else (2 if t < 3.8 else 3)
        chip_head(img, "程序 ② 看见箱子就躲开", C_EYE, WHITE, size=34)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 560), lines, n=n)
        k = min(1.0, t / max(1.0, dur * 0.55))
        cm = int(95 - 80 * k)
        danger = cm <= 20
        distance_bar(d, (MARGIN, 590, W - MARGIN, 780), cm, label="离箱子还有多远")
        floor(d, 1040)
        box_x = 900
        draw_box(d, box_x, 1040, w=118, h=134, label="纸箱")
        cx = 200 + 480 * k
        back = 0.0
        turn = 0.0
        if danger:
            back = 1.0
            turn = 1.0
            cx = 680 - 200 * min(1.0, (t - dur * 0.55) / (dur * 0.25))
        draw_car(d, cx, 1040, s=0.78, led=(0.9 if danger else 0.3),
                 led_col=(C_ALERT if danger else C_LAMP), drive=t * 3.0,
                 turn=turn, back=back)
        if danger:
            d.rounded_rectangle([MARGIN + 20, 850, MARGIN + 320, 930], 22, fill=C_ALERT)
            d.text((MARGIN + 170, 890), "停！后退！左转！", font=font(30, True),
                   fill=WHITE, anchor="mm")
        note_bar(img, "小于 20 厘米就躲开", "停一下、往后退，再转个弯继续巡逻", accent=C_EYE)
        wipe_in(img, C_EYE, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v11
def v11_code_report(dur):
    w = SegWriter("v11_code_report")
    lines = [
        ("if (pir) {            // 有人！", ORANGE),
        ("  led.blink(); arm.wave();", None),
        ("  say(\"发现有人\"); count++; }", None),
    ]
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        n = 1 if t < 1.2 else (2 if t < 3.2 else 3)
        chip_head(img, "程序 ③ 看见人就报告", C_ARM, INK)
        code_reveal(img, (MARGIN, 170, W - MARGIN, 560), lines, n=n)
        pill_row(img, (MARGIN, 580, W - MARGIN, 700), [
            (C_LAMP, "小灯笼闪", "一闪一闪"),
            (C_ARM, "小胳膊挥", "挥三下"),
            (C_MOUTH, "小喇叭喊", "发现有人"),
            (C_BOT, "记一次", "第几次巡逻"),
        ])
        floor(d, 1040)
        wave = t if t > 1.0 else 0.0
        draw_car(d, 300, 1040, s=0.82, led=0.9 * abs(math.sin(t * 6.0)),
                 led_col=C_ALERT, wave=wave)
        draw_person(d, 780, 1040, s=0.92, walk=t * 2.0, wave=max(0.0, t - 1.4))
        if t > 1.6:
            bubble(d, (400, 760, 900, 930), "发现有人！", "一号机器人，正在巡逻！",
                   color=C_ALERT, tail=(470, 930))
            d.rounded_rectangle([MARGIN + 20, 760, MARGIN + 250, 830], 22, fill=C_BOT)
            d.text((MARGIN + 135, 795), "第 1 次报告", font=font(27, True),
                   fill=WHITE, anchor="mm")
        note_bar(img, "看见人：小灯闪、胳膊挥、喇叭喊", "还记下这是今天第几次报告", accent=C_ARM)
        wipe_in(img, C_ARM, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v14
def v14_test_cruise(dur):
    w = SegWriter("v14_test_cruise")
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        chip_head(img, "实测 ① 沿着胶带巡逻", C_BOT, WHITE)
        floor(d, 1120)
        tape_path(d, 1120 + 6, MARGIN + 30, W - MARGIN - 30)
        d.rounded_rectangle([MARGIN + 10, 1000, MARGIN + 60, 1120], 10, fill=(120, 196, 120),
                            outline=(70, 150, 80), width=4)
        d.text((MARGIN + 35, 950), "起点", font=font(26, True), fill=INK_SOFT, anchor="mm")
        d.rounded_rectangle([W - MARGIN - 60, 1000, W - MARGIN - 10, 1120], 10, fill=(244, 160, 160),
                            outline=(200, 90, 90), width=4)
        d.text((W - MARGIN - 35, 950), "终点", font=font(26, True), fill=INK_SOFT, anchor="mm")
        k = min(1.0, t / max(1.0, dur * 0.86))
        cx = MARGIN + 80 + 760 * k
        draw_car(d, cx, 1120, s=0.82, led=0.35 + 0.5 * abs(math.sin(t * 5.0)),
                 led_col=C_LAMP, drive=t * 3.0)
        d.rounded_rectangle([MARGIN, 830, MARGIN + 330, 920], 26, fill=(255, 253, 246),
                            outline=(228, 216, 192), width=3)
        d.text((MARGIN + 165, 858), "已经走了", font=font(26, True), fill=INK_SOFT, anchor="mm")
        d.text((MARGIN + 165, 898), "%d 厘米" % int(20 + 700 * k), font=font(34, True),
               fill=C_BOT, anchor="mm")
        d.rounded_rectangle([MARGIN + 360, 830, MARGIN + 700, 920], 26, fill=C_BOT)
        d.text((MARGIN + 530, 875), "一点都没有歪！", font=font(30, True),
               fill=WHITE, anchor="mm")
        note_bar(img, "它沿着胶带稳稳地走", "两个轮子一样快，所以一点都不歪", accent=C_BOT)
        wipe_in(img, C_BOT, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v15
def v15_test_avoid(dur):
    w = SegWriter("v15_test_avoid")
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        chip_head(img, "实测 ② 遇到纸箱绕开", C_EYE, WHITE)
        floor(d, 1120)
        box_x = 880
        draw_box(d, box_x, 1120, w=124, h=140, label="纸箱")
        phase = t / max(1.0, dur)
        if phase < 0.45:
            cx = 200 + 400 * (phase / 0.45)
            cm = 95 - 80 * (phase / 0.45)
            turn = 0.0
            back = 0.0
        elif phase < 0.66:
            cx = 600 - 170 * ((phase - 0.45) / 0.21)
            cm = 15
            turn = 1.0
            back = 1.0
        else:
            cx = 430 + 300 * ((phase - 0.66) / 0.34)
            cm = 15 + 70 * ((phase - 0.66) / 0.34)
            turn = 0.0
            back = 0.0
        draw_car(d, cx, 1120, s=0.82, led=(0.9 if turn else 0.35),
                 led_col=(C_ALERT if turn else C_LAMP), drive=t * 3.0,
                 turn=turn, back=back)
        distance_bar(d, (MARGIN, 800, W - MARGIN, 990), cm, label="离箱子还有多远")
        if turn:
            d.rounded_rectangle([MARGIN, 700, MARGIN + 330, 780], 22, fill=C_ALERT)
            d.text((MARGIN + 165, 740), "停！往后退，左转！", font=font(29, True),
                   fill=WHITE, anchor="mm")
        note_bar(img, "前面只剩 15 厘米，它马上绕开", "停一下、往后退、左转九十度，再接着走", accent=C_EYE)
        wipe_in(img, C_EYE, t, 0.30)
        w.add(img)
    return w.close()


# ------------------------------------------------------------------ v16
def v16_test_hello(dur):
    w = SegWriter("v16_test_hello")
    for i in range(int(dur * FPS)):
        t = i / float(FPS)
        img = paper().convert("RGBA")
        d = ImageDraw.Draw(img)
        chip_head(img, "实测 ③ 看到人就报告", C_ARM, INK)
        floor(d, 1120)
        k = min(1.0, t / max(1.0, dur * 0.42))
        px = 1000 - 400 * k
        found = t > dur * 0.44
        draw_person(d, px, 1120, s=0.95, walk=t * 2.2, wave=max(0.0, t - dur * 0.5))
        wave = (t - dur * 0.44) if found else 0.0
        draw_car(d, 300, 1120, s=0.86,
                 led=(0.95 * abs(math.sin(t * 7.0)) if found else 0.3),
                 led_col=(C_ALERT if found else C_LAMP), wave=wave)
        if found:
            bubble(d, (430, 740, 930, 910), "发现有人！", "一号机器人，正在巡逻！",
                   color=C_ALERT, tail=(500, 910))
            d.rounded_rectangle([MARGIN + 20, 740, MARGIN + 280, 812], 22, fill=C_BOT)
            d.text((MARGIN + 150, 776), "第 2 次报告", font=font(27, True),
                   fill=WHITE, anchor="mm")
            d.rounded_rectangle([MARGIN, 850, MARGIN + 330, 930], 22, fill=(255, 253, 246),
                                outline=(228, 216, 192), width=3)
            d.text((MARGIN + 165, 890), "小耳朵听见啦！", font=font(29, True),
                   fill=C_EAR, anchor="mm")
        note_bar(img, "小朋友一走近，它马上报告", "小灯闪、胳膊挥、喇叭喊，一样都不少", accent=C_ARM)
        wipe_in(img, C_ARM, t, 0.30)
        w.add(img)
    return w.close()


def build_anims(segdur):
    """Render every animated segment to its exact narration length."""
    return {
        "v09_code_cruise": v09_code_cruise(segdur["v09_code_cruise"]),
        "v10_code_avoid": v10_code_avoid(segdur["v10_code_avoid"]),
        "v11_code_report": v11_code_report(segdur["v11_code_report"]),
        "v14_test_cruise": v14_test_cruise(segdur["v14_test_cruise"]),
        "v15_test_avoid": v15_test_avoid(segdur["v15_test_avoid"]),
        "v16_test_hello": v16_test_hello(segdur["v16_test_hello"]),
    }
