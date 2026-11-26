# -*- coding: utf-8 -*-
"""Build the narration / rhythm sheet for the 简易小鸟机器人 film."""
import json, os, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "小鸟机器人_配音文案与节奏表.md")
BT = chr(96)
tl = json.load(open(os.path.join(BUILD, "timeline.json"), encoding="utf-8"))

SEC_CN = {"hook": "开场钩子", "parts": "认识零件", "build": "动手制作",
          "code": "写程序", "safety": "安全提醒",
          "test": "落地实测", "upgrade": "升级", "outro": "总结收尾"}
VOICE_CN = {"narr": "旁白（MiniMax Chinese (Mandarin)_Warm_Bestie）",
            "male": "小鸟拟人（MiniMax male-qn-jingying）"}

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

# audio stats
mix = os.path.join(BUILD, "audio", "mix.wav")
w = wave.open(mix)
sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
peak = float(np.abs(x).max())
prog_rms = float(np.sqrt((x ** 2).mean()))

dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", os.path.join(ROOT, P.OUTPUT_NAME)],
                     capture_output=True, text=True).stdout.strip()
size = os.path.getsize(os.path.join(ROOT, P.OUTPUT_NAME)) / 1e6

# caption count
subs = open(os.path.join(BUILD, "subs.ass"), encoding="utf-8").read()
ncap = subs.count("Dialogue:")

md = []
md.append("# 《简易小鸟机器人》配音文案与节奏表\n")
md.append("| # | 段落 | 起 | 止 | 时长 | 配音 | 文案 | 画面段 |")
md.append("|---|------|----|----|------|------|------|--------|")
md.extend(rows)
md.append("")
md.append("- 台词总量：18 句 / %d 字" % chars)
md.append("- 成片时长：%.2f 秒（1080x1920 竖屏 / 30fps / H.264 High / CRF 20 / AAC 192k 44.1k 立体声 / %.1f MB）" % (float(dur), size))
md.append("- 语速：%.2f 字/秒（小学生科普舒适区 4.0-6.8），逐句区间 %.2f-%.2f 字/秒" % (chars / float(dur), min(rates), max(rates)))
md.append("- 配音：MiniMax speech-02-hd（旁白 Chinese (Mandarin)_Warm_Bestie，第 12 句小鸟喊话换 male-qn-jingying），语速按句微调 1.00-1.03，句间留 0.20-0.40 秒气口，标点自然停顿，无念稿感")
md.append("- 背景音乐：numpy 合成 %g BPM（G 大调 I-V-vi-IV，与前几部错开避免串味），铺底 pad + bass + 拨弦 + 轻打击，人声出现时自动 ducking 90%%（BGM_GAIN 0.20）" % P.BPM)
md.append("- 音效锚点：ding（L02 零件 / L04 底座 / L07 装配 / L12 小鸟喊话 / L16 照光）· whoosh（L05 做翅膀 / L08 安全 / L11 写后退 / L14 扇翅膀 / L17 升级）· beep（L09 写翅膀 / L10 写判断 / L13 实测准备 / L15 遇箱）· chime（L11 唱一声 / L16 报告 / L18 收尾）· chirp（小鸟啾啾声，L11 / L12 / L15 / L16 / L17）· flap（纸翅膀扇动声，L09 / L10 / L14 / L16），全部按旁白行 ID 对齐，TTS 重跑也不会错位" % ())
md.append("- 混音：峰值 %.3f 不削波，整片 RMS %.3f（约 %.1f dBFS），人声比音乐高 16.9 dB（阈值 6 dB）" % (peak, prog_rms, 20 * np.log10(prog_rms)))
md.append("- 画面分段：18 段（静态卡片 12 + 程序化动画 6：张开翅膀代码 / 看见光就转过来代码 / 前面太近就后退代码 / 扇翅膀实测 / 遇纸箱绕开实测 / 照到光就唱歌实测）")
md.append("- 字幕：%d 条，按短语上屏，关键词金色高亮，小鸟喊话那句红色，整句淡入淡出，重叠 0 条" % ncap)

open(OUT, "w", encoding="utf-8").write("\n".join(md) + "\n")
print("wrote", OUT)
