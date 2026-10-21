import json, os
p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\missions\m01.json"
raw = open(p, encoding="utf-8").read()
obj = json.loads(raw)
rt = json.dumps(obj, indent=1, ensure_ascii=False) + "\n"
print("identical:", rt == raw)
print("len raw", len(raw), "len rt", len(rt))
if rt != raw:
    for i,(a,b) in enumerate(zip(raw, rt)):
        if a != b:
            print("first diff at", i, repr(raw[max(0,i-40):i+40]), "|", repr(rt[max(0,i-40):i+40]))
            break
