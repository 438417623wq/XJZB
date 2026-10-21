"""Reproduce GameView.drawEnt exactly to find why buildings/units look translucent.

Renders the same CC sprite four ways over the real map terrain:
  A) old v2.3 look (no shadow)
  B) v2.4: shadow oval UNDER the sprite (current code)
  C) shadow oval OVER the sprite (what it would look like if the oval leaked)
  D) sprite at alpha 130 (the constructing branch, in case it leaks)
"""
import os
from PIL import Image, ImageDraw

A = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"

terrain = Image.open(os.path.join(A, "maps", "3kingdoms", "c_0_0.png")).convert("RGB")
cc = Image.open(os.path.join(A, "sprites", "cc_b.png")).convert("RGBA")
fw, fh = cc.width // 6, cc.height
frame = cc.crop((0, 0, fw, fh))

zoom = 1.15
W = H = 300


def panel(with_shadow, shadow_over, alpha):
    im = terrain.crop((100, 100, 100 + W, 100 + H)).resize((W, H)).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    cx, cy = W / 2, H / 2
    r = max(40, 4 * 14) * zoom
    if with_shadow and not shadow_over:
        d.ellipse([cx - r * .8, cy - r * .26, cx + r * .8, cy + r * .26],
                  fill=(0, 0, 0, 90))
    spr = frame.resize((int(fw * zoom), int(fh * zoom)), Image.NEAREST)
    if alpha < 255:
        spr = spr.copy()
        spr.putalpha(spr.split()[3].point(lambda v: v * alpha // 255))
    im.paste(spr, (int(cx - spr.width / 2), int(cy - spr.height * .65)), spr)
    if with_shadow and shadow_over:
        d.ellipse([cx - r * .8, cy - r * .26, cx + r * .8, cy + r * .26],
                  fill=(0, 0, 0, 90))
    return im


panels = [
    ("A: v2.3 (no shadow)", panel(False, False, 255)),
    ("B: v2.4 shadow UNDER", panel(True, False, 255)),
    ("C: shadow OVER (leak?)", panel(True, True, 255)),
    ("D: sprite alpha 130", panel(False, False, 130)),
]
sc = 2
cv = Image.new("RGB", (W * sc * 2 + 30, (H * sc + 24) * 2 + 10), (26, 28, 36))
d = ImageDraw.Draw(cv)
for i, (label, im) in enumerate(panels):
    x = (i % 2) * (W * sc + 10) + 6
    y = (i // 2) * (H * sc + 24) + 4
    d.text((x, y), label, fill=(120, 255, 140))
    cv.paste(im.resize((W * sc, H * sc), Image.NEAREST), (x, y + 16))
cv.save(os.path.join(OUT, "transparency_diag.png"))
print("wrote transparency_diag.png", cv.size)
