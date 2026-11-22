# -*- coding: utf-8 -*-
"""project.py - the single source of truth for one video.

Topic: 简易巡逻机器人 - a cardboard patrol robot built with an Arduino.

The robot is a SAFE cardboard prop: a kraft-paper chassis on two toy wheels
and one caster, a cardboard head with an ultrasonic "eye", a tiny PIR
"ear", a servo "arm" that waves, a small speaker "mouth" and an LED
"lantern".  It patrols a taped path on the living-room floor, backs away
from obstacles, and reports when it notices a person.

No cameras, no radios, no mains power: it only ever drives a couple of toy
motors on the floor, and the "person" it reports is the kid in the room.
"""
import json
import os

# ---------------------------------------------------------------- output
OUTPUT_NAME = "巡逻机器人_制作到实测.mp4"
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
     "今天是我们的【巡逻机器人】出任务！它自己在客厅里转圈，看到纸箱就绕开，看到有人就挥挥手喊一声，像家里有个小小警卫员！"),
    ("L02", "parts",   "narr", 1.00, 0.26,
     "零件从哪来？Arduino 小车套件一套就有主板、电机和轮子，超声波传感器、人体感应模块和小舵机，另外再准备卡纸和电池盒。"),
    ("L03", "parts",   "narr", 1.00, 0.40,
     "零件都有昵称：主板是【大脑】，超声波是【小眼睛】，人体感应是【小耳朵】，小喇叭是【小嘴巴】，小舵机是【小胳膊】，LED 灯是【小灯笼】。"),
    ("L04", "build",   "narr", 1.00, 0.26,
     "第一步做身体：卡纸剪一个长方形底盘，两侧装上轮子，前面再剪一个小脑袋——这样它才不会歪歪扭扭。"),
    ("L05", "build",   "narr", 1.00, 0.26,
     "第二步装小眼睛和小耳朵：超声波装在脑袋前面量距离，人体感应装在旁边，谁走过它就知道；顶上那颗灯是它的【小灯笼】。"),
    ("L06", "build",   "narr", 1.00, 0.26,
     "第三步装小胳膊和小嘴巴：一个小舵机夹着一片纸当手臂，转起来就是挥手；小喇叭藏在身子后面，专门负责报告情况。"),
    ("L07", "build",   "narr", 1.00, 0.26,
     "第四步接线和装电池：电机驱动板接两个电机，红黑线一根根插紧；电池盒藏在肚子底下，红灯一亮，它就醒过来啦。"),
    ("L08", "safety",  "narr", 1.00, 0.40,
     "安全提醒：这是纸板玩具，不装摄像头也不联网；电池只用充电宝那种，别接插座；喇叭音量调到最小；别让它掉下楼梯；别让它撞到花瓶；家里有宠物，先让它闻闻味道；接线先断电。"),
    ("L09", "code",    "narr", 1.00, 0.26,
     "开始写程序。第一段【直线巡逻】：让两个电机一起转，小车就往前走；两个轮子转得一样快，它就一点不歪。"),
    ("L10", "code",    "narr", 1.00, 0.26,
     "第二段【看见箱子就躲开】：超声波一秒量几次距离，小于【20 厘米】就停一下、往后退，再转个弯，接着继续巡逻。"),
    ("L11", "code",    "narr", 1.00, 0.26,
     "第三段【看见人就报告】：人体感应一发现有人，小灯笼一闪一闪，小胳膊挥起来，小喇叭喊【发现有人】，还记下这是第几次巡逻。"),
    ("L12", "test",    "male", 1.03, 0.40,
     "【发现有人】！一号机器人，正在巡逻！"),
    ("L13", "test",    "narr", 1.00, 0.26,
     "开始【落地实测】！地上贴一条胶带当巡逻路线，房间里摆两个纸箱当障碍，再请一个小朋友来当被巡逻到的人。"),
    ("L14", "test",    "narr", 1.00, 0.28,
     "先测直线巡逻：小车沿着胶带稳稳往前走，蓝灯一闪一闪像在数格子，走了好长一段，一点都没有歪掉！"),
    ("L15", "test",    "narr", 1.00, 0.28,
     "前面有纸箱！超声波一量，只剩十五厘米——停！往后退一点，左转九十度，再继续走，成功绕过纸箱！"),
    ("L16", "test",    "narr", 1.00, 0.30,
     "小朋友走过来了——小耳朵一听见，有人！小灯笼亮起来，小胳膊挥起来，小喇叭喊【发现有人】，机器人报告成功！"),
    ("L17", "upgrade", "narr", 1.00, 0.28,
     "还能更厉害：加个【无线小发射器】，手机上看它走到哪儿；把小灯换成彩色的，一圈变色像彩虹；再多装一块电池，巡逻更久。"),
    ("L18", "outro",   "narr", 1.00, 0.20,
     "今天你学会了：超声波是【小眼睛】，人体感应是【小耳朵】，舵机是【小胳膊】！点赞收藏，下期做个会自己浇花的小助手。"),
]

# ---------------------------------------------------------------- segments
SEG_NAMES = [
    "v01_cover", "v02_parts_photo", "v03_parts_ai", "v04_step_base",
    "v05_step_eye", "v06_step_arm", "v07_step_wire", "v08_safety",
    "v09_code_cruise", "v10_code_avoid", "v11_code_report", "v12_robot_speak",
    "v13_test_start", "v14_test_cruise", "v15_test_avoid", "v16_test_hello",
    "v17_upgrade", "v18_cta",
]

ANIM_SEGS = {"v09_code_cruise", "v10_code_avoid", "v11_code_report",
             "v14_test_cruise", "v15_test_avoid", "v16_test_hello"}

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
    "v13_test_start":  "px_380768.jpg",
    "v17_upgrade":     "px_28169155.jpg",
    "v18_cta":         "px_32998845.jpg",
}

# ---------------------------------------------------------------- illustrations
IMAGE_STYLE = ("cute 3d cartoon render for children, soft rounded shapes, bright cheerful "
               "colours, friendly smiling faces, one single scene, warm plain background, "
               "soft studio lighting, no text, no letters, no words, no numbers, no captions, "
               "no labels, no infographic, no poster, no diagram, no chart, no document, "
               "no screenshot, no comic panels, no split screen")

# Every shot is ONE photographed moment.  Long lists of parts or step-by-step
# wording make the model answer with an infographic, so each prompt keeps to a
# single subject doing a single thing.
SHOTS = [
    ("01_cover", "a cute 3d cartoon boy proudly pushing a handmade cardboard patrol robot toy on wheels, the robot has a rounded kraft paper body, a small head with two blue round eyes, one waving paper arm and a tiny glowing orange lamp on top, sunny living room, big happy smile, one single photo"),
    ("02_parts", "a cute 3d cartoon boy sitting cross-legged on a wooden floor of a playroom, smiling at the camera while holding a small blue circuit board in one hand and a small blue round robot eye sensor in the other hand, a tiny grey motor and a small green light bulb resting on the floor next to him, a snapshot of a real moment"),
    ("03_make_base", "a cute 3d cartoon boy kneeling on a wooden floor, cutting a long brown cardboard rectangle with blue scissors to make the body of a little cardboard robot, a round cardboard head and two yellow toy wheels beside him, focused happy expression, sunny room, one photo"),
    ("04_make_eye", "a cute 3d cartoon boy kneeling on a wooden floor, carefully pressing a small blue round robot eye sensor onto the front of a cardboard robot head he holds in both hands, a tiny green light bulb glowing beside his knee, warm sunny room, one photo"),
    ("05_make_arm", "a cute 3d cartoon boy mounting a small grey servo motor on the side of the cardboard robot and gluing a flat paper strip on the servo arm so it can wave, excited"),
    ("06_make_wire", "a cute 3d cartoon boy sitting at a small craft table, plugging red and black jumper wires from a small red motor driver board into a yellow toy motor, a battery holder and a cardboard chassis on the table, a tiny screwdriver beside him, focused smile, warm room, one photo"),
    ("07_test_setup", "a cute 3d cartoon boy kneeling on a clean living-room floor laying a yellow tape patrol path on the floor with two cardboard boxes as obstacles and a cute paper robot waiting at the start, sunny room"),
    ("08_hello", "a cute 3d cartoon boy waving his hand at a small handmade cardboard robot that is waving a little paper arm back, a glowing orange lamp on the robot head, both smiling at each other in a sunny living room, one photo"),
    ("09_upgrade", "a cute 3d cartoon boy with a big excited smile standing next to the finished cardboard patrol robot on a sunny craft table, a small rainbow glowing LED ring on the robot head, colourful paper and tools on the table, one photo"),
    ("10_cta", "a cute 3d cartoon boy hugging the finished handmade cardboard patrol robot with its glowing orange lamp and waving paper arm, sparkles and confetti around them, clean warm background, big happy smile, one photo"),
    ("11_safety", "a cute 3d cartoon boy carefully placing the small cardboard robot on the floor next to a small friendly dog, a friendly adult waving in the background, warm sunny room, calm careful mood, one photo"),
]

# ---------------------------------------------------------------- music
BPM = 120.0
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
# the silent gap before the line; "motor" is the toy motor whirr that runs
# while the robot is actually driving.
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
}

SFX_EXTRA = {"motor": "build/sfx/motor.wav"}

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
QA_KEYWORDS = ["巡逻机器人", "Arduino", "超声波传感器", "人体感应", "小舵机",
               "小喇叭", "LED 灯", "电机驱动板", "电池盒", "卡纸", "大脑",
               "小眼睛", "小耳朵", "小嘴巴", "小胳膊", "小灯笼", "20 厘米",
               "直线巡逻", "看见箱子就躲开", "看见人就报告", "落地实测",
               "点赞", "安全", "无线小发射器", "发现有人", "巡逻路线", "往后退",
               "左转", "不联网", "接线先断电"]

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
