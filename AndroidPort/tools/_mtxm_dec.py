import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader

def cv5_of(ts):
    for ar in (pm.SD, pm.BD):
        p = "tileset\\%s.cv5" % ts
        if ar.has(p):
            d, g = ar.read_with_gaps(p)
            return GapReader(d, g or []), (len(d) + sum(s for _, s in (g or []))) // 52

for mid, src, ts in (("bloodbath", r"maps\(4)Blood Bath.scm", "platform"),
                     ("divide", r"maps\(2)The Small Divide.scm", "jungle"),
                     ("volcanis", r"maps\(2)Volcanis.scm", "ashworld")):
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    o, _ = sec[b"DIM "]
    w, h = g.u16(o), g.u16(o+2)
    mo, _ = sec[b"MTXM"]
    vals = [g.u16(mo+i*2) for i in range(w*h)]
    cv, ng = cv5_of(ts)
    for label, dec in (("raw v", lambda v: v), ("v&0x7FF0>>4", lambda v: (v & 0x7FF0) >> 4)):
        grp = collections.Counter(dec(v) for v in vals)
        oob = [x for x in grp if x >= ng]
        zero = [x for x in grp if x < ng and cv.u16(x*52) == 0]
        dood = [x for x in grp if x < ng and cv.u16(x*52) == 1]
        print("%-10s %-12s distinct=%4d oob=%4d typ0=%4d doodad=%4d max=%d" % (
            mid, label, len(grp), len(oob), len(zero), len(dood), max(grp)))
        if oob:
            print("      oob sample:", sorted(oob)[:8])
        if zero:
            print("      typ0 sample:", sorted(zero)[:8])
    print()
