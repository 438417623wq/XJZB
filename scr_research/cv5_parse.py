import sys, os, struct, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TS = ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]
d = r"F:\KF\XJZB\scr_research\tileset"
catalog = {}
for t in TS:
    cv5 = open(os.path.join(d, f"{t}.cv5"), "rb").read()
    n = len(cv5)//52
    groups = []
    for g in range(n):
        at = g*52
        idx = struct.unpack_from("<H", cv5, at)[0]
        if idx != 1: continue
        flags = struct.unpack_from("<H", cv5, at+2)[0]
        overlay, nameIndex, ddData, w, h = struct.unpack_from("<HHHHH", cv5, at+4)
        groups.append((g, overlay, nameIndex, ddData, w, h, flags))
    byid = {}
    for g,ov,ni,dd,w,h,fl in groups:
        byid.setdefault(dd, (g,ov,ni,w,h,fl))
    ids = sorted(byid)
    catalog[t] = byid
    if ids:
        print(f"{t:10s} cv5groups={n:4d} doodadGroups={len(groups):4d} distinctDD={len(ids):4d} min={ids[0]} max={ids[-1]}")
    else:
        print(f"{t:10s} cv5groups={n:4d} doodadGroups=0  (no index==1 groups)")
print()
j = json.load(open(r"F:\KF\XJZB\scr_research\splash_doodadwalk.json", encoding="utf-8"))
alias = {"space":"platform","installation":"install"}
print("=== compare CV5 ddData ids vs splash-editor doodad-walk.json ===")
for t in TS:
    key = None
    for k in j["doodads"]:
        if alias.get(k,k) == t: key = k
    if key is None: print(f"{t}: no walk entry"); continue
    walk_ids = set(int(x) for x in j["doodads"][key])
    cv5_ids = set(catalog[t])
    print(f"{t:10s} walk({key:11s})={len(walk_ids):4d} cv5={len(cv5_ids):4d}  walk-only={sorted(walk_ids-cv5_ids)[:10]}  cv5-only={sorted(cv5_ids-walk_ids)[:10]}")
