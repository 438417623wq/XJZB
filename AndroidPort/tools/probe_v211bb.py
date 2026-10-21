"""v2.11: one image per unit, every block, direction 0, big enough to read.

The combined sheet (probe_v211ba.py) gets downscaled by the image viewer, which
makes the walk/attack seam unreadable. This draws ONE unit per file with the
blocks wrapped across rows so each cell stays large.

Reading rule, calibrated on the five manifest-verified units drawn here too:
    marine   b0,b1,b2 walk -> b3 adds a muzzle flash      => walk=3 atk=3
    zergling b0,b1,b2 walk -> b3 attack                   => walk=3 atk=3
    hydra    b0,b1 walk    -> b2 fires a spine            => walk=2 atk=2
    zealot   b0..b4 walk   -> b5 psi blade                => walk=5 atk=5
    dragoon  b0..b7 walk   -> b8 blue muzzle flash        => walk=8 atk=8
So: walk = the blocks before the first one that is clearly a firing/striking
pose; the last block (short frame count) is the death.

Usage: python probe_v211bb.py <key> [key ...]
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
    "marine": ("unit\\terran\\marine.grp", "RULER walk=3 atk=3"),
    "zergling": ("unit\\zerg\\zergling.grp", "RULER walk=3 atk=3"),
    "hydra": ("unit\\zerg\\hydra.grp", "RULER walk=2 atk=2"),
    "zealot": ("unit\\protoss\\zealot.grp", "RULER walk=5 atk=5"),
    "dragoon": ("unit\\protoss\\dragoon.grp", "RULER walk=8 atk=8"),
    "ultra": ("unit\\zerg\\ultra.grp", ""),
    "queen": ("unit\\zerg\\queen.grp", ""),
    "defiler": ("unit\\zerg\\defiler.grp", ""),
    "guardian": ("unit\\zerg\\guardian.grp", ""),
    "devourer": ("unit\\zerg\\devour.grp", ""),
    "lurker": ("unit\\zerg\\lurknorm.grp", ""),
    "lurker_bur": ("unit\\zerg\\lurkburr.grp", ""),
    "broodling": ("unit\\zerg\\brood.grp", ""),
    "medic": ("unit\\terran\\medic.grp", ""),
    "valkyrie": ("unit\\terran\\bomber.grp", ""),
    "spider": ("unit\\terran\\Spider.grp", ""),
}

CELL = 260
PERROW = 6
LABW = 110


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
    path, note = PATHS[key]
    res = load(path)
    if res is None:
        print("MISS", key)
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    rows = (nb + PERROW - 1) // PERROW
    W = LABW + PERROW * CELL
    H = rows * CELL + 26
    img = Image.new("RGBA", (W, H), (16, 16, 22, 255))
    dr = ImageDraw.Draw(img)
    dr.text((5, 6), "%s  %s  blocks=%d" % (key, note, nb),
            fill=(255, 235, 140, 255))
    for b in range(nb):
        nfr = min(17, len(frames) - b * 17)
        im = tight(frame_image(frames[b * 17]))
        sc = min((CELL - 24) / max(1, im.width), (CELL - 24) / max(1, im.height))
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))),
                       Image.NEAREST)
        ox = LABW + (b % PERROW) * CELL
        oy = 26 + (b // PERROW) * CELL
        img.paste(im, (ox + (CELL - im.width) // 2,
                       oy + 16 + (CELL - 16 - im.height) // 2), im)
        col = (140, 220, 255, 255) if nfr == 17 else (255, 150, 120, 255)
        dr.text((ox + 4, oy + 2), "b%d n=%d" % (b, nfr), fill=col)
    p = os.path.join(OUT, "read_%s.png" % key)
    img.save(p)
    print("->", p, img.size)
