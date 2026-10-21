"""Brightened crops around the blocking cells, with the blocked minitiles tinted red.

Bigger window + brightness boost so the terrain type is actually readable.
"""
import gzip, os
import numpy as np
from PIL import Image, ImageEnhance

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
walk = (np.frombuffer(gzip.open(os.path.join(ASSETS, "walk.bin.gz"), "rb").read(),
                      dtype=np.uint8).reshape(256, 256) != 0)

world = Image.new("RGB", (2048, 2048))
for cy in range(4):
    for cx in range(4):
        world.paste(Image.open(os.path.join(ASSETS, "c_%d_%d.webp" % (cx, cy))).convert("RGB"),
                    (cx * 512, cy * 512))
world = ImageEnhance.Brightness(world).enhance(2.1)

SPAN = 32          # minitiles per side
UP = 6             # output pixels per minitile
tile = SPAN * UP
cells = [(189, 14), (109, 131), (158, 106), (216, 164)]
sheet = Image.new("RGB", (tile * 2 + 12, tile * 2 + 12), (0, 0, 0))
for i, (mx, my) in enumerate(cells):
    x0, y0 = mx * 8 - (SPAN // 2) * 8, my * 8 - (SPAN // 2) * 8
    crop = world.crop((x0, y0, x0 + SPAN * 8, y0 + SPAN * 8)).resize((tile, tile), Image.NEAREST)
    px = crop.load()
    for gy in range(SPAN):
        for gx in range(SPAN):
            gmx, gmy = mx - SPAN // 2 + gx, my - SPAN // 2 + gy
            ok = 0 <= gmx < 256 and 0 <= gmy < 256 and walk[gmy, gmx]
            if ok:
                continue                      # walkable: leave the art alone
            bx, by = gx * UP, gy * UP
            for yy in range(by, by + UP):
                for xx in range(bx, bx + UP):
                    r, g, b = px[xx, yy]
                    px[xx, yy] = (min(255, r + 120), g // 3, b // 3)
    sheet.paste(crop, ((i % 2) * (tile + 12), (i // 2) * (tile + 12)))
    print("cell %d minitile(%d,%d) walk=%s" % (i, mx, my, walk[my, mx]))
sheet.save(os.path.join(OUT, "_divide_cellbig.png"))
print("wrote", os.path.join(OUT, "_divide_cellbig.png"))
