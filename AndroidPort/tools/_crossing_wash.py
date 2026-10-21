"""v2.44: readable overlay -- minitile wash over the shipped art.

The 2px corner dots from _crossing_art.py are invisible at this zoom. Paint a
translucent wash at minitile resolution instead, so "blocked cell sits on cliff
art" vs "blocked cell sits on open ground" is answerable by eye.
"""
import gzip
import os

import numpy as np
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
MID = "divide"
CS = 512
SC = 3  # world px -> display px


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


def render(cx_m, cy_m, r_m, name):
    """cx_m/cy_m = centre minitile, r_m = half window in minitiles."""
    x0, y0 = (cx_m - r_m) * 8, (cy_m - r_m) * 8
    x1, y1 = (cx_m + r_m) * 8, (cy_m + r_m) * 8
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w * 32, x1), min(h * 32, y1)
    base = Image.new("RGB", (x1 - x0, y1 - y0), (0, 0, 0))
    for cy in range(y0 // CS, (y1 - 1) // CS + 1):
        for cx in range(x0 // CS, (x1 - 1) // CS + 1):
            im = chunk(MID, cx, cy)
            if im is None:
                continue
            base.paste(im, (cx * CS - x0, cy * CS - y0))
    big = base.resize(((x1 - x0) * SC, (y1 - y0) * SC), Image.NEAREST)
    wash = Image.new("RGBA", big.size, (0, 0, 0, 0))
    wp = wash.load()
    for my in range(y0 // 8, y1 // 8):
        for mx in range(x0 // 8, x1 // 8):
            ok = walk[my, mx]
            # walkable: faint green edge; blocked: strong red wash
            col = (0, 255, 0, 40) if ok else (255, 0, 0, 120)
            bx, by = (mx * 8 - x0) * SC, (my * 8 - y0) * SC
            for dy in range(8 * SC):
                for dx in range(8 * SC):
                    if 0 <= bx + dx < big.size[0] and 0 <= by + dy < big.size[1]:
                        wp[bx + dx, by + dy] = col
    out = Image.alpha_composite(big.convert("RGBA"), wash).convert("RGB")
    p = os.path.join(OUT, name)
    out.save(p, quality=88)
    print("saved %s  window worldpx x %d..%d y %d..%d  (red=blocked minitile)" % (p, x0, x1, y0, y1))


walk, w, h = load(MID)
render(110, 130, 36, "_divide_x1.jpg")   # tile(27,32) world (880,1040)
render(189, 14, 36, "_divide_x2.jpg")    # tile(47,3)  world (1512,112)
render(158, 106, 36, "_divide_x3.jpg")   # tile(39,26) world (1264,848)
render(216, 164, 36, "_divide_x4.jpg")   # tile(54,41) world (1728,1312)
