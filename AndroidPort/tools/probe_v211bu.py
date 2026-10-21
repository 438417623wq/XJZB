"""v2.11: ONE image, every block of every unit, one row per unit.

Includes the known rulers (marine walk=3, zergling walk=3, hydra walk=2,
zealot walk=5, dragoon walk=8) so the eye can be calibrated on the same page,
then the batch-B units whose walk length is still unconfirmed.

The body stays put (no crop) and only the limbs swing, so the walk cycle is
readable: the walk ends at the first block whose pose equals block 0.
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

CELL = int(os.environ.get("CELL", "150"))
LABW = int(os.environ.get("LABW", "170"))
DIR = int(os.environ.get("DIR", "4"))
CELLH = int(os.environ.get("CELLH", "0")) or CELL
ROW = CELLH


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


wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

keys = sys.argv[1:] or list(PATHS)
NBMAX = int(os.environ.get("NBMAX", "20"))
W = LABW + NBMAX * CELL
H = 26 * len(keys)
img = Image.new("RGBA", (W, H), (16, 16, 22, 255))
dr = ImageDraw.Draw(img)
for r, key in enumerate(keys):
    res = load(PATHS[key])
    if res is None:
        dr.text((5, r * 26 + 6), "%s MISS" % key, fill=(255, 120, 120, 255))
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    dr.text((5, r * 26 + 6), "%s  blocks=%d  %dx%d"
            % (key, nb, mw, mh), fill=(255, 235, 140, 255))
    for b in range(min(nb, NBMAX)):
        nfr = min(17, len(frames) - b * 17)
        im = canvas(frames[b * 17 + DIR], mw, mh)
        sc = min((CELL - 4) / max(1, mw), (CELLH - 4) / max(1, mh))
        im = im.resize((max(1, int(mw * sc)), max(1, int(mh * sc))), Image.NEAREST)
        ox = LABW + b * CELL
        oy = r * 26
        img.paste(im, (ox + (CELL - im.width) // 2,
                       oy + (26 - im.height) // 2), im)
        dr.text((ox + 2, oy + 1), "b%d" % b,
                fill=(140, 220, 255, 255) if nfr == 17 else (255, 150, 110, 255))
p = os.path.join(OUT, "all_%s.png" % "_".join(keys[:4]))
img.save(p)
print("->", p, img.size)
