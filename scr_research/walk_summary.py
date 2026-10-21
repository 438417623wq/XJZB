import json, collections
p = r"F:\KF\XJZB\scr_research\splash_doodadwalk.json"
j = json.load(open(p, encoding="utf-8"))
print("top keys:", list(j.keys()))
for ts, dd in j["doodads"].items():
    ids = sorted(int(k) for k in dd)
    kinds = collections.Counter(v.get("kind") for v in dd.values())
    print(f"{ts}: n={len(ids)} min={ids[0]} max={ids[-1]} kinds={dict(kinds)}")
    # show gaps pattern summary
    print("   ids:", ids[:25], "..." if len(ids)>25 else "")
