import os, sys, json, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader

def cv5_of(ts):
    for ar in (pm.SD, pm.BD):
        p = "tileset\\%s.cv5" % ts
        if ar.has(p):
            d, g = ar.read_with_gaps(p)
            return GapReader(d, g or []), (len(d) + sum(s for _, s in (g or []))) // 52

def dd_groups(cv, ng):
    out = {}
    for gi in range(1024, ng):
        b = gi * 52
        if cv.u16(b) != 1:
            continue
        out.setdefault(cv.u16(b + 12), []).append(gi)
    return out

print("%-14s %-9s %6s %6s %6s %6s" % ("map", "tileset", "recs", "inb", "ovl", "terr"))
tot = collections.Counter()
detail = {}
for src, mid, name in pm.MAPS:
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    if not r: continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"DD2 " not in sec or b"DIM " not in sec or b"ERA " not in sec: continue
    o, s = sec[b"DIM "]
    w, h = g.u16(o), g.u16(o + 2)
    W, H = w * 32, h * 32
    eo, _ = sec[b"ERA "]
    ts = pm.TILESETS.get(g.byte(eo), "?")
    cv, ng = cv5_of(ts)
    dg = dd_groups(cv, ng)
    off, size = sec[b"DD2 "]
    raw = g.bytes_at(off, size)
    recs = []
    for i in range(0, size - 7, 8):
        t = raw[i] | (raw[i+1] << 8)
        x = raw[i+2] | (raw[i+3] << 8)
        y = raw[i+4] | (raw[i+5] << 8)
        if t > 511 or x >= W or y >= H: continue
        gl = dg.get(t)
        if not gl:
            recs.append((t, x, y, None, None, None)); continue
        b = gl[0] * 52
        recs.append((t, x, y, cv.u16(b + 2), cv.u16(b + 4), (cv.u16(b + 14), cv.u16(b + 16))))
    inb = [q for q in recs if q[3] is not None]
    ovl = [q for q in inb if q[3] & 0x3000]
    print("%-14s %-9s %6d %6d %6d %6d" % (mid, ts, len(recs), len(inb), len(ovl), len(inb) - len(ovl)))
    tot["recs"] += len(recs); tot["inb"] += len(inb); tot["ovl"] += len(ovl)
    detail[mid] = (ts, recs)
print("TOTAL", dict(tot))
json.dump({k: (v[0], v[1]) for k, v in detail.items()}, open("_dd2_ovl.json", "w"), indent=1)
