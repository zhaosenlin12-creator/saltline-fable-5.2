# Saltline — Fable 5.2 FPS

A small browser first-person shooter: one level in a rainy container port. Cut three uplink relays while drones ("Gulls") and robot dogs ("Hounds") hunt you.
<img width="1685" height="906" alt="image" src="https://github.com/user-attachments/assets/8dd32149-90f4-4d69-a573-4411a49a9ba9" />


## Demo
https://realcodebear.github.io/saltline-fable-5.2/

## Where it comes from

- Built by **Claude Fable 5.2**. The run was set up by Felix Rieseberg (Anthropic) and shared on X on 2026-11-09:
  https://x.com/felixrieseberg/status/2119925633564463609
- Original playable artifact: https://claude.ai/artifact/BGY1SztrAYcJQHSsnHHGmp
- Per his post: one prompt, no human feedback, about 8 hours, about 2.7M output and 445M input tokens (heavily cached), about $550 at API pricing. Models, sounds and textures are all made in code. These numbers are his own and not checked here.

All credit for the game goes to its original author. This repo is a mirror so people can run it locally. If you are the author and want it taken down, open an issue.

## What changed from the artifact

Nothing in the game code. The claude.ai frame-runtime scripts were removed from `<head>`, and a doctype, charset and viewport tag were added so the file runs as a plain web page.

## Run it

```sh
python3 -m http.server 8731
```

Then open http://localhost:8731 and click the page to capture the mouse and start the sound.

The whole game is one file, `index.html` (~1.4 MB). It bundles three.js and loads fonts from Google Fonts. There are no other outside assets.

---

## 附：儿童科普短视频生产线（`kids-video-production/`）

这个仓库除了游戏本体，还收录了一条**竖屏儿童科普制作视频**的完整可复现流水线：
脚本与节奏设计 → AI 插画 + 真实照片素材 → 配音（TTS）→ 卡片版式 → 动画段 →
程序化背景音乐与音效 → 烧录字幕 → 成片输出 → 六段式交付自检。

| 目录 | 内容 |
| --- | --- |
| `kids-video-production/SKILL.md` | 流水线规格（九步的输入输出契约、配置字段表、交付要求） |
| `kids-video-production/scripts/` | `s1`…`s9` 九步脚本 + `common.py` / `design.py` |
| `kids-video-production/references/` | 视觉风格指南、踩坑记录、流水线契约 |
| `kids-video-production/project/` | 新片模板 + 通用实拍素材池 |
| `kids-video-production/episodes/` | 已交付片目的工程文件与配音节奏表 |

第 17 部样片：《三角洲行动》干员「回响」X 技能「回声探测器」→ 现实可用的纸板声纳探测装置
（182.53 秒 / 1080×1920 / 交付自检 0 失败 0 警告 / 语速 4.98 字每秒 / 人声音乐分离度 17.5 dB）。

用法见 `kids-video-production/README.md`。
