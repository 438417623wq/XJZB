"""v2.11: per-block bounding-box size and centroid, per direction.

Rationale (calibrated against the batch-A rulers): inside a walk cycle the
torso keeps a roughly constant bounding box and only the limbs swing, so the
box edges wander by a pixel or two. The FIRST block after the walk is the
attack, which changes the silhouette enough to move the box much further. On
the rulers this signal fires on marine b3, zealot b5 and dragoon b8 (3 of 5);
zergling and hydra need the picture instead.

Usage: python probe_v211cc.py <key> [key ...]
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


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def bbox(f):
    x0 = y0 = 1 << 30
    x1 = y1 = -1
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            if src[base + x] != 255:
                if x < x0:
                    x0 = x
                if x > x1:
                    x1 = x
                if y < y0:
                    y0 = y
                if y > y1:
                    y1 = y
    if x1 < 0:
        return None
    return (x0, y0, x1, y1, x1 - x0 + 1, y1 - y0 + 1)


for key in sys.argv[1:]:
    res = load(PATHS[key])
    if res is None:
        print("MISS", key)
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    print()
    print("=== %s blocks=%d cell=%dx%d frames=%d ===" % (key, nb, mw, mh, len(frames)))
    for d in (0, 4):
        print("  dir %d:  b :  x0  y0   w   h   dw   dh   dcx  dcy" % d)
        prev = None
        for b in range(nb):
            nfr = min(17, len(frames) - b * 17)
            bb = bbox(frames[b * 17 + d])
            if bb is None:
                print("    b%-3d EMPTY" % b)
                prev = None
                continue
            x0, y0, x1, y1, w, h = bb
            cx = (x0 + x1) / 2.0
            cy = (y0 + y1) / 2.0
            if prev is None:
                print("    b%-3d %4d %4d %4d %4d %s%s n=%d"
                      % (b, x0, y0, w, h, "   -    -", "", nfr))
            else:
                print("    b%-3d %4d %4d %4d %4d %+4d %+4d %+5.1f %+5.1f n=%d"
                      % (b, x0, y0, w, h, w - prev[0], h - prev[1],
                         cx - prev[2], cy - prev[3], nfr))
            prev = (w, h, cx, cy)
