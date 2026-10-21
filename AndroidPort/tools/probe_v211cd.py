"""v2.11: per-block ANCHOR and ground-contact analysis (the signal that works).

Every GRP frame carries its own (x, y) anchor: the offset from the sprite's
anchor point (the point that sits on the ground / at the unit's position). For a
walk cycle the FEET stay planted, so the bottom edge  y + h  stays put; when the
unit rears up to attack (or falls over dying) the bottom edge moves. This is a
different measurement from probe_v211cc, which only looked at the frame's own
tight box size and threw the anchor away.

Calibrated on the batch-A rulers, whose walk lengths are known:
    marine 3, zergling 3, hydra 2, zealot 5, dragoon 8.

Usage: python probe_v211cd.py <key> [key ...]
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
    "marine": "unit\\terran\\marine.grp",
    "zergling": "unit\\zerg\\zergling.grp",
    "hydra": "unit\\zerg\\hydra.grp",
    "zealot": "unit\\protoss\\zealot.grp",
    "dragoon": "unit\\protoss\\dragoon.grp",
    "ultra": "unit\\zerg\\ultra.grp",
    "queen": "unit\\zerg\\queen.grp",
    "defiler": "unit\\zerg\\defiler.grp",
    "guardian": "unit\\zerg\\guardian.grp",
    "devourer": "unit\\zerg\\devour.grp",
    "lurker": "unit\\zerg\\lurknorm.grp",
    "lurker_bur": "unit\\zerg\\lurkburr.grp",
    "broodling": "unit\\zerg\\brood.grp",
    "medic": "unit\\terran\\medic.grp",
    "valkyrie": "unit\\terran\\bomber.grp",
    "spider": "unit\\terran\\Spider.grp",
    "lurk_egg": "unit\\zerg\\LurkEgg.grp",
}


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def stat(frames, idx):
    """(mean x, mean y, mean x+w, mean y+h, mean w, mean h) over the 17 dirs."""
    xs = ys = rs = bs = ws = hs = 0.0
    for d in range(17):
        f = frames[idx + d]
        xs += f["x"]
        ys += f["y"]
        ws += f["w"]
        hs += f["h"]
        rs += f["x"] + f["w"]
        bs += f["y"] + f["h"]
    return (xs / 17.0, ys / 17.0, rs / 17.0, bs / 17.0, ws / 17.0, hs / 17.0)


for key in sys.argv[1:]:
    res = load(PATHS[key])
    if res is None:
        print("MISS", key)
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    print()
    print("=== %s blocks=%d cell=%dx%d frames=%d ===" % (key, nb, mw, mh, len(frames)))
    print("  b    n   anchorX anchorY  right  bottom   w      h     dBot   dRight")
    prev = None
    for b in range(nb):
        nfr = min(17, len(frames) - b * 17)
        if nfr < 17:
            print("  b%-3d %-3d  --- partial block (n<17) ---" % (b, nfr))
            continue
        ax, ay, r, bo, w, h = stat(frames, b * 17)
        if prev is None:
            print("  b%-3d %-3d %7.1f %7.1f %6.1f %7.1f %6.1f %6.1f      -      -"
                  % (b, nfr, ax, ay, r, bo, w, h))
        else:
            print("  b%-3d %-3d %7.1f %7.1f %6.1f %7.1f %6.1f %6.1f %+6.1f %+6.1f"
                  % (b, nfr, ax, ay, r, bo, w, h, bo - prev[0], r - prev[1]))
        prev = (bo, r)
