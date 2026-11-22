# 儿童科普短视频生产线 · kids-video-production

一条**竖屏儿童科普制作视频**的完整可复现流水线：脚本与节奏设计 → AI 插画 + 真实照片素材 →
配音（TTS）→ 卡片版式 → 动画段 → 程序化背景音乐与音效 → 烧录字幕 → 成片输出 → 六段式交付自检。

> 复刻自已验证的「活泼不僵硬」儿童科普风格。一条片 = **一个真实问题 + 一边做一边讲 + 落地实测**。

---

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `SKILL.md` | 流水线规格：九个步骤的输入输出契约、配置字段表、交付要求 |
| `scripts/` | 九步流水线脚本（`s1`…`s9`）+ `common.py` / `design.py` 共用层 |
| `references/style-guide.md` | 配色、字体、卡片版式、插画提示词写法 |
| `references/troubleshooting.md` | 已踩过的坑（缺字豆腐块、裁切过松、ffmpeg 盘符冒号、排版溢出…） |
| `references/pipeline-reference.md` | 九步的输入输出契约与产物路径 |
| `project/` | 新片模板：`project.py` / `cards.py` / `anim.py` + 通用实拍素材池 |
| `episodes/` | 已交付片目的工程文件与配音节奏表 |

---

## 快速开始

```bash
# 1. 建一个新片工程
python scripts/init_project.py <新工程目录> --force

# 2. 只改工程目录里的 project.py（文案 / 镜头 / 插画提示词 / 音乐 / QA 阈值），
#    cards.py 与 anim.py 按新选题改版式与动画，流水线脚本一行不用动。

# 3. 依次跑九步（每步都 --project 指向新工程目录）
python scripts/s1_images.py    --project <工程目录>   # AI 插画（MiniMax image-01）
python scripts/s2_tts.py       --project <工程目录>   # 配音 + timeline.json
python scripts/s3_cards.py     --project <工程目录>   # 静态卡片
python scripts/s4_anim.py      --project <工程目录>   # 程序化动画段
python scripts/s5_audio.py     --project <工程目录>   # BGM + 音效 + 混音
python scripts/s6_subtitles.py --project <工程目录>   # ASS 字幕
python scripts/s7_assemble.py  --project <工程目录>   # 拼接分段
python scripts/s8_final.py     --project <工程目录>   # 烧字幕 + 混音输出成片
python scripts/s9_qa.py        --project <工程目录>   # 六段式交付自检（不绿不许交付）
```

## 环境要求

- Python 3.9+，依赖 `pillow`、`numpy`、`requests`
- `ffmpeg` / `ffprobe` 在 PATH 上（含 `libx264`、`zoompan`、`subtitles` 滤镜）
- 一个 MiniMax API key：环境变量 `MINIMAX_API_KEY`，或
  `~/.codex/skills/minimax-imagegen/key.txt`，或 `~/.codex/auth.json` 里的 `OPENAI_API_KEY`
  （`scripts/common.py` 的 `api_keys()` 会按顺序回退）
- 中文字体：`C:\Windows\Fonts` 下的微软雅黑；其它系统可设 `KVP_FONT_DIR` 指向含
  `NotoSansCJK-*.ttc` 的目录（`scripts/design.py` 会自动回退，不会崩）
- **目标平台是 Windows**（路径、ffmpeg 盘符冒号、微软雅黑都按 Windows 调过）

## 核心配置项（全在 `project.py`）

| 字段 | 含义 |
| --- | --- |
| `OUTPUT_NAME` | 成片文件名（落在工程根目录） |
| `VOICES` / `VOICE_PITCH` / `VOICE_BREATH` | 配音音色；拟人角色单独一个音色，字幕整句标红 |
| `SCRIPT` | 逐句文案 `(id, section, voice, speed, gap_after, text)`，`【】` 里的词自动染金色 |
| `SEG_NAMES` | 视觉分段名，**数量必须等于 `SCRIPT` 条数** |
| `ANIM_SEGS` | 哪些段用动画，其余走静态卡片 |
| `AI_FILE` / `SHOTS` / `IMAGE_STYLE` | AI 插画文件名、提示词、统一画风前缀 |
| `REAL_FILE` | 每张卡片用哪张实拍照片 |
| `BPM` / `CHORDS` / `MELODY` | 程序化 BGM |
| `SFX_CUES` | 音效锚点，**按旁白行 ID 对齐**（TTS 重跑也不会错位） |
| `SFX_EXTRA` | 额外的自定义音效（相对工程根目录的 wav）；第 18 部的「啪」由 `make_pop_sfx.py` 生成到 `build/sfx/pop.wav` |
| `BGM_GAIN` / `DUCK_DEPTH` | 人声优先的 ducking 混音 |
| `QA_*` | 自检阈值（时长、字数、语速、素材数、关键词） |

## 六段式交付自检（`s9_qa.py`）

| 段 | 检查 |
| --- | --- |
| 容器 | 分辨率 / 帧率 / 编码 / 像素格式 / 音频采样率声道 / 时长 / 文件体积 |
| 画面 | 无黑帧、硬切数量达标、无超过 6 秒的静止镜头 |
| 声音 | 峰值不削波、峰值健康、正文无死寂、人声比音乐高出 ≥6 dB |
| 字幕 | 事件数达标、无空字幕、未超出片长、金色高亮存在、重叠数 = 0 |
| 内容 | 关键词覆盖、正文字数、旁白条数、语速 4.0–6.8 字/秒 |
| 素材 | 插画数量、真实照片数量、分段数量 |

**`s9_qa.py` 全绿才允许交付。** 机器只查下限，交付前还必须人耳过一遍：
配音有没有错读吞字、背景音乐有没有盖住人声、转折处有没有音效提示、字幕有没有豆腐块。

## 已交付片目

| # | 选题 | 状态 |
| --- | --- | --- |
| 17 | 三角洲行动 · 干员「回响」X 技能「回声探测器」→ 现实可用的纸板声纳探测装置 | 已交付，`episodes/17-回响声纳探测器/` |
| 18 | 三角洲行动 · 干员「牧羊人」V 技能「声波陷阱」→ 现实可用的纸板声波小圆饼 | 已交付，`episodes/18-牧羊人声波陷阱/` |
| 19 | Arduino + 卡纸 → 会自己巡逻、看见箱子绕开、看见人挥手的简易巡逻机器人 | 已交付，`episodes/19-巡逻机器人/` |

每片的具体脚本、卡片版式、动画段与配音节奏表都在 `episodes/` 下。

## 安全底线

游戏里的武器 / 军用装备一律**降维成纸板 + 玩具传感器道具**：
不装真实机构、不发射、不致伤；程序只写无害逻辑（读数值 → 判断阈值 → 转个舵机 → 点个灯 → 响个喇叭）。

**任何「伤害 / 爆炸 / 耳鸣 / 击晕」类机制，都要改写成儿童向无害表达**（第 18 部示例）：
伤害 → 纸机器人愣住 2 秒；减速 → 走路变慢；耳鸣 → 捂住耳朵嗡嗡响；
屏幕扭曲 → 画面抖一抖；打断动作 → 手里卡片掉地上。
成品卡片必须带安全提醒段：不装爆炸物 / 音量最小不贴耳朵 / 旁边有人先喊一声 /
别放楼梯口马路边 / 别吓到宠物 / 接线前先断电。
