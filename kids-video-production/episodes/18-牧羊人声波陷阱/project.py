# -*- coding: utf-8 -*-
"""project.py - the single source of truth for one video.

Topic: 三角洲行动 干员「牧羊人」的 V 技能「声波陷阱」.

The film builds a SAFE cardboard-and-paper desktop prop: a round black-gold
"sound pancake" that sticks to the floor (or a wall) on three little card
legs, with a tiny speaker in its belly, an LED ring around the rim, an
ultrasonic "eye" that measures how far a paper robot is, a push button for
manual trigger and a magnet underneath for fishing it back in.

NOTHING here is a real military sound-charge.  There is no explosive, no
shock mechanism and no way to hurt anybody: the loudest thing in the build
is a 3mm paper speaker at minimum volume.  The game's "40 damage" becomes
"the paper robot freezes for 2 seconds and walks slowly", the tinnitus
becomes "it covers its ears", the screen warp becomes "the picture shakes",
and the interrupted actions become "the card it was holding falls down".
"""
import json
import os

# ---------------------------------------------------------------- output
OUTPUT_NAME = "声波陷阱_制作到实测.mp4"
W, H, FPS = 1080, 1920, 30
LEAD_IN = 0.35
TAIL_PAD = 0.9

# ---------------------------------------------------------------- voices
VOICES = {
    # "male" is used for the device's own shout so the caption pass paints it red
    "narr":  "Chinese (Mandarin)_Warm_Bestie",
    "male":  "male-qn-jingying",
}
VOICE_PITCH = {"narr": "+0%", "male": "+12%"}
VOICE_BREATH = {"narr": 170, "male": 200}
VOICE_RATE_BIAS = 2

# ---------------------------------------------------------------- script
#   (id, section, voice_key, speed, gap_after_seconds, text)
# 【...】 marks a keyword: it gets highlighted in the captions.
SCRIPT = [
    ("L01", "hook",    "narr", 1.03, 0.32,
     "《三角洲行动》里的牧羊人，最硬核的绝招是【声波陷阱】！往地上一放就滴滴响，谁踩进四米里——啪！当场就震愣住！"),
    ("L02", "parts",   "narr", 1.00, 0.26,
     "先看游戏里的规矩：最多同时带【2 个】，最远扔【15 米】；敌人踩进【4 米】就自动触发，炸开【7 米】那么大的圈；用完等【40 秒】冷却。"),
    ("L03", "parts",   "narr", 1.00, 0.40,
     "零件清单：【Arduino 主板】、【超声波传感器】、【小喇叭】、【LED 灯环】、【按键】、【小磁铁】、【纸板圆底座】。昵称来啦：主板是【大脑】，超声波是【小眼睛】，小喇叭是【小嘴巴】，按键是【小手指】。"),
    ("L04", "build",   "narr", 1.00, 0.26,
     "第一步做底座：硬卡纸剪成圆饼，再剪三条纸折出【小脚丫】撑稳它，斜着靠墙也不倒。游戏里它能贴地、贴墙、贴路灯，就是不能贴天花板。"),
    ("L05", "build",   "narr", 1.00, 0.26,
     "第二步做小嘴巴和小灯笼：把【小喇叭】塞进圆饼肚子里，【LED 灯环】缠在边上一圈。放好后它一直滴滴响，提醒你它还在工作。"),
    ("L06", "build",   "narr", 1.00, 0.26,
     "第三步装小眼睛和小手指：【超声波传感器】像一双眼睛，量得出前面的人有几米远；【按键】是手动引爆的小手指，按一下提前啪！"),
    ("L07", "build",   "narr", 1.00, 0.26,
     "第四步做冷却盘和回收钩：剪一张【CD 盘】贴在侧面当【计时盘】，转一圈就是【40 秒】冷却；底下粘块【小磁铁】，用完钓回来接着玩。"),
    ("L08", "safety",  "narr", 1.00, 0.40,
     "安全提醒：这是纸板玩具，不装爆炸物、没有真实冲击；喇叭音量调到最小，不能贴耳朵；旁边有人先喊一声；别放楼梯口马路边，也别吓到宠物；接线前先断电。"),
    ("L09", "code",    "narr", 1.00, 0.26,
     "开始写程序。第一段【读距离】：超声波每秒发十次声波，把回波时间换算成距离，小眼睛一直眨，看谁在靠近。"),
    ("L10", "code",    "narr", 1.00, 0.26,
     "第二段【判断四米】：距离小于【4 米】就触发，一秒只响一次。游戏里还提醒你，滴滴声在【7 米】外听不见，别放太近把自己暴露啦。"),
    ("L11", "code",    "narr", 1.00, 0.26,
     "第三段【产生效果】：啪的一声，纸机器人【愣住 2 秒】、走路变慢，这就是【减速】；捂耳朵嗡嗡响，叫【耳鸣】；画面抖一下，叫【屏幕扭曲】；手里的动作也被【打断】了。"),
    ("L12", "test",    "male", 1.03, 0.40,
     "【声波陷阱就位】！四米内有人——啪！"),
    ("L13", "test",    "narr", 1.00, 0.26,
     "开始【落地实测】！装置摆在空旷地板上，量好四米，再做两个纸机器人：一个会走，一个站得笔直。"),
    ("L14", "test",    "narr", 1.00, 0.28,
     "先测小声的：放好以后小圆饼开始【滴滴】响，我们一起退到【7 米】外——你猜，还听得见吗？"),
    ("L15", "test",    "narr", 1.00, 0.28,
     "会走的纸机器人一步步靠近，进了【4 米】——啪！它当场【愣住 2 秒】，捂住耳朵，画面抖了抖，手里的卡片掉了！"),
    ("L16", "test",    "narr", 1.00, 0.30,
     "再来手动引爆：按一下【H】键，啪的一声炸开【7 米】的大圈，圈里的纸机器人全被震愣住，圈外安然无恙！"),
    ("L17", "upgrade", "narr", 1.00, 0.28,
     "还能更厉害：加个【无线小发射器】，队友手机也能看到；冷却盘换成【发光转盘】，一眼知道还要等多久；再装块电池，搬到哪都能用。"),
    ("L18", "outro",   "narr", 1.00, 0.20,
     "今天你学会了：超声波是【小眼睛】，小喇叭是【小嘴巴】，按键是【小手指】！点赞收藏，下期做个会播报天气的太阳能小气象台。"),
]

# ---------------------------------------------------------------- segments
SEG_NAMES = [
    "v01_cover", "v02_rules", "v03_parts_ai", "v04_step_base",
    "v05_step_mouth", "v06_step_eye", "v07_step_timer", "v08_safety_real",
    "v09_code_read", "v10_code_judge", "v11_code_effect", "v12_trap_speak",
    "v13_test_start", "v14_test_beep", "v15_test_trigger", "v16_test_manual",
    "v17_upgrade", "v18_cta",
]

ANIM_SEGS = {"v09_code_read", "v10_code_judge", "v11_code_effect",
             "v14_test_beep", "v15_test_trigger", "v16_test_manual"}

AI_FILE = {
    "v03_parts_ai":    "02_parts.png",
    "v04_step_base":   "03_make_base.png",
    "v05_step_mouth":  "04_make_mouth.png",
    "v06_step_eye":    "05_make_eye.png",
    "v07_step_timer":  "06_make_timer.png",
    "v08_safety_real": "11_safety.png",
    "v12_trap_speak":  "07_scan.png",
    "v13_test_start":  "08_test.png",
    "v17_upgrade":     "09_upgrade.png",
    "v18_cta":         "10_cta.png",
}

REAL_FILE = {
    "v01_cover":       "ref_trap_model.jpg",
    "v02_rules":       "ref_trap_guide.jpg",
    "v04_step_base":   "px_35673073.jpg",
    "v05_step_mouth":  "px_35673112.jpg",
    "v06_step_eye":    "px_12741836.jpg",
    "v07_step_timer":  "px_28169155.jpg",
    "v12_trap_speak":  "ref_trap_model.jpg",
    "v13_test_start":  "px_sunny_room.jpg",
    "v17_upgrade":     "px_28169155.jpg",
    "v18_cta":         "px_32998845.jpg",
}

# ---------------------------------------------------------------- illustrations
IMAGE_STYLE = ("cute 3d cartoon for children, soft rounded shapes, bright cheerful "
               "colours, clean simple background, friendly faces, handmade cardboard "
               "and paper craft toy styling, black and gold round disc gadget with "
               "orange glowing centre and orange accent stripes")

SHOTS = [
    ("01_cover", "cute 3d cartoon boy proudly holding up a handmade cardboard round flat disc gadget with three small card legs and a glowing orange speaker mouth in the middle, black and gold paper, big happy smile, clean shiny floor"),
    ("02_parts", "cute 3d cartoon boy laying out parts on a craft mat: a blue microcontroller board, a tiny blue ultrasonic sensor with two round eyes, a tiny black speaker, an orange LED light ring, a red push button, a small magnet, a round cardboard disc base and folded paper legs, each item with a cute smiling face"),
    ("03_make_base", "cute 3d cartoon boy cutting a big circle from brown cardboard with scissors and gluing three folded paper strips as little legs under the round disc base, craft table with glue stick, happy"),
    ("04_make_mouth", "cute 3d cartoon boy gluing a tiny black speaker into the middle of the round cardboard disc and wrapping a glowing orange LED light ring around its rim, excited"),
    ("05_make_eye", "cute 3d cartoon boy clipping a small blue ultrasonic sensor with two round eyes on the front edge of the round cardboard disc and pressing a red push button beside it, focused expression"),
    ("06_make_timer", "cute 3d cartoon boy gluing a shiny CD disc on the side of the round cardboard gadget as a round timer dial and sticking a small magnet under the bottom, craft table with tools"),
    ("07_scan", "cute 3d cartoon boy standing beside the finished black and gold round cardboard gadget on the floor, a big orange expanding sound wave ring rolling out of it, a cute paper robot target far away, sunny room"),
    ("08_test", "cute 3d cartoon boy kneeling on a clean empty floor placing the round cardboard gadget, a measuring tape on the floor, two cute paper robot targets standing a few steps away, sunny room"),
    ("09_upgrade", "cute 3d cartoon boy holding a tiny wireless module and a glowing timer dial next to the finished round cardboard gadget with orange lights, happy excited face, craft table with tools"),
    ("10_cta", "cute 3d cartoon boy hugging the finished round cardboard gadget with its glowing orange centre, sparkles and confetti around him, clean shiny floor, big happy smile"),
    ("11_safety", "cute 3d cartoon boy carefully holding the round cardboard gadget with a tiny speaker, a friendly adult waving in the background, a small orange volume knob turned all the way down, safety reminder mood"),
]

# ---------------------------------------------------------------- music
BPM = 122.0
CHORDS = [                                   # I - V - vi - IV in C major
    (48, [60, 64, 67]),
    (43, [59, 62, 67]),
    (45, [57, 60, 64]),
    (41, [57, 60, 65]),
]
MELODY = [                                   # (bar offset in beats, midi, length in beats)
    (0, 76, 1.0), (1, 79, 1.0), (2, 84, 1.5), (4, 79, 1.0),
    (6, 76, 1.0), (8, 72, 1.5), (10, 74, 1.0), (12, 76, 1.0),
    (16, 79, 1.0), (18, 83, 1.0), (20, 79, 1.5), (22, 74, 1.0),
    (24, 76, 1.0), (26, 71, 1.0), (28, 72, 1.5), (30, 67, 1.5),
]

# ---------------------------------------------------------------- sound effects
# ding / whoosh / beep / chime are transition markers whose attack is placed in
# the silent gap before the line; "pop" is the soft cardboard 啪 of the device.
SFX_CUES = {
    "ding":   [("L02", -0.30, 0.30), ("L04", -0.38, 0.30),
               ("L07", -0.24, 0.30), ("L12", -0.22, 0.32),
               ("L16", -0.26, 0.30)],
    "whoosh": [("L06", -0.30, 0.22), ("L08", -0.22, 0.24),
               ("L14", -0.34, 0.22), ("L17", -0.26, 0.22)],
    "beep":   [("L09", 1.90, 0.30), ("L10", 6.40, 0.28),
               ("L14", 2.70, 0.30)],
    "chime":  [("L11", 8.60, 0.26), ("L15", 4.60, 0.30), ("L18", 9.60, 0.26)],
    "pop":    [("L01", 7.80, 0.34), ("L06", 11.83, 0.26),
               ("L11", 1.60, 0.30), ("L12", 2.25, 0.30),
               ("L15", 3.55, 0.40), ("L16", 2.60, 0.42)],
}

SFX_EXTRA = {"pop": "build/sfx/pop.wav"}

BGM_GAIN = 0.20
DUCK_DEPTH = 0.90

# ---------------------------------------------------------------- QA
QA_DURATION = (150.0, 208.0)
QA_MIN_CUTS = 16
QA_MIN_CAPTIONS = 44
QA_MIN_CHARS = 800
QA_RATE_RANGE = (4.0, 6.8)
QA_MIN_SEPARATION_DB = 6.0
QA_MIN_AI = 10
QA_MIN_REAL = 18
QA_KEYWORDS = ["声波陷阱", "牧羊人", "4 米", "7 米", "15 米", "40 秒", "2 秒",
               "2 个", "H", "滴滴", "啪", "耳鸣", "减速", "屏幕扭曲", "打断",
               "回收", "冷却", "落地实测", "点赞", "安全", "超声波", "Arduino",
               "LED 灯环", "小喇叭", "按键", "小磁铁", "纸板圆底座", "大脑",
               "小眼睛", "小嘴巴", "小手指", "小灯笼", "计时盘", "无线小发射器"]

# ---------------------------------------------------------------- runtime
ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
AI = os.path.join(ROOT, "assets", "ai")
REAL = os.path.join(ROOT, "assets", "real")


def build_plan():
    """One visual segment per narration line; boundaries come from the timeline."""
    with open(os.path.join(BUILD, "timeline.json"), encoding="utf-8") as f:
        tl = json.load(f)
    lines, total = tl["lines"], tl["total"]
    plan = []
    for i, name in enumerate(SEG_NAMES):
        start = lines[i]["start"]
        end = lines[i + 1]["start"] if i + 1 < len(lines) else total
        plan.append({"name": name, "start": round(start, 3),
                     "dur": round(end - start, 3),
                     "kind": "anim" if name in ANIM_SEGS else "static",
                     "line": lines[i]["id"]})
    return plan, total


def segment_durations():
    """name -> duration, so animations can be cut to exactly match the voice."""
    plan, _ = build_plan()
    return {s["name"]: s["dur"] for s in plan}
