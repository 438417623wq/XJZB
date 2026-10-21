import sys, os, struct, collections, pickle
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
from gapio import GapReader
summary = pickle.load(open(r"F:\KF\XJZB\scr_research\cv5_doodads.pkl","rb"))
print("tileset   doodadGroups  distinctIds(<=511)  min  max   idRange(ids>511 dropped)")
tot = 0
for ts in ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]:
    ng, ids, rem1, d = summary[ts]
    clean = sorted(i for i in ids if i <= 511)
    bad = sorted(i for i in ids if i > 511)
    tot += len(clean)
    print(f"{ts:9s} {sum(len(v) for v in d.values()):8d} {len(clean):12d} {clean[0]:6d} {clean[-1]:5d}   dropped={bad}")
print("sum of distinct per-tileset doodad ids:", tot)
# contiguous?
for ts in ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]:
    _, ids, _, d = summary[ts]
    clean = sorted(i for i in ids if i <= 511)
    gaps = [i for i in range(clean[0], clean[-1]+1) if i not in set(clean)]
    print(f"{ts:9s} contiguous 0..{clean[-1]}? missing={len(gaps)} {gaps[:20]}")
