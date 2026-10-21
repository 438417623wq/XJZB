import io, json
p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\missions\m05.json"
obj = json.loads(io.open(p, encoding="utf-8").read())
# The southern outpost's two hydralisks and the mutalisk all landed on the same
# tile after the +160y shift. Give each its own tile; the probe showed the block
# (3120..3320, 3300..3420) is clear ground, so a small fan-out is safe.
spread = {"hydra": [(3090.0, 3345.0), (3180.0, 3345.0)], "muta": [(3130.0, 3300.0)]}
seen = {"hydra": 0, "muta": 0}
for su in obj["startUnits"]:
    if su["team"] != 1 or su["y"] < 3000:
        continue
    t = su["type"]
    if t in spread:
        x, y = spread[t][seen[t]]
        su["x"], su["y"] = x, y
        seen[t] += 1
assert seen["hydra"] == 2 and seen["muta"] == 1, seen
out = json.dumps(obj, indent=1, ensure_ascii=False) + "\n"
io.open(p, "w", encoding="utf-8", newline="\n").write(out)
print("spread", seen)
for su in obj["startUnits"]:
    if su["team"] == 1 and su["y"] > 3000:
        print("   ", su["type"], su["x"], su["y"])