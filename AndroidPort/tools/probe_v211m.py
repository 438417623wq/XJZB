"""v2.11 block-layout periodicity probe (numeric aid to the rendered sheets).

Model being tested (the one the port uses): a GRP is a sequence of blocks of 17
frames, block = one animation step, frame inside a block = facing direction.
So a WALK cycle repeats: some late block matches an early one. An ATTACK block
is a pose the unit never returns to. A DEATH block is novel and (in this pack)
red.

For each block we build a feature vector = 17 directions x 24x24 grayscale
silhouette (luma of the palette colour, 0 where transparent), then print:
  * the full pairwise distance matrix (x1000) so a repeating cycle shows as
    near-zero off-diagonal entries, and
  * for each block the min distance to ANY EARLIER block, i.e. its novelty.
A low novelty on block i means block i re-occupies an earlier pose (cycle step);
a high novelty means a new pose (attack / death / idle).

Usage: python probe_v211m.py <key> [key...]
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

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
LUM = [0.30 * wpe[i * 4] + 0.59 * wpe[i * 4 + 1] + 0.11 * wpe[i * 4 + 2]
       for i in range(256)]

PATHS = {
    "ultra": "unit\\zerg\\ultra.grp",
    "queen": "unit\\zerg\\queen.grp",
    "defiler": "unit\\zerg\\defiler.grp",
    "guardian": "unit\\zerg\\guardian.grp",
    "devourer": "unit\\zerg\\devour.grp",
    "lurker": "unit\\zerg\\lurknorm.grp",
    "broodling": "unit\\zerg\\brood.grp",
    "lurk_egg": "unit\\zerg\\LurkEgg.grp",
    "medic": "unit\\terran\\medic.grp",
    "valkyrie": "unit\\terran\\bomber.grp",
    "spider": "unit\\terran\\Spider.grp",
    "marine": "unit\\terran\\marine.grp",
    "zealot": "unit\\protoss\\zealot.grp",
    "scv": "unit\\terran\\scv.grp",
    "zergling": "unit\\zerg\\zergling.grp",
    "hydra": "unit\\zerg\\hydra.grp",
    "tank": "unit\\terran\\tank.grp",
    "dragoon": "unit\\protoss\\dragoon.grp",
}

G = 24


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def cell_vec(f):
    """GxG grayscale of one frame, anchored at its own bbox top-left (so a
    translation-only difference still counts as different -- poses matter)."""
    w, h = f["w"], f["h"]
    src = f["px"]
    xs, ys = [], []
    for y in range(h):
        base = y * w
        for x in range(w):
            if src[base + x] != 255:
                xs.append(x)
                ys.append(y)
    if not xs:
        return [0.0] * (G * G)
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    bw, bh = max(1, x1 - x0 + 1), max(1, y1 - y0 + 1)
    out = [0.0] * (G * G)
    for gy in range(G):
        for gx in range(G):
            sx = x0 + (gx * bw) // G
            sy = y0 + (gy * bh) // G
            if sx <= x1 and sy <= y1 and src[sy * w + sx] != 255:
                out[gy * G + gx] = LUM[src[sy * w + sx]]
    return out


def block_vec(frames, b, ndir=17):
    # pad to a fixed ndir*G*G so the trailing partial block (ultra b15 has 10
    # frames) stays comparable with the full blocks.
    v = []
    for d in range(ndir):
        i = b * 17 + d
        v.extend(cell_vec(frames[i]) if i < len(frames) else [0.0] * (G * G))
    return v


def dist(a, b):
    s = 0.0
    for i in range(len(a)):
        t = a[i] - b[i]
        s += t * t
    return (s / max(1, len(a))) ** 0.5


for key in sys.argv[1:]:
    r = load(PATHS[key])
    if r is None:
        print("MISS", key)
        continue
    frames, mw, mh = r
    n = len(frames)
    nb = (n + 16) // 17
    vecs = [block_vec(frames, b) for b in range(nb)]
    print("=== %s  frames=%d blocks=%d cell=%dx%d" % (key, n, nb, mw, mh))
    counts = [min(17, n - b * 17) for b in range(nb)]
    print("   frames/block:", " ".join("%d:%d" % (b, counts[b]) for b in range(nb)))
    print("   dist matrix (x1000):")
    print("        " + " ".join("%5d" % b for b in range(nb)))
    for i in range(nb):
        row = " ".join("%5d" % int(round(dist(vecs[i], vecs[j]) * 1000))
                       for j in range(nb))
        print("   b%-4d %s" % (i, row))
    print("   novelty (min dist to any earlier block, x1000):")
    for i in range(nb):
        if i == 0:
            print("   b%-4d  -" % i)
            continue
        best = min((dist(vecs[i], vecs[j]), j) for j in range(i))
        print("   b%-4d  %5d   (closest earlier b%d)" % (i, int(best[0] * 1000), best[1]))
