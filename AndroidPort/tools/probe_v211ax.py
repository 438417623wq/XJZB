"""v2.11: read the walk-cycle length for each batch B unit off the art.

Only blocks 0..7 are shown, because in this pack every verified unit has its
walk->attack seam inside that window (marine 3, zergling 3, hydra 2, zealot 5,
dragoon 8). One row per unit, eight cells, so the whole set fits in a single
image that does not get downscaled.

The rulers are drawn first with their KNOWN answer printed, so the reading rule
is calibrated in the same picture: a walk block is a locomotion pose, the attack
block is the one that adds a muzzle flash / recoil / stab, and everything after
that is attack or death.

Usage: python probe_v211ax.py
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

ROWS = [
    ("marine  WALK=3 atk=3", "unit\\terran\\marine.grp"),
    ("zergling WALK=3 atk=3", "unit\\zerg\\zergling.grp"),
    ("hydra   WALK=2 atk=2", "unit\\zerg\\hydra.grp"),
    ("zealot  WALK=5 atk=5", "unit\\protoss\\zealot.grp"),
    ("dragoon WALK=8 atk=8", "unit\\protoss\\dragoon.grp"),
    ("---", None),
    ("ultra", "unit\\zerg\\ultra.grp"),
    ("queen", "unit\\zerg\\queen.grp"),
    ("defiler", "unit\\zerg\\defiler.grp"),
    ("guardian", "unit\\zerg\\guardian.grp"),
    ("devourer", "unit\\zerg\\devour.grp"),
    ("lurker", "unit\\zerg\\lurknorm.grp"),
    ("lurker_bur", "unit\\zerg\\lurkburr.grp"),
    ("broodling", "unit\\zerg\\brood.grp"),
    ("medic", "unit\\terran\\medic.grp"),
    ("valkyrie", "unit\\terran\\bomber.grp"),
    ("spider", "unit\\terran\\Spider.grp"),
]

NCELL = 8
CELL = 180
LABW = 250


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


img = Image.new("RGBA", (LABW + NCELL * CELL, len(ROWS) * CELL), (16, 16, 22, 255))
dr = ImageDraw.Draw(img)
for r, (lab, path) in enumerate(ROWS):
    y0 = r * CELL
    dr.text((5, y0 + 6), lab, fill=(255, 235, 140, 255))
    if path is None:
        continue
    res = load(path)
    if res is None:
        dr.text((5, y0 + 24), "MISS", fill=(255, 90, 90, 255))
        continue
    frames, mw, mh = res
    for b in range(NCELL):
        fi = b * 17
        if fi >= len(frames):
            break
        im = tight(frame_image(frames[fi]))
        sc = min((CELL - 26) / max(1, im.width), (CELL - 26) / max(1, im.height))
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))),
                       Image.NEAREST)
        ox = LABW + b * CELL
        img.paste(im, (ox + (CELL - im.width) // 2,
                       y0 + 20 + (CELL - 20 - im.height) // 2), im)
        dr.text((ox + 4, y0 + 4), "b%d" % b, fill=(140, 220, 255, 255))
    dr.text((5, y0 + CELL - 16), "blocks=%d" % ((len(frames) + 16) // 17),
            fill=(150, 200, 255, 255))

p = os.path.join(OUT, "walk_read.png")
img.save(p)
print("->", p, img.size)
