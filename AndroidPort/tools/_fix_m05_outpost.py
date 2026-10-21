import io, json
# m05 ships a second enemy outpost at (3200,3200). Its snapped tile (3152,3152)
# sits in a 28-minitile pocket that the player's region cannot reach, and m05's
# objective is destroyAll -- so the level was UNWINNABLE. Probe: the region
# flood from the player's cc covers 189229 of 262144 minitiles and does not
# contain that pocket, while the nearest reachable clear patch is (3152,3312).
#
# snapBuilding(v,4) = ((int)(v/32) - 2)*32 + 16, so:
#   x 3200 -> 3152 (unchanged)   y 3360 -> 3312 (was 3200 -> 3152)
# Everything else in the cluster shifts with it by +160.
p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\missions\m05.json"
raw = io.open(p, encoding="utf-8").read()
obj = json.loads(raw)
shift = {"hatchery": (3200, 3360), "sunken": None, "hydra": None, "muta": None}
moved = 0
for su in obj["startUnits"]:
    if su["team"] != 1:
        continue
    x, y = su["x"], su["y"]
    # only the southern outpost cluster (the northern base is around y=240..450)
    if y < 3000:
        continue
    su["y"] = y + 160
    moved += 1
    if su["type"] == "hatchery":
        assert (x, y) == (3200, 3200), (x, y)
        su["y"] = 3360          # snaps to 3312
assert moved == 6, moved
out = json.dumps(obj, indent=1, ensure_ascii=False) + "\n"
io.open(p, "w", encoding="utf-8", newline="\n").write(out)
print("m05 southern outpost moved +160y on", moved, "entries")
for su in obj["startUnits"]:
    if su["team"] == 1 and su["y"] > 3000:
        print("   ", su["type"], su["x"], su["y"])