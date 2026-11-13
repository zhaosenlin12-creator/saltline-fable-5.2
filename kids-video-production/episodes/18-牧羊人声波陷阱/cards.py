# -*- coding: utf-8 -*-
"""cards.py - the static cards for the 回响·回声探测器 film.

Cream paper ground, one idea per card, real photos as evidence and crayon
illustrations as process, content stops above BOT (1520) so the burned-in
captions never collide.

The spine of this film is a six-part team:
    Arduino 主板   = 大脑   (deciding when the device has heard something)
    声音传感器     = 小耳朵 (the ears that listen)
    小舵机         = 小脖子 (the neck that turns the radar head)
    按键           = 小手指 (the X key the player holds down)
    LED 灯环       = 小灯笼 (lighting up = 被标记)
    小喇叭         = 小嘴巴 (the 发现声音 alert)
and a second LED that stands in for the squad-shared marker.
"""
import os

from PIL import Image, ImageDraw

from design import *
from project import AI_FILE, AI, REAL

BOT = 1520          # content must stop here - captions live below

C_EYE = (30, 168, 190)      # 超声波传感器 小眼睛
C_MOUTH = (245, 166, 35)    # 小喇叭 小嘴巴
C_BOARD = (54, 162, 105)    # Arduino 大脑
C_KEY = (228, 87, 46)       # 按键 小手指
C_LAMP = (255, 148, 58)     # LED 灯环 小灯笼
C_KRAFT = (193, 142, 92)    # 纸板
C_CAMO = (58, 62, 72)       # 黑金卡纸
C_ALERT = (228, 87, 46)     # 啪 的一声


def top_chip(img, text, color=ORANGE, fg=INK, x=MARGIN, y=76, size=38):
    return chip(img, x, y, text, bg=color, fg=fg, size=size, padx=30, pady=16)


def badge_step(img, x, y, num, label, color=BLUE):
    d = ImageDraw.Draw(img)
    r = 40
    d.ellipse([x, y, x + r * 2, y + r * 2], fill=color, outline=WHITE, width=5)
    d.text((x + r, y + r), str(num), font=font(52, True), fill=WHITE, anchor="mm")
    f = font(44, True)
    tw = text_w(d, label, f)
    rounded(img, [x + r * 2 + 16, y + 8, x + r * 2 + 16 + tw + 40, y + r * 2 - 8],
            (r * 2 - 16) // 2, fill=WHITE, outline=color, width=4)
    d.text((x + r * 2 + 36, y + r), label, font=f, fill=color, anchor="lm")


def paper_card(img, box, radius=28, alpha=250):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle(box, radius=radius, fill=(255, 253, 246, alpha),
                                          outline=(228, 216, 192, 255), width=3)
    shadowed(img, box, radius, blur=26, alpha=44, offset=(0, 10))
    img.alpha_composite(lay)


def banner(img, box, text, sub=None, accent=ORANGE, size=44):
    paper_card(img, box, radius=26)
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0 + 26, y0 + 24, x0 + 36, y1 - 24], 5, fill=accent)
    cy = y0 + (y1 - y0) / 2 - (14 if sub else 0)
    d.text((x0 + 58, cy), text, font=font(size, True), fill=INK, anchor="lm")
    if sub:
        d.text((x0 + 58, cy + 46), sub, font=font(30, False), fill=INK_SOFT, anchor="lm")


def illus(img, path, box, feather=34, radius=30, frame=True):
    """Drop a whole illustration into the box as a framed picture."""
    x0, y0, x1, y1 = [int(v) for v in box]
    im = Image.open(path).convert("RGB")
    sw, sh = im.size
    tw, th = x1 - x0, y1 - y0
    scale = min(tw / float(sw), th / float(sh))
    nw, nh = max(1, int(sw * scale + 0.5)), max(1, int(sh * scale + 0.5))
    im = im.resize((nw, nh), Image.LANCZOS)
    mask = Image.new("L", (nw, nh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, nw - 1, nh - 1], radius=radius, fill=255)
    px = x0 + (tw - nw) // 2
    py = y0 + (th - nh) // 2
    shadowed(img, [px, py, px + nw, py + nh], radius, blur=22, alpha=46, offset=(0, 12))
    img.paste(im, (px, py), mask)
    if frame:
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([px, py, px + nw - 1, py + nh - 1], radius=radius,
                            outline=(228, 216, 192), width=3)
    return img


def fade_top(img, height=200, power=2.0):
    """Soft dark gradient at the top so a chip stays readable over a photo."""
    grad = Image.new("L", (1, height), 0)
    gd = ImageDraw.Draw(grad)
    for i in range(height):
        gd.point((0, i), fill=int(96 * (1 - i / float(height)) ** power))
    grad = grad.resize((img.size[0], height))
    lay = Image.new("RGBA", (img.size[0], height), (0, 0, 0, 0))
    lay.putalpha(grad)
    img.alpha_composite(lay, (0, 0))


def fade_bottom(img, top, height=240):
    """Fade the photo into the cream paper, so the cut is not a hard grey edge."""
    grad = Image.new("L", (1, height), 255)
    gd = ImageDraw.Draw(grad)
    for i in range(height):
        gd.point((0, i), fill=int(255 - 255 * (i / float(height)) ** 1.4))
    grad = grad.resize((img.size[0], height))
    lay = Image.new("RGBA", (img.size[0], height), (0, 0, 0, 0))
    lay.putalpha(grad)
    img.alpha_composite(lay, (0, top))


def speech_bubble(img, box, big, small=None, color=(245, 166, 35), tail=(160, 210, 120),
                  up=False):
    """A comic speech bubble with a tail (down-left by default, up-left if up)."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    shadowed(img, box, 40, blur=26, alpha=40, offset=(0, 10))
    d.rounded_rectangle([x0, y0, x1, y1], 40, fill=WHITE, outline=(228, 216, 192), width=4)
    tx, ty, tipx, tipy = tail
    dy = -6 if up else 6
    d.polygon([(tx, ty), (tipx, tipy), (tx + 72, ty + dy)], fill=WHITE)
    d.polygon([(tx, ty), (tipx, tipy), (tx + 72, ty + dy)], outline=(228, 216, 192), width=4)
    cy = (y0 + y1) / 2 - (20 if small else 0)
    d.text(((x0 + x1) / 2, cy), big, font=font(60, True), fill=color, anchor="mm")
    if small:
        d.text(((x0 + x1) / 2, cy + 52), small, font=font(30, True), fill=INK, anchor="mm")


_CARDS = {}


def save(img, name):
    """Collect a finished card; the pipeline writes it to build/cards/."""
    _CARDS[name] = img


def photo_note(img, path, head, line2, line3, focus=(0.5, 0.5), accent=BLUE):
    """Cream strip with one real photo and three lines of caption."""
    d = ImageDraw.Draw(img)
    paper_card(img, [MARGIN, 1290, W - MARGIN, BOT], radius=26)
    paste_cover(img, os.path.join(REAL, path),
                (MARGIN + 24, 1310, MARGIN + 224, 1500), radius=18, focus=focus)
    d.text((MARGIN + 254, 1340), head, font=font(35, True), fill=INK, anchor="lm")
    d.text((MARGIN + 254, 1400), line2, font=font(25, False), fill=INK_SOFT, anchor="lm")
    d.text((MARGIN + 254, 1444), line3, font=font(24, False), fill=accent, anchor="lm")


def role_rows(img, box, rows, title=None, accent=C_BOARD, fs=28, ns=27):
    """A list of 'part = nickname' lines with a coloured dot on the left."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    paper_card(img, box, radius=26)
    if title:
        d.text((x0 + 40, y0 + 44), title, font=font(30, True), fill=INK_SOFT, anchor="lm")
        y = y0 + 92
    else:
        y = y0 + 40
    step = (y1 - y - 30) / len(rows)
    for col, a, b in rows:
        d.ellipse([x0 + 40, y + 4, x0 + 82, y + 46], fill=col)
        d.text((x0 + 61, y + 25), a[0], font=font(26, True), fill=WHITE, anchor="mm")
        d.text((x0 + 104, y + 25), a, font=font(fs, True), fill=INK, anchor="lm")
        tw = text_w(d, b, font(ns, True))
        d.text((x1 - 40 - tw, y + 25), b, font=font(ns, True), fill=col, anchor="lm")
        y += step


def step_text_card(img, box, title, lines, accent=C_BOARD, ts=36, ls=27):
    """Right-hand column of a step card: a headline plus short lines."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    paper_card(img, box, radius=28)
    d.rounded_rectangle([x0 + 26, y0 + 30, x0 + 36, y1 - 30], 5, fill=accent)
    d.text((x0 + 60, y0 + 62), title, font=font(ts, True), fill=INK, anchor="lm")
    d.line([(x0 + 60, y0 + 112), (x1 - 40, y0 + 112)], fill=(228, 216, 192), width=3)
    y = y0 + 170
    for ln in lines:
        d.ellipse([x0 + 62, y - 8, x0 + 78, y + 8], fill=accent)
        d.text((x0 + 98, y), ln, font=font(ls, False), fill=INK_SOFT, anchor="lm")
        y += 62


def part_grid_n(img, box, items, cols=3, rows=3):
    """A dense grid of numbered parts, used for the nine-piece kit list."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    cw = (x1 - x0) / cols
    ch = (y1 - y0) / rows
    for i, (col, name, note) in enumerate(items):
        cx = x0 + (i % cols) * cw
        cy = y0 + (i // cols) * ch
        box2 = [cx + 8, cy + 8, cx + cw - 8, cy + ch - 12]
        paper_card(img, box2, radius=22)
        r = 27
        d.ellipse([box2[0] + 18, box2[1] + 18, box2[0] + 18 + r * 2, box2[1] + 18 + r * 2],
                  fill=col)
        d.text((box2[0] + 18 + r, box2[1] + 18 + r), str(i + 1), font=font(28, True),
               fill=WHITE, anchor="mm")
        d.text((box2[0] + 18 + r * 2 + 14, box2[1] + 30), name, font=font(26, True),
               fill=INK, anchor="lm")
        d.text((box2[0] + 18 + r * 2 + 14, box2[1] + 68), note, font=font(19, False),
               fill=INK_SOFT, anchor="lm")


def rule_rows(img, box, rows, title=None):
    """Safety rules: a warning triangle for the first ones, a tick for the good one."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    if title:
        d.text((x0, y0 - 44), title, font=font(34, True), fill=INK, anchor="lm")
    step = (y1 - y0) / len(rows)
    for i, (kind, head, sub) in enumerate(rows):
        y = y0 + i * step
        paper_card(img, [x0, y + 6, x1, y + step - 12], radius=22)
        cx, cy = x0 + 58, y + 6 + (step - 18) / 2
        if kind == "ok":
            check_icon(d, cx, cy, 30, color=GREEN, width=6)
            col = GREEN
        else:
            warn_icon(d, cx, cy, 30, color=RED, width=6)
            col = RED
        d.text((x0 + 104, cy - 18), head, font=font(30, True), fill=INK, anchor="lm")
        d.text((x0 + 104, cy + 20), sub, font=font(23, False), fill=INK_SOFT, anchor="lm")



# ------------------------------------------------------------------ cards
def c_cover():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "三角洲行动 · 干员「牧羊人」V 技能", C_CAMO, WHITE, size=34)
    d.text((MARGIN, 170), "声波陷阱", font=font(92, True), fill=INK, anchor="lm")
    d.text((MARGIN + 6, 264), "现实版声波小圆饼", font=font(42, True), fill=C_MOUTH, anchor="lm")
    paper_card(img, [MARGIN, 330, W - MARGIN, 1140], radius=30)
    paste_cover(img, os.path.join(REAL, "ref_trap_model.jpg"),
                (MARGIN + 18, 348, W - MARGIN - 18, 1122), radius=24, focus=(0.5, 0.44))
    banner(img, (MARGIN, 1180, W - MARGIN, BOT), "今天咱们做一台真的能用的！",
           sub="纸板 + Arduino + 小眼睛", accent=C_ALERT, size=40)
    save(img, "v01_cover")


def c_rules():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "先看看游戏里怎么玩", BLUE, WHITE)
    paste_cover(img, os.path.join(REAL, "ref_trap_guide.jpg"),
                (MARGIN, 170, 470, 700), radius=22, focus=(0.5, 0.35))
    paste_cover(img, os.path.join(REAL, "ref_trap_model.jpg"),
                (500, 170, W - MARGIN, 700), radius=22, focus=(0.5, 0.44))
    d.text((MARGIN + 10, 736), "游戏里的声波陷阱", font=font(29, True), fill=INK, anchor="lm")
    d.text((510, 736), "它的真身长这样", font=font(29, True), fill=C_CAMO, anchor="lm")
    rule_rows(img, (MARGIN, 790, W - MARGIN, 1250), [
        ("warn", "身上最多同时带 2 个", "用完要等 40 秒才冷却"),
        ("warn", "最远能扔 15 米", "敌人踩进 4 米就自动触发"),
        ("warn", "啪一声炸开 7 米大圈", "滴滴声 7 米外就听不见了"),
        ("ok", "按 H 可以手动引爆", "手动引爆的范围还更大"),
    ])
    banner(img, (MARGIN, 1280, W - MARGIN, BOT), "咱们不用真炸药，用小喇叭就行",
           accent=C_EYE, size=36)
    save(img, "v02_rules")


def c_parts_ai():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "零件清单", GREEN, WHITE)
    illus(img, os.path.join(AI, AI_FILE["v03_parts_ai"]), (MARGIN + 150, 140, W - MARGIN - 150, 780))
    part_grid_n(img, (MARGIN, 800, W - MARGIN, 1198), [
        (C_BOARD, "Arduino", "大脑"),
        (C_EYE, "超声波", "小眼睛"),
        (C_MOUTH, "小喇叭", "小嘴巴"),
        (C_LAMP, "LED灯环", "小灯笼"),
        (C_KEY, "按键", "小手指"),
        (C_CAMO, "小磁铁", "回收钩"),
        (C_KRAFT, "纸板圆底座", "小脚丫"),
        (C_KRAFT, "CD盘", "计时盘"),
        (C_ALERT, "彩纸小脚", "会斜贴"),
    ])
    paper_card(img, [MARGIN, 1226, W - MARGIN, BOT], radius=26)
    paste_cover(img, os.path.join(REAL, "px_35673081.jpg"),
                (MARGIN + 24, 1246, MARGIN + 224, 1500), radius=18, focus=(0.5, 0.5))
    d.text((MARGIN + 254, 1290), "零件都能买到", font=font(33, True), fill=INK, anchor="lm")
    d.text((MARGIN + 254, 1348), "主板、小喇叭、灯环、按键，", font=font(25, False),
           fill=INK_SOFT, anchor="lm")
    d.text((MARGIN + 254, 1392), "文具店和网上都有。", font=font(25, False),
           fill=INK_SOFT, anchor="lm")
    d.text((MARGIN + 254, 1444), "剩下的自己动手做就好！", font=font(25, True),
           fill=C_BOARD, anchor="lm")
    save(img, "v03_parts_ai")


def c_step_base():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "第一步 · 做底座", ORANGE)
    illus(img, os.path.join(AI, AI_FILE["v04_step_base"]), (MARGIN + 120, 150, W - MARGIN - 120, 760))
    step_text_card(img, (MARGIN, 790, W - MARGIN, 1180), "剪一个圆饼，三条小脚", [
        "硬卡纸剪一个圆圆的大饼",
        "再剪三条纸，折成小脚丫",
        "三条腿粘在圆饼底下撑稳它",
        "斜着靠墙也不倒，贴地上更稳",
    ], accent=C_KRAFT)
    photo_note(img, "px_35673073.jpg", "真的在剪卡纸",
               "圆卡纸剪成小圆饼", "三条纸折成小脚丫", accent=C_KRAFT)
    save(img, "v04_step_base")


def c_step_mouth():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "第二步 · 小嘴巴 + 小灯笼", C_MOUTH, INK, size=34)
    illus(img, os.path.join(AI, AI_FILE["v05_step_mouth"]), (MARGIN + 120, 150, W - MARGIN - 120, 760))
    step_text_card(img, (MARGIN, 790, W - MARGIN, 1180), "喇叭藏肚子，灯环缠边上", [
        "把小喇叭塞进圆饼的肚子里",
        "LED 灯环一圈一圈缠在边沿",
        "灯环会一闪一闪，像小灯笼",
        "喇叭小声地滴滴响，提醒你它活着",
    ], accent=C_MOUTH)
    photo_note(img, "px_35673112.jpg", "真的接上喇叭",
               "小喇叭放进圆饼肚子里", "灯环缠在边上一圈", accent=C_MOUTH)
    save(img, "v05_step_mouth")


def c_step_eye():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "第三步 · 小眼睛 + 小手指", C_EYE, WHITE, size=34)
    illus(img, os.path.join(AI, AI_FILE["v06_step_eye"]), (MARGIN + 120, 150, W - MARGIN - 120, 760))
    step_text_card(img, (MARGIN, 790, W - MARGIN, 1180), "量距离，也能手动啪", [
        "超声波传感器装在前边当小眼睛",
        "它发出声波，听回波，算出距离",
        "旁边贴一个红色按键当小手指",
        "按一下，不用等人靠近就提前啪",
    ], accent=C_EYE)
    photo_note(img, "px_12741836.jpg", "真的小眼睛",
               "两只小眼睛量得准准的", "按键就是小手指", accent=C_EYE)
    save(img, "v06_step_eye")


def c_step_timer():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "第四步 · 冷却盘 + 回收钩", C_KEY, WHITE, size=34)
    illus(img, os.path.join(AI, AI_FILE["v07_step_timer"]), (MARGIN + 120, 150, W - MARGIN - 120, 760))
    step_text_card(img, (MARGIN, 790, W - MARGIN, 1180), "转一圈，等它冷却", [
        "剪一张 CD 盘贴在侧面当计时盘",
        "用完以后它会慢慢转 40 秒",
        "转完一圈，才可以再放一个",
        "底下粘一块小磁铁，能钓回来回收",
    ], accent=C_KEY)
    photo_note(img, "px_28169155.jpg", "真的电子零件",
               "CD 盘当冷却计时盘", "磁铁能钓回来接着玩", accent=C_KEY)
    save(img, "v07_step_timer")


def c_safety():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "安全第一", RED, WHITE)
    illus(img, os.path.join(AI, AI_FILE["v08_safety_real"]), (MARGIN + 240, 140, W - MARGIN - 240, 700))
    rule_rows(img, (MARGIN, 760, W - MARGIN, 1300), [
        ("warn", "不装爆炸物，没有真实冲击", "它只是纸板玩具加一个小喇叭"),
        ("warn", "音量调到最小，不能贴耳朵", "更不能对着别人耳朵大喊"),
        ("warn", "别放楼梯口、马路边", "也别放在会吓到宠物的地方"),
        ("warn", "旁边有人，先喊一声", "接线之前一定要先断电"),
        ("ok", "音量小、离得远，就很安全", "和小伙伴一起玩更棒"),
    ])
    banner(img, (MARGIN, 1320, W - MARGIN, BOT), "音量调到最小的那一格",
           sub="它响的是小纸片，可不是炸弹哦", accent=GREEN, size=34)
    save(img, "v08_safety_real")


def c_trap_speak():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "装置自己说话", C_CAMO, WHITE)
    illus(img, os.path.join(AI, AI_FILE["v12_trap_speak"]), (MARGIN + 130, 140, W - MARGIN - 130, 820))
    speech_bubble(img, (MARGIN + 40, 840, W - MARGIN - 40, 1030),
                  "声波陷阱就位！", "四米内有人——啪！",
                  color=RED, tail=(MARGIN + 120, 1030, MARGIN + 60, 1100))
    paper_card(img, [MARGIN, 1110, W - MARGIN, BOT], radius=26)
    paste_cover(img, os.path.join(REAL, "ref_trap_model.jpg"),
                (MARGIN + 22, 1130, MARGIN + 282, 1500), radius=16, focus=(0.5, 0.44))
    d.text((MARGIN + 312, 1188), "游戏里就是这个画面", font=font(34, True), fill=INK, anchor="lm")
    d.text((MARGIN + 312, 1244), "小圆饼一直滴滴响，", font=font(25, False),
           fill=INK_SOFT, anchor="lm")
    d.text((MARGIN + 312, 1288), "敌人踩进来就啪一声。", font=font(25, False),
           fill=INK_SOFT, anchor="lm")
    d.text((MARGIN + 312, 1344), "咱们照着它做一台！", font=font(26, True),
           fill=C_MOUTH, anchor="lm")
    save(img, "v12_trap_speak")


def c_test_start():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    paste_cover(img, os.path.join(REAL, "px_sunny_room.jpg"), (0, 0, W, 600), focus=(0.5, 0.5))
    fade_top(img, 200)
    fade_bottom(img, 600, 220)
    top_chip(img, "落地实测 · 准备", GREEN, WHITE)
    illus(img, os.path.join(AI, AI_FILE["v13_test_start"]), (MARGIN + 170, 630, W - MARGIN - 170, 1280))
    banner(img, (MARGIN, 1300, W - MARGIN, BOT), "摆在空旷的地板上",
           sub="量好四米，两个小纸人当目标", accent=RED, size=36)
    save(img, "v13_test_start")


def c_upgrade():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    top_chip(img, "升级：更厉害的声波陷阱", GREEN, WHITE, size=34)
    illus(img, os.path.join(AI, AI_FILE["v17_upgrade"]), (MARGIN + 180, 160, W - MARGIN - 180, 880))
    y = 910
    ups = [(C_BOARD, "无线小发射器", "队友手机也能看"),
           (C_LAMP, "发光转盘", "一眼知道等多久"),
           (C_CAMO, "加一块电池", "搬到哪都能用")]
    for i, (col, big, small) in enumerate(ups):
        x = MARGIN + i * ((W - 2 * MARGIN) / 3)
        cw = (W - 2 * MARGIN) / 3 - 16
        cxx = x + cw / 2
        paper_card(img, [x, y, x + cw, y + 210], radius=26)
        d.ellipse([cxx - 37, y + 32, cxx + 37, y + 106], fill=col)
        d.text((cxx, y + 69), big[0], font=font(40, True), fill=WHITE, anchor="mm")
        d.text((cxx, y + 150), big, font=font(25, True), fill=INK, anchor="mm")
        d.text((cxx, y + 188), small, font=font(21, False), fill=INK_SOFT, anchor="mm")
    paste_cover(img, os.path.join(REAL, "px_28169155.jpg"),
                (MARGIN, 1150, MARGIN + 300, 1490), radius=20, focus=(0.5, 0.4))
    d.text((MARGIN + 330, 1196), "里面全是真零件", font=font(33, True), fill=INK, anchor="lm")
    d.text((MARGIN + 330, 1250), "升级件接上去，", font=font(28, False),
           fill=INK_SOFT, anchor="lm")
    d.text((MARGIN + 330, 1296), "冷却看得见，队友也看得见。", font=font(28, False),
           fill=INK_SOFT, anchor="lm")
    d.text((MARGIN + 330, 1350), "动手改一改，超有成就感！", font=font(28, True),
           fill=C_BOARD, anchor="lm")
    save(img, "v17_upgrade")


def c_cta():
    img = paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    illus(img, os.path.join(AI, AI_FILE["v18_cta"]), (150, 140, W - 150, 720), feather=30)
    sparkle_field(d, seed=11, n=22, box=(80, 130, W - 80, 720))
    role_rows(img, (MARGIN, 740, W - MARGIN, 1140), [
        (C_EYE, "超声波传感器", "小眼睛"),
        (C_MOUTH, "小喇叭", "小嘴巴"),
        (C_LAMP, "LED 灯环", "小灯笼"),
        (C_KEY, "按键", "小手指"),
    ])
    d.text((W / 2, 1240), "点赞  收藏", font=font(68, True), fill=ORANGE, anchor="mm",
           stroke_width=8, stroke_fill=(190, 120, 10))
    paper_card(img, [MARGIN, 1290, W - MARGIN, BOT], radius=24)
    paste_cover(img, os.path.join(REAL, "px_32998845.jpg"),
                (MARGIN + 20, 1310, MARGIN + 190, 1500), radius=14, focus=(0.5, 0.45))
    d.text((MARGIN + 216, 1342), "下期：会播报天气的太阳能小气象台", font=font(30, True),
           fill=INK, anchor="lm")
    d.text((MARGIN + 216, 1400), "和爸爸妈妈一起做，", font=font(26, False),
           fill=INK_SOFT, anchor="lm")
    d.text((MARGIN + 216, 1444), "动手做的东西最棒啦！", font=font(26, False),
           fill=INK_SOFT, anchor="lm")
    save(img, "v18_cta")


CARD_FUNCS = [c_cover, c_rules, c_parts_ai, c_step_base, c_step_mouth,
              c_step_eye, c_step_timer, c_safety, c_trap_speak,
              c_test_start, c_upgrade, c_cta]


def build_cards():
    """Return {segment_name: PIL.Image} for every static segment."""
    _CARDS.clear()
    for fn in CARD_FUNCS:
        fn()
    return dict(_CARDS)


if __name__ == "__main__":
    for name, im in build_cards().items():
        print("  card", name)
