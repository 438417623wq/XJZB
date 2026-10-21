"""Probe StarDat.mpq for the files the game needs."""
import sc_archive

ar = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
names = [
    "unit\\terran\\marine.grp", "unit\\terran\\scv.grp", "unit\\terran\\firebat.grp",
    "unit\\terran\\vulture.grp", "unit\\terran\\siege tank.grp", "unit\\terran\\siege tank s.grp",
    "unit\\terran\\wraith.grp", "unit\\terran\\goliath.grp", "unit\\terran\\dropship.grp",
    "unit\\terran\\command center.grp", "unit\\terran\\supply depot.grp", "unit\\terran\\barracks.grp",
    "unit\\terran\\refinery.grp", "unit\\terran\\factory.grp", "unit\\terran\\missile turret.grp",
    "unit\\terran\\bunker.grp", "unit\\terran\\academy.grp", "unit\\terran\\engineering bay.grp",
    "unit\\terran\\starport.grp", "unit\\zerg\\zergling.grp", "unit\\zerg\\hydralisk.grp",
    "unit\\zerg\\mutalisk.grp", "unit\\zerg\\hatchery.grp", "unit\\zerg\\overlord.grp",
    "unit\\zerg\\spawning pool.grp", "unit\\zerg\\lair.grp", "unit\\zerg\\hive.grp",
    "unit\\zerg\\creep colony.grp", "unit\\zerg\\sunken colony.grp", "unit\\zerg\\spore colony.grp",
    "unit\\zerg\\hydralisk den.grp", "unit\\zerg\\evolution chamber.grp",
    "unit\\neutral\\mineral field.grp", "unit\\neutral\\Geyser.grp", "unit\\cmdbtns\\cmdicons.grp",
    "arr\\images.tbl", "arr\\images.dat", "arr\\units.dat",
    "tileset\\jungle\\jungle.cv5", "tileset\\jungle\\jungle.vf4", "tileset\\jungle\\jungle.vx4",
    "tileset\\jungle\\jungle.vr4", "tileset\\jungle\\jungle.wpe", "tileset\\jungle\\units.pal",
    "tileset\\badlands\\badlands.wpe", "tileset\\platform\\platform.wpe",
    "tileset\\installation\\installation.wpe", "tileset\\desert\\desert.wpe",
    "tileset\\ice\\ice.wpe", "tileset\\twilight\\twilight.wpe",
]
miss = []
for n in names:
    i = ar.info(n)
    if i:
        print("OK  %8d  %s" % (i["size"], n))
    else:
        miss.append(n)
print("\n--- missing (%d):" % len(miss))
for n in miss:
    print("MISS  %s" % n)
