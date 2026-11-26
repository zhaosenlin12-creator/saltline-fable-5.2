# -*- coding: utf-8 -*-
"""project.py - the single source of truth for one video.

Topic: 简易扫地机器人 - a cardboard robot vacuum built with an Arduino.

The robot is a SAFE cardboard prop: a round kraft-paper body on two toy
wheels and one caster, a small ultrasonic "eye" on the front, a tiny PIR
"ear", a servo side brush that sweeps the floor, a small speaker "mouth"
and an LED "lantern".  It drives a taped path on the living-room floor,
backs away from obstacles, sweeps paper scraps into a paper bin and
reports when a lap is finished.

No cameras, no radios, no mains power and no real vacuum motor: it only
drives a couple of toy motors on the floor, and the "person" it hears is
the kid in the room.
"""
import json
import os

# ---------------------------------------------------------------- output
OUTPUT_NAME = "扫地机器人_制作到实测.mp4"
W, H, FPS = 1080, 1920, 30
LEAD_IN = 0.35
TAIL_PAD = 0.9

# ---------------------------------------------------------------- voices
VOICES = {
    # "male" is used for the robot's own shout so the caption pass paints it red
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
     "今天是我们的【扫地机器人】出任务！它自己在客厅里转圈，看到箱子就绕开，看到纸屑就扫起来，像家里有个小小清洁工！"),
    ("L02", "parts",   "narr", 1.00, 0.26,
     "零件从哪来？Arduino 小车套件一套就有主板、电机和轮子，超声波传感器、小喇叭和小舵机，另外再准备卡纸和电池盒。"),
    ("L03", "parts",   "narr", 1.00, 0.40,
     "零件都有昵称：主板是【大脑】，超声波是【小眼睛】，小喇叭是【小嘴巴】，小舵机是【小刷子】，LED 灯是【小灯笼】，电机是【小脚丫】。"),
    ("L04", "build",   "narr", 1.00, 0.26,
     "第一步做身体：卡纸剪一个圆圆的身体，两边装上轮子，前面再剪一个小鼻子——这样它才能贴着地板慢慢走。"),
    ("L05", "build",   "narr", 1.00, 0.26,
     "第二步装小眼睛和小刷子：超声波装在最前面量距离，小舵机夹着一片彩纸当刷子，转起来就能把纸屑扫起来。"),
    ("L06", "build",   "narr", 1.00, 0.26,
     "第三步装小耳朵和小嘴巴：人体感应装在旁边，谁走过来它就知道；小喇叭藏在身子后面，专门负责报告情况。"),
    ("L07", "build",   "narr", 1.00, 0.26,
     "第四步接线和装电池：电机驱动板接两个电机，红黑线一根根插紧；电池盒藏在肚子底下，红灯一亮，它就醒过来啦。"),
    ("L08", "safety",  "narr", 1.00, 0.40,
     "安全提醒：这是纸板玩具，不装摄像头也不联网；电池只用充电宝那种，别接插座；喇叭音量调到最小；别让它掉下楼梯；别让它撞到花瓶；家里有宠物，先让它闻闻味道；接线先断电。"),
    ("L09", "code",    "narr", 1.00, 0.26,
     "开始写程序。第一段【开始扫地】：让两个电机一起转，小车就往前走；两个轮子转得一样快，它就一点不歪。"),
    ("L10", "code",    "narr", 1.00, 0.26,
     "第二段【碰到东西就拐弯】：超声波一秒量几次距离，小于【20 厘米】就停一下、往后退，再向右转个弯，接着接着扫。"),
    ("L11", "code",    "narr", 1.00, 0.26,
     "第三段【扫完一圈报个到】：一圈扫完，小灯笼一闪一闪，小刷子挥起来，小喇叭喊【扫干净啦】，还记下这是第几圈。"),
    ("L12", "test",    "male", 1.03, 0.40,
     "【扫干净啦】！一号机器人，扫地完成！"),
    ("L13", "test",    "narr", 1.00, 0.26,
     "开始【落地实测】！地上贴一条胶带当清扫路线，房间里摆一个纸箱当障碍，再撒一点碎纸屑，旁边放个小纸盒。"),
    ("L14", "test",    "narr", 1.00, 0.28,
     "先测直线清扫：小车沿着胶带稳稳往前走，蓝灯一闪一闪像在数格子，走了好长一段，一点都没有歪掉！"),
    ("L15", "test",    "narr", 1.00, 0.28,
     "前面有纸箱！超声波一量，只剩十五厘米——停！往后退一点，右转九十度，再继续走，成功绕过纸箱！"),
    ("L16", "test",    "narr", 1.00, 0.30,
     "碎纸屑被小刷子扫起来了！小车一边转圈一边扫，纸屑一点点被推进小纸盒里——哇，地板真的干净了！"),
    ("L17", "upgrade", "narr", 1.00, 0.28,
     "还能更厉害：加个【无线小发射器】，手机上看它扫到哪儿；再装一根小吸管，纸屑直接吸进去；多装一块电池，扫得更久。"),
    ("L18", "outro",   "narr", 1.00, 0.20,
     "今天你学会了：超声波是【小眼睛】，舵机是【小刷子】，电机是【小脚丫】！点赞收藏，下期做个会自己浇花的小助手。"),
]

# ---------------------------------------------------------------- segments
SEG_NAMES = [
    "v01_cover", "v02_parts_photo", "v03_parts_ai", "v04_step_base",
    "v05_step_eye", "v06_step_arm", "v07_step_wire", "v08_safety",
    "v09_code_cruise", "v10_code_avoid", "v11_code_report", "v12_robot_speak",
    "v13_test_start", "v14_test_cruise", "v15_test_avoid", "v16_test_sweep",
    "v17_upgrade", "v18_cta",
]

ANIM_SEGS = {"v09_code_cruise", "v10_code_avoid", "v11_code_report",
             "v14_test_cruise", "v15_test_avoid", "v16_test_sweep"}

AI_FILE = {
    "v01_cover":       "01_cover.png",
    "v03_parts_ai":    "02_parts.png",
    "v04_step_base":   "03_make_base.png",
    "v05_step_eye":    "04_make_eye.png",
    "v06_step_arm":    "05_make_arm.png",
    "v07_step_wire":   "06_make_wire.png",
    "v08_safety":      "11_safety.png",
    "v12_robot_speak": "08_hello.png",
    "v13_test_start":  "07_test_setup.png",
    "v17_upgrade":     "09_upgrade.png",
    "v18_cta":         "10_cta.png",
}

REAL_FILE = {
    "v01_cover":       "px_35673081.jpg",
    "v02_parts_photo": "px_7868822.jpg",
    "v04_step_base":   "px_35673073.jpg",
    "v05_step_eye":    "px_12741836.jpg",
    "v06_step_arm":    "px_25655715.jpg",
    "v07_step_wire":   "px_35673112.jpg",
    "v08_safety":      "px_2607544.jpg",
    "v12_robot_speak": "px_8294806.jpg",
    "v13_test_start":  "px_12741836.jpg",
    "v17_upgrade":     "px_28169155.jpg",
    "v18_cta":         "px_32998845.jpg",
}

# ---------------------------------------------------------------- illustrations
# Every shot is ONE photographed moment.  Long lists of parts or step-by-step
# wording make the model answer with an infographic, so each prompt keeps to a
# single subject doing a single thing.
IMAGE_STYLE = ("cute 3d cartoon render for children, soft rounded shapes, bright cheerful "
               "colours, friendly smiling faces, one single scene, warm plain background, "
               "soft studio lighting, no text, no letters, no words, no numbers, no captions, "
               "no labels, no infographic, no poster, no diagram, no chart, no document, "
               "no screenshot, no comic panels, no split screen, no watermark, no signature, "
               "no logo")

SHOTS = [
    ("01_cover", "a cute 3d cartoon boy proudly pushing a small handmade cardboard robot vacuum toy across the floor, the robot has a round kraft paper body, a small blue round sensor eye on the front, a colourful paper side brush spinning beside it and a tiny glowing orange lamp on top, sunny living room, big happy smile, one single photo"),
    ("02_parts", "a cute 3d cartoon boy sitting cross-legged on a wooden floor of a playroom, smiling at the camera while holding a small blue circuit board in one hand and a small blue round robot eye sensor in the other hand, a tiny grey motor and a small green light bulb resting on the floor next to him, a snapshot of a real moment"),
    ("03_make_base", "a cute 3d cartoon boy kneeling on a wooden floor, cutting a big round brown cardboard disc with blue scissors to make the body of a little cardboard robot vacuum, a yellow toy wheel and a small cardboard box beside him, focused happy expression, sunny room, one photo"),
    ("04_make_eye", "a cute 3d cartoon boy kneeling on a wooden floor, carefully pressing a small blue round robot eye sensor onto the front of a round cardboard robot body he holds in both hands, a tiny green light bulb glowing beside his knee, warm sunny room, one photo"),
    ("05_make_arm", "a cute 3d cartoon boy mounting a small grey servo motor on the side of a round cardboard robot body and gluing a colourful paper strip on the servo arm so it can sweep the floor, excited, one photo"),
    ("06_make_wire", "a close up of a cute 3d cartoon boy at a craft table, his small hands plugging a red and a black jumper wire into a small red motor driver board, a yellow toy motor and a battery holder resting on the wooden table, a tiny screwdriver beside his hand, shallow depth of field close up shot, warm room"),
    ("07_test_setup", "a cute 3d cartoon boy kneeling on a clean living-room floor laying a yellow tape path on the floor, a small cardboard box and a little paper bin beside the path, a few paper scraps scattered on the floor and a cute round cardboard robot waiting at the start, sunny room"),
    ("08_hello", "a cute 3d cartoon boy waving his hand at a small handmade cardboard robot vacuum that is waving a little paper side brush back, a glowing orange lamp on top of the robot, both smiling at each other in a sunny living room, one photo"),
    ("09_upgrade", "a cute 3d cartoon boy with a big excited smile standing next to the finished cardboard robot vacuum on a sunny craft table, a small rainbow glowing LED ring on the robot, colourful paper and tools on the table, one photo"),
    ("10_cta", "a cute 3d cartoon boy hugging the finished handmade cardboard robot vacuum with its glowing orange lamp and a colourful paper side brush, sparkles and confetti around them, clean warm plain background, big happy smile, one photo"),
    ("11_safety", "a cute 3d cartoon boy carefully placing the small cardboard robot vacuum on the floor next to a small friendly dog, a friendly adult waving in the background, warm sunny room, calm careful mood, one photo"),
]

# ---------------------------------------------------------------- music
BPM = 116.0
CHORDS = [                                   # I - V - vi - IV in C major
    (48, [60, 64, 67]),
    (43, [59, 62, 67]),
    (45, [57, 60, 64]),
    (41, [57, 60, 65]),
]
MELODY = [                                   # (bar offset in beats, midi, length in beats)
    (0, 76, 1.0), (1, 81, 1.0), (2, 84, 1.5), (4, 79, 1.0),
    (6, 76, 1.0), (8, 72, 1.5), (10, 74, 1.0), (12, 76, 1.0),
    (16, 79, 1.0), (18, 83, 1.0), (20, 79, 1.5), (22, 76, 1.0),
    (24, 76, 1.0), (26, 71, 1.0), (28, 72, 1.5), (30, 67, 1.5),
]

# ---------------------------------------------------------------- sound effects
# ding / whoosh / beep / chime are transition markers whose attack is placed in
# the silent gap before the line; "motor" is the toy motor whirr that runs
# while the robot is actually driving; "swish" is the paper brush sweeping.
SFX_CUES = {
    "ding":   [("L02", -0.30, 0.30), ("L04", -0.38, 0.30),
               ("L07", -0.24, 0.30), ("L12", -0.22, 0.32),
               ("L16", -0.26, 0.30)],
    "whoosh": [("L05", -0.30, 0.22), ("L08", -0.22, 0.24),
               ("L11", 6.60, 0.26), ("L14", -0.34, 0.22),
               ("L17", -0.26, 0.22)],
    "beep":   [("L09", 1.30, 0.28), ("L10", 3.10, 0.26),
               ("L13", 1.20, 0.28), ("L15", 4.60, 0.28)],
    "chime":  [("L11", 8.80, 0.26), ("L16", 3.60, 0.28), ("L18", 9.60, 0.26)],
    "motor":  [("L09", 2.20, 0.26), ("L10", 5.60, 0.24),
               ("L14", 1.40, 0.30), ("L15", 1.40, 0.30), ("L16", 0.90, 0.24)],
    "swish":  [("L05", 3.20, 0.22), ("L11", 4.40, 0.20),
               ("L16", 1.80, 0.22), ("L16", 5.40, 0.20)],
}

SFX_EXTRA = {"motor": "build/sfx/motor.wav", "swish": "build/sfx/swish.wav"}

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
QA_KEYWORDS = ["扫地机器人", "Arduino", "超声波传感器", "人体感应", "小舵机",
               "小喇叭", "LED 灯", "电机驱动板", "电池盒", "卡纸", "大脑",
               "小眼睛", "小耳朵", "小嘴巴", "小刷子", "小灯笼", "小脚丫",
               "20 厘米", "开始扫地", "碰到东西就拐弯", "扫完一圈报个到",
               "落地实测", "点赞", "安全", "无线小发射器", "扫干净啦",
               "清扫路线", "往后退", "右转", "不联网", "接线先断电"]

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
