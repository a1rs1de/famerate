"""Сборка вертикального ролика 1080x1920@30 по таймингам референса. Звук = ref/ref_audio.wav без изменений.
python build.py            -> out/final.mp4
python build.py preview    -> out/preview_*.png (по одному кадру в сцене)"""
import os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
import textfx

W, H, FPS = 1080, 1920, 30
os.makedirs("out", exist_ok=True)
CYAN, YEL = "#27c7e6", "#ffd92e"
G1_CROP = (459, 178, 986, 740)     # плеер внутри gameplay1 (x,y,w,h)
G2_CROP = (294, 178, 1318, 740)    # плеер внутри gameplay2

def ss(a, b, t): x = min(1, max(0, (t - a) / (b - a))); return x * x * (3 - 2 * x)

# ---------- текст ----------
_cache = {}
def txt(text, kind="caption", size=80, fill="#fff", outline=None, ow=0, glow=None, gs=1.0, mw=980):
    k = (text, kind, size, fill, outline, ow, glow, gs, mw)
    if k not in _cache:
        _cache[k] = textfx.render(text, kind=kind, size=size, fill=fill, outline=outline, outline_w=ow, glow=glow, glow_strength=gs, max_width=mw)
    return _cache[k]

def hcat(parts, gap=30, mw=980):
    parts = [p.crop(p.getbbox()) for p in parts]
    w = sum(p.width for p in parts) + gap * (len(parts) - 1); h = max(p.height for p in parts)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); x = 0
    for p in parts: im.alpha_composite(p, (x, (h - p.height) // 2)); x += p.width + gap
    if im.width > mw: im = im.resize((mw, int(im.height * mw / im.width)), Image.LANCZOS)
    return im

def paste(frame, im, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    x0, y0 = int(cx - im.width / 2), int(cy - im.height / 2)
    xs, ys = max(0, x0), max(0, y0); xe, ye = min(W, x0 + im.width), min(H, y0 + im.height)
    if xe <= xs or ye <= ys: return
    sub = a[ys - y0:ye - y0, xs - x0:xe - x0]; al = sub[..., 3:4] / 255 * alpha
    frame[ys:ye, xs:xe] = (frame[ys:ye, xs:xe] * (1 - al) + sub[..., :3] * al).astype(np.uint8)

def pop(t):  # анимация появления: масштаб 0.82->1 с лёгким перелётом
    p = min(1, t / 0.14); return (0.82 + 0.18 * p + 0.06 * np.sin(p * np.pi)), min(1, t / 0.08)

# ---------- фоны ----------
def bg_red():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * .45) / H) ** 2)
    v = np.clip(1 - r * 1.5, 0, 1)[..., None]
    return (np.array([18, 4, 10]) * (1 - v) + np.array([86, 14, 28]) * v).astype(np.uint8)[..., ::-1].copy()[..., ::-1]
def bg_dark():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * .4) / H) ** 2)
    v = np.clip(1 - r * 1.6, 0, 1)[..., None]
    return (np.array([8, 8, 12]) * (1 - v) + np.array([34, 30, 48]) * v).astype(np.uint8)
BG = {"red": bg_red(), "dark": bg_dark(), "black": np.zeros((H, W, 3), np.uint8)}

def rounded(img, r=34):
    h, w = img.shape[:2]; m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return img, np.asarray(m).astype(np.float32)[..., None] / 255

def card(frame, img, cx, cy, wd, border=None):
    h = int(img.shape[0] * wd / img.shape[1]); im = cv2.resize(img, (wd, h), interpolation=cv2.INTER_AREA)
    im, m = rounded(im); x0, y0 = int(cx - wd / 2), int(cy - h / 2)
    shadow = np.zeros((H, W), np.float32); shadow[max(0, y0):y0 + h, max(0, x0):x0 + wd] = 1
    shadow = cv2.GaussianBlur(shadow, (0, 0), 28)[..., None] * .55
    frame[:] = (frame * (1 - shadow)).astype(np.uint8)
    reg = frame[y0:y0 + h, x0:x0 + wd]; frame[y0:y0 + h, x0:x0 + wd] = (reg * (1 - m) + im * m).astype(np.uint8)
    if border:
        bm = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(bm).rounded_rectangle((x0, y0, x0 + wd, y0 + h), 34, outline=border, width=5)
        paste(frame, bm, W / 2, H / 2)

def cam(src, cx, cy, cw):
    """9:16 окно шириной cw (в пикселях исходника) с центром (cx,cy)."""
    ch = cw * H / W; s = W / cw
    M = np.float32([[s, 0, -(cx - cw / 2) * s], [0, s, -(cy - ch / 2) * s]])
    return cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def crop(src, c): x, y, w, h = c; return src[y:y + h, x:x + w]

def kf(keys, t):  # keys: [(t,cx,cy,cw)] со smoothstep
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if t <= t1: p = ss(t0, t1, t); return [u + (v - u) * p for u, v in zip(a, b)]
    return list(keys[-1][1:])

# ---------- сцены (тайминги из PySceneDetect по референсу) ----------
PROFILE = cv2.cvtColor(cv2.imread("src/profile.jpg"), cv2.COLOR_BGR2RGB)[0:880]
TG = "src/tg_post.png"
def tg_img():
    if os.path.exists(TG): return cv2.cvtColor(cv2.imread(TG), cv2.COLOR_BGR2RGB)
    im = np.zeros((900, 900, 3), np.uint8); im[:] = (28, 24, 44)      # заглушка, пока нет tg_post.png
    for i, (y, w) in enumerate([(120, 600), (190, 760), (250, 700), (330, 780), (400, 500), (500, 720), (570, 640)]):
        cv2.rectangle(im, (70, y), (70 + w, y + 36), (70, 60, 120), -1)
    return cv2.GaussianBlur(im, (0, 0), 9)

SEGS = [
 dict(a=0.00, b=1.367, kind="hook", src="gameplay1", ss=1.0),
 dict(a=1.367, b=2.000, kind="hook", src="gameplay1", ss=1.0 + 1.367),
 dict(a=2.000, b=2.933, kind="hook", src="gameplay1", ss=1.0 + 2.0),
 dict(a=2.933, b=4.433, kind="profile"),
 dict(a=4.433, b=6.600, kind="tg"),
 dict(a=6.600, b=9.167, kind="screen", src="new_b", ss=0.6, text="и переходим уже",
      keys=[(0, 560, 560, 540), (.8, 560, 560, 540), (2.57, 1690, 560, 460)]),
 dict(a=9.167, b=11.233, kind="screen", src="new_a", ss=3.2, text="регистрируйся",
      keys=[(0, 1280, 585, 560), (2.06, 1280, 585, 430)]),
 dict(a=11.233, b=15.800, kind="screen", src="new_c", ss=4.4, text="что модель выбрана",
      keys=[(0, 545, 560, 560), (1.4, 545, 560, 520), (2.6, 1690, 520, 440), (4.57, 1400, 560, 540)]),
 dict(a=15.800, b=19.267, kind="example", src="gameplay2", ss=1.5),
 dict(a=19.267, b=23.267, kind="end"),
]

def overlay_hook(f, i, t):
    s, a = pop(t - 0.0 if i == 0 else t)
    if i == 0:
        paste(f, txt("голос", "headline", 200, "#fff", "#15151c", 10, None, 1, 960), W / 2, 1290, s, a)
        s2, a2 = pop(max(0, t - .35)); paste(f, txt("толисаммера", "headline", 112, CYAN, "#0a2a33", 7, CYAN, 1.3, 980), W / 2, 1500, s2, a2 if t > .35 else 0)
    else:
        paste(f, txt("за", "caption", 96, "#fff", None, 0, "#fff", .4), W / 2, 1560)
        if i == 1: paste(f, txt("20", "headline", 230, YEL, "#4a3500", 8, "#ffb800", 1.4), W / 2, 1330, pop(t)[0], pop(t)[1])
        else:
            paste(f, txt("20 секунд", "headline", 150, YEL, "#4a3500", 8, "#ffb800", 1.4, 980), W / 2, 1340, pop(t)[0], 1)

def overlay_white_boxes(f, lines, cy, t):
    y = cy
    for ln in lines:
        im = txt(ln, "caption", 62, "#111", None, 0, None, 1, 900).copy()
        box = Image.new("RGBA", (im.width + 60, im.height + 36), (0, 0, 0, 0)); ImageDraw.Draw(box).rounded_rectangle((0, 0, box.width - 1, box.height - 1), 20, fill=(255, 255, 255, 255))
        box.alpha_composite(im, (30, 18)); paste(f, box, W / 2, y, *pop(t)[:1], 1); y += box.height + 14

def render(seg, i, local, srcframe):
    t = local
    k = seg["kind"]
    if k == "hook":
        f = BG["red"].copy()
        if srcframe is not None:
            z = 1.0 + .05 * (seg["a"] + t) / 2.9; img = crop(srcframe, G1_CROP); h, w = img.shape[:2]
            cw, ch = int(w / z), int(h / z); img = img[(h - ch) // 2:(h - ch) // 2 + ch, (w - cw) // 2:(w - cw) // 2 + cw]
            card(f, img, W / 2, 720, 960, border=(255, 255, 255, 60))
        overlay_hook(f, i, t); return f
    if k == "profile":
        f = BG["dark"].copy(); z = 1.04 - .04 * ss(0, .25, t)
        card(f, PROFILE, W / 2, 800, int(900 * z), border=(255, 255, 255, 40))
        paste(f, txt("в шапке профиля", "caption", 84, "#fff", None, 0, "#fff", .35), W / 2, 1480, *pop(t)); return f
    if k == "tg":
        f = BG["dark"].copy(); z = 1.04 - .04 * ss(0, .25, t); card(f, tg_img(), W / 2, 780, int(900 * z), border=(255, 255, 255, 40))
        paste(f, txt("телеграм канал", "caption", 84, "#fff", None, 0, "#fff", .35), W / 2, 1480, *pop(t)); return f
    if k == "screen":
        cx, cy, cw = kf(seg["keys"], t); cw *= 1 - .06 * (1 - ss(0, .2, t))
        f = cam(srcframe, cx, cy, cw)
        grad = np.linspace(0, .7, 520)[:, None, None]; f[H - 520:] = (f[H - 520:] * (1 - grad)).astype(np.uint8)
        paste(f, txt(seg["text"], "caption", 84, "#fff", None, 0, "#fff", .45), W / 2, 1640, *pop(t)); return f
    if k == "example":
        f = BG["black"].copy(); img = crop(srcframe, G2_CROP)
        z = 1.0 + .04 * t / 3.4; h, w = img.shape[:2]; cw, ch = int(w / z), int(h / z); img = img[(h - ch) // 2:(h - ch) // 2 + ch, (w - cw) // 2:(w - cw) // 2 + cw]
        card(f, img, W / 2, 900, 1080, None) if False else None
        im = cv2.resize(img, (W, int(img.shape[0] * W / img.shape[1])), interpolation=cv2.INTER_AREA); y0 = 900 - im.shape[0] // 2; f[y0:y0 + im.shape[0]] = im
        overlay_white_boxes(f, ["ТОЛИ САМЕР ВТОРОЙ РАЗ", "ИГРАЕТ В КС"], 470, t)
        paste(f, txt("пример реализации", "caption", 84, "#fff", None, 0, "#fff", .35), W / 2, 1420, *pop(max(0, t - .15))); return f
    if k == "end":
        f = BG["black"].copy(); pill = Image.new("RGBA", (860, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(pill)
        d.rounded_rectangle((0, 0, 859, 119), 60, fill=(255, 255, 255, 255)); d.ellipse((38, 34, 78, 74), outline=(20, 20, 20, 255), width=6); d.line((70, 68, 88, 88), fill=(20, 20, 20, 255), width=6)
        pill.alpha_composite(txt("@motinyo24", "caption", 54, "#111", None, 0, None, 1, 600), (120, 34))
        paste(f, pill, W / 2, 960, *pop(t)); return f

def reader(seg, start=0, count=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{seg['ss'] + start / FPS:.3f}", "-i", f"src/{seg['src']}.mp4", "-vf", f"fps={FPS}"]
    if count: cmd += ["-frames:v", str(count)]
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE); n = 1920 * 1080 * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(1080, 1920, 3)

def seg_frames(seg, i, only=None):
    n = round((seg["b"] - seg["a"]) * FPS); rd = reader(seg) if "src" in seg else None; last = None
    for j in range(n):
        if rd is not None:
            try: last = next(rd)
            except StopIteration: pass
        if only is not None and j != only: continue
        yield render(seg, i, j / FPS, last)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        for i, s in enumerate(SEGS):
            j = min(round((s["b"] - s["a"]) * FPS) - 1, int(.5 * FPS)) if i != 3 else 12
            fr = next(seg_frames(s, i, only=j)); Image.fromarray(fr).resize((540, 960)).save(f"out/preview_{i + 1:02d}.png")
        sys.exit()
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "ref/ref_audio.wav",
        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", "out/final.mp4"], stdin=subprocess.PIPE)
    total = 0
    for i, s in enumerate(SEGS):
        for fr in seg_frames(s, i): ff.stdin.write(fr.tobytes()); total += 1
        print("seg", i + 1, "done", total, flush=True)
    ff.stdin.close(); ff.wait()
