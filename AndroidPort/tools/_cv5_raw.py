import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader

ts = "platform"
for ar in (pm.SD, pm.BD):
    if ar.has("tileset\\%s.cv5" % ts):
        d, g = ar.read_with_gaps("tileset\\%s.cv5" % ts)
        break
cv = GapReader(d, g or [])
n = (len(d) + sum(s for _, s in (g or []))) // 52
print("cv5 groups", n)

def rec(gi):
    b = gi*52
    return [cv.u16(b+k*2) for k in range(26)]

for gi in (0, 1, 2, 100, 1023, 1024, 1254, 1441, 1450):
    r = rec(gi)
    print(f"g{gi:5d} @0={r[0]:5d} @2={r[2]:#06x} @4={r[4]:5d} @6={r[6]} @8={r[8]} @10={r[10]} @12={r[12]:5d} @14={r[14]} @16={r[16]} @18={r[18]}")
    print(f"        refs@20={r[20:26]}")

# also VX4 first entries
for ar in (pm.SD, pm.BD):
    if ar.has("tileset\\%s.vx4" % ts):
        vd, vg = ar.read_with_gaps("tileset\\%s.vx4" % ts)
        break
vx = GapReader(vd, vg or [])
nvx = (len(vd) + sum(s for _, s in (vg or []))) // 32
print("vx4 entries", nvx)
for m in (0,1,2):
    print("vx4[%d]" % m, [vx.u16(m*32+k*2) for k in range(16)])

# bloodbath MTXM histogram
r = pm.read_chk(os.path.join(pm.ROOT, r"maps\(4)Blood Bath.scm"))
chk, gaps = r
gg, sec = pm.parse_chk(chk, gaps)
off, size = sec[b"MTXM"]
o2, _ = sec[b"DIM "]
w, h = gg.u16(o2), gg.u16(o2+2)
vals = collections.Counter(gg.u16(off+i*2) for i in range(w*h))
print("bloodbath MTXM distinct", len(vals), "top:", vals.most_common(8))
print("doodad group vals present:", {k: vals[k] for k in (1254,1255,1441,1442,1445,1450,1451) if k in vals})
