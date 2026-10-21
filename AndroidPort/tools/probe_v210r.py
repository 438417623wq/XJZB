"""v2.10: identify the spell/ability icons in cmdicons.grp.

The order buttons are 228..239. The ability block follows; the templar's
Psionic Storm needs a real button rather than falling back to a text label.
Render 236..272 in a labelled grid so the storm icon can be picked by eye.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
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
else:
    raise SystemExit("cmdicons not found")

print("cmdicons %d frames %dx%d" % (len(frames), mw, mh))

FIRST, LAST = 236, 274
COLS, ZOOM = 8, 4
cw, ch = mw * ZOOM, mh * ZOOM + 16
rows = (LAST - FIRST + COLS) // COLS
img = Image.new("RGBA", (COLS * cw, rows * ch), (24, 24, 32, 255))
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
    im = frame_image(frames[k]).resize((mw * ZOOM, mh * ZOOM), Image.NEAREST)
    ox = (k - FIRST) % COLS * cw
    oy = (k - FIRST) // COLS * ch
    img.paste(im, (ox, oy), im)
    d.text((ox + 4, oy + mh * ZOOM + 1), str(k), fill=(255, 255, 0, 255))

p = os.path.join(OUT, "cmdicons_ability.png")
img.save(p)
print("wrote", p, img.size)
