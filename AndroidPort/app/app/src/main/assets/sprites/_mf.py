import json
m=json.load(open("manifest.json",encoding="utf-8"))
ks=[k for k in m if any(s in k for s in ("medic","valkyrie","spider","brood","lurk_egg","lurkegg","egg"))]
for k in sorted(ks):
    print(k, json.dumps(m[k]))
print("total keys:",len(m))
print("sample:",json.dumps(list(m.items())[0]))
