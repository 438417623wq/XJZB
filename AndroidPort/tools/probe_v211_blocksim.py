"""v2.11 batch B/C: block-vs-block similarity at MATCHED facings.

Within one block the 17 frames are the 17 facing directions, NOT an animation.
So a walk cycle shows up as: frame (b, d) differs from frame (b+1, d) -- the
same facing one animation step later -- and the cycle repeats, so an early
block matches a later one.

This probe prints, for each ordered block pair, the mean absolute per-pixel
palette-index difference over the union of the two frames, averaged across all
17 facings. Identical blocks -> 0.0. A live walk cycle -> the diagonal is 0 and
off-diagonal neighbours are small but non-zero, with a repeat further out.

Frames are compared on an absolute canvas keyed by (x, y), because two frames
of the same facing can carry different bounding boxes; comparing raw w*h
buffers would then report every pixel as different for no reason.

Usage: python probe_v211_blocksim.py <key>
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
    "ultra":      "unit\\zerg\\ultra.grp",
    "guardian":   "unit\\zerg\\guardian.grp",
    "defiler":    "unit\\zerg\\defiler.grp",
    "queen":      "unit\\zerg\\queen.grp",
    "lurker":     "unit\\zerg\\lurknorm.grp",
    "lurker_bur": "unit\\zerg\\lurkburr.grp",
    "devourer":   "unit\\zerg\\devour.grp",
    "broodling":  "unit\\zerg\\brood.grp",
    "lurk_egg":   "unit\\zerg\\LurkEgg.grp",
    "medic":      "unit\\terran\\medic.grp",
    "valkyrie":   "unit\\terran\\bomber.grp",
    "spider":     "unit\\terran\\Spider.grp",
    "marine":     "unit\\terran\\marine.grp",
    "zealot":     "unit\\protoss\\zealot.grp",
    "zergling":   "unit\\zerg\\zergling.grp",
    "hydra":      "unit\\zerg\\hydra.grp",
}


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def canvas(f):
    out = {}
    px, w, h = f["px"], f["w"], f["h"]
    xo, yo = f["x"], f["y"]
    for y in range(h):
        base = y * w
        for x in range(w):
            v = px[base + x]
            if v != 255:
                out[(xo + x, yo + y)] = v
    return out


def diff(a, b):
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    tot = 0
    for k in keys:
        va = a.get(k, 255)
        vb = b.get(k, 255)
        if va == 255 or vb == 255:
            tot += 255
        else:
            tot += abs(va - vb)
    return tot / len(keys)


key = sys.argv[1]
r = load(PATHS[key])
if r is None:
    print("MISS", key)
    sys.exit(1)
frames, mw, mh = r
n = len(frames)
blocks = (n + 16) // 17

cache = {}
for b in range(blocks):
    for d in range(17):
        fi = b * 17 + d
        if fi < n:
            cache[(b, d)] = canvas(frames[fi])

print("%s n=%d blocks=%d cell=%dx%d" % (key, n, blocks, mw, mh))
print("mean |dIndex| across 17 facings; rows=b, cols=b'")
print("      " + "".join("%7d" % b for b in range(blocks)))
for b in range(blocks):
    row = "b%-3d " % b
    for bb in range(blocks):
        vals = [diff(cache[(b, d)], cache[(bb, d)])
                for d in range(17) if (b, d) in cache and (bb, d) in cache]
        row += "%7.1f" % (sum(vals) / len(vals)) if vals else "     --"
    print(row)

print()
print("neighbour step (b -> b+1, same facing) and the block it most resembles:")
for b in range(blocks):
    nb = [diff(cache[(b, d)], cache[(b + 1, d)])
          for d in range(17) if (b, d) in cache and (b + 1, d) in cache]
    nbs = "%7.1f" % (sum(nb) / len(nb)) if nb else "     --"
    best = None
    for bb in range(blocks):
        if bb == b:
            continue
        vals = [diff(cache[(b, d)], cache[(bb, d)])
                for d in range(17) if (b, d) in cache and (bb, d) in cache]
        if vals:
            m = sum(vals) / len(vals)
            if best is None or m < best[1]:
                best = (bb, m)
    print("  b%-2d -> b%-2d step=%s   closest=b%s (%.1f)"
          % (b, b + 1, nbs, best[0] if best else "-", best[1] if best else -1))
