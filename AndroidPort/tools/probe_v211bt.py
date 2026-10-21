"""v2.11: find the walk-cycle length by RED/GREEN OVERLAY against block 0.

Each cell shows block 0 in the red channel and block b in the green channel.
Where the two poses coincide the pixels turn YELLOW. A block that is the same
pose as block 0 (i.e. b == W, one full cycle later) lights up solid yellow --
this is far more sensitive than looking at two pictures side by side.

Calibrated on marine, whose walk is known to be 3 blocks.
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
    "marine": "unit\\terran\\marine.grp",
    "scv": "unit\\terran\\SCV.grp",
    "zergling": "unit\\zerg\\zergling.grp",
    "hydra": "unit\\zerg\\hydra.grp",
    "zealot": "unit\\protoss\\zealot.grp",
    "dragoon": "unit\\protoss\\dragoon.grp",
    "templar": "unit\\protoss\\templar.grp",
}

CELL = int(os.environ.get("CELL", "150"))
PERROW = int(os.environ.get("PERROW", "8"))
LABW = int(os.environ.get("LABW", "70"))
DIR = int(os.environ.get("DIR", "0"))


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def plane(f, mw, mh):
    out = bytearray([255]) * (mw * mh)
    src = f["px"]
    for y in range(f["h"]):
        ty = y + f["y"]
        if not (0 <= ty < mh):
            continue
        base = y * f["w"]
        row = ty * mw
        for x in range(f["w"]):
            v = src[base + x]
            if v == 255:
                continue
            tx = x + f["x"]
            if 0 <= tx < mw:
                out[row + tx] = v
    return out


def overlay(a, b, mw, mh):
    """a -> red, b -> green; both -> yellow."""
    im = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
    px = im.load()
    for y in range(mh):
        for x in range(mw):
            i = y * mw + x
            u, v = a[i], b[i]
            if u == 255 and v == 255:
                continue
            if u != 255 and v != 255:
                px[x, y] = (255, 255, 0, 255)
            elif u != 255:
                px[x, y] = (235, 40, 40, 255)
            else:
                px[x, y] = (40, 235, 60, 255)
    return im


def score(a, b):
    """Fraction of block 0's opaque pixels that block b also covers."""
    both = only_a = only_b = 0
    for u, v in zip(a, b):
        if u != 255 and v != 255:
            both += 1
        elif u != 255:
            only_a += 1
        elif v != 255:
            only_b += 1
    if both + only_a == 0:
        return 0.0
    return both / float(both + only_a)


for key in sys.argv[1:]:
    res = load(PATHS[key])
    if res is None:
        print("MISS", key)
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    P = [plane(frames[b * 17 + DIR], mw, mh) for b in range(nb)]
    cov = [score(P[0], P[b]) for b in range(nb)]
    print()
    print("=== %s blocks=%d cell=%dx%d dir=%d ===" % (key, nb, mw, mh, DIR))
    print("  coverage of block0 by block b (1.000 = identical pose):")
    print("   " + "  ".join("b%d=%.2f" % (b, cov[b]) for b in range(nb)))
    best = sorted(range(1, nb), key=lambda b: -cov[b])[:4]
    print("   top matches: " + ", ".join("b%d(%.2f)" % (b, cov[b]) for b in best))

    rows = (nb + PERROW - 1) // PERROW
    W = LABW + PERROW * CELL
    H = 24 + rows * CELL
    img = Image.new("RGBA", (W, H), (16, 16, 22, 255))
    dr = ImageDraw.Draw(img)
    dr.text((5, 6), "%s dir=%d blocks=%d  RED=b0  GREEN=b  YELLOW=match"
            % (key, DIR, nb), fill=(255, 235, 140, 255))
    for b in range(nb):
        im = overlay(P[0], P[b], mw, mh)
        sc = min((CELL - 6) / max(1, mw), (CELL - 6) / max(1, mh))
        im = im.resize((max(1, int(mw * sc)), max(1, int(mh * sc))), Image.NEAREST)
        ox = LABW + (b % PERROW) * CELL
        oy = 24 + (b // PERROW) * CELL
        img.paste(im, (ox + (CELL - im.width) // 2,
                       oy + (CELL - im.height) // 2), im)
        dr.text((ox + 4, oy + 2), "b%d %.2f" % (b, cov[b]), fill=(200, 240, 255, 255))
    p = os.path.join(OUT, "ov_%s_d%d.png" % (key, DIR))
    img.save(p)
    print("->", p, img.size)
