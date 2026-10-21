import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm
p = r"F:\KF\XJZB\AndroidPort\assets_src\maps\(4)Inferno.chk"
chk, gaps = pm.read_chk(p)
g, sec = pm.parse_chk(chk, gaps)
d = sec.get("DD2 ")
print("DD2 len", len(d), "gaps", [x for x in gaps])
print("ERA", struct.unpack("<H", sec["ERA "][:2])[0] if "ERA " in sec else None)
print("VER", struct.unpack("<H", sec["VER "][:2])[0] if "VER " in sec else None)
recs = [struct.unpack_from("<HHHBB", d, i) for i in range(0, len(d), 8)]
bad = [r for r in recs if r[0] > 511]
print("total recs", len(recs), "ids>511:", len(bad))
print("first 30 recs:", recs[:30])
# where are the bad ones
for i,r in enumerate(recs):
    if r[0] > 511:
        print("bad idx", i, r); break
