"""Wide probe: enumerate StarCraft asset paths across all archives.

Covers unit sprites, palettes, tilesets, interface art and data tables so we
know exactly what art is available before designing the Android port.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"
ARCHIVES = ["StarDat.mpq", "BrooDat.mpq", "BroodWar.mpq", "patch_rt.mpq"]

# --- every unit / building sprite internal name used by StarCraft 1.16 ------
UNITS = """
marine firebat medic ghost ghostnt vulture goliath goliathbase goliath turret
tankbase tankturret tankbase2 tankturret2 scv wraith science_vessel dropship
battlecruiser valkyrie spider_mine scanner_sweep nuclear_missile
zealot dragoon hightemplar hightemplar archon shuttle scout arbiter carrier
interceptor corsair darktemplar darkarchon reaver observer probe scarab
zergling hydralisk lurker ultralisk defiler queen drone overlord mutalisk
guardian devourer scourge egg larva cocoon broodling
terran_civilian terran_civilian2 terran_civilian3 terran_civilian4
protoss_civilian protoss_civilian2 protoss_civilian3
rhynadon bengalaas scantid kakaru ursadon
""".split()

BUILDINGS = """
command_center science_facility refinery academy factory starport
engineering_bay armory supply_depot missileturret bunker comsat_station
physics_lab machine_shop controltower covert_ops
nexus pylon assimilator gateway forge photon_cannon cybernetics_core
citadel_of_adun templar_archives robotics_facility stargate
fleet_beacon arbiter_tribunal observatory robotics_support_bay shield_battery
hatchery creep_colony extractor spawning_pool evolution_chamber
hydralisk_den sunken_colony spire queens_nest ultralisk_cavern
defiler_mound greater_spire nydus_canal infested_command_center
""".split()

PALETTES = """
units tileset loading ofire bfire gfire terran zerg protoss wirefram
gamepal green blue red teal title font 1bit 2bit 3bit 4bit 5bit 6bit 7bit 8bit
""".split()

TILESETS = "badlands platform install ashworld jungle desert ice twilight".split()

EFFECTS = """
thingy thin cursor cmdicons bw_thingy eggspawn
""".split()

SCRIPTS = """iscript images sprites flingy units orders upgrades weapons techdata
buttons weapons.dat""".split()


def paths():
    out = ["(listfile)"]
    for s in SCRIPTS:
        out.append("scripts\\%s.bin" % s)
    for t in TILESETS:
        for ext in ("cv5", "vx4", "vr4", "wpe", "dddata", "minitile"):
            out.append("tileset\\%s.%s" % (t, ext))
    for p in PALETTES:
        out.append("palette\\%s.pal" % p)
    for u in set(UNITS + BUILDINGS):
        out.append("unit\\%s.grp" % u)
    for e in EFFECTS:
        out.append("unit\\%s.grp" % e)
        out.append("game\\%s.grp" % e)
    for d in ("units", "flingy", "sprites", "images", "orders", "weapons",
              "upgrades", "techdata", "sound", "buttons"):
        out.append("arr\\%s.dat" % d)
    out.append("arr\\sfxdata.tbl")
    return out


def main():
    allp = paths()
    print("probing %d paths x %d archives\n" % (len(allp), len(ARCHIVES)))
    hits = {}
    for arc in ARCHIVES:
        p = os.path.join(ROOT, arc)
        if not os.path.exists(p):
            print("== %s MISSING ==" % arc)
            continue
        with MPQ(p) as m:
            lf = m.listfile()
            print("== %s == fmt=%d hash=%d block=%d listfile=%d"
                  % (arc, m.format_version, m.hash_table_size,
                     m.block_table_size, len(lf)))
            if lf:
                print("   listfile sample: %s" % lf[:10])
                for n in lf:
                    hits.setdefault(n.lower(), (arc, None))
            n_hit = 0
            for name in allp:
                info = m.info(name)
                if info:
                    n_hit += 1
                    key = name.lower()
                    if key not in hits or hits[key][1] is None:
                        hits[key] = (arc, info)
            print("   probed hits: %d" % n_hit)
            print()

    print("=" * 70)
    print("UNIQUE ASSETS FOUND: %d" % len(hits))
    print("=" * 70)
    by_dir = {}
    for name, (arc, info) in sorted(hits.items()):
        d = name.rsplit("\\", 1)[0] if "\\" in name else "(root)"
        by_dir.setdefault(d, []).append((name, arc, info))

    for d in sorted(by_dir):
        items = by_dir[d]
        print("\n### %s  (%d)" % (d, len(items)))
        for name, arc, info in items[:80]:
            if info:
                print("   %-38s %-14s %8d" % (name, arc, info["size"]))
            else:
                print("   %-38s %-14s (from listfile)" % (name, arc))
        if len(items) > 80:
            print("   ... +%d more" % (len(items) - 80))


if __name__ == "__main__":
    main()
