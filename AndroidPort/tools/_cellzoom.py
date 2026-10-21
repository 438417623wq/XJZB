"""Zoom the two suspicious blocking cells with the walk bitmap drawn on top.

If a red (blocked) minitile sits on walkable-looking ground, the bake is suspect.
If red traces cliff/water art, the split is real map design.
"""
import gzip, os
import numpy as np
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
raw = gzip.open(os.path.join(ASSETS, "walk.bin.gz"), "rb").read()
walk = np.frombuffer(raw, dtype=np.uint8).reshape(256, 256) != 0

world = Image.new("RGB", (2048, 2048))
for cy in range(4):
    for cx in range(4):
        world.paste(Image.open(os.path.join(ASSETS, "c_%d_%d.webp" % (cx, cy))).convert("RGB"),
                    (cx * 512, cy * 512))

S = 14      # minitiles per side
UP = 12     # pixels per minitile in the output
sheet = Image.new("RGB", (S * UP * 2 + 20, S * UP), (20, 20, 20))
for i, (mx, my) in enumerate([(189, 14), (216, 164)]):
    x0, y0 = mx * 8 - (S // 2) * 8, my * 8 - (S // 2) * 8
    crop = world.crop((x0, y0, x0 + S * 8, y0 + S * 8)).resize((S * UP, S * UP), Image.NEAREST)
    px = crop.load()
    for gy in range(S):
        for gx in range(S):
            gmx, gmy = mx - S // 2 + gx, my - S // 2 + gy
            ok = 0 <= gmx < 256 and 0 <= gmy < 256 and walk[gmy, gmx]
            col = (0, 255, 0) if ok else (255, 0, 0)
            bx, by = gx * UP, gy * UP
            for k in range(UP):
                px[bx + k, by] = col
                px[bx + k, by + UP - 1] = col
                px[bx, by + k] = col
                px[bx + UP - 1, by + k] = col
    sheet.paste(crop, (i * (S * UP + 20), 0))
    print("cell %d  minitile(%d,%d)  walk=%s" % (i, mx, my, walk[my, mx]))
sheet.save(os.path.join(OUT, "_divide_cellzoom.png"))
print("wrote", os.path.join(OUT, "_divide_cellzoom.png"))
