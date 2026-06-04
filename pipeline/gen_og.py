"""Generate the 1200x630 OG share card — Hockey Night in Canada on a warm CRT.
Run: uv run --with pillow python pipeline/gen_og.py
(expects Saira Condensed at /tmp/SairaCondensed-Bold.ttf; falls back to DejaVu)
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1200, 630
INK = (243, 233, 212)
AMBER = (232, 163, 61)
RED = (216, 35, 42)
TEAL = (70, 174, 191)
MUTED = (164, 144, 111)

SAIRA = "/tmp/SairaCondensed-Bold.ttf"
DEJAVU_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DISPLAY = SAIRA if os.path.exists(SAIRA) else DEJAVU_B


def font(p, s):
    return ImageFont.truetype(p, s)


# --- warm gradient base ---
img = Image.new("RGB", (W, H))
top, bot = (20, 48, 71), (7, 15, 24)
px = img.load()
for y in range(H):
    t = y / H
    c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
    for x in range(W):
        px[x, y] = c

# warm amber glow, top-center
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([W * 0.2, -H * 0.5, W * 0.8, H * 0.5], fill=(232, 163, 61, 70))
glow = glow.filter(ImageFilter.GaussianBlur(120))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")

d = ImageDraw.Draw(img)


def center(text, y, f, fill, track=0):
    total = sum(d.textlength(c, font=f) + track for c in text) - (track if text else 0)
    x = (W - total) / 2
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + track


def aberr_run(parts, y):
    """Draw a row of (text, color) parts centered, with RGB misconvergence."""
    f = parts[0][2]
    total = sum(d.textlength(t, font=ff) for t, _, ff in parts)
    x0 = (W - total) / 2
    for dx, col in ((-3, RED), (3, TEAL)):
        x = x0
        for t, _, ff in parts:
            d.text((x + dx, y), t, font=ff, fill=col)
            x += d.textlength(t, font=ff)
    x = x0
    for t, col, ff in parts:
        d.text((x, y), t, font=ff, fill=col)
        x += d.textlength(t, font=ff)


center("NHL · ERA-ADJUSTED · 1929–PRESENT", 96, font(DISPLAY, 30), AMBER, track=8)

# wordmark with misconvergence, auto-fit
size = 168
while True:
    big = font(DISPLAY, size)
    parts = [("CHASE THE ", INK, big), ("CUP", RED, big)]
    if sum(d.textlength(t, font=big) for t, _, _ in parts) <= W - 150 or size <= 110:
        break
    size -= 4
aberr_run(parts, 205)

d.line([(330, 205 + size + 6), (W - 330, 205 + size + 6)], fill=AMBER, width=3)

center("Draft six legends from across hockey history.", 452, font(DEJAVU, 32), MUTED)
center("16 WINS TO THE CUP — CAN YOU GO 16-0?", 512, font(DISPLAY, 44), RED, track=1)
d.text((58, H - 80), "chase-the-cup.com", font=font(DISPLAY, 30), fill=MUTED)

# --- CRT vignette ---
vig = Image.new("L", (W, H), 0)
ImageDraw.Draw(vig).ellipse([-W * 0.16, -H * 0.16, W * 1.16, H * 1.16], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(130))
img = Image.composite(img, Image.new("RGB", (W, H), (4, 2, 0)), vig)

# --- scanlines ---
scan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(scan)
for y in range(0, H, 3):
    sd.line([(0, y), (W, y)], fill=(0, 0, 0, 32))
img = Image.alpha_composite(img.convert("RGBA"), scan).convert("RGB")

out = Path(__file__).parent.parent / "web" / "static" / "og-default.png"
img.save(out, "PNG")
print("wrote", out, img.size, "display=", "Saira" if DISPLAY == SAIRA else "DejaVu")
