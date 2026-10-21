import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

# --- Blood Bath platform map: DD2 ids {137,256,257}
p = r"F:\KF\XJZB\maps\(4)Blood Bath.scm"
chk, gaps = pm.read_chk(p)
g, sec = pm.parse_chk(chk, gaps)
off, sz = sec[b"DD2 "]; raw = g.bytes_at(off, sz)
recs = [struct.unpack_from("<HHHBB", raw, i) for i in range(0, sz, 8)]
print("Blood Bath DD2 recs:", recs)
o, s2 = sec[b"MTXM"]; mtxm = g.bytes_at(o, s2)
tiles = set(struct.unpack_from("<%dH" % (s2//2), mtxm, 0))
groups = set(t >> 4 for t in tiles)
print("MTXM tiles distinct:", len(tiles), "groups distinct:", len(groups), "max group:", max(groups))

D = r"F:\KF\XJZB\scr_research\tileset"
dd = open(os.path.join(D, "platform.dddata.bin"), "rb").read()
for eid in (137, 256, 257):
    base = eid * 512
    vals = struct.unpack_from("<256H", dd, base)
    nz = [v for v in vals if v]
    print(f"\n-- platform dddata entry {eid}: nonzero={len(nz)}")
    print("   first 24 nonzero:", nz[:24])
    print("   as CV5 group (v>>4) <1513:", sum(1 for v in nz if (v>>4) < 1513), "/", len(nz))
    print("   v itself <1513:", sum(1 for v in nz if v < 1513), "/", len(nz))
    print("   raw values in map MTXM tile set:", sum(1 for v in nz if v in tiles), "/", len(nz))
    print("   v>>4 in map MTXM group set:", sum(1 for v in nz if (v>>4) in groups), "/", len(nz))
    print("   max value:", max(nz) if nz else None)
