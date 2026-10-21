import sys, os, struct, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TS = ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]
d = r"F:\KF\XJZB\scr_research\tileset"
res = {}
for t in TS:
    b = open(os.path.join(d, f"{t}.dddata.bin"), "rb").read()
    assert len(b) == 512*256*2, (t, len(b))
    used = []
    for e in range(512):
        row = struct.unpack_from("<256H", b, e*512)
        if any(row): used.append(e)
    res[t] = used
    print(f"{t:10s} nonEmptyEntries={len(used):4d} min={used[0] if used else None} max={used[-1] if used else None}")
print()
print("=== cross-check vs splash-editor doodad-walk.json ===")
j = json.load(open(r"F:\KF\XJZB\scr_research\splash_doodadwalk.json", encoding="utf-8"))
alias = {"space":"platform","installation":"install"}
for t in TS:
    key = None
    for k in j["doodads"]:
        if alias.get(k,k) == t: key = k
    walk = set(int(x) for x in j["doodads"][key])
    dd = set(res[t])
    print(f"{t:10s} dddata={len(dd):4d} walk={len(walk):4d} walk-only={len(walk-dd):4d} dddata-only={len(dd-walk):4d}")
    if walk-dd: print(f"    walk-only sample: {sorted(walk-dd)[:15]}")
    if dd-walk: print(f"    dddata-only sample: {sorted(dd-walk)[:15]}")
json.dump({k:v for k,v in res.items()}, open(r"F:\KF\XJZB\scr_research\dddata_used.json","w"))
