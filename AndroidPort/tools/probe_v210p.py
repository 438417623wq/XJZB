"""v2.10: render one frame of every protoss building GRP into one labelled
contact sheet, so the name->art mapping in pipeline_expand.py's BUILDINGS table
(which carries three "confirm" comments) can be settled by eye instead of guess.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "v210_bld")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


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


CAND = [
    ("nexus", "unit\\protoss\\nexus.grp"),
    ("pylon", "unit\\protoss\\pylon.grp"),
    ("assim", "unit\\protoss\\assim.grp"),
    ("gateway", "unit\\protoss\\gateway.grp"),
    ("forge", "unit\\protoss\\forge.grp"),
    ("photon", "unit\\protoss\\photon.grp"),
    ("gencore", "unit\\protoss\\gencore.grp"),
    ("citadel", "unit\\protoss\\citadel.grp"),
    ("robotic", "unit\\protoss\\robotic.grp"),
    ("archives", "unit\\protoss\\archives.grp"),
    ("stargate", "unit\\protoss\\stargate.grp"),
    ("beacon", "unit\\protoss\\beacon.grp"),
    ("sbattery", "unit\\protoss\\sbattery.grp"),
    ("warp", "unit\\protoss\\warp.grp"),
    ("prism", "unit\\protoss\\prism.grp"),
    ("texture", "unit\\protoss\\texture.grp"),
    ("pylon2", "unit\\protoss\\pylon2.grp"),
    ("crystal", "unit\\thingy\\crystal.grp"),
    ("p_turret", "unit\\protoss\\turret.grp"),
    ("p_observ", "unit\\protoss\\observ.grp"),
    ("p_obsrv", "unit\\protoss\\obsrv.grp"),
    ("p_obscol", "unit\\protoss\\obscol.grp"),
    ("p_eye", "unit\\protoss\\eye.grp"),
]

os.makedirs(OUT, exist_ok=True)
CELL = 200
cols = 6
rows = (len(CAND) + cols - 1) // cols
sheet = Image.new("RGBA", (cols * CELL, rows * CELL), (18, 18, 26, 255))
d = ImageDraw.Draw(sheet)
for i, (name, path) in enumerate(CAND):
    r = load(path)
    cx, cy = (i % cols) * CELL, (i // cols) * CELL
    if r is None:
        d.text((cx + 4, cy + 4), name + " MISS", fill=(255, 90, 90, 255))
        continue
    frames, mw, mh = r
    if not frames:
        d.text((cx + 4, cy + 4), name + " EMPTY", fill=(255, 200, 90, 255))
        continue
    im = frame_image(frames[0])
    sc = min((CELL - 20) / max(1, mw), (CELL - 20) / max(1, mh), 1.0)
    if sc < 1.0:
        im = im.resize((max(1, int(mw * sc)), max(1, int(mh * sc))), Image.NEAREST)
    sheet.paste(im, (cx + 10, cy + 10), im)
    d.text((cx + 4, cy + CELL - 14), "%s %dx%d f=%d" % (name, mw, mh, len(frames)),
           fill=(200, 220, 255, 255))
sheet.save(os.path.join(OUT, "contact.png"))
print("wrote", os.path.join(OUT, "contact.png"), sheet.size)
