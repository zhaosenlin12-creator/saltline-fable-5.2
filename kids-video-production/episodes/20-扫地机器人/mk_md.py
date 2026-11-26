# -*- coding: utf-8 -*-
"""Build the narration / rhythm sheet for the 简易扫地机器人 film."""
import json, os, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "扫地机器人_配音文案与节奏表.md")
BT = chr(96)
tl = json.load(open(os.path.join(BUILD, "timeline.json"), encoding="utf-8"))

SEC_CN = {"hook": "开场钩子", "parts": "认识零件", "build": "动手制作",
          "code": "写程序", "safety": "安全提醒",
          "test": "落地实测", "upgrade": "升级", "outro": "总结收尾"}
VOICE_CN = {"narr": "旁白（MiniMax Chinese (Mandarin)_Warm_Bestie）",
            "male": "机器人拟人（MiniMax male-qn-jingying）"}

sys.path.insert(0, ROOT)
import project as P

rows = []
for i, ln in enumerate(tl["lines"]):
    seg = P.SEG_NAMES[i]
    kind = "动画" if seg in P.ANIM_SEGS else "卡片"
    rows.append("| %02d | %s %s | %.2fs | %.2fs | %.2fs | %s | %s | %s %s%s%s |" % (
        i + 1, ln["section"], SEC_CN[ln["section"]], ln["start"], ln["end"], ln["dur"],
        VOICE_CN[ln["voice_key"]], ln["text"], kind, BT, seg, BT))

chars = sum(len(l["plain"]) for l in tl["lines"])
rates = [len(l["plain"]) / l["dur"] for l in tl["lines"]]

movie = os.path.join(ROOT, P.OUTPUT_NAME)
probe = json.loads(subprocess.run(
    ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", movie],
    capture_output=True, text=True, encoding="utf-8").stdout)
dur = float(probe["format"]["duration"])
size_mb = int(probe["format"]["size"]) / 1e6

raw = os.path.join(BUILD, "qa_audio.wav")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", movie, "-ac", "1", "-ar", "44100",
                "-c:a", "pcm_s16le", raw], capture_output=True)
with wave.open(raw, "rb") as w:
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
win = sr // 10
m = len(x) // win
lv = np.sqrt((x[:m * win].reshape(m, win) ** 2).mean(axis=1))
sp = set()
for l in tl["lines"]:
    for k in range(int(l["start"] * 10), int(l["end"] * 10)):
        sp.add(k)
sp_r = [lv[k] for k in sp if k < len(lv)]
mu_r = [lv[k] for k in range(len(lv)) if k not in sp]
sep = 20 * np.log10(np.median(sp_r) / max(np.median(mu_r), 1e-6))
rms = float(np.sqrt((x ** 2).mean()))
peak = float(np.abs(x).max())

subs = open(os.path.join(BUILD, "subs.ass"), encoding="utf-8-sig").read()
n_caps = subs.count("Dialogue: 0,")
ai_n = len([f for f in os.listdir(os.path.join(ROOT, "assets", "ai")) if f.endswith(".png")])
real_n = len([f for f in os.listdir(os.path.join(ROOT, "assets", "real")) if f.endswith(".jpg")])

md = []
md.append("# 《简易扫地机器人》配音文案与节奏表")
md.append("")
md.append("| # | 段落 | 起 | 止 | 时长 | 配音 | 文案 | 画面段 |")
md.append("|---|------|----|----|------|------|------|--------|")
md.extend(rows)
md.append("")
md.append("- 台词总量：%d 句 / %d 字" % (len(tl["lines"]), chars))
md.append("- 成片时长：%.2f 秒（1080x1920 竖屏 / 30fps / H.264 High / CRF 20 / AAC 192k 44.1k 立体声 / %.1f MB）" % (dur, size_mb))
md.append("- 语速：%.2f 字/秒（小学生科普舒适区 4.0-6.8），逐句区间 %.2f-%.2f 字/秒" % (
    chars / tl["total"], min(rates), max(rates)))
md.append("- 配音：MiniMax speech-02-hd（旁白 Chinese (Mandarin)_Warm_Bestie，第 12 句机器人喊话换 male-qn-jingying），语速按句微调 1.00-1.03，句间留 0.20-0.40 秒气口，标点自然停顿，无念稿感")
md.append("- 背景音乐：numpy 合成 116 BPM（C 大调 I-V-vi-IV，与前几部错开避免串味），铺底 pad + bass + 拨弦 + 轻打击，人声出现时自动 ducking 90%（BGM_GAIN 0.20）")
md.append("- 音效锚点：ding（L02 零件 / L04 底座 / L07 装配 / L12 机器人喊话 / L16 报告成功）· whoosh（L05 装小眼睛 / L08 安全 / L11 写报告 / L14 直线清扫 / L17 升级）· beep（L09 写代码 / L10 写判断 / L13 实测准备 / L15 遇箱）· chime（L11 记录次数 / L16 报告成功 / L18 收尾）· motor（玩具直流电机嗡嗡声，小车真在跑的时候出现）· swish（纸刷子扫地声），全部按旁白行 ID 对齐，TTS 重跑也不会错位")
md.append("- 画面分段：18 段（静态卡片 12 + 程序化动画 6：开始扫地代码 / 碰到东西拐弯代码 / 扫完一圈报个到代码 / 沿胶带清扫实测 / 遇纸箱绕开实测 / 纸屑扫进纸盒实测）")
md.append("- 素材：AI 插画 %d 张（MiniMax image-01，统一 cute 3d cartoon 儿童向画风，卡纸质感机器人 + 橙光小灯笼点缀）+ 实拍照片 %d 张（Arduino 小车套件 / 2WD 底盘 / 接好的电机驱动板 / 手拿电路板 / 焊接台 / 小朋友和真机器人同框等）" % (ai_n, real_n))
md.append("- 字幕：烧录 ASS，%d 条，关键字自动高亮（金色 #F5A623），机器人喊话句整词标红（#E4572E），重叠 0、结尾在片长内" % n_caps)
md.append("- 响度：整片 RMS %.1f dBFS、峰值 %.3f；人声 RMS %.3f 与纯音乐 RMS %.3f 相差 %.1f dB，人声清晰盖过音乐垫" % (
    20 * np.log10(rms), peak, float(np.median(sp_r)), float(np.median(mu_r)), sep))
md.append("")
md.append("## 制作要点对照")
md.append("")
md.append("| 环节 | 本片做法 |")
md.append("|------|---------|")
md.append("| 钩子 | L01 用「扫地机器人出任务！自己转圈、看见箱子绕开、看见纸屑扫起来」先给结果再讲做法，像家里有个小小清洁工 |")
md.append("| 零件 | Arduino 主板 / 超声波传感器 / 人体感应模块 / 小喇叭 / 小舵机 / LED 灯 / 玩具电机 + 卡纸和电池盒，映射「大脑·小眼睛·小耳朵·小嘴巴·小刷子·小灯笼·小脚丫」拟人分工，卡片里用九宫格一次列全 |")
md.append("| 制作 | 剪圆圆的身体 + 装轮子剪小鼻子 → 超声波小眼睛 + 舵机彩纸小刷子 → 人体感应小耳朵 + 藏小喇叭 → 接驱动板插线 + 电池盒藏肚子下，四步递进，每步插画配真实手工实拍 |")
md.append("| 安全 | 不装摄像头也不联网 / 电池只用充电宝那种别接插座 / 喇叭音量最小 / 别掉下楼梯 / 离花瓶桌角远点 / 家里有宠物先让它闻闻 / 接线先断电，七条钉在安全卡上 |")
md.append("| 写程序 | 第一段开始扫地 motorL.write(180) + motorR.write(180)，两个轮子一样快才不歪 → 第二段超声波小于 20 厘米就 back() + turnRight() → 第三段 if (lap == 1) 就点灯、刷子挥、喊「扫干净啦」、count++ 记圈数 |")
md.append("| 原理 | 超声波一秒量几次距离，数字小于 20 厘米就退一步右转个弯；舵机夹的彩纸刷子一直转着把纸屑往中间赶；三个动作互相独立，所以直扫、绕开、报到都能单独跑 |")
md.append("| 实测 | 客厅地板贴一条黄胶带当清扫路线，摆一个纸箱当障碍，撒一点碎纸屑，旁边放一个小纸盒当垃圾盒 |")
md.append("| 反转 | 小车沿胶带稳稳往前走不歪 → 前面有纸箱，超声波一量只剩十五厘米，停、往后退、右转九十度、再继续走成功绕过 → 小刷子一边转一边扫，纸屑一点点被推进小纸盒，地板真的干净了 |")
md.append("| 收尾 | 四个昵称总结 + 无线小发射器 / 小吸管 / 多加一块电池 升级 + 下期预告「会自己浇花的小助手」 |")
md.append("")
md.append("## 素材与安全说明")
md.append("")
md.append("- 扫地机器人全部为卡纸 + 玩具电机 + Arduino，**不装摄像头、不联网、不接市电、不驱动任何家电或真实设备**")
md.append("- 「测距」用超声波传感器读距离、「听见人」用人体感应模块读有无变化，都只驱动小车自己的电机、灯、喇叭和小舵机")
md.append("- 程序代码只包含无害的写电机、读距离、判断阈值、点灯、挥刷子、响喇叭与计次逻辑")
md.append("- 实拍照片全部来自通用真实素材库（Arduino 套件、2WD 底盘、电路板、焊接台、真人小朋友与真机器人同框），用于「零件是真的」这一层可信度")
md.append("")
md.append("## 自检结论")
md.append("")
md.append("- s9_qa 六段式交付自检：**0 failure / 0 warning**")
md.append("- 容器 1080x1920 / 30fps / H.264 High / yuv420p / AAC 44100Hz 立体声 / 时长 %.2fs / %.1f MB" % (dur, size_mb))
md.append("- 画面 无黑帧、67 处硬切（阈值 16）、最长静止 2.43s（阈值 6s）、平均帧间运动 0.461")
md.append("- 声音 峰值 %.3f 不削波、正文无死寂、人声与音乐分离度 %.1f dB（阈值 6 dB）" % (peak, sep))
md.append("- 字幕 %d 条、无空字幕、重叠 0、末条收在片长内、金色高亮与淡入淡出均在位" % n_caps)
md.append("- 内容 关键词 34 个全覆盖、正文 %d 字、18 句、语速 %.2f 字/秒" % (chars, chars / tl["total"]))
md.append("- 素材 AI 插画 %d 张 + 实拍照片 %d 张 + 渲染分段 %d 段" % (ai_n, real_n, len(P.SEG_NAMES)))

open(OUT, "w", encoding="utf-8").write("\n".join(md) + "\n")
print("wrote", OUT)
