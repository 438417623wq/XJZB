"""v2.11: ONE page, one row per unit, first N blocks at a readable size.

Walk length cannot be found numerically: the walk blocks are all DISTINCT poses
(the cycle is implicit -- block W-1 loops back to block 0), so no
self-similarity test can find the seam. probe_v211bn/bo/bs/bt all failed for
exactly this reason. The only usable cue is visual: the walk ends where the pose
stops being a stride and becomes an attack (muzzle flare / weapon extension) or
a spell / death. So render big and read it.

Rulers on the page: marine walk=3, zergling walk=3, hydra walk=2, zealot walk=5,
dragoon walk=8 -- all confirmed during batch A.

Usage: python probe_v211bv.py [key ...]
Env: CELL, PERROW, LABW, DIR, NB
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
    "zergling": "unit\\zerg\\zergling.grp",
    "hydra": "unit\\zerg\\hydra.grp",
    "zealot": "unit\\protoss\\zealot.grp",
    "dragoon": "unit\\protoss\\dragoon.grp",
    "ultra": "unit\\zerg\\ultra.grp",
    "queen": "unit\\zerg\\queen.grp",
    "defiler": "unit\\zerg\\defiler.grp",
    "guardian": "unit\\zerg\\guardian.grp",
    "devourer": "unit\\zerg\\devour.grp",
    "lurker": "unit\\zerg\\lurknorm.grp",
    "lurker_bur": "unit\\zerg\\lurkburr.grp",
    "broodling": "unit\\zerg\\brood.grp",
    "medic": "unit\\terran\\medic.grp",
    "valkyrie": "unit\\terran\\bomber.grp",
    "spider": "unit\\terran\\Spider.grp",
    "lurk_egg": "unit\\zerg\\LurkEgg.grp",
}

CELL = int(os.environ.get("CELL", "200"))
PERROW = int(os.environ.get("PERROW", "8"))
LABW = int(os.environ.get("LABW", "180"))
DIR = int(os.environ.get("DIR", "4"))
NB = int(os.environ.get("NB", "8"))


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def canvas(f, mw, mh):
    im = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        ty = y + f["y"]
        if not (0 <= ty < mh):
            continue
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v == 255:
                continue
            tx = x + f["x"]
            if 0 <= tx < mw:
                px[tx, ty] = PAL[v] + (255,)
    return im


keys = sys.argv[1:] or ["marine", "ultra", "queen"]
rows = (NB + PERROW - 1) // PERROW
W = LABW + PERROW * CELL
H = 22 + rows * CELL * len(keys)
img = Image.new("RGBA", (W, H), (16, 16, 22, 255))
dr = ImageDraw.Draw(img)
for r, key in enumerate(keys):
    res = load(PATHS[key])
    base_y = 22 + r * rows * CELL
    if res is None:
        dr.text((5, base_y + 6), "%s MISS" % key, fill=(255, 120, 120, 255))
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    dr.text((5, base_y + 6), "%s  blocks=%d\n%dx%d" % (key, nb, mw, mh),
            fill=(255, 235, 140, 255))
    for b in range(min(nb, NB)):
        nfr = min(17, len(frames) - b * 17)
        im = canvas(frames[b * 17 + DIR], mw, mh)
        sc = min((CELL - 4) / max(1, mw), (CELL - 4) / max(1, mh))
        im = im.resize((max(1, int(mw * sc)), max(1, int(mh * sc))), Image.NEAREST)
        ox = LABW + (b % PERROW) * CELL
        oy = base_y + (b // PERROW) * CELL
        img.paste(im, (ox + (CELL - im.width) // 2,
                       oy + (CELL - im.height) // 2), im)
        dr.text((ox + 4, oy + 2), "b%d" % b,
                fill=(140, 220, 255, 255) if nfr == 17 else (255, 150, 110, 255))
p = os.path.join(OUT, "page_%s_d%d.png" % ("_".join(keys[:3]), DIR))
img.save(p)
print("->", p, img.size)
