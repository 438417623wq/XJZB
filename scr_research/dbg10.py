import sys, os, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
T = r"F:\KF\XJZB\AndroidPort\tools"
for fn in ("images_tbl.txt","images_tbl2.txt"):
    p = os.path.join(T, fn)
    lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
    ts = [l for l in lines if "thingy\\tileset\\" in l.lower()]
    print(fn, "thingy\\tileset\\ entries:", len(ts))
    for l in ts[:8]: print("   ", l)
print()
# doodad png set
png = os.listdir(r"F:\KF\XJZB\AndroidPort\extracted\expand\doodads")
print("doodad PNG count:", len(png))
# per-tileset subdir names present in images_tbl2
lines = open(os.path.join(T,"images_tbl2.txt"), encoding="utf-8", errors="replace").read().splitlines()
ts = [l for l in lines if "thingy\\tileset\\" in l.lower()]
c = collections.Counter()
for l in ts:
    low = l.lower()
    i = low.find("thingy\\tileset\\")
    rest = low[i+len("thingy\\tileset\\"):]
    c[rest.split("\\")[0]] += 1
print("per-tileset overlay GRP counts:", dict(c), "sum", sum(c.values()))
