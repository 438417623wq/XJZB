"""Whole-map view of divide: art only, and art with the walk bitmap tinted.

Reading the whole picture answers the one question the cell crops cannot:
is this map a canyon with a crossing, or two landmasses with nothing between?
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

bright = ImageEnhance.Brightness(world).enhance(1.7)
bright.resize((760, 760), Image.LANCZOS).save(os.path.join(OUT, "_divide_art.png"))

# walk overlay: blocked = red wash, walkable = untouched
arr = np.asarray(bright).copy()
blk = np.kron(~walk, np.ones((8, 8), dtype=bool))     # minitile -> world px
arr[blk] = (arr[blk] * np.array([0.25, 0.55, 0.55]) + np.array([190, 0, 0])).astype(np.uint8)
Image.fromarray(arr).resize((760, 760), Image.LANCZOS).save(os.path.join(OUT, "_divide_walkmask.png"))

# side-by-side, with the two start positions marked
sheet = Image.new("RGB", (760 * 2 + 10, 760), (0, 0, 0))
for i, name in enumerate(("_divide_art.png", "_divide_walkmask.png")):
    im = Image.open(os.path.join(OUT, name)).copy()
    px = im.load()
    for sx, sy in ((320, 240), (1728, 1776)):
        cx, cy = int(sx / 2048 * 760), int(sy / 2048 * 760)
        for d in range(-6, 7):
            for w in (-1, 0, 1):
                if 0 <= cx + d < 760 and 0 <= cy + w < 760:
                    px[cx + d, cy + w] = (0, 255, 255)
                if 0 <= cx + w < 760 and 0 <= cy + d < 760:
                    px[cx + w, cy + d] = (0, 255, 255)
    sheet.paste(im, (i * 770, 0))
sheet.save(os.path.join(OUT, "_divide_overview.png"))
print("walkable %.1f%%  blocked %.1f%%" % (100 * walk.mean(), 100 * (~walk).mean()))
print("wrote", os.path.join(OUT, "_divide_overview.png"))
