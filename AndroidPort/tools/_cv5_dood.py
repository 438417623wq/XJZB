import os, sys
sys.path.insert(0, ".")
import sc_archive, pipeline_maps as pm
from gapio import GapReader

def cv5_of(ts):
    for ar in (pm.SD, pm.BD):
        if ar.has("tileset\\%s.cv5" % ts):
            d, g = ar.read_with_gaps("tileset\\%s.cv5" % ts)
            return GapReader(d, g or []), len(d) + sum(s for _, s in (g or [])), ar
    return None, 0, None

def doodad_groups(g, n):
    out = {}
    for gi in range(1024, n):
        b = gi * 52
        if g.u16(b) != 1:
            continue
        dd = g.u16(b + 12)
        out.setdefault(dd, []).append(gi)
    return out

for ts in ("platform",):
    g, n, ar = cv5_of(ts)
    print(ts, "cv5 bytes(padded)", n, "groups", n // 52, "archive", "SD" if ar is pm.SD else "BD")
    dg = doodad_groups(g, n // 52)
    print("doodad ids:", len(dg), "range", min(dg), max(dg))
    for dd in (137, 256, 257):
        gl = dg.get(dd, [])
        print("--- id", dd, "groups", len(gl), gl[:12])
        for gi in gl[:1]:
            b = gi * 52
            print("   flags=%#06x overlay=%d remastered=%d name=%d unk10=%d ddIdx=%d w=%d h=%d unk18=%d" % (
                g.u16(b+2), g.u16(b+4), g.u16(b+6), g.u16(b+8), g.u16(b+10),
                g.u16(b+12), g.u16(b+14), g.u16(b+16), g.u16(b+18)))
            refs = [g.u16(b + 20 + k*2) for k in range(16)]
            print("   megatile refs:", refs)
