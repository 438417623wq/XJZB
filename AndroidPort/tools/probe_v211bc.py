"""v2.11: settle the GRP frame layout.

pipeline_sprites.py treats the GRP as frame index = block*17 + direction, i.e.
each "block" is ONE animation frame drawn in all 17 facings, and `walk_blocks`
counts animation frames. If that is right, the 17 frames inside one block must
show the SAME pose rotated through the 17 facings.

This renders, for a few units, the raw frames 0..33 in order (two blocks), one
cell per raw frame. A rotation sequence means the block=animation-frame reading
is correct; an in-place animation means the opposite.

Usage: python probe_v211bc.py <key>
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "v211_unit")
os.makedirs(OUT, exist_ok=True)

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

PATHS = {
    "marine": "unit\\terran\\marine.grp",
    "ultra": "unit\\zerg\\ultra.grp",
    "hydra": "unit\\zerg\\hydra.grp",
    "zergling": "unit\\zerg\\zergling.grp",
}

CELL = 150
PERROW = 17
LABW = 90


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


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


def tight(im):
    bb = im.getbbox()
    return im.crop(bb) if bb else im


for key in sys.argv[1:]:
    res = load(PATHS[key])
    if res is None:
        print("MISS", key)
        continue
    frames, mw, mh = res
    nshow = min(34, len(frames))
    rows = 2
    W = LABW + PERROW * CELL
    H = 26 + rows * CELL
    img = Image.new("RGBA", (W, H), (16, 16, 22, 255))
    dr = ImageDraw.Draw(img)
    dr.text((5, 6), "%s raw frames 0..%d  cell=%dx%d" % (key, nshow - 1, mw, mh),
            fill=(255, 235, 140, 255))
    for i in range(nshow):
        im = tight(frame_image(frames[i]))
        sc = min((CELL - 24) / max(1, im.width), (CELL - 24) / max(1, im.height))
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))),
                       Image.NEAREST)
        ox = LABW + (i % PERROW) * CELL
        oy = 26 + (i // PERROW) * CELL
        img.paste(im, (ox + (CELL - im.width) // 2,
                       oy + 16 + (CELL - 16 - im.height) // 2), im)
        dr.text((ox + 3, oy + 2), "%d" % i, fill=(140, 220, 255, 255))
    p = os.path.join(OUT, "raw_%s.png" % key)
    img.save(p)
    print("->", p, img.size)
