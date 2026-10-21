"""v2.11: render every 17-frame block of a unit GRP as a labelled contact sheet.

One row per block, 17 columns (one per direction). The block index is stamped on
the left of each row. This is the sheet that settles walk / attack / death seams
by eye -- the numeric detectors (probe_v211h/m/o) could not find the
walk/attack seam at all, only the red-gore death seam (probe_v211p) is numeric.

Usage: python probe_v211aj.py <key> [key...]
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
    "lurk_egg": "unit\\zerg\\LurkEgg.grp",
    "medic": "unit\\terran\\medic.grp",
    "valkyrie": "unit\\terran\\bomber.grp",
    "spider": "unit\\terran\\Spider.grp",
}


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


SCALE = int(os.environ.get("SCALE", "3"))
LABEL = 34

for key in sys.argv[1:]:
    r = load(PATHS[key])
    if r is None:
        print("MISS", key)
        continue
    frames, mw, mh = r
    n = len(frames)
    nb = (n + 16) // 17
    cw, ch = mw * SCALE, mh * SCALE
    img = Image.new("RGBA", (LABEL + 17 * cw, nb * ch), (24, 24, 32, 255))
    dr = ImageDraw.Draw(img)
    for b in range(nb):
        dr.text((4, b * ch + 4), "b%d" % b, fill=(255, 220, 120, 255))
        for d in range(17):
            fi = b * 17 + d
            if fi >= n:
                break
            f = frames[fi]
            im = frame_image(f)
            if SCALE != 1:
                im = im.resize((f["w"] * SCALE, f["h"] * SCALE), Image.NEAREST)
            img.paste(im, (LABEL + d * cw + f["x"] * SCALE,
                           b * ch + f["y"] * SCALE), im)
    p = os.path.join(OUT, "%s_blocks.png" % key)
    img.save(p)
    print("%-12s frames=%-4d blocks=%-3d cell=%dx%d -> %s" % (key, n, nb, mw, mh, p))
