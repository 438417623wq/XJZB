import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm

src = r"maps\(4)Blood Bath.scm"
r = pm.read_chk(os.path.join(pm.ROOT, src))
chk, gaps = r
g, sec = pm.parse_chk(chk, gaps)
o, s = sec[b"DIM "]
w, h = g.u16(o), g.u16(o+2)
mo, ms = sec[b"MTXM"]
to, tsz = sec[b"TILE"]
print("map %dx%d MTXM=%d TILE=%d" % (w, h, ms, tsz))
mx = [g.u16(mo+i*2) for i in range(w*h)]
tl = [g.u16(to+i*2) for i in range(w*h)]
print("MTXM max", max(mx), "TILE max", max(tl))
print("MTXM values >1023:", sum(1 for v in mx if v > 1023))
print("TILE values >1023:", sum(1 for v in tl if v > 1023))
print()
print("box for id256 centre (1408,912) tiles 38..49 x 24..32")
for ty in range(24, 33):
    row_m = " ".join("%4d" % mx[ty*w+tx] for tx in range(38, 50))
    row_t = " ".join("%4d" % tl[ty*w+tx] for tx in range(38, 50))
    print("ty%2d M:%s" % (ty, row_m))
    print("     T:%s" % row_t)
print()
print("box for id137 centre (1088,1056) tiles 32..35 x 32..33")
for ty in range(32, 34):
    print("ty%2d M: %s" % (ty, " ".join("%4d" % mx[ty*w+tx] for tx in range(32, 36))))
    print("     T: %s" % " ".join("%4d" % tl[ty*w+tx] for tx in range(32, 36)))
