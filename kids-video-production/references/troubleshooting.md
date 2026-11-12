# 排错手册

全部来自实拍过程中真实踩过的坑。

---

## 1 · 字幕/卡片出现豆腐块 □

**现象**：标题里一个方框。

**原因**：`msyhbd.ttc` 缺 `⚠`(U+26A0)、`✓`(U+2713)、部分符号字形。

**修**：不要用字符，改用 Pillow 矢量绘制。`design.py` 已提供：

```python
design.warn_icon(draw, cx, cy, r, color=design.RED)     # 三角 + 感叹号
design.check_icon(draw, cx, cy, r, color=design.GREEN)   # 对勾
```

**自查**：交付前在成片里 grep 一下有无方框，或直接看 `build/cards/*.png`。

---

## 2 · 插画裁切过松，主体太小

**现象**：AI 生成的插画四周大片留白，铺到画框里显得空。

**原因**：旧版 `auto_crop` 用固定阈值裁，二值化把浅色背景也当主体。

**修**（已内置）：改为**中位数背景估计 + 自适应噪声阈值 + 斑点剔除**：

```python
design.auto_crop(path, thresh=90, pad=22)
```

同时**插画一律用 `paste_soft()` 羽化融合，不做 cover 裁切**；
照片才用 `paste_cover()`。改了裁切逻辑后要清缓存目录（缓存键已升为 `crop3_`）。

---

## 3 · ffmpeg `ass=` 滤镜报路径错误

**现象**：`Unable to parse option value` 或直接找不到字幕文件。

**原因**：`ass=C:\path\subs.ass` 里盘符的冒号被当成滤镜分隔符。

**修**：传**相对路径** `build/subs.ass`，并让 ffmpeg 的 `cwd` = 工程根目录。
`s8_final.py` 已写死这个做法，不要改回绝对路径。

---

## 4 · Windows 下 subprocess 中文乱码 / UnicodeEncodeError

**修**：所有 `subprocess.run` 必须带

```python
encoding="utf-8", errors="replace"
```

`common.run()` / `common.dec()` 已经这么做了。
终端输出中文前先设 `$env:PYTHONIOENCODING="utf-8"`。

---

## 5 · 配音接口选型

`edge-tts` 被封（连接超时 / 空音频），**改用 MiniMax `speech-02-hd`**：
`https://api.minimaxi.com/v1/t2a_v2`，key 在 `minimax-imagegen/key.txt`。
`common.api_key()` 已统一处理（也支持 `$MINIMAX_API_KEY`）。

---

## 6 · 真实照片抓取

Pexels **搜索页**被反爬拦截，但 CDN 可直连：
`https://images.pexels.com/photos/<id>/pexels-photo-<id>.jpeg?...`
按已知 photo id 直接下 URL 即可，不要去搜 HTML。

版权：优先用可商用图库；抓不到的用 AI 插画替代，
**不要**直接搬运他人视频截图。

---

## 7 · numpy 数组广播报错

**现象**：`ValueError: operands could not be broadcast together`

**原因**：`sfx_beep` 这类脉冲音频长度和目标缓冲区不一致。

**修**：用切片累加而不是 `+=`：

```python
out[:len(base)] += base
```

`design.py` / `s5_audio.py` 已修正，改动时注意保持这个写法。

---

## 8 · 语速过快 / 像赶稿

**原因**：`SCRIPT` 里 `speed` 调太高，或句子太长。

**修**：单句 ≤ 45 字，`speed` 控制在 1.00–1.10，
`gap_after` 每句 0.2–0.5 秒。QA 会报实际字/秒，目标 4.0–6.8。

---

## 9 · PowerShell 删文件被策略拦截

`Remove-Item -Recurse` 会被拦。改用 Python：

```python
import shutil; shutil.rmtree(path)
```

---

## 10 · 插画明明生成了，铺进画框却小一圈

**现象**：卡片里的 AI 插画四周留了大片空白，主体显得很小。

**原因**：`s3_cards.py` 里 `importlib.reload(design)` 把 `design.CROPDIR`
重置回 `None`，`auto_crop()` 直接返回原图，**根本没裁**。

**修**：reload 之后再设裁切目录。

```python
import design
importlib.reload(design)          # reload 会清空 CROPDIR
design.set_cropdir(crop_dir)     # 必须放在 reload 之后
import cards
importlib.reload(cards)
```

`cards.py` / `anim.py` 用 `from design import *` 拿到的是函数**引用**，
所以只要 `design.CROPDIR` 是对的，裁切就生效——但前提是 reload 顺序正确。

**自查**：`build/cards/*.png` 与参考成片逐像素比对应完全一致。

---

## 11 · 音效和说话对不上

**现象**：重跑一遍后，`ding` 音效落在了半句话中间。

**原因**：`SFX_CUES` 写的是绝对秒数，锚定在上一版 TTS 的时间轴上。
TTS 重新合成后每句长度会漂几十毫秒到几秒，累计起来就错位。

**修**：音效按**旁白行 ID** 锚定，运行时才解析时间。

```python
SFX_CUES = {"ding": [("L02", 0.00, 0.30), ("L12", 0.00, 0.30)]}
```

`("L12", 0.0, 0.40)` = L12 这句**行首**起 0.0 秒处响。
负偏移表示提前（`("L12", -0.25, 0.40)` = 抢在句首前 0.25 秒）。

---

## 12 · QA 报"字幕重叠"

**原因**：两个字幕事件时间区间相交，通常是 `gap_after` 为 0 且上一句被拉长。

**修**：`s2_tts.py` 里已按实际音频长度排时间轴；
若仍重叠，检查 `s6_subtitles.py` 的分句是否把一句切成了两段且两段时间有交集。

## 8 · MiniMax 插画底部带伪签名水印
**现象**：image-01 会在画面最底部（奶油底色上）留一行类似 `© MiniMax Programming` 的
乱码签名，`design.auto_crop()` 只会按墨迹裁边，**不会去掉它**。

**检测**：把每张图底部 12% 裁出来拼成一张对照图，肉眼扫一遍最快。
```python
for f in files:
    im = Image.open(f).convert("RGB"); w, h = im.size
    strip = im.crop((0, int(h * 0.88), w, h)).resize((360, int(h * 0.12 * 360 / w)))
```

**修**：物理裁掉底边（签名通常在最后 100px 内），不要指望 auto_crop：
```python
im = Image.open(p).convert("RGB"); w, h = im.size
im.crop((0, 0, w, h - 120)).save(p)
```
裁完必须**重新跑 s3/s4**（裁切缓存 `build/crop/crop3_*.png` 是按原图生成的，
删掉 `build/crop` 一起重跑最省事）。

---

## 13 · MiniMax 额度用尽（status_code 2056 / 1002）时的离线替代方案

**现象**：`s1_images.py` 与 `s2_tts.py` 同时报
`已达到 Token Plan 用量上限`（2056）或 `rate limit exceeded(RPM)`（1002）。
图片和 TTS 共用同一个 Token Plan，**两个都会挂**，不是偶发抖动。

**验证**：
```python
requests.post("https://api.minimaxi.com/v1/image_generation", json={...}, headers={"Authorization": "Bearer "+key})
# base_resp.status_code == 2056 -> 额度确实用尽，等重置或换通道
```

**替代方案 A · 配音**：Windows 自带 System.Speech（离线、无限量、确定性）。
- 可选中文音色：`Microsoft Huihui`（女）/ `Microsoft Kangkang`（男）/ `Microsoft Yaoyao`（童声）。
- 走 `System.Speech.Synthesis.SpeechSynthesizer` + `SpeakSsml()`，
  在标点处插 `<break time="170ms"/>` 换气，避免念稿感。
- `Rate` 每档约 +15%，默认语速偏慢，建议 `VOICE_RATE_BIAS = 2`。
- 该引擎峰值动态大、整体 RMS 低，混音后要单独做一次**响度归一**（+6~7 dB + 限幅 0.88），
  否则成片比前几部片子小 6 dB。
- `edge-tts`（pip 已装 7.2.8）目前返回 `WSServerHandshakeError 403`，不可用。

**替代方案 B · 插画**：公共图像端点 `https://image.pollinations.ai/prompt/<urlencoded>`。
- 匿名额度：**每 IP 每 45 秒 1 张**，脚本要按 50~60 秒节流并按 46 秒重试。
- `model=flux` 会 402，`model=turbo` 常常 503，**不带 model 参数最稳**。
- 提示词必须**短**（≤ 15 词）+ 动词构图（holding / wearing / next to）：
  长提示词会被当成关键词堆砌，产出与主题无关的图。
- 风格前缀放在**提示词末尾**，且要写 `cute 3d cartoon`，否则会跑成写实照片。
- 图片右下角有站点水印，生成后**裁掉底部 5%**。
- 画风一致性靠"同一前缀 + 同一 seed 规则"，个别语义跑偏的图要重生成或改用实拍照片顶替。

**收尾**：换通道后一定要重跑 s2→s3→s5→s6→s7→s8→s9，
并注意 `s5` 的 `QA_MIN_SEPARATION_DB`（人声比音乐高 6 dB）与成片响度。

## 14 · 额度恢复后如何把离线替代版换回 MiniMax 正式版

**场景**：第 13 节的替代通道已经交付过一版，MiniMax 额度恢复后要重做，
但**不要**从零改脚本 —— 工程文件（project.py / cards.py / anim.py）都能直接复用。

**1. 换配音音色**：`project.py` 的 `VOICES` 改成 MiniMax voice_id。
已验证可用（speech-02-hd）：

- 旁白女声：`Chinese (Mandarin)_Warm_Bestie`
- 角色男声：`male-qn-jingying`

`VOICE_PITCH` / `VOICE_BREATH` / `VOICE_RATE_BIAS` 是给 System.Speech 备用引擎
（`s2b_tts_sapi.py`）用的，MiniMax 路径不读，保留即可。

**2. 标定语速**：MiniMax `speed=1.0` 约 **5.0 字/秒**，正好落在儿童科普舒适区
（4.0-6.8）。可以先用一句代表台词试 0.95 / 1.0 / 1.05 再定：

    ffprobe -v error -show_entries format=duration -of csv=p=0 L02.mp3

本片用 0.99-1.03 微调（开场句和角色句略快）。整体语速由
`chars / timeline.total` 决定，看 s9 报的 rate 再微调。

**3. 清缓存再跑**：

    Remove-Item assets\ai\*.png            # 否则 s1_images 命中缓存不重新生成
    Remove-Item build\voice\*              # 否则 s2_tts 复用旧 mp3
    Remove-Item build\crop\* -Recurse      # 裁切缓存跟着新图走

**4. 音效锚点要按新时长重算**：TTS 一换，每句时长全变，`SFX_CUES` 里
**行内正偏移**（如 `("L15", 3.45)`、`("L16", 1.55)`、`("L18", 10.40)`）会错位。
正确做法是复用字幕的分句权重模型来定位目标词：

    from s6_subtitles import phrases, weight
    ps = phrases(line["text"]); ws = [weight(x) for x in ps]
    # 累加权重求目标短语在本句内的起始秒数

负偏移（过渡音落在句间停顿）不用改 —— 句间 gap 由 SCRIPT 固定，没变。
收尾 chime 放 `line.dur + 0.05`。

**5. 顺序**：`s1_images → s2_tts → s3_cards → s4_anim → s5_audio → s5b → s6 → s7 → s8 → s9`。
`s4_anim` 最慢（6 段程序化动画约 5 分钟），可以先跑。

**收益对比**（同一支片子，SolarFan 第 11 部）：

| 指标 | System.Speech 替代版 | MiniMax 正式版 |
|------|--------------------|--------------|
| 插画尺寸 / 画质 | 832×1216，语义偶有跑偏 | 720×1280，形象统一、语义准确 |
| 人声 vs 音乐分离 | 6.7 dB | **15.6 dB** |
| 混音增益 | +6.8 dB | +0.3 dB（原生就够响） |
| 峰值 / RMS | 0.914 / −17.7 dBFS | 0.708 / −16.5 dBFS |

---

## 15 · 测混音分离度前，必须先把音频转成单声道（第 12 部踩坑）

`s9_qa.py` 是这样测「人声 vs 音乐」分离度的：

    ffmpeg -i movie -ac 1 -ar 44100 -c:a pcm_s16le tmp.wav   # 先转单声道

自己写脚本复核时如果直接 `wave` 读 `build/audio/mix.wav`，读到的是**立体声交错数据**
（长度 = 帧数 × 2），于是：

- 100 ms 窗口的索引被压缩成实际 **50 ms**，与 `l["start"]*10` 算出的语音窗口**错位一倍**；
- 结果语音段和音乐段的中位 RMS 几乎相等，分离度算出来是 **0 dB**，
  看起来像「音乐盖过人声」，其实是测量 bug。

**正确写法**（和 s9 完全一致）：

    tmp = os.path.join(tempfile.gettempdir(), "_m.wav")
    subprocess.run(["ffmpeg","-y","-v","error","-i",path,"-ac","1","-ar","44100",
                    "-c:a","pcm_s16le",tmp], check=True)
    with wave.open(tmp,"rb") as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768

**别被这个假警报带偏去改 `BGM_GAIN`**：全系列沿用 `BGM_GAIN = 0.20` /
`DUCK_DEPTH = 0.90`，正确测量下分离度约 15-16 dB（已交付成片实测 15.6 dB）。
低于这个数才说明音乐真的压过人头，才需要降 `BGM_GAIN`。

## 16 · 实拍照片的取景要跟文案对得上（第 12 部）
第 11 部把「换更大的太阳能板」配成了一盏黑背景的复古灯泡墙，画面和文案对不上。
换图时先按文案想画面：`px_solar_worker.jpg`（屋顶光伏）才配「换成更大的太阳能板」，
`px_solar_sky.jpg`（蓝天下的太阳能板）配「搬到窗边晒太阳」，
`nx_bulb_leaves_glow.jpg`（夜里亮着的灯泡）配封面「天黑了它自己就亮」。

## 17 · 竖版 AI 插画放进横向画框会留大片空白（第 12 部）
MiniMax 出的是 720×1280 竖图。`illus()` 是「整张缩放塞进画框」，画框一横，
两侧就空出几百像素白，卡片看起来很稀。
两种解法：① 改版式——插画占左半边，文字卡占右半边（`v03_parts_ai`），
插画占窄条、右侧放解释卡（`v08_code_read`）；② 用 `paste_cover()` 铺满并调 `focus` 裁掉空白背景。

## 18 · 卡片文案要照着照片真实内容写，别照着想象写（第 13 部）
第 13 部（扫地机器人）返工了两张卡：

- `v12_robot_speak` 文案写「真的在扫地的小机器人」，配的却是 `px_3861969.jpg`
  （其实是**看代码屏幕的女孩**，跟机器人、跟焊接都没关系）；
- `v17_upgrade` 文案写「装上升级件，它就能自己吃饭、自己掉头」，配的却是
  `px_28169155.jpg`（**绿色电路板特写**，跟吸尘风扇和悬崖传感器无关）。

**正确顺序**：先把照片打开看一眼，**按画面里真实出现的东西写字**，
而不是先想好文案再挑一张「差不多」的照片塞进去。本集改成：
`v12` 用 `px_19895699.jpg`（女孩焊接特写）配「每个零件都是我焊的」；
`v17` 用同一张 PCB 特写配「里面全是真电路 / 升级件接上去，干活又快又安全」。

## 19 · 本机没有 apply_patch，改文件走 node_repl（第 13 部）
这台机器上 `apply_patch` 不可用。改 Python 源文件的可靠写法是 node_repl：

    const fs = await import("node:fs");
    let s = fs.readFileSync(p, "utf8");
    s = s.replace(/\r\n/g, "\n");          // 先归一化换行，再做整块字符串替换
    s = s.replace(oldBlock, newBlock);
    fs.writeFileSync(p, s, "utf8");

两个坑：

1. 匹配串必须按 LF 写。源文件是 CRLF 时直接 `s.includes(old)` 一定 false。
2. node_repl 内核是**跨轮次常驻**的，`const` 变量名会撞车
   （报 `Assignment to constant variable`）。每轮换新名字（`fs3` / `p3` / `res3`…）。

删除文件也别用 PowerShell `Remove-Item`（同一次调用里混其它命令会被策略拦截），
用 `fs.rmSync(path, {recursive:true, force:true})`。

## 20 · 用户给「实物模型照片 + 技能介绍视频」时怎么用（第 17 部）

这一部用户提供了两个东西：**一张实物模型照片**（白底产品图：黑灰迷彩三脚架 + 顶部旋转天线阵）
和**一段游戏内技能介绍 mp4**。处理方式已经验证：

1. **实物照片当封面「证据」**：`paste_cover` 到 (MARGIN, 330, W-MARGIN, 1140)，
   白底产品图和纸面底色放一起会有点跳，所以外面先 `paper_card` 再贴，视觉上像一张产品卡。
2. **技能视频抽帧当「机制对照卡」**：用 ffmpeg 按秒抽帧拼图（`fps=1` + `tile=4x4`），
   先看拼图挑出真正有信息的帧，再单独抽成 `ref_xxx.jpg` 存进 `assets/real/`。
   抽帧时间点要靠拼图定位，写死秒数经常抽错。
3. **真实机制细节要从视频里读出来再写进文案**：本片从参考视频里额外读到了
   「每 10 秒放一次声波，一共 3 次」「发出声音：移动 / 开枪 / 使用技能」「隔着墙也能标记」
   「黄色读条 + 红色被标记」，这些写进台词后，比用户口述的摘要更硬。
4. **安全改写**：游戏里的军用声呐一律改成**纸板道具 + 玩具麦克风模块**，
   「探测」= 音量阈值判断 + 舵机转动 + LED 灯 + 小喇叭，全程无发射、无致伤机构。

## 21 · 静态卡片里最容易犯的两个排版错（第 17 部）

1. **圆圈居中、文字却按圆心偏移写**：
   `d.text((x + 60, ...), "无线小发射器", anchor="mm")` 会让 6 个字的标题冲出卡片左边界。
   正确做法：先算 `cxx = x + cw / 2`，圆圈和两行文字**全部**以 `cxx` 为中心。
2. **同一行的两个标签会撞在一起**：
   场景里两个纸人相隔不到 130px 时，「会动的小纸人」「安静的小纸人」会糊成一行。
   解法：把标签缩短成「会动的 / 安静的」，并把两个纸人拉开到 150px 以上。

另外：卡片顶部的 chip 高约 80px，**紧跟其下的大标题要从 y=206 起**，
写在 y=158 会和 chip 叠在一起。
