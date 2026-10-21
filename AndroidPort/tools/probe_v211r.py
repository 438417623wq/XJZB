"""v2.11 batch B: cmdicons frames 128..150 alone, big, numbered.

pair_id.png scaled the wireframe and the building to the same 220px height,
which turns the wireframe into an unreadable purple smudge -- the icon is a
small 32x32-ish isometric silhouette and every candidate looked alike.

This renders ONLY the wireframes, at 6x nearest with no resampling, one per row
with its units.dat id, so the silhouette can actually be read: the Evolution
Chamber's icon has a distinctive round dome, the Ultralisk Cavern's a low wide
mound, the Hydralisk Den's a coiled snake, the Defiler Mound's a flat hump.

Usage: python probe_v211r.py
Output: tools/out/v211_bld/icons_128_150.png
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v211_bld")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

SC = 6
PERROW = 8
GAP = 16


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


data, gaps = SD.read_with_gaps("unit\\cmdbtns\\cmdicons.grp")
frames, mw, mh = grpm.decode_grp(data, gaps)
print("cmdicons %d frames cell %dx%d" % (len(frames), mw, mh))

cells = []
for idx in range(128, 151):
    if idx >= len(frames):
        break
    im = frame_image(frames[idx])
    bb = im.getbbox()
    c = im.crop(bb) if bb else None
    if c is None:
        print("%3d  BLANK" % idx)
        continue
    c = c.resize((c.width * SC, c.height * SC), Image.NEAREST)
    print("%3d  tight=%dx%d" % (idx, c.width, c.height))
    cells.append((idx, c))

cw = max(c.width for _, c in cells) + GAP
ch = max(c.height for _, c in cells) + GAP + 16
rows = (len(cells) + PERROW - 1) // PERROW
img = Image.new("RGBA", (PERROW * cw, rows * ch), (18, 22, 30, 255))
d = ImageDraw.Draw(img)
for i, (idx, c) in enumerate(cells):
    x = (i % PERROW) * cw
    y = (i // PERROW) * ch
    d.text((x + 4, y + 2), str(idx), fill=(240, 220, 120, 255))
    img.paste(c, (x + 4, y + 18), c)

img.save(os.path.join(OUT, "icons_128_150.png"))
print("-> icons_128_150.png (%dx%d)" % (img.width, img.height))
