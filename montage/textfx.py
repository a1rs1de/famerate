"""Рендер текста в стиле референса: контур + deep glow. Возвращает RGBA PNG."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

FONTS = {
    "headline": ("fonts/Unbounded.ttf", 900),   # «ГОЛОС», «20 СЕКУНД»
    "caption":  ("fonts/Montserrat.ttf", 800),  # субтитры внизу
}

def font(kind, size):
    path, wght = FONTS[kind]
    f = ImageFont.truetype(path, size)
    f.set_variation_by_axes([wght])
    return f

def render(text, kind="caption", size=64, fill="#ffffff", outline=None, outline_w=0,
           glow=None, glow_strength=1.0, tracking=-0.02, pad=160, max_width=None):
    """glow: цвет свечения или None. Свечение = сумма гауссовых размытий разной силы (deep glow)."""
    if max_width:  # автоподгонка под ширину кадра
        probe = font(kind, size)
        tw = sum(probe.getlength(c) + tracking * size for c in text)
        if tw > max_width: size = int(size * max_width / tw)
    f = font(kind, size)
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
