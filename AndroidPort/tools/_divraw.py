"""v2.44: raw art panels around divide's blocked band, one file each.

No overlay: the question is whether the band that separates the two bases is
water/cliff art (a genuine barrier) or ordinary ground (which would mean our
VF4 walkability read is wrong).
"""
import os

from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
MAP = os.path.join(ASSETS, "maps", "divide")

with open(os.path.join(MAP, "meta.txt"), "r", encoding="utf-8", errors="replace") as f:
    meta = f.read()
W = H = 0
for line in meta.splitlines():
    if line.startswith("w="):
        W = int(line[2:])
    elif line.startswith("h="):
        H = int(line[2:])

world = Image.new("RGB", (W * 32, H * 32), (0, 0, 0))
for cy in range(H // 16):
    for cx in range(W // 16):
        p = os.path.join(MAP, "c_%d_%d.webp" % (cx, cy))
        if os.path.exists(p):
            world.paste(Image.open(p).convert("RGB"), (cx * 512, cy * 512))

CENTRES = [(872, 1048), (1264, 848), (1728, 1312), (1512, 112)]
SPAN = 256
SCALE = 2
for i, (cx, cy) in enumerate(CENTRES):
    box = (max(0, cx - SPAN), max(0, cy - SPAN), min(world.width, cx + SPAN), min(world.height, cy + SPAN))
    c = world.crop(box).resize(((box[2] - box[0]) * SCALE, (box[3] - box[1]) * SCALE), Image.LANCZOS)
    c = Image.eval(c, lambda v: min(255, int(v * 1.8)))
    c.save(os.path.join(OUT, "_divraw_%d.png" % i))
    print("centre(%d,%d) -> _divraw_%d.png %s" % (cx, cy, i, c.size))
