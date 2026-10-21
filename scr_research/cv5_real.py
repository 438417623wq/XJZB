import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
from gapio import GapReader

TS = [("StarDat.mpq","badlands"),("StarDat.mpq","platform"),("StarDat.mpq","install"),
      ("StarDat.mpq","ashworld"),("StarDat.mpq","jungle"),
      ("BrooDat.mpq","desert"),("BrooDat.mpq","ice"),("BrooDat.mpq","twilight")]
summary = {}
for arch, ts in TS:
    ar = sc_archive.Archive(os.path.join(r"F:\KF\XJZB", arch))
    data, gaps = ar.read_with_gaps("tileset\\%s.cv5" % ts)
    size = ar.info("tileset\\%s.cv5" % ts)["size"]
    g = GapReader(data, gaps)
    n = size // 52
    doodads = {}
    for k in range(n):
        if g.u16(k*52) != 1: continue
        flags = g.u16(k*52+2); ov = g.u16(k*52+4); rem = g.u16(k*52+6)
        nm = g.u16(k*52+8); dd = g.u16(k*52+12); w = g.u16(k*52+14); h = g.u16(k*52+16)
        doodads.setdefault(dd, []).append((k, flags, ov, rem, nm, w, h))
    ids = sorted(doodads)
    rem1 = sorted(d for d in ids if doodads[d][0][3] == 1)
    summary[ts] = (len(doodads), ids, rem1, doodads)
    print(f"{ts:9s} groups={n:5d} doodad-groups={sum(len(v) for v in doodads.values()):4d} distinct ddData ids={len(ids):4d} min={ids[0]} max={ids[-1]}")
    print(f"           remasteredDoodad==1 ids: {len(rem1)}  {rem1[:25]}")
    print(f"           ids: {ids[:40]}{'...' if len(ids)>40 else ''}")
import pickle
pickle.dump(summary, open(r"F:\KF\XJZB\scr_research\cv5_doodads.pkl","wb"))
print("\n== PLATFORM lookup of the parent's ids 137/256/257 ==")
_, pids, _, pd = summary["platform"]
for eid in (137, 256, 257, 258):
    print(f"  id {eid}: {'PRESENT' if eid in pd else 'ABSENT'}  {pd.get(eid)}")
print("\n== ASHWORLD 0..143 ==")
_, aids, _, ad = summary["ashworld"]
print("  present:", [i for i in range(0,144) if i in ad])
print("  absent :", [i for i in range(0,144) if i not in ad])
