"""Verify Game.Type.unitId against the official rez/stat_txt.tbl names.

Parses the unitId values out of core/Game.java and checks that each one maps to
a stat_txt.tbl entry that plausibly names that unit. Catches a mis-keyed id
(e.g. pointing the missile turret at 'Terran Covert Ops').
"""
import os
import re
import sys

ROOT = r"F:\KF\XJZB"
GAME = os.path.join(ROOT, r"AndroidPort\app\app\src\main\java\com\xjzb\rts\core\Game.java")
NAMES = os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets\ui\unitnames.txt")

# what we expect each game key to be called in stat_txt.tbl
EXPECT = {
    "scv": "SCV", "marine": "Marine", "firebat": "Firebat", "vulture": "Vulture",
    "tank": "Siege Tank", "stank": "Siege Tank", "zergling": "Zergling",
    "hydra": "Hydralisk", "muta": "Mutalisk", "cc": "Command Center",
    "depot": "Supply Depot", "refinery": "Refinery", "barracks": "Barracks",
    "factory": "Factory", "turret": "Missile Turret", "hatchery": "Hatchery",
    "pool": "Spawning Pool", "sunken": "Sunken Colony",
}

src = open(GAME, encoding="utf8").read()
# t("key", "中文", ..., unitId)  -- unitId is the trailing int before ')'
ids = {}
for m in re.finditer(r't\(\s*"([a-z]+)"\s*,(.*?)\);', src, re.S):
    key, rest = m.group(1), m.group(2)
    tail = re.findall(r',\s*(\d+)\s*$', rest.strip())
    if tail:
        ids[key] = int(tail[-1])

names = {}
for line in open(NAMES, encoding="utf8"):
    line = line.strip()
    if not line:
        continue
    i, sep, n = line.partition(" ")
    if not sep or not i.isdigit():
        continue          # continuation rows (ability text) carry no id
    names[int(i)] = n

print("%-10s %5s  %-28s %s" % ("key", "id", "stat_txt name", "verdict"))
bad = 0
for key, exp in EXPECT.items():
    uid = ids.get(key)
    if uid is None:
        print("%-10s %5s  %-28s MISSING unitId" % (key, "-", "-"))
        bad += 1
        continue
    got = names.get(uid, "<no such id>")
    ok = exp.lower() in got.lower()
    if not ok:
        bad += 1
    print("%-10s %5d  %-28s %s" % (key, uid, got, "ok" if ok else "*** MISMATCH, want %r" % exp))

print()
print("checked %d keys, %d problems" % (len(EXPECT), bad))
sys.exit(1 if bad else 0)
