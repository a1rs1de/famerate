"""Рендер текста в стиле референса: контур + deep glow. Возвращает RGBA PNG."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

import os, glob

# Шрифт референса — Druk Wide Bold (платный). Если положить файл в fonts/ (имя содержит "Druk" и "Wide"),
# он подхватится автоматически для всех текстов; иначе — запасные бесплатные шрифты.
def _druks():
    out = []
    for p in sorted(glob.glob("fonts/*")):
        n = os.path.basename(p).lower()
        if "druk" in n and "wide" in n and n.endswith((".ttf", ".otf")) and "bold" in n:
            out.append(p)
    return out

DRUK = _druks()
FALLBACK = {"headline": ("fonts/Unbounded.ttf", 900), "caption": ("fonts/Montserrat.ttf", 800)}

def _covers(path, text):
    from fontTools.ttLib import TTFont
    cmap = TTFont(path).getBestCmap()
    return all(ord(c) in cmap for c in text if not c.isspace())

def pick(kind, text):
    """Druk Wide, если он содержит все символы текста (в текущем файле нет кириллицы), иначе запасной."""
    for p in DRUK:
        if _covers(p, text):
            return p, None
    return FALLBACK[kind]

def font(kind, size, text=""):
    path, wght = pick(kind, text)
    f = ImageFont.truetype(path, size)
    if wght:
        f.set_variation_by_axes([wght])
    return f

def render(text, kind="caption", size=64, fill="#ffffff", outline=None, outline_w=0,
           glow=None, glow_strength=1.0, tracking=-0.02, pad=None, max_width=None):
    """glow: цвет свечения или None. Свечение = сумма гауссовых размытий разной силы (deep glow)."""
    if max_width:  # автоподгонка под ширину кадра
        probe = font(kind, size, text)
        tw = sum(probe.getlength(c) + tracking * size for c in text)
        if tw > max_width: size = int(size * max_width / tw)
    f = font(kind, size, text)
    if pad is None: pad = int(size * 1.8) if glow else 20
    # ручной трекинг
    adv = [f.getlength(c) + tracking * size for c in text]
    w = int(sum(adv)); h = int(size * 1.4)
    W, H = w + pad * 2, h + pad * 2
    mask = Image.new("L", (W, H), 0); d = ImageDraw.Draw(mask)
    x = pad
    for c, a in zip(text, adv):
        d.text((x, pad), c, font=f, fill=255); x += a
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if glow:
        layers = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for r, k in ((size * .9, .55), (size * .45, .75), (size * .2, .9), (size * .08, 1.0)):
            g = mask.filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * k * glow_strength)))
            col = Image.new("RGBA", (W, H), glow); col.putalpha(g)
            layers = Image.alpha_composite(layers, col)
        out = Image.alpha_composite(out, layers)
    if outline and outline_w:
        st = mask.filter(ImageFilter.MaxFilter(outline_w * 2 + 1))
        o = Image.new("RGBA", (W, H), outline); o.putalpha(st); out = Image.alpha_composite(out, o)
    t = Image.new("RGBA", (W, H), fill); t.putalpha(mask)
    out = Image.alpha_composite(out, t)
    return out.crop(out.getbbox() or (0, 0, W, H)) if glow is None else out
