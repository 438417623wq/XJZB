import sys, os, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
T = r"F:\KF\XJZB\AndroidPort\tools"
lines = open(os.path.join(T,"images_tbl2.txt"), encoding="utf-8", errors="replace").read().splitlines()
ts = [(int(l.split("\t")[0]), l.split("\t")[1]) for l in lines if "thingy\\tileset\\" in l.lower()]
runs = {}
for idx, name in ts:
    low = name.lower()
    i = low.find("thingy\\tileset\\")
    rest = low[i+len("thingy\\tileset\\"):]
    key = rest.split("\\")[0]
    runs.setdefault(key, []).append((idx, name))
for k, v in runs.items():
    ids = [a for a,b in v]
    print(f"{k or '(empty)':12s} n={len(v):3d} idx {min(ids)}..{max(ids)} contiguous={ids == list(range(min(ids),max(ids)+1))}")
    if k == "":
        for a,b in v: print("     ", a, b)
