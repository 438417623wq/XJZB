"""Render the newly extracted effect sheets side by side for visual check."""
import os
from PIL import Image

SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
KEYS = ["flsh_s", "flsh_m", "flsh_l", "smoke", "hit"]

cells = []
for k in KEYS:
    im = Image.open(os.path.join(SPR, k + "_b.png")).convert("RGBA")
    cells.append((k, im))

scale = 2
pad = 8
W = max(im.width * scale for _, im in cells) + pad * 2
H = sum(im.height * scale + 22 + pad for _, im in cells) + pad
canvas = Image.new("RGB", (W, H), (26, 28, 36))
y = pad
from PIL import ImageDraw
d = ImageDraw.Draw(canvas)
for k, im in cells:
    d.text((pad, y), "%s  %dx%d" % (k, im.width, im.height), fill=(120, 255, 140))
    y += 18
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    canvas.paste(big, (pad, y), big)
    y += big.height + pad

canvas.save(os.path.join(OUT, "fx_contact.png"))
print("wrote fx_contact.png", canvas.size)
