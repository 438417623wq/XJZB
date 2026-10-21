"""v2.11 batch B/C: census the block structure of every new unit GRP.

Same idea as probe_v210o.py, which found the protoss walk/attack/death blocks:
render each 17-frame block's statistics and let the numbers -- not the file
names -- say which block is which.

The distinguishing signals in this pack, calibrated against the units whose
layout is already known (scv/marine/zergling walk first then attack; templar
and dtemplar reversed):

  * a WALK block has a moderate, roughly constant pixel count across all 17
    directions -- the unit is the same size in every facing.
  * an ATTACK block usually has a spike in bright/warm pixels (muzzle flash,
    projectile) in the frames facing the target, and the newest blocks in a
    Brood War GRP are often the ones with the extra effects.
  * a DEATH block is short (7-12 frames, so a partial block) and much brighter
    than its neighbours -- the blue/white shatter.

Printing (len, brightFrac, meanLum, meanPx) per block makes all three readable.
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
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def stats(f):
    """(bright fraction, mean luminance, pixel count)."""
    bright = lum = n = 0
    for v in f["px"]:
        if v == 255:
            continue
        r, g, b = PAL[v]
        n += 1
        lum += (r + g + b) / 3
        if r + g + b > 540:
            bright += 1
    if n == 0:
        return 0.0, 0.0, 0
    return bright / n, lum / n, n


WANT = [
    # ---- batch B: zerg
    ("ultra",       "unit\\zerg\\ultra.grp"),
    ("guardian",    "unit\\zerg\\guardian.grp"),
    ("defiler",     "unit\\zerg\\defiler.grp"),
    ("queen",       "unit\\zerg\\queen.grp"),
    ("lurker",      "unit\\zerg\\lurknorm.grp"),
    ("lurker_bur",  "unit\\zerg\\lurkburr.grp"),
    ("devourer",    "unit\\zerg\\devour.grp"),
    ("broodling",   "unit\\zerg\\brood.grp"),
    ("lurk_egg",    "unit\\zerg\\LurkEgg.grp"),
    # ---- batch C: terran
    ("medic",       "unit\\terran\\medic.grp"),
    ("valkyrie",    "unit\\terran\\bomber.grp"),
    ("spider",      "unit\\terran\\Spider.grp"),
]

for key, path in WANT:
    r = load(path)
    if r is None:
        print("MISS", key, path)
        continue
    frames, mw, mh = r
    n = len(frames)
    blocks = (n + 16) // 17
    print("%-12s n=%-4d blocks=%-2d cell=%dx%d" % (key, n, blocks, mw, mh))
    for b in range(blocks):
        lo, hi = b * 17, min((b + 1) * 17, n)
        vals = [stats(frames[i]) for i in range(lo, hi)]
        bavg = sum(v[0] for v in vals) / len(vals)
        bmax = max(v[0] for v in vals)
        lavg = sum(v[1] for v in vals) / len(vals)
        pavg = sum(v[2] for v in vals) / len(vals)
        pmin = min(v[2] for v in vals)
        pmax = max(v[2] for v in vals)
        print("  b%-2d len=%-2d bright=%.3f max=%.3f lum=%5.1f px=%4d..%4d"
              % (b, hi - lo, bavg, bmax, lavg, pmin, pmax))
