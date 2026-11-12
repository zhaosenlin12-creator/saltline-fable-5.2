# -*- coding: utf-8 -*-
"""project.py - the single source of truth for one video.

Topic: 三角洲行动 干员「回响」的 X 技能「回声探测器」.

The film builds a SAFE cardboard-and-paper desktop prop: a tripod sonar
detector made from a cardboard disc base, a rolled card-stock tube with a
paper fan dome, and a rotating paper cross-bar antenna driven by a hobby
servo.  A toy microphone module listens, a servo turns the "radar" head,
an LED ring and a tiny speaker report what was heard, and a second LED
stands in for the squad-shared marker.  Nothing transmits any real sound
power and no military hardware is involved - the only "detection" is a
harmless volume threshold that lights a lamp.
"""
import json
import os

# ---------------------------------------------------------------- output
OUTPUT_NAME = "回响声纳_制作到实测.mp4"
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
     "《三角洲行动》里的回响，是个特别会听声音的干员！她往地上一放【回声探测器】，前方七十米、一百二十度的动静全被她听见了，隔着墙也藏不住！"),
    ("L02", "parts",   "narr", 1.00, 0.26,
     "零件清单：【Arduino 主板】、【声音传感器】、【小舵机】、【LED 灯环】、【小喇叭】、【按键】、【纸板圆底座】、【彩纸伞罩】。"),
    ("L03", "parts",   "narr", 1.00, 0.40,
     "它们都有昵称：Arduino 是【大脑】；声音传感器是【小耳朵】；舵机是【小脖子】，负责转雷达盘；按键是【小手指】。"),
    ("L04", "build",   "narr", 1.00, 0.26,
     "第一步做底座：硬卡纸剪成三个圆片叠成圆盘，再剪三根纸条当【小脚丫】撑稳，贴上黑灰迷彩贴条，工业风就出来啦。"),
    ("L05", "build",   "narr", 1.00, 0.26,
     "第二步做声呐头：圆卡纸卷成一个筒，再剪八个扇形彩纸拼成一顶【小伞罩】罩在筒顶，这就是会转的天线阵。"),
    ("L06", "build",   "narr", 1.00, 0.26,
     "第三步装【小脖子】：小舵机卡在筒子下面，轴上插一根纸条当天线横杆。按一下，雷达盘就左右转，一圈一圈扫。"),
    ("L07", "build",   "narr", 1.00, 0.26,
     "第四步装小耳朵和小嘴巴：声音传感器装在罩子底下，LED 灯环缠在筒边，小喇叭藏在罩子里，按键贴在底座旁边。"),
    ("L08", "safety",  "narr", 1.00, 0.40,
     "安全提醒：这是纸板玩具，不装军用雷达、不发强声波；喇叭音量调到最小，不能对着耳朵狂吼；旁边有人先喊一声；接线前先断电。"),
    ("L09", "code",    "narr", 1.00, 0.26,
     "开始写程序。第一段【读音量】：声音传感器一秒读一百次，把最大的那个值记下来，就像小耳朵竖起来仔细听。"),
    ("L10", "code",    "narr", 1.00, 0.26,
     "第二段【判断有没有声音】：游戏里每10秒放一次声波，一共3次；超过阈值就算有声音，再记下声音是从哪个方向来的。"),
    ("L11", "code",    "narr", 1.00, 0.26,
     "第三段【报告给队友】：红灯亮、小喇叭喊【发现声音】，黄色读条拉满，队友那边的小灯也跟着亮，这就是【全队共享】！"),
    ("L12", "test",    "male", 1.03, 0.40,
     "【回声探测器就位】！前方有人，雷达盘转起来——听！"),
    ("L13", "test",    "narr", 1.00, 0.26,
     "开始【落地实测】！模型摆在空旷的地板上，三个纸箱当掩体，两个小纸人当目标：一个会动，一个安静。"),
    ("L14", "test",    "narr", 1.00, 0.28,
     "按下按键，雷达盘慢慢转起来，蓝色的扫描波一圈一圈扫过去，前方的小耳朵正在竖着听每一个动静！"),
    ("L15", "test",    "narr", 1.00, 0.28,
     "会动的小纸人踩出脚步声！音量一下超过阈值，红灯亮了，喇叭喊【发现声音】，黄色读条拉满，队友的小灯也亮了！"),
    ("L16", "test",    "narr", 1.00, 0.30,
     "现在关键的一步：安静的小纸人一动不动，哪怕站在雷达盘正中间——没有声音，就不会被标记！这就是回响的绝活。"),
    ("L17", "upgrade", "narr", 1.00, 0.28,
     "还能更厉害：加个【无线小发射器】，队友除了小灯还能看手机；把角度调成九十度，反应更快；再装块电池，搬到哪儿都能用。"),
    ("L18", "outro",   "narr", 1.00, 0.20,
     "今天你学会了：声音传感器是【小耳朵】，LED 灯环是【小灯笼】，舵机是【小脖子】！点赞收藏，下期做个会播报天气的太阳能小气象台。"),
]

# ---------------------------------------------------------------- segments
SEG_NAMES = [
    "v01_cover", "v02_parts_photo", "v03_parts_ai", "v04_step_base",
    "v05_step_head", "v06_step_neck", "v07_step_ears", "v08_safety_real",
    "v09_code_read", "v10_code_judge", "v11_code_share", "v12_echo_speak",
    "v13_test_start", "v14_test_scan", "v15_test_mark", "v16_test_quiet",
    "v17_upgrade", "v18_cta",
]

ANIM_SEGS = {"v09_code_read", "v10_code_judge", "v11_code_share",
             "v14_test_scan", "v15_test_mark", "v16_test_quiet"}

AI_FILE = {
    "v01_cover":       "01_cover.png",
    "v03_parts_ai":    "02_parts.png",
    "v04_step_base":   "03_make_base.png",
    "v05_step_head":   "04_make_head.png",
    "v06_step_neck":   "05_make_neck.png",
    "v07_step_ears":   "06_make_ears.png",
    "v12_echo_speak":  "07_scan.png",
    "v13_test_start":  "08_test.png",
    "v17_upgrade":     "09_upgrade.png",
    "v18_cta":         "10_cta.png",
}

REAL_FILE = {
    "v01_cover":       "ref_echo_model.jpg",
    "v02_parts_photo": "ref_echo_skill.jpg",
    "v04_step_base":   "px_35673073.jpg",
    "v05_step_head":   "px_1129413.jpg",
    "v06_step_neck":   "px_25655715.jpg",
    "v07_step_ears":   "px_12741836.jpg",
    "v08_safety_real": "px_8294806.jpg",
    "v12_echo_speak":  "ref_echo_game.jpg",
    "v13_test_start":  "px_sunny_room.jpg",
    "v17_upgrade":     "px_28169155.jpg",
    "v18_cta":         "px_32998845.jpg",
}

# ---------------------------------------------------------------- illustrations
IMAGE_STYLE = ("cute 3d cartoon for children, soft rounded shapes, bright cheerful "
               "colours, clean simple background, friendly faces, handmade cardboard "
               "and paper craft toy styling, dark teal and grey camo with cyan and "
               "green glowing accent stripes")

SHOTS = [
    ("01_cover", "cute 3d cartoon boy proudly holding a handmade cardboard sonar detector toy that looks like a small tripod with a rotating cross antenna array on top, a cyan glowing light ring around the tube, big happy smile, clean shiny floor"),
    ("02_parts", "cute 3d cartoon boy laying out parts on a craft mat: a blue microcontroller board, a tiny microphone module, a small grey servo motor, a green LED light ring, a tiny black speaker, a red push button, a round cardboard disc base and coloured paper fan pieces, each item with a cute smiling face"),
    ("03_make_base", "cute 3d cartoon boy cutting a big circle from brown cardboard with scissors and gluing three cardboard strips as tripod legs under the round disc base, craft table with glue stick, happy"),
    ("04_make_head", "cute 3d cartoon boy rolling a cardboard tube and gluing eight coloured paper fan segments into a cone dome on top of the tube, cheerful"),
    ("05_make_neck", "cute 3d cartoon boy mounting a small grey servo motor under the cardboard dome and sticking a paper cross bar antenna on the servo shaft, focused expression"),
    ("06_make_ears", "cute 3d cartoon boy clipping a small blue microphone module under the cardboard dome, wrapping a green LED light ring around the tube, hiding a tiny black speaker inside, excited"),
    ("07_scan", "cute 3d cartoon boy beside the finished cardboard sonar tripod device on the floor, a big cyan expanding radar wave sweeping forward across the floor, a cute paper robot target far away, sunny room"),
    ("08_test", "cute 3d cartoon boy kneeling on a clean empty floor placing the cardboard sonar tripod device, three cardboard boxes as cover, two cute paper robot targets standing a few steps away, sunny room"),
    ("09_upgrade", "cute 3d cartoon boy holding a tiny wireless module and a small screen next to the finished cardboard sonar device with cyan lights, happy excited face, craft table with tools"),
    ("10_cta", "cute 3d cartoon boy hugging the finished cardboard sonar tripod device with its cyan antenna, sparkles and confetti around him, clean shiny floor, big happy smile"),
]

# ---------------------------------------------------------------- music
BPM = 124.0
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
# the silent gap before the line; the radar sweep uses a long whoosh and the
# "发现声音" alert uses a short rising chime.
SFX_CUES = {
    "ding":   [("L02", -0.30, 0.30), ("L04", -0.38, 0.30),
               ("L07", -0.24, 0.30), ("L12", -0.22, 0.32),
               ("L16", -0.26, 0.30)],
    "whoosh": [("L06", -0.30, 0.22), ("L08", -0.22, 0.24),
               ("L14", -0.34, 0.22), ("L17", -0.26, 0.22)],
    "beep":   [("L09", 1.30, 0.30), ("L10", 3.10, 0.28),
               ("L14", 1.20, 0.28), ("L15", 1.90, 0.30)],
    "chime":  [("L11", 8.60, 0.26), ("L15", 4.60, 0.30), ("L18", 9.60, 0.26)],
}

SFX_EXTRA = {}

BGM_GAIN = 0.20
DUCK_DEPTH = 0.90

# ---------------------------------------------------------------- QA
QA_DURATION = (130.0, 200.0)
QA_MIN_CUTS = 16
QA_MIN_CAPTIONS = 44
QA_MIN_CHARS = 800
QA_RATE_RANGE = (4.0, 6.8)
QA_MIN_SEPARATION_DB = 6.0
QA_MIN_AI = 10
QA_MIN_REAL = 18
QA_KEYWORDS = ["回响", "回声探测器", "Arduino", "声音传感器", "小舵机",
               "LED 灯环", "小喇叭", "按键", "纸板圆底座", "彩纸伞罩",
               "大脑", "小耳朵", "小脖子", "小手指", "小灯笼", "七十米",
               "一百二十度", "全队共享", "发现声音", "黄色读条", "队友",
               "读音量", "阈值", "雷达盘", "落地实测", "点赞", "安全", "每10秒", "3次", "隔着墙",
               "无线小发射器"]

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
