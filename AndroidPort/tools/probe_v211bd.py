"""v2.11: find the walk->attack seam from the sprite's bounding box and centroid.

Rationale: during a walk cycle a unit's silhouette stays inside roughly the same
box and its centre of mass stays put, because the feet stay on the ground. An
attack pose extends a weapon (a bigger box, a shifted centroid); a death pose
collapses (a smaller box, a much lower centroid). So the seam should show up as
a step in these per-block statistics.

Statistics per block, averaged over the 17 directions, in ABSOLUTE sprite
coordinates (frame x/y offsets added in):
    w, h     mean bounding-box size
    cx, cy   mean centroid
    area     mean opaque pixel count

Validated on the five units whose walk length is already fixed in the shipped
manifest (marine 3, zergling 3, hydra 2, zealot 5, dragoon 8).

Usage: python probe_v211bd.py
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


def stats(f):
    """Absolute bbox and centroid of one frame."""
    sx = sy = n = 0
    minx = miny = 10 ** 9
    maxx = maxy = -10 ** 9
    px = f["px"]
    for y in range(f["h"]):
        src = y * f["w"]
        ay = y + f["y"]
        for x in range(f["w"]):
            if px[src + x] != 255:
                ax = x + f["x"]
                sx += ax
                sy += ay
                n += 1
                if ax < minx:
                    minx = ax
                if ax > maxx:
                    maxx = ax
                if ay < miny:
                    miny = ay
                if ay > maxy:
                    maxy = ay
    if n == 0:
        return None
    return (maxx - minx + 1, maxy - miny + 1, sx / n, sy / n, n)


def analyse(key, path, truth=None):
    r = load(path)
    if r is None:
        print("MISS", key)
        return
    frames, mw, mh = r
    nb = len(frames) // 17
    rows = []
    for b in range(nb):
        acc = [0.0] * 5
        cnt = 0
        for d in range(17):
            i = b * 17 + d
            if i >= len(frames):
                break
            s = stats(frames[i])
            if s is None:
                continue
            for k in range(5):
                acc[k] += s[k]
            cnt += 1
        rows.append([v / max(1, cnt) for v in acc])
    print("== %s blocks=%d%s" % (key, nb,
                                 "  TRUTH walk=%d" % truth if truth else ""))
    print("    b     w      h      cx      cy     area   | dw     dh     dcx    dcy")
    for b in range(nb):
        w, h, cx, cy, a = rows[b]
        if b == 0:
            dw = dh = dcx = dcy = 0.0
        else:
            dw = w - rows[b - 1][0]
            dh = h - rows[b - 1][1]
            dcx = cx - rows[b - 1][2]
            dcy = cy - rows[b - 1][3]
        mark = "  <== SEAM" if truth is not None and b == truth else ""
        print("  %3d %6.1f %6.1f %7.1f %7.1f %8.0f   | %+6.1f %+6.1f %+6.1f %+6.1f%s"
              % (b, w, h, cx, cy, a, dw, dh, dcx, dcy, mark))
    print()


for key, path, truth in RULERS:
    analyse(key, path, truth)
for key, path in OPEN:
    analyse(key, path)
