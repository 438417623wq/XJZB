"""v2.11 batch B/C: silhouette IoU between blocks at matched facings.

probe_v211_blocksim.py showed that a raw palette-index difference is dominated
by limb movement -- on the marine (walk=[0,1,2], attack=3) b2 vs b3 scores 37.5
while the walk neighbours b0 vs b1 score 64.4. So palette distance cannot tell
walk from attack. What separates them is whether the BODY SILHOUETTE changes:

  * two walk blocks = same body in the same place, limbs moved a little
    -> high mask IoU (typically > 0.80);
  * an attack block = a pose the unit never returns to -> low IoU against
    everything (muzzle flash, spines thrust, body lowered);
  * a death block -> very low IoU against everything.

Mask = the set of non-transparent pixels of the frame, keyed on the absolute
(x, y) canvas so two frames of one facing line up.

Usage: python probe_v211_sil.py <key>
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


def mask(f):
    out = set()
    px, w, h = f["px"], f["w"], f["h"]
    xo, yo = f["x"], f["y"]
    for y in range(h):
        base = y * w
        for x in range(w):
            if px[base + x] != 255:
                out.add((xo + x, yo + y))
    return out


def iou(a, b):
    if not a and not b:
        return 1.0
    u = len(a | b)
    return len(a & b) / u if u else 1.0


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
            cache[(b, d)] = mask(frames[fi])

print("%s n=%d blocks=%d cell=%dx%d" % (key, n, blocks, mw, mh))
print("mean mask IoU across 17 facings; rows=b, cols=b'")
print("      " + "".join("%6d" % b for b in range(blocks)))
for b in range(blocks):
    row = "b%-3d " % b
    for bb in range(blocks):
        vals = [iou(cache[(b, d)], cache[(bb, d)])
                for d in range(17) if (b, d) in cache and (bb, d) in cache]
        row += "%6.2f" % (sum(vals) / len(vals)) if vals else "    --"
    print(row)

print()
print("per-block mean IoU against all OTHER blocks (low = pose break):")
for b in range(blocks):
    vals = []
    for bb in range(blocks):
        if bb == b:
            continue
        v = [iou(cache[(b, d)], cache[(bb, d)])
             for d in range(17) if (b, d) in cache and (bb, d) in cache]
        if v:
            vals.append(sum(v) / len(v))
    print("  b%-2d meanIoU=%.3f  minIoU=%.3f (vs b%d)"
          % (b, sum(vals) / len(vals), min(vals), vals.index(min(vals)) + (1 if vals.index(min(vals)) >= b else 0)))
