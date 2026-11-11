"""Step 2: graphics + punch-ins + SFX on top of build/cut.mov -> output reel.

Styles: H1 headline, C2 captions, B1 step tracker, B3 tick list, B6 big turn word,
E1 save card + end card, M1 punch-in cuts, S1 light ticks (generated SFX).
Layout keeps every element inside the 1080x1920 TikTok/Reels safe zone
(x 60-960, y 210-1500) and out of the face zone.
"""
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
BUILD = os.path.join(HERE, "build")
OUT_DIR = os.path.join(ROOT, "output")
os.makedirs(OUT_DIR, exist_ok=True)
W, H, FPS = 1080, 1920, 30
PREVIEW = "--preview" in sys.argv  # write a few stills only

# ---------- brand ----------
MINT = (188, 228, 181)        # Colour.png  #BCE4B5
GREEN = (85, 190, 56)         # logo top    #55BE38
TEAL = (74, 150, 180)         # logo bottom #4A96B4
DEEP = (28, 84, 52)           # dark green text
YELLOW = (255, 214, 10)
WHITE = (255, 255, 255)
PAPER = (255, 251, 240)

INTER = "/usr/share/fonts/opentype/inter/"
def font(name, size):
    path = os.path.join(HERE, "fonts", name) if name.endswith(".ttf") else INTER + name
    return ImageFont.truetype(path, size)

# ---------- timeline ----------
TL = json.load(open(os.path.join(BUILD, "timeline.json")))
SEG = [s["out_start"] for s in TL["segments"]] + [TL["duration"]]
DUR = TL["duration"]
WORDS = json.load(open(os.path.join(BUILD, "words.json")))
def wt(i, key="s"):
    return WORDS[i][key]

SYMPTOMS = [  # (asset, label, tracker label, side the finger points to)
    ("sym_belly.png", "BELLY FAT", "Belly fat", "L"),
    ("sym_skintags.png", "SKIN TAGS", "Skin tags", "R"),
    ("sym_darkneck.png", "DARK NECK", "Dark neck", "L"),
    ("sym_sugar.png", "SUGAR CRAVINGS", "Cravings", "R"),
    ("sym_fatigue.png", "SLEEPY AFTER MEALS", "Sleepy", "L"),
]
INTRO_END = SEG[5]            # end of the five "insulin resistance"
S2_END = SEG[7]               # end of "...insulin resistant."

# M1 punch-in zoom per segment (alternating masks the jump cuts)
ZOOMS = [1.00, 1.06, 1.00, 1.06, 1.00, 1.08, 1.00, 1.06, 1.00, 1.04]
ANCHOR = (620, 900)           # around the face so it stays in place

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def window(t, a, b, fin=0.18, fout=0.12):
    """alpha for an element visible on [a,b] with fades"""
    if t < a or t > b: return 0.0
    return min(ease_out((t - a) / fin), clamp((b - t) / fout))

# ---------- drawing helpers ----------
def rounded(size, r, fill):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=fill)
    return im

def shadowed(im, blur=14, offset=(0, 8), alpha=110):
    pad = blur * 3
    out = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, alpha))
    sh.putalpha(Image.eval(im.getchannel("A"), lambda a: a * alpha // 255))
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out, pad

def text_img(txt, fnt, fill, stroke=0, stroke_fill=(0, 0, 0), shadow=True):
    l, t, r, b = fnt.getbbox(txt, stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 2 - t), txt, font=fnt, fill=fill,
                            stroke_width=stroke, stroke_fill=stroke_fill)
    if shadow:
        im, _ = shadowed(im, blur=6, offset=(0, 4), alpha=150)
    return im

def fit_font(txt, name, size, max_w, stroke=0):
    while size > 20:
        f = font(name, size)
        l, _, r, _ = f.getbbox(txt, stroke_width=stroke)
        if r - l <= max_w: return f
        size -= 2
    return font(name, size)

def gradient(size, c1, c2):
    w, h = size
    g = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(c1)[None, None] * (1 - g) + np.array(c2)[None, None] * g)
    arr = np.repeat(arr, w, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")

def paste(base, im, xy, alpha=1.0, scale=1.0, anchor="tl"):
    if alpha <= 0.003: return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    x, y = xy
    if anchor == "c": x, y = x - im.width // 2, y - im.height // 2
    elif anchor == "tc": x = x - im.width // 2
    elif anchor == "bc": x, y = x - im.width // 2, y - im.height
    base.alpha_composite(im, (int(x), int(y)))

# ---------- static assets ----------
def make_logo(size=104):
    lg = Image.open(os.path.join(ROOT, "Logo.png")).convert("RGB")
    leaf = lg.crop((560, 440, 1450, 1560))           # leaf mark on mint
    leaf.thumbnail((size - 22, size - 22), Image.LANCZOS)
    tile = rounded((size, size), 24, MINT + (255,))
    tile.alpha_composite(leaf.convert("RGBA"), ((size - leaf.width) // 2, (size - leaf.height) // 2))
    border = rounded((size + 6, size + 6), 27, WHITE + (255,))
    border.alpha_composite(tile, (3, 3))
    return shadowed(border, blur=8, offset=(0, 4), alpha=90)[0]

def make_symptom_card(i):
    asset, label, _, _ = SYMPTOMS[i]
    photo = Image.open(os.path.join(HERE, "assets", asset)).convert("RGB")
    pw = 336
    photo = photo.resize((pw, int(photo.height * pw / photo.width)), Image.LANCZOS)
    cw, pad = pw + 20, 10
    f = fit_font(label, "InterDisplay-ExtraBold.otf", 30, cw - 96)
    lab_h = 54
    card = rounded((cw, lab_h + photo.height + pad * 2), 22, WHITE + (255,))
    d = ImageDraw.Draw(card)
    # label strip
    strip = rounded((cw - pad * 2, lab_h - 6), 14, MINT + (255,))
    card.alpha_composite(strip, (pad, pad))
    d.text((cw // 2 + 24, pad + (lab_h - 6) // 2), label, font=f, fill=DEEP, anchor="mm")
    # number badge (brand gradient)
    badge = gradient((40, 40), GREEN, TEAL)
    m = Image.new("L", (40, 40), 0); ImageDraw.Draw(m).ellipse([0, 0, 39, 39], fill=255)
    badge.putalpha(m)
    ImageDraw.Draw(badge).text((20, 20), str(i + 1), font=font("InterDisplay-Black.otf", 24),
                               fill=WHITE, anchor="mm")
    card.alpha_composite(badge, (pad + 7, pad + 4))
    # photo with rounded corners
    pm = Image.new("L", photo.size, 0)
    ImageDraw.Draw(pm).rounded_rectangle([0, 0, photo.width - 1, photo.height - 1], 14, fill=255)
    ph = photo.convert("RGBA"); ph.putalpha(pm)
    card.alpha_composite(ph, (pad, lab_h + pad - 2))
    return shadowed(card)

def make_tracker_pill(label, state, w=138, h=50):
    if state == "done":
        pill = gradient((w, h), GREEN, TEAL); fg = WHITE
    elif state == "now":
        pill = Image.new("RGBA", (w, h), YELLOW + (255,)); fg = DEEP
    else:
        pill = Image.new("RGBA", (w, h), (255, 255, 255, 170)); fg = (60, 90, 70)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=255)
    pill.putalpha(m)
    f = fit_font(label, "InterDisplay-Bold.otf", 24, w - 16)
    ImageDraw.Draw(pill).text((w // 2, h // 2), label, font=f, fill=fg, anchor="mm")
    return pill

def make_tick_card(n_ticked, flash=None):
    cw, row = 330, 62
    head = 66
    card = rounded((cw, head + row * 5 + 16), 24, (255, 255, 255, 240))
    d = ImageDraw.Draw(card)
    strip = gradient((cw, head), GREEN, TEAL)
    m = Image.new("L", (cw, head), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, head + 30], 24, fill=255)
    strip.putalpha(m)
    card.alpha_composite(strip, (0, 0))
    d.text((cw // 2, head // 2), "2 or more?", font=font("InterDisplay-ExtraBold.otf", 32),
           fill=WHITE, anchor="mm")
    f = font("InterDisplay-Bold.otf", 27)
    for i, (_, label, _, _) in enumerate(SYMPTOMS):
        y = head + 10 + i * row
        cx, cy = 34, y + row // 2
        on = i < n_ticked
        d.ellipse([cx - 17, cy - 17, cx + 17, cy + 17], fill=(GREEN if on else (255, 255, 255)),
                  outline=(GREEN if on else (170, 190, 175)), width=3)
        if on:
            d.line([(cx - 8, cy + 1), (cx - 2, cy + 8), (cx + 9, cy - 7)], fill=WHITE, width=5, joint="curve")
        d.text((64, cy), label.title(), font=f, fill=(DEEP if on else (90, 110, 95)), anchor="lm")
    return shadowed(card)[0]

def make_paper_card(lines, size=(560, 250), with_logo=False):
    """E1 paper card: off-white paper, mint tape, handwritten + clean lines."""
    w, h = size
    card = Image.new("RGBA", (w, h), PAPER + (255,))
    rng = np.random.default_rng(7)
    grain = (rng.normal(0, 5, (h, w))).clip(-12, 12)
    arr = np.asarray(card).astype(int)
    arr[..., :3] = (arr[..., :3] + grain[..., None]).clip(0, 255)
    card = Image.fromarray(arr.astype(np.uint8), "RGBA")
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 10, fill=255)
    card.putalpha(m)
    d = ImageDraw.Draw(card)
    for y in range(78, h - 20, 44):  # faint ruled lines
        d.line([(28, y), (w - 28, y)], fill=(200, 225, 205, 255), width=2)
    x0 = 30
    if with_logo:
        lg = make_logo(84); card.alpha_composite(lg, (16, (h - lg.height) // 2)); x0 = 128
    y = 30 if not with_logo else (h - sum(l[2] + 10 for l in lines)) // 2
    for txt, fnt, lh, col in lines:
        d.text((x0 + (w - x0 - 24) // 2, y + lh // 2), txt, font=fnt, fill=col, anchor="mm")
        y += lh + 10
    # tape
    tape = Image.new("RGBA", (150, 40), MINT + (215,))
    tape = tape.rotate(-6, expand=True, resample=Image.BICUBIC)
    big = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    big.alpha_composite(card, (20, 20))
    big.alpha_composite(tape, ((w + 40 - tape.width) // 2, 2))
    big = big.rotate(-2.0, expand=True, resample=Image.BICUBIC)
    return shadowed(big, blur=12, offset=(0, 10), alpha=100)[0]

def make_headline():
    """H1: full headline on the chest from frame one, key word yellow."""
    small = text_img("5 SIGNS OF", font("InterDisplay-ExtraBold.otf", 56), WHITE, 5)
    big_f = fit_font("INSULIN RESISTANCE", "InterDisplay-Black.otf", 92, 860, 7)
    big = text_img("INSULIN RESISTANCE", big_f, YELLOW, 7)
    im = Image.new("RGBA", (max(small.width, big.width), small.height + big.height - 34), (0, 0, 0, 0))
    im.alpha_composite(small, ((im.width - small.width) // 2, 0))
    im.alpha_composite(big, ((im.width - big.width) // 2, small.height - 34))
    return im

def make_c2(small_txt, big_txt, big_col):
    """C2: small white line + one big bold word under it."""
    s = text_img(small_txt, fit_font(small_txt, "InterDisplay-Bold.otf", 46, 860, 4), WHITE, 4)
    b = text_img(big_txt, fit_font(big_txt, "InterDisplay-Black.otf", 104, 860, 7), big_col, 7)
    im = Image.new("RGBA", (max(s.width, b.width), s.height + b.height - 30), (0, 0, 0, 0))
    im.alpha_composite(s, ((im.width - s.width) // 2, 0))
    im.alpha_composite(b, ((im.width - b.width) // 2, s.height - 30))
    return im

LOGO = make_logo()
CARDS = [make_symptom_card(i) for i in range(5)]
HEADLINE = make_headline()
TURN = text_img("2+", font("InterDisplay-Black.otf", 210), YELLOW, 9)
TICKS = [make_tick_card(n) for n in range(6)]
CAV = font("Caveat-Bold.ttf", 64)
SAVE_CARD = make_paper_card([
    ("Save this for later!", CAV, 70, DEEP),
    ("Read the caption ↓", font("InterDisplay-Bold.otf", 36), 44, (40, 40, 40)),
], size=(560, 200))
END_CARD = make_paper_card([
    ("Follow for more", CAV, 62, DEEP),
    ("simple health tips", CAV, 62, DEEP),
], size=(600, 210), with_logo=True)

# C2 caption chunks (start, end, small line, big word, big colour)
CAPS = [
    (SEG[5], wt(18, "e") + 0.1, "If you have more than two of these", "SYMPTOMS", WHITE),
    (SEG[6], S2_END, "then you can be", "INSULIN RESISTANT", YELLOW),
    (SEG[7], wt(32, "e") + 0.08, "If you want to know more", "ABOUT THIS", WHITE),
    (SEG[8], wt(36, "s") + 0.1, "read my", "CAPTION", YELLOW),
    (wt(36, "s") + 0.1, DUR, "and kindly follow me for more", "SCIENCE-BACKED OPTIONS", YELLOW),
]
CAP_IMGS = [make_c2(s, b, c) for (_, _, s, b, c) in CAPS]

TICK_T0 = wt(17, "s")          # "these symptoms" -> tick off the list
TICK_TIMES = [TICK_T0 + i * 0.2 for i in range(5)]
TURN_T = wt(15, "s")           # "two"
SAVE_T = SEG[8]                # "read my caption"
END_T = wt(38, "s")            # "follow"

# ---------- per-frame composition ----------
def seg_index(t):
    for i in range(len(SEG) - 1):
        if t < SEG[i + 1]: return i
    return len(SEG) - 2

def zoom_at(t):
    i = seg_index(t)
    z_prev = ZOOMS[i - 1] if i > 0 else ZOOMS[0]
    k = ease_out((t - SEG[i]) / (5 / FPS))   # 5-frame punch
    return z_prev + (ZOOMS[i] - z_prev) * k if i > 0 and ZOOMS[i] > z_prev else ZOOMS[i]

def apply_zoom(frame, z):
    if z <= 1.0001: return frame
    cw, ch = W / z, H / z
    ax, ay = ANCHOR
    x0 = clamp(ax - (ax / W) * cw, 0, W - cw)
    y0 = clamp(ay - (ay / H) * ch, 0, H - ch)
    return frame.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))

def overlay(t):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paste(ov, LOGO, (52, 214))  # top-left, inside safe zone

    # B1 tracker + symptom cards (intro) ------------------------------
    trk_a = window(t, -1.0, S2_END - 0.05, fin=0.01, fout=0.25)
    if trk_a > 0:
        cur = seg_index(t) if t < INTRO_END else 5
        x = 196
        for i, (_, _, short, _) in enumerate(SYMPTOMS):
            state = "done" if i < cur else ("now" if i == cur else "todo")
            pill = make_tracker_pill(short, state)
            sc = 1.0
            if state == "now":
                sc = 1.0 + 0.08 * (1 - ease_out((t - SEG[i]) / 0.25))
            paste(ov, pill, (x + 69, 240 + 25), alpha=trk_a, scale=sc, anchor="c")
            x += 150
    for i in range(5):
        a0, a1 = SEG[i] + 0.04, SEG[i + 1] - 0.06
        al = window(t, a0, a1, fin=0.16, fout=0.08)
        if al <= 0: continue
        card, pad = CARDS[i]
        sc = 0.82 + 0.18 * ease_back((t - a0) / 0.24)
        side = SYMPTOMS[i][3]
        cx = 200 + card.width // 2 - pad if side == "L" else 940 - card.width // 2 + pad
        paste(ov, card, (cx, 296 - pad + (card.height) // 2), alpha=al, scale=sc, anchor="c")

    # H1 headline on the chest from frame one ---------------------------
    ha = window(t, -1.0, INTRO_END - 0.02, fin=0.001, fout=0.15)
    paste(ov, HEADLINE, (W // 2, 1268), alpha=ha, anchor="tc")

    # B3 tick list beside her --------------------------------------------
    ta = window(t, SEG[5] + 0.1, S2_END - 0.05, fin=0.22, fout=0.2)
    if ta > 0:
        n = sum(t >= tt for tt in TICK_TIMES)
        card = TICKS[n]
        slide = (1 - ease_out((t - SEG[5] - 0.1) / 0.3)) * -80
        paste(ov, card, (24 + slide, 640), alpha=ta)

    # B6 big turn word below the face -----------------------------------
    ba = window(t, TURN_T, wt(18, "e") + 0.15, fin=0.08, fout=0.15)
    if ba > 0:
        sc = 1.6 - 0.6 * ease_back((t - TURN_T) / 0.22)
        paste(ov, TURN, (700, 1228), alpha=ba, scale=sc, anchor="c")

    # C2 captions ------------------------------------------------------------
    for (a, b, *_), im in zip(CAPS, CAP_IMGS):
        ca = window(t, a, b, fin=0.1, fout=0.06)
        if ca > 0:
            sc = 0.92 + 0.08 * ease_out((t - a) / 0.15)
            paste(ov, im, (W // 2, 1340 + im.height // 2), alpha=ca, scale=sc, anchor="c")

    # E1 save card -> end card ---------------------------------------------
    sa = window(t, SAVE_T, END_T, fin=0.22, fout=0.12)
    if sa > 0:
        sc = 0.9 + 0.1 * ease_back((t - SAVE_T) / 0.3)
        paste(ov, SAVE_CARD, (W // 2, 330 + SAVE_CARD.height // 2 - 20), alpha=sa, scale=sc, anchor="c")
    ea = window(t, END_T, DUR + 1, fin=0.22, fout=0.01)
    if ea > 0:
        sc = 0.9 + 0.1 * ease_back((t - END_T) / 0.3)
        paste(ov, END_CARD, (W // 2, 330 + END_CARD.height // 2 - 20), alpha=ea, scale=sc, anchor="c")
    return ov

# ---------- S1 light ticks (generated, sits under the voice) ----------
SR = 48000
def sfx_pop(f0=900):
    n = int(0.12 * SR); t = np.arange(n) / SR
    f = f0 * np.exp(-t * 9)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
def sfx_tick():
    n = int(0.05 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2400 * t) * 0.6 + np.random.default_rng(1).normal(0, .3, n)) * np.exp(-t * 120)
def sfx_whoosh(d=0.35):
    n = int(d * SR); t = np.arange(n) / SR
    noise = np.random.default_rng(2).normal(0, 1, n)
    k = np.ones(40) / 40; noise = np.convolve(noise, k, "same")
    env = np.sin(np.pi * t / d) ** 2
    thud = np.sin(2 * np.pi * 110 * t) * np.exp(-((t - d * 0.8).clip(0)) * 25) * (t > d * 0.8)
    return noise * env * 2.5 + thud * 0.8
def sfx_chime():
    n = int(0.7 * SR); t = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * f * t) * a for f, a in [(1046.5, .6), (1568, .35), (2093, .2)]) * np.exp(-t * 6)

def build_sfx(path):
    track = np.zeros(int((DUR + 0.5) * SR))
    def add(sig, at, gain_db):
        i = int(at * SR); sig = sig / (np.abs(sig).max() + 1e-9) * 10 ** (gain_db / 20)
        track[i:i + len(sig)] += sig[:len(track) - i]
    for i in range(5): add(sfx_pop(820 + 60 * i), SEG[i] + 0.04, -27)
    for tt in TICK_TIMES: add(sfx_tick(), tt, -31)
    add(sfx_whoosh(), TURN_T - 0.28, -28)
    add(sfx_whoosh(0.3), SAVE_T - 0.05, -32)
    add(sfx_chime(), END_T, -30)
    pcm = (track.clip(-1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

# ---------- main ----------
def frames_in():
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", os.path.join(BUILD, "cut.mov"),
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        yield Image.frombuffer("RGB", (W, H), buf)

def main():
    if PREVIEW:
        times = [float(x) for x in sys.argv[sys.argv.index("--preview") + 1].split(",")]
        os.makedirs(os.path.join(BUILD, "preview"), exist_ok=True)
        for n, fr in enumerate(frames_in()):
            t = n / FPS
            hit = [tt for tt in times if abs(tt - t) < 0.5 / FPS]
            if hit:
                img = apply_zoom(fr, zoom_at(t)).convert("RGBA")
                img.alpha_composite(overlay(t))
                img.convert("RGB").save(os.path.join(BUILD, "preview", f"t{hit[0]:05.2f}.png"))
        return
    sfx = os.path.join(BUILD, "sfx.wav"); build_sfx(sfx)
    out = os.path.join(OUT_DIR, "Priti_Insulin_Resistance_Reel.mp4")
    enc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", os.path.join(BUILD, "cut.mov"), "-i", sfx,
        "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first:normalize=0,"
                           "alimiter=limit=0.89[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    for n, fr in enumerate(frames_in()):
        t = n / FPS
        img = apply_zoom(fr, zoom_at(t)).convert("RGBA")
        img.alpha_composite(overlay(t))
        enc.stdin.write(img.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait()
    print("wrote", out)

if __name__ == "__main__":
    main()
