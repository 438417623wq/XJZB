"""v2.10: large renders of the candidate ability icons.

The order buttons 228..239 are already mapped in pipeline_sprites.py. This
prints 240..274 one per file at 10x so the templar's Psionic Storm button can
be picked by eye instead of by guess.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "v210_abil")
os.makedirs(OUT, exist_ok=True)
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

for ar in (PT, SD, BD):
    if ar.has("unit\\cmdbtns\\cmdicons.grp"):
        data, gaps = ar.read_with_gaps("unit\\cmdbtns\\cmdicons.grp")
        frames, mw, mh = grpm.decode_grp(data, gaps)
        break

Z, PAD = 10, 22
FIRST, LAST = 240, 274
COLS = 7
rows = (LAST - FIRST + 1 + COLS - 1) // COLS
cw, ch = mw * Z + 8, mh * Z + PAD
img = Image.new("RGBA", (COLS * cw, rows * ch), (20, 20, 26, 255))
d = ImageDraw.Draw(img)


def frame_image(f):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = PAL[v] + (255,)
    return im


for k in range(FIRST, LAST + 1):
    if k >= len(frames):
        break
    im = frame_image(frames[k]).resize((mw * Z, mh * Z), Image.NEAREST)
    ox = (k - FIRST) % COLS * cw + 4
    oy = (k - FIRST) // COLS * ch + 2
    img.paste(im, (ox, oy), im)
    d.text((ox + 4, oy + mh * Z + 3), str(k), fill=(255, 255, 0, 255))

p = os.path.join(OUT, "ability_240_274.png")
img.save(p)
print("wrote", p, img.size)
