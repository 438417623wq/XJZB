# _e23.py -- temporarily inject the six batch-E portrait units into mission m01
# so the real-device check can see every talking-head still in one run.
#
# The mission format (Mission.java:100-107) accepts arbitrary startUnits with an
# explicit team, and Game.java:731 spawns them at the authored pixel position,
# so this needs no tech tree and no gameplay. Positions are on the walkable row
# proven by tools/_e21c.py (divide, y=400, x=120..760 all walkable).
#
# REVERT with tools/_e23_revert.py (or copy tools/out/m01.json.bak back) before
# rebuilding anything that ships.
import json, os, shutil

A = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\missions"
SRC = os.path.join(A, "m01.json")
BAK = r"F:\KF\XJZB\AndroidPort\tools\out\m01.json.bak"

if not os.path.exists(BAK):
    shutil.copy2(SRC, BAK)
    print("backed up ->", BAK)

with open(SRC, encoding="utf-8") as f:
    m = json.load(f)

m["startUnits"] = [u for u in m["startUnits"]
                   if u["type"] not in ("medic", "lurker", "devourer",
                                        "valkyrie", "corsair", "darchon")]

# one of each portrait-bearing unit, left to right, 120 px apart
for i, key in enumerate(("medic", "lurker", "devourer",
                         "valkyrie", "corsair", "darchon")):
    m["startUnits"].append({"type": key, "x": 120 + 120 * i, "y": 400, "team": 0})

with open(SRC, "w", encoding="utf-8") as f:
    json.dump(m, f, ensure_ascii=False, indent=1)
    f.write("\n")

print("injected portrait units:", [u["type"] for u in m["startUnits"]
                                   if u["type"] in ("medic", "lurker", "devourer",
                                                    "valkyrie", "corsair", "darchon")])
print("total startUnits:", len(m["startUnits"]))
