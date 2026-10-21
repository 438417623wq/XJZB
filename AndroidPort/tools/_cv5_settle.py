import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader

ts = "platform"
src = None
for ar in (pm.SD, pm.BD):
    if ar.has("tileset\\%s.cv5" % ts):
        d, g = ar.read_with_gaps("tileset\\%s.cv5" % ts)
        src = "SD" if ar is pm.SD else "BD"
        break
cv = GapReader(d, g or [])
ng = (len(d) + sum(s for _, s in (g or []))) // 52
print("platform cv5 src=%s groups=%d" % (src, ng))

# find groups whose field at +12 == 137
hits = [gi for gi in range(1024, ng) if cv.u16(gi*52) == 1 and cv.u16(gi*52+12) == 137]
print("groups with @12==137:", hits)
hits2 = [gi for gi in range(1024, ng) if cv.u16(gi*52) == 1 and cv.u16(gi*52+6) == 137]
print("groups with @6==137:", hits2)

for gi in (1254, 1255):
    b = gi*52
    print("gi=%d b=%d vals@0..20: %s" % (gi, b, [cv.u16(b+k*2) for k in range(11)]))

print()
print("=== sprites.dat readability ===")
for nm, ar in (("SD", pm.SD), ("BD", pm.BD)):
    for p in ("arr\\sprites.dat", "arr\\images.dat"):
        if ar.has(p):
            dd, gg = ar.read_with_gaps(p)
            print("%s %s bytes=%d gaps=%d padded=%d" % (nm, p, len(dd), len(gg or []), len(dd)+sum(s for _,s in (gg or []))))
        else:
            print("%s %s MISSING" % (nm, p))
