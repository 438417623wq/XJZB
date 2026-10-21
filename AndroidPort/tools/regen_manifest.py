import os
import sc_archive
import grp as grpm

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
BD = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")
OUT = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"

units = {
    "scv": ("unit/terran/SCV.grp", 2, 1), "marine": ("unit/terran/marine.grp", 3, 1),
    "firebat": ("unit/terran/firebat.grp", 2, 1), "vulture": ("unit/terran/Vulture.grp", 1, 1),
    "tank": ("unit/terran/tank.grp", 2, 1), "zergling": ("unit/zerg/zergling.grp", 3, 1),
    "hydra": ("unit/zerg/hydra.grp", 2, 1), "muta": ("unit/zerg/mutalid.grp", 2, 1),
    "over": ("unit/zerg/overlord.grp", 1, 0), "drone": ("unit/zerg/drone.grp", 2, 1),
}
singles = {
    "stank": "unit/terran/stank.grp", "cc": "unit/terran/control.grp",
    "depot": "unit/terran/Depot.grp", "barracks": "unit/terran/TBarrack.grp",
    "refinery": "unit/terran/refinery.grp", "factory": "unit/terran/factory.grp",
    "turret": "unit/terran/missile.grp", "bunker": "unit/terran/PillBox.grp",
    "academy": "unit/terran/Academy.grp", "starport": "unit/terran/starport.grp",
    "hatchery": "unit/zerg/hatchery.grp", "lair": "unit/zerg/Lair.grp",
    "hive": "unit/zerg/Hive.grp", "pool": "unit/zerg/Snakey.grp",
    "sunken": "unit/zerg/fcolony.grp", "mineral": "unit/neutral/min01.grp",
    "mineral2": "unit/neutral/min02.grp", "mineral3": "unit/neutral/min03.grp",
    "geyser": "unit/neutral/Geyser.grp",
    "bang_s": "thingy/tBangS.grp",
    "bang_m": "thingy/tBangL.grp",
    "bang_l": "thingy/tBangX.grp",
}
lines = []
for key, (path, walk, atk) in units.items():
    lines.append("%s,0,%d,%d,0" % (key, walk, atk))
for key, path in singles.items():
    n = 1
    for ar in (SD, BD):
        if ar.has(path):
            try:
                data, gaps = ar.read_with_gaps(path)
                frames, mw, mh = grpm.decode_grp(data, gaps)
                n = min(len(frames), 6)
                print(key, "frames:", len(frames))
            except Exception as ex:
                print(key, "DECODE FAIL:", type(ex).__name__, ex)
            break
    else:
        print(key, "MISSING")
    lines.append("%s,1,0,0,%d" % (key, n))
with open(os.path.join(OUT, "sprites", "manifest.txt"), "w", encoding="utf8") as fp:
    fp.write("\n".join(lines))
print("---")
print("\n".join(lines))
