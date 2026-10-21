"""Render the full cmdicons.grp grid with frame indices to identify icons."""
import os
from PIL import Image, ImageDraw
import sc_archive
import grp as grpm

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
pal = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]

data, gaps = SD.read_with_gaps("unit\\cmdbtns\\cmdicons.grp")
frames, mw, mh = grpm.decode_grp(data, gaps)
n = len(frames)
print("cmdicons:", n, "frames", mw, "x", mh)

cols = 20
rows = (n + cols - 1) // cols
img = Image.new("RGB", (cols * (mw + 1), rows * (mh + 8)), (18, 18, 24))
dr = ImageDraw.Draw(img)
for fi in range(n):
    f = frames[fi]
    cx = (fi % cols) * (mw + 1)
    cy = (fi // cols) * (mh + 8)
    for y in range(f["h"]):
        for x in range(f["w"]):
            v = f["px"][y * f["w"] + x]
            if v != 255:
                img.putpixel((cx + f["x"] + x, cy + 8 + f["y"] + y), pal[v])
    dr.text((cx + 1, cy), str(fi), fill=(120, 220, 120))
img.save(r"F:\KF\XJZB\AndroidPort\tools\out\cmdicons_all.png")
print("saved cmdicons_all.png", img.size)
