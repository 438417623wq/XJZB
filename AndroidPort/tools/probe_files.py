"""Probe the StarCraft MPQ archives for the asset names we need.

The MPQ hash table stores no filenames, so we hash a list of known
StarCraft 1.x internal paths and report which ones exist.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"
ARCHIVES = ["StarDat.mpq", "BrooDat.mpq", "BroodWar.mpq", "patch_rt.mpq"]

UNITS = """
marine firebat medic ghost vulture goliath siege_tank siege_tank_turret scv
wraith science_vessel dropship battlecruiser valkyrie spider_mine nuclear_missile
zealot dragoon high_templar archon shuttle scout arbiter carrier interceptor corsair
dark_templar dark_archon reaver observer probe scarab
zergling hydralisk lurker ultralisk defiler queen drone overlord mutalisk guardian
devourer scourge infesting_terran egg larva cocoon broodling
""".split()

TILESETS = "badlands platform install ashworld jungle desert ice twilight".split()

PALETTES = """units tileset loading ofire bfire gfire terran zerg protoss wirefram
gamepal green blue red teal title font""".split()

SCRIPTS = "iscript images stat_txt orders upgrades weapons flingy sprites techdata".split()


def build_candidates():
    c = ["(listfile)"]
    for s in SCRIPTS:
        c.append("scripts\\%s.bin" % s)
        c.append("scripts\\%s.tbl" % s)
    for p in PALETTES:
        c.append("palette\\%s.pal" % p)
    for t in TILESETS:
        for ext in ("cv5", "vx4", "vr4", "wpe", "dddata"):
            c.append("tileset\\%s.%s" % (t, ext))
    for u in UNITS:
        c.append("unit\\%s.grp" % u)
        c.append("unit\\%s.grp" % u.replace("_", ""))
    # a few well-known extras
    c += [
        "game\\cursor.grp",
        "game\\thingy.grp",
        "unit\\thingy.grp",
        "images\\cmdicons.grp",
        "unit\\zergling.grp",
        "arr\\units.dat",
        "arr\\flingy.dat",
        "arr\\weapons.dat",
    ]
    return c


def main():
    cands = build_candidates()
    print("probing %d candidate paths across %d archives\n" % (len(cands), len(ARCHIVES)))

    grand_total = 0
    for arc in ARCHIVES:
        path = os.path.join(ROOT, arc)
        if not os.path.exists(path):
            print("== %s : MISSING ==" % arc)
            continue
        with MPQ(path) as m:
            print("== %s ==" % arc)
            print("   fmt=%d sector=%d hash=%d block=%d"
                  % (m.format_version, m.sector_size,
                     m.hash_table_size, m.block_table_size))
            lf = m.listfile()
            print("   embedded listfile entries: %d" % len(lf))
            if lf:
                print("   sample: %s" % lf[:8])

            found = []
            for name in cands:
                info = m.info(name)
                if info:
                    found.append((name, info))
            print("   candidates found: %d" % len(found))
            for name, info in found[:400]:
                print("      %-40s size=%-9d csize=%-9d flags=0x%08X"
                      % (name, info["size"], info["csize"], info["flags"]))
            grand_total += len(found)
            print()
    print("TOTAL candidate hits: %d" % grand_total)


if __name__ == "__main__":
    main()
