"""v2.11: find the walk-cycle length by LOOP CLOSURE.

The walk animation is a cycle: after the last walk block the animation wraps
back to block 0. So for the correct walk length W the "closure difference"
    closure(W) = diff(block W-1, block 0)
should be no larger than the differences between consecutive blocks INSIDE the
cycle,
    inner(W)   = mean(diff(block b, block b+1) for b in 0..W-2)
If instead W is too long the closure pairs a walk pose with an attack or death
pose and the ratio blows up.

score(W) = closure(W) / max(inner(W), eps)   -- the correct W is the argmin.

Validated against the five units whose walk length is already fixed in the
shipped manifest:
    marine 3, zergling 3, hydra 2, zealot 5, dragoon 8

Usage: python probe_v211az.py [maxW]
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

MAXW = int(sys.argv[1]) if len(sys.argv) > 1 else 9


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def block_profile(frames, b, mw, mh):
    """Sum the alpha masks of the 17 directions of block b."""
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


def diff(a, c):
    n = len(a)
    return sum(abs(a[i] - c[i]) for i in range(n)) / (17.0 * n)


def analyse(key, path, truth=None):
    r = load(path)
    if r is None:
        print("MISS", key)
        return
    frames, mw, mh = r
    nb = len(frames) // 17
    prof = [block_profile(frames, b, mw, mh) for b in range(nb)]
    adj = [diff(prof[b], prof[b + 1]) for b in range(nb - 1)]
    scores = []
    for W in range(2, min(MAXW, nb - 1) + 1):
        clo = diff(prof[W - 1], prof[0])
        inner = sum(adj[:W - 1]) / (W - 1)
        scores.append((clo / max(inner, 1e-9), W))
    scores.sort()
    rank = " ".join("%d:%.2f" % (w, s) for s, w in scores)
    best = scores[0][1]
    tag = ""
    if truth is not None:
        pos = [i for i, (s, w) in enumerate(scores) if w == truth]
        tag = "  TRUTH=%d rank=%s" % (truth, pos[0] + 1 if pos else ">%d" % len(scores))
    print("%-11s blocks=%-3d best=%-2d %s%s" % (key, nb, best, rank, tag))


print("--- rulers (truth known) ---")
for key, path, truth in RULERS:
    analyse(key, path, truth)
print("--- batch B ---")
for key, path in OPEN:
    analyse(key, path)
