"""v2.11 calibration: per-block pixel census for the units whose layout the
shipped pipeline already relies on.

probe_v211a.py prints the new units' blocks; this prints the KNOWN ones, so the
new numbers can be read against a ruler instead of in isolation. The question
being answered is narrow and practical: for each unit that already renders
correctly, which block indices does manifest.txt use for walk, and which for
attack?

A block's frame count is also a reliable tell. Every walk block is a full 17
directions; a death block is short (7-12) because it does not need a facing per
direction.
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


def load(p):
    for ar in (PT, SD, BD):
        if ar.has(p):
            d, g = ar.read_with_gaps(p)
            return grpm.decode_grp(d, g)
    return None


def pxcount(f):
    n = 0
    for v in f["px"]:
        if v != 255:
            n += 1
    return n


KNOWN = [
    ("scv",      "unit\\terran\\SCV.grp"),
    ("marine",   "unit\\terran\\marine.grp"),
    ("firebat",  "unit\\terran\\firebat.grp"),
    ("vulture",  "unit\\terran\\Vulture.grp"),
    ("tank",     "unit\\terran\\tank.grp"),
    ("zergling", "unit\\zerg\\zergling.grp"),
    ("hydra",    "unit\\zerg\\hydra.grp"),
    ("muta",     "unit\\zerg\\mutalid.grp"),
    ("drone",    "unit\\zerg\\drone.grp"),
    ("over",     "unit\\zerg\\overlord.grp"),
    ("ghost",    "unit\\terran\\ghost.grp"),
    ("wraith",   "unit\\terran\\phoenix.grp"),
]

for key, path in KNOWN:
    r = load(path)
    if r is None:
        print("MISS", key)
        continue
    frames, mw, mh = r
    n = len(frames)
    blocks = (n + 16) // 17
    print("%-10s n=%-4d blocks=%-2d cell=%dx%d" % (key, n, blocks, mw, mh))
    for b in range(blocks):
        lo, hi = b * 17, min((b + 1) * 17, n)
        pcs = [pxcount(frames[i]) for i in range(lo, hi)]
        print("  b%-2d len=%-2d px=%4d..%4d" % (b, hi - lo, min(pcs), max(pcs)))
