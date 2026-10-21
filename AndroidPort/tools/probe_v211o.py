"""v2.11: exact pixel comparison of block b against block 0, direction by
direction. Answers one question only: which blocks re-occupy the pose of
block 0 (i.e. belong to the same repeating animation as block 0) and which
are novel poses.

The numeric novelty probe (probe_v211h/m) failed on the walk/attack seam
because a walk cycle need not return to block 0 within one period. This one is
much weaker on purpose and therefore trustworthy: it reports raw pixel
inequality counts, no thresholds, no clustering. If block 3 has 0 differing
pixels from block 0 in every direction, it IS block 0.

Usage: python probe_v211o.py <key> [key...]
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
    "lurk_egg": "unit\\zerg\\LurkEgg.grp",
    "medic": "unit\\terran\\medic.grp",
    "valkyrie": "unit\\terran\\bomber.grp",
    "spider": "unit\\terran\\Spider.grp",
    # controls whose layout manifest.txt already proves
    "scv": "unit\\terran\\scv.grp",
    "marine": "unit\\terran\\marine.grp",
    "zergling": "unit\\zerg\\zergling.grp",
    "hydra": "unit\\zerg\\hydra.grp",
    "muta": "unit\\zerg\\mutalid.grp",
    "zealot": "unit\\protoss\\zealot.grp",
    "dragoon": "unit\\protoss\\dragoon.grp",
    "templar": "unit\\protoss\\templar.grp",
}


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def mask(f):
    """Set of (x, y) covered by non-transparent pixels, plus the pixel ids."""
    w, h = f["w"], f["h"]
    src = f["px"]
    return {(x, y): src[y * w + x]
            for y in range(h) for x in range(w)
            if src[y * w + x] != 255}


def diff_count(a, b):
    """Pixels that differ in either coverage or palette index."""
    if a is None or b is None:
        return -1
    return len(set(a.items()) ^ set(b.items()))


for key in sys.argv[1:]:
    r = load(PATHS[key])
    if r is None:
        print("MISS", key)
        continue
    frames, mw, mh = r
    n = len(frames)
    nb = (n + 16) // 17
    b0 = [mask(frames[d]) if d < n else None for d in range(17)]
    b0_area = sum(len(m) for m in b0 if m)
    print("=== %s frames=%d blocks=%d cell=%dx%d  block0 area=%d"
          % (key, n, nb, mw, mh, b0_area))
    for b in range(1, nb):
        tot = 0
        worst = 0
        for d in range(17):
            i = b * 17 + d
            if i >= n:
                break
            c = diff_count(mask(frames[i]), b0[d])
            tot += c
            worst = max(worst, c)
        # fraction of block 0's pixels that block b changes, averaged over dirs
        pct = 100.0 * tot / max(1, b0_area * min(17, n - b * 17))
        print("   b%-3d vs b0: diff=%-8d worst_dir=%-7d changed=%.1f%%"
              % (b, tot, worst, pct))
