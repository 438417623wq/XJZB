"""v2.11: calibrate the walk->attack seam detector on units whose layout is
ALREADY VERIFIED in the shipped manifest.

Ground truth from pipeline_sprites.py UNITS + ANIMS (block indices):
    marine   14 blocks  walk 0..2  attack 3  death 13 (last)
    zergling 18 blocks  walk 0..2  attack 3  death 17 (last)
    hydra    18 blocks  walk 0..1  attack 2  death 17 (last)
    zealot   14 blocks  walk 0..4  attack 5  death 13 (last)
    dragoon  25 blocks  walk 0..7  attack 8  death 24 (last)

The invariant across all five: the walk cycle starts at block 0, the attack is
the SINGLE block immediately after the walk, and the death is the LAST block.
So the only unknown for a new unit is the walk length W; attack = W, death =
last. This probe measures three candidate signals at every seam so we can see
which one actually peaks at the known W, then reuse that signal for batch B.

Signals, all averaged over the 17 directions:
  diff[b]  mean |px| difference between block b and block b+1
  cov[b]   1 - normalised overlap of the two blocks' alpha masks
  fill[b]  change in opaque-pixel count (an attack pose often adds a flash)

Usage: python probe_v211as.py
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

CAL = [
    ("marine",   "unit\\terran\\marine.grp",   3),
    ("zergling", "unit\\zerg\\zergling.grp",   3),
    ("hydra",    "unit\\zerg\\hydra.grp",      2),
    ("zealot",   "unit\\protoss\\zealot.grp",  5),
    ("dragoon",  "unit\\protoss\\dragoon.grp", 8),
]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def mask_of(f, mw, mh):
    """Return a (mw*mh) 0/1 mask and the opaque count for one frame."""
    m = [0] * (mw * mh)
    n = 0
    px = f["px"]
    for y in range(f["h"]):
        src = y * f["w"]
        dst = (y + f["y"]) * mw + f["x"]
        for x in range(f["w"]):
            if px[src + x] != 255:
                m[dst + x] = 1
                n += 1
    return m, n


for key, path, truth in CAL:
    r = load(path)
    if r is None:
        print("MISS", key)
        continue
    frames, mw, mh = r
    nb = len(frames) // 17
    masks, fills = [], []
    for b in range(nb):
        acc = [0] * (mw * mh)
        tot = 0
        for d in range(17):
            f = frames[b * 17 + d]
            m, n = mask_of(f, mw, mh)
            for i in range(mw * mh):
                acc[i] += m[i]
            tot += n
        masks.append(acc)
        fills.append(tot)
    # per-block alpha fraction (how many of the 17 dirs cover each pixel)
    norm = 17.0
    print("== %-9s blocks=%-3d TRUTH walk=0..%d attack=%d death=%d"
          % (key, nb, truth - 1, truth, nb - 1))
    hdr = "   b   diff%   cov%   fillDelta   marker"
    print(hdr)
    for b in range(nb - 1):
        a, c = masks[b], masks[b + 1]
        diff = sum(abs(a[i] - c[i]) for i in range(mw * mh)) / (norm * mw * mh)
        inter = sum(min(a[i], c[i]) for i in range(mw * mh))
        union = sum(max(a[i], c[i]) for i in range(mw * mh))
        cov = 1.0 - (inter / union if union else 0.0)
        fd = (fills[b + 1] - fills[b]) / max(1, fills[b])
        mark = ""
        if b == truth - 1:
            mark = "  <== TRUE walk->attack seam"
        if b == nb - 2:
            mark += "  [death]"
        print("  %3d  %6.2f  %6.2f   %+8.3f%s" % (b, diff * 100, cov * 100, fd, mark))
    print()
