# -*- coding: utf-8 -*-
"""project.py - the single source of truth for one video.

Topic: 简易小鸟机器人 - a cardboard bird robot built with an Arduino.

The bird is a SAFE cardboard prop: a fat kraft-paper bird body on two toy
wheels, two paper wings on little servo motors, a light sensor on its head,
an ultrasonic "radar" in front of its beak, a tiny speaker "mouth" and an
LED "lantern".  It flaps its wings, turns towards a light, backs away when
something blocks its way and chirps with its little speaker.

No cameras, no radios, no mains power and no real flying motor: it only
turns two toy servos and rolls a couple of toy motors on the floor.
"""
import json
import os

# ---------------------------------------------------------------- output
OUTPUT_NAME = "小鸟机器人_制作到实测.mp4"
W, H, FPS = 1080, 1920, 30
LEAD_IN = 0.35
TAIL_PAD = 0.9

# ---------------------------------------------------------------- voices
VOICES = {
    # "male" is used for the bird's own chirp so the caption pass paints it red
    "narr":  "Chinese (Mandarin)_Warm_Bestie",
    "male":  "male-qn-jingying",
}
VOICE_PITCH = {"narr": "+0%", "male": "+14%"}
VOICE_BREATH = {"narr": 170, "male": 200}
VOICE_RATE_BIAS = 2

# ---------------------------------------------------------------- script
#   (id, section, voice_key, speed, gap_after_seconds, text)
# 【...】 marks a keyword: it gets highlighted in the captions.
SCRIPT = [
    ("L01", "hook",    "narr", 1.03, 0.32,
     "今天是我们的小鸟机器人出任务！它的翅膀一上一下地扇，看到光就转过来，前面有东西挡路还会往后退，还会唱歌——啾啾啾！"),
    ("L02", "parts",   "narr", 1.00, 0.26,
     "零件从哪来？Arduino 套件一套就有主板、电机和轮子，光敏电阻、超声波传感器、小喇叭、两个小舵机，另外再准备卡纸、彩色卡纸和电池盒。"),
    ("L03", "parts",   "narr", 1.00, 0.40,
     "零件都有昵称：主板是【大脑】，光敏电阻是【小眼睛】，超声波是【小雷达】，小喇叭是【小嘴巴】，两个舵机是【小翅膀】，LED 灯是【小灯笼】，电机是【小脚丫】。"),
    ("L04", "build",   "narr", 1.00, 0.26,
     "第一步做身体：卡纸剪一个胖胖的鸟身子，两边装上轮子，尾巴再剪三片羽毛，这样它的小脚丫就能在地上走啦。"),
    ("L05", "build",   "narr", 1.00, 0.26,
     "第二步做翅膀：两个小舵机分别粘在身子两边，舵机臂上各夹一片彩色羽毛翅膀，一上一下地扇，就像小鸟在飞一样。"),
    ("L06", "build",   "narr", 1.00, 0.26,
     "第三步装小眼睛和小雷达：光敏电阻放在脑袋顶上量亮不亮，超声波装在嘴巴前面量前面多远，小喇叭塞进身体里专门负责唱歌。"),
    ("L07", "build",   "narr", 1.00, 0.26,
     "第四步接线和装电池：电机驱动板接电机，舵机线插进主板，喇叭线插进音频口，红黑线一根根插紧；电池盒藏在肚子底下，一开开关它就醒过来啦。"),
    ("L08", "safety",  "narr", 1.00, 0.40,
     "安全提醒：这是纸板玩具，不装摄像头也不联网；电池只用充电宝那种，别接插座；喇叭音量调到最小；别让它掉下楼梯；离花瓶和桌角远一点；家里有宠物，先让它闻闻味道；接线先断电。"),
    ("L09", "code",    "narr", 1.00, 0.26,
     "开始写程序。第一段【张开翅膀】：左翅膀转到六十度，右翅膀转到一百二十度，一高一低，翅膀就扇起来啦。"),
    ("L10", "code",    "narr", 1.00, 0.26,
     "第二段【看见光就转过来】：光敏电阻一秒量好几次，光线超过【500】就慢慢转过头，再唱一句。"),
    ("L11", "code",    "narr", 1.00, 0.26,
     "第三段【前面太近就后退】：超声波量到前面只剩【20 厘米】，先停一下、往后退一点，再唱一声啾，接着继续飞。"),
    ("L12", "test",    "male", 1.03, 0.40,
     "【啾啾】！我是小小鸟，飞起来啦！"),
    ("L13", "test",    "narr", 1.00, 0.26,
     "开始落地实测！地上贴一条胶带当飞行路线，摆一个纸箱当障碍，前面放一支手电筒，再撒一点彩纸屑。"),
    ("L14", "test",    "narr", 1.00, 0.28,
     "先测扇翅膀：左翅膀高、右翅膀低，上下错开，扇得又稳又好看，小灯笼一闪一闪像在数拍子。"),
    ("L15", "test",    "narr", 1.00, 0.28,
     "前面有纸箱挡路！小雷达一量，只剩十五厘米——停！往后退一点，啾一声，再接着往前飞。"),
    ("L16", "test",    "narr", 1.00, 0.30,
     "手电筒照过来啦！小眼睛一看，光线数值一下子变大，它慢慢把头转过来对着光，翅膀扇得更快，还唱起了歌！"),
    ("L17", "upgrade", "narr", 1.00, 0.28,
     "还能更厉害：加个迷你小风扇吹羽毛；再装一块小太阳能板白天晒太阳充电；换成锂电池，就能飞更久一点。"),
    ("L18", "outro",   "narr", 1.00, 0.40,
     "今天你学会了：光敏电阻是小眼睛，舵机是小翅膀，超声波是小雷达！点赞收藏，下期做个会自己报时的小闹钟。"),
]

# ---------------------------------------------------------------- segments
SEG_NAMES = [
    "v01_cover", "v02_parts_photo", "v03_parts_ai",
    "v04_step_body", "v05_step_wing", "v06_step_eye", "v07_step_wire",
    "v08_safety",
    "v09_code_wing", "v10_code_light", "v11_code_back",
    "v12_robot_speak", "v13_test_start",
    "v14_test_flap", "v15_test_block", "v16_test_light",
    "v17_upgrade", "v18_cta",
]

ANIM_SEGS = {"v09_code_wing", "v10_code_light", "v11_code_back",
             "v14_test_flap", "v15_test_block", "v16_test_light"}

AI_FILE = {
    "v01_cover":       "01_cover.png",
    "v03_parts_ai":    "02_parts.png",
    "v04_step_body":   "03_make_body.png",
    "v05_step_wing":   "04_make_wing.png",
    "v06_step_eye":    "05_make_eye.png",
    "v07_step_wire":   "06_make_wire.png",
    "v08_safety":      "11_safety.png",
    "v12_robot_speak": "08_hello.png",
    "v13_test_start":  "07_test_setup.png",
    "v17_upgrade":     "09_upgrade.png",
    "v18_cta":         "10_cta.png",
}

REAL_FILE = {
    "v01_cover":       "px_8294806.jpg",
    "v02_parts_photo": "px_35673081.jpg",
    "v04_step_body":   "px_35673073.jpg",
    "v05_step_wing":   "px_2589555.jpg",
    "v06_step_eye":    "px_35673112.jpg",
    "v07_step_wire":   "px_25655715.jpg",
    "v08_safety":      "pet_golden.jpg",
    "v12_robot_speak": "px_32998845.jpg",
    "v13_test_start":  "px_8294806.jpg",
    "v17_upgrade":     "px_solar_worker.jpg",
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
    ("01_cover", "a cute 3d cartoon boy proudly holding up a small handmade cardboard bird robot, the robot has a fat round kraft paper bird body, two colourful feather paper wings spread wide, a small orange paper beak, a glowing yellow lamp on its head and two tiny toy wheels at the bottom, sunny living room, big happy smile, one single photo"),
    ("02_parts", "a cute 3d cartoon boy sitting cross-legged on a wooden floor of a playroom, smiling at the camera while holding a small blue circuit board in one hand and a tiny green light sensor in the other hand, a small grey servo motor and a small round speaker resting on the floor next to him, a snapshot of a real moment"),
    ("03_make_body", "a cute 3d cartoon boy kneeling on a wooden floor, cutting a fat oval brown cardboard shape with blue scissors to make the body of a little cardboard bird robot, three colourful paper feathers and a yellow toy wheel lying beside him, focused happy expression, sunny room, one photo"),
    ("04_make_wing", "a cute 3d cartoon boy gluing a colourful blue feather shaped paper wing onto the arm of a small grey servo motor, a round kraft paper bird body waiting next to him on the floor, excited smile, warm sunny room, one photo"),
    ("05_make_eye", "a cute 3d cartoon boy kneeling on a wooden floor, carefully sticking a tiny round light sensor onto the top of a round kraft paper bird head he holds in both hands, a small blue sensor module beside his knee, warm sunny room, one photo"),
    ("06_make_wire", "a close up of a cute 3d cartoon boy at a craft table, his small hands plugging a red and a black jumper wire into a small red motor driver board, a tiny grey servo motor and a battery holder resting on the wooden table, shallow depth of field close up shot, warm room"),
    ("07_test_setup", "a cute 3d cartoon boy kneeling on a clean living-room floor laying a yellow tape path on the floor, a table leg with a small cardboard box beside the path, a flashlight lying on the floor and a few colourful paper feathers scattered around, a cute cardboard bird robot waiting at the start, sunny room"),
    ("08_hello", "a cute 3d cartoon boy waving his hand at a small handmade cardboard bird robot that is flapping its colourful paper wings back, a glowing yellow lamp on the robot head, both smiling at each other in a sunny living room, one photo"),
    ("09_upgrade", "a cute 3d cartoon boy with a big excited smile standing next to the finished cardboard bird robot on a sunny craft table, a small solar panel and a tiny toy fan attached to the robot, colourful paper feathers and tools on the table, one photo"),
    ("10_cta", "a cute 3d cartoon boy hugging the finished handmade cardboard bird robot with its glowing yellow lamp and colourful feather wings, sparkles and confetti around them, clean warm plain background, big happy smile, one photo"),
    ("11_safety", "a cute 3d cartoon boy carefully placing the small cardboard bird robot on the floor next to a small friendly dog, a friendly adult waving in the background, warm sunny room, calm careful mood, one photo"),
]

# ---------------------------------------------------------------- music
BPM = 124.0
CHORDS = [                                   # I - V - vi - IV in G major
    (43, [59, 62, 67]),
    (38, [55, 59, 62]),
    (40, [57, 60, 64]),
    (36, [57, 60, 65]),
]
MELODY = [                                   # (bar offset in beats, midi, length in beats)
    (0, 79, 1.0), (1, 81, 1.0), (2, 84, 1.5), (4, 79, 1.0),
    (6, 76, 1.0), (8, 79, 1.5), (10, 74, 1.0), (12, 72, 1.0),
    (16, 74, 1.0), (18, 79, 1.0), (20, 81, 1.5), (22, 79, 1.0),
    (24, 76, 1.0), (26, 74, 1.0), (28, 71, 1.5), (30, 67, 1.5),
]

# ---------------------------------------------------------------- sound effects
# ding / whoosh / beep / chime are transition markers whose attack is placed in
# the silent gap before the line; "chirp" is the little bird call and "flap"
# is the paper wings beating.
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
    "chirp":  [("L11", 6.20, 0.30), ("L12", -0.18, 0.34),
               ("L15", 5.40, 0.30), ("L16", 4.60, 0.32),
               ("L17", 6.20, 0.28)],
    "flap":   [("L09", 2.20, 0.26), ("L10", 5.60, 0.24),
               ("L14", 1.40, 0.30), ("L16", 1.60, 0.30),
               ("L16", 6.20, 0.26)],
}

SFX_EXTRA = {"chirp": "build/sfx/chirp.wav", "flap": "build/sfx/flap.wav"}

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
QA_KEYWORDS = ["小鸟机器人", "Arduino", "光敏电阻", "超声波传感器", "小喇叭",
               "舵机", "LED 灯", "电机驱动板", "电池盒", "卡纸", "大脑",
               "小眼睛", "小雷达", "小嘴巴", "小翅膀", "小灯笼", "小脚丫",
               "20 厘米", "500", "张开翅膀", "看见光就转过来",
               "前面太近就后退", "落地实测", "点赞", "安全", "不联网",
               "接线先断电", "往后退", "唱歌", "手电筒", "小鸟", "彩纸屑"]

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
