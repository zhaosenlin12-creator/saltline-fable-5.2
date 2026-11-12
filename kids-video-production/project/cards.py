# -*- coding: utf-8 -*-
"""cards.py - draw the static cards for this film.

The drawing code below is the house layout that produced the reference film
"智能小车_制作到实测.mp4". Edit the wording and the art references to change
the topic; keep the layout rules.

Layout rules:
  * Content must stop above BOT (1520). Captions occupy 1555-1635.
  * One idea per card: title on top, one visual, one short takeaway.
  * Keep the cream margin - never bleed artwork edge to edge except photos.
  * Step badges number the build steps, and the badge word must match what
    the narration says at that moment.

The pipeline calls build_cards() and saves whatever comes back, so this
module never writes files itself.
"""
import os
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from design import *
from project import AI_FILE, AI, REAL

BOT = 1520          # content must stop here - captions live below

BOT = 1520          # content must stop here - captions live below


def top_chip(img, text, color=ORANGE, fg=INK, x=MARGIN, y=76, size=38):
    return chip(img, x, y, text, bg=color, fg=fg, size=size, padx=30, pady=16)


def badge_step(img, x, y, num, label, color=BLUE):
    d = ImageDraw.Draw(img)
    r = 40
    d.ellipse([x, y, x + r * 2, y + r * 2], fill=color, outline=WHITE, width=5)
    d.text((x + r, y + r), str(num), font=font(52, True), fill=WHITE, anchor="mm")
    f = font(44, True)
    tw = text_w(d, label, f)
    rounded(img, [x + r * 2 + 16, y + 8, x + r * 2 + 16 + tw + 40, y + r * 2 - 8], (r * 2 - 16) // 2,
            fill=WHITE, outline=color, width=4)
    d.text((x + r * 2 + 36, y + r), label, font=f, fill=color, anchor="lm")


def paper_card(img, box, radius=28, alpha=250):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle(box, radius=radius, fill=(255, 253, 246, alpha),
                                          outline=(228, 216, 192, 255), width=3)
    shadowed(img, box, radius, blur=26, alpha=44, offset=(0, 10))
    img.alpha_composite(lay)


def part_grid(img, box, items):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    cols, rows = 3, 2
    cw = (x1 - x0) / cols
    ch = (y1 - y0) / rows
    for i, (col, name, note) in enumerate(items):
        cx = x0 + (i % cols) * cw
        cy = y0 + (i // cols) * ch
        box = [cx + 12, cy + 10, cx + cw - 12, cy + ch - 14]
        paper_card(img, box, radius=24)
        d.ellipse([box[0] + 20, box[1] + 24, box[0] + 20 + 46, box[1] + 70], fill=col)
        d.text((box[0] + 43, box[1] + 47), str(i + 1), font=font(30, True), fill=WHITE, anchor="mm")
        d.text((box[0] + 84, box[1] + 34), name, font=font(40, True), fill=INK, anchor="lm")
        d.text((box[0] + 84, box[1] + 84), note, font=font(30, False), fill=INK_SOFT, anchor="lm")


def banner(img, box, text, sub=None, accent=ORANGE, size=44):
    paper_card(img, box, radius=26)
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0 + 26, y0 + 24, x0 + 36, y1 - 24], 5, fill=accent)
    cy = y0 + (y1 - y0) / 2 - (14 if sub else 0)
    d.text((x0 + 58, cy), text, font=font(size, True), fill=INK, anchor="lm")
    if sub:
        d.text((x0 + 58, cy + 46), sub, font=font(30, False), fill=INK_SOFT, anchor="lm")


def hero(img, path, box, radius=36, focus=(0.5, 0.5)):
    shadowed(img, box, radius, blur=30, alpha=46, offset=(0, 12))
    paste_cover(img, path, box, radius=radius, focus=focus)


def illus(img, path, box, feather=34):
    paste_soft(img, path, box, feather=feather)


_CARDS = {}


def save(img, name):
    """Collect a finished card; the pipeline writes it to build/cards/."""
    _CARDS[name] = img


# ------------------------------------------------------------------ cards
def c_cover():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    chip(img, MARGIN, 96, "科学小实验 · 第 01 讲", bg=BLUE, fg=WHITE, size=36, padx=28, pady=14)
    text_outline(d, (MARGIN, 186), "自己会躲障碍的", font(84, True), fill=INK, outline=(255, 253, 246), width=7)
    d.rounded_rectangle([MARGIN - 6, 300, MARGIN + 560, 442], 24, fill=ORANGE)
    text_outline(d, (MARGIN + 14, 312), "智能小车", font(112, True), fill=WHITE, outline=(180, 106, 10), width=5)
    d.text((MARGIN, 486), "搭小车 → 写程序 → 落地实测，全程零成本", font=font(40, False), fill=INK_SOFT, anchor="lm")
    illus(img, os.path.join(AI, AI_FILE["v01_cover"]), (MARGIN, 560, W - MARGIN, 1860))
    sparkle_field(d, seed=5, n=16, box=(MARGIN, 60, W - MARGIN, 520))
    save(img, "v01_cover")


def c_parts_photo():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    paste_cover(img, os.path.join(REAL, "px_35673081.jpg"), (0, 0, W, 840), focus=(0.5, 0.45))
    top_chip(img, "① 先认识零件", ORANGE, INK)
    part_grid(img, (MARGIN, 880, W - MARGIN, BOT), [
        (BLUE, "主控板", "Arduino · 小车的大脑"),
        (GREEN, "电机驱动板", "L298N · 帮电机用力气"),
        (ORANGE, "减速电机", "×2 · 小车的两条腿"),
        (RED, "超声波传感器", "HC-SR04 · 小车的眼睛"),
        (BLUE, "面包板 + 杜邦线", "接线不用焊接也能试"),
        (GREEN, "两驱底盘", "轮子 + 万向轮"),
    ])
    save(img, "v02_parts_photo")


def c_parts_ai():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "② 它们的分工", GREEN, WHITE)
    illus(img, os.path.join(AI, AI_FILE["v03_parts_ai"]), (MARGIN, 180, W - MARGIN, 1300))
    y = 1330
    for i, (col, big, small) in enumerate([(RED, "眼睛", "超声波传感器"),
                                          (ORANGE, "腿", "直流电机"),
                                          (BLUE, "大脑", "主控板")]):
        x = MARGIN + i * ((W - 2 * MARGIN) / 3)
        cw = (W - 2 * MARGIN) / 3 - 18
        paper_card(img, [x, y, x + cw, y + 170], radius=24)
        d.ellipse([x + 22, y + 34, x + 92, y + 104], fill=col)
        d.text((x + 57, y + 69), big[0], font=font(42, True), fill=WHITE, anchor="mm")
        d.text((x + 110, y + 64), big, font=font(44, True), fill=INK, anchor="lm")
        d.text((x + 110, y + 116), small, font=font(27, False), fill=INK_SOFT, anchor="lm")
    save(img, "v03_parts_ai")


def c_step_motor():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    badge_step(img, MARGIN, 76, 1, "装底盘", BLUE)
    d.text((MARGIN + 330, 116), "电机 + 轮子", font=font(40, False), fill=INK_SOFT, anchor="lm")
    illus(img, os.path.join(AI, AI_FILE["v04_step_motor"]), (MARGIN, 190, W - MARGIN, 1300))
    banner(img, (MARGIN, 1340, W - MARGIN, BOT), "先把电机拧在底盘两边，再装轮子和万向轮",
           accent=BLUE, size=40)
    save(img, "v04_step_motor")


def c_step_wire():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    badge_step(img, MARGIN, 76, 3, "接线", GREEN)
    d.text((MARGIN + 330, 116), "最关键的一步", font=font(40, False), fill=INK_SOFT, anchor="lm")
    illus(img, os.path.join(AI, AI_FILE["v05_step_wire"]), (MARGIN, 190, W - MARGIN, 1290))
    y = 1320
    labels = [("VCC", "5V", BLUE), ("GND", "GND", GREEN), ("信号线", "电机", ORANGE)]
    for i, (a, b, col) in enumerate(labels):
        x = MARGIN + i * ((W - 2 * MARGIN) / 3)
        cw = (W - 2 * MARGIN) / 3 - 18
        paper_card(img, [x, y, x + cw, y + 190], radius=24)
        d.text((x + cw / 2, y + 62), a, font=font(42, True), fill=INK_SOFT, anchor="mm")
        d.text((x + cw / 2, y + 96), "↓", font=font(38, True), fill=col, anchor="mm")
        d.text((x + cw / 2, y + 142), b, font=font(46, True), fill=col, anchor="mm")
    save(img, "v05_step_wire")


def c_sensor():
    """L06 - 第四步：把超声波传感器架到小车前面。"""
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    badge_step(img, MARGIN, 76, 4, "装传感器", ORANGE)
    d.text((MARGIN + 330, 116), "小车的眼睛要朝前", font=font(40, False), fill=INK_SOFT, anchor="lm")
    illus(img, os.path.join(AI, AI_FILE["v06_wire_real"]), (MARGIN, 190, W - MARGIN, 1290))
    banner(img, (MARGIN, 1330, W - MARGIN, BOT), "把超声波传感器架到前面，牢牢盯着前方",
           accent=ORANGE, size=40)
    save(img, "v06_wire_real")


def c_wire_real():
    """L07 - 接线要小心：正负极接反会烧板子。"""
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    paste_cover(img, os.path.join(REAL, "px_12741836.jpg"), (0, 0, W, 1240), focus=(0.5, 0.45))
    grad = Image.new("L", (1, 220), 0)
    gd = ImageDraw.Draw(grad)
    for i in range(220):
        gd.point((0, i), fill=int(90 * (1 - i / 220.0) ** 2))
    grad = grad.resize((W, 220))
    lay = Image.new("RGBA", (W, 220), (0, 0, 0, 0))
    lay.putalpha(grad)
    img.alpha_composite(lay, (0, 0))
    top_chip(img, "实拍 · 焊点与走线", BLUE, WHITE)
    paper_card(img, [MARGIN, 1330, W - MARGIN, BOT], radius=26)
    d.rounded_rectangle([MARGIN + 26, 1352, MARGIN + 36, BOT - 22], 5, fill=RED)
    warn_icon(d, MARGIN + 76, 1380, 21, color=RED)
    d.text((MARGIN + 108, 1380), "红黑线别接反", font=font(40, True), fill=INK, anchor="lm")
    d.text((MARGIN + 58, 1440), "接反了小车可能一动不动，还可能烧坏板子",
           font=font(30, False), fill=INK_SOFT, anchor="lm")
    save(img, "v07_step_sensor")


def c_code_intro():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "③ 给小车写程序", BLUE, WHITE)
    d.text((MARGIN, 186), "它只要干三件事", font=font(72, True), fill=INK, anchor="lm")
    illus(img, os.path.join(AI, AI_FILE["v08_code_intro"]), (MARGIN, 260, W - MARGIN, 1290))
    y = 1320
    for i, (col, t) in enumerate([(GREEN, "① 往前走"), (BLUE, "② 听距离"), (ORANGE, "③ 转弯躲开")]):
        x = MARGIN + i * ((W - 2 * MARGIN) / 3)
        cw = (W - 2 * MARGIN) / 3 - 18
        paper_card(img, [x, y, x + cw, y + 190], radius=24)
        d.text((x + cw / 2, y + 95), t, font=font(40, True), fill=col, anchor="mm")
    save(img, "v08_code_intro")


def c_robot():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "④ 落地实测", RED, WHITE)
    illus(img, os.path.join(AI, AI_FILE["v12_robot"]), (20, 140, W - 20, 1290))
    bx = (MARGIN, 1330, W - MARGIN, BOT)
    paper_card(img, bx, radius=28)
    d.ellipse([bx[0] + 22, bx[1] + 32, bx[0] + 96, bx[1] + 106], fill=RED)
    d.text((bx[0] + 59, bx[1] + 69), "车", font=font(42, True), fill=WHITE, anchor="mm")
    d.text((bx[0] + 118, bx[1] + 56), "叮！前方有障碍物，", font=font(40, True), fill=INK, anchor="lm")
    d.text((bx[0] + 118, bx[1] + 118), "我左转六十度，继续出发！", font=font(40, True), fill=RED, anchor="lm")
    save(img, "v12_robot")


def c_test_start():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    paste_cover(img, os.path.join(REAL, "px_7868822.jpg"), (0, 0, W, 1240), focus=(0.66, 0.58))
    top_chip(img, "实拍 · 小车组装完成", GREEN, WHITE)
    banner(img, (MARGIN, 1330, W - MARGIN, BOT), "按下上传键 —— 一、二、三，走！",
           accent=RED, size=42)
    save(img, "v13_test_start")


def c_tune():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "调参：让它提前刹车", ORANGE, INK)
    hero(img, os.path.join(REAL, "px_28136812.jpg"), (MARGIN, 190, W - MARGIN, 960),
         radius=32, focus=(0.5, 0.5))
    paper_card(img, [MARGIN, 1000, W - MARGIN, BOT], radius=28)
    d.text((MARGIN + 40, 1055), "障碍距离阈值", font=font(38, True), fill=INK, anchor="lm")
    d.text((MARGIN + 40, 1175), "30", font=font(110, True), fill=(196, 196, 196), anchor="lm")
    d.text((MARGIN + 172, 1180), "厘米", font=font(40, False), fill=INK_SOFT, anchor="lm")
    d.line([MARGIN + 34, 1138, MARGIN + 290, 1138], fill=(205, 205, 205), width=7)
    d.text((MARGIN + 330, 1175), "→", font=font(84, True), fill=ORANGE, anchor="lm")
    d.text((MARGIN + 460, 1175), "20", font=font(110, True), fill=ORANGE, anchor="lm")
    d.text((MARGIN + 608, 1180), "厘米", font=font(40, False), fill=INK, anchor="lm")
    d.text((MARGIN + 40, 1330), "提前 10 厘米刹车，撞车率立刻下降", font=font(36, False),
           fill=INK_SOFT, anchor="lm")
    save(img, "v15_tune")


def c_upgrade():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "⑤ 升级：循迹小车", GREEN, WHITE)
    illus(img, os.path.join(AI, AI_FILE["v16_upgrade"]), (MARGIN, 180, W - MARGIN, 1290))
    paper_card(img, [MARGIN, 1330, W - MARGIN, BOT], radius=26)
    d.rounded_rectangle([MARGIN + 26, 1352, MARGIN + 36, BOT - 22], 5, fill=GREEN)
    d.text((MARGIN + 58, 1382), "再加两个红外传感器，它就能沿着黑线跑",
           font=font(38, True), fill=INK, anchor="lm")
    d.text((MARGIN + 58, 1444), "从“会躲”到“会跟”，程序再写一点点就行", font=font(29, False),
           fill=INK_SOFT, anchor="lm")
    save(img, "v16_upgrade")


def c_summary():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "今天你学会了", BLUE, WHITE)
    illus(img, os.path.join(AI, AI_FILE["v17_summary"]), (MARGIN, 185, W - MARGIN, 850))
    rows = [(RED, "传感器", "负责看", "量出前方有多远"),
            (ORANGE, "电机", "负责走", "前进、后退、转向"),
            (BLUE, "程序", "负责想", "如果……就……否则……")]
    y = 880
    for col, a, b, c in rows:
        paper_card(img, [MARGIN, y, W - MARGIN, y + 200], radius=26)
        d.ellipse([MARGIN + 26, y + 56, MARGIN + 100, y + 130], fill=col)
        d.text((MARGIN + 63, y + 93), a[0], font=font(46, True), fill=WHITE, anchor="mm")
        d.text((MARGIN + 124, y + 72), a, font=font(44, True), fill=INK, anchor="lm")
        d.text((MARGIN + 320, y + 72), b, font=font(44, True), fill=col, anchor="lm")
        d.text((MARGIN + 124, y + 134), c, font=font(32, False), fill=INK_SOFT, anchor="lm")
        y += 220
    save(img, "v17_summary")


def c_cta():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((W / 2, 250), "DIY", font=font(190, True), fill=(214, 82, 72), anchor="mm")
    d.text((W / 2, 400), "零成本，也能做出一辆会思考的小车", font=font(40, False), fill=INK_SOFT,
           anchor="mm")
    illus(img, os.path.join(AI, AI_FILE["v18_cta"]), (60, 430, W - 60, 1180), feather=30)
    sparkle_field(d, seed=11, n=30, box=(70, 180, W - 70, 1180))
    d.text((W / 2, 1300), "点赞  收藏", font=font(96, True), fill=ORANGE, anchor="mm",
           stroke_width=8, stroke_fill=(190, 120, 10))
    d.text((W / 2, 1400), "下期，我们让它追着光跑", font=font(42, True), fill=INK, anchor="mm")
    save(img, "v18_cta")


CARD_FUNCS = [c_cover, c_parts_photo, c_parts_ai, c_step_motor, c_step_wire, c_sensor,
              c_wire_real, c_code_intro, c_robot, c_test_start, c_tune, c_upgrade,
              c_summary, c_cta]


def build_cards():
    """Return {segment_name: PIL.Image} for every static segment."""
    _CARDS.clear()
    for fn in CARD_FUNCS:
        fn()
    return dict(_CARDS)


if __name__ == "__main__":
    for name, im in build_cards().items():
        print("  card", name)
