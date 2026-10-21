"""v2.11: calibrate the images.tbl row <-> ImageTypes enum alignment using
KNOWN grp->building pairs, then read off the unknown zerg buildings.

Known pairs come from actual StarCraft retail knowledge (names are unambiguous:
hatchery.grp is the Hatchery, Snakey.grp is the Spawning Pool, ...).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))

ENUM_TXT = os.path.join(
    r"C:\Users\XiaoXin\AppData\Local\Temp\dsh-spill-y8WfPh\session-cb4a4d09e0b0",
    "254abc3c9a02-web_fetch.txt")


def enum_names():
    txt = open(ENUM_TXT, encoding="utf8", errors="replace").read()
    i = txt.find("enum struct ImageTypes")
    j = txt.find("enum struct Sounds", i)
    return re.findall(r"IMAGEID_([A-Za-z0-9_]+)", txt[i:j])


def tbl(path, ar):
    data, _ = ar.read_with_gaps(path)
    cnt = data[0] | (data[1] << 8)
    offs = [data[2 + 2 * k] | (data[3 + 2 * k] << 8) for k in range(cnt)]
    return [data[o:data.index(b"\x00", o)].decode("cp1252", "replace") for o in offs]


names = enum_names()
eidx = {}
for i, n in enumerate(names):
    eidx.setdefault(n, i)

ents = tbl("arr\\images.tbl", SD)

# base-name -> first table row that carries that base with a .grp
trow = {}
for i, e in enumerate(ents):
    b = os.path.basename(e).lower().rsplit(".", 1)[0]
    if e.lower().endswith(".grp") and b not in trow:
        trow[b] = i

# (grp basename, enum name) -- retail StarCraft ground truth
KNOWN = [
    # zerg units
    ("avenger", "Scourge"), ("brood", "Broodling"), ("bugguy", "Infested_Terran"),
    ("cocoon", "Guardian_Cocoon"), ("defiler", "Defiler"), ("drone", "Drone"),
    ("egg", "Egg"), ("guardian", "Guardian"), ("hydra", "Hydralisk"),
    ("larva", "Larva"), ("mutalid", "Mutalisk"), ("overlord", "Overlord"),
    ("queen", "Queen"), ("ultra", "Ultralisk"), ("zergling", "Zergling"),
    # zerg buildings
    ("ucereb", "Cerebrate"), ("chrysal", "Mature_Chrysalis"),
    ("fcolony", "Creep_Colony"), ("hatchery", "Hatchery"), ("hive", "Hive"),
    ("lair", "Lair"), ("mutacham", "Evolution_Chamber"),
    ("mutapit", "Hydralisk_Den"), ("nest", "Queens_Nest"),
    ("nyduspit", "Nydus_Canal"), ("over1", "Overmind_With_Shell"),
    ("over2", "Overmind_Without_Shell"), ("rcluster", "Spore_Colony"),
    ("extract", "Extractor"), ("snakey", "Spawning_Pool"), ("spire", "Spire"),
    ("scolony", "Sunken_Colony"), ("infest03", "Infested_Command_Center_Overlay"),
    ("zbuild", "Zerg_Building_Morph"),
    ("zspawn01", "Zerg_Building_Spawn_Small"),
    ("zspawn02", "Zerg_Building_Spawn_Medium"),
    ("zspawn03", "Zerg_Building_Spawn_Large"),
    # terran buildings (confirmed visually in this project)
    ("research", "Terran_Engineering_Bay"), ("weaponpl", "Terran_Armory"),
    ("physics", "Terran_Science_Facility"),
    # protoss buildings
    ("nexus", "Protoss_Nexus"), ("pylon", "Protoss_Pylon"),
    ("gateway", "Protoss_Gateway"), ("forge", "Protoss_Forge"),
    ("assim", "Protoss_Assimilator"),
]

print("%-14s %-34s %6s %6s %6s" % ("grp", "enum name", "enum#", "tbl#", "delta"))
rows = []
for base, en in KNOWN:
    ei = eidx.get(en)
    ti = trow.get(base)
    if ei is None or ti is None:
        print("%-14s %-34s %6s %6s   MISS" % (base, en, ei, ti))
        continue
    rows.append((ei, ti, base, en))
    print("%-14s %-34s %6d %6d %6d" % (base, en, ei, ti, ti - ei))

print()
print("== monotonic check ==")
rows.sort()
bad = 0
for a, b in zip(rows, rows[1:]):
    if b[1] <= a[1]:
        print("  NON-MONOTONE %s(%d,%d) -> %s(%d,%d)" % (a[2], a[0], a[1], b[2], b[0], b[1]))
        bad += 1
print("  inversions:", bad)

print()
print("== unknown zerg building rows, interpolated enum ==")
for base in ("ucereb", "mutacham", "mutapit", "nest"):
    ti = trow.get(base)
    # nearest known rows below and above in table order
    below = max([r for r in rows if r[1] < ti], key=lambda r: r[1], default=None)
    above = min([r for r in rows if r[1] > ti], key=lambda r: r[1], default=None)
    print("  tbl%-4d %-12s between enum%d %s (tbl%d) and enum%d %s (tbl%d)"
          % (ti, base, below[0], below[3], below[1], above[0], above[3], above[1]))
