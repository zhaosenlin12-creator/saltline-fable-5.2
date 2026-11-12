# -*- coding: utf-8 -*-
"""design.py - shared visual language for the 智能小车 video (1080x1920).

Palette + layout rules mirror the reference video:
  cream paper ground, warm crayon illustrations, real photos,
  bold outlined headings, golden keyword highlights, blue annotations.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FPS = 30

CREAM      = (248, 242, 228)
CREAM_DEEP = (240, 231, 210)
PAPER_EDGE = (226, 214, 190)
INK        = (43, 43, 43)
INK_SOFT   = (108, 112, 120)
BLUE       = (47, 128, 237)
ORANGE     = (245, 166, 35)
GREEN      = (54, 162, 105)
RED        = (228, 87, 46)
WHITE      = (255, 255, 255)
CODE_BG    = (30, 32, 46)
CODE_PANEL = (24, 26, 38)

MARGIN = 64
SUB_TOP = 1300          # subtitle band starts here
SUB_H = 200

def _font_dir():
    """First readable font directory, so the pipeline runs off Windows too."""
    for c in (os.environ.get("KVP_FONT_DIR", ""),
              r"C:\Windows\Fonts",
              "/usr/share/fonts/truetype/dejavu",
              "/usr/share/fonts/opentype/noto",
              "/System/Library/Fonts"):
        if c and os.path.isdir(c):
            return c
    return ""


FONTS = _font_dir()
_cache = {}


def font(size, bold=True, mono=False):
    """Pick the best available face; fall back instead of crashing."""
    key = (size, bold, mono)
    if key in _cache:
        return _cache[key]
    if mono:
        names = ["consolab.ttf" if bold else "consola.ttf",
                 "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf",
                 "menlo.ttc"]
    else:
        names = ["msyhbd.ttc" if bold else "msyh.ttc",
                 "NotoSansCJK-Bold.ttc" if bold else "NotoSansCJK-Regular.ttc",
                 "simhei.ttf", "PingFang.ttc",
                 "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    f = None
    for n in names:
        p = os.path.join(FONTS, n)
        if os.path.exists(p):
            try:
                f = ImageFont.truetype(p, size)
                break
            except Exception:
                pass
    if f is None:
        f = ImageFont.load_default()
    _cache[key] = f
    return f


def paper(w=W, h=H, seed=7):
    """Cream paper ground with soft mottling, like the reference's illustration paper."""
    base = Image.new("RGB", (w, h), CREAM)
    rnd = random.Random(seed)
    layer = Image.new("L", (w // 6, h // 6), 128)
    d = ImageDraw.Draw(layer)
    for _ in range(2200):
        x, y = rnd.randrange(layer.width), rnd.randrange(layer.height)
        r = rnd.choice([2, 3, 4, 6, 9])
        v = rnd.randint(112, 144)
        d.ellipse([x - r, y - r, x + r, y + r], fill=v)
    layer = layer.filter(ImageFilter.GaussianBlur(5)).resize((w, h), Image.LANCZOS)
    tex = Image.merge("RGB", (layer, layer, layer))
    return Image.blend(base, tex, 0.10)


def rounded(img, box, radius, fill=None, outline=None, width=0):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def shadowed(img, box, radius, blur=22, alpha=48, offset=(0, 8), fill=(255, 255, 255)):
    x0, y0, x1, y1 = box
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle(
        [x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]],
        radius=radius, fill=fill + (alpha,))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(lay)


def text_outline(draw, xy, s, fnt, fill=WHITE, outline=INK, width=0, anchor="la", spacing=8, align="left"):
    draw.text(xy, s, font=fnt, fill=fill, anchor=anchor, spacing=spacing, align=align,
              stroke_width=width, stroke_fill=outline)


def text_w(draw, s, fnt):
    return draw.textbbox((0, 0), s, font=fnt)[2] - draw.textbbox((0, 0), s, font=fnt)[0]


def paste_cover(img, path, box, radius=0, focus=(0.5, 0.5), grade=True):
    """Crop-fill a photo into box (keeps aspect, crops overflow)."""
    x0, y0, x1, y1 = [int(v) for v in box]
    tw, th = x1 - x0, y1 - y0
    im = Image.open(path).convert("RGB")
    sw, sh = im.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    left = int((nw - tw) * focus[0]); top = int((nh - th) * focus[1])
    im = im.crop((left, top, left + tw, top + th))
    if grade:
        im = warm_grade(im)
    if radius:
        mask = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw - 1, th - 1], radius=radius, fill=255)
        img.paste(im, (x0, y0), mask)
    else:
        img.paste(im, (x0, y0))
    return img


def paste_contain(img, path, box, radius=0):
    """Fit whole image inside box, centred, transparent-free cream background."""
    x0, y0, x1, y1 = [int(v) for v in box]
    tw, th = x1 - x0, y1 - y0
    im = Image.open(path).convert("RGB")
    sw, sh = im.size
    scale = min(tw / sw, th / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    if radius:
        mask = Image.new("L", (nw, nh), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, nw - 1, nh - 1], radius=radius, fill=255)
        img.paste(im, (x0 + (tw - nw) // 2, y0 + (th - nh) // 2), mask)
    else:
        img.paste(im, (x0 + (tw - nw) // 2, y0 + (th - nh) // 2))
    return img


def warm_grade(im, strength=0.16):
    """Slight warm / lifted-shadow grade so photos match the crayon palette."""
    import numpy as np
    a = np.asarray(im).astype(np.float32) / 255.0
    a = a ** 0.94
    a[..., 0] = a[..., 0] * (1 + 0.05 * strength) + 0.012 * strength
    a[..., 1] = a[..., 1] * (1 + 0.01 * strength)
    a[..., 2] = a[..., 2] * (1 - 0.05 * strength) - 0.004 * strength
    a = np.clip(a, 0, 1)
    return Image.fromarray((a * 255).astype("uint8"))


def sparkle(d, x, y, r, color=ORANGE, alpha=255):
    d.polygon([(x, y - r), (x + r * 0.30, y - r * 0.30), (x + r, y), (x + r * 0.30, y + r * 0.30),
               (x, y + r), (x - r * 0.30, y + r * 0.30), (x - r, y), (x - r * 0.30, y - r * 0.30)],
              fill=color + (alpha,))


def sparkle_field(d, seed=3, n=26, box=None, colors=(ORANGE, BLUE, GREEN, RED)):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box or (0, 0, W, H)
    for _ in range(n):
        x = rnd.randint(x0, x1); y = rnd.randint(y0, y1)
        c = rnd.choice(colors)
        sparkle(d, x, y, rnd.randint(9, 22), c, rnd.randint(150, 235))


def warn_icon(d, cx, cy, r, color=RED, width=0):
    """Vector warning triangle - the U+26A0 glyph is missing from msyh, so draw it."""
    pts = [(cx, cy - r), (cx + r * 0.92, cy + r * 0.72), (cx - r * 0.92, cy + r * 0.72)]
    d.polygon(pts, fill=color, outline=color, width=width)
    d.line([(cx, cy - r * 0.42), (cx, cy + r * 0.16)], fill=WHITE, width=max(4, int(r * 0.16)))
    d.ellipse([cx - r * 0.10, cy + r * 0.36, cx + r * 0.10, cy + r * 0.56], fill=WHITE)


def check_icon(d, cx, cy, r, color=GREEN, width=0):
    """Vector check mark - U+2713 is missing from msyh, so draw it."""
    lw = max(6, int(r * 0.32))
    d.line([(cx - r * 0.60, cy + r * 0.02), (cx - r * 0.16, cy + r * 0.46)],
           fill=color, width=lw, joint="curve")
    d.line([(cx - r * 0.16, cy + r * 0.46), (cx + r * 0.64, cy - r * 0.48)],
           fill=color, width=lw, joint="curve")


def chip(img, x, y, s, bg=ORANGE, fg=INK, size=40, padx=26, pady=14, radius=None, outline=None):
    f = font(size, True)
    d = ImageDraw.Draw(img)
    w = text_w(d, s, f)
    h = size + pady * 2
    r = radius if radius is not None else h // 2
    box = [x, y, x + w + padx * 2, y + h]
    rounded(img, box, r, fill=bg, outline=outline, width=3 if outline else 0)
    d.text((x + padx, y + h / 2), s, font=f, fill=fg, anchor="lm")
    return box[2] - box[0]


def title_block(img, lines, x=MARGIN, y=150, size=76, fill=WHITE, outline=INK, ow=7,
                accent=ORANGE, gap=14, line_gap=1.22):
    """Big bold heading with dark outline + accent bar, like the reference title card."""
    d = ImageDraw.Draw(img)
    f = font(size, True)
    cy = y
    for i, s in enumerate(lines):
        text_outline(d, (x, cy), s, f, fill=fill, outline=outline, width=ow)
        cy += size * line_gap + gap
    d.rectangle([x, cy - gap * 0.4, x + 96, cy - gap * 0.4 + 12], fill=accent)
    return cy + 40


def subtitle_keyword(text):
    """Split 【kw】 markup into [(chunk, is_keyword)]."""
    out, buf, i = [], "", 0
    while i < len(text):
        if text[i] == "【":
            j = text.find("】", i)
            if j > 0:
                if buf:
                    out.append((buf, False)); buf = ""
                out.append((text[i + 1:j], True))
                i = j + 1
                continue
        buf += text[i]; i += 1
    if buf:
        out.append((buf, False))
    return out


KW = {"int", "void", "long", "if", "else", "return", "const", "for", "while", "bool", "float"}
FN = {"setup", "loop", "pinMode", "begin", "measure", "backward", "turnRight", "forward", "delay"}


def draw_code(d, x, y, text):
    """Monospace ASCII (Consolas) + YaHei for CJK, token-coloured."""
    f_code = font(34, False, mono=True)
    f_cn = font(34, False)
    c_num = (240, 178, 96)
    c_kw = (232, 132, 214)
    c_str = (152, 208, 122)
    c_cmt = (118, 126, 158)
    c_fn = (112, 190, 255)
    c_ty = (98, 200, 208)
    c_txt = (222, 226, 238)
    c_pun = (150, 156, 176)
    cw = d.textlength("M", font=f_code)

    def run(s, col):
        nonlocal x
        if not s:
            return
        j = 0
        while j < len(s):
            if ord(s[j]) > 0x2E00:
                k = j
                while k < len(s) and ord(s[k]) > 0x2E00:
                    k += 1
                d.text((x, y), s[j:k], font=f_cn, fill=col, anchor="lm")
                x += d.textlength(s[j:k], font=f_cn)
                j = k
            else:
                k = j
                while k < len(s) and ord(s[k]) <= 0x2E00:
                    k += 1
                d.text((x, y), s[j:k], font=f_code, fill=col, anchor="lm")
                x += cw * (k - j)
                j = k

    if text.startswith("#"):
        run(text, c_cmt)
        return
    ci = text.find("//")
    if ci >= 0:
        run(text[:ci], c_txt)
        run(text[ci:], c_cmt)
        return

    i = 0
    buf = ""

    def flush(col=c_txt):
        nonlocal buf
        if buf:
            run(buf, col)
            buf = ""

    while i < len(text):
        ch = text[i]
        if ch == '"':
            flush()
            j = text.find('"', i + 1)
            j = j if j > 0 else len(text) - 1
            run(text[i:j + 1], c_str)
            i = j + 1
            continue
        if ch.isdigit():
            flush()
            j = i
            while j < len(text) and (text[j].isdigit() or text[j] == "."):
                j += 1
            run(text[i:j], c_num)
            i = j
            continue
        if ch.isalpha() or ch == "_":
            flush()
            j = i
            while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                j += 1
            word = text[i:j]
            col = c_kw if word in KW else (c_ty if word in ("Ultrasonic", "Serial")
                                           else (c_fn if word in FN else c_txt))
            run(word, col)
            i = j
            continue
        if ord(ch) > 0x2E00:
            flush()
            run(ch, c_txt)
            i += 1
            continue
        buf += ch
        i += 1
    flush()


def paste_soft(img, path, box, feather=64, shadow=True):
    """Fit an illustration whole (no crop) and feather its edges into the paper.

    Matches the reference, where crayon illustrations simply float on cream.
    """
    x0, y0, x1, y1 = [int(v) for v in box]
    tw, th = x1 - x0, y1 - y0
    im = Image.open(auto_crop(path)).convert("RGB")
    sw, sh = im.size
    scale = min(tw / sw, th / sh)
    nw, nh = max(1, int(sw * scale + 0.5)), max(1, int(sh * scale + 0.5))
    im = im.resize((nw, nh), Image.LANCZOS)
    mask = Image.new("L", (nw, nh), 255)
    ImageDraw.Draw(mask).rectangle([0, 0, nw - 1, nh - 1], outline=0, width=feather)
    mask = mask.filter(ImageFilter.GaussianBlur(feather * 0.5))
    px = x0 + (tw - nw) // 2
    py = y0 + (th - nh) // 2
    if shadow:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        lay.paste((120, 96, 60, 34), (px, py + 14), mask)
        lay = lay.filter(ImageFilter.GaussianBlur(26))
        img.alpha_composite(lay)
    img.paste(im, (px, py), mask)
    return img


CROPDIR = None


def set_cropdir(path):
    global CROPDIR
    CROPDIR = path
    os.makedirs(path, exist_ok=True)


def auto_crop(path, thresh=90, pad=22):
    """Trim the flat cream margin around a crayon illustration.

    The background is estimated from the median of the border ring (paper
    gradients defeat a single corner sample), and the ink threshold adapts to
    the measured noise floor so faint pencil strokes are kept.
    """
    import numpy as np
    if not CROPDIR:
        return path
    key = os.path.join(CROPDIR, "crop3_" + os.path.splitext(os.path.basename(path))[0] + ".png")
    if os.path.exists(key):
        return key
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    h, w, _ = a.shape
    ring = np.concatenate([
        a[:4].reshape(-1, 3), a[-4:].reshape(-1, 3),
        a[:, :4].reshape(-1, 3), a[:, -4:].reshape(-1, 3)])
    bg = np.median(ring, axis=0)
    diff = np.abs(a - bg).sum(axis=2)
    noise = np.percentile(np.abs(ring - bg).sum(axis=1), 99) + 8
    mask = diff > max(thresh, noise)
    # drop stray specks: a row/column only counts when it holds real ink
    thr = max(3, int(0.004 * w))
    ys = np.where(mask.sum(axis=1) > thr)[0]
    xs = np.where(mask.sum(axis=0) > thr)[0]
    if len(xs) == 0 or len(ys) == 0:
        return path
    box = (max(0, int(xs.min()) - pad), max(0, int(ys.min()) - pad),
           min(w, int(xs.max()) + pad), min(h, int(ys.max()) + pad))
    im.crop(box).save(key)
    return key
