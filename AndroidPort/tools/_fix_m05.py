import io, json
p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\missions\m05.json"
raw = io.open(p, encoding="utf-8").read()
obj = json.loads(raw)
fixes = {"hydra": (3150.0, 3180.0), "muta": (3300.0, 3200.0)}
n = 0
for su in obj["startUnits"]:
    if su["team"] == 1 and su["type"] in fixes and abs(su["x"] - fixes[su["type"]][0]) < 1:
        su["x"] = 3140.0
        su["y"] = 3210.0
        n += 1
assert n == 2, n
out = json.dumps(obj, indent=1, ensure_ascii=False) + "\n"
io.open(p, "w", encoding="utf-8", newline="\n").write(out)
print("m05 fixed", n)