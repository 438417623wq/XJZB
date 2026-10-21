"""v2.11 batch B/C: numeric block-boundary finder.

Each block in a StarCraft GRP is 17 directions of ONE animation frame, so an
animation with K frames occupies K consecutive blocks. The walk cycle therefore
loops (block K looks like block 0) and the walk -> attack transition is a pose
jump. This prints, per block boundary, two distances so the jump is visible as
a number instead of being squinted at in a contact sheet:

    step  = mean abs pixel difference between block b-1 and block b
    loop  = mean abs pixel difference between block b and block 0

`step` spikes at a pose discontinuity (walk -> attack, attack -> death);
`loop` dips to a local minimum every time the walk cycle comes back around.

Calibrated on the units whose layout is already proven in manifest.txt:
    scv      walk=[0,1] atk=2
    marine   walk=[0,1,2] atk=3
    hydra    walk=[0,1] atk=2
    zergling walk=[0,1,2] atk=3

Usage: python probe_v211h.py [key ...]      (no args = the calibration set)
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
    # calibration: layouts already in manifest.txt
    "scv":        "unit\\terran\\SCV.grp",
    "marine":     "unit\\terran\\marine.grp",
    "firebat":    "unit\\terran\\firebat.grp",
    "tank":       "unit\\terran\\tank.grp",
    "zergling":   "unit\\zerg\\zergling.grp",
    "hydra":      "unit\\zerg\\hydra.grp",
    "muta":       "unit\\zerg\\mutalid.grp",
    "drone":      "unit\\zerg\\drone.grp",
    "ghost":      "unit\\terran\\ghost.grp",
    # protoss, verified by eye in v2.10
    "zealot":     "unit\\protoss\\zealot.grp",
    "dragoon":    "unit\\protoss\\dragoon.grp",
    "templar":    "unit\\protoss\\templar.grp",
    # batch B/C candidates
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
}

DEFAULT = ["scv", "marine", "hydra", "zergling", "muta", "drone", "ghost",
           "zealot", "dragoon", "templar"]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def silhouette(f):
    """Alpha mask of one frame: 1 where the GRP index is not the filler."""
    px = f["px"]
    w, h = f["w"], f["h"]
    return [0 if px[i] == 255 else 1 for i in range(w * h)], w, h


def diff(a, b):
    """Mean abs difference over the union of the two masks (0..255).

    Frames carry their own width/height and they legitimately differ between
    blocks (a walk frame and a muzzle-flash frame are not the same canvas), so
    both masks are top-left aligned into the larger canvas instead of bailing.
    """
    (pa, wa, ha) = a
    (pb, wb, hb) = b
    w = max(wa, wb)
    h = max(ha, hb)
    tot = 0
    cnt = 0
    for y in range(h):
        for x in range(w):
            va = pa[y * wa + x] if (x < wa and y < ha) else 0
            vb = pb[y * wb + x] if (x < wb and y < hb) else 0
            if va == 0 and vb == 0:
                continue
            tot += abs(va - vb) * 255
            cnt += 1
    return (tot / cnt) if cnt else 0.0


def block_mask(frames, b, dirs=(0, 4, 8, 12)):
    """Flatten a block's sampled directions into one comparison key."""
    out = []
    for d in dirs:
        fi = b * 17 + d
        if fi < len(frames):
            out.append(silhouette(frames[fi]))
    return out


def block_diff(frames, b, c, dirs=(0, 4, 8, 12)):
    mb = block_mask(frames, b, dirs)
    mc = block_mask(frames, c, dirs)
    vals = [diff(x, y) for x, y in zip(mb, mc)]
    vals = [v for v in vals if v >= 0]
    return sum(vals) / len(vals) if vals else -1.0


keys = sys.argv[1:] or DEFAULT
for key in keys:
    r = load(PATHS[key])
    if r is None:
        print("MISS", key)
        continue
    frames, mw, mh = r
    n = len(frames)
    blocks = (n + 16) // 17
    print("%s  n=%d blocks=%d cell=%dx%d" % (key, n, blocks, mw, mh))
    for b in range(blocks):
        fi = b * 17
        real = sum(1 for d in range(17) if fi + d < n)
        step = block_diff(frames, b - 1, b) if b > 0 else 0.0
        loop = block_diff(frames, b, 0) if b > 0 else 0.0
        print("  b%-3d dirs=%-3d step=%6.2f loop=%6.2f" % (b, real, step, loop))
