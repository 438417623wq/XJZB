"""Batch B/C asset census: for every candidate GRP print which archive holds it
and how many frames it decodes to, so the SINGLES/UNITS tables can be filled
with real numbers instead of guesses.

Usage:  python probe_v211ce.py [group ...]
Groups: zerg_bld terran_bld units all
"""
import sys

import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(ROOT + r"\StarDat.mpq")
BD = sc_archive.Archive(ROOT + r"\BrooDat.mpq")
PT = sc_archive.Archive(ROOT + r"\patch_rt.mpq")

ZERG_BLD = [
    "fcolony", "SColony", "RCluster", "MutaCham", "Mutapit", "nest", "NydusPit",
    "UCereb", "cerebrat", "chrysal", "Over1", "Over2", "ZBuild", "Infest03",
    "zSpawn01", "zSpawn02", "zSpawn03", "Mutate", "spire", "hatchery", "Lair",
    "Hive", "Snakey", "Extract", "lurker",
]
TERRAN_BLD = [
    "research", "weaponpl", "physics", "Academy", "control", "ComSat", "Depot",
    "TBarrack", "factory", "starport", "refinery", "missile", "PillBox",
    "chemlab", "GeneLab", "machines", "nukesilo", "DryDocks", "controlT",
]
UNITS = [
    ("zerg", "ultra"), ("zerg", "queen"), ("zerg", "defiler"), ("zerg", "guardian"),
    ("zerg", "devour"), ("zerg", "lurknorm"), ("zerg", "lurkburr"), ("zerg", "brood"),
    ("zerg", "LurkEgg"), ("zerg", "egg"), ("zerg", "cocoon"), ("zerg", "Scourge"),
    ("zerg", "zdvdeath"), ("zerg", "zlurker"), ("zerg", "mutalid"),
    ("terran", "medic"), ("terran", "bomber"), ("terran", "Spider"),
    ("terran", "tmedeath"), ("terran", "marine"), ("terran", "tmeDeath"),
    ("protoss", "trilob"), ("protoss", "witness"), ("protoss", "corsair"),
]


def census(path):
    where = []
    for tag, ar in (("PT", PT), ("SD", SD), ("BD", BD)):
        if ar.has(path):
            where.append(tag)
    if not where:
        return None, 0, 0
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            r = grpm.decode_grp(data, gaps)
            if r is None:
                return "+".join(where), -1, 0
            frames, mw, mh = r
            return "+".join(where), len(frames), mw
    return "+".join(where), -1, 0


def show(label, path):
    where, n, mw = census(path)
    if where is None:
        print("%-34s %-46s MISS" % (label, path))
        return
    blocks = "%.2f blk" % (n / 17.0) if n > 0 else ""
    print("%-34s %-46s %-8s frames=%-4d %s" % (label, path, where, n, blocks))


def main():
    groups = sys.argv[1:] or ["all"]
    if "zerg_bld" in groups or "all" in groups:
        print("=== zerg buildings ===")
        for k in ZERG_BLD:
            show(k, "unit\\zerg\\%s.grp" % k)
    if "terran_bld" in groups or "all" in groups:
        print("=== terran buildings ===")
        for k in TERRAN_BLD:
            show(k, "unit\\terran\\%s.grp" % k)
    if "units" in groups or "all" in groups:
        print("=== units ===")
        for race, k in UNITS:
            show("%s/%s" % (race, k), "unit\\%s\\%s.grp" % (race, k))


main()
