"""v2.11: for one GRP, print the block-to-block distance matrix (dir 0 only).

A walk cycle of W frames makes d(b, b+W) a local minimum across the walk range.
Printed as a compact integer matrix so the seam can be read by eye.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

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
    "marine": "unit\\terran\\marine.grp",
    "zergling": "unit\\zerg\\zergling.grp",
    "hydra": "unit\\zerg\\hydra.grp",
    "zealot": "unit\\protoss\\zealot.grp",
    "dragoon": "unit\\protoss\\dragoon.grp",
}


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def plane(f, mw, mh):
    """Dense mw*mh byte plane of palette indices (255 = transparent)."""
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


def dist(a, b):
    d = 0
    for x, y in zip(a, b):
        if x == 255 and y == 255:
            continue
        if x == 255 or y == 255:
            d += 200
        else:
            d += abs(x - y)
    return d


for key in sys.argv[1:]:
    res = load(PATHS[key])
    if res is None:
        print("MISS", key)
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    P = [plane(frames[b * 17], mw, mh) for b in range(nb)]
    print()
    print("=== %s  frames=%d blocks=%d cell=%dx%d ===" % (key, len(frames), nb, mw, mh))
    print("d(b, b0) per block:")
    line = []
    for b in range(nb):
        line.append("b%d=%d" % (b, dist(P[b], P[0]) // 100))
    print("  " + "  ".join(line))
    print("d(b, b-W) matrix (rows=b, cols=W=1..min(10,nb-1)); . = self")
    hdr = "  b   " + "".join("%6d" % w for w in range(1, min(11, nb)))
    print(hdr)
    for b in range(nb):
        cells = []
        for w in range(1, min(11, nb)):
            if b - w < 0:
                cells.append("     .")
            else:
                cells.append("%6d" % (dist(P[b], P[b - w]) // 100))
        print("  %-4d%s" % (b, "".join(cells)))
