# 视觉风格指南

参考成片：《智能小车_制作到实测.mp4》（D:\codex\Codex++）。
整体感觉：**暖白纸面上的儿童科学绘本**，不是冷冰冰的产品广告。

---

## 配色

| 名称 | HEX | 用途 |
| --- | --- | --- |
| CREAM | `#F8F2E4` | 卡片底色（纸面） |
| CREAM_DEEP | `#F0E7D2` | 底色渐深、阴影区 |
| PAPER_EDGE | `#E2D6BE` | 纸边、卡片描边 |
| INK | `#2B2B2B` | 正文、主标题 |
| INK_SOFT | `#6C7078` | 次要说明文字 |
| BLUE | `#2F80ED` | 主控板、代码、主要强调 |
| ORANGE | `#F5A623` | 关键词高亮、暖点缀 |
| GREEN | `#36A269` | 正确、勾号、通过状态 |
| RED | `#E4572E` | 警告、机器人台词、错误 |
| CODE_BG | `#1E202E` | 代码块底 |
| WHITE | `#FFFFFF` | 卡片主体填充 |

配色比例：纸底占 70%+，墨色文字 15%，彩色强调 ≤15%。
**一页里彩色强调不超过 3 处**，否则会吵。

---

## 字体

只用系统字体，不下载：

| 用途 | 文件 |
| --- | --- |
| 标题 / 强调 | `C:\Windows\Fonts\msyhbd.ttc`（微软雅黑 Bold） |
| 正文 | `C:\Windows\Fonts\msyh.ttc`（微软雅黑） |
| 代码 | `C:\Windows\Fonts\consolab.ttf`（Consolas Bold） |

> **坑**：`msyhbd.ttc` 没有 `⚠`(U+26A0) 和 `✓`(U+2713) 字形，
> 直接写会渲染成豆腐块 □。用 `design.warn_icon()` / `design.check_icon()`
> 用 Pillow 画矢量三角/对勾，不要用字符。

字号阶梯：主标题 76 → 小标题 54 → 正文 40 → 注释 30。
标题字一律带白色描边 + 深墨外描边（`text_outline`），保证在任何插画上都读得清。

---

## 版式规范（1080x1920）

```
y=0      ┌──────────────────────┐
         │  主标题区 (150-320)   │  白字 + 墨色描边，居中或左对齐
         │                      │
y=350    │  插画 / 实拍照片区     │  圆角 32-40，羽化融入纸底
         │                      │
y=1300   │  小结 / 要点文字区     │  卡片 chip、勾选清单
         │                      │
y=1520   ├──────────────────────┤ ← 正文绝对下界
y=1555   │   字幕带 (1555-1635)  │  白色 + 描边
y=1660   │  留白 / 装饰          │
y=1920   └──────────────────────┘
```

- 左右安全边距 `MARGIN = 64`。
- **正文不得越过 y=1520**，字幕带 1555–1635，两者不打架。
- 照片用 `paste_cover()`（填满画框，会裁边）；插画用 `paste_soft()`
  （羽化融入纸底，不裁主体）——**插画不要用 cover，会切掉小车**。

---

## 插画提示词写法

统一风格前缀（`project.py` 的 `IMAGE_STYLE`），后面每条 prompt 只写内容：

```
children's science book illustration, soft gouache texture, warm cream
background, thick friendly outlines, cute rounded shapes, cheerful and
bright, high detail, no text
```

单张 prompt 要素：**主体 + 动作 + 环境 + 视角**。

- 好：`close up of a cartoon boy's hands using a screwdriver to bolt a
  silver electric motor with a yellow wheel onto a small robot chassis`
- 差：`robot car`（太笼统，多张会撞图）

关键：同一批图里**角色描述要一致**（例如始终是 "cartoon boy"），
否则 AI 会画出不同的小孩，成片看着像几个人。

数量建议 8–10 张，覆盖：封面 / 零件全景 / 3–4 个制作步骤 /
写代码 / 实测 / 升级 / 吉祥物。

---

## 卡片文案写法

- 每张卡片一个**明确的动作或结论**，不是抽象名词。
- 关键词用 `【】` 标记，字幕会自动高亮成金色，视觉上要能对上。
- 数字要具体：`【30 厘米】`、`【20】` 比 "适当的距离" 好。
- 代码卡片每行不超过 4 个 token，字体 40，可用 `draw_code()` 做关键字着色。

---

## 字幕样式

- 字体：Microsoft YaHei，48–56。
- 白字 + 黑描边，位置 `Alignment=2`（底部居中），MarginV 调到 285–300。
- 关键词 `\c&H0023A6F5&`（ASS 是 **BGR**，金色），机器人台词 `\c&H002E57E4&`（红）。
- 逐短语上屏，一屏 ≤ 18 字，加 `fad(120,120)`。

---

## 声音风格

- 人声：`speech-02-hd`，解说用 `Chinese (Mandarin)_Warm_Bestie`。
- BGM：numpy 合成，C 大调 I–V–vi–IV，BPM 100，pad + bass + pluck + 轻 perc。
- 人声出现时音乐下压 86%（`DUCK_DEPTH = 0.86`）。
- 音效：`ding`（转折点）、`whoosh`（换场景）、`beep`（按钮）、`chime`（结尾）。
