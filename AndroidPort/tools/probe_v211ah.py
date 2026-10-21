"""v2.11 batch B: is arr\\images.dat keyed by units.dat id?

If it is, the four zerg building ids the plan could not place (135 hydralisk
den, 136 defiler mound, 137 greater spire, 139 evolution chamber, 140 ultralisk
cavern) can be read straight out of the file instead of guessed from art.

The test needs no format guesswork: take ~30 units whose units.dat id is certain
(Marine 0 -> marine.grp, Hatchery 131 -> hatchery.grp, ...), look up the
images.tbl index of that GRP, then scan every (stride, offset) and count how many
of the known pairs the file reproduces. A real id-keyed record table scores
almost all of them; noise scores a couple by chance.

Usage: python probe_v211ah.py
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))


def tbl(d):
    cnt = d[0] | (d[1] << 8)
    out = []
    for i in range(cnt):
        o = d[2 + i * 2] | (d[3 + i * 2] << 8)
        e = o
        while e < len(d) and d[e] != 0:
            e += 1
        out.append(d[o:e].decode("latin-1"))
    return out


sd_tbl = tbl(SD.read_with_gaps("arr\\images.tbl")[0])
bd_tbl = tbl(BD.read_with_gaps("arr\\images.tbl")[0])


def find_idx(name, table):
    """images.tbl index whose path ends with `name` (case-insensitive)."""
    n = name.lower()
    for i, v in enumerate(table):
        if v.lower().endswith(n):
            return i
    return None


# units.dat id -> GRP basename (certain)
KNOWN = [
    (0, "marine.grp"), (5, "tank.grp"), (7, "SCV.grp"), (8, "phoenix.grp"),
    (11, "dropship.grp"), (12, "BattleCr.grp"), (32, "firebat.grp"),
    (35, "larva.grp"), (37, "zergling.grp"), (38, "hydra.grp"),
    (39, "ultra.grp"), (40, "brood.grp"), (41, "drone.grp"),
    (42, "overlord.grp"), (43, "mutalid.grp"), (44, "guardian.grp"),
    (45, "queen.grp"), (46, "defiler.grp"),
    (131, "hatchery.grp"), (132, "Lair.grp"), (133, "Hive.grp"),
    (134, "NydusPit.grp"), (138, "nest.grp"), (141, "spire.grp"),
    (142, "Snakey.grp"), (143, "fcolony.grp"), (144, "RCluster.grp"),
    (146, "SColony.grp"), (149, "Extract.grp"), (150, "chrysal.grp"),
    (65, "zealot.grp"), (68, "archon.grp"), (72, "carrier.grp"),
    (64, "probe.grp"),
]

PAIRS = []
for uid, grp in KNOWN:
    ix = find_idx(grp, sd_tbl)
    if ix is None:
        ix = find_idx(grp, bd_tbl)
    if ix is None:
        print("  (no images.tbl entry for %s)" % grp)
        continue
    PAIRS.append((uid, ix, grp))
print("%d known (units.dat id -> images.tbl index) pairs\n" % len(PAIRS))

for arcname, ar in (("StarDat", SD), ("BrooDat", BD), ("patch_rt", PT)):
    for path in ("arr\\images.dat", "arr\\units.dat"):
        if not ar.has(path):
            continue
        d, gaps = ar.read_with_gaps(path)
        print("=== %s  %s  %d bytes  gaps=%d" % (arcname, path, len(d), len(gaps)))
        best = []
        for S in range(2, 65, 2):
            n = len(d) // S
            if n < 200:
                continue
            for O in range(0, S - 1, 2):
                hit = 0
                for uid, ix, grp in PAIRS:
                    if uid >= n:
                        continue
                    v = struct.unpack_from("<H", d, uid * S + O)[0]
                    if v == ix:
                        hit += 1
                if hit:
                    best.append((hit, S, O))
        best.sort(reverse=True)
        for hit, S, O in best[:6]:
            print("    stride=%-3d off=%-3d  hits=%d/%d" % (S, O, hit, len(PAIRS)))
        if not best:
            print("    no (stride, offset) reproduces any known pair")
        print()

SD.close()
BD.close()
PT.close()
