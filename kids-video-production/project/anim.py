# -*- coding: utf-8 -*-
"""anim.py - the animated segments for this film.

Four kinds of motion carry the film:
  * code reveal - lines type in one at a time, then a key line is highlighted
  * flow chart - the decision tree lights up step by step
  * live demo  - a car drives a taped track, hits an obstacle, backs up, turns

Every segment is cut to the exact length of its narration beat, so picture
and voice stay locked. The pipeline calls build_anims(segdur) and takes the
returned {name: path} map.

Frame streaming: raw RGB goes straight into ffmpeg's stdin, no PNG buffer.
"""
import os
import math
import subprocess

from PIL import Image, ImageDraw, ImageFilter

from design import *
from project import REAL, BUILD

ANIM = os.path.join(BUILD, "anim")
os.makedirs(ANIM, exist_ok=True)

CODE_SETUP = [
    ("#include <Ultrasonic.h>", 0),
    ("Ultrasonic sensor(9, 10);   // 超声波传感器", 0),
    ("", 0),
    ("int IN1 = 4, IN2 = 5;      // 左侧电机", 0),
    ("int ENA = 6, ENB = 7;      // 速度调节", 0),
    ("", 0),
    ("void setup() {", 0),
    ("  pinMode(IN1, OUTPUT);", 1),
    ("  pinMode(IN2, OUTPUT);", 1),
    ("  pinMode(ENA, OUTPUT);", 1),
    ("  pinMode(ENB, OUTPUT);", 1),
    ("  Serial.begin(9600);", 1),
    ("}", 0),
]

CODE_LOOP = [
    ("void loop() {", 0),
    ("  long d = sensor.measure();  // 量距离", 1),
    ("  if (d < 30 && d > 5) {      // 太近了！", 1),
    ("    backward();               // 后退", 2),
    ("    turnRight();              // 右转", 2),
    ("  } else {", 1),
    ("    forward();                // 前进", 2),
    ("  }", 0),
    ("}", 0),
]


def code_panel(lines, box, hi=None, page=1, pages=2, title="sketch.ino", upto=None):
    x0, y0, x1, y1 = [int(v) for v in box]
    w, h = x1 - x0, y1 - y0
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rounded(img, [0, 0, w, h], 30, fill=CODE_BG)
    rounded(img, [0, 0, w, 76], 30, fill=(44, 47, 66))
    d.rectangle([0, 46, w, 76], fill=(44, 47, 66))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([26 + i * 34, 24, 48 + i * 34, 46], fill=c)
    d.text((150, 36), title, font=font(32, False, mono=True), fill=(190, 196, 214), anchor="lm")
    d.text((w - 26, 36), f"{page}/{pages}", font=font(30, False), fill=(120, 126, 148), anchor="rm")
    d.line([0, 76, w, 76], fill=(64, 68, 92), width=2)
    lh = 52
    for idx, (txt, indent) in enumerate(lines):
        if upto is not None and idx >= upto:
            break
        yy = 106 + idx * lh
        if yy + lh > h - 12:
            break
        if hi and idx in hi:
            d.rounded_rectangle([12, yy - 6, w - 12, yy + lh - 6], 10, fill=(54, 62, 96))
            d.rectangle([12, yy - 6, 18, yy + lh - 6], fill=ORANGE)
        d.text((40, yy), str(idx + 1).rjust(2), font=font(30, False, mono=True), fill=(92, 98, 124), anchor="lm")
        draw_code(d, 108 + indent * 26, yy, txt)
    return img


class SegWriter:
    """Stream RGB frames straight into ffmpeg (no frame buffering)."""

    def __init__(self, name, w=W, h=H, fps=30):
        self.name = name
        self.out = os.path.join(ANIM, name + ".mp4")
        self.n = 0
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
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


def pop(s):
    """0..1 pop scale factor."""
    return 1.0 + 0.06 * math.sin(s * math.pi) * (1 - s) * 3


# ------------------------------------------------------------------ v09
def v09_code_setup(segdur):
    dur, fps = segdur["v09_code_setup"], 30
    rev0, rev_step, note_t = 0.28, dur * 0.057, dur * 0.80
    box = (MARGIN, 300, W - MARGIN, 1120)
    base = paper().convert("RGBA")
    d = ImageDraw.Draw(base)
    chip(base, MARGIN, 76, "写程序 · 第 1 段", bg=BLUE, fg=WHITE, size=36, padx=28, pady=14)
    d.text((MARGIN, 200), "setup：先做准备", font=font(70, True), fill=INK, anchor="lm")
    shadowed(base, box, 30, blur=30, alpha=46, offset=(0, 12))
    panels = [code_panel(CODE_SETUP, box, upto=n) for n in range(len(CODE_SETUP) + 1)]
    note_box = (MARGIN, 1150, W - MARGIN, 1300)
    w = SegWriter("v09_code_setup")
    for i in range(int(dur * fps)):
        t = i / fps
        f = base.copy()
        n = 0
        while n < len(CODE_SETUP) and t >= rev0 + n * rev_step:
            n += 1
        f.alpha_composite(panels[n], (box[0], box[1]))
        # flash the newest line
        if 0 < n <= len(CODE_SETUP):
            age = t - (rev0 + (n - 1) * rev_step)
            if 0 <= age < 0.45:
                a = int(120 * (1 - age / 0.45))
                ly = box[1] + 106 + (n - 1) * 52 - 6
                lay = Image.new("RGBA", f.size, (0, 0, 0, 0))
                ld = ImageDraw.Draw(lay)
                ld.rectangle([box[0] + 12, ly, W - MARGIN - 12, ly + 52], fill=(245, 166, 35, a // 3))
                ld.rectangle([box[0] + 12, ly, box[0] + 19, ly + 52], fill=(245, 166, 35, min(255, a + 60)))
                f.alpha_composite(lay)
        if t > note_t:
            a = int(255 * ease((t - note_t) / 0.5))
            lay = Image.new("RGBA", f.size, (0, 0, 0, 0))
            ImageDraw.Draw(lay).rounded_rectangle(note_box, 26, fill=(255, 253, 246, a),
                                                  outline=(228, 216, 192, a), width=3)
            ImageDraw.Draw(lay).rounded_rectangle([note_box[0] + 26, note_box[1] + 24,
                                                   note_box[0] + 36, note_box[3] - 24], 5, fill=ORANGE)
            ImageDraw.Draw(lay).text((note_box[0] + 58, note_box[1] + 46),
                                     "setup 只在开机时执行一次", font=font(40, True),
                                     fill=INK + (a,), anchor="lm")
            ImageDraw.Draw(lay).text((note_box[0] + 58, note_box[1] + 100),
                                     "把引脚和串口准备好，就可以开机跑啦", font=font(30, False),
                                     fill=INK_SOFT + (a,), anchor="lm")
            f.alpha_composite(lay)
        w.add(f)
    return w.close()


# ------------------------------------------------------------------ v10
def v10_code_loop(segdur):
    dur, fps = segdur["v10_code_loop"], 30
    rev0, rev_step = 0.26, dur * 0.057
    h1, h2, h3 = dur * 0.56, dur * 0.72, dur * 0.86
    box = (MARGIN, 290, W - MARGIN, 880)
    base = paper().convert("RGBA")
    d = ImageDraw.Draw(base)
    chip(base, MARGIN, 76, "写程序 · 第 2 段", bg=GREEN, fg=WHITE, size=36, padx=28, pady=14)
    d.text((MARGIN, 190), "loop：一遍遍重复", font=font(70, True), fill=INK, anchor="lm")
    shadowed(base, box, 30, blur=30, alpha=46, offset=(0, 12))
    n_l = len(CODE_LOOP)
    panels = {n: code_panel(CODE_LOOP, box, upto=n) for n in range(n_l + 1)}
    panels[(n_l, 0)] = code_panel(CODE_LOOP, box)
    panels[(n_l, 2)] = code_panel(CODE_LOOP, box, hi={2})
    panels[(n_l, 4)] = code_panel(CODE_LOOP, box, hi={3, 4})
    panels[(n_l, 6)] = code_panel(CODE_LOOP, box, hi={6})
    note_box = (MARGIN, 920, W - MARGIN, 1300)
    w = SegWriter("v10_code_loop")
    for i in range(int(dur * fps)):
        t = i / fps
        f = base.copy()
        n = 0
        while n < n_l and t >= rev0 + n * rev_step:
            n += 1
        if n < n_l:
            panel = panels[n]
        else:
            key = (n_l, 0)
            if t >= h1:
                key = (n_l, 2)
            if t >= h2:
                key = (n_l, 4)
            if t >= h3:
                key = (n_l, 6)
            panel = panels[key]
        f.alpha_composite(panel, (box[0], box[1]))
        if n == n_l and t >= h1:
            a = int(255 * ease((t - h1) / 0.4))
            lay = Image.new("RGBA", f.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            ld.rounded_rectangle(note_box, 26, fill=(255, 253, 246, a),
                                 outline=(228, 216, 192, a), width=3)
            ld.rounded_rectangle([note_box[0] + 26, note_box[1] + 24, note_box[0] + 36,
                                  note_box[3] - 24], 5, fill=GREEN)
            ld.text((note_box[0] + 58, note_box[1] + 46), "d < 30  →  太近了！",
                    font=font(40, True), fill=RED + (a,), anchor="lm")
            ld.text((note_box[0] + 58, note_box[1] + 100), "后退一步，再向右转",
                    font=font(30, False), fill=INK_SOFT + (a,), anchor="lm")
            if t >= h3:
                b = int(255 * ease((t - h3) / 0.35))
                ld.text((note_box[0] + 58, note_box[1] + 186), "否则  →  继续前进",
                        font=font(40, True), fill=GREEN + (b,), anchor="lm")
                ld.text((note_box[0] + 58, note_box[1] + 240), "这就是“如果 A，就 B”",
                        font=font(30, False), fill=INK_SOFT + (b,), anchor="lm")
            f.alpha_composite(lay)
        w.add(f)
    return w.close()


# ------------------------------------------------------------------ v11
def flow_node(img, box, text, sub=None, fill=WHITE, border=BLUE, tcol=INK, scale=1.0, alpha=255):
    d = ImageDraw.Draw(img)
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    bw = (box[2] - box[0]) * scale
    bh = (box[3] - box[1]) * scale
    b = [cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2]
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle(b, 26, fill=fill + (alpha,), outline=border + (alpha,), width=5)
    ld.text((cx, cy - (16 if sub else 0)), text, font=font(44, True), fill=tcol + (alpha,), anchor="mm")
    if sub:
        ld.text((cx, cy + 34), sub, font=font(28, False), fill=INK_SOFT + (alpha,), anchor="mm")
    img.alpha_composite(lay)


def arrow_down(img, x, y0, y1, col=BLUE, alpha=255, w=7):
    d = ImageDraw.Draw(img)
    d.line([x, y0, x, y1 - 18], fill=col + (alpha,), width=w)
    d.polygon([(x - 14, y1 - 20), (x + 14, y1 - 20), (x, y1)], fill=col + (alpha,))


def arrow_right(img, x0, x1, y, col=BLUE, alpha=255, w=7):
    d = ImageDraw.Draw(img)
    d.line([x0, y, x1 - 18, y], fill=col + (alpha,), width=w)
    d.polygon([(x1 - 20, y - 14), (x1 - 20, y + 14), (x1, y)], fill=col + (alpha,))


def v11_flow(segdur):
    dur, fps = segdur["v11_flow"], 30
    tB, tC, tD, tN = dur * 0.14, dur * 0.30, dur * 0.52, dur * 0.68
    base = paper().convert("RGBA")
    d = ImageDraw.Draw(base)
    chip(base, MARGIN, 76, "程序的思路", bg=ORANGE, fg=INK, size=36, padx=28, pady=14)
    d.text((MARGIN, 196), "小车每秒钟想一遍", font=font(66, True), fill=INK, anchor="lm")
    A = (250, 300, 830, 440)
    B = (150, 540, 930, 690)
    C = (60, 840, 480, 990)
    D = (600, 840, 1020, 990)
    w = SegWriter("v11_flow")
    for i in range(int(dur * fps)):
        t = i / fps
        f = base.copy()
        aA = int(255 * ease(t / (dur * 0.08))) if t < dur * 0.08 else 255
        aB = int(255 * ease((t - tB) / (dur * 0.08))) if t >= tB else 0
        aC = int(255 * ease((t - tC) / (dur * 0.08))) if t >= tC else 0
        aD = int(255 * ease((t - tD) / (dur * 0.08))) if t >= tD else 0
        flow_node(f, A, "① 超声波测距", "量出前方多远", border=BLUE, alpha=aA)
        flow_node(f, B, "② 距离 d < 30 厘米？", border=ORANGE, tcol=INK, alpha=aB)
        flow_node(f, C, "是：后退 + 右转", border=RED, tcol=RED, alpha=aC)
        flow_node(f, D, "否：继续前进", border=GREEN, tcol=GREEN, alpha=aD)
        if aB:
            arrow_down(f, W / 2, 448, 532, BLUE, aB)
        if aC:
            arrow_down(f, 270, 700, 830, RED, aC)
        if aD:
            arrow_down(f, 810, 700, 830, GREEN, aD)
        if aC:
            d2 = ImageDraw.Draw(f)
            lbl = "是" if t > tC else ""
            d2.text((300, 762), lbl, font=font(34, True), fill=RED, anchor="mm")
            d2.text((780, 762), "否" if t > tD else "", font=font(34, True), fill=GREEN, anchor="mm")
        if t > tN:
            a = int(255 * ease((t - tN) / 0.4))
            lay = Image.new("RGBA", f.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            ld.rounded_rectangle([MARGIN, 1050, W - MARGIN, 1300], 26, fill=(255, 253, 246, a),
                                 outline=(228, 216, 192, a), width=3)
            ld.rounded_rectangle([MARGIN + 26, 1072, MARGIN + 36, 1278], 5, fill=BLUE)
            ld.text((MARGIN + 58, 1104), "量一量 → 想一想 → 动一动", font=font(40, True),
                    fill=INK + (a,), anchor="lm")
            ld.text((MARGIN + 58, 1160), "loop 一秒钟跑一遍，所以它会一直躲", font=font(30, False),
                    fill=INK_SOFT + (a,), anchor="lm")
            ld.text((MARGIN + 58, 1216), "这跟人做判断的顺序一模一样", font=font(30, False),
                    fill=INK_SOFT + (a,), anchor="lm")
            f.alpha_composite(lay)
        w.add(f)
    return w.close()


# ------------------------------------------------------------------ v14
def floor_bg():
    img = Image.new("RGB", (W, H), (206, 170, 122))
    d = ImageDraw.Draw(img)
    rnd = __import__("random").Random(4)
    for i in range(0, H, 96):
        d.rectangle([0, i, W, i + 92], fill=(211, 176, 128) if i // 96 % 2 == 0 else (202, 166, 119))
    for _ in range(260):
        x = rnd.randrange(W); y = rnd.randrange(H); ln = rnd.randint(30, 160)
        d.line([x, y, x + ln, y + rnd.randint(-2, 2)], fill=(196, 160, 114), width=rnd.choice([1, 1, 2]))
    return img.filter(ImageFilter.GaussianBlur(0.6))


def car_sprite():
    s = 200
    c = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([42, 40, 158, 160], 20, fill=(56, 158, 160), outline=(30, 96, 100), width=5)
    d.rounded_rectangle([58, 62, 142, 108], 12, fill=(96, 200, 200))
    for cx in (72, 128):
        d.ellipse([cx - 20, 30, cx + 20, 70], fill=(52, 58, 68))
        d.ellipse([cx - 9, 41, cx + 9, 59], fill=(150, 158, 170))
    for cx in (72, 128):
        d.ellipse([cx - 20, 130, cx + 20, 170], fill=(52, 58, 68))
        d.ellipse([cx - 9, 141, cx + 9, 159], fill=(150, 158, 170))
    d.rounded_rectangle([78, 12, 122, 46], 12, fill=(70, 96, 130), outline=(40, 58, 84), width=4)
    d.ellipse([86, 20, 98, 32], fill=(150, 200, 235))
    d.ellipse([102, 20, 114, 32], fill=(150, 200, 235))
    d.ellipse([86, 118, 100, 132], fill=(255, 255, 255), outline=(40, 90, 96), width=3)
    d.ellipse([100, 118, 114, 132], fill=(255, 255, 255), outline=(40, 90, 96), width=3)
    d.ellipse([89, 121, 96, 128], fill=(40, 44, 52))
    d.ellipse([103, 121, 110, 128], fill=(40, 44, 52))
    return c


def v14_test_drive(segdur):
    dur, fps = segdur["v14_test_drive"], 30
    T0, T1, T2, T3, T4, T5 = (dur * 0.10, dur * 0.45, dur * 0.59, dur * 0.73,
                              dur * 0.80, dur * 0.94)
    bg = floor_bg()
    car = car_sprite()
    photo = os.path.join(REAL, "px_7868822.jpg")
    w = SegWriter("v14_test_drive")
    track_v = (W / 2, 1080, W / 2, 400)
    track_h = (W / 2, 740, 990, 740)
    for i in range(int(dur * fps)):
        t = i / fps
        f = bg.copy().convert("RGBA")
        d = ImageDraw.Draw(f)
        # taped track
        d.line([track_v[0], track_v[1], track_v[2], track_v[3]], fill=(252, 250, 244), width=26)
        d.line([track_h[0], track_h[1], track_h[2], track_h[3]], fill=(252, 250, 244), width=26)
        d.line([track_v[0], track_v[1], track_v[2], track_v[3]], fill=(214, 210, 200), width=2)
        d.line([track_h[0], track_h[1], track_h[2], track_h[3]], fill=(214, 210, 200), width=2)
        # obstacle box
        bx, by = W / 2 - 80, 330
        d.rounded_rectangle([bx, by, bx + 156, by + 150], 10, fill=(186, 140, 84),
                            outline=(140, 102, 58), width=5)
        d.line([bx, by + 52, bx + 156, by + 52], fill=(140, 102, 58), width=4)
        d.line([bx + 78, by, bx + 78, by + 52], fill=(140, 102, 58), width=4)
        d.text((bx + 78, by + 104), "障碍", font=font(40, True), fill=(96, 66, 34), anchor="mm")

        # ---- car path
        cx, cy, ang = W / 2, 1020, 0
        dist, status, flash = 100, "前进中", False
        if t < T0:
            pass
        elif t < T1:
            p = ease((t - T0) / (T1 - T0))
            cy = 1020 - p * 470
            dist = int(100 - p * 60)
        elif t < T2:
            cy = 550
            dist = 28
            status = "前方有障碍！"
            flash = True
        elif t < T3:
            p = ease((t - T2) / (T3 - T2))
            cy = 550 + p * 190
            dist = 28 + int(p * 18)
            status = "后退！"
        elif t < T4:
            cy = 740
            ang = -p_ease(t, T3, T4) * 90
            dist = 46
            status = "右转"
        else:
            p = ease((t - T4) / max(0.2, dur - T4 - 0.2))
            cx = W / 2 + p * 400
            cy = 740
            status = "绕开啦，继续前进！"
            dist = 0

        # trail
        if t >= T1:
            d.line([W / 2, 1020, W / 2, 550], fill=(245, 166, 35), width=8)
        if t >= T3:
            d.line([W / 2, 550, W / 2, 740], fill=(245, 166, 35), width=8)
        if t >= T4:
            d.line([W / 2, 740, W / 2 + 400 * ease((t - T4) / max(0.2, dur - T4 - 0.2)), 740],
                   fill=(245, 166, 35), width=8)

        c = car.rotate(-ang, resample=Image.BICUBIC, expand=True)
        f.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))

        # HUD
        chip(f, MARGIN, 70, f"前方距离 {dist} cm", bg=(255, 255, 255) if not flash else (255, 226, 220),
             fg=INK if not flash else RED, size=38, padx=28, pady=14)
        if flash:
            lay = Image.new("RGBA", f.size, (0, 0, 0, 0))
            ImageDraw.Draw(lay).rounded_rectangle(
                [MARGIN - 6, 64, MARGIN + 300, 140], 38, outline=(228, 87, 46, 210), width=5)
            f.alpha_composite(lay)
        sc = (232, 87, 46) if flash else (54, 162, 105)
        chip(f, MARGIN, 152, status, bg=sc, fg=WHITE, size=36, padx=26, pady=12)

        # real-photo inset
        ins = Image.open(photo).convert("RGB")
        iw, ih = ins.size
        ins = ins.crop((int(iw * 0.47), int(ih * 0.40), int(iw * 0.86), int(ih * 0.94)))
        ins = ins.resize((260, 260), Image.LANCZOS)
        im = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle([0, 0, 259, 259], 22, fill=(255, 255, 255, 255))
        f.alpha_composite(im, (W - MARGIN - 260, 66))
        f.paste(ins, (W - MARGIN - 260, 66))
        dd = ImageDraw.Draw(f)
        dd.rounded_rectangle([W - MARGIN - 260, 66, W - MARGIN, 326], 22, outline=(255, 255, 255), width=8)
        dd.text((W - MARGIN - 130, 344), "实拍", font=font(30, True), fill=(255, 255, 255),
                anchor="mm", stroke_width=5, stroke_fill=(60, 46, 30))

        if t > T5:
            a = int(255 * ease((t - T5) / 0.4))
            lay = Image.new("RGBA", f.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            ld.rounded_rectangle([MARGIN, 1130, W - MARGIN, 1290], 26, fill=(255, 253, 246, a),
                                 outline=(54, 162, 105, a), width=4)
            check_icon(ld, W / 2 - 132, 1182, 24, color=(54, 162, 105, a))
            ld.text((W / 2 + 14, 1182), "成功绕开！", font=font(48, True), fill=(54, 162, 105, a), anchor="mm")
            ld.text((W / 2, 1240), "小车会自己躲开障碍物了", font=font(30, False),
                    fill=INK_SOFT + (a,), anchor="mm")
            f.alpha_composite(lay)
        w.add(f)
    return w.close()


def p_ease(t, a, b):
    return ease((t - a) / (b - a))


def build_anims(segdur):
    """Render every animated segment. Returns {name: path}."""
    return {
        "v09_code_setup": v09_code_setup(segdur),
        "v10_code_loop": v10_code_loop(segdur),
        "v11_flow": v11_flow(segdur),
        "v14_test_drive": v14_test_drive(segdur),
    }


if __name__ == "__main__":
    for name in build_anims({}):
        print("  anim", name)
