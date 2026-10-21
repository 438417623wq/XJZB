"""v2.11: find the walk length by CYCLE RETURN.

A walk animation is a loop, so block W (the first block after the cycle) should
resemble block 0 more than a random later block does. This prints, for every b,
the distance between block b and block 0, and marks local minima -- the first
convincing local minimum after b=0 is the cycle length.

Unlike probe_v211az.py (which normalised by the inner mean and failed), this
prints the RAW distance curve, so a weak but real dip is still visible.

Validated on the five units whose walk length is already in the shipped
manifest: marine 3, zergling 3, hydra 2, zealot 5, dragoon 8.

Usage: python probe_v211bg.py
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

RULERS = [
    ("marine", "unit\\terran\\marine.grp", 3),
    ("zergling", "unit\\zerg\\zergling.grp", 3),
    ("hydra", "unit\\zerg\\hydra.grp", 2),
    ("zealot", "unit\\protoss\\zealot.grp", 5),
    ("dragoon", "unit\\protoss\\dragoon.grp", 8),
]
OPEN = [
    ("ultra", "unit\\zerg\\ultra.grp"),
    ("queen", "unit\\zerg\\queen.grp"),
    ("defiler", "unit\\zerg\\defiler.grp"),
    ("guardian", "unit\\zerg\\guardian.grp"),
    ("devourer", "unit\\zerg\\devour.grp"),
    ("lurker", "unit\\zerg\\lurknorm.grp"),
    ("lurker_bur", "unit\\zerg\\lurkburr.grp"),
    ("broodling", "unit\\zerg\\brood.grp"),
    ("medic", "unit\\terran\\medic.grp"),
]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def prof(frames, b, mw, mh):
    acc = [0] * (mw * mh)
    for d in range(17):
        i = b * 17 + d
        if i >= len(frames):
            break
        f = frames[i]
        px = f["px"]
        for y in range(f["h"]):
            src = y * f["w"]
            dst = (y + f["y"]) * mw + f["x"]
            for x in range(f["w"]):
                if px[src + x] != 255:
                    acc[dst + x] += 1
    return acc


def dist(a, c):
    n = len(a)
    return sum(abs(a[i] - c[i]) for i in range(n)) / (17.0 * n)


def analyse(key, path, truth=None):
    r = load(path)
    if r is None:
        print("MISS", key)
        return
    frames, mw, mh = r
    nb = len(frames) // 17
    pr = [prof(frames, b, mw, mh) for b in range(nb)]
    d0 = [dist(pr[b], pr[0]) for b in range(nb)]
    # local minima
    mins = [b for b in range(1, nb - 1)
            if d0[b] < d0[b - 1] and d0[b] <= d0[b + 1]]
    line = " ".join("%d:%.3f%s" % (b, d0[b], "*" if b in mins else "")
                    for b in range(1, min(nb, 12)))
    tag = ""
    if truth is not None:
        tag = "  TRUTH=%d" % truth
        if truth < len(d0):
            rank = sorted(range(1, nb), key=lambda b: d0[b]).index(truth) + 1
            tag += " rank=%d/%d" % (rank, nb - 1)
    print("%-11s nb=%-3d%s\n     %s\n     minima=%s" % (key, nb, tag, line, mins))


print("--- rulers ---")
for key, path, truth in RULERS:
    analyse(key, path, truth)
print("--- batch B ---")
for key, path in OPEN:
    analyse(key, path)
