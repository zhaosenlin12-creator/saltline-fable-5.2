# 流水线参考

九步的输入输出契约。全部脚本接受 `--project <目录>`，
也可设 `$VIDEO_PROJECT`，或从当前目录向上找 `project.py`。

定位优先级：`--project` > `$VIDEO_PROJECT` > 向上查找 `project.py` > skill 内置模板。

---

## s1_images.py — AI 插画

- 读 `project.py` 的 `SHOTS` / `IMAGE_STYLE` / `IMAGE_ASPECT` / `IMAGE_MODEL`
- 输出：`assets/ai/*.png`
- 缓存：文件 > 20KB 跳过；4 线程并发；失败重试 4 次（3 + 3 + 3 秒退避）

## s2_tts.py — 配音与时间轴

- 读 `SCRIPT` / `VOICES`
- 输出：`build/audio/voice.wav`（每句一条 + 拼接）、`build/timeline.json`
- `timeline.json` 结构：`{"total": 秒, "lines": [{"id","start","dur","text",...}]}`
- 处理：去首尾静音（按能量）、归一化到 -1 dBFS、按 `gap_after` 排时钟

## s3_cards.py — 静态卡片

- 调 `cards.py` 的 `build_cards() -> dict[name: PIL.Image]`
- 输出：`build/cards/*.png`（1080x1920）
- `design.set_cropdir(build/crop)` 提供插画裁切缓存

## s4_anim.py — 动画段

- 调 `anim.py` 的 `build_anims(segdur) -> dict[name: path]`
- `segdur` 来自 `timeline.json`，段长与配音严格对齐
- 输出：`build/anim/*.mp4`

## s5_audio.py — 音乐音效混音

- 读 `BPM` / `CHORDS` / `MELODY` / `SFX_CUES` / `BGM_GAIN` / `DUCK_DEPTH`
- `SFX_CUES` 的锚点格式是 `(line_id, offset_seconds, amplitude)`，
  运行时才从 `timeline.json` 解析出行首时间（也兼容旧的 `(seconds, amp)`）
- 输出：`build/audio/bgm.wav`、`sfx.wav`、`mix.wav`
- 合成链：pad + bass + pluck + perc → 叠音效 → 人声 ducking 混音

## s6_subtitles.py — 字幕

- 读 `build/timeline.json`
- 输出：`build/subs.ass`
- 逐短语上屏；`【】` 关键词金色；机器人段红色；`fad()` 淡入淡出

## s7_assemble.py — 拼接

- 读 `SEG_NAMES` / `ANIM_SEGS`，卡片走 `zoompan` Ken Burns（6 种运动轮换）
- 输出：`build/seg/*.mp4`、`build/concat.txt`、`build/video_nosub.mp4`
- 同时记录每句的 A/V 偏差供字幕对齐

## s8_final.py — 成片

- concat → 烧 ASS → 混音 → H.264 High CRF20 / AAC 192k 44.1k 立体声 / faststart
- 输出：工程根目录 `OUTPUT_NAME`

## s9_qa.py — 自检

- 六段式：容器 / 画面 / 声音 / 字幕 / 内容 / 素材
- 失败 `exit 1`；阈值全部来自 `project.py` 的 `QA_*`

---

## 产物路径速查

```
<工程>/
  OUTPUT_NAME            成片
  assets/ai/             AI 插画
  assets/real/           真实照片
  build/
    timeline.json        配音时间轴（时间基准）
    cards/               静态卡片 PNG
    anim/                动画段 MP4
    seg/                 分段 MP4
    crop/                插画裁切缓存
    subs.ass             字幕
    concat.txt           拼接清单
    video_nosub.mp4      未烧字幕中间片
    audio/               voice / bgm / sfx / mix
```

---

## 常用命令

```bash
# 新建工程
python <skill>/scripts/init_project.py <工程目录>

# 全流程
for s in s1_images s2_tts s3_cards s4_anim s5_audio s6_subtitles s7_assemble s8_final s9_qa; do
  python <skill>/scripts/$s.py --project <工程目录> || break
done

# 只改字幕/音频后重出片（跳过 s1-s4）
python <skill>/scripts/s6_subtitles.py --project <工程目录>
python <skill>/scripts/s7_assemble.py --project <工程目录>
python <skill>/scripts/s8_final.py  --project <工程目录>
python <skill>/scripts/s9_qa.py      --project <工程目录>
```

改 `SCRIPT` 文案后必须从 **s2** 重跑（时间轴变了）。
只改 `cards.py` 版式：从 **s3** 重跑。
只改音乐：从 **s5** 重跑。
