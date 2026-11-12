# -*- coding: utf-8 -*-
"""project.py - the single source of truth for one video.

Copy this folder, edit this file, then run the stages s1..s9 in order.

Everything the pipeline needs is here: the narration script, the illustration
prompts, the cut list, the music, and the QA thresholds. No stage script
needs editing to make a new video.
"""
import json
import os

# ---------------------------------------------------------------- output
OUTPUT_NAME = "my_video.mp4"      # delivered file name, at the project root
W, H, FPS = 1080, 1920, 30        # 9:16 vertical, 30fps
LEAD_IN = 0.35                    # silence before the first word
TAIL_PAD = 0.9                    # tail after the last word

# ---------------------------------------------------------------- voice
# MiniMax speech-02-hd voice ids. "narr" is the host; "robot" is the
# inanimate object speaking for one beat, which gives the film a joke.
VOICES = {
    "narr":  "Chinese (Mandarin)_Warm_Bestie",
    "robot": "male-qn-jingying",
}

# ---------------------------------------------------------------- script
# One tuple per visual segment. Keep the beat count equal to len(SEG_NAMES).
#   (id, section, voice_key, speed, gap_after_seconds, text)
# 【...】 marks a keyword: it gets highlighted in the captions.
SCRIPT = [
    ("L01", "hook",    "narr", 1.06, 0.30,
     "一个玩具小车，凭什么能自己躲开前面的箱子？答案就藏在今天的这堆零件里。"),
    ("L02", "parts",   "narr", 1.09, 0.26,
     "零件就这几样：一块【主控板】、一块【电机驱动板】、两个【减速电机】、一个【超声波传感器】，再配上面包板和杜邦线。"),
    ("L03", "parts",   "narr", 1.05, 0.50,
     "别被名字吓到，它们的分工可简单了：传感器是【眼睛】，电机是【腿】，主控板是【大脑】。"),
    ("L04", "build",   "narr", 1.08, 0.26,
     "第一步，把两个电机用螺丝固定在底盘两边；第二步，装上轮子和万向轮。"),
    ("L05", "build",   "narr", 1.07, 0.26,
     "第三步最关键：用杜邦线把【主控板】和【电机驱动板】连起来。记住——VCC 接 5V，GND 接 GND，信号线接电机。"),
    ("L06", "build",   "narr", 1.06, 0.26,
     "第四步，把【超声波传感器】架到小车前面，让它的小眼睛盯着前方。"),
    ("L07", "build",   "narr", 1.05, 0.50,
     "接线要小心：正负极接反了，小车可能不动，还可能烧坏板子。"),
    ("L08", "code",    "narr", 1.05, 0.28,
     "接下来给小车写程序。它只要干三件事：【往前走】、【听距离】、【转弯躲开】。"),
    ("L09", "code",    "narr", 1.02, 0.26,
     "先看 setup：pinMode 把引脚设成输出；再看 loop，它每一秒重复同一件事——先量出前方障碍物的距离。"),
    ("L10", "code",    "narr", 1.00, 0.28,
     "如果距离小于【30 厘米】，就说明前面有东西，【后退】、【转向】；如果大于 30 厘米，就继续【往前冲】。"),
    ("L11", "code",    "narr", 1.00, 0.40,
     "这个 if，就是数学课上的“如果 A，就 B”，是不是很像？"),
    ("L12", "test",    "robot", 1.06, 0.42,
     "叮！前方有障碍物，我左转六十度，继续出发！"),
    ("L13", "test",    "narr", 1.06, 0.26,
     "现在把小车放到地板上，开始落地实测！按下上传键——一、二、三，走！"),
    ("L14", "test",    "narr", 1.05, 0.26,
     "看，小车笔直往前走……前面有个箱子，它立刻刹车、后退，然后向右一拐，绕过去继续前进！"),
    ("L15", "test",    "narr", 1.05, 0.50,
     "总是撞上？没关系，把 30 厘米改成 20，让它提前刹车，多试几次就顺啦。"),
    ("L16", "upgrade", "narr", 1.05, 0.28,
     "想让小车更聪明？再加两个红外传感器，它就能沿着黑线跑——这就是【循迹小车】。"),
    ("L17", "outro",   "narr", 1.04, 0.30,
     "今天你学会了：传感器负责看，电机负责走，程序负责想。"),
    ("L18", "outro",   "narr", 1.06, 0.20,
     "零成本也能做出一辆会思考的小车！点赞收藏！下期，让它追着光跑。"),
]

# ---------------------------------------------------------------- cut list
# One visual segment per narration beat, in the same order.
# "anim" segments are rendered by anim.py; everything else is a static card.
SEG_NAMES = [
    "v01_cover", "v02_parts_photo", "v03_parts_ai", "v04_step_motor", "v05_step_wire",
    "v06_wire_real", "v07_step_sensor", "v08_code_intro", "v09_code_setup", "v10_code_loop",
    "v11_flow", "v12_robot", "v13_test_start", "v14_test_drive", "v15_tune",
    "v16_upgrade", "v17_summary", "v18_cta",
]

ANIM_SEGS = {"v09_code_setup", "v10_code_loop", "v11_flow", "v14_test_drive"}

# Which illustration each segment draws on. Value is a file in assets/ai.
AI_FILE = {
    "v01_cover": "01_cover.png",
    "v03_parts_ai": "02_parts.png",
    "v04_step_motor": "03_assemble_motor.png",
    "v05_step_wire": "04_assemble_wire.png",
    "v06_wire_real": "05_assemble_sensor.png",
    "v08_code_intro": "06_code.png",
    "v12_robot": "07_test.png",
    "v16_upgrade": "08_upgrade.png",
    "v17_summary": "09_mascot.png",
    "v18_cta": "09_mascot.png",
}

# ---------------------------------------------------------------- illustration prompts
# One (filename_stem, prompt) per image. The STYLE prefix is shared.
IMAGE_STYLE = ("children's book illustration, soft watercolor and crayon texture, warm cream paper background, "
               "gentle orange and teal accent palette, cute cartoon boy about 8 years old with round eyes wearing "
               "orange overalls and a yellow t-shirt, clean flat shapes, soft shadows, no text, no watermark, "
               "no letters, vertical composition, plenty of empty cream space around the subject")
IMAGE_ASPECT = "9:16"
IMAGE_MODEL = "image-01"

SHOTS = [
    ("01_cover", "a cheerful cartoon boy kneeling beside a small homemade four-wheel robot car that he built, "
                 "the car has a blue ultrasonic sensor with two round eyes on the front and yellow wheels, a desk "
                 "workshop background with a laptop and some wires, the boy is smiling and waving at the viewer"),
    ("02_parts", "a cartoon boy holding up a small open toolbox, floating around him in a neat row: a blue "
                 "microcontroller board, a green circuit board, two small silver electric motors with yellow "
                 "wheels, a small white breadboard, colorful jumper wires and a small blue ultrasonic sensor, "
                 "each item drawn as a clear friendly icon, arrangement like a science textbook plate"),
    ("03_assemble_motor", "close up top-down view of a cartoon boy's small hands using a screwdriver to bolt a "
                          "silver electric motor with a yellow wheel onto a small two-wheel robot chassis, "
                          "a few screws and a blue screwdriver lying beside it, workbench surface"),
    ("04_assemble_wire", "close up of a cartoon boy's hands plugging colorful red and black jumper wires into a "
                         "blue microcontroller board and a green motor driver board mounted on a small robot "
                         "chassis, the wires connect the board to a motor, colorful and tidy, workbench surface"),
    ("05_assemble_sensor", "cartoon boy carefully clipping a small blue ultrasonic sensor with two round silver "
                           "eyes onto the front top of his small robot car, a tiny red led blinking on the sensor, "
                           "the boy looks curious and focused, workbench surface"),
    ("06_code", "cartoon boy sitting cross legged in front of an open laptop whose screen glows with colorful "
                "simple code lines, a friendly small robot car with big eyes sits next to the laptop watching, "
                "a small blackboard with a simple flow diagram is behind them"),
    ("07_test", "cartoon boy kneeling on a wooden floor placing his small robot car onto a taped white line track, "
                "a small cardboard box obstacle stands ahead of the car, the boy is watching it carefully, "
                "a few toy blocks and a ruler on the floor, warm home interior"),
    ("08_upgrade", "cartoon boy celebrating with both arms raised as his small robot car follows a thick black "
                   "line drawn on white paper, two small red infrared eyes glow at the front of the car, "
                   "a happy little robot face drawn on the car body"),
    ("09_mascot", "a cute mascot small robot car alone, teal and red rounded body with two big friendly eyes, "
                  "yellow wheels, a small blue ultrasonic sensor on top, waving, standing on a soft cream ground "
                  "with a subtle warm shadow, centered with generous empty space"),
]

# ---------------------------------------------------------------- music
BPM = 100.0
CHORDS = [                                   # I - V - vi - IV in C major
    (48, [60, 64, 67]),
    (43, [59, 62, 67]),
    (45, [57, 60, 64]),
    (41, [57, 60, 65]),
]
MELODY = [                                   # (bar offset in beats, midi, length in beats)
    (0, 76, 1.5), (2, 79, 1.0), (4, 72, 1.0), (5, 74, 1.0),
    (8, 76, 1.0), (10, 79, 1.5), (12, 84, 2.0),
    (16, 81, 1.0), (18, 79, 1.0), (20, 76, 1.5), (22, 72, 1.5),
    (24, 74, 1.0), (26, 76, 1.0), (28, 79, 2.0), (30, 76, 1.5),
]
# Sound effects are anchored to narration lines, not absolute seconds:
#   (line_id, offset_seconds, amplitude)
# That way they stay in sync even when the TTS run comes out longer or
# shorter than the previous one.
SFX_CUES = {                                # sound name -> [(line_id, offset, amp)]
    "ding":   [("L02", 0.00, 0.30), ("L04", 0.00, 0.30),
               ("L08", 0.00, 0.30), ("L12", 0.00, 0.30)],
    "whoosh": [("L06", 0.00, 0.16)],
    "beep":   [("L12", -0.25, 0.40)],
    "chime":  [("L18", -0.70, 0.26)],
}
BGM_GAIN = 0.26                              # music level under the voice
DUCK_DEPTH = 0.86                           # how much the music drops under speech

# ---------------------------------------------------------------- QA
QA_DURATION = (120.0, 130.0)
QA_MIN_CUTS = 16
QA_MIN_CAPTIONS = 40
QA_MIN_CHARS = 600
QA_RATE_RANGE = (4.0, 6.8)                  # Chinese chars per second
QA_MIN_SEPARATION_DB = 6.0                  # voice above the music bed
QA_MIN_AI = 9
QA_MIN_REAL = 5
QA_KEYWORDS = ["主控板", "电机驱动板", "超声波传感器", "减速电机", "接线",
               "VCC", "GND", "setup", "loop", "pinMode", "30 厘米",
               "后退", "转向", "落地实测", "循迹", "点赞"]

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
