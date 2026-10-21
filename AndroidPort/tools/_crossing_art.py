"""v2.44: is divide's 3-minitile wall real terrain or repack damage?

_wall.py/_crossing.py show the two starts sit behind a wall only 3 minitiles
(24 world px, less than one 32px tile) thick at its thinnest, and that
pipeline_maps.connectivity() only calls the map "connected" because of its
1-minitile dilation -- which its own docstring says is "far too small to bridge
an island's water". Meanwhile the SHIPPED walk.bin.gz is the raw bitmap, so at
runtime the two starts really are cut off.

A wall thinner than a tile is geometrically odd for terrain art, and the
pipeline header already documents that "the damaged repack leaves single
minitile holes in the VF4 read". So overlay the walk bitmap on the actual
shipped chunk art at the crossing: cliff/water art under a blocked cell means
the map is genuinely divided; plain ground art under it means the repack
dropped walkability bits.
"""
import gzip
import os

import numpy as np
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
MID = "divide"
CS = 512


def load(mid):
    with gzip.open(os.path.join(ASSETS, mid, "walk.bin.gz"), "rb") as f:
        raw = f.read()
    meta = {}
    with open(os.path.join(ASSETS, mid, "meta.txt"), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                meta.setdefault(k, []).append(v)
    w, h = int(meta["w"][0]), int(meta["h"][0])
    return np.frombuffer(raw, dtype=np.uint8).reshape(h * 4, w * 4), w, h


def chunk(mid, cx, cy):
    p = os.path.join(ASSETS, mid, "c_%d_%d.webp" % (cx, cy))
    if not os.path.exists(p):
        return None
    return Image.open(p).convert("RGB")


walk, w, h = load(MID)
print("walk %dx%d minitiles" % (walk.shape[1], walk.shape[0]))

# the three crossing cells found by _crossing.py, plus the two singles
crossings = [(189, 14), (109, 131), (110, 130), (111, 129), (158, 106), (159, 107), (216, 164)]

# world-pixel box covering all of them
wxs = [x * 8 for (_y, x) in crossings]
wys = [y * 8 for (y, _x) in crossings]
x0, x1 = min(wxs) - 256, max(wxs) + 256
y0, y1 = min(wys) - 256, max(wys) + 256
x0, y0 = max(0, x0), max(0, y0)
x1, y1 = min(w * 32, x1), min(h * 32, y1)
print("art window world px x %d..%d  y %d..%d" % (x0, x1, y0, y1))

# stitch the chunk art for that window (nearest, no scaling yet)
base = Image.new("RGB", (x1 - x0, y1 - y0))
for cy in range(y0 // CS, (y1 - 1) // CS + 1):
    for cx in range(x0 // CS, (x1 - 1) // CS + 1):
        im = chunk(MID, cx, cy)
        if im is None:
            print("  MISSING chunk %d_%d" % (cx, cy))
            continue
        ox, oy = cx * CS - x0, cy * CS - y0
        base.paste(im, (ox, oy))
print("art stitched %s" % (base.size,))

# overlay: blocked minitile -> red dot, walkable -> green dot, on a 4x upscale
sc = 4
big = base.resize((base.size[0] * sc, base.size[1] * sc), Image.NEAREST)
px = big.load()
mx0, my0 = x0 // 8, y0 // 8
for my in range(my0, y1 // 8):
    for mx in range(x0 // 8, x1 // 8):
        if my < 0 or mx < 0 or my >= walk.shape[0] or mx >= walk.shape[1]:
            continue
        ok = walk[my, mx]
        col = (0, 255, 0) if ok else (255, 0, 0)
        bx, by = (mx * 8 - x0) * sc, (my * 8 - y0) * sc
        # 1x1 world-px dot in the corner of each minitile so the art stays readable
        for dy in range(2):
            for dx in range(2):
                if 0 <= bx + dx < big.size[0] and 0 <= by + dy < big.size[1]:
                    px[bx + dx, by + dy] = col
p = os.path.join(OUT, "_divide_walk_over_art.png")
big.save(p)
print("saved %s  (green dot = walkable minitile, red dot = blocked)" % p)

# and a tight crop around the thinnest crossing (110,130)
cy_, cx_ = 130, 110
r = 40
c = big.crop(((cx_ * 8 - x0 - r * 8) * sc, (cy_ * 8 - y0 - r * 8) * sc,
              (cx_ * 8 - x0 + r * 8) * sc, (cy_ * 8 - y0 + r * 8) * sc))
p2 = os.path.join(OUT, "_divide_crossing_art.png")
c.save(p2)
print("saved %s (tight crop around minitile 110,130)" % p2)
