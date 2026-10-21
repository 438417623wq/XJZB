"""v2.11: per-block contact sheet WITHOUT tight cropping.

Tight cropping destroys the one cue that makes a walk cycle readable: with the
anchor preserved the unit's body stays in place and the legs swing; tight-cropped
every block looks like a different picture simply because the crop box moved.

Draws, for each unit, every block at direction 0 (and direction 4 for a side-on
view) on a FIXED canvas the size of the GRP cell, so the pose change is the only
thing that varies.

Usage: python probe_v211bk.py <key> [key ...]
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
    "marine": "unit\\terran\\marine.grp",
    "scv": "unit\\terran\\SCV.grp",
    "zergling": "unit\\zerg\\zergling.grp",
    "hydra": "unit\\zerg\\hydra.grp",
    "zealot": "unit\\protoss\\zealot.grp",
    "dragoon": "unit\\protoss\\dragoon.grp",
}

CELL = int(os.environ.get("CELL", "150"))
PERROW = int(os.environ.get("PERROW", "8"))
LABW = int(os.environ.get("LABW", "60"))
DIRS = (0, 4)


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def canvas(f, mw, mh):
    """Place the frame on a fixed mw x mh canvas at its anchor (no cropping)."""
    im = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        ty = y + f["y"]
        if not (0 <= ty < mh):
            continue
        for x in range(f["w"]):
            v = src[base + x]
            if v == 255:
                continue
            tx = x + f["x"]
            if 0 <= tx < mw:
                px[tx, ty] = PAL[v] + (255,)
    return im


for key in sys.argv[1:]:
    res = load(PATHS[key])
    if res is None:
        print("MISS", key)
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    for d in DIRS:
        rows = (nb + PERROW - 1) // PERROW
        W = LABW + PERROW * CELL
        H = 24 + rows * CELL
        img = Image.new("RGBA", (W, H), (16, 16, 22, 255))
        dr = ImageDraw.Draw(img)
        dr.text((5, 6), "%s dir=%d blocks=%d cell=%dx%d  (NO crop: body stays put)"
                % (key, d, nb, mw, mh), fill=(255, 235, 140, 255))
        for b in range(nb):
            nfr = min(17, len(frames) - b * 17)
            im = canvas(frames[b * 17 + d], mw, mh)
            sc = min((CELL - 6) / max(1, mw), (CELL - 6) / max(1, mh))
            im = im.resize((max(1, int(mw * sc)), max(1, int(mh * sc))),
                           Image.NEAREST)
            ox = LABW + (b % PERROW) * CELL
            oy = 24 + (b // PERROW) * CELL
            img.paste(im, (ox + (CELL - im.width) // 2,
                           oy + (CELL - im.height) // 2), im)
            col = (140, 220, 255, 255) if nfr == 17 else (255, 150, 110, 255)
            dr.text((ox + 4, oy + 2), "b%d" % b, fill=col)
        p = os.path.join(OUT, "nc_%s_d%d.png" % (key, d))
        img.save(p)
        print("->", p, img.size)
