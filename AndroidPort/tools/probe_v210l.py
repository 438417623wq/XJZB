"""v2.10 probe 12: locate the walk->attack block boundary numerically.

For each unit, take every block's dir-8 frame (and dir 0/4/12 for robustness),
build a silhouette mask, and print the XOR-difference between consecutive
blocks. A walk cycle moves smoothly (small diffs); the first attack block is a
new action (large diff), so the boundary shows up as a spike. Calibrated on
marine (known walk=[0,1,2], attack=3) and SCV (walk=[0,1], attack=2).
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

CASES = [
    ("scv", "unit\\terran\\SCV.grp"),
    ("marine", "unit\\terran\\marine.grp"),
    ("firebat", "unit\\terran\\firebat.grp"),
    ("zergling", "unit\\zerg\\zergling.grp"),
    ("hydra", "unit\\zerg\\hydra.grp"),
    ("muta", "unit\\zerg\\mutalid.grp"),
    ("drone", "unit\\zerg\\drone.grp"),
    ("probe", "unit\\protoss\\probe.grp"),
    ("zealot", "unit\\protoss\\zealot.grp"),
    ("dragoon", "unit\\protoss\\dragoon.grp"),
    ("templar", "unit\\protoss\\templar.grp"),
    ("dtemplar", "unit\\protoss\\dtemplar.grp"),
    ("archon", "unit\\protoss\\archon.grp"),
    ("reaver", "unit\\protoss\\trilob.grp"),
    ("scout", "unit\\protoss\\scout.grp"),
    ("arbiter", "unit\\protoss\\arbiter.grp"),
    ("corsair", "unit\\protoss\\corsair.grp"),
    ("carrier", "unit\\protoss\\carrier.grp"),
]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def mask(f, size=48):
    """Silhouette mask of a frame, scaled into a size x size box, centred."""
    src = f["px"]
    w, h = f["w"], f["h"]
    m = [[0] * size for _ in range(size)]
    # bounding box of opaque pixels
    xs, ys = [], []
    for y in range(h):
        base = y * w
        for x in range(w):
            if src[base + x] != 255:
                xs.append(x)
                ys.append(y)
    if not xs:
        return m
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    sc = min(size / float(bw), size / float(bh))
    ox = (size - bw * sc) / 2.0
    oy = (size - bh * sc) / 2.0
    for y in range(y0, y1 + 1):
        base = y * w
        for x in range(x0, x1 + 1):
            if src[base + x] == 255:
                continue
            tx = int((x - x0) * sc + ox)
            ty = int((y - y0) * sc + oy)
            if 0 <= tx < size and 0 <= ty < size:
                m[ty][tx] = 1
    return m


def diff(a, b):
    n = 0
    for y in range(len(a)):
        for x in range(len(a)):
            if a[y][x] != b[y][x]:
                n += 1
    return n


def px_count(m):
    return sum(sum(r) for r in m)


print("%-9s %-4s %s" % ("unit", "n", "per-block dir8/4/12/0 mask XOR to next block"))
for name, path in CASES:
    r = load(path)
    if r is None:
        print("%-9s MISS" % name)
        continue
    frames, mw, mh = r
    n = len(frames)
    nb = n // 17
    masks = []
    for b in range(nb):
        ms = []
        for dd in (8, 4, 12, 0):
            fi = b * 17 + dd
            ms.append(mask(frames[fi]))
        masks.append(ms)
    row = []
    for b in range(nb - 1):
        d = sum(diff(masks[b][k], masks[b + 1][k]) for k in range(4))
        row.append("%d:%d" % (b, d))
    px = [px_count(masks[b][0]) for b in range(nb)]
    print("%-9s %-4d %s" % (name, n, " ".join(row)))
    print("%-9s %-4s px(b0..)=%s" % ("", "", " ".join(str(p) for p in px)))
